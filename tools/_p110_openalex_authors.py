# -*- coding: utf-8 -*-
r"""用 **OpenAlex** 查全 A1 的 56 条作者名单（Crossref 对 ML 会议论文覆盖差）（2026-10-10）。

## 实测依据

| 源 | `radford2021`（CLIP） | 判定 |
|---|---|---|
| Crossref 标题检索 | 返回鱼类分类/手术视频等**无关**论文（最高相似度 0.77） | ❌ 覆盖差 |
| **OpenAlex** | **精确命中，12 位作者** | ✅ |

**故：OpenAlex 为主，Crossref 仅用于有 DOI 的条目做交叉核对。**

## 方法（可核、不猜）

1. 抽 key / 标题 / DOI（**修掉尾部逗号**）；
2. OpenAlex `search=` 标题 → 取最相似候选；
3. **相似度 ≥ 0.90 才采用**，否则标 `UNRESOLVED`（不强行采用）；
4. 每条落盘：来源、相似度、OpenAlex ID、作者列表、年份 → 可复核。

    python tools\_p110_openalex_authors.py --apply
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
UA = "A1-ref-audit/1.0 (mailto:hw4c24@soton.ac.uk)"
THRESH = 0.90


def norm(s: str) -> str:
    s = re.sub(r"[^a-z0-9 ]", " ", (s or "").lower())
    return " ".join(s.split())


def extract(src: str, tag: str):
    out = []
    for m in re.finditer(r"\\bibitem(?:\[[^\]]*\])?\{([^}]*)\}\s*(.*?)(?=\\bibitem|$)",
                         src, re.S):
        key, body = m.group(1), " ".join(m.group(2).split())
        t = re.search(r"``(.+?)''", body)
        title = t.group(1).strip().rstrip(".,;") if t else ""
        d = re.search(r"DOI:\s*(10\.[^\s.,]+)", body)
        doi = d.group(1).rstrip(".") if d else ""
        out.append({"source": tag, "key": key, "title": title, "doi": doi,
                    "raw": body[:320]})
    return out


def get(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=45) as r:
        return json.loads(r.read().decode("utf-8"))


def resolve(rec: dict) -> dict:
    if not rec["title"]:
        return {**rec, "method": "NO_TITLE", "authors": []}
    try:
        q = urllib.parse.urlencode({"search": rec["title"], "per-page": 5,
                                    "mailto": "hw4c24@soton.ac.uk"})
        d = get(f"{OA}?{q}")
    except Exception as e:
        return {**rec, "method": "ERROR", "authors": [], "error": str(e)[:140]}
    best, bs = None, 0.0
    for w in d.get("results", []):
        s = difflib.SequenceMatcher(None, norm(rec["title"]),
                                    norm(w.get("title") or "")).ratio()
        if s > bs:
            best, bs = w, s
    if best is None or bs < THRESH:
        return {**rec, "method": "UNRESOLVED", "similarity": round(bs, 3),
                "authors": [], "note": f"最佳相似度 {bs:.2f} < {THRESH}"}
    au = best.get("authorships") or []
    authors = []
    for a in au:
        nm = (a.get("author") or {}).get("display_name", "")
        if not nm:
            continue
        parts = nm.split()
        family = parts[-1]
        given = " ".join(parts[:-1])
        authors.append({"family": family, "given": given, "display": nm})
    return {**rec, "method": f"openalex({bs:.2f})", "similarity": round(bs, 3),
            "openalex_id": best.get("id"), "openalex_title": best.get("title"),
            "year": best.get("publication_year"), "n_authors": len(authors),
            "authors": authors}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()

    recs = extract(io.open(A1 / "main.tex", encoding="utf-8", errors="replace").read(), "main")
    f2 = A1 / "related_work_bibitems.tex"
    if f2.exists():
        recs += extract(io.open(f2, encoding="utf-8", errors="replace").read(),
                        "related_work")
    seen, uniq = set(), []
    for r in recs:
        if r["key"] not in seen:
            seen.add(r["key"])
            uniq.append(r)
    print(f"=== {len(uniq)} 条待查 ===")
    if a.limit:
        uniq = uniq[:a.limit]

    if not a.apply:
        for r in uniq[:5]:
            print(f"  [{r['key']}] {r['title'][:78]}")
        print("  （预演）")
        return 0

    resolved = []
    for i, r in enumerate(uniq, 1):
        got = resolve(r)
        resolved.append(got)
        print(f"  {i:>2}/{len(uniq)} [{got['key']:<24}] {got['method']:<16} "
              f"作者 {len(got.get('authors', [])):>2} 位 ｜ "
              f"{(got.get('openalex_title') or '')[:40]}", flush=True)
        time.sleep(0.4)
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(resolved, ensure_ascii=False, indent=1))

    ok = [r for r in resolved if r.get("authors")]
    bad = [r for r in resolved if not r.get("authors")]
    print(f"\n=== {len(ok)}/{len(resolved)} 条拿到作者 ===")
    for r in bad:
        print(f"  ✗ [{r['key']}] {r['method']} ｜ {r.get('note') or r.get('error','')[:80]}")
    print(f"  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
