# -*- coding: utf-8 -*-
r"""落账：A 脚本 CPU 预检通过 + 队列状态（2026-10-08 08:15）。

    python tools\_docs_a_preflight.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **✅ 2026-10-08 08:15 —— A 脚本 CPU 预检通过（上 GPU 前先验证，避免浪费）**
>
> 预检脚本：`tools/_p21_preflight_cpu.py`（**不落盘、不改结果**）
>
> | 预检项 | 结果 |
> |---|---|
> | `GapAwareTrainer.setup_model()`（cpu） | ✅ 48 个 LoRA 层、245,760 可训参数 |
> | dataloader | ✅ train=3 / val=1 批 |
> | `_compute_dg_star_record` 返回字段 | ✅ `['dg_star', 'cg', 'dg_empirical']`（`dg_star = 1.5199`） |
> | 前向返回字段 | ✅ `['image_embeds', 'text_embeds']` |
> | **`dg_star.backward()` 梯度路径** | ✅ **`‖∇DG*‖ = 19.4810`，349/397 张量非零** |
>
> **→ A 脚本可上 GPU。** 这一步的目的：本项目已因"没先验证就开跑"浪费过两次
> （样本量差 15 倍、动力学差 10 倍），**故新规矩：上 GPU 前先在 CPU 走通接口与梯度路径**。
>
> ### 队列状态（实测）
>
> ```
> [04:01:13] ▶ ③b both
> [06:15:13] ✅ ③b both rc=0 用时 134 min
> [06:15:14] ▶ ③b vision_only
> ```
>
> **`vision_only` 实测速度约 46 s/step，epoch 6/10**（32 步/epoch）→ **预计还需约 85 min**，
> 比我先前估的 18 min **慢 4.7 倍**（**估算再次偏乐观，此处如实修正**）。
>
> ### 待办（下一步动作明确）
>
> 1. **等 `vision_only` 完成** → **重启执行器**（当前实例加载的是旧队列，
>    不含新插入的 `CLIP B/32 @ rank 4` 同秩对照三臂）；
> 2. 重启后执行器将从第 4 项起跑：**同秩对照 CLIP B/32 r4（三臂）** → 然后 COCO 12 配置；
> 3. **A 实验**（`_p21_alpha_trainer_based.py`）也需 GPU —— **排在 COCO 之前**，
>    因为它回答的是论文中心论断（α 能否由梯度预测），而 COCO 补的是附表。
"""


def main() -> int:
    apply = "--apply" in sys.argv
    if not apply:
        print("  （预演）")
        return 0
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "A 脚本 CPU 预检通过" in t:
        print("  已记录，跳过")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("CPU 预检通过", "19.4810", "46 s/step", "慢 4.7 倍", "重启执行器"):
        assert k in t2, f"断言失败：缺 {k}"
    print(f"  ✅ HANDOFF 已追加（{len(t2.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
