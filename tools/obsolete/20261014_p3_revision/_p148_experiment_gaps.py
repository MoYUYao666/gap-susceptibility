# -*- coding: utf-8 -*-
r"""清点 `paper合` 剩余的实验缺口（2026-10-10）。

## 逐项查

1. `docs/PAPERA_REVIEWER_RISKS.md` 里标为未完成的风险项；
2. 各风险项**现在是否已解决**（用文件存在性 + 数字匹配判）；
3. 论文正文里是否有**未兑现的"我们将…"式承诺**。

    python tools\_p148_experiment_gaps.py
"""
from __future__ import annotations

import glob
import io
import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def main() -> int:
    print("=" * 72)
    print("① 风险清单逐项（PAPERA_REVIEWER_RISKS.md）")
    print("=" * 72)
    f = REPO / "docs" / "PAPERA_REVIEWER_RISKS.md"
    if f.exists():
        t = io.open(f, encoding="utf-8", errors="replace").read()
        # 抽 B*/C* 条目及其标题
        for m in re.finditer(r"\|\s*\*\*(B\d|C\d)\*\*\s*\|([^|]{0,72})\|([^|]{0,90})\|",
                             t):
            print(f"  {m.group(1):<4} {m.group(2).strip()[:60]:<60} {m.group(3).strip()[:44]}")
    else:
        print("  （无该文件）")

    print()
    print("=" * 72)
    print("② 各风险项的现状（按证据文件判）")
    print("=" * 72)
    checks = [
        ("B1 patch-size 归因", "paper合/sections/empirical.tex", "patch size"),
        ("B2 数据集翻转", "outputs/analysis/dataset_flip_strict.json", "flip_holds_r4"),
        ("B3 OpenCLIP 效应量", "outputs/analysis/oclip_effectsize.json", '"k_sd"'),
        ("B4 COCO DG* 不动", "paper合/sections/discussion.tex", "0.003"),
        ("C1 COCO ODE 表撤回", "paper合/sections/supplement.tex", "COCO"),
        ("C2 严格冻结 3 seed", "outputs/strict_freeze_b32_r4", None),
        ("C3 解码器 VLM", "paper合/sections/supplement.tex", "Decoder-Based VLM"),
        ("C4 α 预测", "outputs/theory/prospective/prospective_results.json", "alpha_pred"),
        ("C5 4-bit vs bf16", "paper合/sections/supplement.tex", "4-bit"),
        ("C7 Γ_m 解码器验证", "outputs/analysis/gamma_vlm.json", None),
    ]
    for tag, path, needle in checks:
        p = REPO / path
        if not p.exists():
            print(f"  ❌ {tag:<24} 缺 {path}")
            continue
        if p.is_dir():
            n = len(list(p.rglob("results.json")))
            print(f"  ✅ {tag:<24} 目录，含 {n} 个 results.json")
            continue
        t = io.open(p, encoding="utf-8", errors="replace").read()
        ok = needle is None or needle in t
        print(f"  {'✅' if ok else '⚠️'} {tag:<24} {path}"
              + ("" if ok else f"  ← 未找到 {needle!r}"))

    print()
    print("=" * 72)
    print("③ 论文里未兑现的承诺（future work / 我们将 / left to）")
    print("=" * 72)
    for f2 in sorted(glob.glob(str(REPO / "paper合" / "sections" / "*.tex"))):
        t = io.open(f2, encoding="utf-8", errors="replace").read()
        for pat in (r"left (?:to|for) future work", r"we leave", r"future work",
                    r"remains? (?:to be|open)", r"not yet (?:established|resolved|pinned)"):
            for m in re.finditer(pat, t, re.I):
                s = " ".join(t[max(0, m.start() - 190):m.start() + 190].split())
                print(f"  [{Path(f2).name}] …{s}…")
                print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
