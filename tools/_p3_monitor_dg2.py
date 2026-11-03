# -*- coding: utf-8 -*-
r"""实验 ⑤ 修正版：**用可实现规则**检验"DG 早停"（2026-10-07）。

## 第一版的缺陷（必须承认）

`_p3_monitor_dg.py` 的 Q2 取 **DG 最小的 epoch** 作早停点——那是**看了完整轨迹后的事后择优**，
**不是任何部署中可用的规则**。据此说"DG 早停无效"**过强**。

## 本版改测**三种可实现规则**

| 规则 | 定义 | 部署可行性 |
|---|---|---|
| **R1 平台化早停** | 当 $\|DG_t - DG_{t-1}\|/DG_{t-1} < \epsilon$ 时停（$\epsilon=1\%$），取**首次触发**的 epoch | ✅ 在线可算 |
| **R2 相对初值阈值** | 当 $DG_t / DG_0 < \theta$（$\theta=0.99$）时停 | ✅ 在线可算 |
| **R3 固定早停** | 固定停在第 $k$ 个 epoch（$k=2,3,5$） | ✅ 最简单基线 |

**比较对象**：不早停（取最终 epoch）的 CG。
**评价**：早停点的 CG 与最终 CG 之差（负=早停更好）。

**判据（事先写明）**：若三种规则中**多数**在可比较样本上不优于不早停，则论文的设计原则 ③
应从"principled application"**降级为"未经验证的推测"**。

    python tools\_p3_monitor_dg2.py [--apply]
"""
from __future__ import annotations

import glob
import io
import json
import statistics as st
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "monitor_dg_check2.json"


def main() -> int:
    apply = "--apply" in sys.argv
    runs = []
    for f in sorted(glob.glob(str(REPO / "outputs/theory/**/dg_star_history.json"), recursive=True)):
        rel = Path(f).relative_to(REPO / "outputs" / "theory")
        d = json.loads(io.open(f, encoding="utf-8").read())
        if len(d.get("dg_star", [])) < 5 or not d.get("cg"):
            continue
        runs.append(dict(conf="/".join(rel.parts[:-2]), seed=rel.parts[-2],
                         dg=d["dg_star"], cg=d["cg"]))
    print(f"  可用 run（含 DG* 与 CG 轨迹）: {len(runs)}")

    def first_trigger(tr, rule):
        if rule == "R1":
            for i in range(1, len(tr)):
                if abs(tr[i] - tr[i - 1]) / max(abs(tr[i - 1]), 1e-12) < 0.01:
                    return i
            return len(tr) - 1
        if rule == "R2":
            for i in range(1, len(tr)):
                if tr[i] / max(abs(tr[0]), 1e-12) < 0.99:
                    return i
            return len(tr) - 1
        raise ValueError(rule)

    print(f"\n  === 可实现规则 vs 不早停（差 <0 表示早停更好）===")
    print(f"  {'规则':<22} {'可比较 n':>8} {'早停更优':>8} {'更差':>6} {'相同':>6} {'平均 CG 差':>12}")
    print("  " + "-" * 74)
    res = {}
    rules = [("R1 平台化(ε=1%)", lambda tr: first_trigger(tr, "R1")),
             ("R2 相对初值(θ=0.99)", lambda tr: first_trigger(tr, "R2")),
             ("R3 固定停 k=2", lambda tr: min(1, len(tr) - 1)),
             ("R3 固定停 k=3", lambda tr: min(2, len(tr) - 1)),
             ("R3 固定停 k=5", lambda tr: min(4, len(tr) - 1))]
    for name, fn in rules:
        better = worse = same = 0
        diffs = []
        for r in runs:
            k = fn(r["dg"])
            if k >= len(r["cg"]) - 1:
                same += 1
                continue
            d = r["cg"][k] - r["cg"][-1]
            diffs.append(d)
            if d < -1e-9:
                better += 1
            elif d > 1e-9:
                worse += 1
            else:
                same += 1
        mean_d = st.mean(diffs) if diffs else float("nan")
        res[name] = dict(n=len(diffs), better=better, worse=worse, same=same, mean_diff=mean_d)
        print(f"  {name:<22} {len(diffs):>8} {better:>8} {worse:>6} {same:>6} {mean_d:>+12.4f}")

    print(f"\n  === 可部署规则的触发点分布（R1/R2）===")
    for name in ("R1 平台化(ε=1%)", "R2 相对初值(θ=0.99)"):
        ks = [first_trigger(r["dg"], name[:2]) for r in runs]
        import collections
        print(f"    {name}: epoch 分布 {dict(sorted(collections.Counter(ks).items()))}")

    print(f"\n  === 结论 ===")
    ok = sum(1 for v in res.values() if v["n"] and v["better"] > v["worse"])
    print(f"    5 种规则中，早停优于不早停的: **{ok}/5**")
    if ok == 0:
        print("    ❌ **论文的设计原则 ③（DG 早停）在归档轨迹上未获支持**")
        print("       → 应把 'principled applications' 改为如实措辞：DG 是自然状态变量，")
        print("         但**早停是否受益尚未验证**（本检验给出负面证据）。")
    elif ok < 3:
        print("    ⚠ **部分支持**：措辞应收紧并附条件")
    else:
        print("    ✅ 支持 DG 早停")

    if apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(
            {"n_runs": len(runs), "rules": res, "rules_favouring_early_stop": ok},
            ensure_ascii=False, indent=1))
        print(f"    ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
