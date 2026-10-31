# -*- coding: utf-8 -*-
r"""rank sweep 分析：严格冻结下 ΔCG 是否随 LoRA rank 单调（检验设计模式②）。

## 设计模式②原文

> "Lower LoRA rank preserves alignment better"

它来自 **legacy 约定**（`src/lora.py` 不冻结基座）下的观测。严格冻结后必须重新检验。

## 协议（同前）

5000 样本 / 10 epochs / CLIP ViT-B/32 / seeds 42,123,456 ｜ alpha = rank × 2。

| rank | text_only 可训 | both 可训 |
|---|---|---|
| 4 | 98,304 | 245,760 |
| 8（论文口径） | 196,608 | — |
| 16 | 393,216 | 983,040 |
| 32 | 786,432 | （跑中） |

## 产物目录（**每个 rank 必须独立目录**，否则跳过逻辑会互相污染）

- rank 4/16/32：`outputs/strict_freeze_rank/r{4,16,32}/`
- rank 8（论文口径）：`outputs/strict_freeze/`

    python tools\_pa_rank_sweep_stats.py
"""
from __future__ import annotations

import glob
import io
import json
import statistics as st
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

SOURCES = {1: "outputs/strict_freeze_rank/r1", 2: "outputs/strict_freeze_rank/r2", 4: "outputs/strict_freeze_rank/r4",
           8: "outputs/strict_freeze",
           16: "outputs/strict_freeze_rank/r16",
           32: "outputs/strict_freeze_rank/r32", 64: "outputs/strict_freeze_rank/r64"}
ARMS = ("text_only", "both")


def arm(root: str, tag: str) -> dict[int, tuple[float, float, int]]:
    out = {}
    for p in sorted(glob.glob(str(REPO / root / tag / "seed*" / "results.json"))):
        try:
            d = json.loads(io.open(p, encoding="utf-8", errors="ignore").read())
            v = d["final_gap"]["centroid_gap"] - d["initial_gap"]["centroid_gap"]
            r1 = (d.get("final_task_metrics") or {}).get("R@1")
            out[int(d.get("seed", 0))] = (v, float(r1) if r1 is not None else float("nan"),
                                          int(d.get("n_trainable_params") or 0))
        except Exception:
            continue
    return out


def main() -> int:
    print("=== 严格冻结下 ΔCG 随 rank 的变化（CLIP ViT-B/32，alpha = rank x 2）===")
    data: dict[str, dict[int, float]] = {}
    r1s: dict[str, dict[int, float]] = {}
    for tag in ARMS:
        print("\n  [%s]" % tag)
        print("   %-6s %-22s %-10s %-12s" % ("rank", "ΔCG 均值 ± sd", "R@1", "可训参数"))
        for rk in sorted(SOURCES):
            a = arm(SOURCES[rk], tag)
            if not a:
                print("   %-6d %-22s %-10s %-12s" % (rk, "(未跑)", "-", "-"))
                continue
            vs = [a[s][0] for s in a]
            rs = [a[s][1] for s in a]
            n = next(iter(a.values()))[2]
            data.setdefault(tag, {})[rk] = st.mean(vs)
            r1s.setdefault(tag, {})[rk] = st.mean(rs)
            print("   %-6d %+.4f ± %.4f       %.3f      %-12s (n=%d)"
                  % (rk, st.mean(vs), st.stdev(vs) if len(vs) > 1 else 0.0, st.mean(rs), n, len(vs)))

    print("\n=== 单调性判定 ===")
    print("  设计模式②称 lower rank 更能保对齐 -> ΔCG 应随 rank 单调递增（rank 越小越负）")
    for tag in ARMS:
        if tag not in data or len(data[tag]) < 3:
            print("  %-10s 数据不足（%d 个 rank）" % (tag, len(data.get(tag, {}))))
            continue
        ks = sorted(data[tag])
        vs = [data[tag][k] for k in ks]
        inc = all(vs[i] <= vs[i + 1] for i in range(len(vs) - 1))
        dec = all(vs[i] >= vs[i + 1] for i in range(len(vs) - 1))
        print("  %-10s rank %s -> %s" % (tag, ks, "  ".join("%+.4f" % v for v in vs)))
        verdict = ("单调递增，支持设计模式②" if inc else
                   "单调递减，与设计模式②相反" if dec else "非单调，不支持设计模式②")
        print("  %-10s -> %s" % ("", verdict))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
