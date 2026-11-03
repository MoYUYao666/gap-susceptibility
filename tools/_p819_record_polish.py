# -*- coding: utf-8 -*-
r"""Record the language polish and the R2-3 scale-up plan.

    python tools/_p819_record_polish.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **✏️ 2026-10-15 23:00 —— 语言润色完成（可验证）；R2-3「更大数据集」方案启动**
>
> 操作者指令：**「找更大数据集 / 更现代 VLM，并做语言润色」**
>
> ### 一、✅ 语言润色（`tools/_p816_polish.py`，**POLISH VERIFIED**）
>
> 3 位审稿人一致要求语言编辑。先用 `tools/_p815_polish_survey.py` **量化缺陷**，再改 —— 结果：
>
> | 指标 | 润色前 | 润色后 |
> |---|---|---|
> | **英式拼写** | **25 处**（`optimise` 10、`analyse` 4、`behaviour` 3…）| **0** ✅ |
> | 美式拼写 | 9 | 15（统一）|
> | `cross-architecture` 空格变体 | 3 | **0** ✅ |
> | `cross-dataset` 空格变体 | 2 | **0** ✅ |
> | `both-position` 空格变体 | 7 | **0** ✅ |
> | 超长句（≥70 词）| 19 | 18（最长句 124 词已拆）|
>
> **改动量**：**35 处拼写 + 13 处复合词 + 1 处长句拆分**。
> **编译**：**64 页 / 0 错误** ✅
> **断言**：**数字 / `\\label` / `\\ref` / `\\cite` / `\\includegraphics` 全部未变**（逐文件核验）✅
>
> **设计要点**：**受保护区（`$...$` 数学、`\\texttt{}`、`\\cite{}`、`\\label{}` 等）一律不改** ——
> 其中的英式拼写是**代码标识符**（如 ImageNet-C 的 corruption 名 `colour_jitter`），改了会让程序找不到东西。
>
> **⚠️ 我在这次润色中犯了 4 个错，全部已修**（如实记录，供日后复核）：
>
> | # | 错误 | 根因 | 修正 |
> |---|---|---|---|
> | 1 | 模式表混了「词干」与「整词」，统一加后缀 | `\\bbehaviour\\b(?=\\w)` **自相矛盾、永不匹配** | 分成 `SPELLING_STEMS`（`\\bstem\\w*`）与 `SPELLING_WORDS`（`\\bword\\b`）|
> | 2 | 把 `favour` 当整词 | `\\bfavour\\b` **不匹配 `favours`**（复数）| 移入词干列表 |
> | 3 | 断言与替换口径不一致 | 断言扫了受保护区 ⇒ **误报 3 处** | 断言改为**掩码**受保护区 |
> | 4 | 半改状态下重跑 | 上次 `--apply` 已部分改过 | **先从 `.bak_p816` 还原**再重跑（还原 3 次）|
>
> ### 二、⚠️ R2-3「更现代 VLM」—— **评估后不采用**（理由充分）
>
> | 候选项 | 可行性 | 裁决 |
> |---|---|---|
> | `llava-hf/llava-1.5-7b-hf`（本地已缓存 **14.13 GB**）| 本地 GPU 仅 **8.6 GB** ⇒ **必须 4-bit 量化**；而**本稿自己记录过 4-bit 不可复现**（*"repeating one configuration with an identical seed changed the measured gap span from 0.304 to 0.407"*）| 🔴 **不用** —— 用它会引入本稿已承认的不可靠因素 |
> | `Qwen/Qwen2-VL-2B-Instruct` | 缓存目录**为空** | 🔴 不可用 |
> | 服务器下载新权重 | **`192.168.1.103` 不可达**（实测 `ping` 失败）| 🔴 不可用 |
>
> **⇒ 我写了一个 LLaVA 评测脚本（`tools/_p817_llava_modern.py`），发现其中 `gap_from_embeddings`
> 的 CG/DG 复用了同一个公式（占位符），且只测冻结模型、没做三臂对照 ⇒ 已删除**，
> 不把带占位符的脚本留在仓库里充当交付。
>
> ### 三、✅ R2-3「更大数据集」—— **采用全量 COCO val**（无需新数据、无需量化）
>
> **关键事实**：本稿此前的规模实验只用了 COCO val 的 **3,000 张**（因为 loader 按 **caption 行**截断，
> 而非按图像截断）；**val2014 实际有 40,504 张 / 202,654 条 caption** ⇒ **可把评测放大 13 倍**。
>
> **`tools/_p818_full_coco.py`**：同一套已验证配置（CLIP ViT-B/32、冻结基座 + 仅适配器、
> rank 8、text-only、3 seeds、lr 1e-5、dropout 0），**唯一变量是规模**；
> 检索用**修正协议**（同图任一 caption 命中即算、唯一图像 gallery、双向）。
>
> **✅ 已启动串行任务**（`tools/_p818_launch.ps1`，启动器 PID **32096**）：
> 等 Flickr30k rank 扫（PID 34144）结束 → 自动开跑全量 COCO。
>
> ### 四、⏳ 当前两个后台任务
>
> | PID | 任务 | 状态 |
> |---|---|---|
> | **34144** | Flickr30k rank 扫（ranks 1,2,4,8,16,32,64）| 进行中（rank1）|
> | **32096** | 全量 COCO 串行启动器（等 34144 结束）| 等待中 |
>
> ### 五、⏳ 剩余
>
> 1. 两个实验跑完 ⇒ 把结果写进 Paper A（`validation.tex` / `empirical.tex`）；
> 2. 重新上传 GitHub（**同样不建 tag**）；
> 3. Paper A 投稿。
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
    if "语言润色完成（可验证）" in t:
        print("  already recorded")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("语言润色完成（可验证）", "POLISH VERIFIED", "32096", "40,504",
              "永不匹配", "_p817_llava_modern"):
        print(f"  {'OK ' if k in t2 else 'BAD'} {k}")
    print(f"  HANDOFF lines = {len(t2.splitlines())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
