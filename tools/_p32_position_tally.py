# -*- coding: utf-8 -*-
r"""统计"哪个位置更保护"在**全部骨干 × 数据集**组合上的胜负分布（2026-10-08）。

## 为什么要算

若答案是"没有可推荐的位置"，那这篇论文的建议部分就没内容了。
**但"不可无条件推荐"≠"没有建议"**——须先看**胜负分布**，再决定能说什么。

## 统计口径

对每个（骨干，数据集）组合，比较 `text_only` 与 `both` 的 CGΔ 均值，谁的更负谁胜。
**只统计两臂齐备的组合**；`vision_only` 作为第三方计入（它从未胜出）。

    python tools\_p32_position_tally.py
"""
from __future__ import annotations

import collections
import glob
import io
import json
import statistics as st
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def load(pat: str) -> dict:
    """按 (arm, rk) 汇总 CGΔ 均值。"""
    out = collections.defaultdict(list)
    for f in sorted(glob.glob(str(REPO / pat), recursive=True)):
        p = Path(f).parts
        d = json.loads(io.open(f, encoding="utf-8").read())
        cg = d["final_gap"]["centroid_gap"] - d["initial_gap"]["centroid_gap"]
        out[(p[-3], p[-4])].append(cg)
    return {k: st.mean(v) for k, v in out.items()}


def main() -> int:
    combos = []

    # ① Flickr30k：严格冻结各骨干
    for name, pat in (
        ("CLIP B/32 r8", "outputs/strict_freeze/{arm}/seed*/results.json"),
        ("CLIP B/32 r4", "outputs/strict_freeze_b32_r4/{arm}/seed*/results.json"),
        ("CLIP B/16 r4", "outputs/strict_freeze_b16/r4/{arm}/seed*/results.json"),
        ("OpenCLIP B/32 r4", "outputs/strict_freeze_oclip/r4/{arm}/seed*/results.json"),
    ):
        pass  # 由下方逐 arm 收集

    def flickr(root: str, label: str):
        vals = {}
        for arm in ("text_only", "both", "vision_only"):
            fs = sorted(glob.glob(str(REPO / root / arm / "seed*" / "results.json")))
            xs = []
            for f in fs:
                d = json.loads(io.open(f, encoding="utf-8").read())
                xs.append(d["final_gap"]["centroid_gap"] - d["initial_gap"]["centroid_gap"])
            if xs:
                vals[arm] = st.mean(xs)
        if "text_only" in vals and "both" in vals:
            best = min(vals, key=lambda a: vals[a])
            combos.append(("Flickr30k", label, vals, best))

    flickr("outputs/strict_freeze", "CLIP B/32 r8")
    flickr("outputs/strict_freeze_b32_r4", "CLIP B/32 r4")
    flickr("outputs/strict_freeze_b16/r4", "CLIP B/16 r4")
    flickr("outputs/strict_freeze_oclip/r4", "OpenCLIP B/32 r4")

    # SigLIP / BioCLIP（归档汇总）
    combos.append(("Flickr30k", "SigLIP B/16 (5 seed)",
                   {"text_only": 0.0664, "both": -0.0114, "vision_only": 0.0522}, "both"))
    combos.append(("Flickr30k", "BioCLIP B/16 (3 seed)",
                   {"text_only": -0.3671, "both": -0.4515, "vision_only": -0.2927}, "both"))

    # ② COCO：新补跑逐秩
    coco = load("outputs/coco_sweep/**/results.json")
    byrk = collections.defaultdict(dict)
    for (arm, rk), v in coco.items():
        byrk[rk][arm] = v
    for rk in sorted(byrk, key=lambda x: int(x[1:])):
        d = byrk[rk]
        if "text_only" in d and "both" in d:
            best = min(d, key=lambda a: d[a])
            combos.append(("COCO", f"rank {rk[1:]}", d, best))

    print("=== 各组合的胜者 ===")
    print(f"  {'数据集':<11} {'配置':<24} {'text_only':>10} {'both':>10} {'vision_only':>12}  胜者")
    win = collections.Counter()
    for ds, label, vals, best in combos:
        win[best] += 1
        print(f"  {ds:<11} {label:<24} {vals.get('text_only', float('nan')):>+10.4f} "
              f"{vals.get('both', float('nan')):>+10.4f} "
              f"{vals.get('vision_only', float('nan')):>+12.4f}  **{best}**")

    n = sum(win.values())
    print(f"\n=== 胜负分布（{n} 个组合）===")
    for k, v in win.most_common():
        print(f"  {k:<14} {v}/{n}  （{100*v/n:.0f}%）")

    print("\n=== 按数据集 ===")
    for ds in ("Flickr30k", "COCO"):
        c = collections.Counter(b for d, _, _, b in combos if d == ds)
        tot = sum(c.values())
        print(f"  {ds:<11} " + " ｜ ".join(f"{k} {v}/{tot}" for k, v in c.most_common()))

    print("\n=== 关键对比：text_only vs both 的**参数量** ===")
    print("  text_only 只训文本侧（如 CLIP B/32 r8：196,608）")
    print("  both      训两侧（491,520）→ **约 2.5 倍**")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
