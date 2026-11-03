# -*- coding: utf-8 -*-
r"""核查 `tab:position_strict` 的 R@1 列为何 5/12 格复现不出（2026-10-12）。

## 触发

task-8 成员报：ΔCG 列 12/12 与表一致，但 **R@1 列 5/12 不一致**
（最大差 OpenCLIP r4 text_only：重算 0.6366 vs 发表 0.643，差 −0.0064）。
且这些 run **全部 batch=128 / 10 epoch**（已排除 batch 混用）。

## 要回答的三个问题

1. 论文发表值是**单个 seed** 还是**多个 seed 的均值**？
2. 每条 run 的 `final_task_metrics.R@1` 到底是多少，seed 有哪些？
3. 差异是否可用"论文用了另一组 seed"或"评测集 500 vs 1000 对"解释？

## 方法

直接读归档里每个 run 的 `results.json`，取 `final_task_metrics.R@1` 与 `seed`，
**按臂分组列出全部原值**，再与论文表逐格对照。

    python tools\_p311_audit_strict_r1.py [--apply]
"""
from __future__ import annotations

import argparse
import glob
import io
import json
import os
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "strict_r1_audit.json"

# 论文 tab:position_strict 的发表值（ΔCG, R@1）
PUBLISHED = {
    ("CLIP_B32_r8", "text_only"): (None, 0.627),
    ("CLIP_B32_r8", "both"): (None, None),
    ("CLIP_B32_r4", "text_only"): (None, 0.621),
    ("CLIP_B32_r4", "both"): (None, 0.679),
    ("CLIP_B16_r4", "text_only"): (None, 0.651),
    ("CLIP_B16_r4", "both"): (None, None),
    ("OpenCLIP_r4", "text_only"): (None, 0.643),
    ("OpenCLIP_r4", "both"): (None, 0.680),
    ("OpenCLIP_r4", "vision_only"): (None, 0.672),
}


def get(d, *path, default=None):
    cur = d
    for p in path:
        if isinstance(cur, dict) and p in cur:
            cur = cur[p]
        else:
            return default
    return cur


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    print("=" * 100)
    print("① 收集所有 strict-freeze 相关 run 的 (exp, seed, R@1, batch)")
    print("=" * 100)
    rows = []
    pats = ["outputs/strict_freeze/**/results.json",
            "outputs/**/strict*/**/results.json",
            "outputs/siglip_strict/**/results.json"]
    seen = set()
    for pat in pats:
        for f in glob.glob(str(REPO / pat), recursive=True):
            if f in seen:
                continue
            seen.add(f)
            try:
                d = json.loads(io.open(f, encoding="utf-8", errors="replace").read())
            except Exception:
                continue
            exp = d.get("experiment", "?")
            r1 = get(d, "final_task_metrics", "R@1")
            if r1 is None:
                r1 = d.get("R1") or d.get("r1")
            rows.append({
                "file": str(Path(f).relative_to(REPO)),
                "experiment": exp,
                "seed": d.get("seed"),
                "R@1": r1,
                "batch": d.get("batch_size"),
                "max_samples": d.get("max_samples"),
                "n_trainable": d.get("n_trainable_params"),
                "dCG": (get(d, "final_gap", "centroid_gap") or 0)
                       - (get(d, "initial_gap", "centroid_gap") or 0)
                if get(d, "final_gap", "centroid_gap") is not None else None,
            })

    print(f"  找到 {len(rows)} 个 run")
    from collections import defaultdict
    by = defaultdict(list)
    for r in rows:
        by[r["experiment"]].append(r)
    for exp in sorted(by):
        rs = by[exp]
        seeds = sorted(str(x["seed"]) for x in rs)
        r1s = [x["R@1"] for x in rs if x["R@1"] is not None]
        batches = sorted({x["batch"] for x in rs})
        mean = sum(r1s) / len(r1s) if r1s else None
        print(f"  {exp:<34} n={len(rs):<3} seeds={','.join(seeds)[:22]:<24} "
              f"batch={batches} R@1均值={mean if mean is None else round(mean,4)}")

    print()
    print("=" * 100)
    print("② 与论文发表值对照（只列两者都有的）")
    print("=" * 100)
    print(f"  {'臂':<28} {'归档 n':<7} {'归档均值':<10} {'发表值':<8} {'差':<10} 判定")
    drift = []
    for (key, arm), (_, pub) in PUBLISHED.items():
        if pub is None:
            continue
        cands = [r for r in rows if r["R@1"] is not None
                 and re.search(key.split("_")[-1], r["experiment"], re.I)
                 and re.search(r"text|both|vision", r["experiment"], re.I)
                 and arm.replace("_", "") in r["experiment"].replace("_", "").lower()]
        if not cands:
            continue
        vals = [r["R@1"] for r in cands]
        m = sum(vals) / len(vals)
        d = m - pub
        ok = abs(d) < 5e-4
        print(f"  {key+'/'+arm:<28} {len(cands):<7} {m:<10.4f} {pub:<8.3f} {d:<+10.4f} "
              f"{'✅' if ok else '⚠️ '}")
        if not ok:
            drift.append({"cell": f"{key}/{arm}", "archive_mean": round(m, 6),
                          "published": pub, "diff": round(d, 6),
                          "n": len(cands),
                          "values": [round(v, 6) for v in vals],
                          "files": [c["file"] for c in cands]})

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(
            {"rows": rows, "drift": drift, "published": {str(k): v for k, v in PUBLISHED.items()}},
            ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
