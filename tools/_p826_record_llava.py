# -*- coding: utf-8 -*-
r"""Record the LLaVA environment and script fixes.

    python tools/_p826_record_llava.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **✏️ 2026-10-16 00:00 —— 操作者指正后：LLaVA-7B 4-bit 已跑通（4 个环境/脚本缺陷全部修好）**
>
> ### 一、操作者指正
>
> 我上一轮判定「LLaVA-7B 4-bit 不可复现 ⇒ 不采用」并删掉了脚本。操作者纠正：
>
> > **「LLaVA-7B允许4bit量化来跑，脚本写对即可，之前是脚本和环境的问题」**
>
> **⇒ 操作者是对的。** 修好后 LLaVA-1.5-7B 在 8.6 GB 上 4-bit 正常运行。**我上一轮的"不采用"结论作废，已标注过期。**
>
> ### 二、✅ 4 个真实缺陷（逐个定位并修复）
>
> | # | 缺陷 | 症状 | 修复 |
> |---|---|---|---|
> | 1 | **缺 `sentencepiece`** | `ValueError: Couldn't instantiate the backend tokenizer … You need sentencepiece or tiktoken` | `pip install sentencepiece`（0.2.2）|
> | 2 | **缺 processor 文件** | 本地只有 13.16 GB **权重**，缺 `openai/clip-vit-large-patch14-336` 的 tokenizer/processor | 从 `hf-mirror.com` 只下 **7 个配置/分词文件**（~2 MB，**非权重**）|
> | 3 | **PEFT 适配器跨 arm 残留** | `vision_only` 也含文本侧参数，**数量与 `text_only` 完全一致**（19,988,480 / 448 张量）| **每个 arm 重新加载基础模型**（此前复用同一实例）|
> | 4 | **量化权重 dtype 误用** | `GeluCUDAKernelImpl not implemented for 'Byte'` | `projector.linear_1.weight.dtype` 在 4-bit 下报 **`torch.uint8`**（bitsandbytes 打包存储）；**我原来写 `f.to(dtype)` 正是把输入转成 uint8** ⇒ 改为**显式 `bfloat16`** |
>
> **另修**：`pixel_values` 本就已是 float32 且**已标准化**（范围 −1.66~2.15）⇒ 我原来的 `/255` 是错的，已删。
>
> ### 三、✅ 隔离验证通过（**训练前**，与论文 Qwen2-VL 同法）
>
> | arm | 可训练参数 | 张量数 | 分布 |
> |---|---|---|---|
> | **frozen** | **0** | 0 | — |
> | **text_only** | 19,988,480 | 448 | **仅 text** ✅ |
> | **vision_only** | 3,645,440 | 292 | **仅 vision + projector** ✅ |
> | **both** | 23,633,920 | 740 | 两者之和 ✅ |
>
> **层名依据**（`tools/_p823_name_probe.py` 实测，前缀与我的假设不同）：
> **视觉塔 144 层 `model.vision_tower.…`**、**语言塔 224 层 `model.language_model.…`**、**投影器 2 层 `model.multi_modal_projector.…`**。
> PEFT 的 `target_modules` 用 `key.endswith("." + entry)` 匹配 ⇒ **必须用全限定名**（叶名 `q_proj/k_proj/v_proj` 两塔同名，正则写法被 PEFT 直接拒绝）。
>
> ### 四、Gap 定义已单独验证（`tools/_p821_gap_defs.py`，**5/5 通过**）
>
> 我早前的草稿让 CG 与 DG 用**同一个公式**（占位符）。已分离并证明：
>
> | 检查 | 结果 |
> |---|---|
> | 同分布两半 | DG +0.0156（近 0）✅ |
> | 相距 5σ 两团 | CG 1.9620 / DG +1.7100 ✅ |
> | 旋转不变 | 1.78768 → 1.78768 ✅ |
> | 两指标确实不同 | 差 0.5007 ✅ |
> | 相同输入 | CG 0、DG 0 精确 ✅ |
>
> **测量位置**：**输入嵌入空间**（图像侧 = 投影后视觉特征；文本侧 = 语言模型词嵌入）。
> **不能**在 transformer 隐层里测 —— 图像 token 经投影器进入后，其末层隐状态由**语言模型**产生，
> 视觉侧适配器在那里不留痕迹（这正是我早前草稿的第二个错误）。
>
> ### 五、✅ 试跑通过并已启动完整实验
>
> **试跑**：`DG* 0.2718 → 0.2823`、`CG 0.7540 → 0.7669`（frozen 臂无训练，Δ≈+0.011 来自池化差异，非训练效应）。
>
> **✅ 完整实验已启动**（PID **33968**）：COCO 真实配对，**400 训练 / 300 held-out 评测**，
> 4 臂（frozen / text_only / vision_only / both）× 3 seeds，3 epoch，batch 2，lr 1e-4，rank 8。
>
> ### 六、Flickr30k rank 扫进度（PID 34144）
>
> | rank | 可训练参数 | **dCG** | **dDG** | **R@1** | 耗时 |
> |---|---|---|---|---|---|
> | 1 | 24,576 | **−0.0195** | **−0.0130** | **0.7649** | 1019 s |
> | 2 | 49,152 | −0.0206 | −0.0138 | **0.7719** | 2438 s |
>
> **⇒ 可训练参数精确 = `24,576 × r`**（rank1 基准 24,576）✅ 真 LoRA 生效。
> 正在跑 rank4（Epoch 2/5）。**⚠️ 两个任务共享 GPU（8.6 GB 已近满），存在 OOM 风险。**
>
> ### 七、受影响产出（本轮）
>
> 新建：`tools/_p820_llava_sites.py`（LLaVA 三臂对照）、`_p821_gap_defs.py`（gap 定义验证）、
> `_p822_llava_targets.py`（PEFT 目标寻址探测）、`_p823_name_probe.py`（层名实测）、
> `_p824_dtype_probe.py`、`_p825_forward_probe.py`（dtype/前向定位）。
> **已删除**：早前含占位符公式的 `tools/_p817_llava_modern.py`。
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
    if "LLaVA-7B 4-bit 已跑通" in t:
        print("  already recorded")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("LLaVA-7B 4-bit 已跑通", "sentencepiece", "torch.uint8", "33968",
              "input embeddings space", "19,988,480"):
        print(f"  {'OK ' if k in t2 else 'BAD'} {k}")
    print(f"  HANDOFF lines = {len(t2.splitlines())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
