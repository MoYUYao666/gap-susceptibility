# -*- coding: utf-8 -*-
r"""批量查全 A1 的 **56 条**参考文献作者名单（APA 转换的前置）（2026-10-10）。

## 方法（**可核、不猜**）

1. 从 `main.tex` + `related_work_bibitems.tex` 抽出每条：**key / 标题 / DOI（若有）**；
2. **优先按 DOI 查 Crossref**（`works/{doi}`）→ 精确；
3. 无 DOI 者按**标题检索**（`query.bibliographic`）→ **用标题相似度校验**，
   **相似度 < 阈值则标为 UNRESOLVED，不强行采用**；
4. 每条结果**落盘**（含来源、匹配方式、相似度）→ 可复核。

**输出**：`outputs/analysis/a1_refs_resolved.json`

    python tools\_p108_resolve_authors.py [--apply] [--limit N]
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
OUT = REPO / "outputs" / "analysis" / "a1_refs_resolved.json"
API = "https://api.crossref.org/works"
UA = "A1-ref-audit/1.0 (mailto:hw4c24@soton.ac.uk)"
THRESH = 0.90


def norm(s: str) -> str:
    s = re.sub(r"[^a-z0-9 ]", " ", (s or "").lower())
    return " ".join(s.split())


def extract(src: str, tag: str):
    """抽出 (key, title, doi, raw)。"""
    out = []
    for m in re.finditer(r"\\bibitem(?:\[[^\]]*\])?\{([^}]*)\}\s*(.*?)(?=\\bibitem|$)",
                         src, re.S):
        key, body = m.group(1), " ".join(m.group(2).split())
        t = re.search(r"``(.+?)''", body)
        title = t.group(1).rstrip(".,") if t else ""
        d = re.search(r"DOI:\s*(10\.[^\s.,]+)", body)
        doi = d.group(1).rstrip(".") if d else ""
        if not doi:
            d2 = re.search(r"arXiv[:\s]*(?:abs/)?(\d{4}\.\d{4,5})", body)
            if d2:
                doi = f"10.48550/arXiv.{d2.group(1)}"
        out.append({"source": tag, "key": key, "title": title, "doi": doi,
                    "raw": body[:300]})
    return out


def get(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=45) as r:
        return json.loads(r.read().decode("utf-8"))


def authors_of(item) -> list:
    return [{"family": a.get("family", ""), "given": a.get("given", "")}
            for a in (item.get("author") or [])]


def resolve(rec: dict) -> dict:
    # ① DOI 直查
    if rec["doi"]:
        try:
            d = get(f"{API}/{urllib.parse.quote(rec['doi'])}")
            it = d["message"]
            return {**rec, "method": "doi", "similarity": 1.0,
                    "authors": authors_of(it),
                    "year": (it.get("issued", {}).get("date-parts") or [[""]])[0][0],
                    "crossref_title": (it.get("title") or [""])[0],
                    "doi_found": it.get("DOI")}
        except Exception as e:
            rec["doi_error"] = str(e)[:100]
    # ② 标题检索 + 相似度校验
    if rec["title"]:
        try:
            q = urllib.parse.urlencode({"query.bibliographic": rec["title"], "rows": 5})
            d = get(f"{API}?{q}")
            best, bs = None, 0.0
            for it in d.get("message", {}).get("items", []):
                ct = (it.get("title") or [""])[0]
                s = difflib.SequenceMatcher(None, norm(rec["title"]), norm(ct)).ratio()
                if s > bs:
                    best, bs = it, s
            if best is not None and bs >= THRESH:
                return {**rec, "method": f"title({bs:.2f})", "similarity": bs,
                        "authors": authors_of(best),
                        "year": (best.get("issued", {}).get("date-parts") or [[""]])[0][0],
                        "crossref_title": (best.get("title") or [""])[0],
                        "doi_found": best.get("DOI")}
            return {**rec, "method": "UNRESOLVED", "similarity": bs,
                    "authors": [], "note": f"最佳相似度 {bs:.2f} < {THRESH}"}
        except Exception as e:
            return {**rec, "method": "ERROR", "authors": [], "error": str(e)[:120]}
    return {**rec, "method": "NO_TITLE", "authors": []}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()

    recs = extract(io.open(A1 / "main.tex", encoding="utf-8", errors="replace").read(), "main")
    extra_f = A1 / "related_work_bibitems.tex"
    if extra_f.exists():
        recs += extract(io.open(extra_f, encoding="utf-8", errors="replace").read(), "related_work")
    # 去重（按 key）
    seen, uniq = set(), []
    for r in recs:
        if r["key"] in seen:
            continue
        seen.add(r["key"])
        uniq.append(r)
    print(f"=== 共 {len(uniq)} 条待查（去重后）===")
    if a.limit:
        uniq = uniq[:a.limit]
        print(f"  （限 {a.limit} 条）")

    if not a.apply:
        for r in uniq[:6]:
            print(f"  [{r['key']}] doi={r['doi'] or '—'} ｜ title={r['title'][:70]}")
        print("  （预演；加 --apply 实跑）")
        return 0

    resolved = []
    for i, r in enumerate(uniq, 1):
        got = resolve(r)
        resolved.append(got)
        n = len(got.get("authors", []))
        print(f"  {i:>2}/{len(uniq)} [{got['key']:<22}] {got['method']:<14} "
              f"作者 {n:>2} 位 ｜ {got.get('crossref_title','')[:44]}", flush=True)
        time.sleep(0.6)
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(resolved, ensure_ascii=False, indent=1))

    ok = [r for r in resolved if r.get("authors")]
    bad = [r for r in resolved if not r.get("authors")]
    print(f"\n=== 结果：{len(ok)}/{len(resolved)} 条拿到作者 ===")
    if bad:
        print(f"  未解决 {len(bad)} 条：")
        for r in bad:
            print(f"    [{r['key']}] {r['method']} ｜ {r.get('note') or r.get('error','')}")
    print(f"  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
