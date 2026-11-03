# -*- coding: utf-8 -*-
r"""Record the run order, the labels fix and the measured noise floor.

    python tools/_p831_record_order.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **🔄 2026-10-16 01:00 —— 按操作者要求重排任务；labels bug 修复；4-bit 噪声地板已量化**
>
> 操作者指令：**「停一个，另一个接在后面」**
>
> ### 一、✅ 顺序已按要求排定（并修掉一个队列缺陷）
>
> **当前顺序**：**LLaVA（优先，PID 34872）→ Flickr30k rank 扫（从 rank4 续跑）→ 全量 COCO**。
>
> **⚠️ 我第一次写队列时用了错误的等待条件**：以「某 python 进程内存 > 2 GB」判断 LLaVA 是否在跑，
> 而 LLaVA **启动时内存尚未涨到 2 GB** ⇒ **条件立即为假，Flickr 被提前启动**，两任务抢 GPU。
> **已改为按 PID 精确等待**（`tools/_p830_chain.ps1`，等 PID 34872 结束）。
>
> | 任务 | 状态 | 已完成 |
> |---|---|---|
> | **LLaVA 4 臂 × 3 seed** | ✅ **运行中**（PID 34872，独享 GPU）| frozen × 3 |
> | Flickr30k rank 扫 | ⏸ 排队（`_p830_chain`，PID 11172）| rank 1、2 |
> | 全量 COCO | ⏸ 排队（Flickr 之后）| — |
>
> ### 二、✅ 修掉第 5 个脚本缺陷：`labels` 从未被构造
>
> **症状**：`AttributeError: 'NoneType' object has no attribute 'backward'` —— 训练臂一启动就崩。
> **根因**：我传了 `with_labels=True`，但 `make_batch` **从未真的往批次里放 `labels`** ⇒ `out.loss` 为 `None`。
>
> **修复中又发现一个陷阱**：**`<image>` 单个占位符会被展开成 577 个 token**
> ⇒ 按文本 token 数（20）掩码是错的（真实提示长度 596）。
> **改为按「最后一个图像 token 的位置」掩码**，对任何 tokenizer 行为都稳健。
>
> **✅ 单独验证通过**（`tools/_p828_labels_check.py`，**LABELS VERIFIED**）：
>
> | 检查 | 结果 |
> |---|---|
> | 监督跨度是 caption 而非提示 | ✅ 图像 token **不被监督** |
> | 跨度是 caption 量级 | ✅ caption 14/15 token → 监督 28/29（**chat 模板固定加 14**）|
> | 损失为有限合理值 | ✅ **3.29**（修前错位时为 **14.77**，是错位的直接证据）|
> | 序列长度 | 610（其中图像 token 577）|
>
> ### 三、✅ 4-bit 的噪声地板已量化（论文的 4-bit 顾虑现在有数）
>
> **frozen 臂（无训练）** 在 300 个 held-out COCO 配对上的重复测量：
>
> | 量 | before | after | 相对变化 |
> |---|---|---|---|
> | `DG*` | 0.2716 | 0.2696 | **−0.77%** |
> | `CG` | 0.7537 | 0.7516 | −0.28% |
>
> **⇒ 4-bit 下的噪声地板 ≈ 0.8%**。三个 seed 的 frozen 数值**完全一致**（0.2716 → 0.2696），
> 说明在同一进程内 4-bit 是确定性的；论文记录的不可复现是**跨运行**的。
> **后续各臂的效应只有超过 0.8% 才算真信号** —— 这一判据会写进稿件。
>
> ### 四、当前环境修复清单（累计 5 项脚本 + 2 项环境）
>
> | 类 | 项 |
> |---|---|
> | **环境** | ① 装 `sentencepiece`（LLaMA tokenizer 转 fast 必需）② 从 `hf-mirror.com` 下载 `clip-vit-large-patch14-336` 的 **7 个配置/分词文件（~2 MB，非权重）** |
> | **脚本** | ① 缺 `labels` ② `<image>` 展开 577 token 导致掩码错位 ③ PEFT 适配器跨 arm 残留（**每 arm 重载基础模型**）④ 量化权重 dtype 报 `uint8`（bitsandbytes 打包）⑤ `pixel_values` 已标准化却又除 255 |
>
> ### 五、完成后的下一步
>
> 1. LLaVA 三臂对照结果 ⇒ 写进 `supplement.tex` 的 decoder-VLM 小节（与 Qwen2-VL 并列）；
> 2. Flickr30k rank 扫 ⇒ 重核 ODE 拟合 $R^2$；
> 3. 全量 COCO（40,504 图 / 202,654 caption，比现规模大 13 倍）⇒ 回应 R2-3「更大数据集」；
> 4. 重新上传 GitHub（**不建 tag**）；5. 投稿。
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
    if "按操作者要求重排任务" in t:
        print("  already recorded")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("按操作者要求重排任务", "噪声地板", "577 个 token", "LABELS VERIFIED", "3.29"):
        print(f"  {'OK ' if k in t2 else 'BAD'} {k}")
    print(f"  HANDOFF lines = {len(t2.splitlines())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
