# -*- coding: utf-8 -*-
r"""Record the COCO convergence investigation in the handoff.

    python tools/_p768_record_convergence.py --apply"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **🧪 2026-10-15 08:30 —— COCO 微调排查：**LoRA 在 COCO 上不是欠训练，是训练失败；错在我把学习率放大**（附三项实测）**
>
> ### 一、起点
>
> 上一轮结论是"LoRA 在 COCO 上不收敛，根因未查完"。本轮把它查清。
>
> ### 二、✅ 先排除三个嫌疑
>
> | 嫌疑 | 检验 | 结论 |
> |---|---|---|
> | **代码没在学** | 200 图、60 步、**全量微调 lr=1e-5**：loss **0.876 → 0.246** | ❌ 数据与损失都正常（能过拟合） |
> | | 只训 **projection** lr=1e-3：**0.915 → 0.733** | ❌ |
> | | 只训 **`logit_scale`** lr=1e-2：0.72 → 0.89（首步即低） | ❌ |
> | **LoRA 没接进 forward** | 注入后扰动 adapter：文本嵌入变化 **>1e-6**；48 个 `lora_*` 张量均 `requires_grad=True` | ❌ 接线正常 |
> | **设备不匹配** | trainer 的 LoRA 参数设备 = **`cuda:0`**，model 设备 = **`cuda:0`** | ❌ 顺序正确（**注入后才 `.to(device)`**）|
>
> **⚠️ 我自己的测试脚本一度顺序写反**（先 `.to(cuda)` 再注入 LoRA）⇒ 报 `Expected all tensors to be on the same device`。**那是我的脚本问题，不是 trainer 的问题** —— 已更正，不得把它算作项目缺陷。
>
> ### 三、🔴 实测：**LoRA 在 2,000 图 COCO 上把检索从 0.48 打到 0.007**
>
> **学习率扫描**（2,000 训练图 / 4 epoch / batch 64 / rank 8 / text-only；**修正协议**，500 图 gallery）：
>
> | lr | train loss | val loss | 修正 R@1 |
> |---|---|---|---|
> | **1e-4** | 4.01 → 2.45 | 3.53 → **4.95 ↑** | **0.0070** |
> | **3e-4** | 4.17 → **4.15（锁死）** | **3.4465 恒定** | **0.0050** |
> | **1e-3** | 4.20 → **4.15（锁死）** | **3.4465 恒定** | **0.0040** |
>
> **冻结基线（同 gallery）**：**i2t R@1 = 0.4755**、**t2i = 0.2857**。
>
> **⇒ 三点结论**：
> 1. **lr 越大越糟**：3e-4 / 1e-3 下 loss 锁死在 4.15、val 恒为 **3.4465 = log(64) = 无信息** ⇒ **模型退化到"什么都不学"**（与直觉相反，值得记录）；
> 2. **lr=1e-4 是过拟合**：train 降、val 升，而不是收敛；
> 3. **微调后的检索（0.007）远低于冻结（0.4755）** ⇒ **这套 COCO 微调配置产不出可用的检索结果**。
>
> ### 四、这意味着什么（对 Paper A 的直接影响）
>
> | 稿件内容 | 受影响程度 |
> |---|---|
> | COCO 的 `R@1 < 0.001`（"near-random"） | 🔴 **不是模型性质，是这套配置的产物**；冻结基线本身就有 0.4755 |
> | "COCO cross-dataset validation" 的规模主张 | 🔴 实际 **~2,000 唯一图**（`max_samples=10000` 是 caption 行数） |
> | train/val 同源 | 🔴 旧 `create_dataloaders()` 对 COCO 两个 loader 传同一 `split` |
> | 检索协议 | ✅ 已修（`src/trainer.py`）+ 逐例验证（`tools/_p760`） |
>
> ### 五、⏸ 为什么**没有**直接启动 10,000 图大跑
>
> 训练吞吐实测 **~65 s / 1,000 图 / epoch**；10,000 图 × 3 epoch × 5 seed × 2 arm ≈ **5.4 小时**。
> **但当前配置下跑 10,000 图只会产出又一批 R@1≈0.005 的坏数**（lr 扫描已证明），
> **所以必须先解决"为何微调在 COCO 上失败"，再跑规模。**
>
> ### 六、进行中
>
> `tools/_p767_arm_compare.py`：同数据同预算下对比 **`full_ft`（全量微调）** 与 **`lora`**，
> 以判定"失败是 COCO 训练通病"还是"LoRA 专属"。**结果出来后据此决定下一步。**
>
> **⚠️ 诚实标注**：本轮**没有产出任何可写进稿件的数字**，产出的是**对现有 COCO 结果的否证**。
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  (dry run)")
        return 0
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "COCO 微调排查" in t:
        print("  already recorded")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("COCO 微调排查", "0.0070", "3.4465", "0.4755", "5.4 小时", "我自己的测试脚本"):
        print(f"  {'OK ' if k in t2 else 'BAD'} {k}")
    print(f"  HANDOFF lines = {len(t2.splitlines())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
