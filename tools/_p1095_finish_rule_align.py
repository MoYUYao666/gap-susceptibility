# -*- coding: utf-8 -*-
r"""Finish the rule change: remove the last "switch to a domestic source" leftovers and align the resume note.

Three things remain from the earlier "no HF" wording:

* point 5 of the execution list still says "then switch to a **domestic** source (not back to HF)";
* the resume note for tomorrow tells the reader to prefer ModelScope and to treat the operator's mirror
  instruction as merely one option -- which is now backwards.

    python tools/_p1095_finish_rule_align.py [--apply]
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
FILES = [REPO / "AGENTS.md", REPO / "CLAUDE.md"]
NOTE = REPO / "docs" / "resume_2026-10-17_llava_metric.md"

OLD5 = "5. **慢 ≠ 卡死**：连续 30–60 秒零增长才判定卡死，然后**换国内源**（不是换回 HF）；"
NEW5 = "5. **慢 ≠ 卡死**：连续 30–60 秒零增长才判定卡死；判卡死后**先测多连接**，再换源；"

NOTE_OLD = """2. weights: prefer `tools/_p1083_parallel_fetch.py` on ModelScope (proven 13-18 MB/s); note the "
                 "operator asked for the mirror, but the mirror measured 0.5 MB/s here, so report the conflict and "
                 "go with what the measurements say;"""
NOTE_NEW = """2. weights: **use the mirror first** -- `HF_ENDPOINT=https://hf-mirror.com` with "
                 "`HF_HOME=/root/autodl-tmp/hf` and `snapshot_download` (host 3: 15 GB in 6-8 min). If it is slow "
                 "on the new host, fall back to the multi-connection ModelScope fetcher "
                 "(`tools/_p1083_parallel_fetch.py`, proven 13-18 MB/s). Measure first, as the rule requires;"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  (dry run)")
        return 0
    for f in FILES:
        t = io.open(f, encoding="utf-8").read()
        if OLD5 in t:
            t = t.replace(OLD5, NEW5, 1)
            io.open(f, "w", encoding="utf-8", newline="").write(t)
            print(f"  {f.name}: execution point 5 aligned with the mirror-first rule")
        else:
            print(f"  {f.name}: point 5 not found")
    if NOTE.exists():
        t = io.open(NOTE, encoding="utf-8").read()
        if NOTE_OLD in t:
            t = t.replace(NOTE_OLD, NOTE_NEW, 1)
            io.open(NOTE, "w", encoding="utf-8", newline="").write(t)
            print("  resume note: mirror-first")
        else:
            print("  resume note: target text not found (already aligned?)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
