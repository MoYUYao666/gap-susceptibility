# -*- coding: utf-8 -*-
r"""落账：A1 重定位完成（标题 + 摘要）+ `paper合` 两处否证入库（2026-10-10）。

    python tools\_docs_a1_reframe.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **✍️ 2026-10-10 —— A1 重定位完成（操作者选 A）；`paper合` 两处理论否证入库**
>
> ### 一、A1：把"零开销监控器"提到最前
>
> **改前的标题**（否定式）：
> > *The Modality Gap Is **Not** a Universal Health Metric: Order Preservation Governs Zero-Shot Robustness*
>
> **改后**：
> > **Order Preservation as a Zero-Overhead Monitor for Classification Fine-Tuning:
> > Why the Modality Gap Is Not a Universal Health Metric**
>
> **摘要首段重写**（把已埋在正文里的卖点提上来）：
> > *"Classification fine-tuning of a contrastive vision--language model moves the modality gap
> > and erodes class-relative rank order together. **Only the second governs zero-shot accuracy,
> > and it is free to monitor**: the Kendall order-preservation coefficient $\\tau$ follows from
> > the top-$k$ class sets a validation pass already produces."*
>
> ### 二、摘要**词数**（目标刊 ESWA/KBS/CVIU 均限 **250**）
>
> | 阶段 | 标准口径词数 |
> |---|---|
> | 原摘要 | 247（贴上限） |
> | 我改写后 | **317（超 67）** |
> | 逐轮压缩后 | **245** ✅ |
>
> **三种口径全部达标**：字面 215 ｜ 标准 **245** ｜ 数学式整体算 1 词 235。
> **压缩只删散文冗余，未动任何数字**；删掉的"(fourteen LoRA, three full-fine-tuning)"
> **在正文保留**（已脚本核对）✅
>
> ### 三、**保留声明逐字未动**（这是"更克制"的资产）
>
> | 声明 | 状态 |
> |---|---|
> | *"order preservation is **necessary, not sufficient**"* | ✅ |
> | *"a **self-consistency check** of the closed form, **not independent validation**"* | ✅ |
> | *"we claim this for **no other families**, benchmarks or mechanisms"* | ✅ |
> | 全部数字（0.82→0.01、59.3%→32.0%、+0.033/+0.114、r=1.000、59.3%→78.6%、0.615/0.761） | ✅ 逐字保留 |
>
> ### 四、编译
>
> | 稿 | 页数 | 错误 | 未定义 | Overfull |
> |---|---|---|---|---|
> | **A1**（`paper_a1/main.tex`） | **40** | 0 | 0 | 0 |
> | `paper合` Springer | **40** | 0 | 0 | 0 |
> | `paper合` NC | **54** | 0 | 0 | 0 |
>
> ### 五、`paper合`：两处**理论否证**已写入 limitation（本会话第 1 步）
>
> | 新条目 | 内容 |
> |---|---|
> | **Seventh** | `f(DG₀)` 的**绝对标定失败**：实测 $+66.7\\pm4.8$ vs 归档 $\\alpha$ 蕴含的 $-27.7$，**符号相反、差 2.4 倍**，且非采样噪声（se=4.8）。**但同号率 6/6、中位相对误差 34%** → 相对次序可预测，绝对标定不行 |
> | **Eighth** | 驱动项**排序不成立**：轨迹平均 $+10.8/+10.2/+9.2$（极差 **16.5%**）vs 实测 CGΔ 极差 **277%**，且排序不同 → **只预测对最好的那个位置** |
>
> **原 Seventh（轨迹为子集）顺延为 Ninth。** 序号 First→Ninth 无重复 ✅
> **门禁：55/55 通过**（新增 8 条主张）✅
>
> ### 六、GPU 任务（并行进行中）
>
> **COCO `text_only` 补跑 11 run**（r2 缺 2 + r8/r32/r64 各 3）→ 让"数据集翻转"那张表两臂齐备。
> 输出 `outputs/coco_sweep_text_only/`（**不覆盖旧 sweep**）｜`--batch-size 64`（共享显存约束，已记录）。
"""


def main() -> int:
    apply = "--apply" in sys.argv
    if not apply:
        print("  （预演）")
        return 0
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "A1 重定位完成（操作者选 A）" in t:
        print("  已记录，跳过")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("A1 重定位完成（操作者选 A）", "Zero-Overhead Monitor", "245", "necessary, not sufficient",
              "Seventh", "Eighth", "55/55 通过", "COCO `text_only` 补跑 11 run"):
        assert k in t2, f"断言失败：缺 {k}"
    print(f"  ✅ HANDOFF 已追加（{len(t2.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
