# -*- coding: utf-8 -*-
r"""更新门禁台账：**删除已撤回的 COCO ODE 主张**（2026-10-08）。

## 为什么

`tab:coco_ode` 与其 3 行数字（`0.897` / `0.910` / `0.966`）**已按 ③+① 从正文删除**
（实测：这三个值已不在任何 `.tex` 里）。

但台账 `tools/_claim_ledger.py` 仍在断言它们（L123 起），
**过期的台账条目会让日后复核的人以为那些表还在**——**台账必须与正文同步**。

## 改法

把该段替换为**一条说明性注释**，记录数字的去向与原因，但**不再断言**。

    python tools\_pa_ledger_drop_coco.py [--apply]
"""
from __future__ import annotations

import ast
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "tools" / "_claim_ledger.py"

OLD = '''    # ── ④ COCO 三配置（改表后的值）
    coco = [r for r in runs if r["top"] == "coco"]
    for conf, want in (("coco_text_r8", 0.897), ("coco_both_r8", 0.910), ("coco_full_ft", 0.966)):
        sel = [r for r in coco if r["conf"].endswith(conf)]
        claim(f"COCO {conf} R²", want, st.mean(x["R2"] for x in sel),
              f"ode_ledger.json:runs({conf})")'''

NEW = '''    # ── ④ COCO ODE 主张：**已于 2026-10-08 撤回**（操作者选 ③+①）
    #
    # 原断言（coco_text_r8=0.897 / coco_both_r8=0.910 / coco_full_ft=0.966）随
    # supplement 的 `tab:coco_ode` 一并删除。原因：那些系数拟合自**非严格冻结**的 run
    # （n_trainable=145,170,177），而严格冻结下 MS-COCO 的 DG* 几乎不动
    # （跨度 0.003–0.006，拟合 R² 0.12/0.68；同 run 的 CG R² 为 0.93）。
    # 论文明说不再为 MS-COCO 报告 ODE 系数，故此处**不再断言任何数字**。
    # 证据：tools/_p39_verify_dgstar_failure.py；HANDOFF 2026-10-08「DG* 框架失效」条。'''


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8").read()
    if "COCO ODE 主张：**已于 2026-10-08 撤回**" in t:
        print("  已改，跳过")
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
    assert "COCO ODE 主张：**已于 2026-10-08 撤回**" in t2
    assert "coco_full_ft\", 0.966" not in t2, "旧断言仍在"
    print("  ✅ 台账已同步：COCO ODE 的 3 条断言移除，改为说明性注释")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
