# -*- coding: utf-8 -*-
r"""清点补跑实验的进度与已得结果（2026-10-08）。

    python tools\_status_summary.py
"""
from __future__ import annotations

import glob
import io
import json
import statistics as st
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def cg(f: Path):
    try:
        d = json.loads(io.open(f, encoding="utf-8").read())
    except Exception:
        return None, None
    g = d.get("initial_gap", {}).get("centroid_gap")
    h = d.get("final_gap", {}).get("centroid_gap")
    r1 = d.get("final_task_metrics", {}).get("R@1")
    return (h - g) if (g is not None and h is not None) else None, r1


def main() -> int:
    print("=== ① patch-16 骨干对照（③b）===")
    for f in sorted(glob.glob(str(REPO / "outputs/strict_freeze_b16/r4/*/seed*/results.json"))):
        v, r1 = cg(Path(f))
        print(f"  {Path(f).parts[-3]:<12} CGΔ={v:+.4f}  R@1={r1:.3f}")

    print("\n=== ② 同秩对照（CLIP B/32 @ rank 4）===")
    for f in sorted(glob.glob(str(REPO / "outputs/strict_freeze_b32_r4/*/seed*/results.json"))):
        v, r1 = cg(Path(f))
        print(f"  {Path(f).parts[-3]:<12} CGΔ={v:+.4f}  R@1={r1:.3f}")

    print("\n=== ③ OpenCLIP B/32 @ rank 4（③a）===")
    for f in sorted(glob.glob(str(REPO / "outputs/strict_freeze_oclip/r4/*/seed*/results.json"))):
        v, r1 = cg(Path(f))
        print(f"  {Path(f).parts[-3]:<12} CGΔ={v:+.4f}  R@1={r1:.3f}")

    print("\n=== ④ COCO 补跑（36 run 目标）===")
    fs = sorted(glob.glob(str(REPO / "outputs/coco_sweep/**/results.json"), recursive=True))
    print(f"  已完成 {len(fs)} / 36")
    for f in fs:
        v, r1 = cg(Path(f))
        rel = str(Path(f)).replace(str(REPO) + "\\", "").replace("\\", "/")
        print(f"  {rel:<52} CGΔ={v:+.4f}  R@1={r1:.3f}" if v is not None else f"  {rel}")

    print("\n=== ⑤ 实验 A（α 由梯度预测）===")
    pa = REPO / "outputs/theory/alpha_trainer_based/alpha_trainer_based.json"
    if pa.exists():
        d = json.loads(io.open(pa, encoding="utf-8").read())
        print(f"  aligned={d.get('aligned')}  attempt={d.get('attempt')}")
        for r in d.get("records", []):
            y = r.get("dg_star", [])
            print(f"  seed {r.get('seed')}: 跨度 {r.get('span'):.4f}（归档 0.1641）"
                  f" ｜ 起始 {y[0] if y else '—'}")
        for k in d.get("diagnosis", {}).get("problems", []):
            print(f"    • {k}")
    else:
        print("  尚无结果")

    print("\n=== ⑥ 三臂汇总（5 骨干，含论文归档）===")
    rows = [
        ("CLIP B/32 @ r8 (WIT)", "outputs/strict_freeze", "5 seed"),
        ("CLIP B/32 @ r4 (WIT)", "outputs/strict_freeze_b32_r4", "1 seed"),
        ("CLIP B/16 @ r4 (WIT)", "outputs/strict_freeze_b16/r4", "1 seed"),
        ("OpenCLIP B/32 r4 (LAION)", "outputs/strict_freeze_oclip/r4", "1 seed"),
    ]
    for name, root, seeds in rows:
        vals = {}
        for arm in ("text_only", "both", "vision_only"):
            xs = [v for v, _ in (cg(Path(f)) for f in
                                 glob.glob(str(REPO / root / arm / "seed*" / "results.json")))
                  if v is not None]
            if xs:
                vals[arm] = st.mean(xs)
        if vals:
            best = min(vals, key=lambda a: vals[a])
            s = " ｜ ".join(f"{a}={vals[a]:+.4f}" for a in ("text_only", "both", "vision_only")
                            if a in vals)
            print(f"  {name:<26} {s}  → **{best}**（{seeds}）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
