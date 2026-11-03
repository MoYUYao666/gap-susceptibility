# -*- coding: utf-8 -*-
r"""修 A 脚本的 CUDA OOM（2026-10-08 19:35）。

## 实测故障

```
[Epoch 1 完成] → capture_inner → torch.OutOfMemoryError:
GPU 0 总容量 8.00 GiB，0 字节空闲；PyTorch 已分配 21.15 GiB
```

**根因**：`capture_inner` 在 `torch.enable_grad()` 下对**最多 8 个验证批**做前向，
**把每批的嵌入与计算图都留在列表里**；而此时**训练循环的图尚未释放**
→ 两者叠加远超 8 GB。

**次因**：`imgs`/`txts` 列表在 `with torch.enable_grad()` 内累积，
循环结束后才 `torch.cat` → 图全部驻留。

## 修法（三个改动，都不影响动力学）

| # | 改动 | 理由 |
|---|---|---|
| 1 | 梯度版**只取 2 批**（其余批数不再参与） | `∇DG*` 是**期望**的估计，2 批 × 64 = 128 个样本足够；**DG\\* 轨迹本身由 `_compute_dg_star_record` 单独测**（`no_grad`，可用满验证集） |
| 2 | `loss.backward()` **之后立即** `del` 中间量并 `torch.cuda.empty_cache()` | 及时释放，避免碎片 |
| 3 | 每 epoch 结束后 `empty_cache()` | 同上 |

**注意**：`DG*` 的**取值口径不变**（仍是 `_compute_dg_star_record` 在全验证集上的结果），
**只有 `∇DG*` 的估计样本数减少** —— 这属于估计成本的取舍，**不是口径变更**，须在文档里写明。

    python tools\_p46_fix_alpha_oom.py [--apply]
"""
from __future__ import annotations

import ast
import io
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "tools" / "_p21_alpha_trainer_based.py"

OLD = """            # ② ∇DG*：临时开梯度，对 val 上的 centroid gap 反向
            self.model.eval()
            self.model.zero_grad(set_to_none=True)
            imgs, txts = [], []
            with torch.enable_grad():
                for i, batch in enumerate(val_loader):
                    if i >= 8:
                        break"""

NEW = """            # ② ∇DG*：临时开梯度，对 val 上的 DG* 反向
            # **只取 2 批**：实测 8 批会在 8 GB 卡上 OOM（PyTorch 累计分配 21 GiB）——
            # 训练循环的图尚未释放，两者叠加超限。∇DG* 是期望的估计，
            # 2 批 × 64 = 128 样本足够；**DG* 轨迹本身仍由 _compute_dg_star_record
            # 在全验证集上单独测**（no_grad），故取值口径不变。
            self.model.eval()
            self.model.zero_grad(set_to_none=True)
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            imgs, txts = [], []
            with torch.enable_grad():
                for i, batch in enumerate(val_loader):
                    if i >= 2:
                        break"""

OLD2 = """                dg = ((I - T) ** 2).sum(dim=-1).mean()
                dg.backward()"""
NEW2 = """                dg = ((I - T) ** 2).sum(dim=-1).mean()
                dg.backward()
            # 及时释放图与嵌入，避免与训练循环的图叠加爆显存
            del imgs, txts, I, T"""

OLD3 = """            loss = tr._train_epoch(train_loader, opt, sched, ep)"""
NEW3 = """            loss = tr._train_epoch(train_loader, opt, sched, ep)
            if torch.cuda.is_available():
                torch.cuda.empty_cache()"""


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8").read()
    if "只取 2 批" in t and "避免与训练循环的图叠加爆显存" in t:
        print("  已修，跳过")
        return 0
    n = 0
    for old, new, tag in ((OLD, NEW, "梯度版批数 8→2 + 预清缓存"),
                          (OLD2, NEW2, "backward 后释放中间量"),
                          (OLD3, NEW3, "每 epoch 后清缓存")):
        c = t.count(old)
        print(f"  {'✅' if c == 1 else '⚠'} {tag}：命中 {c}")
        if c == 1:
            t = t.replace(old, new, 1)
            n += 1
    if n != 3:
        print("  ❌ 未全部命中")
        return 1
    ast.parse(t)
    if not apply:
        print("  （预演）")
        return 0
    io.open(F, "w", encoding="utf-8", newline="").write(t)
    t2 = io.open(F, encoding="utf-8").read()
    assert "只取 2 批" in t2 and "避免与训练循环的图叠加爆显存" in t2
    print("  ✅ 已修：梯度版 2 批、及时释放、每 epoch 清缓存")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
