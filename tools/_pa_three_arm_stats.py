# -*- coding: utf-8 -*-
r"""三臂位置图谱的统一配对统计（CLIP / OpenCLIP / SigLIP）。

## 背景

先前 `tools/_crossarch_strict_stats.py` 只比较 **text_only vs both** 两臂。
跑完 OpenCLIP 后有了**完整三臂**（text_only / both / vision_only），需要统一口径：
同一骨干内做**配对**比较（同 seeds），并检验"**降间隙排序**与**检索排序**是否一致"。

## 协议（三者相同）

5000 样本 / 10 epochs / **rank 8 + α16** / seeds 42,123,456,789,1024 / **同一 InfoNCE 微调损失**。
严格冻结：只训练 LoRA 的 A/B 矩阵（每臂的 `[strict] trainable` 与 `vis_nonzero=0` 已在日志核对）。

## 数据来源

- CLIP：`outputs/strict_freeze/`（MODEL=clip-vit-base-patch32）
- OpenCLIP：`outputs/strict_freeze_openclip/`（MODEL=openclip，LAION-2B）
- SigLIP：`outputs/siglip_strict/seed*/s4_siglip_lora_{text_only,both}` + `s6_siglip_lora_vision_only`

    python tools\_pa_three_arm_stats.py
"""
from __future__ import annotations

import glob
import io
import json
import math
import statistics as st
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def _load(p: str) -> dict | None:
    try:
        return json.loads(io.open(p, encoding="utf-8", errors="ignore").read())
    except Exception:
        return None


def _dcg_r1(d: dict) -> tuple[float, float] | None:
    ig, fg = d.get("initial_gap") or {}, d.get("final_gap") or {}
    if ig.get("centroid_gap") is None or fg.get("centroid_gap") is None:
        return None
    r1 = (d.get("final_task_metrics") or {}).get("R@1")
    return (fg["centroid_gap"] - ig["centroid_gap"], float(r1) if r1 is not None else float("nan"))


def cli_arm(root: str, tag: str) -> dict[int, tuple[float, float]]:
    out: dict[int, tuple[float, float]] = {}
    for p in sorted(glob.glob(str(REPO / root / tag / "seed*" / "results.json"))):
        d = _load(p)
        v = _dcg_r1(d) if d else None
        if v:
            out[int(d["seed"])] = v
    return out


def siglip_arm(tag: str) -> dict[int, tuple[float, float]]:
    pat = {"text_only": "s4_siglip_lora_text_only", "both": "s4_siglip_lora_both",
           "vision_only": "s6_siglip_lora_vision_only"}[tag]
    out: dict[int, tuple[float, float]] = {}
    for p in sorted(glob.glob(str(REPO / "outputs" / "siglip_strict" / "seed*" / pat / "results.json"))):
        d = _load(p)
        v = _dcg_r1(d) if d else None
        if v:
            out[int(Path(p).parts[-3].replace("seed", ""))] = v
    return out


BACKBONES = [
    ("CLIP B/32 (WIT)", lambda t: cli_arm("outputs/strict_freeze", t)),
    ("OpenCLIP B/32 (LAION)", lambda t: cli_arm("outputs/strict_freeze_openclip", t)),
    ("SigLIP B/16", siglip_arm),
]
ARMS = ("text_only", "both", "vision_only")


def main() -> int:
    print("=== 三臂位置图谱（同协议；ΔCG 负=间隙下降）===")
    for name, getter in BACKBONES:
        A = {t: getter(t) for t in ARMS}
        have = [t for t in ARMS if A[t]]
        if not have:
            print(f"\n  【{name}】无数据")
            continue
        print(f"\n  【{name}】n={len(A[have[0]])}")
        print("   %-12s %12s %12s %10s" % ("臂", "ΔCG 均值", "± sd", "R@1"))
        means = {}
        for t in ARMS:
            if not A[t]:
                print("   %-12s %12s" % (t, "（未跑）"))
                continue
            vs = [A[t][s][0] for s in A[t]]
            rs = [A[t][s][1] for s in A[t]]
            means[t] = (st.mean(vs), st.mean(rs))
            print("   %-12s %+12.4f %12.4f %10.3f"
                  % (t, st.mean(vs), st.stdev(vs) if len(vs) > 1 else 0.0, st.mean(rs)))
        if len(means) == 3:
            by_gap = sorted(means, key=lambda k: means[k][0])
            by_r1 = sorted(means, key=lambda k: -means[k][1])
            print("   → ΔCG 排序: %s" % " < ".join(by_gap))
            print("   → 检索排序: %s" % " > ".join(by_r1))
            print("   → 两者%s" % ("一致 ✅" if by_gap[0] == by_r1[0]
                                   else f"不一致 ⚠️（降间隙最好={by_gap[0]}，检索最好={by_r1[0]}）"))

    print("\n=== 配对比较（text_only vs both，同 seeds）===")
    for name, getter in BACKBONES:
        a, b = getter("text_only"), getter("both")
        ss = sorted(set(a) & set(b))
        if len(ss) < 2:
            print(f"  {name}: 数据不足（{len(ss)}）")
            continue
        ds = [b[s][0] - a[s][0] for s in ss]
        m, sd = st.mean(ds), st.stdev(ds)
        t = m / (sd / math.sqrt(len(ds))) if sd else float("inf")
        same = all(x > 0 for x in ds) or all(x < 0 for x in ds)
        print("  %-24s n=%d 差 %+.4f ± %.4f ｜ t=%+.2f ｜ 同向=%s ｜ text_only ΔCG=%+.4f"
              % (name, len(ss), m, sd, t, same, st.mean([a[s][0] for s in ss])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
