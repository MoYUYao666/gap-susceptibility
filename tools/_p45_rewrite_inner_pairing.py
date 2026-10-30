# -*- coding: utf-8 -*-
r"""重写 A 脚本 `capture_inner` 的配对段（2026-10-08）。

## 问题

`gL`（训练梯度）与 `gdg`（∇DG*）**非零个数不同**（实测 398 vs 397：
某些参数对 DG* 无梯度）→ 原判据 `len(gL) != len(gdg)` **永远成立** → 永远返回 None。

且两侧的 `None`（无梯度）处理不一致：
- 钩子：`[g if g is not None else None for p in ... if p.requires_grad]`（**有占位，长度 = 可训数**）
- `gdg`：`[g if g is not None else None for p in params]`（**有占位，长度 = params**）
- 旧 `inner`：`zip(gdg, gL)` 直接相乘 → **遇 None 抛 TypeError**

## 修法（一处改清）

**用位置配对 + 跳过任一为 None 的对**，并统计实际可用对数与跳过数（**不静默**）。

    python tools\_p45_rewrite_inner_pairing.py [--apply]
"""
from __future__ import annotations

import ast
import io
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "tools" / "_p21_alpha_trainer_based.py"

NEW_BLOCK = '''            gdg = [(p.grad.detach().clone() if p.grad is not None else None) for p in params]
            self.model.zero_grad(set_to_none=True)
            # **按位置配对，跳过任一为 None 的对**：训练梯度与 ∇DG* 的非零个数不同
            # （实测 398 vs 397），故不能用"长度相等"做判据——那会永远返回 None。
            pairs, skipped_none = [], 0
            for a, b in zip(gdg, gL):
                if a is None or b is None:
                    skipped_none += 1
                    continue
                pairs.append((a, b))
            if not pairs:
                print(f"     [capture_inner] 无可用配对（gdg 非零 "
                      f"{sum(1 for x in gdg if x is not None)} / gL 非零 "
                      f"{sum(1 for x in gL if x is not None)}）", flush=True)
                return None
            if skipped_none:
                print(f"     [capture_inner] 用 {len(pairs)} 对，跳过 {skipped_none} 个"
                      f"（任一侧无梯度）", flush=True)
            inner = float(sum((a * b).sum() for a, b in pairs))
            nL = float(sum(a.pow(2).sum() for a, _ in pairs)) ** 0.5
            nD = float(sum(b.pow(2).sum() for _, b in pairs)) ** 0.5
            self.model.train()
            return inner, nL, nD'''

# 用正则替换从 "gdg = [" 到 "return inner, nL, nD"
PAT = re.compile(
    r"            gdg = \[.*?return inner, nL, nD",
    re.S)


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8").read()
    if "用位置配对，跳过任一为 None 的对" in t:
        print("  已改，跳过")
        return 0
    m = PAT.search(t)
    if not m:
        print("  ❌ 未找到待替换段")
        return 1
    print(f"  找到待替换段（{len(m.group(0))} 字符）")
    t = t[:m.start()] + NEW_BLOCK + t[m.end():]
    ast.parse(t)
    if not apply:
        print("  （预演）")
        return 0
    io.open(F, "w", encoding="utf-8", newline="").write(t)
    t2 = io.open(F, encoding="utf-8").read()
    assert "用位置配对，跳过任一为 None 的对" in t2
    assert "len(gL) != len(gdg)" not in t2, "旧判据仍在"
    print("  ✅ 已重写配对段：按位置配对、跳过 None、如实统计")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
