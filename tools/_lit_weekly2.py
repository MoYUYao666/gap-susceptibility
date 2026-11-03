# -*- coding: utf-8 -*-
r"""每周文献检索（改用 arXiv API）（2026-10-12）。

## 为什么换

OpenAlex 的 `search=` 对 "modality gap parameter-efficient fine-tuning" 这类**短语**
返回了大量无关论文（太阳能、隧道、放射报告…）→ **信噪比太低，不可用**。

**改用 arXiv API**（`export.arxiv.org/api/query`）：ML/CV 预印本覆盖最好，
且支持 `ti:` / `abs:` 字段限定。

## 检索式（字段限定，避免泛搜）

| # | 检索式 | 目的 |
|---|---|---|
| 1 | `abs:"modality gap" AND abs:"parameter-efficient"` | 直接竞争 |
| 2 | `abs:"modality gap" AND abs:"fine-tuning"` | 主战场 |
| 3 | `ti:"modality gap"` | 标题级 |
| 4 | `abs:"modality gap" AND abs:"dynamics"` | 动力学建模（本稿的 ODE） |
| 5 | `abs:"text-only" AND abs:"modality gap"` | 位置效应 |
| 6 | `abs:"adapter" AND abs:"modality gap"` | 适配器位置 |

    python tools\_lit_weekly2.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "lit_weekly_arxiv.json"
NS = {"a": "http://www.w3.org/2005/Atom"}

QUERIES = [
    'abs:"modality gap" AND abs:"parameter-efficient"',
    'abs:"modality gap" AND abs:"fine-tuning"',
    'ti:"modality gap"',
    'abs:"modality gap" AND abs:"dynamics"',
    'abs:"text-only" AND abs:"modality gap"',
    'abs:"adapter" AND abs:"modality gap"',
    'all:"order preservation" AND all:"zero-shot"',
]


def arxiv(q: str, n: int = 25):
    url = ("http://export.arxiv.org/api/query?search_query=" + urllib.parse.quote(q)
           + f"&start=0&max_results={n}&sortBy=submittedDate&sortOrder=descending")
    req = urllib.request.Request(url, headers={"User-Agent": "lit-weekly/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=45) as r:
            raw = r.read()
    except Exception as e:
        return {"error": f"{type(e).__name__}: {e}"}
    try:
        root = ET.fromstring(raw)
    except Exception as e:
        return {"error": f"XML: {e}"}
    out = []
    for e in root.findall("a:entry", NS):
        out.append({
            "id": (e.findtext("a:id", "", NS) or "").strip(),
            "title": " ".join((e.findtext("a:title", "", NS) or "").split()),
            "published": (e.findtext("a:published", "", NS) or "")[:10],
            "updated": (e.findtext("a:updated", "", NS) or "")[:10],
            "authors": [a.findtext("a:name", "", NS)
                        for a in e.findall("a:author", NS)][:4],
            "summary": " ".join((e.findtext("a:summary", "", NS) or "").split()),
        })
    return {"results": out}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    hits = {}
    for q in QUERIES:
        d = arxiv(q)
        if "error" in d:
            print(f"\n  🔴 「{q}」→ {d['error']}")
            continue
        res = d["results"]
        print(f"\n{'=' * 96}")
        print(f"「{q}」→ {len(res)} 条")
        print("=" * 96)
        for w in res:
            key = w["id"].split("/abs/")[-1]
            w["query"] = q
            hits[key] = w
            print(f"  [{w['published']}] {key}")
            print(f"     {w['title'][:92]}")
            print(f"     {', '.join(w['authors'])[:80]}")
        time.sleep(3.2)
    print()
    print("=" * 96)
    print(f"去重后共 {len(hits)} 条")
    print("=" * 96)
    recent = [v for v in hits.values() if v["published"] >= "2026-01-01"]
    print(f"  2026 年及以后: {len(recent)} 条")
    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(hits, ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
