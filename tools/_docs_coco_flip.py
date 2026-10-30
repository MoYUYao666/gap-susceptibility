# -*- coding: utf-8 -*-
r"""落账：COCO 补跑完成 + 数据集翻转写入 + 表注错误修正（2026-10-10）。

    python tools\_docs_coco_flip.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **🔬 2026-10-10 —— COCO `text_only` 补跑完成；**查出一处真错误**并修正；数据集翻转写进论文**
>
> ### 一、COCO 补跑完成（11/11，0 失败）
>
> **动机**：论文主张"**最优位置随数据集翻转**"，但 COCO 的 `text_only` 只有 r1/r4/r16 与 1 个 r2，
> **r8/r32/r64 完全缺失** → 该结论在 COCO 上**只有 `both` 一侧的数据**。
>
> **补跑**（逐 seed + 失败重试，幂等）：r8/r32/r64 各 3 seed + r2 补 2 seed = **11 run**，全部成功。
> 期间遇**间歇性 `CUDA error: unknown error`**（旧 driver 一次传 3 seed，中途崩会丢掉同批剩余）
> → 改为**逐 seed 调用 + 重试 2 次**（`tools/_p132_coco_resume.py`），4 个剩余 run 全部 rc=0。
>
> ### 二、🔴 查出 `tab:position` 表注一处**与数据矛盾**的主张
>
> 表注原文：*"Text-only gives the smaller gap increase on Flickr30k, BLIP-1 and ViT-L, **while
> MS-COCO reverses that ordering**."*
>
> **但该表自己的 COCO 行**（三值同源 `outputs/coco/rq2_*`）：
> `text_only=-0.041`（**加粗**）｜`both=-0.052`｜`vision_only=+0.031`
> → **`text_only` 的间隙增长最小 → 加粗是对的 → 与 Flickr30k 同向，没有反转。**
>
> **溯源**（`tools/_p144`，扫描 **570** 个文件）：表中 10 个数字**全部有归档出处**，
> 含 COCO `vision_only=+0.031` → `outputs/coco/rq2_vision_only_coco/results.json`。
>
> **真正的反转在 SigLIP**（`validation.tex`，严格冻结）：`text_only` **+0.066±0.006** vs
> `both` **−0.011±0.006**（配对差 −0.078，t = −52.7，5 seed 同号）——
> **表注把一个不存在的数据集反转，与真实的架构反转混为一谈。**
>
> **已改**为：四个数据集上 text-only 都最保护，**反转发生在 SigLIP 且属严格冻结协议**
> （引 `sec:validation`）。
>
> ### 三、数据集翻转：**严格冻结协议下确实成立**（本次首次两侧齐备）
>
> | 数据集（r4，严格冻结） | `text_only` | `both` | 最保护 | 出处 |
> |---|---|---|---|---|
> | **Flickr30k** | **−0.0288 ± 0.0013** | −0.0188 ± 0.0004 | **`text_only`** | `strict_freeze_b32_r4/*/seed*` |
> | **MS-COCO** | −0.0414 ± 0.0015 | **−0.0886 ± 0.0026** | **`both`** | `coco_sweep_text_only/r4` + `coco_sweep/r4` |
>
> **COCO `text_only` 全秩单调改善**：r2 −0.0488 ｜ r8 −0.0944 ｜ r32 −0.1315 ｜ r64 −0.1396（各 3 seed）
> → **不是单秩的偶然**。
>
> **已写入 `validation.tex`**（新段："The comparison also depends on the evaluation corpus…"）
>
> ### 四、我又犯的两个错（留档）
>
> | # | 错 | 真因 | 修法 |
> |---|---|---|---|
> | 1 | 判"数据集翻转不成立" | **ΔCG 的符号约定搞反**：越负 = 间隙收缩越多 = **越保护**，我写成"越大越保护" | 核对 `tab:position_strict` 的加粗是**最小值** → 修正后**翻转成立** |
> | 2 | 先说表里 `vision_only=+0.031` 找不到出处 | **我只搜了 `coco_sweep/`，没搜 `outputs/coco/`** | 扩大到全归档 570 个文件 → **全部找到** |
>
> ### 五、编译与门禁
>
> | 稿 | 页数 | 错误 | 未定义 | Overfull |
> |---|---|---|---|---|
> | Springer | **40** | 0 | 0 | 0 |
> | **NC** | **55**（原 54） | 0 | 0 | 0 |
>
> **门禁：65/65 通过**（新增 10 条 COCO 主张）｜退出码 0
>
> ### 六、还差什么
>
> | # | 项 | 状态 |
> |---|---|---|
> | 1 | `paper合` 定目标刊（ESWA/KBS/CVIU）并投出 | ⏳ 待操作者 |
> | 2 | 解码器 VLM 仍单模型/单 seed/4-bit | ⏳ 需可用 GPU |
> | 3 | A1 转投确认（`Neural Networks`，截止 `Nov 08 2026 23:59`） | ⏳ 待操作者 |
"""


def main() -> int:
    apply = "--apply" in sys.argv
    if not apply:
        print("  （预演）")
        return 0
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "COCO `text_only` 补跑完成" in t:
        print("  已记录，跳过")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("COCO `text_only` 补跑完成", "MS-COCO reverses that ordering", "65/65",
              "符号约定搞反", "570", "55**（原 54）"):
        assert k in t2, f"断言失败：缺 {k}"
    print(f"  ✅ HANDOFF 已追加（{len(t2.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
