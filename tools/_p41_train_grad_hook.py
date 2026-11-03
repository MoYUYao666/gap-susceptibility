# -*- coding: utf-8 -*-
r"""给 `GapAwareTrainer._train_epoch` 加**最小侵入的梯度取值钩子**（2026-10-08）。

## 为什么

实验 A 的 `inner` 恒为 nan / 取不到值。**实测根因**（`tools/_p40_diag_inner_nan.py`）：

```
训练后 p.grad 状态：非 None 的 grad 张量: 0 / 398
```

**`_train_epoch` 在每个优化步后调用 `optimizer.zero_grad()`（`src/trainer.py:449`）**
→ 我在 epoch 之外读 `p.grad` 时**已被清空**。

**同时这也解释了为什么训练动力学无法通过改 lr 对齐**：
`lr` 扫描实测 **lr=1e-4 本来就 ✅ 已对齐**（跨度 0.0817，归档 0.1641），
我先前"需把 lr 减半"的结论是拿 **3 epoch 与归档 10 epoch** 比出来的，**口径不同，结论错误**。

## 修法（最小侵入）

在 `loss.backward()` 之后、`optimizer.zero_grad()` 之前，插入一次回调：

```python
self._last_train_grad = [p.grad.detach().clone() for p in self._trainable_params
                         if p.grad is not None]
```

- **不改动**损失、优化器、调度器、数据或任何控制流（只多一次 clone，成本极低）；
- **仅在显式开启时生效**（`self._capture_train_grad = True`），
  **默认关闭 → 对既有实验零影响**（这是本项目"改动用脚本 + 默认不变"的纪律）。

## 用法（在 A 脚本里）

```python
tr._capture_train_grad = True          # 开启
tr._train_epoch(...)                   # 跑一个 epoch
gL = tr._last_train_grad               # 该 epoch 最后一批的损失梯度
```

    python tools\_p41_train_grad_hook.py [--apply]
"""
from __future__ import annotations

import ast
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "src" / "trainer.py"

OLD = """            # 反向传播
            loss = loss / self.train_cfg.gradient_accumulation_steps
            loss.backward()

            if (n_batches + 1) % self.train_cfg.gradient_accumulation_steps == 0:"""

NEW = """            # 反向传播
            loss = loss / self.train_cfg.gradient_accumulation_steps
            loss.backward()

            # 梯度取值钩子：**必须在 zero_grad 之前**（否则 p.grad 已被清空，见
            # tools/_p40_diag_inner_nan.py 的实测）。默认关闭 → 对既有实验零影响。
            if getattr(self, "_capture_train_grad", False):
                self._last_train_grad = [
                    p.grad.detach().clone() for p in self._trainable_params
                    if p.grad is not None
                ]

            if (n_batches + 1) % self.train_cfg.gradient_accumulation_steps == 0:"""


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8").read()
    if "_capture_train_grad" in t:
        print("  已加，跳过")
        return 0
    if t.count(OLD) != 1:
        print(f"  ❌ 锚点未唯一命中（{t.count(OLD)}）")
        return 1
    if not apply:
        print("  （预演）")
        return 0
    t = t.replace(OLD, NEW, 1)
    ast.parse(t)
    io.open(F, "w", encoding="utf-8", newline="").write(t)
    t2 = io.open(F, encoding="utf-8").read()
    assert "_capture_train_grad" in t2 and "_last_train_grad" in t2
    # 确认钩子在 zero_grad 之前
    i_hook = t2.find("_capture_train_grad")
    i_zero = t2.find("optimizer.zero_grad()", t2.find("def _train_epoch"))
    assert i_hook < i_zero, "钩子不在 zero_grad 之前！"
    print("  ✅ 已加梯度钩子（位于 zero_grad 之前，默认关闭，对既有实验零影响）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
