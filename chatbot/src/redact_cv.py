"""Remove phone numbers from a CV .docx before it is committed or indexed.

The CV's contact line (page header) holds a phone number that is deliberately kept
off the portfolio site. This script strips it from every paragraph in the body,
tables, headers and footers, then re-reads the saved file's raw XML and refuses to
succeed if any trace of a phone number is left.

    python chatbot/src/redact_cv.py INPUT.docx OUTPUT.docx
"""
import argparse
import re
import sys
import zipfile

from docx import Document
from docx.oxml.ns import qn
from docx.text.paragraph import Paragraph

# +44 793 654 8807 / 07936 548807 / (0161) 123 4567. Needs a country or area prefix plus
# two more digit groups, so years ("2022 – 2023"), "10+" and "224 UCAS points" never match.
PHONE = r"\+?\d{1,3}[\s.-]?\(?\d{2,4}\)?[\s.-]?\d{3}[\s.-]?\d{3,4}"
SEPARATOR = r"\s*\|\s*"  # the contact line is "a | b | c"
PHONE_WITH_SEPARATOR = re.compile(rf"{PHONE}(?:{SEPARATOR})?")
LEADING_SEPARATOR = re.compile(rf"(?:{SEPARATOR})$")

PART_KINDS = ("/header", "/footer")


def remove_span(paragraph, start, end):
    """Delete paragraph.text[start:end], even when it spans several runs."""
    position = 0
    for run in paragraph.runs:
        run_start, run_end = position, position + len(run.text)
        position = run_end
        if run_end <= start or run_start >= end:
            continue
        cut_from, cut_to = max(start, run_start) - run_start, min(end, run_end) - run_start
        run.text = run.text[:cut_from] + run.text[cut_to:]


def redact_paragraph(paragraph):
    """Remove every phone number (and one neighbouring '|'). Returns how many were removed."""
    removed = 0
    while True:
        match = PHONE_WITH_SEPARATOR.search(paragraph.text)
        if match is None:
            return removed
        start, end = match.span()
        if not re.search(SEPARATOR + r"$", match.group()):
            # No trailing '|' was consumed (phone was last): take the one before it instead.
            before = LEADING_SEPARATOR.search(paragraph.text[:start])
            if before:
                start = before.start()
        remove_span(paragraph, start, end)
        removed += 1


def all_paragraphs(document):
    """Body (including tables) plus every header and footer part."""
    yield from (Paragraph(p, document.part) for p in document.element.body.iter(qn("w:p")))
    for relationship in document.part.rels.values():
        if relationship.reltype.endswith(("/header", "/footer")):
            part = relationship.target_part
            yield from (Paragraph(p, part) for p in part.element.iter(qn("w:p")))


def redact(document):
    return sum(redact_paragraph(paragraph) for paragraph in all_paragraphs(document))


def leftover_phone_numbers(path):
    """Phone-like text still present in any XML part of the saved file (empty list = clean)."""
    found = []
    with zipfile.ZipFile(path) as archive:
        for name in archive.namelist():
            if not name.endswith((".xml", ".rels")):
                continue
            xml = archive.read(name).decode("utf8", errors="ignore")
            for paragraph in re.findall(r"<w:p[ >].*?</w:p>", xml, flags=re.S):
                text = "".join(re.findall(r"<w:t[^>]*>([^<]*)</w:t>", paragraph))
                found += [(name, m.group()) for m in re.finditer(PHONE, text)]
            found += [(name, m) for m in re.findall(r"tel:[^\"'<]+", xml)]
    return found


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("input")
    parser.add_argument("output")
    args = parser.parse_args(argv)

    document = Document(args.input)
    removed = redact(document)
    document.save(args.output)

    leftovers = leftover_phone_numbers(args.output)
    if leftovers:
        print(f"FAILED: phone numbers still present: {leftovers}", file=sys.stderr)
        return 1
    print(f"Removed {removed} phone number(s); re-scan of {args.output} is clean.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
