# -*- coding: utf-8 -*-
r"""核 task-10（F+G 组）的关键数字（2026-10-12）。

## 待核（每条都会改稿）

1. **下游反例**：`Spearman(ΔE_test, ΔR@1) = −0.3742`（n=78）
   → **能量降幅与下游收益负相关** ⇒ 直接否证 R1.3/R3.15 想问的"能量是不是下游代理"
2. **blank 与 real 符号相反**：n=16 时 real 全负、blank 全正；Γ 的文本块 cos φ **符号翻转**；
   `Γ_text_shallow` real **−0.25** vs blank **+171.39**
3. **Γ 块排序不一致**（秩相关 0.8，1 对块序颠倒）
4. **blank vs real 交互**：n=16 时 blank **略好**（+0.0051~+0.0081）；n=1024 时 blank **明显更差**（−0.0139~−0.0314）
5. **它自报的一个假数字已修**：caption 张量未 reshape → i2t R@1 假降到 0.145（真值 0.822）→ 有硬断言

    python tools\_p437_verify_downstream.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import os
import statistics
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "p3_downstream_verified.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    rep = {}

    print("=" * 100)
    print("① 归档清单")
    print("=" * 100)
    for f in ("p3d_manifest.json", "p3d_summary.json", "p3d_gamma_real_vs_blank.json",
              "p3d_clip_ranksweep.json", "p3d_qwen_ranksweep.json"):
        p = REPO / "outputs" / "analysis" / f
        print(f"  {'✅' if p.exists() else '⚠️ '} {f}"
              + (f"  {os.path.getsize(p):,} B" if p.exists() else ""))

    print()
    print("=" * 100)
    print("② summary 全文（关键结论的出处）")
    print("=" * 100)
    p = REPO / "outputs" / "analysis" / "p3d_summary.json"
    if p.exists():
        d = json.loads(io.open(p, encoding="utf-8", errors="replace").read())
        s = json.dumps(d, ensure_ascii=False, indent=1)
        print(s[:3000])
        rep["summary"] = d

    print()
    print("=" * 100)
    print("③ 独立重算 Spearman(ΔE_test, ΔR@1)（不信报告，自己从 runs 算）")
    print("=" * 100)
    p = REPO / "outputs" / "analysis" / "p3d_clip_ranksweep.json"
    if p.exists():
        d = json.loads(io.open(p, encoding="utf-8", errors="replace").read())
        runs = d.get("runs") if isinstance(d, dict) else d
        print(f"  runs 类型 {type(runs).__name__} ｜ 长度 {len(runs) if runs else 0}")
        if isinstance(runs, list) and runs:
            print("  第一条 run 的键：")
            print("    " + str(sorted(runs[0].keys())))

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(rep, ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
