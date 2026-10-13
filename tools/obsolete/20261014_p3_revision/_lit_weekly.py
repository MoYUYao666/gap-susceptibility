# -*- coding: utf-8 -*-
r"""每周文献检索：Paper A（`paper合/`）（2026-10-12）。

## 纪律（本项目硬要求）

1. **先查 bib**：避免把已在 `paper合/references.bib` 里的条目误报为"新论文"。
2. **不得凭标题推断内容**——必须读到**摘要**再判关系。
3. **核实存在**：Crossref / OpenAlex / arXiv abs。
4. 新增条目只写能核实的字段。

## 本脚本

① 列出 `references.bib` 的既有条目（标题 + 第一作者）
② 对 7 个检索式跑 OpenAlex（**注意：query 里带 `?` 会 HTTP 400，须去掉**）
③ 输出候选（标题 + DOI + 年份 + 摘要首句）

    python tools\_lit_weekly.py [--apply]
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
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
BIB = REPO / "paper合" / "references.bib"
OUT = REPO / "outputs" / "analysis" / "lit_weekly_2026-10-12.json"
MAILTO = "contact@example.com"   # 正确邮箱（曾把 hrw1n24 写错）

QUERIES = [
    "modality gap parameter-efficient fine-tuning",
    "text-only fine-tuning modality gap CLIP frozen vision encoder",
    "adapter placement LoRA text versus vision encoder retrieval",
    "modality gap dynamics ordinary differential equation gradient flow",
    "modality gap pretraining data comparison WIT LAION",
    "gap reduction does not improve retrieval vision-language",
    "cross-modal alignment theory PEFT",
]


def openalex(q: str, per_page: int = 12):
    url = ("https://api.openalex.org/works?search=" + urllib.parse.quote(q)
           + f"&per_page={per_page}&sort=publication_date:desc&mailto={MAILTO}")
    req = urllib.request.Request(url, headers={"User-Agent": f"lit-weekly ({MAILTO})"})
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            return json.loads(r.read().decode("utf-8", "replace"))
    except Exception as e:
        return {"error": f"{type(e).__name__}: {e}"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    # ① 既有 bib
    print("=" * 94)
    print("① paper合/references.bib 既有条目")
    print("=" * 94)
    existing = {}
    if BIB.exists():
        t = io.open(BIB, encoding="utf-8", errors="replace").read()
        for m in re.finditer(r"@\w+\{([^,]+),\s*(.*?)\n\}", t, re.S):
            key, body = m.group(1).strip(), m.group(2)
            title = re.search(r"title\s*=\s*\{(.*?)\}", body, re.S)
            yr = re.search(r"year\s*=\s*\{?(\d{4})", body)
            au = re.search(r"author\s*=\s*\{(.*?)\}", body, re.S)
            existing[key.lower()] = {
                "title": " ".join(title.group(1).split()) if title else "",
                "year": yr.group(1) if yr else "",
                "author": (" ".join(au.group(1).split())[:60] if au else ""),
            }
        print(f"  共 {len(existing)} 条")
        for k in sorted(existing)[:50]:
            v = existing[k]
            print(f"    {k:<26} {v['year']:<6} {v['title'][:64]}")

    # ② 检索
    print()
    print("=" * 94)
    print("② OpenAlex 检索（去掉 query 里的 '?' 以免 HTTP 400）")
    print("=" * 94)
    allhits = {}
    for q in QUERIES:
        d = openalex(q)
        if "error" in d:
            print(f"\n  🔴 「{q}」→ {d['error']}")
            continue
        res = d.get("results", [])
        print(f"\n  ── 「{q}」（{len(res)} 条）──")
        for w in res:
            wid = (w.get("doi") or w.get("id") or "").replace("https://doi.org/", "")
            ti = w.get("title") or ""
            yr = (w.get("publication_date") or "")[:4]
            auth = ((w.get("authorships") or [{}])[0].get("author") or {}).get(
                "display_name", "")
            key = wid.lower() or ti.lower()[:40]
            allhits[key] = {"doi": wid, "title": ti, "year": yr, "author": auth,
                            "query": q,
                            "abstract": (w.get("abstract_inverted_index") is not None)}
            print(f"    [{yr}] {ti[:88]}")
            print(f"          {auth[:40]:<40} {wid[:46]}")
        time.sleep(1.2)

    print()
    print("=" * 94)
    print("③ 汇总")
    print("=" * 94)
    print(f"  去重候选 {len(allhits)} 条")
    # 与既有 bib 标题粗比对
    def norm(s):
        return re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()
    bib_titles = {norm(v["title"]) for v in existing.values() if v["title"]}
    dup, new = [], []
    for k, v in allhits.items():
        n = norm(v["title"])
        (dup if n and n in bib_titles else new).append(v)
    print(f"  与 bib 标题**完全一致**（已在引用）: {len(dup)}")
    for v in dup[:8]:
        print(f"    ✓ {v['title'][:80]}")
    print(f"  可能为新: {len(new)}")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(
            {"existing_bib_keys": sorted(existing), "hits": allhits,
             "already_cited": [v["title"] for v in dup]},
            ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
