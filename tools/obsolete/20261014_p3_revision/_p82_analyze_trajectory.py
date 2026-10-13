# -*- coding: utf-8 -*-
r"""分析**驱动项轨迹**并给出理论判定（2026-10-09）。

## 判据（在 `_p81` 里已先写明，此处复用）

- **轨迹平均后三臂极差 < 10%** → 理论的一阶项**确实无法**解释位置效应 → **须修订**；
- **≥ 10%** → 理论**可解释**，只是需要轨迹平均。

**同时报告**：
- 逐 epoch 极差（看演化趋势）；
- 三臂轨迹均值与符号；
- 与实测 CGΔ（极差 0.0571，4.4× 于均值）的对比。

    python tools\_p82_analyze_trajectory.py [--apply]
"""
from __future__ import annotations

import io
import json
import statistics as st
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "outputs" / "analysis" / "driving_trajectory.json"
OUT = REPO / "outputs" / "analysis" / "driving_verdict.json"
ARMS = ("text_only", "both", "vision_only")


def main() -> int:
    apply = "--apply" in sys.argv
    if not SRC.exists():
        print(f"  ⏳ 轨迹数据未就绪：{SRC.relative_to(REPO)}")
        return 1
    d = json.loads(io.open(SRC, encoding="utf-8").read())
    traj = d["trajectories"]

    n_ep = len(next(iter(traj.values())))
    print(f"=== 驱动项轨迹（{n_ep - 1} epoch + 初始）===")
    print(f"  {'ep':>3}" + "".join(f"{a:>15}" for a in ARMS) + f"{'极差/均值':>12}")
    spreads = []
    for ep in range(n_ep):
        vals = [traj[a][ep]["sum"] for a in ARMS]
        sp = (max(vals) - min(vals)) / abs(sum(vals) / 3) * 100
        spreads.append(sp)
        print(f"  {ep:>3}" + "".join(f"{v:>+15.4f}" for v in vals) + f"{sp:>11.2f}%")

    mean_traj = {a: st.mean(traj[a][ep]["sum"] for ep in range(n_ep)) for a in ARMS}
    mv = [mean_traj[a] for a in ARMS]
    sp_mean = (max(mv) - min(mv)) / abs(sum(mv) / 3) * 100

    print("\n=== 轨迹均值 ===")
    for a in ARMS:
        print(f"  {a:<13} {mean_traj[a]:>+12.4f}")
    print(f"  → **轨迹平均后极差 = {sp_mean:.2f}%**")

    # 逐 epoch 分量的均值（两侧分开看）
    print("\n=== 两侧分量（轨迹均值）===")
    print(f"  {'臂':<13}{'Σ<∇_vDG*,g_v>':>18}{'Σ<∇_tDG*,g_t>':>18}")
    comp = {}
    for a in ARMS:
        iv = st.mean(traj[a][ep]["ip_v"] for ep in range(n_ep))
        it = st.mean(traj[a][ep]["ip_t"] for ep in range(n_ep))
        comp[a] = {"ip_v": iv, "ip_t": it}
        print(f"  {a:<13}{iv:>+18.4f}{it:>+18.4f}")

    print("\n=== 与实测 CGΔ 的对比 ===")
    cg = {"text_only": -0.0465, "both": -0.0258, "vision_only": +0.0106}
    cgs = [cg[a] for a in ARMS]
    sp_cg = (max(cgs) - min(cgs)) / abs(sum(cgs) / 3) * 100
    print(f"  实测 CGΔ 极差 / 均值 = **{sp_cg:.1f}%**（绝对极差 {max(cgs)-min(cgs):.4f}）")
    print(f"  理论驱动项（轨迹平均）极差 / 均值 = **{sp_mean:.2f}%**")
    print(f"  → 相差 **{sp_cg/max(sp_mean,1e-9):.1f} 倍**")

    print("\n=== 排序对比 ===")
    o_th = sorted(ARMS, key=lambda a: -mean_traj[a])
    o_cg = sorted(ARMS, key=lambda a: cg[a])
    print(f"  按理论（轨迹平均驱动项，越大越应降低 gap）: {o_th}")
    print(f"  按实测（CGΔ 越小越好）                    : {o_cg}")
    same = o_th == o_cg
    print(f"  一致？ {'✅ 是' if same else '❌ 否'}")

    print("\n=== 判定 ===")
    if sp_mean < 10:
        verdict = ("first-order term cannot explain the position effect "
                   "even after trajectory averaging")
        print(f"  ❌ **轨迹平均后极差 {sp_mean:.2f}% < 10%**")
        print("     ⇒ **理论的一阶项确实无法解释位置效应** → **须修订理论**")
    else:
        verdict = "trajectory averaging widens the gap; theory can explain it"
        print(f"  ✅ **轨迹平均后极差 {sp_mean:.2f}% ≥ 10%**")
        print("     ⇒ 理论**可解释**，只是需要轨迹平均")

    if apply:
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps({
            "per_epoch_spread_pct": spreads,
            "trajectory_mean_spread_pct": sp_mean,
            "trajectory_means": mean_traj, "components": comp,
            "cg_delta_spread_pct": sp_cg, "ratio": sp_cg / max(sp_mean, 1e-9),
            "ordering_theory": o_th, "ordering_measured": o_cg, "ordering_same": same,
            "verdict": verdict,
        }, ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
