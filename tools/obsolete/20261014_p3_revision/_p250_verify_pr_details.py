# -*- coding: utf-8 -*-
r"""核验 R1.4/R3.1/R3.4/R2.3b 在 `paper合` 里的真实状态（2026-10-12）+ 列实验数据。

    python tools\_p250_verify_pr_details.py [--apply]
"""
from __future__ import annotations

import argparse
import glob
import io
import json
import os
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
FH = sorted(glob.glob(str(REPO / "paper合" / "sections" / "*.tex"))) + \
    sorted(glob.glob(str(REPO / "paper合" / "main*.tex")))
OUT = REPO / "outputs" / "analysis" / "pr_details_verify.json"


def show(pat, label, w=400, n=8):
    print("=" * 96)
    print(f"「{label}」")
    print("=" * 96)
    tot = 0
    for f in FH:
        t = io.open(f, encoding="utf-8", errors="replace").read()
        for m in re.finditer(pat, t, re.I):
            tot += 1
            if tot > n:
                continue
            ln = t[:m.start()].count("\n") + 1
            s = " ".join(t[max(0, m.start() - w // 3):m.start() + w].split())
            print(f"\n  [{Path(f).name}:{ln}] …{s[:430]}…")
    print(f"\n  共 {tot} 处\n")
    return tot


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    res = {}

    res["blip"] = show(r"BLIP", "BLIP（R1.4/R3.4：选择性解冻）")
    res["coco_r1"] = show(r"COCO", "COCO 检索（R1.4/R3.4：R@1<0.001）", n=5)
    res["116"] = show(r"\b116\b", "「116 experiments」（R2.3b）", n=5)
    res["0.079"] = show(r"\+0\.079", "+0.079（R1.1/R3.1）", n=3)
    res["0.064"] = show(r"0\.064|0\.066", "−0.064 / −0.066（R3.1）", n=3)
    res["selective"] = show(r"selective unfreez|unfreez", "选择性解冻（R3.4）", n=4)

    print("=" * 96)
    print("可用实验数据（供补做混合效应/参数扰动/lr 扫描）")
    print("=" * 96)
    for pat, label in (
            ("outputs/**/*.json", "全部结果 JSON"),
            ("outputs/analysis/*.json", "分析归档"),
            ("outputs/**/*seed*.json", "种子级归档"),
            ("outputs/**/*.pt", "检查点"),
            ("outputs/**/*.csv", "CSV")):
        n = len(glob.glob(str(REPO / pat), recursive=True))
        print(f"  {label:<22} {n} 个")
    # 关键：有没有"实验级"表格（供混合效应）
    for f in ("outputs/dg_full_results.json", "outputs/a1_full_results.json",
              "outputs/analysis/recomputed_tables.json",
              "outputs/analysis/coco_sweep_audit.json"):
        p = REPO / f
        print(f"  {'✅' if p.exists() else '❌'} {f}")
    print()
    print("  ── outputs/ 顶层 JSON（前 30）──")
    for f in sorted(glob.glob(str(REPO / "outputs" / "*.json")))[:30]:
        print("    " + Path(f).name)

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(res, ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
