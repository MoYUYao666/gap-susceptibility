# -*- coding: utf-8 -*-
r"""核 B 级候选与 `paper合/references.bib` 的关系（2026-10-12）。

**纪律**：不得凭标题推断内容 → 逐条读**摘要**；并查 bib 是否已收录。

    python tools\_lit_verify.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
POOL = REPO / "outputs" / "analysis" / "lit_pool.json"
BIB = REPO / "paper合" / "references.bib"
OUT = REPO / "outputs" / "analysis" / "lit_verify.json"

CANDIDATES = [
    "2610.09411v2",   # Shared Geometry As A Rosetta Stone
    "2610.11113v1",   # DiscoVL
    "2610.11526v1",   # MSGAT
    "2610.09863v1",   # Global Average Precision
    "2610.09227v1",   # Quantize by Drift
    "2610.06226v1",   # LeAVJEPA
]


def norm(s):
    return re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    pool = json.loads(io.open(POOL, encoding="utf-8", errors="replace").read())
    bib = io.open(BIB, encoding="utf-8", errors="replace").read() if BIB.exists() else ""
    bib_titles = {}
    for m in re.finditer(r"@\w+\{([^,]+),\s*(.*?)\n\}", bib, re.S):
        key, body = m.group(1).strip(), m.group(2)
        t = re.search(r"title\s*=\s*\{(.*?)\}", body, re.S)
        if t:
            bib_titles[norm(t.group(1))] = key
        # 也收 arxiv 编号
        for ax in re.findall(r"arXiv[:\s]*(\d{4}\.\d{4,5})", body, re.I):
            bib_titles["arxiv:" + ax] = key

    print("=" * 96)
    print("逐条核（读摘要 + 查 bib）")
    print("=" * 96)
    out = []
    for cid in CANDIDATES:
        w = pool.get(cid)
        if not w:
            print(f"\n  🔴 {cid}：池中无（编号可能已更新版本）")
            continue
        ax = cid.split("v")[0]
        in_bib = bib_titles.get("arxiv:" + ax) or bib_titles.get(norm(w["title"]))
        print(f"\n  ── {cid} ──")
        print(f"     标题: {w['title']}")
        print(f"     作者: {', '.join(w['authors'])} ｜ {w['published']}")
        print(f"     bib 中: {'✅ 已收录 key=' + in_bib if in_bib else '❌ 未收录'}")
        print(f"     摘要全文:")
        import textwrap
        for line in textwrap.wrap(w["summary"], 92):
            print(f"       {line}")
        out.append({"id": cid, "title": w["title"], "authors": w["authors"],
                    "published": w["published"], "in_bib": in_bib,
                    "summary": w["summary"]})
    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(out, ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
