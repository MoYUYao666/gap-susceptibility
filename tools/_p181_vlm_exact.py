# -*- coding: utf-8 -*-
r"""从**原始 per-seed 文件**重算 VLM 精确统计（不经 2 位取整的汇总）（2026-10-11）。

## 为什么

`vlm_bf16_detail.json` 的 `summary` 是 `round(x, 2)` 后的值 → 从它再取整会引入二次误差
（如 `sd=5.35` 被论文写成 `5.3`，而正确写法是 `5.4`；`max=95.05` 被写成 `95.1`，正确是 `95.0`）。

**本脚本**：直接读 `outputs/vlm_seeds_bf16/*_seed*.json`，算**未取整**的 mean/sd/min/max，
并给出**论文应写的 1 位小数**。

    python tools\_p181_vlm_exact.py [--apply]
"""
from __future__ import annotations

import argparse
import glob
import io
import json
import statistics as st
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "vlm_exact.json"


def round_half_up(x: float, digits: int = 1) -> float:
    """标准四舍五入（Python 的 round 是银行家舍入）。"""
    from decimal import Decimal, ROUND_HALF_UP
    q = Decimal(1).scaleb(-digits)
    return float(Decimal(str(x)).quantize(q, rounding=ROUND_HALF_UP))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    rows = defaultdict(list)
    for f in sorted(glob.glob(str(REPO / "outputs" / "vlm_seeds_bf16" / "*_seed*.json"))):
        d = json.loads(io.open(f, encoding="utf-8", errors="replace").read())
        dg = d.get("dg_star") or []
        cg = d.get("cg") or []
        if len(dg) >= 2 and dg[0]:
            rows[d["arm"]].append({
                "seed": d["seed"],
                "rel": (dg[0] - dg[-1]) / dg[0] * 100.0,
                "cg_span": max(cg) - min(cg) if cg else None,
            })

    print("=" * 88)
    print("VLM 精确统计（从原始 per-seed 重算，未取整）")
    print("=" * 88)
    res = {}
    for arm in ("text_only", "vision_only", "both"):
        rs = rows.get(arm, [])
        if not rs:
            print(f"  {arm}: 无数据")
            continue
        rels = [r["rel"] for r in rs]
        cgs = [r["cg_span"] for r in rs if r["cg_span"] is not None]
        n = len(rels)
        mean, sd = st.mean(rels), st.stdev(rels) if n > 1 else None
        lo, hi = min(rels), max(rels)
        res[arm] = {
            "n": n, "mean": mean, "sd": sd, "min": lo, "max": hi,
            "cg_mean": st.mean(cgs) if cgs else None,
            "cg_sd": st.stdev(cgs) if len(cgs) > 1 else None,
            "seeds": sorted(r["seed"] for r in rs),
            "per_seed": {str(r["seed"]): round(r["rel"], 4) for r in rs},
        }
        print(f"\n  {arm}  (n={n}, seeds {sorted(r['seed'] for r in rs)})")
        print(f"    DG* 相对变化  mean = {mean:.6f}  → 论文 **{round_half_up(mean):.1f}**")
        print(f"                  sd   = {sd:.6f}  → 论文 **{round_half_up(sd):.1f}**"
              f"   （注意 Python round() 会给 {round(sd,1):.1f}，银行家舍入）")
        print(f"                  范围 = {lo:.6f} – {hi:.6f}  → 论文 "
              f"**{round_half_up(lo)}–{round_half_up(hi)}**")
        print(f"    CG 跨度       mean = {st.mean(cgs):.6f} ± {st.stdev(cgs):.6f}"
              f"  → 论文 {round(st.mean(cgs),3)} ± {round(st.stdev(cgs),3)}")
        print(f"    逐 seed: {[round(x,2) for x in sorted(rels)]}")

    print()
    print("=" * 88)
    print("论文当前写法 vs 应为")
    print("=" * 88)
    paper = {"text_only": (66.5, 8.3, 47.8, 78.8),
             "vision_only": (18.0, 8.8, 8.5, 35.7),
             "both": (87.9, 5.3, 73.1, 95.1)}
    for arm, (pm, ps, plo, phi) in paper.items():
        r = res.get(arm)
        if not r:
            continue
        want = (round_half_up(r["mean"]), round_half_up(r["sd"]),
                round_half_up(r["min"]), round_half_up(r["max"]))
        ok = (pm, ps, plo, phi) == want
        print(f"  {'✅' if ok else '🔴'} {arm:<12} 论文 {pm}±{ps} [{plo},{phi}]"
              f" ｜ 应为 {want[0]}±{want[1]} [{want[2]},{want[3]}]")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(res, ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
