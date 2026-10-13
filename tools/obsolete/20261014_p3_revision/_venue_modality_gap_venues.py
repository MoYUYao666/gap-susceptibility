# -*- coding: utf-8 -*-
r"""标题级精确反查：**"modality gap" 类论文实际发在哪**（2026-10-07，选项 3 第 2 轮）。

## 为什么再换方法

`_venue_reverse_lookup.py` 用 `search=`（全文松匹配）→ 总命中 **3–4 万**，
说明匹配过宽，**venue 计数不可信**（与第 3 轮同样的病）。

## 本轮改用 `title.search=`（**只在标题里匹配**）

标题含 "modality gap" 的论文**一定属于本文这一支**（不论其形态），
其 venue 分布可回答：**这支工作实际发在哪些刊**。

    python tools\_venue_modality_gap_venues.py [--apply]
"""
from __future__ import annotations

import collections
import io
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "modality_gap_venues.json"

FREE = {
    "neurocomputing", "pattern recognition letters", "pattern recognition",
    "image and vision computing", "computer vision and image understanding",
    "neural networks", "expert systems with applications", "information fusion",
    "knowledge-based systems",
}

TITLE_QUERIES = [
    "modality gap",
    "cross-modal alignment",
    "parameter-efficient fine-tuning",
]


def fetch(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "title-lookup/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


def main() -> int:
    apply = "--apply" in sys.argv
    res = {}
    for q in TITLE_QUERIES:
        url = (f"https://api.openalex.org/works?filter=title.search:{urllib.parse.quote(q)},"
               f"from_publication_date:2023-01-01,type:article"
               f"&per-page=200&select=id,title,publication_year,primary_location")
        try:
            d = fetch(url)
        except Exception as e:
            print(f"  [{q}] ❌ {e}")
            continue
        tot = d.get("meta", {}).get("count", 0)
        venues, papers = collections.Counter(), []
        for w in d.get("results", []):
            pl = w.get("primary_location") or {}
            src = pl.get("source") or {}
            name = (src.get("display_name") or "(unknown)").strip()
            venues[name] += 1
            papers.append({"y": w.get("publication_year"), "v": name,
                           "t": (w.get("title") or "")[:150]})
        res[q] = {"total": tot, "venues": venues.most_common(30), "papers": papers[:60]}
        print("=" * 98)
        print(f"  【title.search = {q!r}】总命中 {tot}（取前 200 篇统计）")
        print("=" * 98)
        for name, n in venues.most_common(14):
            tag = "  🆓免APC" if name.lower() in FREE else ""
            print(f"    {n:>4}  {name[:66]}{tag}")
        print()
        time.sleep(0.3)
    if apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(res, ensure_ascii=False, indent=1))
        print(f"  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
