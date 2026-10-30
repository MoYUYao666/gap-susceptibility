# -*- coding: utf-8 -*-
r"""把本阶段发现写入 `文件地图.md` 的"当前真正待办"（2026-10-08，阶段收尾规则）。

## 为什么

项目规则：**涉及"当前待办/状态"变化时必改 `文件地图.md`**（导航与待办的唯一入口）。
本阶段有三件影响待办的事，须落进去。

## 幂等

若已含标志句则跳过，可反复运行。

    python tools\_docs_update_map2.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "文件地图.md"
ANCHOR = "## 七、当前真正待办（按优先级）\n"
MARK = "0A. patch-size 规律被关键对照证伪"

ENT = """
### 🔴🔴 2026-10-08 新增最高优先级（唯一原则下的实证发现）

**0A. patch-size 规律被关键对照**证伪** → 论文 `empirical.tex` 必须改（**待操作者决定改法**）**

- **先说清**：论文**现有表格 12 个数字全部可复现**（`tools/_verify_position_table2.py`，复算失败 **0**、违反规律 **0**）——**论文没编造**。
- **问题**：新增的 **CLIP B/16**（严格冻结、rank 4、5000 样本，实测）
  **text_only −0.0190 / both +0.0150** → **最保护臂 = text_only**，
  而论文规律要求 patch-16 骨干应为 **both**。
- **为什么这条特别重**：CLIP B/16 是**唯一能把 patch size 与模型身份分开**的对照
  （同族 CLIP、同 WIT 预训练目标、仅 patch size 32→16）。
- **由证据浮现的假说**：两个 patch-16 骨干（SigLIP=WebLI/sigmoid、BioCLIP=生物域）**都不是 WIT**；
  唯一 WIT 的 patch-16 给出的是 patch-32 的排序 → **假说：排序跟的是预训练目标/语料，不是 patch size。**
- **决定性对照已入队**：`CLIP B/32 @ rank 4`（三臂）—— 排除"rank 4 本身导致 text_only 更保护"。
- **证据强度差异（须如实标注）**：CLIP/OpenCLIP/SigLIP 为**逐 run 可复算**；
  **BioCLIP 只有汇总**（`outputs/strict_freeze_bioclip/results_partial.json`，
  注明「rank 8 未完成」，由 `tools/_exp3_bioclip_harvest.py` 从运行日志解析落盘，**无逐 run `results.json`**）。
- **日志**：`outputs/_serial_executor.log`、`outputs/_handoff_executor.log`。

**0B. 实验 A（α 能否由梯度预测）—— 脚本就绪，已入队**

- 脚本 `tools/_p21_alpha_trainer_based.py`（**子类化 `GapAwareTrainer`**，复用其训练循环 → 动力学与归档一致）。
- **CPU 预检已通过**（`tools/_p21_preflight_cpu.py`）：`dg_star` 字段存在、`dg_star.backward()` 可用
  （梯度范数 19.48、349/397 张量非零）。
- **前两次失败原因（已记录）**：① 样本量 2000 vs 归档 5000（DG 星跨度差 15 倍）；
  ② **自行实现训练循环**（`final_step` 780 vs 归档 630、DG 星跨度 0.0159 vs 0.1641，差 10 倍）。
- **量名混淆已修正**：论文 ODE 拟合的是 **`dg_star`（配对均方距离）**，**不是** `cg`（质心间隙）；
  归档里两者跨度 **0.1641 vs 0.1149**。
- **判据（事先写明）**：`corr>0.7` 且 中位相对误差 `<35%` 且 比值 `∈[0.5,2]`。

**0C. COCO 逐配置补跑（操作者选①严格冻结）—— 36 h，可续跑**

- 原因：`supplement.tex` 的 COCO 表原 **15 行**，归档只支持 **3 配置 × 3 seed** → 我按原则删到 3 行；
  **操作者指示"可以把没有的补上，重跑"** → 用**严格冻结**补 12 配置 × 3 seed。
- 顺带修口径不一致：旧 COCO run 记 `n_trainable_params=145,170,177`，**不是严格冻结**。
- **脚本**：`tools/_p20_serial_executor.py` + `experiments/strict_freeze_control.py --dataset coco --data-dir .`。

**0D. 串行执行器（架构修复）—— 已完成**

- 昨夜三个驱动各看各的信号 → **必然撞车**（队列 2 在 ③b 未完成时启动 α 重跑，两实验争 8 GB 显存）。
- 已换 `tools/_p20_serial_executor.py`：单写者、超时 `killpg` 杀整组、日志逐行落盘、
  **等 GPU 而不跳过**、启动前按命令行查重。
- **教训（Windows 必守）**：`capture_output=True, text=True` **必须显式 `encoding="utf-8"`**——
  否则中文路径触发 `UnicodeDecodeError`，且异常被吞成空列表，**守卫静默失效**。

**0E. 可复现门禁 —— 已完成**

- 唯一原则已写入 `AGENTS.md`（最高优先级）：每个数字须**指名脚本 + 归档字段**；**无来源者一律删除**。
- **门禁**：`python tools\\_claim_ledger.py --apply` → **24/24 通过**。
- **我否掉了自己的假门禁** `tools/_reproducibility_gate.py`：它用 0.5% 容差在 **122,161 个归档数值**里模糊匹配
  → **145/145 "通过"纯属假象**。**自动模糊匹配不算验证。**

"""


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8").read()
    if MARK in t:
        print("  已更新，跳过")
        return 0
    if t.count(ANCHOR) != 1:
        print(f"  未唯一命中锚点（{t.count(ANCHOR)}）")
        return 1
    if not apply:
        print("  （预演）")
        return 0
    t2 = t.replace(ANCHOR, ANCHOR + ENT, 1)
    io.open(F, "w", encoding="utf-8", newline="").write(t2)
    t3 = io.open(F, encoding="utf-8").read()
    for k in (MARK, "0.1641 vs 0.1149", "24/24 通过", "UnicodeDecodeError",
              "自动模糊匹配不算验证"):
        assert k in t3, f"断言失败：缺 {k}"
    print(f"  ✅ 文件地图.md 已更新（{len(t3.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
