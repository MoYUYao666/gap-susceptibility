# -*- coding: utf-8 -*-
r"""落账：配置错标扫描（9 → 1，我判据的第一版有 8 处假阳性）（2026-10-13 11:05）。

    python tools\_p479_record_mislabel_scan.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **🔍 2026-10-13 11:05 —— 机器穷举"配置错标"（161 脚本）：**第一版判据 9 处 → 修正后 1 处**（我的 8 处假阳性）**
>
> ### 一、触发
>
> `p3-allocation` 修 `--lr` 后**自查出同类第三例**，并说 *"若无 `--lr`，传了也会被忽略、四个 tag 全跑 5e-5，
> 而文件名却写着 lr=1e-3 —— **比覆盖更隐蔽（错标）**"*。
> **我核它的修复**，发现**同一文件仍有残留**：`tools/_p434_alloc_train.py` **L345** 的**汇总归档**写 `"lr": LR`（**模块级常量**）。
>
> ### 二、机器穷举（我写的扫描器 `tools/_p478`）
>
> **第一版判据**：归档字段写模块级全大写常量，且同文件存在对应 `--<key>` 或 `args.<key>`。
> ⇒ **命中 9 处**：`_p434:345 "lr": LR` + **`_p464_qwen_ranksweep.py` 的 8 处 `MAX_PIX`/`MIN_PIX`**。
>
> **⚠️ 但那 8 处是**假阳性** —— 我核出 `_p464` **L191-192 有动态回写**：
> ```python
> # 命令行可覆盖像素预算（模块级常量被 qwen_inputs / protocol 引用）
> globals()["MIN_PIX"] = a.min_pixels
> globals()["MAX_PIX"] = a.max_pixels
> ```
> ⇒ 常量**被 CLI 覆盖** ⇒ 归档写的值与实际一致 ⇒ **不是 bug。**
> **⇒ 我的判据漏掉了"常量被动态覆盖"这一合法模式。**
>
> ### 三、修正判据（两步）后 ⇒ **全仓库只剩 1 处真错标**
>
> **判据**：① 归档字段 `"<key>": <CONST>` 且同文件有 `--<key>`/`args.<key>`；
> **② 且该 `CONST` 在文件中没有任何重新赋值**（`globals()["CONST"]=…` / `CONST = args…` / `CONST = a…`）。
>
> **逐项核 `LR`**：`globals()["LR"]` **0 命中**、`LR = args.lr` **0 命中**、`LR = a.lr` **0 命中**
> ⇒ **无常量回写 ⇒ 常量恒为 5e-5 ⇒ L345 在非默认 lr 下确实错标** 🔴
>
> **修正后结果**：`outputs/analysis/config_mislabel_scan2.json` ⇒ **1 处**（`_p434_alloc_train.py:345`）。
>
> ### 四、⭐ 危害分级（成员提出，我采纳并给判据）
>
> > **错标 > 覆盖 > 重写**
> > - **重写**：丢方案（"少了一个"）⇒ **可见**
> > - **覆盖**：丢数据（"少了一个"）⇒ **可见**
> > - **错标**：**所有产物都在、数字都真实，只是标签与内容不符** ⇒ **不可见**，任何下游推断都错
>
> **⇒ 已要求写进报告的"防御"段，并作为给另两个成员的通用提醒。**
>
> ### 五、⭐ 我推荐的自检（比扫描更硬，能挡住整类）
>
> **在写归档前，从**真实对象**回读配置并断言**：
> ```python
> _actual_lr = opt.param_groups[0]["lr"]        # 优化器实际用的
> assert _actual_lr == args.lr == rec["protocol"]["lr"], \\
>     f"[配置错标] optimizer={_actual_lr} args={args.lr} archive={rec['protocol']['lr']}"
> ```
> **⇒ 从优化器回读，能挡住所有"参数传了但没生效"的情形，且不依赖人去找哪一行。**
> **同理**：`max_pixels` 从 processor 回读、`epochs` 从训练循环计数回读。
> **⇒ 已要求成员把这条加进训练脚本模板。**
>
> ### 六、⚠️ 我提出的一个连带风险（要成员明确处理）
>
> 若那 8 个 run **在修 L345 之前**已跑完 ⇒ **它们的汇总归档仍带错误的 `lr: 5e-5`** ⇒
> **修完必须重跑汇总（或改写已落盘的汇总字段），否则归档自相矛盾**（文件名 `lr0.001` / 逐 run `1e-3` / 汇总 `5e-5`）。
> **已要求成员明确说明处理方式。**
>
> ### 七、本类缺陷已出现**三次**（全是靠人发现）
>
> | # | 缺陷 | 后果 | 发现者 |
> |---|---|---|---|
> | ① | `_p440` 重写 `<tag>/summary.json` | 静默丢掉 4 个规则方案 | `p3-allocation` 自查 |
> | ② | `_p451` 无 `--tag` | 两个 lr 写同一文件、后者覆盖前者 | `p3-allocation` 自查 |
> | ③ | `_p434` L345 写常量 `LR` | 汇总归档**错标** lr | **我核它的修复时发现** |
>
> **⇒ 结论：要减少一个"只能靠人"的环节。** 两条机器手段已提出：**扫描器（两步判据）+ 回读断言**。
>
> ### 八、状态
>
> - **P1 ✅（30）｜P2 ✅（6 seed / 57 run）｜P3 ✅（AdaLoRA + lr 扫描）**｜**Γ 侧对称 lr 扫描 8 run 进行中**
> - **P3 稿件**：**14 页** / 0 错 / 0 未定义；**累计修 24 处**
> - **PRL 硬约束**：**双栏 ≤7 页** ⇒ 待压缩 + 新建 Supplementary
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  （预演）")
        return 0
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "配置错标" in t and "8 处假阳性" in t:
        print("  已记录")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("配置错标", "8 处假阳性", "_p434_alloc_train.py:345", "错标 > 覆盖 > 重写", "param_groups[0]"):
        print(f"  {'✅' if k in t2 else '🔴'} {k}")
    print(f"  HANDOFF 行数 = {len(t2.splitlines())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
