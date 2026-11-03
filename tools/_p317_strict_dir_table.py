# -*- coding: utf-8 -*-
r"""精确对表：`tab:position_strict` 每格 ↔ 归档顶层目录（2026-10-12）。

顶层目录（已由 `outputs/` 列表确认）：
`strict_freeze`、`strict_freeze_b16`、`strict_freeze_b32_r4`、`strict_freeze_bioclip`、
`strict_freeze_oclip`、`strict_freeze_openclip`、`strict_freeze_openclip_rank`、
`strict_freeze_rank`

    python tools\_p317_strict_dir_table.py [--apply]
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
OUT = REPO / "outputs" / "analysis" / "strict_dir_table.json"

# 论文发表值（R@1）
PUBLISHED = {
    "CLIP_B32_r8_text_only": 0.627,
    "CLIP_B32_r4_text_only": 0.621,
    "CLIP_B32_r4_both": 0.679,
    "CLIP_B16_r4_text_only": 0.651,
    "CLIP_B16_r4_both": 0.679,
    "OpenCLIP_r4_text_only": 0.643,
    "OpenCLIP_r4_both": 0.680,
    "OpenCLIP_r4_vision_only": 0.672,
}


def arm_of(path: str) -> str:
    for a in ("text_only", "vision_only", "both"):
        if f"/{a}/" in path or path.endswith(f"/{a}"):
            return a
    return "?"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    # 目录 -> 臂 -> [run]
    cells = defaultdict(lambda: defaultdict(list))
    for f in glob.glob(str(REPO / "outputs" / "strict_freeze*" / "**" / "results.json"),
                       recursive=True):
        try:
            d = json.loads(io.open(f, encoding="utf-8", errors="replace").read())
        except Exception:
            continue
        rel = Path(f).relative_to(REPO)
        top = rel.parts[1]
        arm = arm_of("/" + "/".join(rel.parts))
        if arm == "?":
            continue
        fin = (d.get("final_gap") or {}).get("centroid_gap")
        ini = (d.get("initial_gap") or {}).get("centroid_gap")
        cells[top][arm].append({
            "seed": d.get("seed"),
            "R@1": (d.get("final_task_metrics") or {}).get("R@1"),
            "dCG": (fin - ini) if (fin is not None and ini is not None) else None,
            "n_train": d.get("n_trainable_params"),
            "dir": "/".join(rel.parts[:-1]),
        })

    print("=" * 104)
    print("① 每个顶层目录 × 臂 的 5-seed 均值")
    print("=" * 104)
    table = {}
    for top in sorted(cells):
        print(f"\n{top}")
        table[top] = {}
        for arm in ("text_only", "both", "vision_only"):
            rs = cells[top].get(arm, [])
            if not rs:
                continue
            r1 = [x["R@1"] for x in rs if x["R@1"] is not None]
            dcg = [x["dCG"] for x in rs if x["dCG"] is not None]
            if not r1:
                continue
            m = sum(r1) / len(r1)
            md = (sum(dcg) / len(dcg)) if dcg else None
            table[top][arm] = {"R1_mean": m, "dCG_mean": md, "n": len(r1),
                               "dirs": sorted({x["dir"] for x in rs})}
            print(f"   {arm:<12} n={len(r1):<3} R@1均值={m:.4f}  "
                  f"ΔCG均值={(f'{md:+.4f}' if md is not None else '—'):<9} "
                  f"n_train={sorted({str(x['n_train']) for x in rs})}")
            for dd in sorted({x["dir"] for x in rs})[:3]:
                print(f"        └ {dd}")

    print()
    print("=" * 104)
    print("② 与论文发表值对表（找最接近的 目录×臂）")
    print("=" * 104)
    cands = [(top, arm, v["R1_mean"]) for top in table for arm, v in table[top].items()]
    report = []
    hit = 0
    for name, pub in PUBLISHED.items():
        best = min(cands, key=lambda c: abs(c[2] - pub))
        diff = best[2] - pub
        ok = abs(diff) < 1e-3
        hit += 1 if ok else 0
        print(f"  {name:<26} 发表 {pub:.3f} ｜ 最接近 {best[0]}/{best[1]:<12} "
              f"均值 {best[2]:.4f} 差 {diff:+.4f} {'✅' if ok else '⚠️ '}")
        report.append({"cell": name, "published": pub, "dir": best[0], "arm": best[1],
                       "mean": round(best[2], 6), "diff": round(diff, 6), "match": ok})
    print(f"\n  → {hit}/{len(PUBLISHED)} 格可在目录级复现")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(
            {"table": table, "match_report": report}, ensure_ascii=False, indent=1))
        print(f"  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
