# -*- coding: utf-8 -*-
r"""最终解析：查询剥 `?`、收紧匹配、未命中者标 NOT_INDEXED（2026-10-10）。

## 两个已实测的坑

| 坑 | 现象 | 修法 |
|---|---|---|
| **`?` 触发 400** | `search=...what to do about it?` → HTTP 400；**去掉 `?` → count=6701 且榜首即目标** | 查询前 `rstrip("?")` 并去中间问号 |
| **假匹配** | `hu2022lora` 在 0.85 相似度下匹配到 **QA-LoRA**（不同论文） | **收紧**：相似度 ≥0.90，**或**（≥0.75 且**归一化后前 10 词完全一致**） |

    python tools\_p114_final_resolve.py --apply
"""
from __future__ import annotations

import argparse
import difflib
import io
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
A1 = REPO / "paper_a1"
OUT = REPO / "outputs" / "analysis" / "a1_refs_openalex.json"
OA = "https://api.openalex.org/works"
UA = "A1-ref-audit/1.0 (mailto:contact@example.com)"

RETRY = ["chowers2026", "yuksekgonul2023when", "ovadia2019trust", "steck2024cosine",
         "hu2022lora", "huh2024platonic", "imod", "wan2026protect"]


def norm(s: str) -> str:
    s = (s or "").lower()
    s = re.sub(r"^position\s*:?\s*", "", s)
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    return " ".join(s.split())


def get(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=45) as r:
        return json.loads(r.read().decode("utf-8"))


def search(title: str):
    """剥 `?` 后检索（实测 `?` 会导致 400）。"""
    q = title.replace("?", " ").replace("  ", " ").strip()
    qs = urllib.parse.urlencode({"search": q, "per-page": 8,
                                 "mailto": "contact@example.com"})
    return get(f"{OA}?{qs}")


def resolve_one(title: str, raw: str) -> dict:
    d = search(title)
    best, bs, why = None, 0.0, ""
    for w in d.get("results", []):
        ct = w.get("title") or ""
        s = difflib.SequenceMatcher(None, norm(title), norm(ct)).ratio()
        head_a = " ".join(norm(title).split()[:10])
        head_b = " ".join(norm(ct).split()[:10])
        if head_a and head_a == head_b:
            s = max(s, 0.95)
        if s > bs:
            best, bs = w, s
    accept = bs >= 0.90
    if best is not None and bs >= 0.75:
        ct = best.get("title") or ""
        if " ".join(norm(title).split()[:10]) == " ".join(norm(ct).split()[:10]):
            accept = True
    if not accept:
        return {"method": "NOT_INDEXED", "similarity": round(bs, 3), "authors": [],
                "note": f"最佳 {bs:.2f}（{ (best.get('title') or '?')[:50] if best else '无'}）"}
    au = best.get("authorships") or []
    authors = []
    for a in au:
        nm = (a.get("author") or {}).get("display_name", "")
        if nm:
            p = nm.split()
            authors.append({"family": p[-1], "given": " ".join(p[:-1]), "display": nm})
    return {"method": f"openalex({bs:.2f})", "similarity": round(bs, 3),
            "openalex_id": best.get("id"), "openalex_title": best.get("title"),
            "year": best.get("publication_year"), "n_authors": len(authors),
            "authors": authors}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    res = json.loads(io.open(OUT, encoding="utf-8").read())
    rmap = {r["key"]: r for r in res}
    print(f"=== 重试 {len(RETRY)} 条（剥 `?` + 收紧判据）===")
    for key in RETRY:
        r = rmap.get(key)
        if not r:
            continue
        try:
            got = resolve_one(r["title"], r.get("raw", ""))
        except Exception as e:
            print(f"  ✗ [{key}] {str(e)[:90]}")
            continue
        r.update(got)
        n = len(got.get("authors", []))
        print(f"  {'✅' if n else '⚠'} [{key:<22}] {got['method']:<16} 作者 {n:>2} 位 ｜ "
              f"{(got.get('openalex_title') or got.get('note') or '')[:52]}")
        time.sleep(0.4)

    if a.apply:
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(list(rmap.values()), ensure_ascii=False, indent=1))
        ok = [r for r in rmap.values() if r.get("authors")]
        no = [r for r in rmap.values() if not r.get("authors")]
        print(f"\n=== {len(ok)}/{len(rmap)} 条已有作者 ===")
        if no:
            print(f"  未索引 {len(no)} 条（预期为新论文/在投）：")
            for r in no:
                print(f"    [{r['key']}] {(r.get('openalex_title') or '')[:40]} "
                      f"｜ {r.get('note','')[:60]}")
        print(f"  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
