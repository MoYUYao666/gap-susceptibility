# -*- coding: utf-8 -*-
r"""最终对表：`tab:position_strict` 12 格全部按目录精确对标（2026-10-12）。

**已定位的正确目录**：
| 行 | 目录 |
|---|---|
| CLIP B/32 (WIT) | `strict_freeze` |
| OpenCLIP B/32 (LAION) | **`strict_freeze_oclip/r4`** ← 不是 `strict_freeze_openclip` |
| CLIP B/32† (r4) | `strict_freeze_b32_r4` |
| CLIP B/16† (r4) | `strict_freeze_b16/r4` |

    python tools\_p322_strict_final_match.py [--apply]
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
OUT = REPO / "outputs" / "analysis" / "strict_final_match.json"

# (行, 臂) -> (目录key, 发表ΔCG, 发表R@1)
PUB = {
    ("CLIP_B32_WIT", "text_only"): ("strict_freeze", -0.0465, 0.624),
    ("CLIP_B32_WIT", "both"): ("strict_freeze", -0.0258, 0.693),
    ("CLIP_B32_WIT", "vision_only"): ("strict_freeze", 0.0106, 0.680),
    ("OpenCLIP", "text_only"): ("strict_freeze_oclip/r4", 0.0802, 0.643),
    ("OpenCLIP", "both"): ("strict_freeze_oclip/r4", 0.0864, 0.680),
    ("OpenCLIP", "vision_only"): ("strict_freeze_oclip/r4", 0.0996, 0.672),
    ("CLIP_B32_r4", "text_only"): ("strict_freeze_b32_r4", -0.0304, 0.621),
    ("CLIP_B32_r4", "both"): ("strict_freeze_b32_r4", -0.0204, 0.679),
    ("CLIP_B32_r4", "vision_only"): ("strict_freeze_b32_r4", 0.0166, 0.670),
    ("CLIP_B16_r4", "text_only"): ("strict_freeze_b16/r4", -0.0166, 0.651),
    ("CLIP_B16_r4", "both"): ("strict_freeze_b16/r4", 0.0124, 0.707),
    ("CLIP_B16_r4", "vision_only"): ("strict_freeze_b16/r4", 0.0376, 0.686),
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    idx = defaultdict(list)
    for f in glob.glob(str(REPO / "outputs" / "strict_freeze*" / "**" / "results.json"),
                       recursive=True):
        try:
            d = json.loads(io.open(f, encoding="utf-8", errors="replace").read())
        except Exception:
            continue
        parts = Path(f).relative_to(REPO).parts[1:-1]
        arm = next((p for p in reversed(parts)
                    if p in ("text_only", "both", "vision_only")), None)
        if not arm:
            continue
        key = "/".join(parts[:parts.index(arm)])
        fin = (d.get("final_gap") or {}).get("centroid_gap")
        ini = (d.get("initial_gap") or {}).get("centroid_gap")
        idx[(key, arm)].append({
            "seed": d.get("seed"),
            "R@1": (d.get("final_task_metrics") or {}).get("R@1"),
            "dCG": (fin - ini) if (fin is not None and ini is not None) else None,
            "n_train": d.get("n_trainable_params"),
            "file": str(Path(f).relative_to(REPO)),
        })

    print("=" * 112)
    print("最终逐格对表（ΔCG 按 4 位小数；R@1 按 3 位小数）")
    print("=" * 112)
    rep, okc = [], 0
    for (row, arm), (key, pd_cg, pd_r1) in PUB.items():
        rs = idx.get((key, arm), [])
        if not rs:
            print(f"  ⚠️  {row:<16} {arm:<12} 无归档 ({key})")
            continue
        dc = [x["dCG"] for x in rs if x["dCG"] is not None]
        r1 = [x["R@1"] for x in rs if x["R@1"] is not None]
        mc = sum(dc) / len(dc) if dc else None
        mr = sum(r1) / len(r1) if r1 else None
        cg_ok = mc is not None and round(mc, 4) == round(pd_cg, 4)
        r1_ok = mr is not None and round(mr, 3) == round(pd_r1, 3)
        both = bool(cg_ok and r1_ok)
        okc += 1 if both else 0
        print(f"  {'✅' if both else '⚠️ '} {row:<16} {arm:<12} "
              f"ΔCG {pd_cg:+.4f} vs {mc:+.4f} {round(mc,4):+.4f} {'✅' if cg_ok else '🔴'} ｜ "
              f"R@1 {pd_r1:.3f} vs {mr:.4f} {round(mr,3):.3f} {'✅' if r1_ok else '🔴'}")
        rep.append({"row": row, "arm": arm, "dir": key, "n": len(rs),
                    "pub_dCG": pd_cg, "arc_dCG": round(mc, 6), "dCG_ok": cg_ok,
                    "pub_R1": pd_r1, "arc_R1": round(mr, 6), "R1_ok": r1_ok,
                    "ok": both, "n_train": sorted({str(x["n_train"]) for x in rs}),
                    "files": [x["file"] for x in rs]})
    print(f"\n  → {okc}/{len(PUB)} 格完全复现")

    print()
    print("=" * 112)
    print("仍不一致的格（若有）")
    print("=" * 112)
    bad = [r for r in rep if not r["ok"]]
    for r in bad:
        print(f"  🔴 {r['row']}/{r['arm']}: ΔCG 发表 {r['pub_dCG']:+.4f} 归档 "
              f"{r['arc_dCG']:+.6f} ｜ R@1 发表 {r['pub_R1']:.3f} 归档 {r['arc_R1']:.6f}")
    if not bad:
        print("  ✅ 无")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps({"cells": rep, "n_ok": okc, "n_total": len(PUB)},
                       ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
