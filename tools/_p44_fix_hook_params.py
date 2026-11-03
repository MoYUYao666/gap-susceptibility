# -*- coding: utf-8 -*-
r"""修钩子：遍历 `model.parameters()` 而非 `_trainable_params`（2026-10-08）。

## 实测根因（`tools/_p43_diag_hook.py`）

```
_trainable_params: NoneType ｜ 长度 0
全模型可训张量: 398
backward 后：全模型有 grad 398 ｜ 可训张量中 398/398 ｜ _trainable_params 中 0/0
```

**`_trainable_params` 是 `None`** —— trainer 只在 `train()` 里设置它，
而**实验 A 从未调用 `train()`**（为每 epoch 插一次 ∇DG* 反向而自走循环，
但用的是 `_train_epoch`）→ 该属性一直未初始化 →
**钩子遍历空列表 → `_last_train_grad` 是空列表 → `inner` 取不到值**。

**→ 改用 `[p for p in self.model.parameters() if p.requires_grad]`**，
与 `tools/_p43` 实测的 398 个真正可训张量一致。

    python tools\_p44_fix_hook_params.py [--apply]
"""
from __future__ import annotations

import ast
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "src" / "trainer.py"

OLD = """            if getattr(self, "_capture_train_grad", False):
                self._last_train_grad = [
                    p.grad.detach().clone() for p in self._trainable_params
                    if p.grad is not None
                ]"""

NEW = """            if getattr(self, "_capture_train_grad", False):
                # **必须用 model.parameters()**：`_trainable_params` 只在 train() 里设置，
                # 而调用方（实验 A）为插 ∇DG* 反向而自走循环、从未调用 train()
                # → 该属性为 None → 遍历空列表 → 取不到任何梯度（实测，见 tools/_p43）。
                self._last_train_grad = [
                    p.grad.detach().clone() for p in self.model.parameters()
                    if p.requires_grad and p.grad is not None
                ]"""


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8").read()
    if "必须用 model.parameters()" in t:
        print("  已修，跳过")
        return 0
    if t.count(OLD) != 1:
        print(f"  ❌ 未唯一命中（{t.count(OLD)}）")
        return 1
    if not apply:
        print("  （预演）")
        return 0
    t = t.replace(OLD, NEW, 1)
    ast.parse(t)
    io.open(F, "w", encoding="utf-8", newline="").write(t)
    t2 = io.open(F, encoding="utf-8").read()
    assert "必须用 model.parameters()" in t2
    print("  ✅ 钩子已改用 model.parameters()")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
