# -*- coding: utf-8 -*-
r"""交叉验证：我的组内结果 vs 论文**自己的归档**（`a1_h_seed_summary.json`）（2026-10-12）。

## 为什么要交叉验证

`_p209` 得出 **τ 组内 Fisher 均值 = −0.268**（几乎反向），
而 `cg` = +0.975、`margin` = +0.877。
**这直接推翻论文核心主张** → 必须先排除"我算错了"。

**验证方法**：用论文自己的 `within_dataset_rank_check`（τ 与 top-1 的**排名向量**）
独立复算组内相关。

    python tools\_p210_crosscheck_within.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import statistics as st
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
S1 = REPO / "outputs" / "a1_h_seed_summary.json"
S2 = REPO / "outputs" / "a1_h_offset.json"
OUT = REPO / "outputs" / "analysis" / "a1_within_crosscheck.json"


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
    out = {}

    print("=" * 92)
    print("① 论文自己的 within_dataset_rank_check（a1_h_seed_summary.json）")
    print("=" * 92)
    d1 = json.loads(io.open(S1, encoding="utf-8", errors="replace").read())
    wd = d1.get("within_dataset_rank_check", {})
    print("  " + json.dumps(wd, ensure_ascii=False, indent=1)[:1800])

    print()
    print("=" * 92)
    print("② 用其排名向量独立复算 τ 的组内相关")
    print("=" * 92)
    for ds, v in sorted(wd.items()):
        if not isinstance(v, dict):
            continue
        tr = v.get("tau_rank_of_seeds")
        pr = v.get("top1_rank_of_seeds")
        if not (isinstance(tr, list) and isinstance(pr, list) and len(tr) == len(pr)):
            continue
        # 排名向量之间的相关（Spearman of ranks = Pearson of ranks）
        rho_ranks = pearson(tr, pr)
        inv = "（反向）" if rho_ranks < 0 else ""
        print(f"  {ds:<14} tau_rank={tr}  top1_rank={pr}  → ρ={rho_ranks:+.4f} {inv}")
        out[ds] = {"tau_rank": tr, "top1_rank": pr, "rho_from_ranks": round(rho_ranks, 4)}

    print()
    print("=" * 92)
    print("③ 与 _p209 的结果对照（a1_h_offset.json 的 3-seed 组）")
    print("=" * 92)
    d2 = json.loads(io.open(S2, encoding="utf-8", errors="replace").read())
    by = {}
    for c in d2["checkpoints"]:
        by.setdefault(c.get("dataset"), []).append(c)
    print(f"  {'数据集':<14} {'_p209 ρ':>10} {'归档排名 ρ':>12}   一致？")
    for ds in sorted(by):
        rs = by[ds]
        if len(rs) < 3:
            continue
        xs = [r.get("summary_tau5") for r in rs]
        ys = [r.get("summary_top1_5k") for r in rs]
        if not all(isinstance(x, (int, float)) for x in xs + ys):
            continue
        rho209 = pearson(
            [sorted(xs).index(v) + 1 for v in xs],
            [sorted(ys).index(v) + 1 for v in ys])
        arch = out.get(ds, {}).get("rho_from_ranks")
        agree = ("✅" if arch is not None and abs(rho209 - arch) < 0.01 else
                 ("（无归档）" if arch is None else "⚠️ 不一致"))
        print(f"  {ds:<14} {rho209:>+10.4f} "
              f"{(f'{arch:+.4f}' if arch is not None else '—'):>12}   {agree}")
        out.setdefault(ds, {})["rho_p209"] = round(rho209, 4)
        out[ds]["agree"] = agree

    print()
    print("=" * 92)
    print("④ 判定")
    print("=" * 92)
    agrees = [v for v in out.values() if isinstance(v, dict) and "agree" in v]
    n_ok = sum(1 for v in agrees if v["agree"] == "✅")
    print(f"  我算的与归档排名向量一致的数据集: {n_ok}/{len(agrees)}")
    if n_ok == len(agrees) and agrees:
        print("  ✅ **我的计算与论文自己的归档一致** → 结论不是我算错，而是数据本身的属性")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(out, ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
