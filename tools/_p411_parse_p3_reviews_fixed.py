# -*- coding: utf-8 -*-
r"""精确解析 P3 审稿意见（修正跨行漏检）（2026-10-12）。

## 上一版的 bug

我用 `(?:^|\n)\s*(\d{1,2})\s*[.．]` 找编号条目 → **漏掉行末编号**
（如 `...visual question answering` 后换行接 `4. Table IV is qualitative only.`）。
结果 R2 报 3 条（实际 5 条）、R3 报 18 条（实际 23 条）。

**正确做法**：用 `\n\s*(\d{1,2})\s*[.．]\s+` **或** `\s(\d{1,2})\.\s+[A-Z]`，
并以"编号必须**连续**"为校验（缺号即漏检）。

    python tools\_p411_parse_p3_reviews_fixed.py [--apply]
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


def split_reviewers(t: str):
    marks = [(m.start(), m.group(1)) for m in re.finditer(r"Reviewer\s+(\d)", t)]
    marks.append((len(t), None))
    out = {}
    for i in range(len(marks) - 1):
        out[f"R{marks[i][1]}"] = t[marks[i][0]:marks[i + 1][0]]
    return out


def parse_items(seg: str):
    """找所有编号条目（容忍行内/行末编号）。"""
    # 编号后跟空格 + 大写字母或 `The`/`In`/`Could` 等（避免匹配 "0.14" 这类小数）
    pat = re.compile(r"(\d{1,2})\s*[.．]\s*(?=[A-Z\u201c\"(]|\bThe\b|\bIn\b)", re.M)
    hits = list(pat.finditer(seg))
    items = []
    for i, m in enumerate(hits):
        num = int(m.group(1))
        start = m.end()
        end = hits[i + 1].start() if i + 1 < len(hits) else len(seg)
        txt = " ".join(seg[start:end].split())
        items.append({"n": num, "text": txt[:400]})
    return items


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(SRC, encoding="utf-8", errors="replace").read()
    secs = split_reviewers(t)

    print("=" * 100)
    print("解析结果（以编号连续为校验）")
    print("=" * 100)
    rep = {}
    for name in ("R1", "R2", "R3"):
        seg = secs.get(name, "")
        if not seg:
            continue
        items = parse_items(seg)
        nums = [x["n"] for x in items]
        # 去重（同编号可能因跨页重复出现）
        seen, uniq = set(), []
        for x in items:
            if x["n"] in seen:
                continue
            seen.add(x["n"])
            uniq.append(x)
        uniq.sort(key=lambda x: x["n"])
        need = set(range(1, max(nums) + 1)) if nums else set()
        missing = sorted(need - set(nums))
        rep[name] = {"n_items": len(uniq), "max_n": max(nums) if nums else 0,
                     "missing": missing,
                     "items": uniq}
        flag = "✅ 连续" if not missing else f"🔴 缺号 {missing}"
        print(f"\n  {name}: 解析到 {len(uniq)} 条（最大编号 {max(nums) if nums else 0}）｜ {flag}")
        for x in uniq:
            print(f"     {x['n']:>2}. {x['text'][:135]}")

    total = sum(v["n_items"] for v in rep.values())
    print()
    print(f"  → 合计 **{total}** 条")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(
            {"source": "docs/_inbox/P3_reviews/_reviews.txt",
             "manuscript": "PRLETTERS-D-26-02378",
             "journal": "Pattern Recognition Letters",
             "decision": "Revise", "revision_deadline": "2026-11-02",
             "status_date": "2026-10-12", "editor": "Yonghuai Liu",
             "total_items": total, "by_reviewer": rep},
            ensure_ascii=False, indent=1))
        print(f"  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
