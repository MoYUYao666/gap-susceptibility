# -*- coding: utf-8 -*-
"""探测可用的引用核验数据源（一次性诊断脚本，可复跑）。

背景：本网络环境下
  - Crossref ✅ 稳定（期刊 + 部分会议；ML 会议论文常无 DOI）
  - arXiv **API** 被限流（间歇性 406）
  - OpenAlex / Semantic Scholar 间歇 429
  - DBLP 反爬
故需逐个实测，挑出可靠通道。

    python tools/_probe_citation_sources.py
"""
from __future__ import annotations

import re
import time
import urllib.request

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}


def get(url: str, headers: dict | None = None, timeout: int = 30) -> str:
    try:
        req = urllib.request.Request(url, headers=headers or UA)
        return urllib.request.urlopen(req, timeout=timeout).read().decode("utf-8", "ignore")
    except Exception as e:
        return f"ERR: {e}"


def probe_arxiv_html(ids: list[str]) -> None:
    print("=== arXiv abs 页面（HTML 通道，非 API）===")
    for aid in ids:
        r = get(f"https://arxiv.org/abs/{aid}")
        if r.startswith("ERR"):
            print(f"  {aid:<14} ❌ {r[:70]}")
            continue
        ti = re.search(r'<meta name="citation_title" content="(.*?)"', r)
        au = re.search(r'<meta name="citation_author" content="(.*?)"', r)
        dt = re.search(r'<meta name="citation_date" content="(.*?)"', r)
        print(f"  {aid:<14} ✅ | {(ti.group(1)[:56] if ti else '?')} | "
              f"{(au.group(1) if au else '?')} | {(dt.group(1) if dt else '?')}")
        time.sleep(1.5)


def probe_arxiv_api(terms: list[str]) -> None:
    print("\n=== arXiv API（判断限流是否持续）===")
    for t in terms:
        r = get(f"https://export.arxiv.org/api/query?search_query=all:{t}&max_results=2")
        n = len(re.findall(r"<entry>", r)) if not r.startswith("ERR") else 0
        print(f"  all:{t:<22} {'✅ entries=%d' % n if not r.startswith('ERR') else '❌ ' + r[:60]}")
        time.sleep(2)


def probe_openalex() -> None:
    print("\n=== OpenAlex（带 mailto）===")
    for u in ["https://api.openalex.org/works/doi:10.48550/arXiv.2106.09685?mailto=contact@example.com",
              "https://api.openalex.org/works?search=LoRA%20low-rank%20adaptation&per-page=2&mailto=contact@example.com"]:
        r = get(u, {"User-Agent": "citation-verify/1.0 (mailto:contact@example.com)"})
        ok = not r.startswith("ERR")
        print(f"  {'✅' if ok else '❌'} {u[:78]}… {'' if ok else r[:70]}")
        if ok:
            ti = re.search(r'"title":\s*"([^"]{0,70})"', r)
            yr = re.search(r'"publication_year":\s*(\d{4})', r)
            print(f"      首条: {ti.group(1) if ti else '?'} | {yr.group(1) if yr else '?'}")
        time.sleep(2)


def probe_semanticscholar() -> None:
    print("\n=== Semantic Scholar ===")
    u = ("https://api.semanticscholar.org/graph/v1/paper/search?query=LoRA+low-rank+adaptation"
         "&limit=2&fields=title,year,venue,externalIds")
    r = get(u, {"User-Agent": "citation-verify/1.0"})
    if r.startswith("ERR"):
        print(f"  ❌ {r[:80]}")
    else:
        print(f"  ✅ {r[:160]}")


if __name__ == "__main__":
    probe_arxiv_html(["2106.09685", "1902.00751", "2308.12966"])
    probe_arxiv_api(["electron", "LoRA", "low rank adaptation"])
    probe_openalex()
    probe_semanticscholar()
