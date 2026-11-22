"""Apply Word heading styles to the CV so the indexer can chunk it by structure.

The CV was laid out visually: every paragraph is "Normal" and the hierarchy only
exists as direct formatting (bold / size / colour). This script reads that
formatting once and writes the structure into real Word styles:

    Heading 1  top-level section        (PROFESSIONAL SUMMARY, EXPERIENCE, PROJECTS, ...)
    Heading 2  project role group       (AI / ML Engineer, Backend Engineer, ...)
    Heading 3  individual project title (Real-Time IoT Sensor Intelligence Platform, ...)

Only the paragraph style changes: run formatting is left alone, so the CV looks
the same. The script is idempotent and fails loudly on anything it cannot classify.

    python chatbot/src/tag_cv_headings.py INPUT.docx OUTPUT.docx
"""
import argparse
import sys

from docx import Document
from docx.text.paragraph import Paragraph

# Formatting fingerprints, read from the CV itself (RGB hex, size in points).
SECTION_COLOUR = "1F4E79"   # H1 and H2 share this colour
PROJECT_COLOUR = "262626"
SECTION_SIZE = 14.0         # H1 only
GROUP_SIZE = 11.5           # H2 and H3 share this size
TECH_LINE_SIZE = 9.5        # the grey "Python · FastAPI · ..." line under a project title
TECH_LINE_COLOUR = "595959"

PROJECTS_SECTION = "PROJECTS"


def run_format(paragraph):
    """(all_bold, size_pt, colour_hex) of the first non-empty run, or None for a blank line."""
    runs = [run for run in paragraph.runs if run.text.strip()]
    if not runs:
        return None
    first = runs[0]
    colour = first.font.color
    return (
        all(run.bold for run in runs),
        first.font.size.pt if first.font.size else None,
        str(colour.rgb) if colour is not None and colour.type is not None and colour.rgb else None,
    )


def is_tech_line(paragraph):
    fmt = run_format(paragraph)
    return fmt is not None and not fmt[0] and fmt[1] == TECH_LINE_SIZE and fmt[2] == TECH_LINE_COLOUR


def next_nonblank(paragraphs, index):
    for later in paragraphs[index + 1:]:
        if later.text.strip():
            return later
    return None


def classify(paragraph, next_paragraph, in_projects):
    """Return 1, 2, 3 or None (leave as Normal). Raises on an ambiguous bold line."""
    fmt = run_format(paragraph)
    if fmt is None:
        return None
    all_bold, size, colour = fmt
    if not all_bold:
        return None  # bullets, descriptions, tech lines, job lines (title bold, dates not)

    if size == SECTION_SIZE and colour == SECTION_COLOUR:
        return 1
    if in_projects and size == GROUP_SIZE and colour == SECTION_COLOUR:
        return 2
    if in_projects and (
        (size == GROUP_SIZE and colour == PROJECT_COLOUR)
        # A title that lost its size/colour (JustCalls did) is still recognisable by
        # structure: all-bold, directly above the grey tech line.
        or (next_paragraph is not None and is_tech_line(next_paragraph))
    ):
        return 3

    raise ValueError(f"Unclassified fully-bold line {fmt}: {paragraph.text.strip()[:70]!r}")


def tag(document):
    styles = {1: "Heading 1", 2: "Heading 2", 3: "Heading 3"}
    paragraphs = list(document.paragraphs)
    in_projects = False
    counts = {1: 0, 2: 0, 3: 0}
    for index, paragraph in enumerate(paragraphs):
        level = classify(paragraph, next_nonblank(paragraphs, index), in_projects)
        if level is None:
            continue
        if level == 1:
            in_projects = paragraph.text.strip().upper() == PROJECTS_SECTION
        paragraph.style = document.styles[styles[level]]
        counts[level] += 1
    return counts


def outline(document):
    """[(level, text)] for every heading paragraph, in order."""
    return [
        (int(p.style.name.split()[-1]), p.text.strip())
        for p in document.paragraphs
        if p.style.name.startswith("Heading ") and p.text.strip()
    ]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("input")
    parser.add_argument("output")
    args = parser.parse_args(argv)

    document = Document(args.input)
    counts = tag(document)
    document.save(args.output)
    print(f"Tagged {counts[1]} sections (H1), {counts[2]} role groups (H2), {counts[3]} projects (H3) -> {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
