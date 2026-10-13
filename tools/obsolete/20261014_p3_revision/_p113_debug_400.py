# -*- coding: utf-8 -*-
r"""诊断 OpenAlex 的 HTTP 400（含 `?` 的标题）+ 验证 hu2022lora 的假匹配（2026-10-10）。

    python tools\_p113_debug_400.py
"""
from __future__ import annotations

import io
import json
import urllib.parse
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
UA = "A1-ref-audit/1.0 (mailto:contact@example.com)"


def try_url(url: str, tag: str):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            d = json.loads(r.read().decode("utf-8"))
        n = d.get("meta", {}).get("count")
        print(f"  ✅ {tag}: count={n}")
        for w in (d.get("results") or [])[:2]:
            print(f"       • {(w.get('title') or '?')[:70]}")
        return True
    except Exception as e:
        print(f"  ❌ {tag}: {str(e)[:120]}")
        return False


def main() -> int:
    title = "When and why vision-language models behave like bags-of-words, and what to do about it?"
    print("=== ① 各种构造方式对比 ===")
    enc = urllib.parse.urlencode({"search": title, "per-page": 3})
    try_url(f"https://api.openalex.org/works?{enc}", "urlencode(search=)")
    try_url(f"https://api.openalex.org/works?search={urllib.parse.quote(title, safe='')}&per-page=3",
            "quote(safe='')")
    try_url(f"https://api.openalex.org/works?filter=title.search:{urllib.parse.quote(title, safe='')}&per-page=3",
            "filter=title.search")
    # 去掉问号
    t2 = title.rstrip("?")
    enc2 = urllib.parse.urlencode({"search": t2, "per-page": 3})
    try_url(f"https://api.openalex.org/works?{enc2}", "urlencode(去问号)")

    print("\n=== ② hu2022lora 的搜索返回了什么（判假匹配）===")
    q = urllib.parse.urlencode({"search": "LoRA: Low-rank adaptation of large language models",
                                "per-page": 6})
    req = urllib.request.Request(f"https://api.openalex.org/works?{q}",
                                 headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=40) as r:
        d = json.loads(r.read().decode("utf-8"))
    for w in d.get("results", []):
        au = w.get("authorships") or []
        print(f"   • {(w.get('title') or '?')[:74]}")
        print(f"       作者 {len(au)} 位 ｜ {w.get('publication_year')} ｜ {w.get('doi')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
