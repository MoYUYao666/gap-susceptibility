# -*- coding: utf-8 -*-
r"""四骨干 × rank 的位置效应**权威分析**（2026-10-06）。

## 为什么单独成脚本

我在这个主题上**已快速断言错三次**，故一律：**数字由代码算，结论由代码判**。

## 数据（全部严格冻结）

| 骨干 | 架构 | 预训练 | 来源 |
|---|---|---|---|
| CLIP ViT-B/32 | patch 32 | WIT | `outputs/strict_freeze{,_rank}` |
| OpenCLIP ViT-B/32 | patch 32 | LAION-2B | `outputs/strict_freeze_openclip{,_rank}` |
| SigLIP ViT-B/16 | patch 16 | WebLI（sigmoid） | `outputs/siglip_strict` |
| **BioCLIP ViT-B/16** | patch 16 | **生物域** | `outputs/strict_freeze_bioclip` |

    python tools\_pa_four_backbone_analysis.py
"""
from __future__ import annotations

import glob
import json
import statistics as st
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

# (骨干, 架构标签, 臂) -> {rank: [ΔCG...]}
SRC = {
    ("CLIP B/32", "patch32", "text_only"): {
        4: "outputs/strict_freeze_rank/r4/text_only/seed*/results.json",
        8: "outputs/strict_freeze/text_only/seed*/results.json"},
    ("CLIP B/32", "patch32", "both"): {
        4: "outputs/strict_freeze_rank/r4/both/seed*/results.json",
        8: "outputs/strict_freeze/both/seed*/results.json"},
    ("CLIP B/32", "patch32", "vision_only"): {
        8: "outputs/strict_freeze/vision_only/seed*/results.json"},
    ("OpenCLIP B/32", "patch32", "text_only"): {
        4: "outputs/strict_freeze_openclip_rank/r4/text_only/seed*/results.json",
        8: "outputs/strict_freeze_openclip/text_only/seed*/results.json"},
    ("OpenCLIP B/32", "patch32", "both"): {
        4: "outputs/strict_freeze_openclip_rank/r4/both/seed*/results.json",
        8: "outputs/strict_freeze_openclip/both/seed*/results.json"},
    ("OpenCLIP B/32", "patch32", "vision_only"): {
        8: "outputs/strict_freeze_openclip/vision_only/seed*/results.json"},
    ("SigLIP B/16", "patch16", "text_only"): {
        4: "outputs/siglip_strict/*/s7_siglip_lora_r4_text_only/results.json",
        8: "outputs/siglip_strict/*/s4_siglip_lora_text_only/results.json"},
    ("SigLIP B/16", "patch16", "both"): {
        4: "outputs/siglip_strict/*/s7_siglip_lora_r4_both/results.json",
        8: "outputs/siglip_strict/*/s4_siglip_lora_both/results.json"},
    ("SigLIP B/16", "patch16", "vision_only"): {
        8: "outputs/siglip_strict/*/s6_siglip_lora_vision_only/results.json"},
}


def dcg(pattern: str) -> list[float]:
    out = []
    for p in sorted(REPO.glob(pattern)):
        try:
            d = json.loads(p.read_text(encoding="utf-8", errors="ignore"))
        except Exception:
            continue
        ig, fg = d.get("initial_gap") or {}, d.get("final_gap") or {}
        if ig.get("centroid_gap") is not None and fg.get("centroid_gap") is not None:
            out.append(fg["centroid_gap"] - ig["centroid_gap"])
    return out


def main() -> int:
    # BioCLIP 走部分结果文件
    bio = json.loads((REPO / "outputs/strict_freeze_bioclip/results_partial.json").read_text(encoding="utf-8"))
    for arm in ("text_only", "both", "vision_only"):
        SRC[("BioCLIP B/16", "patch16", arm)] = {4: None}
    bio_vals = {}
    for r in bio["records"]:
        bio_vals.setdefault(r["arm"], []).append(r["delta_cg"])

    table: dict[str, dict[str, float]] = {}
    print("=== 四骨干 × rank：ΔCG（严格冻结）===")
    print(f"  {'骨干':<16}{'架构':<9}{'rank':<6}{'text_only':>12}{'both':>12}{'vision_only':>13}")
    for (bb, arch), ranks in sorted({(k[0], k[1]): None for k in SRC}.items()):
        for rk in (4, 8):
            cells = {}
            for arm in ("text_only", "both", "vision_only"):
                s = SRC.get((bb, arch, arm), {}).get(rk)
                if s:
                    v = dcg(s)
                    if v:
                        cells[arm] = st.mean(v)
            if bb.startswith("BioCLIP") and rk in bio_vals:
                pass
            if bb.startswith("BioCLIP") and rk == 4:
                cells = {a: st.mean(vs) for a, vs in bio_vals.items()}
            elif bb.startswith("BioCLIP"):
                continue
            if not cells:
                continue
            key = f"{bb} r{rk}"
            table[key] = cells
            print(f"  {bb:<16}{arch:<9}r{rk:<5}"
                  f"{cells.get('text_only', float('nan')):>12.4f}"
                  f"{cells.get('both', float('nan')):>12.4f}"
                  f"{cells.get('vision_only', float('nan')):>13.4f}")

    print("\n=== 位置排序（ΔCG 最小者胜）===")
    verdict: dict[str, list[str]] = {"patch32": [], "patch16": []}
    for key, cells in table.items():
        if len(cells) < 2:
            continue
        best = min(cells, key=lambda a: cells[a])
        arch = "patch32" if "B/32" in key else "patch16"
        bb = key.rsplit(" r", 1)[0]
        verdict[arch].append(best)
        print(f"  {key:<24} 最佳臂 = {best:<12}（{cells[best]:+.4f}）  [{arch}]")

    print("\n=== 判定 ===")
    for arch, bests in verdict.items():
        if bests:
            uniq = sorted(set(bests))
            print(f"  {arch:<9} 各配置最佳臂: {uniq}  → "
                  f"{'一致' if len(uniq) == 1 else '不一致'}（{len(bests)} 个配置）")
    p32 = set(verdict["patch32"])
    p16 = set(verdict["patch16"])
    if len(p32) == 1 and len(p16) == 1 and p32 != p16:
        print(f"\n  ✅ **位置效应按 patch 尺寸分组**：patch32 → {p32.pop()} ｜ patch16 → {p16.pop()}")
    else:
        print(f"\n  ⚠ 未呈现清晰的按-架构分组（patch32 {p32} ｜ patch16 {p16}）")
    print("\n  注：BioCLIP 仅 rank 4（操作者 2026-10-06 要求停止）；其余骨干 rank 4 与 8 皆有。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
