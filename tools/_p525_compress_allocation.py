# -*- coding: utf-8 -*-
r"""算各节的"可移出余量"，给出达到 ≤7 页的分配（2026-10-13）。

## 依据（`tools/_p524`）

**必留 21,700 + 固定开销 8,400 = 30,100 字符 ≈ 5.4 页**；**7 页 = 39,194 字符**
⇒ **可移出内容只需 ≤ 9,094 字符**。

    python tools\_p525_compress_allocation.py --apply
"""
from __future__ import annotations

import argparse
import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PI = REPO / "paper3" / "paper_ieee"
OUT = REPO / "outputs" / "analysis" / "p3_compress_allocation.json"

# 各节"必留"的估计（依据 `_p524` 的 MUST 表分摊）
MUST = {
    "theory": 7300,          # R1–R5+R3′+反例、定理/推论、两种预算口径、β 出处、bracketed 口径
    "experiments": 10500,    # 逐块 Γ 表、同预算对比、AdaLoRA、随机池、blank 3.09×、下游否证、零样本
    "discussion": 2400,      # 6 条 limitation 结论 + 三处已修口径
    "conclusion": 1000,      # 四处已修 + 诚实口径 + 定位句
    "introduction": 900,     # 贡献列表 + R3′ 限定 + 定位
    "related_work": 700,     # 与先前工作的差异
}
FIXED_OVERHEAD = 8, 400   # 标题/摘要/关键词/声明 + 3 图 + 表


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    files = {
        "introduction": "sections/introduction.tex",
        "related_work": "sections/related_work.tex",
        "theory": "sections/theory.tex",
        "experiments": "sections/experiments.tex",
        "discussion": "sections/discussion.tex",
        "conclusion": "sections/conclusion.tex",
    }
    cur = {}
    for k, f in files.items():
        cur[k] = len(io.open(PI / f, encoding="utf-8", errors="replace").read())
    total = sum(cur.values())
    overhead = 2600 + 3 * 1600 + 1000
    budget = 39194

    print("=" * 100)
    print("各节：现状 / 必留 / 可移出余量")
    print("=" * 100)
    print(f"  {'节':<15} {'现状':>8} {'必留':>8} {'余量':>8} {'余量占比':>9}")
    movable_total = 0
    for k in files:
        mv = cur[k] - MUST[k]
        movable_total += mv
        print(f"  {k:<15} {cur[k]:>8,} {MUST[k]:>8,} {mv:>8,} "
              f"{100 * mv / cur[k]:>8.1f}%")
    print(f"  {'-' * 92}")
    print(f"  {'合计':<15} {total:>8,} {sum(MUST.values()):>8,} {movable_total:>8,}")
    print(f"  固定开销（标题/摘要/图/表）     {overhead:>8,}")
    print()
    print(f"  必留 + 开销 = **{sum(MUST.values()) + overhead:,} 字符**")
    print(f"  7 页预算     = **{budget:,} 字符**")
    avail = budget - sum(MUST.values()) - overhead
    print(f"  ⇒ **可移出额度 = {avail:,} 字符**（可移出总量 {movable_total:,}）")
    print()
    if movable_total <= avail:
        print(f"  ✅ **可行**：余量 {movable_total:,} ≤ 额度 {avail:,}")
    else:
        print(f"  🔴 **不可行**：余量 {movable_total:,} > 额度 {avail:,}，"
              f"仍超 {movable_total - avail:,} 字符")

    # 按比例分配削减额
    print()
    print("=" * 100)
    print("建议削减额（按余量比例；写作时以此为预算）")
    print("=" * 100)
    print(f"  {'节':<15} {'现状':>8} {'目标':>8} {'需删':>8} {'删幅':>7}")
    plan = {}
    for k in files:
        target = MUST[k] + max(0, int(avail * (cur[k] - MUST[k]) / max(movable_total, 1)))
        need = cur[k] - target
        plan[k] = {"now": cur[k], "must": MUST[k], "target": target, "cut": need,
                   "cut_pct": round(100 * need / cur[k], 1)}
        print(f"  {k:<15} {cur[k]:>8,} {target:>8,} {need:>8,} {100 * need / cur[k]:>6.1f}%")
    print(f"  {'-' * 92}")
    print(f"  {'合计':<15} {total:>8,} {sum(p['target'] for p in plan.values()):>8,} "
          f"{total - sum(p['target'] for p in plan.values()):>8,}")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps({"current": cur, "must": MUST, "overhead": overhead,
                        "budget": budget, "available_for_cutting": avail,
                        "plan": plan}, ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
