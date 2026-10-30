# -*- coding: utf-8 -*-
r"""量化"7 页在内容约束下是否可达"（2026-10-13）。

## 背景

成员 `writing-hardener` 已给出一条反证：**它四节整节删光也只到 ≈6.3 页**。
本脚本给**更完整的算术**：把每节分成"审稿人点名要的必留"与"可移出"两部分，
算出**在保留全部必留内容的前提下，最少需要多少页**。

    python tools\_p524_page_feasibility.py --apply
"""
from __future__ import annotations

import argparse
import io
import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PI = REPO / "paper3" / "paper_ieee"
OUT = REPO / "outputs" / "analysis" / "p3_page_feasibility.json"

# 审稿人点名要、不可移出的项（33 条意见归纳）
# 每项 = (标签, 依据意见, 估字符)
MUST = [
    ("R1–R5 五项要求 + R3′ + 反例 ‖∇E‖² + Lemma S=‖x‖²", "R1.5/R3.1/R3.3", 3200),
    ("定理/推论陈述（Theorem + 5 Corollaries）", "R1.3/R3.2", 2200),
    ("rank 预算 vs 参数预算两种口径 + c_k + 2.65×", "R3.8/R3.9", 1200),
    ("β 来源更正（runs[90]、R²=0.951、median 0.072）", "R3.8", 700),
    ("crossing 的 bracketed 口径 + CI + 置换 p=0.100", "R3.4/R3.17", 1100),
    ("逐块 Γ + rank 表（Qwen2-VL 实测）", "R3.12", 1800),
    ("同预算分配对比（容量逐位对齐 + 反转 + matched-loss）", "R2.2/R2.4/R3.9/R3.21", 2600),
    ("AdaLoRA 同预算 + 对称 lr 扫描 + 如实承认更优", "R2.4/R3.9", 1000),
    ("与随机池不可区分（30 run、47 分位、2/10 更优）", "R2.2/R3.9", 800),
    ("blank = 3.09× @ 论文操作点（595 vs 576 token）", "R1.4/R3.13/R3.14/R3.23", 1500),
    ("下游检验否证（R@1 对照 + 分层相关 + 配对）", "R3.15/R3.16", 1600),
    ("零样本约束/定位（分配决策不含目标模型梯度）", "R2.1/R3.10", 700),
    ("limitation（6 条结论）", "R3.17–R3.22", 1800),
    ("统计与可复现（有效 n、种子出处、功效 11–28）", "R3.17–R3.22", 1500),
]


def pages_of(n_chars: float, per_page: float) -> float:
    return n_chars / per_page


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    inputs = ["main.tex", "sections/introduction.tex", "sections/related_work.tex",
              "sections/theory.tex", "sections/experiments.tex",
              "sections/discussion.tex", "sections/conclusion.tex"]
    total = 0
    for f in inputs:
        p = PI / f
        if p.exists():
            total += len(io.open(p, encoding="utf-8", errors="replace").read())
    pdf = PI / "main.pdf"
    npages = None
    if pdf.exists():
        r = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, encoding="utf-8", errors="replace")
        for ln in (r.stdout or "").splitlines():
            if ln.startswith("Pages:"):
                npages = int(ln.split(":", 1)[1].strip())
    per_page = total / npages if npages else 5702.0

    print("=" * 100)
    print("现状")
    print("=" * 100)
    print(f"  tex 字符合计 {total:,} ｜ PDF {npages} 页 ｜ ≈{per_page:,.0f} 字符/页")
    print(f"  ≤7 页预算 = {per_page * 7:,.0f} 字符 ⇒ 需删 {total - per_page * 7:,.0f}")

    must = sum(x[2] for x in MUST)
    print()
    print("=" * 100)
    print("审稿人点名要、不可移出的内容（33 条意见归纳）")
    print("=" * 100)
    for label, ref, n in MUST:
        print(f"  {n:>6,}  {label:<52} 【{ref}】")
    print(f"  {'-' * 92}")
    print(f"  {must:>6,}  合计（≈{pages_of(must, per_page):.2f} 页）")

    # 固定开销
    fixed = 2600   # 标题+作者+摘要(243词)+关键词+声明段+参考文献(bibtex自动排)
    figs = 3 * 1600  # 3 张图各占约半栏
    tabs = 1000
    overhead = fixed + figs + tabs
    print()
    print("=" * 100)
    print("不可压缩的版面开销")
    print("=" * 100)
    print(f"  标题/摘要/关键词/声明      {fixed:>6,}")
    print(f"  3 张图（约占版面）         {figs:>6,}")
    print(f"  表格                       {tabs:>6,}")
    print(f"  {'-' * 92}")
    print(f"  小计 ≈{overhead:,.0f} 字符（≈{pages_of(overhead, per_page):.2f} 页）")

    floor = must + overhead
    print()
    print("=" * 100)
    print("**可行性结论**")
    print("=" * 100)
    print(f"  必留内容 + 固定开销 = **{floor:,} 字符 ≈ {pages_of(floor, per_page):.1f} 页**")
    print(f"  PRL 上限 = **7.0 页**（{per_page * 7:,.0f} 字符）")
    over = pages_of(floor, per_page) - 7
    print()
    if over > 0:
        print(f"  🔴 **即使把所有可移出的文字全部移出，仍需 {pages_of(floor, per_page):.1f} 页 > 7 页**")
        print(f"     ⇒ **超出 {over:.1f} 页（≈{over * per_page:,.0f} 字符）**")
        print(f"     ⇒ **在保留 33 条意见所需全部证据的前提下，7 页不可达。**")
        print()
        print("  要真正达到 7 页，必须放弃以下之一（都属于审稿人明确要求的证据）：")
        print("    ① 逐块 Γ/rank 表（R3.12）")
        print("    ② 下游检验（R3.15/R3.16）")
        print("    ③ blank 3.09× 探针测量（R1.4/R3.13/R3.14/R3.23）")
        print("    ④ 同预算分配对比（R2.2/R2.4/R3.9/R3.21）")
    else:
        print(f"  ✅ 可行：需把可移出内容压到 {per_page * 7 - floor:,.0f} 字符以内")

    rep = {"total_chars": total, "pdf_pages": npages, "chars_per_page": round(per_page, 1),
           "budget_7pp": round(per_page * 7), "must_keep": must, "overhead": overhead,
           "floor_chars": floor, "floor_pages": round(pages_of(floor, per_page), 2),
           "feasible_7pp": over <= 0, "over_pages": round(over, 2),
           "must_items": [{"label": l, "ref": r, "chars": n} for l, r, n in MUST]}
    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(rep, ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
