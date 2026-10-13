# -*- coding: utf-8 -*-
r"""落账：按"可以把没有的补上，重跑"制定补齐计划（2026-10-07 深夜）。

    python tools\_docs_refill.py [--apply]
"""
from __future__ import annotations

import io
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def main() -> int:
    apply = "--apply" in sys.argv
    if not apply:
        print("  （预演）")
        return 0
    gpu = subprocess.run(["nvidia-smi", "--query-gpu=memory.used,utilization.gpu",
                          "--format=csv,noheader"], capture_output=True, text=True).stdout.strip()
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "补齐计划：重跑而非删表" in t:
        print("  已记录，跳过")
        return 0
    ent = f"""> **🔁 2026-10-07 深夜 —— 操作者指示"可以把没有的补上，重跑" → 补齐计划**
>
> ### 这条指示**修正了我上一轮的做法**
>
> 我按唯一原则把 `supplement.tex` 的 COCO 表**从 15 行删到 3 行**（因归档只支持 3 个配置）。
> **操作者的意思更对**：**删是因为"没来源"；重跑就能有来源 → 数据应回到论文，且这次可复现。**
>
> ### 三项要补的（按优先级）
>
> | # | 缺什么 | 归档现状 | 补齐方式 | 成本 |
> |---|---|---|---|---|
> | **B** | **α 预测**（首跑因样本量差 15 倍而无效） | 无效结果（已备份） | **`max_samples=5000`**（与归档同口径）重跑，seeds 42/123 | **≈2 h** |
> | **A** | **COCO 逐配置 ODE 表**（删剩 3 行） | 3 配置 × 3 seed | **12 配置 × 3 seed**（r∈{{1,2,4,16,32,64}} × {{text,both}}） | **≈15 h** |
> | **C** | **解码器 VLM 对照**（`discussion` 自认的 scope 缺口） | 无 | 写 Qwen2-VL 三臂脚本 + 跑 | 3–4 h |
>
> ### ✅ 好消息：**COCO 数据完整在本地**，无需下载
>
> `coco/train2014`（**82,783 张**）+ `coco/val2014`（**40,504 张**）+ `coco/annotations/`
> —— `src/dataset.py:209` 的 `COCODataset` 直接支持，只是路径在**根目录 `coco/`**（非 `data/coco/`）。
>
> ### ⚠️ 一处口径差异（须先定）
>
> 归档的 COCO run 记 `n_trainable_params = 145,170,177` → **不是严格冻结**
> （严格冻结 rank-8 应约 491,520）。而本组新实验用**严格冻结**。
> **→ 补跑时须二选一**：① 沿用严格冻结（与本文其它严格冻结结果一致，但与旧 COCO 数字口径不同）；
> ② 复刻旧口径（与旧表可比，但非严格冻结）。**待定。**
>
> ### 🌙 队列（GPU 串行）
>
> | 队列 | 内容 | 状态 |
> |---|---|---|
> | 队列 1（`_p7`） | α 首跑 → ③a OpenCLIP ✅ → **③b CLIP B/16** ⏳ | 运行中 |
> | **队列 2（`_p11`）** | **等 ③b → α 重跑（5000 样本）** | ✅ 已启动 |
>
> **当前 GPU**：{gpu}
>
> ### 队列 2 的实现细节
>
> - **等 ③b 三臂各出 `results.json`** 才启动（不靠 sleep 猜时间）；
> - **首跑结果先备份**为 `alpha_from_gradients_maxsamp2000.json`（**保留证据，不覆盖**）；
> - **判据与首跑一致**（事先写明）：corr > 0.7 且 中位相对误差 < 35% 且 比值 ∈ [0.5, 2]。
"""
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ent + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("可以把没有的补上", "82,783", "145,170,177", "队列 2", "maxsamp2000"):
        assert k in t2, f"断言失败：缺 {k}"
    print(f"  ✅ HANDOFF 已追加（{len(t2.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
