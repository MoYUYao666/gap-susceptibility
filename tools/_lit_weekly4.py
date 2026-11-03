# -*- coding: utf-8 -*-
r"""每周文献检索（第四版：抓 14 天全量 + 两级过滤 + 缓存）（2026-10-12）。

## 前几版的问题

| 版本 | 问题 |
|---|---|
| OpenAlex `search=` | 短语检索返回太阳能/隧道等无关论文 |
| arXiv `abs:"A" AND abs:"B"` | 多词字段查询被当成 OR |
| `_lit_weekly3` | 只抓 2 天（arXiv API 单次 300 上限）→ 池太小 |

## 本版

1. **分页抓 cs.CV / cs.LG 各 900 条**（覆盖约 1–2 周）
2. 缓存到 `outputs/analysis/lit_pool.json`（**重跑不重抓**）
3. **两级过滤**：
   - **A 级**（必报）：含 `modality gap` / `order preservation`（本稿专属概念）
   - **B 级**（相关）：含 `cross-modal align` / `kendall` 且含任务词

    python tools\_lit_weekly4.py [--apply] [--refetch]
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
POOL = REPO / "outputs" / "analysis" / "lit_pool.json"
OUT = REPO / "outputs" / "analysis" / "lit_weekly_report.json"
NS = {"a": "http://www.w3.org/2005/Atom"}

A_TERMS = [r"modality gap", r"order preservation", r"modality[- ]gap"]
B_TERMS = [r"cross[- ]modal (mis)?align", r"kendall", r"rank order",
           r"representation (collapse|drift)"]
TASK = [r"fine[- ]tun", r"parameter[- ]efficient", r"\blora\b", r"adapter",
        r"zero[- ]shot", r"retrieval", r"\bclip\b", r"vision[- ]language"]


def fetch(cat: str, want: int = 900, page: int = 100):
    out = []
    for start in range(0, want, page):
        url = ("http://export.arxiv.org/api/query?search_query="
               + urllib.parse.quote(f"cat:{cat}")
               + f"&start={start}&max_results={page}"
               "&sortBy=submittedDate&sortOrder=descending")
        req = urllib.request.Request(url, headers={"User-Agent": "lit-weekly/4.0"})
        ok = False
        for attempt in range(3):
            try:
                with urllib.request.urlopen(req, timeout=70) as r:
                    root = ET.fromstring(r.read())
                ok = True
                break
            except Exception as e:
                print(f"      ⚠ {cat} start={start} attempt {attempt + 1}: "
                      f"{type(e).__name__}")
                time.sleep(6)
        if not ok:
            break
        ents = root.findall("a:entry", NS)
        if not ents:
            break
        for e in ents:
            out.append({
                "id": (e.findtext("a:id", "", NS) or "").split("/abs/")[-1],
                "title": " ".join((e.findtext("a:title", "", NS) or "").split()),
                "published": (e.findtext("a:published", "", NS) or "")[:10],
                "authors": [a.findtext("a:name", "", NS)
                            for a in e.findall("a:author", NS)][:4],
                "summary": " ".join((e.findtext("a:summary", "", NS) or "").split()),
                "cat": cat,
            })
        print(f"      {cat} start={start}: +{len(ents)}（共 {len(out)}）")
        time.sleep(3.2)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--refetch", action="store_true")
    a = ap.parse_args()

    pool = {}
    if POOL.exists() and not a.refetch:
        pool = json.loads(io.open(POOL, encoding="utf-8", errors="replace").read())
        print(f"  ✅ 复用缓存 {POOL.relative_to(REPO)}：{len(pool)} 条")
    else:
        for cat in ("cs.CV", "cs.LG"):
            r = fetch(cat)
            for w in r:
                pool[w["id"]] = w
        print(f"  抓取完成：{len(pool)} 条")
        POOL.parent.mkdir(parents=True, exist_ok=True)
        io.open(POOL, "w", encoding="utf-8", newline="").write(
            json.dumps(pool, ensure_ascii=False, indent=1))

    vals = list(pool.values())
    dates = sorted({v["published"] for v in vals})
    print(f"  日期覆盖: {dates[0]} … {dates[-1]}（{len(dates)} 天）")

    a_re = re.compile("|".join(A_TERMS), re.I)
    b_re = re.compile("|".join(B_TERMS), re.I)
    t_re = re.compile("|".join(TASK), re.I)

    A, B = [], []
    for w in vals:
        blob = w["title"] + " " + w["summary"]
        ha = a_re.search(blob)
        hb = b_re.search(blob)
        ht = t_re.search(blob)
        if ha and ht:
            w["level"] = "A"
            w["hits"] = sorted({m.group(0).lower() for m in a_re.finditer(blob)})
            A.append(w)
        elif hb and ht:
            w["level"] = "B"
            w["hits"] = sorted({m.group(0).lower() for m in b_re.finditer(blob)})
            B.append(w)
    A.sort(key=lambda w: w["published"], reverse=True)
    B.sort(key=lambda w: w["published"], reverse=True)

    print()
    print("=" * 96)
    print(f"A 级（含 modality gap / order preservation + 任务词）: {len(A)} 条")
    print("=" * 96)
    for w in A:
        print(f"\n  [{w['published']}] {w['id']}  ({w['cat']})")
        print(f"     {w['title'][:94]}")
        print(f"     {', '.join(w['authors'])[:74]}")
        print(f"     命中: {','.join(w['hits'])[:60]}")
        print(f"     摘要: {w['summary'][:300]}…")
    print()
    print("=" * 96)
    print(f"B 级（cross-modal align 等 + 任务词）: {len(B)} 条（只列标题）")
    print("=" * 96)
    for w in B[:20]:
        print(f"  [{w['published']}] {w['id']}  {w['title'][:86]}")

    if a.apply:
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(
            {"pool_size": len(pool), "date_range": [dates[0], dates[-1]],
             "level_A": A, "level_B_count": len(B),
             "level_B": [{"id": w["id"], "title": w["title"],
                          "published": w["published"]} for w in B]},
            ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
