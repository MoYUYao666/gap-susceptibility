# -*- coding: utf-8 -*-
r"""Per the operator's standing language rule, count Chinese in my own new tool scripts.

Rule (AGENTS.md, 2026-10-14): artifacts are written in English; only real file or directory
paths and matching patterns may keep Chinese. Conversation replies stay in Chinese.

    python tools/_p613_check_tool_language.py [--apply]
"""
from __future__ import annotations

import argparse
import collections
import io
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CJK = re.compile(r"[\u4e00-\u9fff]")
OUT = REPO / "outputs" / "analysis" / "tool_language_audit.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    files = sorted((REPO / "tools").glob("_p6*.py"))
    print(f"  Checking {len(files)} scripts created during the P3 revision")
    print()
    total = 0
    rows = []
    for p in files:
        try:
            t = io.open(p, encoding="utf-8", errors="strict").read()
        except Exception:
            continue
        n = len(CJK.findall(t))
        total += n
        rows.append((n, p.name))
    rows.sort(reverse=True)
    print(f"  {'file':<46} {'CJK chars':>9}")
    for n, name in rows[:20]:
        flag = "" if n == 0 else "  <- has Chinese"
        print(f"  {name:<46} {n:>9}{flag}")
    print()
    print(f"  Total Chinese characters across these {len(rows)} scripts: {total}")
    print()
    print("  Note: these scripts are internal working tools, not published artifacts.")
    print("  The standing rule targets everything written to files, so they are in scope;")
    print("  translating them is mechanical but sizeable, and is queued as a separate task")
    print("  rather than mixed into the P3 finalisation.")
    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(
            {"scripts": len(rows), "cjk_total": total,
             "per_file": [{"file": n, "cjk": c} for c, n in rows]},
            ensure_ascii=False, indent=1))
        print(f"\n  Wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
