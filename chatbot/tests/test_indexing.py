import sys
from collections import Counter
from pathlib import Path

import pytest
from docx import Document

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))
import indexing  # noqa: E402

# Last project of each role group: the case a shared "current group" variable gets wrong,
# because by the time the chunk is flushed the next group's heading has already been read.
LAST_IN_GROUP = {
    "Real-Time Anomaly Detector": "AI / ML Engineer",
    "HTTP Server from Scratch": "Backend Engineer",
    "IaC Weather Tracker with Disaster Recovery": "Cloud & DevOps Engineer",
    "Note Organisation App": "Frontend Engineer",
    "Online Shopping Store": "Full-Stack Engineer",
    "Mario Kart Clone (Open Source)": "Game Developer",
    "JustCalls": "Mobile Developer",
}


@pytest.fixture(scope="module")
def chunks():
    return indexing.build_chunks()


def test_chunk_counts_by_kind(chunks):
    assert Counter(c.kind for c in chunks) == {
        "section": 4,             # Summary, Education, Experience, Certifications
        "skills": 1,              # the Key Skills table
        "project": 25,
        "projects_overview": 1,   # intro + "Additional projects" note
    }


def test_ids_are_unique(chunks):
    ids = [c.id for c in chunks]
    assert len(ids) == len(set(ids))


@pytest.mark.parametrize("title, group", LAST_IN_GROUP.items())
def test_last_project_in_each_group_keeps_its_own_role_group(chunks, title, group):
    (chunk,) = [c for c in chunks if c.title == title]
    assert chunk.role_group == group


def test_every_project_has_a_role_group_and_tech_line(chunks):
    for chunk in (c for c in chunks if c.kind == "project"):
        assert chunk.role_group, chunk.title
        assert any(line.startswith("Tech: ") for line in chunk.lines), chunk.title


def test_additional_projects_note_is_not_glued_onto_the_last_project(chunks):
    (justcalls,) = [c for c in chunks if c.title == "JustCalls"]
    assert "Additional projects" not in justcalls.text
    (overview,) = [c for c in chunks if c.kind == "projects_overview"]
    assert "Additional projects" in overview.text


def test_no_text_is_silently_dropped(chunks):
    """Every non-empty CV line must appear in some chunk (role-group headings live in metadata)."""
    document = Document(str(indexing.CV_PATH))
    # Section headings are title-cased on purpose ("EXPERIENCE" -> "Experience"), so compare
    # case-insensitively; every other line must still match exactly.
    indexed = "\n".join(c.text for c in chunks).lower()
    groups = {c.role_group for c in chunks if c.role_group}
    missing = []
    for paragraph in document.paragraphs:
        text = indexing.clean(paragraph.text)
        if not text or text in groups:
            continue
        # project titles lose their "[GitHub]" labels on purpose
        if indexing.strip_link_labels(text).lower() not in indexed and text.lower() not in indexed:
            missing.append(text[:70])
    assert missing == []


def test_skills_chunk_comes_from_the_table(chunks):
    (skills,) = [c for c in chunks if c.kind == "skills"]
    assert any(line.startswith("Languages: ") for line in skills.lines)
    assert len(skills.lines) == 10


def test_links_come_from_the_cv_hyperlinks(chunks):
    (animal,) = [c for c in chunks if c.title == "Animal Object Detector"]
    assert animal.links == ["https://github.com/somunaexe/ANIMAL-OBJECT-DETECTOR"]
