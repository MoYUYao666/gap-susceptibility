# -*- coding: utf-8 -*-
r"""重算 OpenCLIP 的效应量（按**逐臂 sd**，修正我先前"约 2 sd"用错的参照）（2026-10-10）。

## 为什么

我在 2026-10-08 写过"OpenCLIP 相邻臂差异仅约 **2 sd**"，
但那个 **2 sd 是拿单 seed 差异除以 CLIP B/32 r8 的跨臂 sd（0.0030）**算的——
**参照量选错**（应逐臂 sd）。**现在 OpenCLIP 已补到 3 seed，可以按正确口径重算。**

    python tools\_p92_oclip_effectsize.py [--apply]
"""
from __future__ import annotations

import glob
import io
import json
import statistics as st
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "oclip_effectsize.json"
ARMS = ("text_only", "both", "vision_only")


def vals(root, arm):
    xs = []
    for f in sorted(glob.glob(str(REPO / root / arm / "seed*" / "results.json"))):
        d = json.loads(io.open(f, encoding="utf-8").read())
        xs.append(d["final_gap"]["centroid_gap"] - d["initial_gap"]["centroid_gap"])
    return xs


def main() -> int:
    apply = "--apply" in sys.argv
    out = {}
    for label, root in (("OpenCLIP B/32 r4", "outputs/strict_freeze_oclip/r4"),
                        ("CLIP B/32 r4", "outputs/strict_freeze_b32_r4"),
                        ("CLIP B/16 r4", "outputs/strict_freeze_b16/r4")):
        print(f"\n=== {label} ===")
        m, s, n = {}, {}, {}
        for arm in ARMS:
            xs = vals(root, arm)
            if not xs:
                continue
            m[arm] = st.mean(xs)
            s[arm] = st.stdev(xs) if len(xs) > 1 else float("nan")
            n[arm] = len(xs)
            print(f"  {arm:<12} mean={m[arm]:+.4f}  sd={s[arm]:.4f}  n={n[arm]}  "
                  f"{[round(v, 4) for v in xs]}")
        print("  相邻臂差异 / 合并 sd：")
        rows = []
        for a, b in (("text_only", "both"), ("both", "vision_only"),
                     ("text_only", "vision_only")):
            if a not in m or b not in m:
                continue
            diff = abs(m[a] - m[b])
            psd = (s[a] ** 2 + s[b] ** 2) ** 0.5
            k = diff / psd if psd else float("nan")
            rows.append({"pair": f"{a} vs {b}", "diff": diff, "pooled_sd": psd, "k_sd": k})
            print(f"    {a:<11} vs {b:<11}  |Δ|={diff:.4f}  pooled_sd={psd:.4f}  "
                  f"→ **{k:.2f} sd**")
        out[label] = {"means": m, "sds": s, "n": n, "pairs": rows}

    print("\n=== 结论（修正我先前'约 2 sd'的说法）===")
    oc = out["OpenCLIP B/32 r4"]["pairs"]
    for r in oc:
        print(f"  OpenCLIP {r['pair']}: **{r['k_sd']:.2f} sd**")
    print("  先前口径错误：用 CLIP B/32 r8 的跨臂 sd（0.0030）当参照；")
    print("  **正确口径**：逐臂 sd 的合并值（见上）")
    if apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(out, ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
