# -*- coding: utf-8 -*-
r"""两架构严格冻结对照的**配对统计**（CLIP vs SigLIP）。

## 背景：一次自我更正

我在正文里写过"两个对照用了不同的 epoch 预算，故方向相反只是观察"。
**查证后该 caveat 是错的**——两者配置匹配：

| 项 | CLIP（`outputs/strict_freeze/`） | SigLIP（`outputs/siglip_strict/`） |
|---|---|---|
| max_samples | 5000 | 5000 |
| epochs | 10 | 10 |
| **LoRA rank / alpha** | **8 / 16** | **8 / 16** |
| gap_history 点数 | 7 | 7 |
| seeds | 42,123,456,789,1024 | 同一组 |
| batch_size | 128 | 64 |
| 可训参数（text_only） | 196,608 | 294,912 |

后两项是**编码器规模差异**（CLIP ViT-B/32 vs SigLIP ViT-B/16），不是协议差异；
严格冻结保证每臂内部只有"适配器注入位置"一个变量。

## 因此可支持的结论

两架构在**匹配预算、匹配种子、匹配 rank** 下给出**相反**的位置效应 →
**架构依赖是实测结论**；但"由损失函数（InfoNCE vs pairwise sigmoid）导致"仍属推测，
因为两架构同时还差着编码器与嵌入维度。

    python tools\_crossarch_strict_stats.py
"""
from __future__ import annotations

import glob
import io
import json
import math
import statistics as st
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SEEDS = [42, 123, 456, 789, 1024]


def clip_arm(tag: str) -> dict[int, float]:
    out = {}
    for p in sorted(glob.glob(str(REPO / "outputs" / "strict_freeze" / tag / "seed*" / "results.json"))):
        d = json.loads(io.open(p, encoding="utf-8", errors="ignore").read())
        out[int(d["seed"])] = d["final_gap"]["centroid_gap"] - d["initial_gap"]["centroid_gap"]
    return out


def siglip_arm(tag: str) -> dict[int, float]:
    out = {}
    for p in sorted(glob.glob(str(REPO / "outputs" / "siglip_strict" / "seed*" / tag / "results.json"))):
        d = json.loads(io.open(p, encoding="utf-8", errors="ignore").read())
        seed = int(Path(p).parts[-3].replace("seed", ""))
        out[seed] = d["final_gap"]["centroid_gap"] - d["initial_gap"]["centroid_gap"]
    return out


def paired(a: dict[int, float], b: dict[int, float], seeds: list[int]) -> tuple[float, float, float]:
    diffs = [b[s] - a[s] for s in seeds if s in a and s in b]
    m, sd = st.mean(diffs), st.stdev(diffs)
    t = m / (sd / math.sqrt(len(diffs))) if sd else float("inf")
    return m, sd, t


def main() -> int:
    panels = [
        ("CLIP (InfoNCE)", clip_arm("text_only"), clip_arm("both")),
        ("SigLIP (sigmoid)", siglip_arm("s4_siglip_lora_text_only"), siglip_arm("s4_siglip_lora_both")),
    ]
    print("=== 两架构严格冻结对照（配对，同 seeds 同预算同 rank）===")
    for name, a, b in panels:
        ss = [s for s in SEEDS if s in a and s in b]
        print("\n  【%s】n=%d" % (name, len(ss)))
        print("   %-6s %11s %11s %11s" % ("seed", "text_only", "both", "both−text"))
        for s in ss:
            print("   %-6d %+11.4f %+11.4f %+11.4f" % (s, a[s], b[s], b[s] - a[s]))
        ma, mb = st.mean([a[s] for s in ss]), st.mean([b[s] for s in ss])
        m, sd, t = paired(a, b, ss)
        print("   均值   %+11.4f %+11.4f %+11.4f  (sd %.4f, t=%.1f)" % (ma, mb, m, sd, t))
        print("   → text_only 更优: %s" % ("是" if ma < mb else "否（both 更优）"))

    print("\n=== 判定 ===")
    ca, cb = panels[0][1], panels[0][2]
    sa, sb = panels[1][1], panels[1][2]
    clip_better = st.mean([ca[s] for s in SEEDS if s in ca]) < st.mean([cb[s] for s in SEEDS if s in cb])
    sig_better = st.mean([sa[s] for s in SEEDS if s in sa]) < st.mean([sb[s] for s in SEEDS if s in sb])
    print("  CLIP: text_only 更优 = %s ｜ SigLIP: text_only 更优 = %s ｜ **方向相反 = %s**"
          % (clip_better, sig_better, clip_better != sig_better))
    print("  ⚠ 仍属观察而非机制：两架构同时差着损失函数、编码器与嵌入维度。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
