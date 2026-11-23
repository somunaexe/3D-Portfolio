"""Retrieve the CV chunks nearest to a question.

DEFAULT_K = 10 was chosen from measurement, not instinct: across 20 "Have you used X?"
technology questions, average recall of the chunks that mention X was 50% at k=3, 85% at
k=8, 91% at k=10 and 96% at k=15, for roughly 1,350 prompt tokens at k=10 (CV chunks are
small). Past about 10 the gains flatten. The LLM is told to ignore irrelevant excerpts.
"""
import os
import re
import threading
from functools import lru_cache

import chromadb

from indexing import COLLECTION, DB_DIR, embedding_function

DEFAULT_K = 10

# Embedding runs the ONNX model, and every thread that runs it at once allocates its own working memory:
# 16 simultaneous retrievals took peak memory from ~280 MB to ~2 GB. Retrieval is only ~200 ms of a request
# (the LLM call is the slow part), so letting a couple run at a time costs almost nothing and bounds memory.
_slots = threading.BoundedSemaphore(int(os.environ.get("RETRIEVAL_CONCURRENCY", "2")))


@lru_cache(maxsize=8)
def _collection(db_dir):
    """Open the collection once per database path and reuse it, so the embedding model is loaded once, not per
    request. (If you re-run `indexing.py --index` while a server is running, restart the server.)"""
    client = chromadb.PersistentClient(path=db_dir)
    # The embedding function must be the one used at indexing time (see indexing.embedding_function).
    return client.get_collection(COLLECTION, embedding_function=embedding_function())


MAX_NAMED = 3   # at most this many chunks are pulled in by name, so one broad question can't flood the prompt


@lru_cache(maxsize=8)
def _names(db_dir):
    """[(name, chunk id)] for every role's company and every project's short title, e.g. ("Bulfighter", ...).
    Read once from the stored metadata, so it can never drift from what was indexed."""
    stored = _collection(db_dir).get(include=["metadatas"])
    names = []
    for id_, meta in zip(stored["ids"], stored["metadatas"]):
        name = meta.get("company") if meta["kind"] == "experience" else meta["title"].split(" \u2014 ")[0] if meta["kind"] == "project" else None
        if name:
            names.append((name, id_))
    return tuple(names)


def named_chunk_ids(question, db_dir=DB_DIR):
    """Chunks whose company or project name appears in the question (whole word, any case).

    Why: embeddings match on MEANING, and a rare proper noun like "Bulfighter" carries little of it. Measured on
    "What did Somuna do at Bulfighter?", the Bulfighter role fell out of the top 10 behind the contact chunk
    (which contains the name "Somuna") and unrelated roles. Asking about something BY NAME is a lookup, not a
    similarity search, so we do the lookup directly and let vector search fill the rest."""
    found = []
    for name, id_ in _names(str(db_dir)):
        if re.search(rf"(?<!\w){re.escape(name)}(?!\w)", question, re.IGNORECASE):
            found.append(id_)
    return found[:MAX_NAMED]


def retrieve(question, k=DEFAULT_K, db_dir=DB_DIR):
    """The k most relevant chunks: any named in the question first, then nearest by meaning.
    [{id, distance, text, title, kind, ...metadata}]; distance is None for a chunk found by name only."""
    collection = _collection(str(db_dir))
    with _slots:
        result = collection.query(query_texts=[question], n_results=k)
    hits = [
        {"id": id_, "distance": distance, "text": text, **metadata}
        for id_, distance, text, metadata in zip(
            result["ids"][0], result["distances"][0], result["documents"][0], result["metadatas"][0]
        )
    ]
    named = named_chunk_ids(question, db_dir)
    if not named:
        return hits
    by_id = {hit["id"]: hit for hit in hits}
    missing = [id_ for id_ in named if id_ not in by_id]
    if missing:
        stored = collection.get(ids=missing, include=["documents", "metadatas"])
        for id_, text, metadata in zip(stored["ids"], stored["documents"], stored["metadatas"]):
            by_id[id_] = {"id": id_, "distance": None, "text": text, **metadata}
    front = [by_id[id_] for id_ in named]
    rest = [hit for hit in hits if hit["id"] not in named]
    return (front + rest)[:k]
