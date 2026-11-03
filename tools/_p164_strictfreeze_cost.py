# -*- coding: utf-8 -*-
r"""精确清点"论文在用"的严格冻结组 + 成本估算（2026-10-10）。

    python tools\_p164_strictfreeze_cost.py
"""
from __future__ import annotations

import glob
import io
import json
import re
import statistics as st
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def main() -> int:
    # 找出所有严格冻结 run（含多级目录）
    pats = ["outputs/strict_freeze_b32_r4", "outputs/strict_freeze_b32_r8",
            "outputs/strict_freeze_b16*", "outputs/strict_freeze_oclip*"]
    rows = []
    for p in pats:
        for f in glob.glob(str(REPO / p / "**" / "results.json"), recursive=True):
            d = json.loads(io.open(f, encoding="utf-8", errors="replace").read())
            rel = str(Path(f).relative_to(REPO))
            parts = Path(f).parts
            seed = next((x for x in parts if x.startswith("seed")), "?")
            arm = next((x for x in parts if x in ("text_only", "both", "vision_only")), "?")
            rank = next((x for x in parts if re.fullmatch(r"r\d+", x)), "?")
            rows.append({"rel": rel, "group": str(Path(rel).parent.parent.parent),
                         "arm": arm, "seed": seed, "rank": rank,
                         "elapsed": d.get("elapsed_sec"),
                         "dcg": (d.get("final_gap", {}).get("centroid_gap", 0)
                                 - d.get("initial_gap", {}).get("centroid_gap", 0))})

    print("=" * 82)
    print("严格冻结 run 清点（含多级目录）")
    print("=" * 82)
    by = defaultdict(list)
    for r in rows:
        by[(r["group"], r["arm"])].append(r)
    for k in sorted(by):
        seeds = sorted(x["seed"] for x in by[k])
        el = [x["elapsed"] for x in by[k] if x["elapsed"]]
        avg = f"{st.mean(el):.0f}s/run" if el else "?"
        dcg = [x["dcg"] for x in by[k]]
        print(f"  {k[0]:<44} {k[1]:<12} {len(seeds)} seed  {avg:<12} "
              f"ΔCG={st.mean(dcg):+.4f}")

    print()
    print("=" * 82)
    print("提升到 5 seed 的成本")
    print("=" * 82)
    total = 0.0
    for k in sorted(by):
        n = len(by[k])
        if n >= 5:
            continue
        el = [x["elapsed"] for x in by[k] if x["elapsed"]]
        if not el:
            continue
        avg = st.mean(el)
        need = 5 - n
        total += need * avg
        print(f"  {k[0]:<44} {k[1]:<12} {n}→5 seed  = {need} run × {avg:.0f}s "
              f"= {need * avg / 60:.0f} min")
    print(f"\n  **合计约 {total / 3600:.1f} 小时**（严格冻结部分）")

    print()
    print("=" * 82)
    print("注：旧协议组（`outputs/coco/coco_*`、`coco_full_ft`）与 adapter / β pilot 未计入")
    print("=" * 82)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
