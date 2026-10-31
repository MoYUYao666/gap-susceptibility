# -*- coding: utf-8 -*-
r"""Clarify and extend the language rule, then scope the tool-script translation.

Operator (2026-10-14), in Chinese: all future experiment outputs and results are to be
written in English, while replies addressed to the operator stay in Chinese.

Interpretation recorded here:

| Artifact | Language |
|---|---|
| code, comments, docstrings, print/argparse messages | English |
| result JSONs (keys and values) | English |
| reports, checklists, READMEs | English |
| manuscripts | English |
| **handoff documents** (`HANDOFF.md`, `文件地图.md`, `docs/` working notes) | **Chinese** - they exist to report to the operator, who reads Chinese |
| conversation replies | Chinese |
| real file/directory names, matching patterns | keep as-is |

    python tools/_p614_scope_tool_translation.py [--apply]
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
OUT = REPO / "outputs" / "analysis" / "tool_translation_scope.json"


def bucket(name: str) -> str:
    m = re.match(r"^_p(\d+)", name)
    if not m:
        return "unclassified"
    k = int(m.group(1))
    if k >= 600:
        return "P3 revision, session tools (_p6xx)"
    if k >= 400:
        return "P3 revision (_p4xx-_p5xx)"
    if k >= 100:
        return "earlier papers (_p1xx-_p3xx)"
    return "early (_p0xx)"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    files = sorted((REPO / "tools").glob("*.py"))
    b = collections.Counter()
    bc = collections.Counter()
    names = collections.defaultdict(list)
    for p in files:
        try:
            t = io.open(p, encoding="utf-8", errors="strict").read()
        except Exception:
            continue
        c = len(CJK.findall(t))
        if not c:
            continue
        k = bucket(p.name)
        b[k] += 1
        bc[k] += c
        names[k].append((c, p.name))
    print(f"  tools/*.py total: {len(files)}")
    print()
    print(f"  {'bucket':<34} {'files':>6} {'CJK chars':>10}")
    for k in sorted(b, key=lambda x: -bc[x]):
        print(f"  {k:<34} {b[k]:>6} {bc[k]:>10,}")
    print()
    print(f"  TOTAL with Chinese: {sum(b.values())} files / {sum(bc.values()):,} chars")

    # priority: P3-revision scripts that are still in the working tree
    pri = []
    for k in ("P3 revision, session tools (_p6xx)", "P3 revision (_p4xx-_p5xx)"):
        pri += names.get(k, [])
    pri.sort(reverse=True)
    print()
    print(f"  Priority set (P3 revision, {len(pri)} files / {sum(c for c, _ in pri):,} chars):")
    for c, n in pri[:15]:
        print(f"    {c:>5}  {n}")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(
            {"buckets": {k: {"files": b[k], "cjk": bc[k]} for k in b},
             "total_files": sum(b.values()), "total_cjk": sum(bc.values()),
             "priority": [{"file": n, "cjk": c} for c, n in pri]},
            ensure_ascii=False, indent=1))
        print(f"\n  Wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
