# -*- coding: utf-8 -*-
r"""Record the two code fixes and the rerun.

    python tools/_p785_record_fixes.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **🔧 2026-10-15 15:30 —— 两处代码修复完成并验证：**LoRA 真正冻结基座** + **checkpoint 完整可复现****
>
> ### 一、修复 1：`src/lora.py :: apply_lora_to_model` —— 冻结非 LoRA 参数
>
> **改动**：注入完成后遍历 `model.named_parameters()`：名字含 `lora_` ⇒ `requires_grad_(True)`，否则 `requires_grad_(False)`；
> 并**断言**可训练参数总数等于 LoRA 参数总数，不等则 `RuntimeError`（防止此类缺陷再现）。
>
> **验证（实测）**：
>
> | 配置 | 修复前可训练参数 | **修复后可训练参数** |
> |---|---|---|
> | `text_only`（rank 8，文本塔） | 145,170,177（95.84%） | **196,608（0.13%）** ✅ |
> | `both`（rank 8，双塔） | — | **491,520（0.32%）** ✅ |
>
> ### 二、修复 2：`src/trainer.py :: _save_checkpoint` —— 保存全部可训练状态
>
> **原因**：旧版只存 `lora_state_dict`，注释假设"其余已冻结"；而基座并未冻结
> ⇒ **一次动了 1.45 亿参数的训练，checkpoint 只留了 19.6 万** ⇒ **微调后模型无法从自己的 checkpoint 恢复**。
>
> **改动**：新增 `trainable_state_dict`（按 `named_parameters()` 收集所有 `requires_grad` 张量）、
> `trainable_param_names`、`n_trainable_params`；**保留 `lora_state_dict` 以兼容旧分析脚本**。
>
> **验证（端到端，实测）**：
>
> ```
> 可训练参数: 196,608         ← 只有 LoRA
> 训练后评测: R@1=0.5212  i2t=0.6725
> checkpoint 键: [..., 'trainable_state_dict', 'trainable_param_names', 'n_trainable_params', ...]
> n_trainable_params 记录: 196,608
> 加载 48/48 个张量
> 加载后评测: R@1=0.5212  i2t=0.6725     ← 与训练后完全一致 ✅
> ```
>
> ### 三、✅ 已启动重跑（真 LoRA）
>
> - 旧结果（用"未冻结"的错误 LoRA 得到）已归档到
>   **`outputs/_scaleup_coco_LOORA_NOT_FROZEN/`** 与 **`outputs/analysis/_coco_scaleup_LOORA_NOT_FROZEN.json`**
>   —— **不删除**，作为"缺陷版 vs 修复版"的对照证据；
> - 新跑：**10,000 训练图 / 3,000 评测图 / 3 epoch / 3 seed / 2 arm + frozen**，配置与之前一致，
>   **唯一差别是 LoRA 现在真正只训适配器**；
> - 启动日志已确认：`可训练参数合计: 196,608 (LoRA only)`。
>
> **预计约 2.8 小时**（6 个 run）。
>
> ### 四、⚠️ 一个需要留意的初步信号
>
> 端到端验证时的小规模试验（200 训练图 / 1 epoch / 400 图 gallery）：
> **真 LoRA 微调后 R@1 = 0.5212、i2t = 0.6725**，
> 而**同 gallery 的冻结基线** i2t = **0.4203**（3,000 图 gallery 的测量）。
> **⚠️ gallery 不同（400 vs 3,000），两者不可直接比较** —— 此处只作"修复后在学"的证据，
> **正式对比要等重跑结果。**
>
> ### 五、待办
>
> | # | 事项 | 状态 |
> |---|---|---|
> | 1 | `apply_lora_to_model` 冻结基座 | ✅ 已完成并验证 |
> | 2 | `_save_checkpoint` 完整保存 | ✅ 已完成并验证 |
> | 3 | 重跑规模实验（真 LoRA） | ⏳ 运行中（PID 15612）|
> | 4 | **重评并重写受影响的结论**（Paper A / P3 中所有"LoRA"字样） | ⏳ 待 3 完成 |
> | 5 | **同步修复到 P3 的 `publish_clean` 与发布库** | ⏳ 待操作者确认（涉及已投论文） |
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
    if "两处代码修复完成并验证" in t:
        print("  already recorded")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("两处代码修复完成并验证", "196,608", "491,520", "trainable_state_dict",
              "LOORA_NOT_FROZEN", "0.5212"):
        print(f"  {'OK ' if k in t2 else 'BAD'} {k}")
    print(f"  HANDOFF lines = {len(t2.splitlines())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
