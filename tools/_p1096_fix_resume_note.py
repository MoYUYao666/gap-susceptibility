# -*- coding: utf-8 -*-
r"""Point the resume note's step 2 at the mirror, matching the operator's rule change.

The note still said to prefer ModelScope and to treat the mirror instruction as a conflict to report. The rule
is now mirror-first, so the step is rewritten; the measured caveat stays, because the rule itself says to
measure first.

    python tools/_p1096_fix_resume_note.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
NOTE = REPO / "docs" / "resume_2026-10-17_llava_metric.md"

NEW_STEP = ("2. weights: **mirror first** -- `HF_ENDPOINT=https://hf-mirror.com`, "
            "`HF_HOME=/root/autodl-tmp/hf`, then `snapshot_download('llava-hf/llava-1.5-7b-hf')` "
            "(host 3: 15 GB in 6-8 min). If it is slow on the new host, fall back to the multi-connection "
            "ModelScope fetcher (`tools/_p1083_parallel_fetch.py`, proven 13-18 MB/s). Measure first, as the "
            "rule requires -- the mirror gave 0.5 MB/s on the 2026-10-16 host and 30-40 MB/s on host 3;")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(NOTE, encoding="utf-8").read()
    if "mirror first" in t:
        print("  already mirror-first")
        return 0
    m = re.search(r"^2\. weights:.*$", t, re.M)
    assert m, "step 2 not found"
    t = t[:m.start()] + NEW_STEP + t[m.end():]
    if not a.apply:
        print("  (dry run)")
        return 0
    io.open(NOTE, "w", encoding="utf-8", newline="").write(t)
    print("  resume note: step 2 now mirror-first")
    check = io.open(NOTE, encoding="utf-8").read()
    print("  verify:", "mirror first" in check, "| still says prefer ModelScope:",
          "prefer `tools/_p1083_parallel_fetch.py` on ModelScope" in check)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
