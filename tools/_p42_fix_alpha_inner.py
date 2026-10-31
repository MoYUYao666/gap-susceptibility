# -*- coding: utf-8 -*-
r"""改 A 脚本：用**梯度钩子**取 `gL`，并修正一处会掩盖错误的写法（2026-10-08）。

## 两个改动

### ① 用钩子取训练梯度（替代在 epoch 外读 `p.grad`）

**实测根因**（`tools/_p40_diag_inner_nan.py`）：
`_train_epoch` 内 `optimizer.zero_grad()` 在每个优化步后清空梯度
→ epoch 之外读 `p.grad` 得到 **0/398 个非 None** → `gL` 为空。

**已加钩子**（`tools/_p41_train_grad_hook.py`）：`loss.backward()` 之后、
`zero_grad` 之前把梯度 clone 到 `self._last_train_grad`（**默认关闭**）。

### ② 修 `inner` 的打印缺陷（**它会掩盖真实故障**）

原写法：

```python
if r: inner_hist.append(r[0])
print(f"inner={inner_hist[-1] if inner_hist else float('nan'):+.3e}")
```

**当 `capture_inner` 持续返回 None 时，`inner_hist` 为空 → 打印 `nan`**
—— **把"取不到梯度"伪装成"算出了 nan"**，误导诊断方向。
**改为分别记录** `inner_hist` 与 `skip` 计数，并打印实际原因。

    python tools\_p42_fix_alpha_inner.py [--apply]
"""
from __future__ import annotations

import ast
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "tools" / "_p21_alpha_trainer_based.py"

OLD_G = """            # ① 训练梯度：取本 epoch 累积的 loss 梯度（用最后一个 batch 的 grad 作代表，
            #    与"每步梯度"同量级；若为 None 说明未产生梯度）
            gL = [p.grad.detach().clone() for p in params if p.grad is not None]
            if not gL:
                return None"""

NEW_G = """            # ① 训练梯度：**必须用钩子在 zero_grad 之前取**（见 _p40 的实测：
            #    _train_epoch 内每个优化步后都会 zero_grad，epoch 之外 p.grad 全为 None）。
            gL = getattr(self, "_last_train_grad", None)
            if gL is None or len(gL) == 0:
                return None"""

OLD_L = """        inner_hist, lr_hist, dg_hist = [], [], []
        for ep in range(1, epochs + 1):
            tr.current_epoch = ep
            loss = tr._train_epoch(train_loader, opt, sched, ep)
            lr_hist.append(opt.param_groups[0]["lr"])
            r = tr.capture_inner(val_loader)
            if r:
                inner_hist.append(r[0])
            rec = tr._compute_dg_star_record(val_loader, ep)
            dg_hist.append(rec.dg_star if hasattr(rec, "dg_star") else rec.get("dg_star"))
            print(f"     ep {ep:>2} loss={loss:.4f} lr={lr_hist[-1]:.2e} "
                  f"inner={inner_hist[-1] if inner_hist else float('nan'):+.3e} "
                  f"DG*={dg_hist[-1]:.4f}", flush=True)"""

NEW_L = """        inner_hist, lr_hist, dg_hist = [], [], []
        skipped = 0
        tr._capture_train_grad = True          # 开启梯度钩子（默认关闭）
        for ep in range(1, epochs + 1):
            tr.current_epoch = ep
            loss = tr._train_epoch(train_loader, opt, sched, ep)
            lr_hist.append(opt.param_groups[0]["lr"])
            r = tr.capture_inner(val_loader)
            if r is None:
                skipped += 1
                inner_txt = "无梯度(已跳过)"       # **不得把跳过伪装成 nan**
            else:
                inner_hist.append(r[0])
                inner_txt = f"{r[0]:+.3e}"
            rec = tr._compute_dg_star_record(val_loader, ep)
            dg_hist.append(rec.dg_star if hasattr(rec, "dg_star") else rec.get("dg_star"))
            print(f"     ep {ep:>2} loss={loss:.4f} lr={lr_hist[-1]:.2e} "
                  f"inner={inner_txt} DG*={dg_hist[-1]:.4f}", flush=True)
        if skipped:
            print(f"     ⚠ {skipped}/{epochs} 个 epoch 未取到训练梯度（inner 序列长度 "
                  f"{len(inner_hist)}）", flush=True)"""


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8").read()
    if "_last_train_grad" in t and "不得把跳过伪装成 nan" in t:
        print("  已改，跳过")
        return 0
    n = 0
    for old, new, tag in ((OLD_G, NEW_G, "取梯度改钩子"), (OLD_L, NEW_L, "打印不再伪装 nan")):
        c = t.count(old)
        print(f"  {'✅' if c == 1 else '⚠'} {tag}：命中 {c}")
        if c == 1:
            t = t.replace(old, new, 1)
            n += 1
    if n != 2:
        print("  ❌ 未全部命中")
        return 1
    ast.parse(t)
    if not apply:
        print("  （预演）")
        return 0
    io.open(F, "w", encoding="utf-8", newline="").write(t)
    t2 = io.open(F, encoding="utf-8").read()
    assert "_last_train_grad" in t2 and "不得把跳过伪装成 nan" in t2
    assert "_capture_train_grad = True" in t2
    print("  ✅ 已改：用钩子取 gL；打印区分「无梯度」与「nan」")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
