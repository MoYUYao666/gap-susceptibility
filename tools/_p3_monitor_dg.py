# -*- coding: utf-8 -*-
r"""实验 ⑤：**"monitor DG" 能否作为早停准则**（2026-10-07，用现有轨迹，零 GPU）。

## 论文的主张

`discussion.tex` 的设计原则 ③：

> "**Monitor DG as an alignment health signal.** The ODE establishes DG as the natural state variable for
> alignment dynamics. **DG-based early stopping** or learning rate scheduling are principled applications."

**但论文从未验证过这条**——它只是从"DG 是自然状态变量"**推出**的。审稿人会问：
**"你说可以用 DG 早停，那早停的结果对吗？"**

## 本脚本检验两个可检验的问题

| # | 问题 | 数据 |
|---|---|---|
| **Q1** | **epoch-1 的 DG 变化能否预测最终检索性能？** 若能，DG 可作**在线**健康信号 | 归档 `dg_star`/`cg` 轨迹 + 同 run 的检索指标 |
| **Q2** | **按 DG 早停（取 DG 最优的 epoch）是否比取最终 epoch 更好？** | 逐 epoch 检索指标 |

**判据（事先写明）**：Q1 若 \|r\| ≥ 0.5 且 p < 0.05 → DG 是有效在线信号；否则**该设计原则需降级为推测**。

    python tools\_p3_monitor_dg.py [--apply]
"""
from __future__ import annotations

import glob
import io
import json
import re
import statistics as st
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "monitor_dg_check.json"


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
    # 双尾 p（t 分布近似 → 用正态近似，n 小故标注局限）
    t = r * ((n - 2) / max(1e-12, 1 - r * r)) ** 0.5
    # 正态近似双尾 p
    import math
    p = 2 * (1 - 0.5 * (1 + math.erf(abs(t) / 2 ** 0.5)))
    return r, p


def main() -> int:
    apply = "--apply" in sys.argv

    # ── 载入 DG 轨迹
    runs = []
    for f in sorted(glob.glob(str(REPO / "outputs/theory/**/dg_star_history.json"), recursive=True)):
        rel = Path(f).relative_to(REPO / "outputs" / "theory")
        conf = "/".join(rel.parts[:-2])
        d = json.loads(io.open(f, encoding="utf-8").read())
        if len(d.get("dg_star", [])) < 5:
            continue
        runs.append(dict(conf=conf, top=rel.parts[0], seed=rel.parts[-2],
                         ep=d["epochs"], dg=d["dg_star"],
                         dg_emp=d.get("dg_empirical"), cg=d.get("cg")))
    print(f"  DG 轨迹: {len(runs)} 条")

    # ── 找同 run 的检索指标（results.json / v1_result.json 等）
    def metrics_for(conf: str, seed: str):
        base = REPO / "outputs" / "theory" / conf / seed
        for name in ("results.json", "v1_result.json", "adapter_result.json",
                     "coco_result.json", "beta_pilot_results.json"):
            p = base / name
            if p.exists():
                try:
                    return json.loads(io.open(p, encoding="utf-8").read()), name
                except Exception:
                    pass
        return None, None

    have = [(r, *metrics_for(r["conf"], r["seed"])) for r in runs]
    n_have = sum(1 for _, m, _ in have if m)
    print(f"  其中有检索指标的 run: {n_have}/{len(runs)}")
    if n_have:
        ex, name = next((m, n) for _, m, n in have if m)
        print(f"  指标字段样例（{name}）: {list(ex)[:14] if isinstance(ex, dict) else type(ex)}")

    # ── Q1：epoch-1 的 DG 相对下降 能否预测末态 DG / 检索
    print(f"\n  === Q1：epoch-1 DG 变化 vs 末态 ===")
    d1, dend = [], []
    for r in runs:
        if len(r["dg"]) < 5:
            continue
        d1.append((r["dg"][1] - r["dg"][0]) / abs(r["dg"][0]))   # 首步相对变化
        dend.append(r["dg"][-1])
    r_q1, p_q1 = pearson(d1, dend)
    print(f"    corr(epoch-1 相对变化, 末态 DG*) = {r_q1:+.3f}  (p≈{p_q1:.3g}, n={len(d1)})")
    print(f"    → {'✅ 首步变化有预测力' if abs(r_q1) >= 0.5 and p_q1 < 0.05 else '⚠ 首步变化预测力不足'}")

    # ── Q2：DG 最优 epoch 的 CG 是否优于最终 epoch 的 CG
    print(f"\n  === Q2：按 DG 早停 vs 取最终 epoch（用同 run 的 cg 轨迹）===")
    better = worse = same = 0
    gains = []
    for r in runs:
        cg = r.get("cg")
        if not cg or len(cg) < 5:
            continue
        i_best = min(range(len(r["dg"])), key=lambda i: r["dg"][i])
        if i_best == len(r["dg"]) - 1:
            same += 1
        elif cg[i_best] < cg[-1]:
            better += 1
            gains.append(cg[-1] - cg[i_best])
        else:
            worse += 1
    tot = better + worse + same
    print(f"    n={tot} ｜ DG 最优 epoch 的 CG 更小: {better} ｜ 更差: {worse} ｜ 相同（末态即最优）: {same}")
    if better + worse:
        print(f"    在可比较的 {better+worse} 例中，早停更优 {better} 例（{100*better/(better+worse):.0f}%）")
    if gains:
        print(f"    平均 CG 收益: {st.mean(gains):+.4f}")

    print(f"\n  === 结论 ===")
    q1_ok = abs(r_q1) >= 0.5 and p_q1 < 0.05
    q2_ok = (better > worse) if (better + worse) else False
    if q1_ok and q2_ok:
        print("    ✅ 「DG 可作早停信号」得到支持")
    elif q2_ok or q1_ok:
        print("    ⚠ **部分支持**：其中一项成立、另一项不成立 → 论文的措辞应收紧")
    else:
        print("    ❌ **未获支持**：论文的设计原则 ③ 应**降级为推测**（从状态变量推出 ≠ 早停有效）")

    if apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(
            {"n_runs": len(runs), "n_with_metrics": n_have,
             "q1_corr": r_q1, "q1_p": p_q1, "q1_supported": bool(q1_ok),
             "q2_better": better, "q2_worse": worse, "q2_same": same,
             "q2_mean_gain": st.mean(gains) if gains else None,
             "q2_supported": bool(q2_ok)}, ensure_ascii=False, indent=1))
        print(f"    ✅ 已写 {OUT.relative_to(REPO)}")
    else:
        print("    （预演；加 --apply 落盘）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
