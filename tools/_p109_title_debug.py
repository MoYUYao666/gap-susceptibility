# -*- coding: utf-8 -*-
r"""诊断标题检索为何失效（2026-10-10）。

    python tools\_p109_title_debug.py
"""
from __future__ import annotations

import difflib
import io
import json
import re
import urllib.parse
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
API = "https://api.crossref.org/works"
UA = "A1-ref-audit/1.0 (mailto:hw4c24@soton.ac.uk)"


def norm(s: str) -> str:
    s = re.sub(r"[^a-z0-9 ]", " ", (s or "").lower())
    return " ".join(s.split())


def get(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=45) as r:
        return json.loads(r.read().decode("utf-8"))


def main() -> int:
    # 从 bibitems 抽真实标题（验证抽取是否正确）
    src = io.open(REPO / "paper_a1" / "main.tex", encoding="utf-8",
                  errors="replace").read()
    print("=== 抽取到的标题（前 4 条）===")
    titles = []
    for m in re.finditer(r"\\bibitem(?:\[[^\]]*\])?\{([^}]*)\}\s*(.*?)(?=\\bibitem|$)",
                         src, re.S):
        key, body = m.group(1), " ".join(m.group(2).split())
        t = re.search(r"``(.+?)''", body)
        title = t.group(1) if t else "(无)"
        titles.append((key, title))
        if len(titles) <= 4:
            print(f"  [{key}] {title[:100]}")

    print("\n=== 对 radford2021 做标题检索，列出全部候选 ===")
    key, title = titles[1] if len(titles) > 1 else ("?", "Learning transferable visual models")
    q = urllib.parse.urlencode({"query.bibliographic": title, "rows": 6})
    d = get(f"{API}?{q}")
    items = d.get("message", {}).get("items", [])
    print(f"  查询: {title[:90]}")
    print(f"  返回 {len(items)} 条：")
    for it in items:
        ct = (it.get("title") or ["?"])[0]
        s = difflib.SequenceMatcher(None, norm(title), norm(ct)).ratio()
        au = it.get("author") or []
        print(f"   • [{s:.2f}] {ct[:78]}")
        print(f"        DOI {it.get('DOI')} ｜ {it.get('type')} ｜ 作者 {len(au)} 位")

    print("\n=== 试 OpenAlex（会议论文覆盖更好）===")
    try:
        q2 = urllib.parse.urlencode({"search": title, "per-page": 3})
        req = urllib.request.Request(f"https://api.openalex.org/works?{q2}",
                                     headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=45) as r:
            oa = json.loads(r.read().decode("utf-8"))
        for w in oa.get("results", [])[:3]:
            au = w.get("authorships") or []
            print(f"   • {w.get('title','?')[:78]}")
            print(f"        DOI {w.get('doi')} ｜ 作者 {len(au)} 位 ｜ "
                  f"{w.get('publication_year')}")
            if au:
                print("        前 3:", "; ".join(
                    a.get("author", {}).get("display_name", "?") for a in au[:3]))
    except Exception as e:
        print(f"   ❌ OpenAlex 失败: {str(e)[:160]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
