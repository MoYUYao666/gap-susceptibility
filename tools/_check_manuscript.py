# -*- coding: utf-8 -*-
r"""稿件自检：字数、引用 key 是否都在库中、是否引用了作者自己的在审工作。

    python tools/_check_manuscript.py paper_review_prl/MANUSCRIPT.md
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
REFS = REPO / "paper_review" / "refs_all.json"


def main() -> int:
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO / "paper_review_prl" / "MANUSCRIPT.md"
    text = src.read_text(encoding="utf-8")
    refs = {e.get("key"): e for e in json.loads(REFS.read_text(encoding="utf-8"))}

    # 去掉 markdown 标题/引用块等非正文行，统计正文词数
    body_lines = [l for l in text.splitlines()
                  if l.strip() and not l.startswith(("#", ">", "|", "```", "---"))]
    body = " ".join(body_lines)
    words = len([w for w in re.split(r"\s+", body) if re.search(r"[A-Za-z]", w)])

    # 引用：形如 [key] 或 [k1; k2]
    keys: list[str] = []
    for m in re.finditer(r"\[([a-z][a-z0-9_]*\d[a-z0-9_]*)(?:\s*[;,]\s*([a-z][a-z0-9_]*\d[a-z0-9_]*))*\]", text):
        seg = m.group(0)[1:-1]
        for part in re.split(r"[;,]", seg):
            k = part.strip()
            if k:
                keys.append(k)
    # 补充：多 key 括号内的其余 key
    for m in re.finditer(r"\[([^\]]+)\]", text):
        for part in re.split(r"[;,]", m.group(1)):
            k = part.strip()
            if re.match(r"^[a-z][a-z0-9_]*\d[a-z0-9_]*$", k) and k not in keys:
                keys.append(k)

    uniq = sorted(set(keys))
    missing = [k for k in uniq if k not in refs]

    print(f"稿件: {src.name}")
    print(f"  正文词数（去标题/表格行）: {words}")
    print(f"  引用条目数（去重）      : {len(uniq)}")
    print(f"  引用键是否都在库中      : {'✅ 全部命中' if not missing else '❌ 缺失 ' + str(missing)}")

    # 自查自引：作者本人（Hongrui Wan）
    self_cites = []
    for k in uniq:
        e = refs.get(k) or {}
        for a in (e.get("authors") or []):
            if re.search(r"\bHongrui\b", str(a)):
                self_cites.append(k)
    print(f"  是否引用作者在审工作    : {'✅ 无' if not self_cites else '❌ ' + str(self_cites)}")

    # 预算对照（SPEC.md 实测：~4000 词 + ~50 引用）
    print()
    print("  预算对照（SPEC.md 实测：≈4,000 词正文 + ≈50 引用 = 7 页）")
    print(f"    词数: {words} → {'✅ 在预算内' if words <= 4200 else '⚠️ 超预算 ' + str(words - 4200) + ' 词'}")
    print(f"    引用: {len(uniq)} → {'✅ 在预算内' if len(uniq) <= 60 else '⚠️ 超预算'}")
    return 1 if (missing or self_cites) else 0


if __name__ == "__main__":
    raise SystemExit(main())
