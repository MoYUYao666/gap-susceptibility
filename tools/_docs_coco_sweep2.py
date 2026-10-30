# -*- coding: utf-8 -*-
r"""落账：COCO 补跑就绪（重跑版，2026-10-07 深夜）。

第一版因 f-string 内嵌中文导致断言失败。本版**不用 f-string 拼中文**，改为纯字符串 + 事后格式化。

    python tools\_docs_coco_sweep2.py [--apply]
"""
from __future__ import annotations

import io
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **🧪 2026-10-07 深夜 —— COCO 补跑就绪（操作者选①严格冻结）｜三队列串行等待**
>
> ### 操作者决定：**① 沿用严格冻结**补跑 COCO
>
> 本文的**核心证据就是严格冻结**（*"the optimiser sees only the adapter matrices"*）。
> 旧的 COCO 数字记 `n_trainable_params = 145,170,177`，**不是严格冻结**，
> 本就不该与严格冻结结果并列。用严格冻结补跑，**顺带修掉这个口径不一致**。
>
> ### 已完成的前置（三项，均实测）
>
> | # | 工作 | 结果 |
> |---|---|---|
> | 1 | 给 `experiments/strict_freeze_control.py` 加 **`--dataset` / `--data-dir`** | ✅ 已生效（原为硬编码 `flickr30k`，三处） |
> | 2 | **COCO 数据路径验证**（不占 GPU） | ⚠️ 加载器内部是 `join(data_dir, dataset_name)` → 传 `coco` 会拼成 `coco/coco/`；**正确传 `--data-dir .`** → 实测 `train=64 val=64 test=64` ✅ |
> | 3 | **COCO batch 键核验** | batch 为 `{'caption','image'}`，无 `input_ids` → 查 `src/trainer.py:379-391`：**trainer 会实时分词** → **无需改数据层** ✅ |
>
> ### 🐛 顺带修掉一个**会在最需要日志时崩溃**的 bug
>
> `tools/_p14_coco_sweep_driver.py` 原写 `... if 'r' in dir() else []`：
> **`'r' in dir()` 恒为真**（模块层 `import re` 绑定了名字 `r`），而 `r` 只在 try 成功路径存在
> → **超时分支一触发就 `NameError`**（恰在最需要诊断信息时）。
> **已改为显式初始化 `ok_this`/`out_lines`，`r` 改名 `pr`。**
> **已按 job id 精确终止旧实例并重启**（不再按 CPU/启动时间筛进程——那是先前误杀驱动的错法）。
>
> ### 🌙 三队列（GPU 串行，8 GB 只能一个）
>
> | 队列 | 脚本 | 内容 | 状态 |
> |---|---|---|---|
> | 1 | `_p7_overnight_driver.py` | α 首跑 → ③a OpenCLIP ✅ → **③b CLIP B/16** | ⏳ 运行中（已出 1/3 个 results.json） |
> | 2 | `_p11_alpha_rerun_driver.py` | 等 ③b → **α 重跑（5000 样本）** | ⏳ 等待中 |
> | 3 | `_p14_coco_sweep_driver.py` | 等队列 2 → **COCO 12 配置 × 3 seed**（严格冻结） | ⏳ 等待中 |
>
> ### 队列 3 的规模
>
> - **待补 12 配置**：`r ∈ {1,2,4,16,32,64} × {text_only, both}`（r=8 已有归档）× **3 seed** = **36 run**
> - **成本**：每 run ≈ 60 min → **≈36 h**（跨会话，**可续跑**：已有 `results.json` 的 run 自动跳过）
> - **日志**：`outputs/_coco_sweep_driver.log`
"""


def main() -> int:
    apply = "--apply" in sys.argv
    if not apply:
        print("  （预演）")
        return 0
    gpu = subprocess.run(["nvidia-smi", "--query-gpu=memory.used,utilization.gpu",
                          "--format=csv,noheader"], capture_output=True, text=True).stdout.strip()
    body = ENT.replace("### 🌙 三队列（GPU 串行，8 GB 只能一个）",
                       "### 🌙 三队列（GPU 串行，8 GB 只能一个）\n>\n> **当前 GPU**：" + gpu)
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "COCO 补跑就绪" in t:
        print("  已记录，跳过")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + body + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("COCO 补跑就绪", "--data-dir .", "trainer.py:379-391", "恒为真", "36 h"):
        assert k in t2, f"断言失败：缺 {k}"
    print(f"  ✅ HANDOFF 已追加（{len(t2.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
