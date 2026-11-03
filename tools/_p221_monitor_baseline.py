# -*- coding: utf-8 -*-
r"""E-B 补强：把"停早更好"与**最简单基线**对照（2026-10-12）。

## 为什么必须补

`_p220` 的 D3 得出"按 τ 达峰停 → +2.30 点（10/10 为正）"。
**但 τ 在 10 条轨迹里全部于 epoch 1 达峰**，而各指标的 top-1 也在 epoch 1–2 最高
→ "停早有收益"可能只是"这条轨迹一开始就最好"，**与 τ 无关**。

**必须对照的基线**：
| 基线 | 说明 |
|---|---|
| **固定 `epoch=1`** | 不看任何信号，总在第一轮停 |
| **固定 `epoch=2`** | 同上 |
| **固定 `epoch=3`** | 同上 |
| **τ 达峰** | 本方法 |
| **top-1 达峰** | 已知最优（但它需要 ImageNet 标签，非零开销） |

**另有 D1 的修正**：原用"跌破起点 90%"阈值过于粗糙；
改用**首次单调下降**（`τ_e < τ_{e-1}` 且此后不再创新高）。

    python tools\_p221_monitor_baseline.py [--apply]
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
OUT = REPO / "outputs" / "analysis" / "a1_monitor_baseline.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    d = json.loads(io.open(SRC, encoding="utf-8", errors="replace").read())
    frozen = d["meta"]["frozen_top1_5k"]
    traj = defaultdict(list)
    for r in d["checkpoints"]:
        if "error" in r:
            continue
        traj[f"{r['dataset']}|seed{r['seed']}"].append(r)
    for k in traj:
        traj[k].sort(key=lambda r: r["epoch"])
    keys = sorted(traj)

    print("=" * 94)
    print("① 各「停止准则」选出的检查点 top-1（同一批 10 条轨迹）")
    print("=" * 94)
    print(f"  {'轨迹':<22}" + "".join(f"{c:>11}" for c in
          ("ep1", "ep2", "ep3", "τ峰", "top1峰", "ep10")) + f"{'最优':>9}")
    rows = {}
    for k in keys:
        v = traj[k]
        best_tau = max(v, key=lambda r: r["tau5"])
        best_t1 = max(v, key=lambda r: r["top1_5k"])
        opt = best_t1["top1_5k"]
        r = {
            "ep1": v[0]["top1_5k"], "ep2": v[1]["top1_5k"] if len(v) > 1 else None,
            "ep3": v[2]["top1_5k"] if len(v) > 2 else None,
            "tau_peak": best_tau["top1_5k"], "top1_peak": opt, "ep10": v[-1]["top1_5k"],
            "tau_peak_epoch": best_tau["epoch"], "top1_peak_epoch": best_t1["epoch"],
        }
        rows[k] = r
        print(f"  {k:<22}" + "".join(
            f"{r[c]:>11.2f}" for c in ("ep1", "ep2", "ep3", "tau_peak", "top1_peak",
                                       "ep10")) + f"{opt:>9.2f}")

    print()
    print("=" * 94)
    print("② 各准则的平均 top-1 与「相对已知最优的损失」")
    print("=" * 94)
    print(f"  {'准则':<28}{'平均 top-1':>12}{'平均损失':>12}{'中位损失':>12}{'零损失轨迹':>12}")
    summary = {}
    for c in ("ep1", "ep2", "ep3", "tau_peak", "top1_peak", "ep10"):
        vals = [rows[k][c] for k in keys if rows[k][c] is not None]
        losses = [rows[k]["top1_peak"] - rows[k][c] for k in keys
                  if rows[k][c] is not None]
        summary[c] = {"mean_top1": round(st.mean(vals), 4),
                      "mean_loss": round(st.mean(losses), 4),
                      "median_loss": round(st.median(losses), 4),
                      "n_zero_loss": sum(1 for x in losses if abs(x) < 1e-9),
                      "n": len(vals)}
        label = {"ep1": "固定 epoch 1（无信号）",
                 "ep2": "固定 epoch 2（无信号）",
                 "ep3": "固定 epoch 3（无信号）",
                 "tau_peak": "★ τ 达峰（本方法）",
                 "top1_peak": "top-1 达峰（需标签）",
                 "ep10": "训到 epoch 10"}[c]
        print(f"  {label:<28}{summary[c]['mean_top1']:>12.2f}"
              f"{summary[c]['mean_loss']:>+12.2f}{summary[c]['median_loss']:>+12.2f}"
              f"{summary[c]['n_zero_loss']:>10}/{len(keys)}")

    print()
    print("=" * 94)
    print("③ 判定：τ 是否优于「不看信号的固定 epoch」")
    print("=" * 94)
    best_fixed = min(("ep1", "ep2", "ep3"), key=lambda c: summary[c]["mean_loss"])
    tau_loss = summary["tau_peak"]["mean_loss"]
    fixed_loss = summary[best_fixed]["mean_loss"]
    print(f"  最好的固定基线 = {best_fixed}（平均损失 {fixed_loss:+.2f}）")
    print(f"  τ 达峰           = 平均损失 {tau_loss:+.2f}")
    if abs(tau_loss - fixed_loss) < 0.15:
        print(f"  🔴 **τ 与「固定 {best_fixed}」无实质差别** → 停止决策上 τ 未显示额外价值")
    elif tau_loss < fixed_loss:
        print(f"  ✅ τ 优于最好的固定基线（省 {fixed_loss - tau_loss:+.2f} 点）")
    else:
        print(f"  🔴 τ 差于最好的固定基线")

    print()
    print("=" * 94)
    print("④ D1 修正：首次「单调下降」发生在第几轮")
    print("=" * 94)
    print(f"  {'轨迹':<22}{'τ 首降':>9}{'top1 首降':>11}{'τ更早':>9}")
    earlier = 0
    det = {}
    for k in keys:
        v = traj[k]
        e_tau = next((v[i]["epoch"] for i in range(1, len(v))
                      if v[i]["tau5"] < v[i - 1]["tau5"]), None)
        e_t1 = next((v[i]["epoch"] for i in range(1, len(v))
                     if v[i]["top1_5k"] < v[i - 1]["top1_5k"]), None)
        fl = (e_tau is not None and (e_t1 is None or e_tau < e_t1))
        earlier += 1 if fl else 0
        det[k] = {"tau_first_drop": e_tau, "top1_first_drop": e_t1, "tau_earlier": fl}
        print(f"  {k:<22}{str(e_tau):>9}{str(e_t1):>11}{'✅' if fl else '否':>9}")
    print(f"\n  → τ 首次下降更早: **{earlier}/{len(keys)}** 条轨迹")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(
            {"source": str(SRC.relative_to(REPO)),
             "criteria_summary": summary,
             "per_trajectory": rows,
             "best_fixed_epoch": best_fixed,
             "tau_beat_best_fixed": tau_loss < fixed_loss - 0.15,
             "D1_first_drop": det,
             "D1_tau_earlier_count": earlier},
            ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
