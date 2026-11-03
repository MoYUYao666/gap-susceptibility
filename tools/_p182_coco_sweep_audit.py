# -*- coding: utf-8 -*-
r"""核 `outputs/coco_sweep`（both 与旧 text_only）的批次与 seed 数（2026-10-11）。

## 为什么要核

论文的"数据集翻转"表里，COCO 侧用 `coco_sweep`（`both` 对照）。
若那里的 `text_only`/`both` **批次不一致**或 **seed 数不足**，对照就不成立。

    python tools\_p182_coco_sweep_audit.py [--apply]
"""
from __future__ import annotations

import argparse
import glob
import io
import json
import re
import statistics as st
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "coco_sweep_audit.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    table = defaultdict(dict)
    for f in sorted(glob.glob(str(REPO / "outputs" / "coco_sweep" / "**"
                                   / "results.json"), recursive=True)):
        if ".bak" in f:
            continue
        d = json.loads(io.open(f, encoding="utf-8", errors="replace").read())
        p = Path(f).parts
        rank = next((x for x in p if re.fullmatch(r"r\d+", x)), "?")
        arm = next((x for x in p if x in ("text_only", "both", "vision_only")), "?")
        seed = next((x for x in p if x.startswith("seed")), "?")
        fg = (d.get("final_gap") or {}).get("centroid_gap")
        ig = (d.get("initial_gap") or {}).get("centroid_gap")
        table[(rank, arm)][seed] = {
            "dcg": (fg - ig) if (fg is not None and ig is not None) else None,
            "batch": d.get("batch_size"), "elapsed": d.get("elapsed_sec"),
        }

    print("=" * 88)
    print("outputs/coco_sweep ｜ 逐 (rank, 臂)：seed 数 / 批次 / ΔCG")
    print("=" * 88)
    issues = []
    for (rank, arm) in sorted(table, key=lambda k: (int(k[0][1:]), k[1])):
        e = table[(rank, arm)]
        batches = sorted({v["batch"] for v in e.values()})
        vals = [v["dcg"] for v in e.values() if v["dcg"] is not None]
        n = len(vals)
        m = st.mean(vals) if vals else None
        sd = st.stdev(vals) if n > 1 else None
        flag = "✅" if batches == [128] else "🔴"
        print(f"  {flag} {rank:<5} {arm:<12} n={n} batch={batches}  "
              f"ΔCG={m:+.4f}" + (f" ± {sd:.4f}" if sd else "") if m is not None
              else f"  {flag} {rank:<5} {arm:<12} n={n} batch={batches}  无 ΔCG")
        if batches != [128]:
            issues.append(f"{rank}/{arm} 批次 {batches}")

    print()
    print("=" * 88)
    print(f"问题：{len(issues)}")
    for x in issues:
        print(f"  🔴 {x}")

    # 与论文对照所需的两臂
    print()
    print("=" * 88)
    print("论文『数据集翻转』所需：COCO 同秩 text_only vs both")
    print("=" * 88)
    for rank in ("r2", "r4", "r8", "r16", "r32", "r64"):
        to = table.get((rank, "text_only"), {})
        bo = table.get((rank, "both"), {})
        tvals = [v["dcg"] for v in to.values() if v["dcg"] is not None]
        bvals = [v["dcg"] for v in bo.values() if v["dcg"] is not None]
        ts = (f"{st.mean(tvals):+.4f}(n={len(tvals)})" if tvals else "缺")
        bs = (f"{st.mean(bvals):+.4f}(n={len(bvals)})" if bvals else "缺")
        print(f"  {rank:<5} text_only={ts:<22} both={bs:<22}")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(
            {f"{k[0]}|{k[1]}": {s: v for s, v in val.items()}
             for k, val in table.items()},
            ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
