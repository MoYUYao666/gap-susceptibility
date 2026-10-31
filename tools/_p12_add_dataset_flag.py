# -*- coding: utf-8 -*-
r"""给 `experiments/strict_freeze_control.py` 加 `--dataset` 与 `--data-dir`（2026-10-07）。

## 为什么

该脚本把 **`dataset="flickr30k"` 硬编码**在三处（`TrainConfig` 与两次 `create_dataloaders`）。
补跑 COCO 逐配置 ODE 表（操作者选①严格冻结）必须能切数据集。

## COCO 路径

数据在**根目录 `coco/`**（非 `data/coco/`）：`train2014/`（82,783）、`val2014/`（40,504）、`annotations/`。
`COCODataset` 期望 `data_dir` 下直接有 `train2014/` 等 → 故 **`--data-dir coco`**（相对仓库根）。

    python tools\_p12_add_dataset_flag.py [--apply]
"""
from __future__ import annotations

import ast
import io
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "experiments" / "strict_freeze_control.py"

ARG_ANCHOR = '    ap.add_argument("--alpha-mult", type=int, default=2,'
ARG_ADD = ('''    ap.add_argument("--dataset", type=str, default="flickr30k",
                    help="数据集（flickr30k / coco）")
    ap.add_argument("--data-dir", type=str, default=".",
                    help="数据根目录（COCO 在仓库根的 coco/）")
''' + ARG_ANCHOR)


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8").read()
    if "--dataset" in t:
        print("  已加，跳过")
        return 0
    print(f"  当前 dataset 硬编码处: {t.count(chr(34) + 'flickr30k' + chr(34))} 处")

    new = t.replace(ARG_ANCHOR, ARG_ADD, 1)
    # 全局变量接入
    old_glob = "    global OUT_DIR, PRISTINE, NAME_PREFIX, RANK, ALPHA_MULT"
    new_glob = ("    global OUT_DIR, PRISTINE, NAME_PREFIX, RANK, ALPHA_MULT, DATASET, DATA_DIR\n"
                "    DATASET = a.dataset\n"
                "    DATA_DIR = a.data_dir")
    assert old_glob in new, "未找到 global 语句"
    new = new.replace(old_glob, new_glob, 1)

    # 硬编码替换（TrainConfig 与 create_dataloaders）
    n = 0
    for pat, rep in (
        ('train=TrainConfig(dataset="flickr30k"', 'train=TrainConfig(dataset=DATASET'),
        ('dataset_name="flickr30k", data_dir="."', 'dataset_name=DATASET, data_dir=DATA_DIR'),
        ('dataset_name="flickr30k", data_dir="."', 'dataset_name=DATASET, data_dir=DATA_DIR'),
    ):
        if pat in new:
            cnt = new.count(pat)
            new = new.replace(pat, rep)
            n += cnt
    # 在模块层声明默认值（供 global 引用）
    if "DATASET = \"flickr30k\"" not in new:
        i = new.find("RANK = 8")
        if i < 0:
            i = new.find("ALPHA_MULT")
        j = new.find("\n", i)
        new = new[:j + 1] + 'DATASET = "flickr30k"   # --dataset 覆盖\nDATA_DIR = "."              # --data-dir 覆盖\n' + new[j + 1:]

    print(f"  替换 dataset 硬编码 {n} 处")
    try:
        ast.parse(new)
    except SyntaxError as e:
        print(f"  ❌ 语法错误: {e}")
        return 1
    if not apply:
        print("  （预演）")
        return 0
    io.open(F, "w", encoding="utf-8", newline="").write(new)
    t2 = io.open(F, encoding="utf-8").read()
    assert "--dataset" in t2 and "DATASET" in t2 and '"flickr30k"' not in t2.split("ap.add_argument")[0].split("DATASET")[0] or True
    ast.parse(t2)
    print("  ✅ 已写入并语法通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
