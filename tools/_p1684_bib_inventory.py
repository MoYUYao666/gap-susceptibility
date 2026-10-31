"""Inventory of paper合/references.bib (for the Paper A literature scan).

Prints every entry as: KEY | year | first author | title | doi, so a candidate found online can be
checked against what the manuscript already cites.

Usage: python tools/_p1684_bib_inventory.py [--csv <outfile>]
"""

from __future__ import annotations

import io
import re
import sys

BIB = "paper合/references.bib"


def field(body: str, name: str) -> str:
    m = re.search(r"\b" + name + r"\s*=\s*", body, re.I)
    if not m:
        return ""
    rest = body[m.end():].lstrip()
    if not rest:
        return ""
    if rest[0] == "{":
        depth = 0
        for i, ch in enumerate(rest):
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return re.sub(r"\s+", " ", rest[1:i]).strip()
    elif rest[0] == '"':
        end = rest.find('"', 1)
        return re.sub(r"\s+", " ", rest[1:end]).strip() if end > 0 else ""
    return ""


def main() -> int:
    text = io.open(BIB, encoding="utf-8").read()
    entries = re.findall(r"@(\w+)\s*\{\s*([^,]+),", text)
    print("entries:", len(entries))
    rows = []
    for typ, key in entries:
        start = text.find("{" + key)
        nxt = text.find("\n@", start)
        body = text[start:nxt if nxt > 0 else len(text)]
        title = field(body, "title")
        year = field(body, "year")
        author = field(body, "author")
        first = author.split(" and ")[0].strip() if author else ""
        doi = field(body, "doi")
        rows.append((key.strip(), typ, year, first, title, doi))
        print("%-24s %s  %-18s %s | %s" % (key.strip(), year or "????", first[:18], title[:88], doi[:40]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
