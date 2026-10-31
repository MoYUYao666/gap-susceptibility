# -*- coding: utf-8 -*-
r"""Record the seed-convention mistake and the corrected rerun.

    python tools/_p787_record_seeds.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **🌱 2026-10-15 16:00 —— 操作者指出 seed 用错：**项目约定是 `42, 123, 456`，我用了 `42, 43, 44`**
>
> ### 一、操作者指出
>
> > **"这种三seed对吗，之前的实验不都是42,123,456这种吗，还是说有什么说法"**
>
> **⇒ 是对的，我用错了。**
>
> ### 二、查证：项目约定确为 `42, 123, 456`
>
> | 来源 | SEEDS |
> |---|---|
> | `experiments/theory/coco_validation.py` | **`[42, 123, 456]`** |
> | `experiments/theory/beta_pilot.py` | **`[42, 123, 456]`** |
> | `experiments/seed_experiments.py` | `[42, 123, 456, 789, 1024]` |
> | `experiments/theory/adapter_sweep.py` | `[42, 123, 456, 789, 999]` |
> | `experiments/theory/v1_rank_sweep{,coco}.py` | `[42, 123, 456, 789, 999]` |
> | **档案 `outputs/theory` 实际存在的 seed 目录** | **seed42(133) / seed123(127) / seed456(127) / seed789(4)** |
>
> **⇒ 约定：基准三 seed 用 `42, 123, 456`；要五个则续 `789, 999`。**
>
> ### 三、🔴 我的错误
>
> `tools/_p754_coco_scaleup.py` 里我写了 `list(range(42, 42 + a.seeds))` ⇒ **得到 `42, 43, 44`**。
>
> **后果**：
> 1. **与档案不可直接比较** —— 同 seed 才有配对可比性，`43/44` 在档案里不存在；
> 2. **"多 seed 验证"的说服力下降** —— 审稿人看到 `42,43,44` 会认为不是项目既定协议；
> 3. 已完成的 4 个 run（`text_only` s42/s43/s44、`both` s42）**全部作废**（s42 与约定重合，但为保持一致仍重跑）。
>
> ### 四、✅ 修正
>
> 在 `_p754_coco_scaleup.py` 顶部加入显式常量并替换生成逻辑：
>
> ```python
> # Seed pool used throughout the project (experiments/theory/coco_validation.py, beta_pilot.py,
> # seed_experiments.py, v1_rank_sweep*.py), so runs made here stay comparable with the archive.
> # The archive contains seed42, seed123, seed456 and a few seed789 runs.
> SEED_POOL = [42, 123, 456, 789, 999]
> ...
> seeds = [42] if arm == "frozen" else SEED_POOL[:a.seeds]
> ```
>
> **验证**：`--seeds 3` ⇒ **`[42, 123, 456]`** ✅
>
> ### 五、✅ 重跑（PID 24440）
>
> - 错 seed 的结果已归档（**不删**）：`outputs/_scaleup_coco_SEEDS_42_43_44/`
> - 新跑：**真 LoRA（196,608 参数 / 0.13%）+ 正确 seed `42, 123, 456`**，规模与配置不变
>   （10,000 训练图 / 3,000 评测图 / 3 epoch / rank 8 / lr 1e-5 / dropout 0）
> - 启动日志已确认：`可训练参数合计: 196,608 (LoRA only)`
>
> ### 六、📌 已观测到的（错 seed 但仍有参考价值的）趋势
>
> | 配置 | 可训练参数 | R@1 |
> |---|---|---|
> | 冻结基线 | 0 | 0.5794 |
> | 旧"LoRA"（实为文本塔全量微调，13 亿倍于 LoRA） | 145,170,177 | 0.6190 ± 0.0024 |
> | **真 LoRA text_only**（错 seed） | **196,608** | **0.6082 ± 0.0009** |
> | **真 LoRA both**（错 seed, s42） | 491,520 | **0.6246** |
>
> **⚠️ 三个臂的 t2i/i2t 分项旧值受 `evaluate()` 的重复计数 bug 影响，已作废；此处只比 R@1。**
> **初步趋势：真 LoRA 用 740 分之一的可训练参数达到与"全塔微调"同档的检索（0.608 vs 0.619），且 `both` 略高。**
> **⇒ 这对"参数高效"是利好，但须等正确 seed 的结果确认。**
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
    if "操作者指出 seed 用错" in t:
        print("  already recorded")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("操作者指出 seed 用错", "SEED_POOL", "42, 43, 44", "0.6082", "_SEEDS_42_43_44"):
        print(f"  {'OK ' if k in t2 else 'BAD'} {k}")
    print(f"  HANDOFF lines = {len(t2.splitlines())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
