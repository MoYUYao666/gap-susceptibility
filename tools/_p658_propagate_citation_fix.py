# -*- coding: utf-8 -*-
r"""Propagate the citation repairs to every copy of the response material.

The three fixes were applied by hand to the two _plain.txt files; the same sentences appear in
the Markdown twins and in the combined letter, which must not diverge from what is pasted.

    python tools/_p658_propagate_citation_fix.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RESP = REPO / "SUBMISSION" / "P3_PRL_revision" / "response"
DOCS = REPO / "docs" / "P3_RESPONSE_LETTER.md"

PAIRS = [
    ("analysis in docs/P3_DOWNSTREAM.md.",
     "the downstream tables are in the supplementary material."),
    (":: rows[*].device; docs/P3_STATS.md.",
     ":: rows[*].device."),
    ("per-run protocol blocks; assertion in tools/_p434_alloc_train.py.",
     "assertion recorded in each per-run protocol block under outputs/analysis/p3_alloc_runs/."),
    (":: measured_n_trainable_params and the\nper-run protocol blocks; assertion in tools/_p434_alloc_train.py.",
     ":: measured_n_trainable_params, and the\nassertion recorded in each per-run protocol block under outputs/analysis/p3_alloc_runs/."),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    total = 0
    for p in sorted(list(RESP.glob("*")) + [DOCS]):
        if not p.is_file() or p.suffix.lower() not in (".txt", ".md"):
            continue
        t = io.open(p, encoding="utf-8", errors="replace").read()
        t2, n = t, 0
        for old, new in PAIRS:
            c = t2.count(old)
            if c:
                t2 = t2.replace(old, new)
                n += c
        if n:
            total += n
            print(f"  {p.name:<46} {n} replacement(s)")
            if a.apply:
                bak = p.with_suffix(p.suffix + ".bak_p658")
                if not bak.exists():
                    shutil.copy2(p, bak)
                io.open(p, "w", encoding="utf-8", newline="").write(t2)
    print(f"  total {total}")
    print()
    print("  Re-check across all response files:")
    bad = 0
    for p in sorted(list(RESP.glob("*")) + [DOCS]):
        if not p.is_file() or p.suffix.lower() not in (".txt", ".md"):
            continue
        t = io.open(p, encoding="utf-8", errors="replace").read()
        hits = [k for k in ("docs/P3_DOWNSTREAM", "docs/P3_STATS", "docs/P3_EXPERIMENTS",
                            "tools/_p434") if k in t]
        if hits:
            print(f"    BAD {p.name:<44} {hits}")
            bad += 1
    print(f"    {bad} file(s) still cite internal paths")
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
