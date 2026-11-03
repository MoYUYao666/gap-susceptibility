# -*- coding: utf-8 -*-
r"""核论文主表的"有效 n"（2026-10-13）。

## 已确认

**task-9**：`delta_E_per_sample` 的 **32 个值逐位相同**，`delta_E_per_sample_sd = 0.0`
（同图 `blank_img` + 同提示 `"Describe this image."`）⇒ **有效 n = seed 数 = 3** ✅ 成员披露正确

## 待核

论文 Table 1 用的 `run_training.py`：`eval_data = processed[:4]`，**4 个样本的 instruction 不同**
（Alpaca 前 4 条），图**同为 `blank_img`（336×336 全零）**。
⇒ 逐样本 E **是否**有差异？即论文的"n"到底是多少？

    python tools\_p44c_verify_paper_effective_n.py [--apply]
"""
from __future__ import annotations

import argparse
import glob
import io
import json
import os
import statistics
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "p3_paper_effective_n.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    rep = {}

    print("=" * 100)
    print("① 归档里是否有逐样本 E（论文侧）")
    print("=" * 100)
    found = []
    for f in glob.glob(str(REPO / "paper3/scripts/outputs/experiments/*.json")):
        try:
            d = json.loads(io.open(f, encoding="utf-8", errors="replace").read())
        except Exception:
            continue
        s = json.dumps(d, ensure_ascii=False)
        if "per_sample" in s or "_ps" in s:
            found.append(os.path.basename(f))
    print(f"  含 per_sample 的归档：{len(found)} 个")
    for x in found[:10]:
        print(f"     {x}")
    rep["archives_with_per_sample"] = found

    print()
    print("=" * 100)
    print("② E2_results.json 的 n 口径")
    print("=" * 100)
    p = REPO / "paper3/scripts/outputs/experiments/E2_results.json"
    if p.exists():
        d = json.loads(io.open(p, encoding="utf-8", errors="replace").read())
        for key in ("E2", "extra", "sweep"):
            v = d.get(key) or []
            if v:
                print(f"  {key}: {len(v)} run ｜ 首项键 {sorted(v[0].keys())}")
        rep["E2_counts"] = {k: len(d.get(k) or []) for k in ("E2", "extra", "sweep")}

    print()
    print("=" * 100)
    print("③ 决定性判据：同一 rank 下不同 seed 的 ΔE 是否远大于 0？")
    print("=" * 100)
    from collections import defaultdict
    if p.exists():
        d = json.loads(io.open(p, encoding="utf-8", errors="replace").read())
        g = defaultdict(list)
        for key in ("E2", "extra", "sweep"):
            for r in (d.get(key) or []):
                E = r.get("E") or []
                if len(E) >= 2 and isinstance(E[0], (int, float)) and isinstance(E[-1], (int, float)):
                    g[r.get("rank")].append(E[-1] - E[0])
        print(f"  {'rank':<6} {'n seed':<8} 均值       sd(跨 seed)")
        for rk in sorted(g, key=lambda x: (x is None, x)):
            v = g[rk]
            if len(v) < 2:
                print(f"  {str(rk):<6} {len(v):<8} {v[0] if v else float('nan'):+10.2f}   —")
                continue
            print(f"  {str(rk):<6} {len(v):<8} {statistics.mean(v):+10.2f}   {statistics.stdev(v):8.2f}")
        # 逐 seed 的 E0 是否一致
        e0s = [ (r.get("E") or [None])[0] for key in ("E2","extra","sweep") for r in (d.get(key) or []) ]
        e0s = [x for x in e0s if isinstance(x, (int, float))]
        print(f"\n  E(0) 取值集合（全部 run）：{sorted(set(round(x,1) for x in e0s))}")
        print(f"  ⇒ E(0) 若只有少数取值，说明**同一环境块内**逐 run 的起点相同；")
        print(f"    **但 sd(跨 seed) 不为 0** ⇒ 论文报的 sd 是**跨 seed/run** 的，不是跨样本的")
        rep["e0_values"] = sorted(set(round(x, 1) for x in e0s))

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(rep, ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
