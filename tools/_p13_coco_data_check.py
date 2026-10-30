# -*- coding: utf-8 -*-
r"""验证 COCO 数据路径与批量形状（**不加载模型、不占 GPU**，2026-10-07）。

## 为什么先做这个

补跑 COCO 逐配置表前，须先确认：
1. `--data-dir coco` 能正确找到 `train2014/` 与标注；
2. 取出的 batch 含 CLIP 训练所需的键（`image` / `input_ids` / `attention_mask`）。

**若这两步不过，跑几小时的训练纯属浪费**（本项目已有"α 首跑样本量错 15 倍"的前车之鉴）。

    python tools\_p13_coco_data_check.py
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))


def main() -> int:
    from src.dataset import create_dataloaders

    print("=== COCO 数据路径验证（CPU，不加载模型）===")
    for ds, dd in (("coco", "coco"),):
        print(f"\n  ── dataset={ds}  data_dir={dd} ──")
        try:
            loader, val, test = create_dataloaders(
                dataset_name=ds, data_dir=dd, batch_size=8, max_samples=64)
        except Exception as e:
            print(f"  ❌ 构造失败: {str(e)[:200]}")
            return 1
        print(f"  ✅ 三个 loader: train={len(loader.dataset)} val={len(val.dataset)} "
              f"test={len(test.dataset)}")
        b = next(iter(loader))
        print(f"  batch 键: {sorted(b.keys())}")
        for k in ("image", "input_ids", "attention_mask"):
            if k in b:
                try:
                    print(f"    {k:<16} shape={tuple(b[k].shape)}")
                except Exception:
                    print(f"    {k:<16} {type(b[k])}")
            else:
                print(f"    ❌ 缺 {k}")
        need = {"image", "input_ids", "attention_mask"}
        missing = need - set(b.keys())
        if missing:
            print(f"  ❌ 缺必需键: {missing}")
            return 1
        print("  ✅ 训练所需键齐备")
    print("\n  ✅ COCO 数据路径验证通过 → 可安全安排补跑")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
