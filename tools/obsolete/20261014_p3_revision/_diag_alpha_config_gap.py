# -*- coding: utf-8 -*-
r"""查归档 ODE 轨迹的训练配置，与我的 α 实验逐项对照（2026-10-08 04:05）。

## 为什么

α 重跑（5000 样本）的 DG\\* 跨度 **0.0175**，而归档中位 **0.1538**（**小 8 倍**）。
**样本量加了 2.5 倍只让跨度从 0.0102 增到 0.0175** → **差异不在样本量**。

必须找出**真正的差异**（学习率？调度器？rank？数据划分？），否则这个对照实验**测不出 α 能否被预测**。

    python tools\_diag_alpha_config_gap.py
"""
from __future__ import annotations

import glob
import io
import json
import statistics as st
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def spans(pattern: str) -> list[tuple[str, float, float, float]]:
    out = []
    for f in sorted(glob.glob(pattern)):
        try:
            d = json.loads(io.open(f, encoding="utf-8").read())
        except Exception:
            continue
        y = d.get("dg_star") or d.get("dg_star_history")
        if not y:
            continue
        out.append((f.replace("\\", "/"), max(y) - min(y), y[0], y[-1]))
    return out


def main() -> int:
    print("=== 归档各臂的 DG* 跨度 ===")
    for pat, name in (("outputs/theory/v1_trajectory/*both*/seed*/dg_star_history.json", "both"),
                      ("outputs/theory/v1_trajectory/*text*/seed*/dg_star_history.json", "text"),
                      ("outputs/theory/adapter/*/seed*/dg_star_history.json", "adapter"),
                      ("outputs/theory/coco/*/seed*/dg_star_history.json", "coco")):
        s = spans(pat)
        if s:
            print(f"  {name:<10} n={len(s):>3} ｜ 跨度中位 {st.median(x[1] for x in s):.4f} "
                  f"｜ 首→末 {st.mean(x[2] for x in s):.4f} → {st.mean(x[3] for x in s):.4f}")

    print("\n=== 归档 both 臂按 rank 分组的跨度 ===")
    byrank = {}
    for f, sp, y0, y1 in spans("outputs/theory/v1_trajectory/*both*/seed*/dg_star_history.json"):
        tag = f.split("/")[3]           # 如 v1_both_r16
        byrank.setdefault(tag, []).append((sp, y0, y1))
    for tag in sorted(byrank):
        v = byrank[tag]
        print(f"  {tag:<18} n={len(v)} ｜ 跨度中位 {st.median(x[0] for x in v):.4f}"
              f" ｜ 首→末 {st.mean(x[1] for x in v):.4f} → {st.mean(x[2] for x in v):.4f}")

    print("\n=== 关键对照 ===")
    print("  我的 α 重跑（both, rank8, 5000 样本, lr 1e-4 cosine）：跨度 0.0159 / 0.0191")
    if byrank:
        lo = min(st.median(x[0] for x in v) for v in byrank.values())
        hi = max(st.median(x[0] for x in v) for v in byrank.values())
        print(f"  归档各 rank：跨度中位 {lo:.4f} – {hi:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
