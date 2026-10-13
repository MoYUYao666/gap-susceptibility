# -*- coding: utf-8 -*-
r"""逐 (组, 臂, seed) 列出 batch_size，找出批次不一致的确切范围（2026-10-10 晚）。

## 为什么

`tools/_p166` 发现：`strict_freeze_b16/r4` 与 `strict_freeze_oclip/r4` 的
**同一臂内混了 batch 64 与 128**；且 `coco_sweep`（128）与 `coco_sweep_text_only`（64）**跨臂不一致**。

**若批次与臂/seed 相关，则臂间比较被混淆。**

    python tools\_p167_batch_per_run.py [--apply]
"""
from __future__ import annotations

import argparse
import glob
import io
import json
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "batch_audit.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    targets = ["outputs/strict_freeze_b32_r4", "outputs/strict_freeze_b16/r4",
               "outputs/strict_freeze_oclip/r4", "outputs/coco_sweep_text_only",
               "outputs/coco_sweep"]
    table = defaultdict(dict)      # (组, 臂) -> {(rank, seed): batch}
    for t in targets:
        for f in glob.glob(str(REPO / t / "**" / "results.json"), recursive=True):
            d = json.loads(io.open(f, encoding="utf-8", errors="replace").read())
            p = Path(f).parts
            arm = next((x for x in p if x in ("text_only", "both", "vision_only")), "?")
            seed = next((x for x in p if x.startswith("seed")), "?")
            rank = t.split("/")[-1] if "r4" not in t else "r4"
            table[(t, arm)][(rank, seed)] = d.get("batch_size")

    print("=" * 84)
    print("逐 (组, 臂, rank, seed) 的 batch_size")
    print("=" * 84)
    problems = []
    for (grp, arm) in sorted(table):
        items = sorted(table[(grp, arm)].items())
        batches = sorted({v for _, v in items})
        flag = "🔴" if len(batches) > 1 else "✅"
        print(f"\n{flag} {grp} ／ {arm}   批次={batches}")
        for (rank, seed), b in items:
            print(f"      {rank:<5} {seed:<9} batch={b}")
        if len(batches) > 1:
            problems.append((grp, arm, batches))

    print()
    print("=" * 84)
    print(f"不一致的 (组, 臂)：{len(problems)} 个")
    print("=" * 84)
    for grp, arm, bs in problems:
        print(f"  🔴 {grp} ／ {arm} 混用 {bs}")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(
            {"table": {f"{k[0]}|{k[1]}": {f"{a2}|{b2}": v for (a2, b2), v in val.items()}
                       for k, val in table.items()},
             "inconsistent": [{"group": g, "arm": ar, "batches": bs}
                              for g, ar, bs in problems]},
            ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
