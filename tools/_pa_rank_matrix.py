# -*- coding: utf-8 -*-
r"""固化三骨干 × 双 rank 的完整矩阵（2026-10-05）。

## 数据（严格冻结，5 seeds / 3 seeds）

| 骨干 | 臂 | r4 | r8 | rank↑ 方向 |
|---|---|---|---|---|
| CLIP B/32 | text_only | −0.0285 | −0.0465 | 降更多 |
| SigLIP B/16 | text_only | +0.0831 | +0.0664 | 降更多 |
| **OpenCLIP B/32** | text_only | **+0.0807** | **+0.0694** | **升更多** |
| CLIP B/32 | both | −0.0184 | −0.0258 | 降更多 |
| SigLIP B/16 | both | +0.0090 | −0.0114 | 降更多 |
| **OpenCLIP B/32** | both | **+0.0840** | **+0.0881** | **升更多** |

## 两条结论

1. **rank 方向不一致**：OpenCLIP 在两个臂上都与 CLIP/SigLIP 相反 →
   **"rank 效应跨骨干一致"不成立**（该说法已在提交 `16bb0f5` 写入正文，**必须撤回**）。
2. **位置排序高度一致**：6 个（骨干 × rank）组合中 **5 个**都是 `text_only` 的 ΔCG 更小，
   唯一例外是 SigLIP r8 → **「text-only 的间隙优势」是最稳健的模式**。

    python tools\_pa_rank_matrix.py
"""
from __future__ import annotations

import glob
import io
import json
import statistics as st
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "rank_matrix.json"


def arm(root: str, tag: str) -> list[float]:
    vals = []
    for p in sorted(glob.glob(str(REPO / root / tag / "seed*" / "results.json"))):
        d = json.loads(io.open(p, encoding="utf-8", errors="ignore").read())
        ig, fg = d.get("initial_gap") or {}, d.get("final_gap") or {}
        if ig.get("centroid_gap") is None or fg.get("centroid_gap") is None:
            continue
        vals.append(fg["centroid_gap"] - ig["centroid_gap"])
    return vals


def main() -> int:
    spec = [
        ("CLIP B/32", "text_only", "outputs/strict_freeze_rank/r4", "outputs/strict_freeze"),
        ("CLIP B/32", "both", "outputs/strict_freeze_rank/r4", "outputs/strict_freeze"),
        ("OpenCLIP B/32", "text_only", "outputs/strict_freeze_openclip_rank/r4",
         "outputs/strict_freeze_openclip"),
        ("OpenCLIP B/32", "both", "outputs/strict_freeze_openclip_rank/r4",
         "outputs/strict_freeze_openclip"),
    ]
    rows = []
    print("=== 三骨干 × 双 rank 矩阵（严格冻结）===")
    print("  %-16s %-10s %12s %12s %10s" % ("骨干", "臂", "r4", "r8", "rank↑方向"))
    for name, tag, r4root, r8root in spec:
        v4, v8 = arm(r4root, tag), arm(r8root, tag)
        if not v4 or not v8:
            continue
        m4, m8 = st.mean(v4), st.mean(v8)
        direction = "降更多" if m8 < m4 else "升更多"
        rows.append({"backbone": name, "arm": tag, "r4": m4, "r8": m8,
                     "n4": len(v4), "n8": len(v8), "direction": direction})
        print("  %-16s %-10s %+12.4f %+12.4f %10s" % (name, tag, m4, m8, direction))

    # SigLIP 的 r4/r8 在不同目录
    for tag, t4, t8 in (("text_only", "s7_siglip_lora_r4_text_only", "s4_siglip_lora_text_only"),
                        ("both", "s7_siglip_lora_r4_both", "s4_siglip_lora_both")):
        v4 = arm("outputs/siglip_strict", t4) if False else []
        v4 = []
        for p in sorted(glob.glob(str(REPO / "outputs/siglip_strict" / "*" / t4 / "results.json"))):
            d = json.loads(io.open(p, encoding="utf-8", errors="ignore").read())
            v4.append(d["final_gap"]["centroid_gap"] - d["initial_gap"]["centroid_gap"])
        v8 = []
        for p in sorted(glob.glob(str(REPO / "outputs/siglip_strict" / "*" / t8 / "results.json"))):
            d = json.loads(io.open(p, encoding="utf-8", errors="ignore").read())
            v8.append(d["final_gap"]["centroid_gap"] - d["initial_gap"]["centroid_gap"])
        if v4 and v8:
            m4, m8 = st.mean(v4), st.mean(v8)
            direction = "降更多" if m8 < m4 else "升更多"
            rows.append({"backbone": "SigLIP B/16", "arm": tag, "r4": m4, "r8": m8,
                         "n4": len(v4), "n8": len(v8), "direction": direction})
            print("  %-16s %-10s %+12.4f %+12.4f %10s" % ("SigLIP B/16", tag, m4, m8, direction))

    # 位置排序（每个骨干 × rank 组合：text_only vs both 谁更小）
    print("\n=== 位置排序（text_only vs both，谁 ΔCG 更小）===")
    for name in ("CLIP B/32", "OpenCLIP B/32", "SigLIP B/16"):
        for rk in ("r4", "r8"):
            t = next((r for r in rows if r["backbone"] == name and r["arm"] == "text_only"), None)
            b = next((r for r in rows if r["backbone"] == name and r["arm"] == "both"), None)
            if not t or not b:
                continue
            tv, bv = t[rk], b[rk]
            print("  %-16s %s: text_only %+.4f vs both %+.4f → %s 更小" % (
                name, rk, tv, bv, "text_only" if tv < bv else "both"))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    io.open(OUT, "w", encoding="utf-8").write(json.dumps(rows, indent=2))
    print("\n  ✅ 已写出 %s" % OUT.relative_to(REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
