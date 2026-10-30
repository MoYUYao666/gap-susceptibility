# -*- coding: utf-8 -*-
r"""COCO 补跑的逐配置汇总（2026-10-08）。

    python tools\_p31_coco_table.py [--apply]
"""
from __future__ import annotations

import collections
import glob
import io
import json
import statistics as st
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def main() -> int:
    apply = "--apply" in sys.argv
    byconf = collections.defaultdict(list)
    for f in sorted(glob.glob(str(REPO / "outputs/coco_sweep/**/results.json"), recursive=True)):
        parts = Path(f).parts
        rk = parts[-4]      # 如 r4
        arm = parts[-3]     # 如 text_only
        d = json.loads(io.open(f, encoding="utf-8").read())
        cg = d["final_gap"]["centroid_gap"] - d["initial_gap"]["centroid_gap"]
        r1 = d["final_task_metrics"].get("R@1")
        byconf[(arm, rk)].append((cg, r1))

    print("=== COCO 逐配置 CGΔ（严格冻结，5000 样本 × 10 epoch）===")
    print(f"  {'配置':<22} {'seed':<6} {'CGΔ 均值':>10} {'sd':>8} {'R@1':>7}")
    rows = []
    for k in sorted(byconf, key=lambda x: (x[0], int(x[1][1:]))):
        v = byconf[k]
        cgs = [a for a, _ in v]
        r1s = [b for _, b in v if b is not None]
        sd = st.stdev(cgs) if len(cgs) > 1 else None
        arm, rk = k
        label = f"{arm} r={rk[1:]}"
        print(f"  {label:<22} {len(v)}/3    {st.mean(cgs):>+10.4f} "
              f"{(f'{sd:.4f}' if sd is not None else '—'):>8} "
              f"{(f'{st.mean(r1s):.3f}' if r1s else '—'):>7}")
        rows.append((label, len(v), st.mean(cgs), sd, st.mean(r1s) if r1s else None))

    total = sum(len(v) for v in byconf.values())
    print(f"\n  总计 {total}/36 run")

    # 两臂齐备的秩 → 判最保护臂
    print("\n=== 两臂齐备的秩：最保护臂 ===")
    done = collections.defaultdict(dict)
    for (arm, rk), v in byconf.items():
        if len(v) == 3:
            done[rk][arm] = st.mean(a for a, _ in v)
    for rk in sorted(done, key=lambda x: int(x[1:])):
        d = done[rk]
        if "text_only" in d and "both" in d:
            best = "text_only" if d["text_only"] < d["both"] else "both"
            print(f"  r={rk[1:]:<4} text_only={d['text_only']:+.4f}  both={d['both']:+.4f}"
                  f"  → **{best}**")
        else:
            have = ", ".join(f"{k}={v:+.4f}" for k, v in d.items())
            print(f"  r={rk[1:]:<4} 仅 {have}（缺另一臂）")

    if apply:
        out = REPO / "outputs/analysis/coco_sweep_table.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        io.open(out, "w", encoding="utf-8", newline="").write(json.dumps(
            {"rows": [{"config": a, "n": b, "cg_mean": c, "cg_sd": d, "r1": e}
                      for a, b, c, d, e in rows], "total": total},
            ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {out.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
