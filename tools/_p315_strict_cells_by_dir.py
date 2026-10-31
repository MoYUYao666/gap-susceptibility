# -*- coding: utf-8 -*-
r"""定位 `tab:position_strict` 12 格的真实归档出处（按目录分组）（2026-10-12）。

## 结论方向

`experiment` 字段**不足以唯一标识配置**（`strict_both` 混了 7 种参数量）。
**必须按目录分组**才能对上论文的单 backbone 值。

    python tools\_p315_strict_cells_by_dir.py [--apply]
"""
from __future__ import annotations

import argparse
import glob
import io
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "strict_cells_by_dir.json"

# 论文发表值（来自 tab:position_strict 的 R@1 行）—— 用于逐格比对
PUBLISHED_R1 = {
    ("CLIP_B32", "r8", "text_only"): 0.627,
    ("CLIP_B32", "r4", "text_only"): 0.621,
    ("CLIP_B32", "r4", "both"): 0.679,
    ("CLIP_B16", "r4", "text_only"): 0.651,
    ("CLIP_B16", "r4", "both"): 0.679,
    ("OpenCLIP", "r4", "text_only"): 0.643,
    ("OpenCLIP", "r4", "both"): 0.680,
    ("OpenCLIP", "r4", "vision_only"): 0.672,
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    bydir = defaultdict(list)
    for f in glob.glob(str(REPO / "outputs" / "**" / "results.json"), recursive=True):
        try:
            d = json.loads(io.open(f, encoding="utf-8", errors="replace").read())
        except Exception:
            continue
        exp = str(d.get("experiment", "?"))
        if not exp.startswith("strict"):
            continue
        rel = str(Path(f).relative_to(REPO))
        parent = "/".join(rel.split("/")[:-1])
        fin = (d.get("final_gap") or {}).get("centroid_gap")
        ini = (d.get("initial_gap") or {}).get("centroid_gap")
        bydir[parent].append({
            "experiment": exp,
            "n_train": d.get("n_trainable_params"),
            "seed": d.get("seed"),
            "R@1": (d.get("final_task_metrics") or {}).get("R@1"),
            "dCG": (fin - ini) if (fin is not None and ini is not None) else None,
            "file": rel,
        })

    print("=" * 108)
    print("① 按目录分组的 strict run")
    print("=" * 108)
    for parent in sorted(bydir):
        rs = bydir[parent]
        r1 = [x["R@1"] for x in rs if x["R@1"] is not None]
        dcg = [x["dCG"] for x in rs if x["dCG"] is not None]
        exps = sorted({x["experiment"] for x in rs})
        nts = sorted({str(x["n_train"]) for x in rs})
        print(f"  {parent}")
        print(f"     exp={exps}  n={len(rs)}  n_train={nts}")
        print(f"     R@1={[round(v,4) for v in r1]} → 均值 "
              f"{(sum(r1)/len(r1) if r1 else float('nan')):.4f}")
        if dcg:
            print(f"     ΔCG 均值 = {sum(dcg)/len(dcg):+.4f}")

    print()
    print("=" * 108)
    print("② 把这些目录的均值与论文发表值对表")
    print("=" * 108)
    # 建立 目录 -> (R1均值, ΔCG均值) 的表，然后人工映射
    table = {}
    for parent, rs in bydir.items():
        r1 = [x["R@1"] for x in rs if x["R@1"] is not None]
        dcg = [x["dCG"] for x in rs if x["dCG"] is not None]
        if r1:
            table[parent] = {
                "R1_mean": sum(r1) / len(r1),
                "dCG_mean": (sum(dcg) / len(dcg)) if dcg else None,
                "n": len(r1),
            }
    matched = 0
    report = []
    for (model, rank, arm), pub in PUBLISHED_R1.items():
        # 找 R@1 均值最接近的目录
        best = min(table.items(), key=lambda kv: abs(kv[1]["R1_mean"] - pub))
        diff = best[1]["R1_mean"] - pub
        ok = abs(diff) < 5e-4
        matched += 1 if ok else 0
        print(f"  {model:<10} {rank:<4} {arm:<12} 发表 {pub:.3f} ｜ "
              f"最接近目录 {best[0][:52]:<54} 均值 {best[1]['R1_mean']:.4f} "
              f"差 {diff:+.4f} {'✅' if ok else '⚠️ '}")
        report.append({"cell": f"{model}/{rank}/{arm}", "published": pub,
                       "best_dir": best[0], "dir_mean": round(best[1]["R1_mean"], 6),
                       "diff": round(diff, 6), "match": ok})
    print(f"\n  → {matched}/{len(PUBLISHED_R1)} 格能在**目录级**复现")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(
            {"by_dir": {k: v for k, v in bydir.items()}, "match_report": report},
            ensure_ascii=False, indent=1))
        print(f"  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
