# -*- coding: utf-8 -*-
r"""实验 ⑤ 第三版：**DG 作为在线健康信号**的完整检验（2026-10-07）。

## 前两版的缺陷（逐版承认）

| 版本 | 做法 | 缺陷 |
|---|---|---|
| v1 | 取 **DG 最小 epoch** 作早停 | **事后择优（oracle）**，部署中不可用 |
| v2 | 5 种**可实现**早停规则 vs 不早停 | ✅ 方法可信，但**评价指标是 CG**，而目标是 **R@1** |

**且 v2 的控制被告知：**归档里 `results.json` **只有末态检索指标**（无逐 epoch R@1）
→ **早停对检索的影响无法用归档直接测**。本版据此改为测**可直接测**的三件事。

## 本版测什么

| # | 问题 | 可用数据 |
|---|---|---|
| **Q1** | **早停（只训 1–2 epoch）在检索上损失多少？** | `results.json` 的末态 R@1 + `gap_history.json` 的逐 epoch DG |
| **Q2** | **epoch-1 的 DG 变化能否预测末态 R@1？** | 同上 |
| **Q3** | **DG 轨迹与 CG 轨迹是否给出相同的"哪个 epoch 最好"？** | 逐 epoch DG 与 CG |

**判据（事先写明）**：
- Q1：若早停的平均 R@1 损失 > 0.05 → 早停代价大，**"DG 早停"需谨慎表述**；
- Q2：若 \|r\| ≥ 0.5 且 p < 0.05 → DG 首步变化可作**配置筛选**信号（非早停）；
- Q3：一致率 < 70% → **DG 与 CG 的"最优 epoch"不同**，DG 不能替代任务指标作停止准则。

    python tools\_p3_monitor_dg3.py [--apply]
"""
from __future__ import annotations

import glob
import io
import json
import math
import statistics as st
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "monitor_dg_check3.json"


def pearson(xs, ys):
    n = len(xs)
    if n < 3:
        return float("nan"), float("nan")
    mx, my = st.mean(xs), st.mean(ys)
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    if sxx <= 0 or syy <= 0:
        return float("nan"), float("nan")
    r = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / (sxx * syy) ** 0.5
    t = r * ((n - 2) / max(1e-12, 1 - r * r)) ** 0.5
    p = 2 * (1 - 0.5 * (1 + math.erf(abs(t) / 2 ** 0.5)))
    return r, p


def main() -> int:
    apply = "--apply" in sys.argv
    rows = []
    for f in sorted(glob.glob(str(REPO / "outputs/theory/**/dg_star_history.json"), recursive=True)):
        rel = Path(f).relative_to(REPO / "outputs" / "theory")
        base = f.rsplit("/", 1)[0].rsplit("\\", 1)[0]
        d = json.loads(io.open(f, encoding="utf-8").read())
        # 末态 R@1
        r1 = None
        for name in ("results.json", "v1_result.json", "adapter_result.json", "coco_result.json"):
            p = Path(base) / name
            if p.exists():
                try:
                    m = json.loads(io.open(p, encoding="utf-8").read())
                    if isinstance(m, dict):
                        if "final_task_metrics" in m:
                            r1 = m["final_task_metrics"].get("R@1")
                        elif "final_r1" in m:
                            r1 = m["final_r1"]
                    if r1 is not None:
                        break
                except Exception:
                    pass
        rows.append(dict(conf="/".join(rel.parts[:-2]), seed=rel.parts[-2],
                         dg=d.get("dg_star", []), cg=d.get("cg", []), r1=r1))
    have = [r for r in rows if r["r1"] is not None and len(r["dg"]) >= 5]
    print(f"  轨迹 {len(rows)} 条 ｜ 其中含末态 R@1: {len(have)}")
    if have:
        print(f"  末态 R@1 范围: {min(r['r1'] for r in have):.3f}–{max(r['r1'] for r in have):.3f}")

    # ── Q1：早停的检索代价（用"只训 k epoch"不可得 → 用 DG 变化幅度作代理不可靠）
    print(f"\n  === Q1：逐 epoch 检索缺失 → 改测「DG 变化幅度 vs 末态 R@1」===")
    xs = [(r["dg"][1] - r["dg"][0]) / abs(r["dg"][0]) for r in have]
    ys = [r["r1"] for r in have]
    r_q1, p_q1 = pearson(xs, ys)
    print(f"    corr(epoch-1 DG 相对变化, 末态 R@1) = {r_q1:+.3f}  (p≈{p_q1:.3g}, n={len(xs)})")
    # 也测 DG 绝对水平与 R@1
    xs2 = [r["dg"][0] for r in have]
    r_q1b, p_q1b = pearson(xs2, ys)
    print(f"    corr(初始 DG*, 末态 R@1)            = {r_q1b:+.3f}  (p≈{p_q1b:.3g})")
    xs3 = [r["dg"][-1] for r in have]
    r_q1c, p_q1c = pearson(xs3, ys)
    print(f"    corr(末态 DG*, 末态 R@1)            = {r_q1c:+.3f}  (p≈{p_q1c:.3g})")

    # ── Q3：DG 与 CG 的"最优 epoch"是否一致
    print(f"\n  === Q3：DG 与 CG 给出的「最优 epoch」是否一致 ===")
    agree = tot = 0
    for r in rows:
        if len(r["cg"]) < 5 or len(r["dg"]) < 5:
            continue
        i_dg = min(range(len(r["dg"])), key=lambda i: r["dg"][i])
        i_cg = min(range(len(r["cg"])), key=lambda i: r["cg"][i])
        tot += 1
        if i_dg == i_cg:
            agree += 1
    print(f"    一致 {agree}/{tot}（{100*agree/max(tot,1):.0f}%）")
    print(f"    → {'✅ 可替代' if tot and agree/tot >= 0.7 else '⚠ **不一致**：DG 不能替代任务指标作停止准则'}")

    print(f"\n  === 结论 ===")
    q2_ok = abs(r_q1) >= 0.5 and p_q1 < 0.05
    q3_ok = tot and agree / tot >= 0.7
    print(f"    Q1 首步 DG 变化→R@1 有预测力: {'✅' if q2_ok else '❌'}（r={r_q1:+.3f}）")
    print(f"    Q3 DG 与 CG 最优 epoch 一致:   {'✅' if q3_ok else '❌'}（{100*agree/max(tot,1):.0f}%）")
    if not q2_ok and not q3_ok:
        print("    ❌ **两项均不成立** → 论文的设计原则 ③ 应从 'principled application' "
              "改为**如实措辞**：DG 是自然状态变量，但**以 DG 作早停/调度尚未获支持**。")

    if apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(
            {"n_traj": len(rows), "n_with_r1": len(have),
             "corr_dg1chg_r1": r_q1, "p_dg1chg_r1": p_q1,
             "corr_dg0_r1": r_q1b, "p_dg0_r1": p_q1b,
             "corr_dgend_r1": r_q1c, "p_dgend_r1": p_q1c,
             "argmin_agree": agree, "argmin_total": tot,
             "argmin_agree_rate": agree / max(tot, 1)},
            ensure_ascii=False, indent=1))
        print(f"    ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
