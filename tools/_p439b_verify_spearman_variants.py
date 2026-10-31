# -*- coding: utf-8 -*-
r"""核 p3-downstream 的更正：三个 Spearman 口径（2026-10-12）。

## 它更正了什么

上一条它写 *"Spearman(ΔE_test, ΔR@1) = −0.3742 → 能量降幅与下游收益负相关"* ——
**把整体相关当成了子集内的单调关系**。真实的三个口径：

| 口径 | Spearman | n |
|---|---|---|
| **ΔE_train vs ΔR@1**（论文 ΔE 的直接类比） | **+0.478** | 78 |
| ΔE_test vs ΔR@1（全体） | **−0.374**（我算 −0.3819 @ n=79） | 78 |
| ΔE_test vs ΔR@1，**只在 ΔE_test<0 内** | **+0.171** | 54 |
| ΔE_test vs ΔR@1，只看 real | −0.691 | 39 |

**⚠️ 这直接影响我刚写进 `experiments.tex` 的那句**：
我写的是 *"improving the energy is associated with worse retrieval"*，依据是全体 −0.3819。
若子集内只有 +0.171（几乎无关），**我那句要改**——否则我也犯了同一个错。

    python tools\_p439b_verify_spearman_variants.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import statistics
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "p3_spearman_variants.json"


def spearman(xs, ys):
    def rank(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
                j += 1
            avg = (i + j) / 2.0 + 1
            for k in range(i, j + 1):
                r[order[k]] = avg
            i = j + 1
        return r
    rx, ry = rank(xs), rank(ys)
    n = len(xs)
    mx, my = statistics.mean(rx), statistics.mean(ry)
    num = sum((rx[i] - mx) * (ry[i] - my) for i in range(n))
    dx = sum((rx[i] - mx) ** 2 for i in range(n)) ** 0.5
    dy = sum((ry[i] - my) ** 2 for i in range(n)) ** 0.5
    return num / (dx * dy) if dx and dy else float("nan")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    d = json.loads(io.open(REPO / "outputs/analysis/p3d_clip_ranksweep.json",
                           encoding="utf-8", errors="replace").read())
    runs = d.get("runs") if isinstance(d, dict) else d
    rows = []
    for r in runs:
        e_tr, e_te, r1 = r.get("dE_train"), r.get("dE_test"), r.get("R@1")
        if e_tr is None or e_te is None or r1 is None:
            continue
        rows.append({"cond": r.get("condition"), "n": r.get("n_train"), "rank": r.get("rank"),
                     "seed": r.get("seed"), "dE_tr": e_tr, "dE_te": e_te,
                     "dR1": r1 - 0.7058})
    print(f"  可用 run = {len(rows)}")
    rep = {"n": len(rows)}

    def report(label, sel, xkey):
        if len(sel) < 3:
            print(f"  {label:<46} n={len(sel)} 样本不足")
            return
        rho = spearman([s[xkey] for s in sel], [s["dR1"] for s in sel])
        print(f"  {label:<46} **{rho:+.4f}**  (n={len(sel)})")
        rep[label] = {"rho": round(rho, 6), "n": len(sel)}

    print("=" * 100)
    print("独立重算四个口径")
    print("=" * 100)
    report("ΔE_train vs ΔR@1（论文类比）", rows, "dE_tr")
    report("ΔE_test vs ΔR@1（全体）", rows, "dE_te")
    report("ΔE_test vs ΔR@1（仅 ΔE_test<0）", [s for s in rows if s["dE_te"] < 0], "dE_te")
    report("ΔE_test vs ΔR@1（仅 ΔE_test>0）", [s for s in rows if s["dE_te"] > 0], "dE_te")
    report("ΔE_test vs ΔR@1（仅 real）", [s for s in rows if s["cond"] == "real"], "dE_te")
    report("ΔE_test vs ΔR@1（仅 blank）", [s for s in rows if s["cond"] == "blank"], "dE_te")

    print()
    print("=" * 100)
    print("配对比较（同 rank / 同 n / 同 seed，real → blank）")
    print("=" * 100)
    from collections import defaultdict
    g = defaultdict(dict)
    for s in rows:
        g[(s["n"], s["rank"], s["seed"])][s["cond"]] = s
    pr = []
    for k, v in sorted(g.items()):
        if "real" in v and "blank" in v:
            pr.append((k, v["blank"]["dE_te"] - v["real"]["dE_te"],
                       v["blank"]["dR1"] - v["real"]["dR1"]))
    print(f"  配对数 = {len(pr)}")
    for n in sorted(set(k[0] for k, _, _ in pr)):
        sub = [(de, dr) for k, de, dr in pr if k[0] == n]
        print(f"     n={n}: {len(sub)} 对 ｜ Δ(ΔE_test) 均值 {statistics.mean(x for x,_ in sub):+.5f} "
              f"｜ Δ(ΔR@1) 均值 {statistics.mean(y for _,y in sub):+.5f} "
              f"｜ 范围 [{min(y for _,y in sub):+.4f}, {max(y for _,y in sub):+.4f}]")
        rep[f"paired_n{n}"] = {"n_pairs": len(sub),
                               "mean_ddE": round(statistics.mean(x for x, _ in sub), 6),
                               "mean_ddR1": round(statistics.mean(y for _, y in sub), 6),
                               "dR1_range": [round(min(y for _, y in sub), 4),
                                             round(max(y for _, y in sub), 4)]}

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(rep, ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
