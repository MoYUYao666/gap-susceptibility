# -*- coding: utf-8 -*-
r"""COCO `text_only` 补齐后的分析（2026-10-10）。

## 背景

论文说"**最优位置随数据集翻转**：Flickr30k = `text_only`，COCO = `both`"。
但补跑前 COCO 的 `text_only` 只有 r1/r4/r16 和一个 r2，**r8/r32/r64 完全缺失** →
该结论在 COCO 上**只有 `both` 一侧的数据**。

**本脚本**：把新旧两批的 COCO 结果合起来，算出每臂每秩的 ΔCG，判"翻转"是否成立。

    python tools\_p140_coco_analysis.py [--apply]
"""
from __future__ import annotations

import argparse
import glob
import io
import json
import statistics as st
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "coco_textonly_verdict.json"


def load(pattern: str):
    rows = []
    for f in sorted(glob.glob(str(REPO / pattern), recursive=True)):
        p = Path(f)
        d = json.loads(io.open(f, encoding="utf-8").read())
        # 从路径解析：.../<rank>/<arm>/seed<N>/results.json
        parts = p.parts
        seed = next((x for x in parts if x.startswith("seed")), "?")
        arm = parts[-3] if parts[-2].startswith("seed") else parts[-2]
        rank = parts[-4] if parts[-3] in ("text_only", "both", "vision_only") else parts[-3]
        dcg = None
        for key in ("final_gap", "initial_gap"):
            pass
        fg = d.get("final_gap") or {}
        ig = d.get("initial_gap") or {}
        if "centroid_gap" in fg and "centroid_gap" in ig:
            dcg = fg["centroid_gap"] - ig["centroid_gap"]
        rows.append({"file": str(p.relative_to(REPO)), "rank": rank, "arm": arm,
                     "seed": seed, "dcg": dcg,
                     "r1": (d.get("final_retrieval") or {}).get("r1"),
                     "n_trainable": d.get("n_trainable_params")})
    return rows


def agg(rows, tag):
    print(f"\n=== {tag}（{len(rows)} run）===")
    by = {}
    for r in rows:
        by.setdefault((r["rank"], r["arm"]), []).append(r)
    for (rank, arm) in sorted(by, key=lambda k: (int(k[0].lstrip("r")), k[1])):
        xs = [x["dcg"] for x in by[(rank, arm)] if x["dcg"] is not None]
        if not xs:
            continue
        m = st.mean(xs)
        sd = st.stdev(xs) if len(xs) > 1 else float("nan")
        print(f"  {rank:<5} {arm:<12} n={len(xs)}  ΔCG = {m:+.4f}"
              + (f" ± {sd:.4f}" if len(xs) > 1 else "  (单 seed)"))
    return by


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    new = load("outputs/coco_sweep_text_only/**/results.json")
    old = load("outputs/coco_sweep/**/results.json")
    print(f"=== 新跑（text_only）{len(new)} 个 ｜ 旧 sweep {len(old)} 个 ===")

    by_new = agg(new, "新跑：COCO text_only")
    by_old = agg(old, "旧 sweep：COCO（both 为主）")

    # 合并同 (rank, arm)
    print("\n=== 合并后：每秩每臂的 ΔCG ===")
    merged = {}
    for r in new + old:
        merged.setdefault((r["rank"], r["arm"]), []).append(r)
    verdict = {}
    for rank in sorted({k[0] for k in merged}, key=lambda x: int(x.lstrip("r"))):
        row = {}
        for arm in ("text_only", "both", "vision_only"):
            xs = [x["dcg"] for x in merged.get((rank, arm), []) if x["dcg"] is not None]
            if xs:
                row[arm] = {"n": len(xs), "mean": round(st.mean(xs), 5),
                            "sd": round(st.stdev(xs), 5) if len(xs) > 1 else None}
        if not row:
            continue
        verdict[rank] = row
        parts = []
        for arm, v in row.items():
            parts.append(f"{arm}={v['mean']:+.4f}(n={v['n']})")
        # 谁最保护（ΔCG 越小越保护）
        best = min(row, key=lambda k: row[k]["mean"])
        print(f"  {rank:<5} " + " ｜ ".join(parts) + f"   → 最保护: **{best}**")

    print("\n=== 论文主张：'Flickr30k = text_only｜COCO = both' ===")
    coco_best = {}
    for rank, row in verdict.items():
        if len(row) >= 2:
            coco_best[rank] = min(row, key=lambda k: row[k]["mean"])
    from collections import Counter
    c = Counter(coco_best.values())
    print(f"  COCO 上各秩的'最保护臂'分布: {dict(c)}")
    print(f"  秩数（有两臂以上的）: {len(coco_best)}")
    if c.get("both", 0) > c.get("text_only", 0):
        print("  → ✅ **COCO 上 both 更常最保护**（支持'翻转'）")
    elif c.get("text_only", 0) > c.get("both", 0):
        print("  → 🔴 **COCO 上 text_only 更常最保护**（**与论文主张相反**）")
    else:
        print("  → ⚠️ 两者持平或无两臂数据")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(
            {"by_rank": verdict, "coco_best_per_rank": coco_best,
             "counts": dict(c), "n_new": len(new), "n_old": len(old)},
            ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
