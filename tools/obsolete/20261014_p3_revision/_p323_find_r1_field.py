# -*- coding: utf-8 -*-
r"""查 `results.json` 里是否还有**另一个** R@1 字段能对上论文（2026-10-12）。

论文表：OpenCLIP text_only **0.643**、both 0.680、vision_only 0.672；
CLIP B/32 r4 text_only 0.621、both 0.679；CLIP B/16 r4 text_only 0.651。
归档 `final_task_metrics.R@1` 的 5-seed 均值分别是
0.6366 / 0.6818 / 0.6698 / 0.6222 / 0.6796 / 0.6502。

**要么论文用了另一个字段，要么用了另一个统计量。**

    python tools\_p323_find_r1_field.py
"""
from __future__ import annotations

import glob
import io
import json
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

TARGETS = {
    ("strict_freeze_oclip/r4", "text_only"): 0.643,
    ("strict_freeze_oclip/r4", "both"): 0.680,
    ("strict_freeze_oclip/r4", "vision_only"): 0.672,
    ("strict_freeze_b32_r4", "text_only"): 0.621,
    ("strict_freeze_b32_r4", "both"): 0.679,
    ("strict_freeze_b16/r4", "text_only"): 0.651,
}


def walk(o, path=""):
    """产出所有 (字段路径, 数值)。"""
    if isinstance(o, dict):
        for k, v in o.items():
            yield from walk(v, f"{path}.{k}" if path else k)
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from walk(v, f"{path}[{i}]")
    elif isinstance(o, (int, float)):
        yield path, float(o)


def main() -> int:
    # 先看单文件里有哪些含 R 或 recall 的数值字段
    sample = REPO / "outputs" / "strict_freeze_oclip" / "r4" / "text_only" / "seed42" / "results.json"
    if sample.exists():
        d = json.loads(io.open(sample, encoding="utf-8", errors="replace").read())
        print("=" * 100)
        print("① 样本 run 里所有含 R/recall/task 的数值字段")
        print("=" * 100)
        for p, v in walk(d):
            if any(t in p.lower() for t in ("r@", "recall", "r1", "r5", "r10", "task")):
                print(f"  {p:<52} {v}")

    print()
    print("=" * 100)
    print("② 每个字段的 5-seed 均值，看哪个能命中论文")
    print("=" * 100)
    for (key, arm), tgt in TARGETS.items():
        files = sorted(glob.glob(str(REPO / "outputs" / key / arm / "seed*" / "results.json")))
        if not files:
            print(f"  ⚠️  {key}/{arm}: 无文件")
            continue
        vals = defaultdict(list)
        for f in files:
            d = json.loads(io.open(f, encoding="utf-8", errors="replace").read())
            for p, v in walk(d):
                if any(t in p.lower() for t in ("r@", "recall", "r1", "r5", "r10")):
                    vals[p].append(v)
        print(f"\n  {key}/{arm}  论文 {tgt}  （n={len(files)}）")
        for p in sorted(vals):
            vs = vals[p]
            if len(vs) != len(files):
                continue
            m = sum(vs) / len(vs)
            hit = "🎯" if abs(m - tgt) < 5e-4 else ("≈" if abs(m - tgt) < 5e-3 else " ")
            print(f"     {hit} {p:<46} 均值={m:.6f} 差={m-tgt:+.6f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
