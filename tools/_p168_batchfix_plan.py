# -*- coding: utf-8 -*-
r"""算出"统一到 batch 128"要重跑哪些 run + 提升到 5 seed 的计划（2026-10-10 晚）。

## 规则

1. **所有 batch != 128 的 run → 重跑（用 128）**
2. 之后**每组补到 5 seed**（seed 789 / 1011）
3. **VLM 不受影响**（它一直是 batch 2，脚本内一致）

## 已完成 9-seed 之外的组

| 组 | 现 seed | 批次 | 需重跑 | 需补 seed |
|---|---|---|---|---|
| `strict_freeze_b32_r4` | 3 | 全 128 ✅ | 0 | 6 |
| `strict_freeze_oclip/r4` | 3 | 42=128, 123/456=64 | **6** | 6 |
| `strict_freeze_b16/r4` | 3 | both/vision 的 456=64 | **2** | 6 |
| `coco_sweep_text_only` | r2/r8/r32/r64 各 3 | 全 64 | **12** | 0（重跑即 3 seed，再补 2 → +8） |
| `coco_sweep`（both） | 各 3 | 全 128 ✅ | 0 | 0 |

    python tools\_p168_batchfix_plan.py [--apply]
"""
from __future__ import annotations

import argparse
import glob
import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "batchfix_plan.json"
TARGET_BATCH = 128


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    groups = ["outputs/strict_freeze_b32_r4", "outputs/strict_freeze_oclip/r4",
              "outputs/strict_freeze_b16/r4", "outputs/coco_sweep_text_only",
              "outputs/coco_sweep"]
    rerun, ok = [], []
    for g in groups:
        for f in sorted(glob.glob(str(REPO / g / "**" / "results.json"), recursive=True)):
            d = json.loads(io.open(f, encoding="utf-8", errors="replace").read())
            p = Path(f).parts
            arm = next((x for x in p if x in ("text_only", "both", "vision_only")), "?")
            seed = next((x for x in p if x.startswith("seed")), "?")
            rank = next((x for x in p if x and x[0] == "r" and x[1:].isdigit()), "r4")
            rec = {"group": g, "arm": arm, "seed": seed, "rank": rank,
                   "batch": d.get("batch_size"), "file": str(Path(f).relative_to(REPO))}
            (rerun if d.get("batch_size") != TARGET_BATCH else ok).append(rec)

    print("=" * 80)
    print(f"目标批次 {TARGET_BATCH}")
    print("=" * 80)
    print(f"\n✅ 已是 {TARGET_BATCH}：{len(ok)} run")
    from collections import Counter
    for k, v in sorted(Counter(f"{r['group']}|{r['arm']}" for r in ok).items()):
        print(f"   {k:<50} {v}")
    print(f"\n🔴 需重跑（batch != {TARGET_BATCH}）：{len(rerun)} run")
    for k, v in sorted(Counter(f"{r['group']}|{r['arm']}|{r['rank']}"
                               for r in rerun).items()):
        print(f"   {k:<56} {v}")
    print("\n   明细：")
    for r in sorted(rerun, key=lambda x: (x["group"], x["arm"], x["rank"], x["seed"])):
        print(f"     {r['group']:<34} {r['arm']:<12} {r['rank']:<5} {r['seed']:<9} "
              f"batch={r['batch']}")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(
            {"target_batch": TARGET_BATCH, "needs_rerun": rerun, "already_ok": ok,
             "n_rerun": len(rerun), "n_ok": len(ok)},
            ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
