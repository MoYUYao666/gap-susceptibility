# -*- coding: utf-8 -*-
r"""给 `_p21_alpha_trainer_based.py` 补 `train()` 会设置、而 `_train_epoch` 依赖的属性。

## 为什么要补

我**绕过训练的 `train()` 方法**自己走循环（为了每 epoch 插一次 `∇DG*` 反向），
因此 `train()` 里设置的属性不会就位。**实测报错**：

```
File "tools/_p21_alpha_trainer_based.py", line 167, in main
File "src/trainer.py", line 445, in _train_epoch
AttributeError: 'AlphaTrainer' object has no attribute '_trainable_params'
```

**`train()` 里设置**：`peft_method`、`missing_sim`、`_trainable_params`、`current_epoch`、
`_current_gap_delta`、`best_val_loss`。
**`_train_epoch` 用到**：`_collect_gradient_snapshot`、`_compute_gap_penalty`、`_trainable_params`、
`current_epoch`、`device`、`global_step`、`lora_layers`、`missing_sim`、`model`、`peft_method`、
`processor`、`train_cfg`。

→ 缺的是 **`_trainable_params` / `missing_sim` / `_current_gap_delta` / `best_val_loss`**。

## 先确认导入路径（不猜）

    python tools\_p27_fix_alpha_attrs.py [--apply]
"""
from __future__ import annotations

import ast
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "tools" / "_p21_alpha_trainer_based.py"


def find_imports() -> tuple[str, str]:
    t = io.open(REPO / "src" / "trainer.py", encoding="utf-8").read()
    gp = mm = None
    for ln in t.splitlines():
        s = ln.strip()
        if "get_peft_params" in s and ("import" in s):
            gp = s
        if "MissingModalitySimulator" in s and ("import" in s):
            mm = s
    return gp or "?", mm or "?"


OLD = """        tr = AlphaTrainer(cfg)
        tr.setup_model()
        tr.enable_dg_star_tracking()"""

NEW = """        tr = AlphaTrainer(cfg)
        tr.setup_model()
        tr.enable_dg_star_tracking()
        # **补齐 train() 会设置、而 _train_epoch 依赖的属性**——
        # 我绕过 train() 自走循环（为每 epoch 插一次 ∇DG* 反向），故这些不会自动就位。
        # 实测缺 _trainable_params 会报 AttributeError（src/trainer.py:445）。
        tr.peft_method = "lora"
        tr._trainable_params = [p for p in tr.model.parameters() if p.requires_grad]
        tr._current_gap_delta = 0.0
        tr.best_val_loss = float("inf")"""


def main() -> int:
    apply = "--apply" in sys.argv
    gp, mm = find_imports()
    print(f"  trainer.py 的导入：\n    {gp}\n    {mm}")
    t = io.open(F, encoding="utf-8").read()
    if "补齐 train() 会设置" in t:
        print("  已补，跳过")
        return 0
    if t.count(OLD) != 1:
        print(f"  未唯一命中（{t.count(OLD)}）")
        return 1
    if not apply:
        print("  （预演）")
        return 0
    t = t.replace(OLD, NEW, 1)
    ast.parse(t)
    io.open(F, "w", encoding="utf-8", newline="").write(t)
    t2 = io.open(F, encoding="utf-8").read()
    assert "tr._trainable_params" in t2 and "tr.best_val_loss" in t2
    print("  ✅ 已补 _trainable_params / _current_gap_delta / best_val_loss / peft_method")


def _unused() -> None:
    """`missing_sim` 的处理：`_train_epoch` 会用到它，但若为 None 则视为 identity。"""
    return None


if __name__ == "__main__":
    raise SystemExit(main())
