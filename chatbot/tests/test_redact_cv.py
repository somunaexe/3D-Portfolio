import sys
from pathlib import Path

import pytest
from docx import Document

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import redact_cv  # noqa: E402


def paragraph_with_runs(*texts):
    document = Document()
    paragraph = document.add_paragraph()
    for text in texts:
        paragraph.add_run(text)
    return paragraph


@pytest.mark.parametrize(
    "runs, expected",
    [
        # phone in the middle of the contact line: one separator goes with it
        (["me@x.com   |   +44 7700 900123   |   Salford, UK"], "me@x.com   |   Salford, UK"),
        # phone is the last item: take the separator before it
        (["me@x.com | Salford | +44 7700 900123"], "me@x.com | Salford"),
        # phone split across runs (Word does this after edits)
        (["me@x.com | +44 7700 ", "900123", " | Salford"], "me@x.com | Salford"),
        # UK local format
        (["call 07700 900456 anytime"], "call anytime"),
    ],
)
def test_phone_is_removed(runs, expected):
    paragraph = paragraph_with_runs(*runs)
    assert redact_cv.redact_paragraph(paragraph) == 1
    assert " ".join(paragraph.text.split()) == " ".join(expected.split())


@pytest.mark.parametrize(
    "text",
    [
        "Sep 2025 – Present",
        "Oct 2021 – May 2022, Oct 2023 – Present",
        "Achieved: 4 A*'s (224 UCAS points)",
        "supporting 100 monthly active users and 50+ concurrent sessions",
        "scaled to support 2,000 concurrent users",
        "cutting release time from 30 mins - 40 secs",
    ],
)
def test_ordinary_cv_text_is_untouched(text):
    paragraph = paragraph_with_runs(text)
    assert redact_cv.redact_paragraph(paragraph) == 0
    assert paragraph.text == text
