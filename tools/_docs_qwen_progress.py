# -*- coding: utf-8 -*-
r"""落账：实验 ④（Qwen2-VL 三臂）已启动并完成第一臂（2026-10-08 20:45）。

    python tools\_docs_qwen_progress.py [--apply]
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
D = REPO / "outputs" / "vlm_strictfreeze" / "text_only_seed42.json"


def main() -> int:
    apply = "--apply" in sys.argv
    if not apply:
        print("  （预演）")
        return 0
    d = json.loads(io.open(D, encoding="utf-8").read())
    dg = ", ".join(f"{x:.4f}" for x in d["dg_star"])
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "实验 ④（Qwen2-VL 三臂）已启动" in t:
        print("  已记录，跳过")
        return 0
    ent = f"""> **🧪 2026-10-08 20:45 —— 实验 ④（Qwen2-VL 三臂）已启动，第一臂完成**
>
> ### 目的：补论文自认的最大 scope 缺口
>
> `discussion.tex`：*"our study is limited to contrastive dual-encoder architectures;
> whether the framework generalizes to decoder-based VLMs … remains open"*
> —— 而摘要称验证跨"five architectures"，**那五个都是双塔编码器**。
>
> ### 脚本与口径
>
> **`tools/_p47_qwen_train.py`**（新写，含训练循环 + 逐 epoch `DG*`/`CG` 记录）
>
> | 项 | 值 |
> |---|---|
> | 模型 | Qwen2-VL-2B-Instruct（4.13 GB，bf16，8 GB 卡可跑，**未用量化**） |
> | 严格冻结 | 仅放开 LoRA A/B；**分塔由 `_p4_verify_tower_split.py` CPU 实测验证** |
> | rank / α | 8 / 16 ｜ lr 1e-4 ｜ AdamW ｜ cosine |
> | 规模 | **1000 样本 × 5 epoch，batch 4**（200 批/epoch） |
> | 测量 | **`DG*` = 配对均方距离**（与 ODE 状态变量同量）｜`CG` = 质心距离 |
> | 嵌入 | 两塔**最后一层隐状态的均值池化** → **固定随机投影到 512 维**（seed=0，不训练，跨臂同投影 → 可比） |
>
> **注意**：Qwen2-VL 的嵌入**无训练过的投影头**，故 `DG*` **绝对值**与 CLIP 不可比
> （实测 2.17 vs CLIP 的 1.2–1.5）；**本实验只比较三臂的逐 epoch 变化**。
>
> ### ✅ 冒烟已通过（16 样本 1 epoch，8.3s）——链路与显存均验证
>
> ### ✅ 第一臂完成：`text_only`（722.5s = 12 min）
>
> | epoch | 1 | 2 | 3 | 4 | 5 |
> |---|---|---|---|---|---|
> | **DG\\*** | **0.0964** | 0.0493 | 0.0354 | 0.0275 | **0.0262** |
> | CG | 0.1073 | 0.0580 | 0.0400 | 0.0276 | 0.0243 |
> | loss | 1.0687 | 0.8369 | 0.7765 | 0.7335 | 0.7131 |
>
> **`DG*` 跨度 0.0703** —— 呈**清晰的指数衰减形状**（正是 ODE 能拟合的形态），
> 与 **COCO 严格冻结下 `DG*` 几乎不动（跨度 0.003–0.006）形成鲜明对比**。
>
> **严格冻结校验**：`n_trainable = 9,232,384`，**视觉侧 0 个** LoRA 张量 ✅
>
> ### ⏳ 进行中
>
> `vision_only`（`n_trainable = 5,262,528`，**视觉 258 / 语言 0** ✅ 分塔正确）→ 之后 `both`。
> **预计三臂共约 40 min。**
"""

    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ent + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("实验 ④（Qwen2-VL 三臂）已启动", dg.split(",")[0].strip()[:6],
              "9,232,384", "5,262,528", "指数衰减形状"):
        assert k in t2, f"断言失败：缺 {k}"
    print(f"  ✅ HANDOFF 已追加（{len(t2.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
