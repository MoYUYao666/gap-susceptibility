# -*- coding: utf-8 -*-
r"""修 4 类解析失败：URL 编码 + 标题归一化（2026-10-10）。

## 两类根因（实测）

| 类 | 条目 | 原因 | 修法 |
|---|---|---|---|
| **HTTP 400** | `chowers2026`、`yuksekgonul2023when`、`ovadia2019trust`、`steck2024cosine` | 标题含 `?`（`?` 后 URL 被截断） | 用 `urlencode` 对 `search=` 做**完整 percent-encode** |
| **相似度低** | `hu2022lora`（0.82）、`huh2024platonic`（0.75） | 归一化未处理 `LoRA:`/`Position:` 前缀与冒号 | 归一化时**去冒号、去前导 `position`**、再用**双阈值**（≥0.80 且首 8 词匹配即接受） |

**仍无法解决的（预期）**：`imod`（CVPR 2026）、`wan2026protect`（在投，无公开记录）
→ **标为 `NOT_INDEXED`，不猜作者**。

    python tools\_p112_fix_unresolved.py --apply
"""
from __future__ import annotations

import argparse
import difflib
import io
import json
import re
import sys
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
    s = re.sub(r"^position\s*:?\s*", "", s)      # 去 "Position:" 前缀
    s = re.sub(r"[^a-z0-9 ]", " ", s)            # 去冒号/问号/撇号等
    return " ".join(s.split())


def get(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=45) as r:
        return json.loads(r.read().decode("utf-8"))


def resolve_one(title: str) -> dict:
    # **关键修法**：search 用 urlencode（百分号编码），不手拼
    qs = urllib.parse.urlencode({"search": title, "per-page": 8,
                                 "mailto": "contact@example.com"})
    d = get(f"{OA}?{qs}")
    best, bs = None, 0.0
    for w in d.get("results", []):
        ct = w.get("title") or ""
        s = difflib.SequenceMatcher(None, norm(title), norm(ct)).ratio()
        # 双阈值：相似度 ≥0.80 **或** 归一化后的前 8 词完全一致
        head_a = " ".join(norm(title).split()[:8])
        head_b = " ".join(norm(ct).split()[:8])
        if head_a and head_a == head_b:
            s = max(s, 0.95)
        if s > bs:
            best, bs = w, s
    if best is None or bs < 0.80:
        return {"method": "NOT_INDEXED", "similarity": round(bs, 3), "authors": [],
                "note": f"最佳相似度 {bs:.2f}；疑似新论文或未收录"}
    au = best.get("authorships") or []
    authors = []
    for a in au:
        nm = (a.get("author") or {}).get("display_name", "")
        if not nm:
            continue
        parts = nm.split()
        authors.append({"family": parts[-1], "given": " ".join(parts[:-1]),
                        "display": nm})
    return {"method": f"openalex({bs:.2f})", "similarity": round(bs, 3),
            "openalex_id": best.get("id"), "openalex_title": best.get("title"),
            "year": best.get("publication_year"), "n_authors": len(authors),
            "authors": authors}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    src = ""
    for f in (A1 / "main.tex", A1 / "related_work_bibitems.tex"):
        if f.exists():
            src += io.open(f, encoding="utf-8", errors="replace").read()
    res = json.loads(io.open(OUT, encoding="utf-8").read())
    rmap = {r["key"]: r for r in res}

    print(f"=== 重试 {len(RETRY)} 条 ===")
    for key in RETRY:
        r = rmap.get(key)
        if not r:
            print(f"  ✗ [{key}] 不在结果文件中")
            continue
        try:
            got = resolve_one(r["title"])
        except Exception as e:
            print(f"  ✗ [{key}] 请求失败 {str(e)[:90]}")
            r["method"] = "ERROR"
            r["error"] = str(e)[:120]
            continue
        r.update(got)
        n = len(got.get("authors", []))
        flag = "✅" if n else "⚠"
        print(f"  {flag} [{key:<22}] {got['method']:<16} 作者 {n:>2} 位 ｜ "
              f"{(got.get('openalex_title') or '')[:44]}")

    if a.apply:
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(list(rmap.values()), ensure_ascii=False, indent=1))
        ok = sum(1 for r in rmap.values() if r.get("authors"))
        print(f"\n=== 现 {ok}/{len(rmap)} 条已有作者 ===")
        print(f"  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
