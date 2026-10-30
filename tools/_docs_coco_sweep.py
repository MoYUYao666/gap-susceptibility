# -*- coding: utf-8 -*-
r"""落账：COCO 补跑就绪 + `--dataset` 支持 + 队列三（2026-10-07 深夜）。

    python tools\_docs_coco_sweep.py [--apply]
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
    if "COCO 补跑队列已就绪" in t:
        print("  已记录，跳过")
        return 0
    ent = f"""> **🧪 2026-10-07 深夜 —— COCO 补跑就绪（操作者选①严格冻结）｜三队列并行等待**
>
> ### 操作者决定：**① 沿用严格冻结**补跑 COCO
>
> 理由（我的建议被采纳）：本文的**核心证据就是严格冻结**（*"the optimiser sees only the adapter
> matrices"*）。旧的 COCO 数字记 `n_trainable_params = 145,170,177`，**不是严格冻结**——
> **它本就不该与严格冻结结果并列**。用严格冻结补跑，顺带修掉这个口径不一致。
>
> ### 已完成的前置工作（三项，均实测）
>
> | # | 工作 | 结果 |
> |---|---|---|
> | 1 | 给 `experiments/strict_freeze_control.py` 加 **`--dataset` / `--data-dir`** | ✅ 已生效（原为硬编码 `flickr30k`，三处） |
> | 2 | **COCO 数据路径验证**（不占 GPU） | ⚠️ 发现 `create_dataloaders` 内部会 `join(data_dir, dataset_name)` → 传 `coco` 会拼成 `coco/coco/`；**正确传 `--data-dir .`** → 实测 `train=64 val=64 test=64` ✅ |
> | 3 | **COCO batch 键核验** | batch 为 `{{'caption','image'}}`，**无 `input_ids`/`attention_mask`** → 查 `src/trainer.py:379-391`：**trainer 会实时分词**（"优先用预 tokenize，否则实时 tokenize"）→ **无需改数据层** ✅ |
>
> ### 🐛 顺带修掉一个**会在最需要日志时崩溃**的 bug
>
> `tools/_p14_coco_sweep_driver.py` 原写：
> `for ln in (r.stdout or "").splitlines()[-3:] if 'r' in dir() else []`
> —— **`'r' in dir()` 恒为真**（模块层 `import re` 引入了名字 `r`），且 `r` 在 `try` 内定义，
> **超时分支一旦触发就 `NameError`**（恰好发生在最需要诊断信息的时刻）。
> **已改为显式初始化 `ok_this`/`out_lines`，并把 `r` 改名 `pr`**（避免与 `re` 混淆）。
> **已按 job id 精确终止旧实例并用修好的代码重启**（不再按 CPU/启动时间筛进程——那是上一次误杀驱动的错误做法）。
>
> ### 🌙 三队列（GPU 串行）
>
> | 队列 | 脚本 | 内容 | 状态 |
> |---|---|---|---|
> | 1 | `_p7_overnight_driver.py` | α 首跑 → ③a OpenCLIP ✅ → **③b CLIP B/16** | ⏳ 运行中（**已出 1/3 个 results.json**） |
> | 2 | `_p11_alpha_rerun_driver.py` | 等 ③b → **α 重跑（5000 样本）** | ⏳ 等待中 |
> | 3 | `_p14_coco_sweep_driver.py` | 等队列 2 → **COCO 12 配置 × 3 seed**（严格冻结） | ⏳ 等待中 |
>
> **当前 GPU**：{gpu}
>
> ### 队列 3 的规模与排序
>
> - **待补 12 配置**：`r ∈ {{1,2,4,16,32,64}} × {{text_only, both}}`（r=8 已有归档）× **3 seed** = **36 run**；
> - **成本**：每 run ≈ 60 min → **≈36 h**（跨多个会话，**可续跑**：已存在 `results.json` 的 run 自动跳过）；
> - **日志**：`outputs/_coco_sweep_driver.log`。
"""
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ent + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("COCO 补跑队列已就绪", "--data-dir .", "trainer.py:379-391", "恒为真", "36 h"):
        assert k in t2, f"断言失败：缺 {k}"
    print(f"  ✅ HANDOFF 已追加（{len(t2.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
