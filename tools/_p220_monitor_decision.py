# -*- coding: utf-8 -*-
r"""E-B：监控决策闭环 —— τ 作为停止准则 vs top-1（2026-10-12）。

## 要解决的缺口

审稿人：*"the deliverable is never exercised — no τ-triggered early stopping,
no checkpoint selection, no comparison against loss/top-1"*。

## 数据

`outputs/a1_epoch_sweep.json`（100 个检查点 = 10 条训练轨迹 × epoch1–10，
每条轨迹有逐 epoch 的 τ 与 top-1）。

## 三个决策实验（全部无需新训练）

| # | 实验 | 判据 |
|---|---|---|
| **D1** | **哪个信号先发现问题** | 每条轨迹里，τ 首次跌破阈值 vs top-1 首次跌破阈值的 epoch |
| **D2** | **早停选点**：按 τ 谷底停 vs 按 top-1 峰值停 | 停下的 epoch 与最终 top1 差 |
| **D3** | **选择准则**：τ / CG / 常数 选"最佳检查点" | 选中的 top1 与真实最优的差 |

**注意**：这里**没有 val_loss 的逐 epoch 数据**（只有 ImageNet 5k top-1 与 τ），
故 D2/D3 用 top-1 作对照，并**如实标注该限制**。

    python tools\_p220_monitor_decision.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import statistics as st
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "outputs" / "a1_epoch_sweep.json"
OUT = REPO / "outputs" / "analysis" / "a1_monitor_decision.json"


def pearson(xs, ys):
    n = len(xs)
    if n < 2:
        return float("nan")
    mx, my = st.mean(xs), st.mean(ys)
    num = sum((xs[i] - mx) * (ys[i] - my) for i in range(n))
    den = (sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys)) ** 0.5
    return num / den if den else float("nan")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    d = json.loads(io.open(SRC, encoding="utf-8", errors="replace").read())
    rows = [r for r in d["checkpoints"] if "error" not in r]
    frozen_top1 = d["meta"]["frozen_top1_5k"]

    traj = defaultdict(list)
    for r in rows:
        traj[f"{r['dataset']}|seed{r['seed']}"].append(r)
    for k in traj:
        traj[k].sort(key=lambda r: r["epoch"])

    print("=" * 92)
    print(f"① 数据：{len(rows)} 个检查点，{len(traj)} 条轨迹（冻结 top-1 = {frozen_top1:.2f}%）")
    print("=" * 92)
    for k in sorted(traj):
        v = traj[k]
        print(f"  {k:<24} n={len(v):<3} τ {v[0]['tau5']:.4f}→{v[-1]['tau5']:.4f} ｜ "
              f"top1 {v[0]['top1_5k']:.2f}→{v[-1]['top1_5k']:.2f}（冻结 {frozen_top1:.2f}）")

    # ── D1：谁先发现问题 ──
    print()
    print("=" * 92)
    print("② D1：τ 与 top-1 谁先跌破「冻结值 − 1 点」")
    print("=" * 92)
    thr_t1 = frozen_top1 - 1.0
    d1 = {}
    print(f"  阈值：top-1 < {thr_t1:.2f}%（= 冻结 − 1.0 点）")
    print(f"  {'轨迹':<24} {'τ首破':>8} {'top1首破':>9} {'τ更早?':>8}")
    for k in sorted(traj):
        v = traj[k]
        # τ 的阈值：用冻结的 τ（=1.0）与自身起点的比例；改用"τ 跌破起点 90%"
        tau_start = v[0]["tau5"]
        thr_tau = tau_start * 0.90
        e_tau = next((r["epoch"] for r in v if r["tau5"] < thr_tau), None)
        e_t1 = next((r["epoch"] for r in v if r["top1_5k"] < thr_t1), None)
        earlier = (e_tau is not None and (e_t1 is None or e_tau < e_t1))
        d1[k] = {"tau_break_epoch": e_tau, "top1_break_epoch": e_t1,
                 "tau_threshold": round(thr_tau, 4), "tau_earlier": earlier}
        print(f"  {k:<24} {str(e_tau):>8} {str(e_t1):>9} "
              f"{'✅ 是' if earlier else '否':>8}")
    n_earlier = sum(1 for v in d1.values() if v["tau_earlier"])
    n_both = sum(1 for v in d1.values() if v["tau_break_epoch"] and v["top1_break_epoch"])
    print(f"\n  → τ 更早: **{n_earlier}/{len(d1)}** 条轨迹"
          f"（两者都触发的 {n_both} 条中）")

    # ── D2：早停选点 ──
    print()
    print("=" * 92)
    print("③ D2：早停选点 —— 按 τ 谷底停 vs 按 top-1 峰值停")
    print("=" * 92)
    print(f"  {'轨迹':<24} {'τ最优ep':>8} {'top1最优ep':>10} {'τ选的top1':>10} "
          f"{'top1选的':>9} {'差':>7}")
    d2 = {}
    gaps = []
    for k in sorted(traj):
        v = traj[k]
        best_tau = max(v, key=lambda r: r["tau5"])
        best_t1 = max(v, key=lambda r: r["top1_5k"])
        gap = best_t1["top1_5k"] - best_tau["top1_5k"]
        gaps.append(gap)
        d2[k] = {"tau_best_epoch": best_tau["epoch"],
                 "top1_best_epoch": best_t1["epoch"],
                 "top1_at_tau_choice": best_tau["top1_5k"],
                 "top1_at_own_best": best_t1["top1_5k"],
                 "gap": round(gap, 4)}
        print(f"  {k:<24} {best_tau['epoch']:>8} {best_t1['epoch']:>10} "
              f"{best_tau['top1_5k']:>10.2f} {best_t1['top1_5k']:>9.2f} {gap:>+7.2f}")
    print(f"\n  用 τ 选点 vs 用 top-1 选点：平均损失 **{st.mean(gaps):+.2f} 点** "
          f"（范围 {min(gaps):+.2f} ~ {max(gaps):+.2f}）")
    print(f"  → {'✅ τ 选点几乎无损（差 <0.5 点）' if abs(st.mean(gaps)) < 0.5 else '⚠️ τ 选点有明显损失'}")

    # ── D3：τ 达峰后是否该停 ──
    print()
    print("=" * 92)
    print("④ D3：若在「τ 达峰」处停止，相对训练到 epoch10 的收益")
    print("=" * 92)
    gains = []
    for k in sorted(traj):
        v = traj[k]
        best_tau = max(v, key=lambda r: r["tau5"])
        last = v[-1]
        gains.append(best_tau["top1_5k"] - last["top1_5k"])
    print(f"  平均收益 **{st.mean(gains):+.2f} 点**（范围 {min(gains):+.2f} ~ {max(gains):+.2f}）")
    print(f"  为正的轨迹: {sum(1 for g in gains if g > 0)}/{len(gains)}")
    print(f"  → {'✅ 在 τ 达峰处停比继续训到 ep10 更好' if st.mean(gains) > 0 else '⚠️ 无收益'}")

    # ── D4：τ 与 top1 的相关（组内）──
    print()
    print("=" * 92)
    print("⑤ D4：逐轨迹 τ–top1 相关（决策可行性的前提）")
    print("=" * 92)
    rhos = []
    for k in sorted(traj):
        v = traj[k]
        rho = pearson([r["tau5"] for r in v], [r["top1_5k"] for r in v])
        rhos.append(rho)
    print(f"  10 条轨迹 Pearson(τ, top1)：均值 **{st.mean(rhos):+.4f}**，"
          f"最小 {min(rhos):+.4f}，最大 {max(rhos):+.4f}")
    print(f"  全部为正: {'✅ 是' if all(r > 0 for r in rhos) else '否'}")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(
            {"source": str(SRC.relative_to(REPO)), "frozen_top1_5k": frozen_top1,
             "n_trajectories": len(traj),
             "D1_earlier_detection": d1,
             "D1_tau_earlier_count": n_earlier,
             "D2_stopping_point": d2,
             "D2_mean_gap": round(st.mean(gaps), 4),
             "D3_gain_if_stop_at_tau_peak": round(st.mean(gains), 4),
             "D4_per_trajectory_pearson": [round(r, 4) for r in rhos],
             "D4_mean_pearson": round(st.mean(rhos), 4),
             "limitation": "no per-epoch validation loss in this archive; top-1 is the only "
                           "downstream signal available for the comparison"},
            ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
