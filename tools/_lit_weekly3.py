# -*- coding: utf-8 -*-
r"""每周文献检索（第三版：抓近期预印本 + 本地严格过滤）（2026-10-12）。

## 为什么再换

- OpenAlex `search=`：短语检索返回大量无关论文（太阳能/隧道）
- arXiv `abs:"A" AND abs:"B"`：多词字段查询**被 arXiv 当成 OR**（返回时间序列/ASR）

## 本版做法

**从权威源抓"近期全量候选"，再在本地用**严格正则**过滤**：
1. arXiv `cat:cs.CV` + `cat:cs.LG` 最近提交（各 ~300 条，按提交日倒序）
2. 本地过滤：摘要**同时**含（本稿核心词）与（任务词）
3. 输出候选 + 摘要首句，供人工判定关系

    python tools\_lit_weekly3.py [--apply]
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
OUT = REPO / "outputs" / "analysis" / "lit_weekly3.json"
NS = {"a": "http://www.w3.org/2005/Atom"}

# 本稿核心概念组（任一组命中即算"相关"）
CORE = [
    r"modality gap", r"modality[- ]gap", r"cross[- ]modal (mis)?align",
    r"order preservation", r"kendall", r"rank order",
]
TASK = [
    r"fine[- ]tun", r"parameter[- ]efficient", r"lora", r"adapter",
    r"zero[- ]shot", r"retrieval", r"clip",
]


def fetch(cat: str, n: int = 300, page: int = 100):
    out = []
    for start in range(0, n, page):
        url = ("http://export.arxiv.org/api/query?search_query="
               + urllib.parse.quote(f"cat:{cat}")
               + f"&start={start}&max_results={page}"
               "&sortBy=submittedDate&sortOrder=descending")
        req = urllib.request.Request(url, headers={"User-Agent": "lit-weekly/3.0"})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                root = ET.fromstring(r.read())
        except Exception as e:
            print(f"    ⚠ {cat} start={start}: {type(e).__name__}")
            break
        for e in root.findall("a:entry", NS):
            out.append({
                "id": (e.findtext("a:id", "", NS) or "").split("/abs/")[-1],
                "title": " ".join((e.findtext("a:title", "", NS) or "").split()),
                "published": (e.findtext("a:published", "", NS) or "")[:10],
                "authors": [a.findtext("a:name", "", NS)
                            for a in e.findall("a:author", NS)][:4],
                "summary": " ".join((e.findtext("a:summary", "", NS) or "").split()),
                "cat": cat,
            })
        time.sleep(3.2)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    pool = {}
    for cat in ("cs.CV", "cs.LG"):
        r = fetch(cat)
        print(f"  {cat}: 抓取 {len(r)} 条（{r[0]['published'] if r else '-'} … "
              f"{r[-1]['published'] if r else '-'}）")
        for w in r:
            pool[w["id"]] = w
    print(f"  去重后池 {len(pool)} 条")

    core_re = re.compile("|".join(CORE), re.I)
    task_re = re.compile("|".join(TASK), re.I)
    sel = []
    for w in pool.values():
        blob = w["title"] + " " + w["summary"]
        if core_re.search(blob) and task_re.search(blob):
            w["core_hits"] = sorted({m.group(0).lower()
                                     for m in core_re.finditer(blob)})
            w["task_hits"] = sorted({m.group(0).lower()
                                     for m in task_re.finditer(blob)})
            sel.append(w)

    sel.sort(key=lambda w: w["published"], reverse=True)
    print()
    print("=" * 96)
    print(f"过滤后候选: {len(sel)} 条（核心词 ∩ 任务词）")
    print("=" * 96)
    for w in sel:
        print(f"\n  [{w['published']}] {w['id']}  ({w['cat']})")
        print(f"     {w['title'][:94]}")
        print(f"     {', '.join(w['authors'])[:76]}")
        print(f"     核心: {','.join(w['core_hits'])[:60]} ｜ 任务: {','.join(w['task_hits'])[:50]}")
        print(f"     摘要: {w['summary'][:220]}…")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps({"pool": len(pool), "selected": sel},
                       ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}（池 {len(pool)}，候选 {len(sel)}）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
