"""Milestone 1, step 1-2: load the tagged CV and split it into retrieval chunks.

Reads chatbot/data/Main_CV_Improved.docx (Heading 1/2/3 applied by tag_cv_headings.py,
phone number removed by redact_cv.py) and produces one Chunk per:

    * contact & headline        name, tagline, email, location, links (from the page header)
    * top-level text section    Professional Summary, Education, Certifications
    * the Key Skills table      (it has no paragraphs, only a table)
    * job / role                one per Experience entry, e.g. "Generative AI Engineer at Reality AI Lab"
    * individual project        tagged with its role group (the H2 it sits under)
    * Projects overview         the intro and "Additional projects" lines that belong to no project

Then embeds every chunk and stores it in a local Chroma database (chatbot/chroma_db):

    python chatbot/src/indexing.py            # prints a summary of the chunks
    python chatbot/src/indexing.py --index    # ...and embeds + stores them (rebuilds from scratch)
"""
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import chromadb
from chromadb.utils.embedding_functions import ONNXMiniLM_L6_V2
from docx import Document
from docx.oxml.ns import qn
from docx.table import Table
from docx.text.paragraph import Paragraph

from redact_cv import PHONE
from tag_cv_headings import is_tech_line, run_format

CV_PATH = Path(__file__).resolve().parents[1] / "data" / "Main_CV_Improved.docx"

DB_DIR = Path(__file__).resolve().parents[1] / "chroma_db"
COLLECTION = "portfolio_cv"

PROJECTS = "PROJECTS"
SKILLS = "KEY SKILLS"
EXPERIENCE = "EXPERIENCE"
ADDITIONAL_PROJECTS = "Additional projects"
ROLE_LINE_SIZE = 12.0  # job-title lines are 12pt; project titles are 11.5pt


@dataclass
class Chunk:
    """All metadata is fixed when the chunk is opened, never read from loop state later."""

    kind: str                      # "contact" | "section" | "skills" | "experience" | "project" | "projects_overview"
    title: str
    section: str | None            # the H1 it belongs to
    id: str = ""                   # assigned in a final pass, once every title is known
    detail: str | None = None      # shown next to the title: a project's role group or a job's dates
    role_group: str | None = None  # the H2 above it (projects only)
    company: str | None = None     # experience only
    links: list[str] = field(default_factory=list)
    lines: list[str] = field(default_factory=list)

    @property
    def text(self):
        header = f"{self.title} ({self.detail})" if self.detail else self.title
        return "\n".join([header, *self.lines])


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def clean(text):
    """Tidy Word's layout whitespace: tabs separate a job title from its dates."""
    text = re.sub(r"\s*\t\s*", "  |  ", text.strip())
    return re.sub(r" {2,}", " ", text)


def strip_link_labels(title):
    """'Animal Object Detector   [GitHub]' -> 'Animal Object Detector'."""
    return re.sub(r"\s*\[[^\]]+\]", "", title).strip()


def heading_level(paragraph):
    name = paragraph.style.name
    return int(name.split()[-1]) if name.startswith("Heading ") else None


def is_role_line(paragraph):
    """'Generative AI Engineer <tab> Dec 2024 - June 2025': a tab plus 12pt text."""
    fmt = run_format(paragraph)
    return "\t" in paragraph.text and fmt is not None and fmt[1] == ROLE_LINE_SIZE


def iter_blocks(document):
    """Paragraphs and tables in true document order (python-docx lists them separately)."""
    for child in document.element.body.iterchildren():
        if child.tag == qn("w:p"):
            yield Paragraph(child, document)
        elif child.tag == qn("w:tbl"):
            yield Table(child, document)


def table_lines(table):
    return [f"{row.cells[0].text.strip()}: {row.cells[1].text.strip()}" for row in table.rows]


def header_paragraphs(document):
    """Every distinct non-empty page-header paragraph (the contact block lives here)."""
    seen, found = set(), []
    for section in document.sections:
        for header in (section.header, section.first_page_header, section.even_page_header):
            for paragraph in header.paragraphs:
                text = clean(paragraph.text)
                if text and text not in seen:
                    seen.add(text)
                    found.append(paragraph)
    return found


def contact_chunk(document):
    paragraphs = header_paragraphs(document)
    if not paragraphs:
        raise ValueError("No page-header text found: the contact chunk would be empty")
    chunk = Chunk(kind="contact", title="Contact & headline", section=None)
    for paragraph in paragraphs:
        chunk.lines.append(clean(paragraph.text))
        chunk.links += [h.url for h in paragraph.hyperlinks if h.url]
    return chunk


def assert_no_phone_numbers(chunks):
    """Refuse to index a CV that still contains a phone number (run redact_cv.py first)."""
    for chunk in chunks:
        if re.search(PHONE, chunk.text):
            raise ValueError(f"Phone number found in chunk {chunk.title!r}: run redact_cv.py on the CV first")


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

    def open_chunk(kind, title, **fields):
        nonlocal current
        flush()
        current = Chunk(kind=kind, title=title, section=section, **fields)

    for block in iter_blocks(document):
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
        in_section = section.upper() if section else None

        if level == 1:
            flush()
            section, role_group = text.title(), None
            if text.upper() == PROJECTS:
                overview = Chunk(kind="projects_overview", title="Projects overview", section=section)
            elif text.upper() not in (SKILLS, EXPERIENCE):   # skills = table, experience = one chunk per role
                open_chunk("section", section)
        elif level == 2:
            flush()
            role_group = text
        elif level == 3:
            open_chunk(
                "project",
                strip_link_labels(text),
                detail=role_group,
                role_group=role_group,
                links=[h.url for h in block.hyperlinks if h.url],
            )
        elif in_section == EXPERIENCE and is_role_line(block):
            job, _, dates = text.partition(" | ")
            open_chunk(
                "experience",
                strip_link_labels(job),
                detail=dates.strip(),
                links=[h.url for h in block.hyperlinks if h.url],
            )
        elif in_section == EXPERIENCE and current is not None and current.company is None:
            # The line under a job title: "Reality AI Lab — Salford, UK"
            current.company = text.split(" — ")[0].strip()
            current.title = f"{current.title} at {current.company}"
            current.lines.append(text)
        elif in_section == PROJECTS and (current is None or text.startswith(ADDITIONAL_PROJECTS)):
            # Intro line, or the closing "Additional projects" note: belongs to no single project.
            overview.lines.append(text)
        elif current is not None:
            bulleted = current.kind in ("project", "experience")
            current.lines.append(("Tech: " if is_tech_line(block) else "- " if bulleted else "") + text)
        else:
            raise ValueError(f"Paragraph outside any chunk (nothing would index it): {text[:70]!r}")

    flush()
    if overview is not None and overview.lines:
        chunks.append(overview)

    chunks.insert(0, contact_chunk(document))
    assert_no_phone_numbers(chunks)
    for number, chunk in enumerate(chunks, start=1):
        chunk.id = f"{number:02d}-{slug(chunk.title)}"
    return chunks


def embedding_function():
    """The ONE embedding model, defined in a single place.

    Stored chunk vectors and later query vectors must come from the same model, so
    anything that embeds text (indexing now, the query pipeline later) must call this.
    all-MiniLM-L6-v2 runs locally via ONNX: 384 dimensions, no API key.
    """
    return ONNXMiniLM_L6_V2()


def chunk_metadata(chunk):
    """Chroma metadata must be flat str/int/float/bool, and may not hold None or lists."""
    values = {
        "kind": chunk.kind,
        "title": chunk.title,
        "section": chunk.section,
        "role_group": chunk.role_group,
        "company": chunk.company,
        "dates": chunk.detail if chunk.kind == "experience" else None,
        "links": " ".join(chunk.links) or None,
    }
    return {key: value for key, value in values.items() if value is not None}


def index_chunks(chunks, db_dir=DB_DIR):
    """Embed and store every chunk. Rebuilds the collection so stale chunks never linger."""
    client = chromadb.PersistentClient(path=str(db_dir))
    existing = [c if isinstance(c, str) else c.name for c in client.list_collections()]
    if COLLECTION in existing:
        client.delete_collection(COLLECTION)
    collection = client.create_collection(
        COLLECTION,
        embedding_function=embedding_function(),
        configuration={"hnsw": {"space": "cosine"}},
    )
    collection.add(
        ids=[chunk.id for chunk in chunks],
        documents=[chunk.text for chunk in chunks],
        metadatas=[chunk_metadata(chunk) for chunk in chunks],
    )
    return collection


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    chunks = build_chunks()
    print(f"{len(chunks)} chunks from {CV_PATH.name}\n")
    for chunk in chunks:
        print(f"{chunk.id:<58} {chunk.kind:<18} {len(chunk.text):>5} chars  {chunk.detail or ''}")
    if "--index" in argv:
        collection = index_chunks(chunks)
        print(f"\nStored {collection.count()} chunks in {DB_DIR} (collection {COLLECTION!r}, cosine distance)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
