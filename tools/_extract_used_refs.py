# -*- coding: utf-8 -*-
r"""从 MANUSCRIPT.md 抽取**当前实际引用**的 key，生成 `_refs_used.json`（供 build 生成参考文献）。

为什么单独做成脚本：build 曾读一份手写的 `_refs_used.json`，正文后来加了 20 条引用而该文件未更新，
导致编译出的 PDF 有 20 处未定义引用（参考文献表只有 26 条）。**改为每次从正文抽取，消除这类漂移。**

    python tools/_extract_used_refs.py
"""
from __future__ import annotations

import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MD = REPO / "paper_review_prl" / "MANUSCRIPT.md"
REFS = REPO / "paper_review" / "refs_all.json"
OUT = REPO / "paper_review_prl" / "_refs_used.json"

KEY = re.compile(r"^[a-z][a-z0-9_]*\d[a-z0-9_]*$")


def main() -> int:
    text = MD.read_text(encoding="utf-8")
    # 所有 [a; b, c] 形式的方括号引用（排除 markdown 链接与表格）
    keys: set[str] = set()
    for m in re.finditer(r"\[([^\]\[]+)\]", text):
        inner = m.group(1)
        if "://" in inner or "](" in inner:
            continue
        for part in re.split(r"[;,]", inner):
            k = part.strip()
            if KEY.match(k):
                keys.add(k)

    db = {e.get("key"): e for e in json.loads(REFS.read_text(encoding="utf-8"))}
    missing = sorted(k for k in keys if k not in db)
    rows = []
    for k in sorted(keys):
        e = db.get(k)
        if not e:
            continue
        au = e.get("authors") or []
        au_s = ", ".join(str(a) for a in au[:6]) + (" et al." if len(au) > 6 else "")
        rows.append({"key": k, "authors": au_s, "title": e.get("title"), "year": e.get("year"),
                     "venue": e.get("venue"), "doi": e.get("doi"), "arxiv": e.get("arxiv_id")})

    OUT.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"正文引用 key: {len(keys)}｜库中命中: {len(rows)}｜缺失: {len(missing)}")
    if missing:
        print(f"  ❌ 缺失（会在 PDF 里变成未定义引用）: {missing}")
    print(f"写出 {OUT.relative_to(REPO)}")
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
