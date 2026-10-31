# -*- coding: utf-8 -*-
r"""`tab:position_strict` 逐格对标归档（17 个数值格）（2026-10-12）。

表（`empirical.tex` 的 tab:position_strict）：

| Backbone | Text-only | Both | Vision-only |
|---|---|---|---|
| CLIP B/32 (WIT) | −0.0465 / 0.624 | −0.0258 / 0.693 | +0.0106 / 0.680 |
| OpenCLIP B/32 (LAION) | +0.0802 / 0.643 | +0.0864 / 0.680 | +0.0996 / 0.672 |
| CLIP B/32† (WIT) | −0.0304 / 0.621 | −0.0204 / 0.679 | +0.0166 / 0.670 |
| CLIP B/16† (WIT) | −0.0166 / 0.651 | +0.0124 / 0.707 | +0.0376 / 0.686 |
| SigLIP B/16 (WebLI) | +0.0664 / 0.432 | −0.0114 / 0.619 | +0.0522 / 0.341 |
| BioCLIP B/16 (bio.) | −0.3671 / --- | −0.4515 / --- | −0.2927 / --- |

    python tools\_p319_strict_cell_match.py [--apply]
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
OUT = REPO / "outputs" / "analysis" / "strict_cell_match.json"

# (行标签, 臂) -> (发表 ΔCG, 发表 R@1)
PUB = {
    ("CLIP_B32_WIT", "text_only"): (-0.0465, 0.624),
    ("CLIP_B32_WIT", "both"): (-0.0258, 0.693),
    ("CLIP_B32_WIT", "vision_only"): (+0.0106, 0.680),
    ("OpenCLIP_B32_LAION", "text_only"): (+0.0802, 0.643),
    ("OpenCLIP_B32_LAION", "both"): (+0.0864, 0.680),
    ("OpenCLIP_B32_LAION", "vision_only"): (+0.0996, 0.672),
    ("CLIP_B32_r4", "text_only"): (-0.0304, 0.621),
    ("CLIP_B32_r4", "both"): (-0.0204, 0.679),
    ("CLIP_B32_r4", "vision_only"): (+0.0166, 0.670),
    ("CLIP_B16_r4", "text_only"): (-0.0166, 0.651),
    ("CLIP_B16_r4", "both"): (+0.0124, 0.707),
    ("CLIP_B16_r4", "vision_only"): (+0.0376, 0.686),
    ("SigLIP_B16", "text_only"): (+0.0664, 0.432),
    ("SigLIP_B16", "both"): (-0.0114, 0.619),
    ("SigLIP_B16", "vision_only"): (+0.0522, 0.341),
    ("BioCLIP_B16", "text_only"): (-0.3671, None),
    ("BioCLIP_B16", "both"): (-0.4515, None),
    ("BioCLIP_B16", "vision_only"): (-0.2927, None),
}

# 每个 (行, 臂) 对应的归档目录 key（= outputs/<key>/<arm>/seed*/results.json）
CELLDIR = {
    ("CLIP_B32_WIT", "text_only"): "strict_freeze",
    ("CLIP_B32_WIT", "both"): "strict_freeze",
    ("CLIP_B32_WIT", "vision_only"): "strict_freeze",
    ("OpenCLIP_B32_LAION", "text_only"): "strict_freeze_openclip",
    ("OpenCLIP_B32_LAION", "both"): "strict_freeze_openclip",
    ("OpenCLIP_B32_LAION", "vision_only"): "strict_freeze_openclip",
    ("CLIP_B32_r4", "text_only"): "strict_freeze_b32_r4",
    ("CLIP_B32_r4", "both"): "strict_freeze_b32_r4",
    ("CLIP_B32_r4", "vision_only"): "strict_freeze_b32_r4",
    ("CLIP_B16_r4", "text_only"): "strict_freeze_b16/r4",
    ("CLIP_B16_r4", "both"): "strict_freeze_b16/r4",
    ("CLIP_B16_r4", "vision_only"): "strict_freeze_b16/r4",
    ("SigLIP_B16", "text_only"): "siglip_strict",
    ("SigLIP_B16", "both"): "siglip_strict",
    ("SigLIP_B16", "vision_only"): "siglip_strict",
    ("BioCLIP_B16", "text_only"): "strict_freeze_bioclip",
    ("BioCLIP_B16", "both"): "strict_freeze_bioclip",
    ("BioCLIP_B16", "vision_only"): "strict_freeze_bioclip",
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    # 载入所有 strict 相关 run，按 (top2, arm) 索引
    idx = defaultdict(list)
    for pat in ("strict_freeze*", "siglip_strict*", "siglip"):
        for f in glob.glob(str(REPO / "outputs" / pat / "**" / "results.json"),
                           recursive=True):
            try:
                d = json.loads(io.open(f, encoding="utf-8", errors="replace").read())
            except Exception:
                continue
            rel = Path(f).relative_to(REPO)
            parts = rel.parts[1:-1]      # 去掉 outputs 与 results.json
            arm = next((p for p in reversed(parts)
                        if p in ("text_only", "both", "vision_only",
                                 "text-only", "vision-only")), None)
            if not arm:
                continue
            fin = (d.get("final_gap") or {}).get("centroid_gap")
            ini = (d.get("initial_gap") or {}).get("centroid_gap")
            key = "/".join(parts[:parts.index(arm)])
            idx[(key, arm)].append({
                "seed": d.get("seed"),
                "R@1": (d.get("final_task_metrics") or {}).get("R@1"),
                "dCG": (fin - ini) if (fin is not None and ini is not None) else None,
                "file": str(rel),
            })

    print("=" * 110)
    print("逐格对标")
    print("=" * 110)
    report = []
    ok_n = 0
    for (row, arm), (pd_cg, pd_r1) in PUB.items():
        want = CELLDIR.get((row, arm))
        rs = idx.get((want, arm), []) if want else []
        if not rs:
            print(f"  ⚠️  {row:<22} {arm:<12} 找不到归档（期望 {want}）")
            report.append({"cell": f"{row}/{arm}", "status": "no_archive",
                           "expected_dir": want})
            continue
        dcgs = [x["dCG"] for x in rs if x["dCG"] is not None]
        r1s = [x["R@1"] for x in rs if x["R@1"] is not None]
        m_cg = sum(dcgs) / len(dcgs) if dcgs else None
        m_r1 = sum(r1s) / len(r1s) if r1s else None
        cg_ok = m_cg is not None and abs(m_cg - pd_cg) < 5e-4
        r1_ok = (m_r1 is None and pd_r1 is None) or \
                (m_r1 is not None and pd_r1 is not None and abs(m_r1 - pd_r1) < 5e-4)
        both_ok = cg_ok and r1_ok
        ok_n += 1 if both_ok else 0
        print(f"  {'✅' if both_ok else '⚠️ '} {row:<22} {arm:<12} "
              f"ΔCG 发表 {pd_cg:+.4f} / 归档 "
              f"{(f'{m_cg:+.4f}' if m_cg is not None else '—'):<9} "
              f"{'✅' if cg_ok else '🔴'} ｜ R@1 发表 "
              f"{(f'{pd_r1:.3f}' if pd_r1 is not None else '—'):<7} / 归档 "
              f"{(f'{m_r1:.4f}' if m_r1 is not None else '—'):<8} "
              f"{'✅' if r1_ok else '🔴'}")
        report.append({
            "cell": f"{row}/{arm}", "dir": want, "n": len(rs),
            "pub_dCG": pd_cg, "arc_dCG": round(m_cg, 6) if m_cg is not None else None,
            "dCG_ok": cg_ok,
            "pub_R1": pd_r1, "arc_R1": round(m_r1, 6) if m_r1 is not None else None,
            "R1_ok": r1_ok, "ok": both_ok,
            "seeds": sorted(str(x["seed"]) for x in rs),
        })
    print(f"\n  → {ok_n}/{len(PUB)} 格完全复现")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(report, ensure_ascii=False, indent=1))
        print(f"  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
