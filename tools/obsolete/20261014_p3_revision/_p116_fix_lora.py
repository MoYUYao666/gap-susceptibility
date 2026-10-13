# -*- coding: utf-8 -*-
r"""修 `hu2022lora`（我上一版按错误 DOI 填错了作者）（2026-10-10）。

## 我的错

我用 `10.48550/arXiv.2106.09685` 直查，返回了
**"LoRA Fine-Tuning of a 3B Code LLM for Algorithmic Efficiency"**（**另一篇论文**，
只是作者里有 J. Edward Hu）→ 我却把它当成了原版 LoRA 的作者列表。

**原版**是：*LoRA: Low-Rank Adaptation of Large Language Models*, ICLR 2022
（Hu, Shen, Wallis, Allen-Zhu, Li, Wang, Wang）。

**修法**：按「标题 + 作者姓」检索，并**用标题相似度校验**（≥0.90）才采用。

    python tools\_p116_fix_lora.py --apply
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
OUT = REPO / "outputs" / "analysis" / "a1_refs_openalex.json"
UA = "A1-ref-audit/1.0 (mailto:contact@example.com)"
TITLE = "LoRA: Low-rank adaptation of large language models"


def norm(s: str) -> str:
    s = re.sub(r"[^a-z0-9 ]", " ", (s or "").lower())
    return " ".join(s.split())


def get(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=45) as r:
        return json.loads(r.read().decode("utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    print("=== 检索：标题 + 作者 Hu ===")
    q = urllib.parse.urlencode({"search": f"{TITLE} Hu", "per-page": 10,
                                "mailto": "contact@example.com"})
    d = get(f"https://api.openalex.org/works?{q}")
    best, bs = None, 0.0
    for w in (d.get("results") or []):
        ct = w.get("title") or ""
        s = difflib.SequenceMatcher(None, norm(TITLE), norm(ct)).ratio()
        au = w.get("authorships") or []
        print(f"   [{s:.2f}] {ct[:66]} ｜ 作者 {len(au)} 位 ｜ {w.get('publication_year')}")
        if s > bs:
            best, bs = w, s

    if best is None or bs < 0.90:
        print(f"\n  ❌ 未找到可信匹配（最佳 {bs:.2f}）→ **保持 UNAVAILABLE，不采用**")
        if a.apply:
            res = json.loads(io.open(OUT, encoding="utf-8").read())
            for r in res:
                if r["key"] == "hu2022lora":
                    r.update({"method": "UNAVAILABLE", "authors": [],
                              "note": f"检索最佳相似度 {bs:.2f} < 0.90；"
                                      f"**不猜作者**（上一版误用了另一篇论文的作者）"})
            io.open(OUT, "w", encoding="utf-8", newline="").write(
                json.dumps(res, ensure_ascii=False, indent=1))
            print("  ✅ 已改回 UNAVAILABLE")
        return 0

    au = []
    for x in (best.get("authorships") or []):
        nm = (x.get("author") or {}).get("display_name", "")
        if nm:
            p = nm.split()
            au.append({"family": p[-1], "given": " ".join(p[:-1]), "display": nm})
    print(f"\n  ✅ 采用：{best.get('title')}")
    print(f"     作者 {len(au)} 位: {', '.join(x['display'] for x in au)}")

    if a.apply:
        res = json.loads(io.open(OUT, encoding="utf-8").read())
        for r in res:
            if r["key"] == "hu2022lora":
                r.update({"method": f"openalex({bs:.2f})", "similarity": round(bs, 3),
                          "openalex_id": best.get("id"),
                          "openalex_title": best.get("title"),
                          "year": best.get("publication_year"),
                          "n_authors": len(au), "authors": au})
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(res, ensure_ascii=False, indent=1))
        ok = sum(1 for r in res if r.get("authors"))
        print(f"\n  ✅ 已写（现 {ok}/{len(res)} 条有作者）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
