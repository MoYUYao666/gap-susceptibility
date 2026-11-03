# -*- coding: utf-8 -*-
r"""核验审计成员的关键数字（2026-10-12）。

## 待核（都是会影响改稿的）

| # | 主张 | 影响 |
|---|---|---|
| 1 | ΔCG 抽样 sd 仅 **0.0003–0.0007**（四臂 × 12 次） | 支持"ΔCG 排序稳健" |
| 2 | **vision_only 归档 R@1 = 0.7000 复现不出**（三条独立路径给 ≈0.679） | 查实一处归档异常 |
| 3 | R@1 抽样 sd 0.0055–0.0078；**5-seed 均值口径 0.0025–0.0035** | 决定 "both > vision_only (0.013)" 是否该弱化 |
| 4 | **OpenCLIP r4 text_only 的 0.0064 不是噪声，是 provenance 混用** | 我在 caption 里把它归入"抽样差异"，**须更正** |
| 5 | 归一化对照：frozen CG 只变 +0.24%，成对 ΔCG 变 ≤0.0025 | 排除归一化假设 |

    python tools\_p372_verify_audit_numbers.py [--apply]
"""
from __future__ import annotations

import argparse
import glob
import io
import json
import os
import statistics
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def find(pattern):
    return sorted(glob.glob(str(REPO / pattern), recursive=True))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    print("=" * 100)
    print("① 审计产出的归档文件清单")
    print("=" * 100)
    for p in find("outputs/analysis/dinov2_hetero/**/*.json"):
        print(f"  {Path(p).relative_to(REPO)}")

    print()
    print("=" * 100)
    print("② 画廊噪声（_p360 rev-2 / results_corrected.json）—— 四臂 × 12 次")
    print("=" * 100)
    for cand in ("outputs/analysis/dinov2_hetero/gallery_noise/results_corrected.json",
                 "outputs/analysis/dinov2_hetero/gallery_noise/results.json"):
        p = REPO / cand
        if not p.exists():
            print(f"  ⚠️ 缺 {cand}")
            continue
        d = json.loads(io.open(p, encoding="utf-8", errors="replace").read())
        print(f"  {cand}")
        s = json.dumps(d, ensure_ascii=False, indent=1)
        print(s[:2200])
        break

    print()
    print("=" * 100)
    print("③ vision_only 的归档 R@1 vs 复评（审计主张 0.7000 复现不出）")
    print("=" * 100)
    for arm in ("text_only", "both", "vision_only"):
        fs = find(f"outputs/strict_freeze/{arm}/seed*/results.json")
        vals = []
        for f in fs:
            d = json.loads(io.open(f, encoding="utf-8", errors="replace").read())
            r1 = (d.get("final_task_metrics") or {}).get("R@1")
            if r1 is not None:
                vals.append((d.get("seed"), round(r1, 4)))
        if vals:
            nums = [v for _, v in vals]
            print(f"  {arm:<12} 归档逐 seed {sorted(vals)} ｜ 均值 {sum(nums)/len(nums):.4f}")

    print()
    print("=" * 100)
    print("④ provenance 混用（OpenCLIP 那格）—— 核 r1_provenance.json")
    print("=" * 100)
    for cand in ("outputs/analysis/dinov2_hetero/r1_provenance.json",
                 "outputs/analysis/strict_final_match.json",
                 "outputs/analysis/r1_attribution_verify.json"):
        p = REPO / cand
        if not p.exists():
            continue
        d = json.loads(io.open(p, encoding="utf-8", errors="replace").read())
        s = json.dumps(d, ensure_ascii=False)
        print(f"  {cand}（{len(s)} 字符）")
        for key in ("strict_freeze_oclip", "strict_freeze_openclip", "0.6366", "0.6428"):
            if key in s:
                i = s.find(key)
                print(f"     …{s[max(0,i-120):i+180]}…")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
