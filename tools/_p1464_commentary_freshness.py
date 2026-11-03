# -*- coding: utf-8 -*-
r"""Commentary: cite the 2026 evaluation-artifact study and rebuild the PDF.

Adds sun2026reading to paper_review_prl/_refs_used.json, inserts one sentence in section 3.2, and reruns the build script.

    python tools/_p1464_commentary_freshness.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MD = os.path.join(REPO, "paper_review_prl", "MANUSCRIPT.md")
REFS = os.path.join(REPO, "paper_review_prl", "_refs_used.json")
BUILD = os.path.join(REPO, "tools", "_build_prl_tex.py")
REF = {"key": "sun2026reading",
       "authors": "Kaiser Sun, Xiaochuang Yuan, Hongjun Liu, Chen Zhao, Cheng Zhang, Mark Dredze, Fan Bai",
       "title": "Reading, Not Thinking: Understanding and Bridging the Modality Gap When Text Becomes Pixels in "
                "Multimodal LLMs",
       "year": 2026, "venue": "arXiv", "arxiv": "2603.09095", "doi": "10.48550/arXiv.2603.09095"}
ANCHOR = "documented for multimodal benchmarks specifically [song2025bothleaked]."
SENT = (" The sensitivity is not limited to answer formats: when the same content is presented to a multimodal model as "
        "rendered pixels rather than as text, the measured gap depends on rendering choices such as font and resolution "
        "[sun2026reading], so the evaluation pipeline itself is part of the reported quantity.")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    changed = False
    d = json.load(io.open(REFS, encoding="utf-8"))
    if not any(r.get("key") == "sun2026reading" for r in d):
        d.append(REF)
        changed = True
        print("  reference added")
    t = io.open(MD, encoding="utf-8").read()
    if "sun2026reading" not in t:
        assert t.count(ANCHOR) == 1, t.count(ANCHOR)
        t = t.replace(ANCHOR, ANCHOR + SENT, 1)
        changed = True
        print("  citation sentence inserted")
    if a.apply and changed:
        io.open(REFS, "w", encoding="utf-8", newline="").write(json.dumps(d, indent=1, ensure_ascii=False))
        io.open(MD, "w", encoding="utf-8", newline="").write(t)
        print("  written")
        r = subprocess.run([sys.executable, BUILD], cwd=REPO, capture_output=True, text=True, encoding="utf-8",
                           errors="replace")
        print((r.stdout or "")[-1200:])
        print("build exit", r.returncode)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
