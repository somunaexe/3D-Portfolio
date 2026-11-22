"""Milestone 1, step 1-2: load the tagged CV and split it into retrieval chunks.

Reads chatbot/data/Main_CV_Improved.docx (Heading 1/2/3 applied by tag_cv_headings.py)
and produces one Chunk per:

    * top-level text section   Professional Summary, Education, Experience, Certifications
    * the Key Skills table     (it has no paragraphs, only a table)
    * individual project       tagged with its role group (the H2 it sits under)
    * Projects overview        the intro and "Additional projects" lines that belong to no project

    python chatbot/src/indexing.py            # prints a summary of the chunks
"""
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

from docx import Document
from docx.oxml.ns import qn
from docx.table import Table
from docx.text.paragraph import Paragraph

from tag_cv_headings import is_tech_line

CV_PATH = Path(__file__).resolve().parents[1] / "data" / "Main_CV_Improved.docx"

PROJECTS = "PROJECTS"
SKILLS = "KEY SKILLS"
ADDITIONAL_PROJECTS = "Additional projects"


@dataclass
class Chunk:
    """All metadata is fixed when the chunk is opened, never read from loop state later."""

    id: str
    kind: str                      # "section" | "skills" | "project" | "projects_overview"
    title: str
    section: str                   # the H1 it belongs to
    role_group: str | None = None  # the H2 above it (projects only)
    links: list[str] = field(default_factory=list)
    lines: list[str] = field(default_factory=list)

    @property
    def text(self):
        header = self.title if not self.role_group else f"{self.title} ({self.role_group})"
        return "\n".join([header, *self.lines])


def clean(text):
    """Tidy Word's layout whitespace: tabs separate a job title from its dates."""
    text = re.sub(r"\s*\t\s*", "  |  ", text.strip())
    return re.sub(r" {2,}", " ", text).replace(" | ", " | ")


def strip_link_labels(title):
    """'Animal Object Detector   [GitHub]' -> 'Animal Object Detector'."""
    return re.sub(r"\s*\[[^\]]+\]", "", title).strip()


def heading_level(paragraph):
    name = paragraph.style.name
    return int(name.split()[-1]) if name.startswith("Heading ") else None


def iter_blocks(document):
    """Paragraphs and tables in true document order (python-docx lists them separately)."""
    for child in document.element.body.iterchildren():
        if child.tag == qn("w:p"):
            yield Paragraph(child, document)
        elif child.tag == qn("w:tbl"):
            yield Table(child, document)


def table_lines(table):
    return [f"{row.cells[0].text.strip()}: {row.cells[1].text.strip()}" for row in table.rows]


def build_chunks(path=CV_PATH):
    document = Document(str(path))
    chunks = []
    current = None       # the chunk being filled
    section = None       # current H1 title
    role_group = None    # current H2 title; copied into a chunk only at the moment it opens
    overview = None      # PROJECTS intro / trailing notes

    def flush():
        nonlocal current
        if current is not None and current.lines:
            chunks.append(current)
        current = None

    def open_chunk(kind, title, links=()):
        nonlocal current
        flush()
        current = Chunk(
            id=f"{len(chunks) + 1:02d}-{re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')}",
            kind=kind,
            title=title,
            section=section,
            role_group=role_group if kind == "project" else None,
            links=list(links),
        )

    blocks = list(iter_blocks(document))
    for index, block in enumerate(blocks):
        if isinstance(block, Table):
            if section and section.upper() == SKILLS:
                open_chunk("skills", "Key Skills")
                current.lines.extend(table_lines(block))
                flush()
            continue

        text = clean(block.text)
        if not text:
            continue
        level = heading_level(block)

        if level == 1:
            flush()
            section, role_group = text.title(), None
            if text.upper() not in (PROJECTS, SKILLS):
                open_chunk("section", section)
            elif text.upper() == PROJECTS:
                overview = Chunk(id="projects-overview", kind="projects_overview", title="Projects overview", section=section)
        elif level == 2:
            flush()
            role_group = text
        elif level == 3:
            open_chunk("project", strip_link_labels(text), links=[h.url for h in block.hyperlinks if h.url])
        elif section and section.upper() == PROJECTS and (current is None or text.startswith(ADDITIONAL_PROJECTS)):
            # Intro line, or the closing "Additional projects" note: belongs to no single project.
            overview.lines.append(text)
        elif current is not None:
            prefix = "Tech: " if is_tech_line(block) else ("- " if current.kind == "project" else "")
            current.lines.append(prefix + text)
        else:
            raise ValueError(f"Paragraph outside any chunk (nothing would index it): {text[:70]!r}")

    flush()
    if overview is not None and overview.lines:
        overview.id = f"{len(chunks) + 1:02d}-projects-overview"
        chunks.append(overview)
    return chunks


def main():
    chunks = build_chunks()
    print(f"{len(chunks)} chunks from {CV_PATH.name}\n")
    for chunk in chunks:
        print(f"{chunk.id:<58} {chunk.kind:<18} {len(chunk.text):>5} chars  {chunk.role_group or ''}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
