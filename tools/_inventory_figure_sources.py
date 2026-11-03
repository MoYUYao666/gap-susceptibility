# -*- coding: utf-8 -*-
r"""盘点 9 张来源不明图的源数据可得性（决定哪些能立即重绘）。

## 现状（`docs/PAPERA_FIGURE_PROVENANCE.md`）

| 类 | 数量 | 图 |
|---|---|---|
| 来源明确（本轮重绘） | 3 | `fig2.png`、`fig8_weight_svd.png`、`fig9_noise_sensitivity.png` |
| **来源不明，需重绘** | 9 | 见下 |

## 本脚本做什么

逐图**探测候选源数据**是否存在、含哪些字段，从而判断能否**重建出与正文数字一致的图**。
**原则：重建必须复现正文所报数值**——若数据缺或对不上，就如实标注"不可重建"，不硬凑。

    python tools\_inventory_figure_sources.py
"""
from __future__ import annotations

import glob
import io
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

# 图 -> (正文 label, 候选源数据 glob 列表, 期望内容)
FIGS: list[tuple[str, str, list[str], str]] = [
    ("fig1.png", "fig:overview",
     ["outputs/flickr30k/rq2_text_only/gap_history.json",
      "outputs/flickr30k/rq2_both/gap_history.json",
      "outputs/flickr30k/baseline_full_ft/gap_history.json",
      "outputs/flickr30k_seeds/rq2_text_only/seed*/gap_history.json"],
     "间隙演化轨迹：Full FT / text-only / both + text-only 5-seed 带"),
    ("fig3.png", "fig:ablation",
     ["outputs/flickr30k/**/gap_history.json", "outputs/**/alpha*.json"],
     "LoRA scaling α 与 target modules 的消融"),
    ("fig4.png", "fig:crossmethod",
     ["outputs/analysis/adapter_common_baseline.json", "outputs/theory/adapter/adapter_all_results.json"],
     "跨方法比较：LoRA 与 Adapter 的 rank/维度缩放"),
    ("fig10_layered_ft.png", "fig:layered_ft",
     ["outputs/layered_ft_results.json"],
     "ViT-B 分层微调：Text+Vis-L1"),
    ("fig12_zeroshot_more.png", "fig:zeroshot",
     ["outputs/imagenet1k_zs_50k_plain.json", "outputs/**/zeroshot*.json"],
     "零样本：DTD 与 Food101"),
    ("fig14_adapter_layered.png", "fig:adapter_layered",
     ["outputs/analysis/adapter_common_baseline.json", "outputs/**/adapter_layered*.json"],
     "Adapter 分层微调"),
    ("fig1_ode_fits.png", "fig:ode",
     ["outputs/theory/beta_pilot/*/seed*/dg_star_history.json",
      "outputs/theory/beta_pilot/*/seed*/beta_results.json"],
     "ODE 轨迹拟合示例"),
    ("fig2_v5_falsification.png", "fig:falsification",
     ["outputs/analysis/k_remeasured_both.json"],
     "‖g_v‖ vs rank：随机投影对照 + 实测"),
    ("fig4_effective_rank.png", "fig:ers",
     ["outputs/analysis/k_remeasured_both.json"],
     "Effective Rank Saturation"),
]


def describe(p: Path) -> str:
    try:
        d = json.loads(p.read_text(encoding="utf-8", errors="ignore"))
    except Exception as e:
        return f"读取失败 {type(e).__name__}"
    if isinstance(d, dict):
        keys = list(d)[:7]
        return f"dict keys={keys}"
    if isinstance(d, list):
        return f"list len={len(d)} 首元素键={list(d[0])[:6] if d and isinstance(d[0], dict) else type(d[0]).__name__}"
    return type(d).__name__


def main() -> int:
    for fig, label, pats, want in FIGS:
        print(f"=== {fig}  [{label}] ===")
        print(f"  期望内容: {want}")
        hits = []
        for pat in pats:
            hits.extend(glob.glob(str(REPO / pat), recursive=True))
        hits = sorted(set(hits))
        if not hits:
            print("  ❌ 无候选源数据")
        else:
            print(f"  候选源数据 {len(hits)} 个：")
            for h in hits[:4]:
                rel = Path(h).relative_to(REPO)
                print(f"    {rel}  → {describe(Path(h))}")
            if len(hits) > 4:
                print(f"    …另有 {len(hits)-4} 个")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
