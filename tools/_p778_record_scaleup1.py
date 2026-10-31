# -*- coding: utf-8 -*-
r"""Record the first completed large-scale COCO point and resume the full grid.

    python tools/_p778_record_scaleup1.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **📈 2026-10-15 11:00 —— 规模跑第一个点完成：**text_only 在 10,000 图 COCO 上把 i2t 检索从冻结的 0.4755 提到 0.9293****
>
> ### 一、操作者指令
>
> > **"我刚刚重启电脑了，直接跑全配置，第一个是不是跑完了，跳过"**
>
> ### 二、✅ 重启前的第一个 run 完整可用（**不是半截**）
>
> `outputs/scaleup_coco/coco_scaleup_text_only_r8_s42.json`（559 字节，10-14 10:22 写入）：
>
> | 项 | 值 |
> |---|---|
> | 训练规模 | **COCO train2014 10,000 唯一图 / 50,020 caption 行** |
> | 评测规模 | **COCO val2014 3,000 唯一图 / 15,010 caption 行**（**与训练不相交**）|
> | epochs | 3 ｜ batch 64 ｜ rank 8 ｜ lr 1e-5 ｜ dropout 0 |
> | **R@1** | **0.6179** |
> | R@5 | 0.7775 |
> | R@10 | 0.8339 |
> | **R@1 i2t** | **0.9293** |
> | R@1 t2i | 0.3065 |
> | 训练耗时 | 1,712.6 s（28.5 分钟）｜ 评测 37.8 s |
>
> ### 三、🔴 与冻结基线的对比（**这是本轮的核心数字**）
>
> | 口径 | 冻结 CLIP（同 3,000 图 gallery） | **text_only LoRA 微调后** |
> |---|---|---|
> | **i2t R@1** | **0.4755** | **0.9293** ✅ **+95%** |
>
> **⇒ 在正确的检索协议 + 分离的 train/val + 5 倍规模下，文本侧 LoRA 微调显著提升检索**，
> 与档案里 COCO 的 `R@1 < 0.001`（near-random）**完全矛盾** ⇒ 进一步确认档案的 COCO 结果是配置/协议产物。
>
> ### 四、✅ 已加的 resume 逻辑（避免重跑）
>
> `tools/_p754_coco_scaleup.py` 原先**没有跳过逻辑**。已加：每个 run 开工前检查
> `outputs/scaleup_coco/<name>.json` 是否存在且 `R@1` 非空 ⇒ 存在则读入并 `continue`。
> **实测生效**：日志显示 `coco_scaleup_text_only_r8_s42: already complete, skipping (R@1 0.6179)`。
>
> ### 五、当前状态（PID 21952 运行中）
>
> | run | 状态 |
> |---|---|
> | `text_only` s42 | ✅ **已完成**（跳过）|
> | `text_only` s43 / s44 | ⏳ |
> | `both` s42 / s43 / s44 | ⏳ |
> | `frozen`（基线，同 gallery） | ⏳ |
>
> **预计剩余约 1.9 小时**（实测 28 分钟/run，5 个未完成 run）。
>
> **⚠️ 诚实标注**：**目前只有 1 个 seed**，`both` 臂与另外 2 个 seed 尚未跑完 ⇒ **还不能下"text-only 优于 both"的结论**，
> 只能确认"text-only 微调在 10,000 图上有效"。
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
    if "规模跑第一个点完成" in t:
        print("  already recorded")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("规模跑第一个点完成", "0.9293", "0.6179", "already complete, skipping", "1.9 小时"):
        print(f"  {'OK ' if k in t2 else 'BAD'} {k}")
    print(f"  HANDOFF lines = {len(t2.splitlines())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
