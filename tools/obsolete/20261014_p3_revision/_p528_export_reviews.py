# -*- coding: utf-8 -*-
r"""导出 33 条意见的结构化文本（供撰写正式回复信）（2026-10-13）。

    python tools\_p528_export_reviews.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "docs" / "P3_REVIEW_RESPONSE.md"
OUT = REPO / "outputs" / "analysis" / "p3_reviews_structured.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(SRC, encoding="utf-8", errors="replace").read()
    pat = re.compile(r"#### (R\d+\.\d+) — ([^\n]*)\n\n> ([^\n]*(?:\n> [^\n]*)*)\n\n\*\*建议动作\*\*：([^\n]*)")
    items = []
    for m in pat.finditer(t):
        rid, kind, quote, act = m.group(1), m.group(2), m.group(3), m.group(4)
        q = quote.replace("> ", "").strip()
        q = re.sub(r"\s*\n\s*", " ", q)
        items.append({"id": rid, "kind": kind.strip(), "comment": q, "suggested_action": act.strip()})
    print(f"  导出 {len(items)} 条")
    byrev = {}
    for it in items:
        byrev.setdefault(it["id"].split(".")[0], []).append(it)
    for k in sorted(byrev):
        print(f"     {k}: {len(byrev[k])} 条")
    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(items, ensure_ascii=False, indent=1))
        print(f"  ✅ 已写 {OUT.relative_to(REPO)}")
    # 打印全部意见全文（供撰写）
    print()
    for it in items:
        print(f"[{it['id']}] ({it['kind']})")
        print(f"  {it['comment']}")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
