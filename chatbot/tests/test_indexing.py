import re
import sys
from collections import Counter
from pathlib import Path

import pytest
from docx import Document

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))
import indexing  # noqa: E402
import redact_cv  # noqa: E402

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
        "contact": 1,             # name, tagline, email, links (from the page header)
        "section": 3,             # Summary, Education, Certifications
        "skills": 1,              # the Key Skills table
        "experience": 6,          # one per job
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
        # Titles lose their "[GitHub]" labels on purpose, and a job line ("Title | dates") is reshaped
        # into "Title at Company (dates)", so each " | " part must survive rather than the whole line.
        parts = [indexing.strip_link_labels(part).lower() for part in text.split(" | ")]
        if text.lower() not in indexed and not all(part in indexed for part in parts):
            missing.append(text[:70])
    assert missing == []


def test_skills_chunk_comes_from_the_table(chunks):
    (skills,) = [c for c in chunks if c.kind == "skills"]
    assert any(line.startswith("Languages: ") for line in skills.lines)
    assert len(skills.lines) == 10


def test_links_come_from_the_cv_hyperlinks(chunks):
    (animal,) = [c for c in chunks if c.title == "Animal Object Detector"]
    assert animal.links == ["https://github.com/somunaexe/ANIMAL-OBJECT-DETECTOR"]


EXPECTED_ROLES = {
    "Full Stack Developer at Bulfighter": ("Bulfighter", "Sep 2025 – Present"),
    "Generative AI Engineer at Reality AI Lab": ("Reality AI Lab", "Dec 2024 – June 2025"),
    "Customer Service Manager at Entain": ("Entain", "Mar 2025 – Sep 2026"),
    "Web Developer at Car2Enquiries": ("Car2Enquiries", "Dec 2022 – Jan 2023"),
    "Course Representative (Voluntary) at University of Salford": ("University of Salford", "Oct 2021 – May 2022, Oct 2023 – Present"),
    "Student Ambassador (Voluntary) at NCUK": ("NCUK", "Jun 2022 – Jul 2023"),
}


@pytest.mark.parametrize("title, expected", EXPECTED_ROLES.items())
def test_each_job_is_its_own_chunk_with_company_and_dates(chunks, title, expected):
    (chunk,) = [c for c in chunks if c.kind == "experience" and c.title == title]
    assert (chunk.company, chunk.detail) == expected
    assert any(line.startswith("- ") for line in chunk.lines)


def test_a_job_chunk_holds_only_that_job(chunks):
    (entain,) = [c for c in chunks if c.company == "Entain"]
    assert "Bulfighter" not in entain.text and "Reality AI Lab" not in entain.text


def test_the_bulfighter_role_keeps_its_website_link(chunks):
    (bulfighter,) = [c for c in chunks if c.company == "Bulfighter"]
    assert bulfighter.links == ["http://bulfighter.com/"]


def test_contact_chunk_has_email_and_location_but_no_phone(chunks):
    (contact,) = [c for c in chunks if c.kind == "contact"]
    assert "somunanzenwa@gmail.com" in contact.text
    assert "Salford, UK" in contact.text
    assert "Full-Stack Developer" in contact.text          # the headline
    assert not re.search(redact_cv.PHONE, contact.text)


def test_no_chunk_contains_a_phone_number(chunks):
    assert all(not re.search(redact_cv.PHONE, c.text) for c in chunks)


def test_indexer_refuses_text_with_a_phone_number():
    # 07700 900xxx is Ofcom's reserved drama range (never assigned to anyone)
    leaky = indexing.Chunk(kind="section", title="Oops", section="X", lines=["call me on +44 7700 900123"])
    with pytest.raises(ValueError, match="redact_cv"):
        indexing.assert_no_phone_numbers([leaky])
