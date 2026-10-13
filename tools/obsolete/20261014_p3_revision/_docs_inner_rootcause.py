# -*- coding: utf-8 -*-
r"""落账：`inner` 取不到的根因链（四层）与修复（2026-10-08 19:20）。

    python tools\_docs_inner_rootcause.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **🐛 2026-10-08 19:20 —— `inner` 恒为 nan 的**根因链（四层）**已逐层查出并修复**
>
> ### 四层根因（**每层都要单独实测才能看到下一层**）
>
> | 层 | 现象 | 根因 | 抓出方式 |
> |---|---|---|---|
> | **1** | 训练后 `p.grad` **全为 None**（0/398） | `_train_epoch` 内每个优化步后调用 `optimizer.zero_grad()`（`src/trainer.py:449`）→ **epoch 之外读不到梯度** | `tools/_p40_diag_inner_nan.py` |
> | **2** | 加了钩子仍取不到 | **`_trainable_params` 是 `None`**（trainer 只在 `train()` 里设置，而实验 A 为插 ∇DG* 反向自走循环、**从未调用 `train()`**）→ 钩子遍历空列表 | `tools/_p43_diag_hook.py` |
> | **3** | 改用 `model.parameters()` 后仍取不到 | **`gL`(398) 与 `gdg`(397) 非零个数不同**（某参数对 DG* 无梯度）→ 我的判据 `len(gL) != len(gdg)` **永远成立** → 永远返回 None | 在 `capture_inner` 内打印长度 |
> | **4** | 放开长度判据后抛 `TypeError` | `zip(gdg, gL)` 直接相乘，**遇 None 抛错**（两侧 None 占位处理不一致） | 运行报错栈 |
>
> ### 修复
>
> | 需求 | 做法 |
> |---|---|
> | 要在 `zero_grad` **之前**取梯度 | `src/trainer.py` 加**最小侵入钩子**：`loss.backward()` 后、`zero_grad` 前 clone 到 `self._last_train_grad`；**默认关闭**（`_capture_train_grad=False`）→ **对既有实验零影响** |
> | 与 `model.parameters()` 一一对应 | 钩子**保留 `None` 占位** |
> | 非零个数不同的配对 | **按位置配对、跳过任一为 None 的对**，并**如实打印**用了几对、跳过几个 |
>
> ### 一个被同步修掉的"掩盖故障"的写法
>
> 原打印：`inner={inner_hist[-1] if inner_hist else float('nan')}`
> —— 当 `capture_inner` 持续返回 None 时，`inner_hist` 为空 → **打印 `nan`**，
> **把"取不到梯度"伪装成"算出了 nan"**，把诊断引向数值溢出方向（我确实先怀疑过 bf16 溢出）。
> **已改为分别打印「无梯度(已跳过)」与真实值**，并在结尾报告跳过计数。
>
> ### 关于 lr：我先前的结论被自己的扫描推翻
>
> | lr | DG* 跨度（2000 样本 3 epoch） | 判定（对齐带 [0.066, 0.492]） |
> |---|---|---|
> | **1e-4** | **0.0817** | ✅ **已对齐** |
> | 5e-5 | 0.0319 | ❌ |
> | 2.5e-5 | 0.0193 | ❌ |
>
> **→ `lr=1e-4`（默认）本来就是对的。** 我先前"峰值 lr 约需减半"的说法，
> 是拿 **2000 样本 3 epoch** 与**归档 5000 样本 10 epoch** 比出来的——**口径不同，结论错误**。
>
> ### 现状
>
> **`inner` 已能取到**（实测：`用 397 对，跳过 1 个`，返回三元组），
> **完整实验 A（5000 样本 × 10 epoch, lr=1e-4）已启动**。
"""


def main() -> int:
    apply = "--apply" in sys.argv
    if not apply:
        print("  （预演）")
        return 0
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "根因链（四层）" in t:
        print("  已记录，跳过")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("根因链（四层）", "永远返回 None", "把\"取不到梯度\"伪装成\"算出了 nan\"",
              "我先前\"峰值 lr 约需减半\"的说法", "用 397 对，跳过 1 个"):
        assert k in t2, f"断言失败：缺 {k}"
    print(f"  ✅ HANDOFF 已追加（{len(t2.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
