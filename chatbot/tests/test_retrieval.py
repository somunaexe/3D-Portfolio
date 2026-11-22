"""Retrieval-quality regression tests: build a throwaway index and ask recruiter-style questions.

First run downloads the 79 MB embedding model (cached afterwards), then takes a few seconds.
These record what retrieval does TODAY so a change to chunking or embeddings can be judged
against evidence. Known weaknesses are marked xfail, not hidden.
"""
import sys
from pathlib import Path

import chromadb
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import indexing  # noqa: E402
import probe  # noqa: E402


@pytest.fixture(scope="module")
def db_dir(tmp_path_factory):
    path = tmp_path_factory.mktemp("chroma")
    indexing.index_chunks(indexing.build_chunks(), db_dir=path)
    return path


def titles(db_dir, question, k=3):
    return [hit["title"] for hit in probe.retrieve(question, k=k, db_dir=db_dir)]


def test_every_chunk_is_stored_with_flat_metadata(db_dir):
    collection = chromadb.PersistentClient(path=str(db_dir)).get_collection(
        indexing.COLLECTION, embedding_function=indexing.embedding_function()
    )
    assert collection.count() == len(indexing.build_chunks()) == 37
    for metadata in collection.get(include=["metadatas"])["metadatas"]:
        assert all(isinstance(v, (str, int, float, bool)) for v in metadata.values())


@pytest.mark.parametrize(
    "question, expected_top",
    [
        ("What did you do at Entain?", "Customer Service Manager at Entain"),
        ("What did you do at Reality AI Lab?", "Generative AI Engineer at Reality AI Lab"),
        ("Where are you based and how can I contact you?", "Contact & headline"),
        ("What is your degree?", "Education"),
        ("What programming languages do you know?", "Key Skills"),
        ("Do you have any certifications?", "Certifications"),
        ("Have you used Terraform?", "IaC Weather Tracker with Disaster Recovery"),
    ],
)
def test_the_right_chunk_ranks_first(db_dir, question, expected_top):
    assert titles(db_dir, question)[0] == expected_top


def test_collaboration_question_finds_bulwriter_in_the_top_three(db_dir):
    assert "Bulwriter — Collaborative Screenwriting Platform" in titles(db_dir, "Have you built anything with real-time collaboration?")


def test_mobile_question_returns_only_mobile_projects(db_dir):
    hits = probe.retrieve("Have you built mobile apps?", k=3, db_dir=db_dir)
    assert [hit.get("role_group") for hit in hits] == ["Mobile Developer"] * 3


def test_ml_question_ranks_an_ai_ml_project_first(db_dir):
    (top,) = probe.retrieve("Tell me about your machine learning projects", k=1, db_dir=db_dir)
    assert top["role_group"] == "AI / ML Engineer"


DOCKER_CHUNKS = {
    "Key Skills",
    "Real-Time IoT Sensor Intelligence Platform",
    "Runners Tracker API",
    "Bulwriter — Collaborative Screenwriting Platform",
}


@pytest.mark.xfail(
    reason="Known weakness: 'Docker' is one word among many in each chunk, so dense retrieval ranks "
    "JustCalls (no Docker) first and only 1 of 4 Docker chunks is in the top 3. Candidates: larger k, "
    "hybrid keyword search, or a technologies line per chunk.",
    strict=True,
)
def test_docker_question_finds_most_docker_chunks_in_the_top_three(db_dir):
    assert len(DOCKER_CHUNKS & set(titles(db_dir, "Have you used Docker?"))) >= 2
