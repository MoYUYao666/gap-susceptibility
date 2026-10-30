# -*- coding: utf-8 -*-
r"""解析并落账 P3（`PRLETTERS-D-26-02378`）的审稿意见，生成逐条应答骨架（2026-10-12）。

## 决定

- **期刊**：Pattern Recognition Letters
- **决定**：**Revise**（可修改后重审）
- **提交**：Sep 28, 2026 ｜ **状态日期**：Oct 12, 2026 ｜ **修订截止**：**Nov 02, 2026**
- **编辑**：Yonghuai Liu（Editor-in-Chief）
- **总评**：*"clarity of technical details and sufficiency of experimental studies"*
- **要求**：**在 EM 平台逐条 reply to reviews**（"you must respond to reviews in our peer review platform"）

    python tools\_p410_parse_p3_reviews.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "docs" / "_inbox" / "P3_reviews" / "_reviews.txt"
OUT = REPO / "outputs" / "analysis" / "p3_reviews_parsed.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not SRC.exists():
        print("  🔴 审稿意见文本不存在")
        return 1
    t = io.open(SRC, encoding="utf-8", errors="replace").read()

    # 按 "Reviewer N" 切段
    marks = [(m.start(), m.group(0)) for m in re.finditer(r"Reviewer\s+(\d)", t)]
    marks.append((len(t), "END"))
    sections = {}
    for i in range(len(marks) - 1):
        name = f"R{marks[i][1].split()[-1]}"
        seg = t[marks[i][0]:marks[i + 1][0]]
        sections.setdefault(name, "")
        sections[name] += seg

    print("=" * 100)
    print("审稿意见条目统计")
    print("=" * 100)
    rep = {}
    for name in ("R1", "R2", "R3"):
        seg = sections.get(name, "")
        if not seg:
            continue
        # 编号条目：行首 "N." 或 "N.The"
        items = re.findall(r"(?:^|\n)\s*(\d{1,2})\s*[.．]\s*(.{0,220})", seg, re.S)
        # 去重（同一编号可能因换行出现多次）
        seen, uniq = set(), []
        for num, txt in items:
            if num in seen:
                continue
            seen.add(num)
            uniq.append((int(num), " ".join(txt.split())))
        uniq.sort()
        rep[name] = {"n_items": len(uniq),
                     "items": [{"n": n, "text": x} for n, x in uniq]}
        print(f"\n  {name}: {len(uniq)} 条")
        for n, x in uniq:
            print(f"     {n:>2}. {x[:150]}")

    total = sum(v["n_items"] for v in rep.values())
    print()
    print(f"  → 合计 **{total}** 条（R1 {rep.get('R1',{}).get('n_items',0)} ｜ "
          f"R2 {rep.get('R2',{}).get('n_items',0)} ｜ R3 {rep.get('R3',{}).get('n_items',0)}）")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(
            {"source": "docs/_inbox/P3_reviews/_reviews.txt",
             "manuscript": "PRLETTERS-D-26-02378",
             "decision": "Revise", "revision_deadline": "2026-11-02",
             "editor": "Yonghuai Liu",
             "total_items": total, "by_reviewer": rep},
            ensure_ascii=False, indent=1))
        print(f"  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
