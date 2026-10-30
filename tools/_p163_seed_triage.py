# -*- coding: utf-8 -*-
r"""把 seed 清点结果分组，并标记哪些**值得提升**（2026-10-10）。

## 原则

**只提升"论文仍在用"的实验**——旧协议（被"earlier adaptation convention"取代的）
与已归档的坏数据（`_archive_broken_*`）**不值得花 GPU**。

    python tools\_p163_seed_triage.py
"""
from __future__ import annotations

import io
import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
INV = REPO / "outputs" / "analysis" / "seed_inventory.json"


def main() -> int:
    d = json.loads(io.open(INV, encoding="utf-8").read())
    need = d["need_upgrade"]

    print("=" * 80)
    print(f"seed < 5 的组：{len(need)} 个 → 按类别分组")
    print("=" * 80)

    cats = {
        "① 严格冻结对照（论文 tab:position_strict）": lambda g: g.startswith("strict_freeze"),
        "② COCO 严格冻结（论文数据集翻转段）": lambda g: g.startswith("coco_sweep"),
        "③ 解码器 VLM（论文 §E）": lambda g: g.startswith("vlm_"),
        "④ Adapter 对照（论文 fig:crossmethod）": lambda g: g.startswith("adapter/"),
        "⑤ β pilot（论文 β 系数）": lambda g: g.startswith("beta_pilot/"),
        "⑥ 旧协议 COCO（论文 'earlier convention'）": lambda g: re.match(r"coco/(coco_|full)", g),
        "⑦ 旧协议类对齐（A1 线）": lambda g: g.startswith("a1_class_aligned"),
        "⑧ 已归档坏数据": lambda g: g.startswith("_archive_broken"),
        "⑨ 其他 outputs/ 顶层（无 seed 层）": lambda g: g.startswith("outputs/"),
    }
    seen = set()
    for name, pred in cats.items():
        grp = [r for r in need if pred(r["group"]) and r["group"] not in seen]
        seen |= {r["group"] for r in grp}
        if not grp:
            continue
        print(f"\n── {name}：{len(grp)} 组 ──")
        for r in grp[:12]:
            print(f"   {r['group']:<44} {r['n_seeds']} seed")
        if len(grp) > 12:
            print(f"   …（另 {len(grp) - 12} 组）")

    rest = [r for r in need if r["group"] not in seen]
    if rest:
        print(f"\n── 未分类：{len(rest)} 组 ──")
        for r in rest[:16]:
            print(f"   {r['group']:<44} {r['n_seeds']} seed")

    print()
    print("=" * 80)
    print("建议（按论文价值排序）")
    print("=" * 80)
    recs = [
        ("① 严格冻结三骨干（3→5 seed）", "strict_freeze_b32_r4 / b16/r4 / oclip/r4",
         "论文 tab:position_strict 的核心；OpenCLIP 与 B/16 的相邻臂差异只在 1–5 sd 之间，加 seed 最有价值"),
        ("② COCO 严格冻结（3→5 seed）", "coco_sweep_text_only + coco_sweep",
         "数据集翻转段的证据；现 text_only 3 seed、both 3 seed"),
        ("③ 解码器 VLM（5→9 seed）", "vlm_seeds_bf16", "**已在跑**"),
        ("④ Adapter 对照（3→5 seed）", "outputs/adapter/*（10 组 × 3 seed）",
         "论文 fig:crossmethod；10 组 × 2 seed = 20 run"),
        ("⑤ β pilot（3→5 seed）", "outputs/theory/beta_pilot/*（3 组）", "β 系数，论文已标注偏大 ~40×"),
        ("⑥–⑨", "旧协议 / 归档坏数据 / 无 seed 层", "**不建议**——论文已声明旧协议被取代，且已归档为坏数据"),
    ]
    for tag, scope, why in recs:
        print(f"\n  {tag}\n     范围：{scope}\n     理由：{why}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
