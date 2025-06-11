
from __future__ import annotations
import re
from typing import Dict, List

# Regex that finds the FIRST http/https URL anywhere in the line
_URL_RE = re.compile(r"https?://[^\s)>\]]+")

# Grab the part of the Markdown file that is the table body
_TABLE_RE = re.compile(
    r"^\| *Company *\|.*?\n"     # header row
    r"\|[-:| ]+\|\n"             # separator row (---|---|---)
    r"(.*?)"                     # group 1 = body rows
    r"\n\n",                     # table ends with a blank line
    re.S | re.M,
)

def _parse_row(raw_line: str) -> Dict[str, str]:
    """
    Turn one Markdown‑table row into a dict with company, role, and link.
    Handles rows that begin with “↳” as well.
    """
    # Split on vertical bars, but keep empty cells so indexes stay stable
    cells = [c.strip() for c in raw_line.strip().lstrip("|").rstrip("|").split("|")]

    # Skip header lines or garbage
    if len(cells) < 5 or cells[0].lower() == "company":
        raise ValueError("not a data row")

    # Some indented rows start the company cell with the unicode arrow ↳
    company = cells[0].lstrip("↳").strip() or cells[0].strip()

    role    = cells[1]

    link_cell = cells[3]  # “Application/Link” column in the repo
    m = _URL_RE.search(link_cell)
    if not m:
        raise ValueError(f"no URL found in: {link_cell!r}")
    link = m.group(0)

    return {"company": company, "role": role, "link": link}


def parse(md_text: str) -> List[Dict[str, str]]:
    """Extract every internship row from the whole README.md."""
    m = _TABLE_RE.search(md_text)
    if not m:
        raise RuntimeError("Could not find internship table in README.md")

    body_lines = [ln for ln in m.group(1).splitlines() if ln.strip()]
    rows: List[Dict[str, str]] = []
    for ln in body_lines:
        try:
            rows.append(_parse_row(ln))
        except ValueError:
            # silently skip malformed or header lines
            continue
    return rows
