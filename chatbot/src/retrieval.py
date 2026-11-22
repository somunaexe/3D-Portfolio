"""Retrieve the CV chunks nearest to a question.

DEFAULT_K = 10 was chosen from measurement, not instinct: across 20 "Have you used X?"
technology questions, average recall of the chunks that mention X was 50% at k=3, 85% at
k=8, 91% at k=10 and 96% at k=15, for roughly 1,350 prompt tokens at k=10 (CV chunks are
small). Past about 10 the gains flatten. The LLM is told to ignore irrelevant excerpts.
"""
import os
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


def retrieve(question, k=DEFAULT_K, db_dir=DB_DIR):
    """Nearest chunks first: [{id, distance, text, title, kind, ...metadata}]."""
    collection = _collection(str(db_dir))
    with _slots:
        result = collection.query(query_texts=[question], n_results=k)
    return [
        {"id": id_, "distance": distance, "text": text, **metadata}
        for id_, distance, text, metadata in zip(
            result["ids"][0], result["distances"][0], result["documents"][0], result["metadatas"][0]
        )
    ]
