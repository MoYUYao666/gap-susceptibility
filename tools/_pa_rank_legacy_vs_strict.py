# -*- coding: utf-8 -*-
r"""对照 legacy 约定与严格冻结下的 rank 效应（核实"lower rank preserves better"的来源与现状）。

## 为什么要对照

正文两处（`empirical.tex:59`、`:124`）称 "**lower LoRA rank preserves alignment better**"，
原始依据是 `docs/P1_REVIEW_OVERLAP.md:47`：

> "Lower ranks ($r=4,8,16$) consistently reduce or maintain the gap, while higher ranks ($r=32,64$)
> tend to increase it. On Flickr30k, rank-4 achieves..."

那是在 **legacy 约定**（`src/lora.py` 不冻结基座）下测的。本次 **rank sweep 在严格冻结下**测出相反趋势，
故必须**并排核对两者**，判断是"约定改变导致方向反转"，还是别的差异。

## 数据来源

- legacy：`outputs/flickr30k/rq1_rank{4,8,16,32,64}/gap_history.json`
- 严格冻结：`outputs/strict_freeze/`（rank8）与 `outputs/strict_freeze_rank/r{4,16,32}/`

    python tools\_pa_rank_legacy_vs_strict.py
"""
from __future__ import annotations

import glob
import io
import json
import statistics as st
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def legacy() -> list[tuple[int, float]]:
    out = []
    for p in sorted(glob.glob(str(REPO / "outputs" / "flickr30k" / "rq1_rank*" / "gap_history.json"))):
        name = Path(p).parent.name
        rk = name.replace("rq1_rank", "")
        try:
            rk_i = int(rk)
        except ValueError:
            continue
        d = json.loads(io.open(p, encoding="utf-8", errors="ignore").read())
        cg = d.get("centroid_gap")
        if cg and len(cg) >= 2:
            out.append((rk_i, cg[-1] - cg[0]))
    return sorted(out)


def strict() -> list[tuple[int, float]]:
    src = {4: "outputs/strict_freeze_rank/r4", 8: "outputs/strict_freeze",
           16: "outputs/strict_freeze_rank/r16", 32: "outputs/strict_freeze_rank/r32"}
    out = []
    for rk, root in sorted(src.items()):
        vs = []
        for p in glob.glob(str(REPO / root / "text_only" / "seed*" / "results.json")):
            d = json.loads(io.open(p, encoding="utf-8", errors="ignore").read())
            vs.append(d["final_gap"]["centroid_gap"] - d["initial_gap"]["centroid_gap"])
        if vs:
            out.append((rk, st.mean(vs)))
    return sorted(out)


def main() -> int:
    L, S = legacy(), strict()
    print("=== legacy 约定（不冻结基座）：text_only 的 ΔCG 随 rank ===")
    if L:
        for rk, d in L:
            print("  rank %-3d ΔCG=%+.4f" % (rk, d))
        ds = [d for _, d in L]
        print("  → 单调递增（低 rank 更负）: %s" % all(ds[i] <= ds[i + 1] for i in range(len(ds) - 1)))
    else:
        print("  未找到数据")

    print("\n=== 严格冻结：text_only 的 ΔCG 随 rank ===")
    for rk, d in S:
        print("  rank %-3d ΔCG=%+.4f" % (rk, d))
    ds = [d for _, d in S]
    print("  → 单调递增（低 rank 更负）: %s" % all(ds[i] <= ds[i + 1] for i in range(len(ds) - 1)))
    print("  → 单调递减（高 rank 更负）: %s" % all(ds[i] >= ds[i + 1] for i in range(len(ds) - 1)))

    print("\n=== 判定 ===")
    if L and S:
        lin = all([d for _, d in L][i] <= [d for _, d in L][i + 1] for i in range(len(L) - 1))
        sin = all([d for _, d in S][i] <= [d for _, d in S][i + 1] for i in range(len(S) - 1))
        print("  legacy 支持『lower rank preserves better』: %s" % lin)
        print("  严格冻结支持同一说法: %s" % sin)
        print("  → 结论：%s" % ("两种约定下方向不一致，正文必须按约定分别陈述"
                               if lin != sin else "两种约定方向一致"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
