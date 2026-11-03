# -*- coding: utf-8 -*-
r"""按**表的发布精度**重新判等，并深挖 OpenCLIP 的 ΔCG 偏移（2026-10-12）。

## 已发现

- `CLIP B/32 (WIT)` 三格、`CLIP B/32†(r4)` vision_only、`CLIP B/16†(r4)` both/vision_only
  **完全复现**。
- 剩余"差异"里，**R@1 全部是 3 位小数发布的舍入**（0.6222→0.622、0.6796→0.680、0.6502→0.650）。
- **真正的偏移只有 OpenCLIP 的 ΔCG**：发表 +0.0802/+0.0864/+0.0996 vs
  归档 +0.0694/+0.0881/+0.0925 → 三格**全部**发表值更大（最大差 0.0108）。

    python tools\_p320_strict_precision.py [--apply]
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
OUT = REPO / "outputs" / "analysis" / "strict_precision_match.json"

PUB = {
    ("CLIP_B32_WIT", "text_only"): ("strict_freeze", -0.0465, 0.624),
    ("CLIP_B32_WIT", "both"): ("strict_freeze", -0.0258, 0.693),
    ("CLIP_B32_WIT", "vision_only"): ("strict_freeze", 0.0106, 0.680),
    ("OpenCLIP", "text_only"): ("strict_freeze_openclip", 0.0802, 0.643),
    ("OpenCLIP", "both"): ("strict_freeze_openclip", 0.0864, 0.680),
    ("OpenCLIP", "vision_only"): ("strict_freeze_openclip", 0.0996, 0.672),
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
        rel = Path(f).relative_to(REPO)
        parts = rel.parts[1:-1]
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
            "file": str(rel),
        })

    print("=" * 108)
    print("按表的发布精度判等（ΔCG 4 位小数，R@1 3 位小数）")
    print("=" * 108)
    okc = 0
    rep = []
    for (row, arm), (key, pd_cg, pd_r1) in PUB.items():
        rs = idx.get((key, arm), [])
        if not rs:
            print(f"  ⚠️  {row:<16} {arm:<12} 无归档")
            continue
        dcgs = [x["dCG"] for x in rs if x["dCG"] is not None]
        r1s = [x["R@1"] for x in rs if x["R@1"] is not None]
        m_cg = sum(dcgs) / len(dcgs) if dcgs else None
        m_r1 = sum(r1s) / len(r1s) if r1s else None
        cg_ok = m_cg is not None and round(m_cg, 4) == round(pd_cg, 4)
        r1_ok = m_r1 is not None and round(m_r1, 3) == round(pd_r1, 3)
        both = cg_ok and r1_ok
        okc += 1 if both else 0
        print(f"  {'✅' if both else '⚠️ '} {row:<16} {arm:<12} "
              f"ΔCG {pd_cg:+.4f}/{m_cg:+.4f}→{round(m_cg,4):+.4f} "
              f"{'✅' if cg_ok else '🔴'} ｜ R@1 {pd_r1:.3f}/{m_r1:.4f}→{round(m_r1,3):.3f} "
              f"{'✅' if r1_ok else '🔴'}")
        rep.append({"row": row, "arm": arm, "dir": key,
                    "pub_dCG": pd_cg, "arc_dCG": round(m_cg, 6),
                    "pub_R1": pd_r1, "arc_R1": round(m_r1, 6),
                    "dCG_ok": cg_ok, "R1_ok": r1_ok, "ok": both,
                    "seeds": sorted(str(x["seed"]) for x in rs)})
    print(f"\n  → {okc}/{len(PUB)} 格按发布精度复现")

    print()
    print("=" * 108)
    print("OpenCLIP ΔCG 偏移的深挖：是否用了不同的 initial 基准？")
    print("=" * 108)
    rs = idx.get(("strict_freeze_openclip", "text_only"), [])
    if rs:
        f0 = rs[0]["file"]
        d = json.loads(io.open(REPO / f0, encoding="utf-8", errors="replace").read())
        ig = (d.get("initial_gap") or {})
        fg = (d.get("final_gap") or {})
        print(f"  样本 run: {f0}")
        print(f"    initial CG = {ig.get('centroid_gap')}")
        print(f"    final   CG = {fg.get('centroid_gap')}")
        print(f"    Δ = {fg.get('centroid_gap',0) - ig.get('centroid_gap',0):+.6f}")
        print(f"    initial DG = {ig.get('distribution_gap')}")
        print(f"    final   DG = {fg.get('distribution_gap')}")
    # 归档里三个臂的 ΔCG
    for arm in ("text_only", "both", "vision_only"):
        r = idx.get(("strict_freeze_openclip", arm), [])
        dc = [x["dCG"] for x in r if x["dCG"] is not None]
        if dc:
            pub = PUB[("OpenCLIP", arm)][1]
            print(f"    {arm:<12} 归档 ΔCG 各 seed = {[round(v,4) for v in dc]} "
                  f"均值 {sum(dc)/len(dc):+.4f} ｜ 发表 {pub:+.4f} ｜ 差 {pub - sum(dc)/len(dc):+.4f}")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(rep, ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
