# -*- coding: utf-8 -*-
r"""**同秩对照判定**：patch size 还是预训练目标决定排序？（2026-10-08）。

## 在等什么

| 实验 | 协议 | 状态 |
|---|---|---|
| CLIP B/32 @ rank 8 | 归档 | ✅ 5 seed：text_only **−0.0465** 最保护 |
| **CLIP B/16 @ rank 4** | 新增 | ✅ text_only **−0.0190** 最保护（both +0.0150） |
| **CLIP B/32 @ rank 4** | **跑中** | ⏳ **本判定的关键** |

## 三种可能的结果与含义

| 结果 | 含义 | 对论文的处置 |
|---|---|---|
| **B/32@r4 也是 text_only 最保护** | **排序跟的是 patch size？不——B/16 也 text_only** → 排序在 **CLIP 系内与 patch size 无关**；两个 patch-16 都是 both 恰因**它们不是 WIT** | **规律改为按预训练目标分组** |
| B/32@r4 是 **both** 最保护 | 排序跟 **rank**，与 patch size/预训练都无关 | 规律**撤回**，改为"排序依配置而变" |
| 数据不支持判定（差异在噪声内） | 需多 seed | 补 seed 后再判 |

## 判据（事先写明）

1. 计算各臂 **5 个 seed 或单 seed** 的 CGΔ **均值**；
2. 取**最保护臂**（CGΔ 最小）；
3. 比较 `CLIP B/16@r4` 与 `CLIP B/32@r4` 的**最保护臂是否相同**：
   - **相同** → 排序与 patch size **无关**（CLIP 系内）；
   - **不同** → patch size 有影响，但与 r8 的结论矛盾 → 需 rank 维度解释。

## 同时报告效应量与不确定性

单 seed 的 CGΔ 差异可能落在噪声内（B/16 的 text_only −0.0190 vs both +0.0150，差 0.034）
——**故一并输出每个臂的 CGΔ 与可得的 sd**，并**明确标注"单 seed，无不确定性估计"**。

    python tools\_p25_samerank_verdict.py [--apply]
"""
from __future__ import annotations

import glob
import io
import json
import statistics as st
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "samerank_verdict.json"

# (标签, 归档 glob 模板, seed 数说明, 协议)
CONFIGS = [
    ("CLIP B/32 @ r8 (归档)", "outputs/strict_freeze/{arm}/seed*/results.json", "5 seed"),
    ("CLIP B/16 @ r4 (新增)", "outputs/strict_freeze_b16/r4/{arm}/seed*/results.json", "1 seed"),
    ("CLIP B/32 @ r4 (新增)", "outputs/strict_freeze_b32_r4/{arm}/seed*/results.json", "1 seed"),
    ("OpenCLIP B/32 @ r4 (新增)", "outputs/strict_freeze_oclip/r4/{arm}/seed*/results.json", "1 seed"),
]
ARMS = ("text_only", "both", "vision_only")


def cg_delta(f: Path):
    try:
        d = json.loads(io.open(f, encoding="utf-8").read())
    except Exception:
        return None
    g = d.get("initial_gap", {}).get("centroid_gap") if isinstance(d.get("initial_gap"), dict) else None
    h = d.get("final_gap", {}).get("centroid_gap") if isinstance(d.get("final_gap"), dict) else None
    return (h - g) if (g is not None and h is not None) else None


def main() -> int:
    apply = "--apply" in sys.argv
    print("=== 同秩对照判定：patch size vs 预训练目标 ===")
    table, best = {}, {}
    for label, pat, seeds in CONFIGS:
        vals = {}
        for arm in ARMS:
            files = glob.glob(str(REPO / pat.format(arm=arm)))
            xs = [v for v in (cg_delta(Path(f)) for f in files) if v is not None]
            if xs:
                vals[arm] = {"mean": st.mean(xs), "n": len(xs),
                             "sd": st.stdev(xs) if len(xs) > 1 else None}
        if not vals:
            print(f"\n  {label:<28} ⏳ 尚无数据")
            continue
        print(f"\n  {label:<28} （{seeds}）")
        for arm in ARMS:
            if arm in vals:
                sd = f" ± {vals[arm]['sd']:.4f}" if vals[arm]["sd"] is not None else "（单 seed）"
                print(f"     {arm:<12} {vals[arm]['mean']:+.4f}{sd}  n={vals[arm]['n']}")
        b = min(vals, key=lambda a: vals[a]["mean"])
        best[label] = b
        print(f"     → 最保护臂 = **{b}**")
        table[label] = vals

    print("\n  === 判定 ===")
    key_old, key_new16, key_new32 = ("CLIP B/32 @ r8 (归档)", "CLIP B/16 @ r4 (新增)",
                                     "CLIP B/32 @ r4 (新增)")
    if key_new32 not in best or key_new16 not in best:
        print(f"     ⏳ 关键对照尚未跑完（B/32@r4: {'有' if key_new32 in best else '无'}，"
              f"B/16@r4: {'有' if key_new16 in best else '无'}）")
        verdict = "pending"
    else:
        b32_4, b16_4 = best[key_new32], best[key_new16]
        if b32_4 == b16_4:
            verdict = "pretraining_not_patch_size"
            print(f"     同秩下 CLIP B/32 与 B/16 的**最保护臂相同**（都是 {b32_4}）")
            print(f"     → **排序在 CLIP 系内与 patch size 无关**；")
            print(f"       两个 patch-16 都是 both，恰因（SigLIP/BioCLIP）**不是 WIT 预训练**。")
            print(f"     → **论文处置：规律改为按预训练目标分组。**")
        else:
            verdict = "rank_or_inconsistent"
            print(f"     同秩下两骨干最保护臂**不同**（B/32={b32_4}、B/16={b16_4}）")
            print(f"     → 与 r8 的结论（B/32=text_only）比较：")
            if b32_4 != best.get(key_old):
                print(f"       **同一骨干 B/32 在 r4 与 r8 排序不同**（{b32_4} vs {best.get(key_old)}）")
                print(f"       → **排序跟的是 rank，不是 patch size 也不是预训练目标**")
                print(f"       → **论文处置：规律撤回，改为'排序依配置而变'。**")
            else:
                print(f"       B/32 在 r4 与 r8 排序一致（都是 {b32_4}）→ patch size 有影响")
                print(f"       → **论文处置：需在 limitation 说明 rank 依赖性。**")
        print(f"\n     ⚠️ 新增对照均为**单 seed**，无不确定性估计；"
              f"差异若在噪声内不足以判定 → 必要时补 seed。")

    if apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(
            {"table": table, "most_protective": best, "verdict": verdict},
            ensure_ascii=False, indent=1))
        print(f"\n     ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
