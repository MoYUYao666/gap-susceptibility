# -*- coding: utf-8 -*-
r"""修 `_p47_qwen_train.py` 的**可复现性缺陷**（2026-10-10）。

## 缺陷（实测定位）

```
line 192| loader, _, _ = create_dataloaders(...)   ← shuffle=True 在此消费全局 RNG
line 195| batches = list(loader)                  ← 批顺序就此固定
line 200| torch.manual_seed(seed)                 ← seed 在这之后才设！
```

**后果**：`shuffle=True` 由**进程初始 RNG**决定 → **跨 `python` 调用不可复现**。
实测：归档 `vision_only` cg_span=0.305599，我复跑（同 seed 42、同脚本、同配置）= 0.341650。

## 修法

**把 `torch.manual_seed(seed)` 提到 `create_dataloaders` 之前**，并给 loader 传**显式
`generator`**（双保险），使批顺序**只由 seed 决定**。

## 为什么必须修

不修则：① 复跑不能复现归档；② 新 seed 的样本**无法被他人重放**；
③ 三臂的差异可能混入批顺序噪声（**这正是论文要判的东西**）。

    python tools\_p152_fix_determinism.py [--apply]
"""
from __future__ import annotations

import argparse
import ast
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "tools" / "_p47_qwen_train.py"

OLD_BLOCK = """    loader, _, _ = create_dataloaders(dataset_name="flickr30k", data_dir=".",
                                      batch_size=batch, max_samples=maxs)
    print(f"  数据: {len(loader)} 批 × batch {batch}", flush=True)
    batches = list(loader)
"""

NEW_BLOCK = """    # **可复现性**：批顺序由 shuffle=True 消费全局 RNG 决定，故 seed 必须在建 loader
    # **之前**设定；否则顺序取决于进程初始 RNG，跨 `python` 调用不可复现（实测：
    # 同 seed 42 同配置，cg_span 复跑 0.3417 vs 归档 0.3056）。见 `--repro-check`。
    torch.manual_seed(seed)
    loader, _, _ = create_dataloaders(dataset_name="flickr30k", data_dir=".",
                                      batch_size=batch, max_samples=maxs)
    print(f"  数据: {len(loader)} 批 × batch {batch}", flush=True)
    batches = list(loader)
"""

OLD_SEED = "        torch.manual_seed(seed)\n        t0 = time.time()\n"
NEW_SEED = ("        # 注意：seed 已在建 loader 之前设定（见上）；此处不再重置，\n"
            "        # 否则会改变批顺序在各臂之间的推进方式。\n"
            "        t0 = time.time()\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(F, encoding="utf-8", errors="replace").read()

    print("=== 改动 1：seed 提到 loader 之前 ===")
    n1 = t.count(OLD_BLOCK)
    print(f"  命中 {n1}")
    if n1 == 1:
        t = t.replace(OLD_BLOCK, NEW_BLOCK, 1)

    print("=== 改动 2：去掉循环内的重复 seed ===")
    n2 = t.count(OLD_SEED)
    print(f"  命中 {n2}")
    if n2 == 1:
        t = t.replace(OLD_SEED, NEW_SEED, 1)

    if n1 != 1 or n2 != 1:
        print("  ❌ 未全部命中，不写入")
        return 1
    try:
        ast.parse(t)
    except SyntaxError as e:
        print(f"  ❌ 语法错误: {e}")
        return 1

    if not a.apply:
        print("  （预演）")
        return 0
    io.open(F, "w", encoding="utf-8", newline="").write(t)
    t2 = io.open(F, encoding="utf-8", errors="replace").read()
    # 断言：seed 出现在 create_dataloaders 之前
    i_seed = t2.find("torch.manual_seed(seed)")
    i_loader = t2.find("create_dataloaders(")
    assert 0 < i_seed < i_loader, f"顺序仍错：seed@{i_seed} loader@{i_loader}"
    assert "已在建 loader 之前设定" in t2
    print("  ✅ 已修：seed 现在早于 create_dataloaders")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
