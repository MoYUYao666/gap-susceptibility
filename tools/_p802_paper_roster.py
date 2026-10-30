# -*- coding: utf-8 -*-
r"""Collect every manuscript and its status, so the weekly literature task can cover all of them.

The existing reminder searches only for Paper A. Extending it needs the identifiers, targets and
states of the other papers, taken from the repository rather than from memory.

    python tools/_p802_paper_roster.py --apply
"""
from __future__ import annotations

import argparse
import io
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "paper_roster.json"

# directories that hold a manuscript
CANDIDATES = [
    ("paper合", "Paper A (P1+P2 merged)"),
    ("paper3/paper_ieee", "P3"),
    ("paper_a1", "A1"),
    ("paper_a2", "A23"),
    ("paper", "P1"),
    ("paper_a4", "A4"),
    ("备选/06_归档稿件/paper_ap3", "ap3 (archived)"),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    roster = []
    for rel, label in CANDIDATES:
        d = REPO / rel
        if not d.exists():
            continue
        info = {"path": rel, "label": label}
        # title and journal from the main tex files
        titles, journals = [], set()
        for f in list(d.glob("main*.tex"))[:6]:
            t = io.open(f, encoding="utf-8", errors="replace").read()
            m = re.search(r"\\title\{([^{}]{0,300})\}", t)
            if m:
                titles.append(" ".join(m.group(1).split()))
            for j in ("Neurocomputing", "Pattern Recognition Letters", "Pattern Recognition",
                      "IEEE Journal", "Elsevier", "elsarticle", "IEEEtran", "sn-jnl"):
                if j in t:
                    journals.add(j)
        # identifiers found anywhere in the tree
        ids = set()
        for f in list(d.rglob("*.tex"))[:40] + list(d.rglob("*.md"))[:20]:
            t = io.open(f, encoding="utf-8", errors="replace").read()
            for pat in (r"PRLETTERS-D-\d{2}-\d{4,5}R?\d?", r"PR-D-\d{2}-\d{5}",
                        r"NEUCOM-D-\d{2}-\d{5}", r"NEUNET-D-\d{2}-\d{5}", r"\b\d{2}-\d{4}\b"):
                ids.update(re.findall(pat, t))
        info["titles"] = titles[:2]
        info["journals"] = sorted(journals)
        info["ids"] = sorted(ids)[:8]
        # bib size
        bibs = list(d.rglob("*.bib"))
        info["bib_entries"] = sum(
            len(re.findall(r"^@", io.open(b, encoding="utf-8", errors="replace").read(), re.M))
            for b in bibs)
        info["bib_files"] = len(bibs)
        roster.append(info)

    for i in roster:
        print("=" * 104)
        print(f"{i['label']}   ({i['path']})")
        print("=" * 104)
        for t in i["titles"]:
            print(f"  title   : {t[:150]}")
        print(f"  ids     : {i['ids']}")
        print(f"  journal : {i['journals']}")
        print(f"  bib     : {i['bib_entries']} entries in {i['bib_files']} file(s)")
        print()

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(roster, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"  wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
