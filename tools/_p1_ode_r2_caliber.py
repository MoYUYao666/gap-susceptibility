# -*- coding: utf-8 -*-
r"""复现正文的 in-sample R²=0.986（口径核查，2026-10-07）。

## 为什么要查

`_p1_ode_loco2.py` 用**种子均值轨迹**逐配置拟合，得 in-sample 平均 **R²=0.877**，
而正文写 **"mean R² = 0.986（range 0.978–0.997）across the **LoRA** configurations"**。

**差异必须解释**，否则后续任何"拟合 vs 预测"的结论都不成立。**两种候选口径**：

| 口径 | 说明 |
|---|---|
| **① 逐 run 拟合** | 162 个 run（含 5 seeds）**各自**拟合，再取平均 |
| **② 种子均值** | 每个配置先按 seed 平均，再拟合（我在 LOCO 里用的） |

正文说 "162 experiments（81 per dataset）… each configuration replicated over five random seeds"
→ 162 = 81 × 2，而每个配置 5 seeds → **162 更像"逐 run"或"逐配置"的口径需实测确认**。

**本脚本两种都算**，并只取 **LoRA** 配置（正文明确限定），看哪个落在 0.978–0.997。

    python tools\_p1_ode_r2_caliber.py
"""
from __future__ import annotations

import glob
import io
import json
import statistics as st
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

try:
    import numpy as np
except Exception:
    np = None


def r2(y, yh):
    y = np.asarray(y, float); yh = np.asarray(yh, float)
    ss = float(((y - y.mean()) ** 2).sum())
    return 1.0 - float(((y - yh) ** 2).sum()) / ss if ss > 0 else float("nan")


def grid_fit(t, y):
    """网格 β + 解析幅度 → (α, β, R²)；与 `_p1_ode_loco2.py` 完全同法。"""
    t = np.asarray(t, float); y = np.asarray(y, float)
    dg0 = float(y[0]); r = y - dg0
    best = (float("nan"), float("nan"), float("inf"))
    for logb in np.linspace(np.log10(0.005), np.log10(20.0), 800):
        b = 10.0 ** logb
        u = 1.0 - np.exp(-b * t)
        den = float((u * u).sum())
        if den < 1e-12:
            continue
        a = float((u * r).sum()) / den
        resid = float(((r - a * u) ** 2).sum())
        if resid < best[2]:
            best = (a * b, b, resid)
    A, B, _ = best
    return float(A), float(B), r2(y, dg0 + (A / B) * (1.0 - np.exp(-B * t)))


def is_lora(conf: str) -> bool:
    low = conf.lower()
    if "adapter" in low or "full_ft" in low or "fullft" in low:
        return False
    return True


def main() -> int:
    if np is None:
        print("  ❌ 需要 numpy")
        return 1

    runs, confs = [], {}
    for f in sorted(glob.glob(str(REPO / "outputs/theory/**/dg_star_history.json"), recursive=True)):
        parts = Path(f).parts
        conf = "/".join(parts[-4:-2])
        d = json.loads(io.open(f, encoding="utf-8").read())
        if len(d["epochs"]) < 5:
            continue
        if not is_lora(conf):
            continue
        runs.append((conf, d["epochs"], d["dg_star"]))
        confs.setdefault(conf, []).append((d["epochs"], d["dg_star"]))

    print(f"  LoRA-family runs: {len(runs)} ｜ 配置数: {len(confs)}")
    lens = sorted({len(y) for _, _, y in runs})
    print(f"  轨迹长度分布: {lens}")

    # 口径 ① 逐 run
    r1 = []
    for conf, ep, y in runs:
        A, B, R = grid_fit(ep, y)
        if R == R:
            r1.append(R)
    # 口径 ② 种子均值
    r2v = []
    for conf, rr in confs.items():
        n = min(len(y) for _, y in rr)
        y = [st.mean(x[i] for _, x in rr) for i in range(n)]
        A, B, R = grid_fit(rr[0][0][:n], y)
        if R == R:
            r2v.append(R)

    print(f"\n  === 口径 ① 逐 run（n={len(r1)}）===")
    print(f"    平均 {st.mean(r1):.4f} ｜ 中位 {st.median(r1):.4f} ｜ 范围 {min(r1):.3f}–{max(r1):.3f}")
    print(f"    ≥0.978 的比例: {sum(1 for x in r1 if x >= 0.978)}/{len(r1)}")
    print(f"\n  === 口径 ② 种子均值（n={len(r2v)}）===")
    print(f"    平均 {st.mean(r2v):.4f} ｜ 中位 {st.median(r2v):.4f} ｜ 范围 {min(r2v):.3f}–{max(r2v):.3f}")

    print(f"\n  === 正文声称 ===")
    print("    mean R² = 0.986（range 0.978–0.997），针对 **LoRA 配置**")
    for name, arr in (("逐 run", r1), ("种子均值", r2v)):
        m = st.mean(arr)
        hit = abs(m - 0.986) < 0.02
        print(f"    口径 {name}: 均值 {m:.4f} → {'✅ 与正文一致' if hit else '⚠ 不符'}")

    # 只看 10-epoch 的配置（正文口径）——上面已都是 10
    longest = [conf for conf, rr in confs.items() if max(len(y) for _, y in rr) == max(lens)]
    print(f"\n  最长轨迹（{max(lens)} epoch）的配置数: {len(longest)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
