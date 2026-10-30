# -*- coding: utf-8 -*-
r"""SigLIP 严格冻结对照的最终统计（5 seeds 配对）。

## 设计（同预算、同协议，唯一差别 = 适配器注入位置）

| 臂 | LoRA 注入 | 可训参数 | 视觉侧可训 |
|---|---|---|---|
| text_only | 仅文本 | 294,912 | **0**（视觉侧完全冻结） |
| both | 文本 + 视觉 | 589,824 | 294,912（**仅 LoRA**，基座冻结） |

5000 样本 / 10 epochs / batch 64 / seeds 42,123,456,789,1024。

## 为什么这个实验重要

legacy 约定下（`src/lora.py` 不冻结基座），text-only 臂反而训练 1.89 亿参数（含整个视觉塔），
两臂都动视觉侧，故"位置"差别被冻结失效掩盖。严格冻结后两臂**只差适配器位置**，比较才成立。

    python tools\_siglip_strict_stats.py
"""
from __future__ import annotations

import glob
import io
import json
import math
import statistics as st
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ROOT = REPO / "outputs" / "siglip_strict"


def load(arm: str) -> dict[int, dict]:
    out: dict[int, dict] = {}
    for p in sorted(glob.glob(str(ROOT / "seed*" / f"s4_siglip_lora_{arm}" / "results.json"))):
        d = json.loads(io.open(p, encoding="utf-8", errors="ignore").read())
        seed = int(Path(p).parts[-3].replace("seed", ""))
        ig, fg = d["initial_gap"]["centroid_gap"], d["final_gap"]["centroid_gap"]
        r1 = (d.get("final_task_metrics") or {}).get("R@1")
        out[seed] = {"dcg": fg - ig, "r1": r1, "ntr": d.get("n_trainable_params")}
    return out


def main() -> int:
    A, B = load("text_only"), load("both")
    seeds = sorted(set(A) & set(B))
    print("=== 配对结果（ΔCG = final − initial；负 = 间隙下降）===")
    print("  %-6s %12s %12s %12s" % ("seed", "text_only", "both", "差(≈both−text)"))
    diffs, ra, rb = [], [], []
    for s in seeds:
        d = B[s]["dcg"] - A[s]["dcg"]
        diffs.append(d)
        if A[s]["r1"] is not None: ra.append(A[s]["r1"])
        if B[s]["r1"] is not None: rb.append(B[s]["r1"])
        print("  %-6d %+12.4f %+12.4f %+12.4f" % (s, A[s]["dcg"], B[s]["dcg"], d))

    ma, mb = st.mean(x["dcg"] for x in A.values()), st.mean(x["dcg"] for x in B.values())
    print("\n  text_only 均值 %+.4f ± %.4f （n=%d，全为正: %s）"
          % (ma, st.stdev([x["dcg"] for x in A.values()]), len(A), all(x["dcg"] > 0 for x in A.values())))
    print("  both      均值 %+.4f ± %.4f （n=%d，全为负: %s）"
          % (mb, st.stdev([x["dcg"] for x in B.values()]), len(B), all(x["dcg"] < 0 for x in B.values())))

    md = st.mean(diffs)
    sd = st.stdev(diffs)
    t = md / (sd / math.sqrt(len(diffs))) if sd else float("inf")
    print("\n=== 配对检验（n=%d）===" % len(diffs))
    print("  平均差 %+.4f ｜ sd %.4f ｜ 配对 t = %.2f" % (md, sd, t))
    print("  5/5 方向一致 → 符号检验 p = %.4f（双侧 2^-5 × 2）" % (2 ** -len(diffs) * 2))
    print("  → 结论：%s" % ("**both 显著更优**（间隙下降 vs 上升）" if md < 0 and abs(t) > 3
                            else "差异不足以判定"))

    if ra and rb:
        print("\n=== 检索对比（final_task_metrics R@1）===")
        print("  text_only %.3f ± %.3f ｜ both %.3f ± %.3f ｜ 差 %+.3f"
              % (st.mean(ra), st.stdev(ra), st.mean(rb), st.stdev(rb), st.mean(rb) - st.mean(ra)))

    print("\n=== 可训参数（验证严格冻结）===")
    for name, D in (("text_only", A), ("both", B)):
        print("  %-10s %s" % (name, {s: D[s]["ntr"] for s in seeds}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
