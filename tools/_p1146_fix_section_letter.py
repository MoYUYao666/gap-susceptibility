# -*- coding: utf-8 -*-
r"""Fix the duplicated supplement section letter and record the measurement-convention finding.

Two separate things, both GPU-free:

1. The supplement has two sections lettered F ("Provenance of the R@1 column" and "A Larger Decoder Model"), so
   the second is relettered G and its title stops calling the result a null. The body is NOT rewritten here: the
   numbers it currently quotes were measured under a convention that is not the paper's, and the replacement text
   waits for the clean re-measurement.

2. The finding itself goes into the handover documents, because it affects two different tables and one pending
   decision. It is recorded with the code line references so it can be re-checked:

   * `tools/_p820_llava_sites.py` measured the LLaVA gap with `make_batch(..., with_labels=False)`, which builds
     the prompt "USER: <image> Describe this image in detail. ASSISTANT: " and **no caption**, so the text side
     was the instruction rather than the caption;
   * `tools/_p47_qwen_train.py` (the producer of `outputs/analysis/vlm_bf16_detail.json`, i.e. supplement
     Table E) pools the "text" side over **all non-padding positions**, which on a Qwen2-VL sequence is ~196
     image tokens plus ~15 caption tokens, and then applies **two different fixed random projections**
     (`proj_i`, `proj_t`, `PROJ_DIM=512`, seed 0);
   * the clean definition -- image-token pool against caption-token pool, identical treatment, no projection --
     has not been measured on either model yet.

    python tools/_p1146_fix_section_letter.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SUPP = REPO / "paper合" / "sections" / "supplement.tex"
HANDOFF = REPO / "HANDOFF.md"
MAP = REPO / "文件地图.md"
MARK = "测量口径发现"

OLD_HEAD = "\\section*{F. A Larger Decoder Model: A Scoped Null Result}"
NEW_HEAD = "\\section*{G. A Larger Decoder Model: Adaptation-Site Effects}"

ENT = """> **🔬 2026-10-17 18:00 —— 发现两处**测量口径问题**（影响补充 E/F 两节）；云端主机已停（数据未丢）**
>
> ### 一、⚠️ 云端主机失联，但**无数据损失**
>
> `connect.westb.seetacloud.com:19434` 三次测试均不可达（可能已被操作者关机/到期）。
> **12 条记录 + 9 个适配器已全部取回本地**：`outputs/llava_canonical_cloud/`，**22 文件 / 1700.1 MB**，逐文件大小校验 0 不符。
> 本地只有 **RTX 4060 Laptop 8 GB**，跑不了 LLaVA-7B bf16（14 GB），且论文明确拒绝 4-bit（不可复现）⇒ **干净重测须在云端做**。
>
> ### 二、🔬 发现：补充 E 与 LLaVA 用的**都不是论文正文的定义**，而且三者互不相同
>
> | 出处 | 图像侧 | 文本侧 | 投影 |
> |---|---|---|---|
> | **正文/ODE 定义** | 图像嵌入 | **caption** 嵌入 | 无 |
> | **补充 E（Qwen2-VL-2B）**，源 `tools/_p47_qwen_train.py` | 图像 token 均值池化 | **全部非 padding 位置**（Qwen 序列里 **196 图像 token + ~15 caption token** ⇒ 93% 是图像）| **两侧各过一个不同的固定随机投影**（`PROJ_DIM=512`，seed 0，不训练）|
> | **本次 LLaVA 重训**，源 `tools/_p820_llava_sites.py` | 图像 token 均值池化 | **提示词**（`with_labels=False` ⇒ **不含 caption**）| 无 |
>
> **证据行号**：
> - `_p47_qwen_train.py:129-133`（text = `str(c)` caption）、`:140-141`（`mask = attention_mask` ⇒ T 含图像 token）、`:144`（vis_mask 151652–151656）、`:150-151`（`proj_i`/`proj_t`）、`:220-229`（固定随机初始化、不训练）；
> - `_p820_llava_sites.py:200`（`pre + ""`，`with_labels=False` 时无 caption）、`:406` 起的 `_sides`。
>
> **两条后果**：
> 1. **补充 E 的 DG\\* 不是图像-文本 gap**：两侧都主要是图像内容，再经两个**不同的随机投影**。其相对变化的**符号与幅度依赖那次随机抽签**——换一组 `proj_i`/`proj_t` 结果会变 ⇒ E 节"各臂均下降 X%"的结论**对任意投影不稳健**；
> 2. **本次 LLaVA 的 +35.7% 也不是正文定义**（文本侧是提示词）。
>
> ### 三、✅ 已经准备好的干净定义重测（只前向，不需重训）
>
> `tools/_p1145_clean_gap_measure.py`：**图像 token 池化 vs caption token 池化**（`labels != -100`）、**两侧同等处理、无投影**，从已存的 9 个适配器重算；
> 同时**在同一批数据上**再算一遍提示词口径，用来**量化口径效应**大小而非口头断言。
> 预计 **30–40 分钟**（10 次测量 × 500 对 + 每适配器加载）。
> **阻塞**：需要一台 ≥16 GB 显存的机器（新机还需重下 LLaVA 权重约 8 分钟）。
>
> ### 四、⏸️ 因此补充 F/G 节**正文暂未改写**
>
> 只把**重复的节号修掉**：第二个 "F." → **"G."**，标题去掉 "A Scoped Null Result"（旧结论已被推翻）。
> 正文等干净数值出来再一次性改写，避免写两遍、也避免把非正文定义的数字当正文定义发表。
>
> ### 五、⏭️ 待操作者决定
>
> | 选项 | 内容 | 代价 |
> |---|---|---|
> | **A** | 开一台 24–32 GB 机器，跑干净重测（`_p1145`，30–40 min）→ 据干净数值改写 G 节 | 约 1 小时（含重下权重）|
> | **B** | 就用现有提示词口径写 G 节，写明口径、**不宣称与 E 可比** | 0，但 G 节较弱 |
> | **C** | 连 E 节一起修：重下 Qwen2-VL-2B（~4.4 GB）并按干净定义重跑 13 seed × 3 臂（论文自述每 run 3.3–5.0 分钟 ⇒ 约 3.3 小时）| 约 4 小时 |
>
> **脚本**：`_p1145`（干净重测）｜`_p1146`（修节号 + 本条记录）。
>

"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(SUPP, encoding="utf-8").read()
    n_heads = t.count(OLD_HEAD)
    n_fs = len(re.findall(r"\\section\*\{F\.", t))
    print(f"  occurrences of the LLaVA head: {n_heads} | sections lettered F: {n_fs}")
    if n_heads != 1:
        print("  !! expected exactly one LLaVA head")
        return 1
    if n_fs != 2:
        print(f"  !! expected two sections lettered F before the fix, found {n_fs}")
        return 1
    if not a.apply:
        print("  (dry run)")
        return 0

    t = t.replace(OLD_HEAD, NEW_HEAD, 1)
    io.open(SUPP, "w", encoding="utf-8", newline="").write(t)
    after = io.open(SUPP, encoding="utf-8").read()
    print(f"  relettered; sections lettered F now: {len(re.findall(r'\\section\\*\\{F\\.', after))}, "
          f"lettered G: {len(re.findall(r'\\section\\*\\{G\\.', after))}")
    assert len(re.findall(r"\\section\*\{F\.", after)) == 1
    assert len(re.findall(r"\\section\*\{G\.", after)) == 1

    hp = io.open(HANDOFF, encoding="utf-8").read()
    if MARK not in hp:
        i = hp.find("# 项目交接文档")
        j = hp.find("\n", i)
        hp = hp[: j + 1] + "\n" + ENT + hp[j + 1:]
        io.open(HANDOFF, "w", encoding="utf-8", newline="").write(hp)
        print("  handoff entry added")
    else:
        print("  handoff already has this entry")

    mp = io.open(MAP, encoding="utf-8").read()
    row = ("51. 🔬 **发现 E/F 两节的测量口径都不是正文定义（2026-10-17 18:00）** —— "
           "**E 节**（源 `_p47_qwen_train.py:140-151`）文本侧池化**全部非 padding 位置**（Qwen 序列 ≈196 图像 token + 15 caption ⇒ **93% 图像**）"
           "且两侧过**两个不同的固定随机投影**（`PROJ_DIM=512`, seed 0, 不训练）⇒ **其相对变化依赖随机抽签、对投影不稳健**；"
           "**本次 LLaVA**（源 `_p820:200`）文本侧是**提示词、不含 caption**。三者互不相同。"
           "已备好干净重测 `_p1145`（图像 token vs **caption token**、无投影、只前向 30–40 min）。"
           "**云端主机已失联但 12 记录 + 9 适配器已取回本地（1700 MB，0 不符）**；本地 4060 8 GB 跑不了 7B、且 4-bit 被论文拒绝 ⇒ 重测需新机。"
           "补充节已把**重复的 F 改为 G**；**G 节正文暂未改写**（等干净数值）。详见 `HANDOFF.md` 18:00 条目。\n")
    anchor = "50. 🎯 **规范度量重训完成 + Qwen 试跑成功"
    idx = mp.find(anchor)
    if idx >= 0:
        end = mp.find("\n", idx)
        mp = mp[: end + 1] + row + mp[end + 1:]
        io.open(MAP, "w", encoding="utf-8", newline="").write(mp)
        print("  map item added")
    else:
        print("  !! map anchor not found")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
