# -*- coding: utf-8 -*-
r"""拉取 Pattern Recognition Letters 近年的综述/评论类文章，建立"同类稿件规格"基准。

用途：回答"本文还缺什么"时用**已发表同类文章的实测数据**，而不是凭感觉。
量化指标是**参考文献条数**（Crossref 提供 reference-count）——PRL 的 7 页上限把所有稿件
篇幅压平，参考文献数是区分"综述"与"短评"最直接的可得信号。

    python tools/_benchmark_prl_reviews.py
"""
from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "paper_review_prl" / "benchmark_prl_reviews.md"
UA = "citation-verify/1.0 (mailto:contact@example.com)"
OURS = 35


def fetch(url: str) -> dict | None:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        return json.loads(urllib.request.urlopen(req, timeout=45).read().decode("utf-8", "ignore"))
    except Exception as e:
        print("  取数失败:", e)
        return None


def main() -> int:
    seen: dict[str, dict] = {}
    for q in ["review", "survey", "critical review", "overview", "tutorial", "systematic review"]:
        url = ("https://api.crossref.org/journals/0167-8655/works?"
               f"query.bibliographic={urllib.parse.quote(q)}&filter=from-pub-date:2022-01-01&rows=100")
        d = fetch(url)
        if not d:
            continue
        for it in d.get("message", {}).get("items", []):
            t = (it.get("title") or [""])[0]
            if t and re.search(r"\b(review|survey|overview|tutorial)\b", t, re.I):
                seen[it["DOI"]] = it

    items = sorted(seen.values(), key=lambda x: -(x.get("reference-count") or 0))
    rows = []
    print(f"命中综述/评论类文章 {len(items)} 篇（PRL，2022 起）\n")
    print(f"{'年份':<6}{'引用数':>7}  标题")
    print("-" * 90)
    for it in items:
        yr = ((it.get("issued") or {}).get("date-parts") or [[None]])[0][0]
        rc = it.get("reference-count")
        title = (it.get("title") or [""])[0]
        print(f"{str(yr):<6}{str(rc):>7}  {title[:62]}")
        rows.append((yr, rc, title, it["DOI"]))

    refs = sorted(r[1] for r in rows if isinstance(r[1], int) and r[1] > 0)
    summary = []
    if refs:
        n = len(refs)
        med = refs[n // 2] if n % 2 else (refs[n // 2 - 1] + refs[n // 2]) // 2
        q1, q3 = refs[n // 4], refs[(3 * n) // 4]
        print(f"\n引用数：n={n}｜中位 {med}｜四分位 {q1}–{q3}｜范围 {min(refs)}–{max(refs)}")
        verdict = ("✅ 落在四分位区间内" if q1 <= OURS <= q3
                   else ("⚠️ 低于下四分位，建议补足" if OURS < q1 else "高于上四分位"))
        print(f"本文 {OURS} 条 → {verdict}")
        summary = [f"**引用数**：已发表同类 n={n}，中位 **{med}**，四分位 **{q1}–{q3}**，"
                   f"范围 {min(refs)}–{max(refs)}；**本文 {OURS} 条 → {verdict}**"]

    lines = ["# PRL 综述/评论类文章对标（Crossref 拉取，2022 起）", "",
             f"命中 **{len(items)}** 篇；按参考文献数降序。", ""]
    lines += summary + ["", "| 年 | 引用数 | 标题 | DOI |", "|---|---|---|---|"]
    lines += [f"| {yr} | {rc} | {title[:70]} | `{doi}` |" for yr, rc, title, doi in rows]
    lines += ["", "> 为什么只看参考文献数：PRL 的 7 页上限把所有稿件篇幅压平，"
                  "参考文献数是区分综述与短评最直接的可得信号。",
              "> 数据源：Crossref `reference-count`（出版商存入的计数）。"]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n写出 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
