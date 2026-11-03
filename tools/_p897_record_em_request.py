# -*- coding: utf-8 -*-
r"""Record that the replacement request was sent to the Editorial Manager for P3.

Operator-supplied screenshots (2026-10-15) show the EM query form filled in from the counterpart of
`SUBMISSION/P3_PRL_revision/EMAIL_TO_EM_2026-10-15.txt`: name Hongrui Wan, hw4c24@soton.ac.uk, and the
form's own footer confirming Journal = Pattern Recognition Letters, Article = Zero-Shot
Cross-Architecture Rank Allocation from Gradient Geometry, Manuscript = PRLETTERS-D-26-02378R1.

The query text is unpasted-without-the-subject-line: the form has no subject field, which is why the
file no longer carries a "Subject:" line and its body is wrapped at 80 columns.

    python tools/_p897_record_em_request.py [--apply]
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HANDOFF = REPO / "HANDOFF.md"
MAP = REPO / "文件地图.md"
MARK = "P3 替换件申请已发 EM"

ENT = """> **📤 2026-10-15 14:10 —— P3 替换件申请已通过 Editorial Manager 查询表单发出**
>
> 操作者提供了两张 EM 表单截图（`Name: Hongrui Wan` ／ `hw4c24@soton.ac.uk`），
> **正文与我准备的文本逐字一致**，表单页脚自带确认：
> `Journal title: Pattern Recognition Letters` ／
> `Article title: Zero-Shot Cross-Architecture Rank Allocation from Gradient Geometry` ／
> `Manuscript number: PRLETTERS-D-26-02378R1`。
>
> ### 一、✅ 发出内容（`SUBMISSION/P3_PRL_revision/EMAIL_TO_EM_2026-10-15.txt`）
>
> | 段 | 要点 |
> |---|---|
> | 请求 | 允许**替换两份文件**（正文 + 补充材料），因为 10-13 上传的版本发现**两处交叉引用缺陷** |
> | 定性 | **不影响任何结果、数字、图或结论**；纯属内部引用错误，希望更正而不是留在存档里 |
> | 缺陷 1 | 正文指向补充材料的 **4 个节号 + 1 个区间**与补充实际不符（正文写 `S1–S6`、补充实为 9 节；样本量/第二数据集指向 S3、秩缩放指向 S4、与先前工作比较指向 S5，而它们实际在 **S8/S9**）——内容都在，**只是指针错** |
> | 缺陷 2 | 补充材料**7 处畸形交叉引用**（PDF 里可见）：`Theorem the main text`、`Table the main text`×2、`Table Supplementary Table S4/S3/S2`、`Figure Supplementary Figure S3`、`Lemma Lemma 1`；其中 **S2 表与 S3 图在补充里根本不存在** |
> | 替换内容 | 正文：**只改那 5 个指针**，句子/数字/表/图全不变；补充：**所有交叉引用改为可解析** + 节序对齐正文编号 + **补上承诺却缺失的样本量表**（$n=16/64/128/256$，源自归档 20 run、单 seed、4 epoch，表注写明 seed 与 epoch 数）|
> | 备选 | 可提供**新旧对照标注版**，或**只换补充**（正文只改 5 个数字）|
> | 问题 | 现阶段能否替换上传、应放入哪些文件槽位 |
>
> ### 二、⚠️ 表单互动的两点更正（已落进文件）
>
> 1. **EM 查询表单没有 Subject 字段** ⇒ 我原先写的 `Subject:` 行已**从文件中删除**（操作者粘贴时也未包含它，是对的）；
> 2. 原文本最长行 **103 字符**，表单自己折行后出现**孤字换行**（截图第 3 行末 "the" 单独成行）⇒
>    已按 **80 列**重排（`tools/_p896_reformat_em_text.py`），正文最长行 **80**。
>
> ### 三、✅ 替换件已就绪（等编辑部回复即可上传）
>
> `SUBMISSION/P3_PRL_revision/CORRECTED_2026-10-15/`
>
> | 文件 | 页数 | 与提交版差别 |
> |---|---|---|
> | `main_corrected.pdf` | **10** | 仅 5 个数字：`S3→S9`×2、`S4→S5`、`S5→S9`、`S1–S6→S1–S9` |
> | `supplementary_corrected.pdf` | **5** | 节序对齐 + 8 处引用可解析 + 补样本量表（**5 张表**）|
> | `README.md` | — | 两版逐项差别 + 复核命令 |
>
> **复核**：`tools/_p893_p3_correspondence.py` → **CORRESPONDENCE VERIFIED**；
> `tools/_p892_p3_build_check.py` → 两份 **0 错误 / 0 未定义引用 / 0 未定义引文**；两份 PDF **无 `??`**。
>
> ### 四、⏳ 下一步
>
> **等编辑部回复**（能否替换、槽位）。回复后动作已备妥：
> 若同意 ⇒ 直接上传 `CORRECTED_2026-10-15/` 两个 PDF；
> 若只允许换补充 ⇒ 上传补充 + 正文按信中所述只改 5 个数字（改动与 `main_corrected.pdf` 相同）。
>

"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    hp = io.open(HANDOFF, encoding="utf-8").read()
    if MARK in hp:
        print("  already recorded")
        return 0
    if not a.apply:
        print("  (dry run)")
        return 0

    i = hp.find("# 项目交接文档")
    j = hp.find("\n", i)
    hp = hp[: j + 1] + "\n" + ENT + hp[j + 1:]
    io.open(HANDOFF, "w", encoding="utf-8", newline="").write(hp)

    mp = io.open(MAP, encoding="utf-8").read()
    row = ("20. 📤 **P3 替换件申请已发 EM（2026-10-15 14:10）** —— 通过 Editorial Manager 查询表单发出，"
           "表单页脚确认稿号 **PRLETTERS-D-26-02378R1**；正文与我准备的文本逐字一致。请求替换正文+补充两份文件，"
           "理由是 **4 个节号 + 1 个区间指针错** 与 **补充里 7 处畸形交叉引用**（其中 S2 表、S3 图**根本不存在**）；"
           "**声明不影响任何结果/数字/图/结论**。替换件已就绪："
           "`SUBMISSION/P3_PRL_revision/CORRECTED_2026-10-15/`（main **10 页**、supplementary **5 页**，"
           "`_p893` → CORRESPONDENCE VERIFIED）。文本 `SUBMISSION/P3_PRL_revision/EMAIL_TO_EM_2026-10-15.txt`"
           "（已去 Subject 行、按 80 列重排）。**下一步=等编辑部回复**。详见 `HANDOFF.md` 顶部 2026-10-15 14:10 条目。\n")
    anchor = "19. ✅ **P3 正文↔补充材料对应关系已修好"
    idx = mp.find(anchor)
    if idx >= 0:
        end = mp.find("\n", idx)
        mp = mp[: end + 1] + row + mp[end + 1:]
        io.open(MAP, "w", encoding="utf-8", newline="").write(mp)
    else:
        print("  WARN: map item 19 not found")

    h2 = io.open(HANDOFF, encoding="utf-8").read()
    for k in ("替换件申请已通过", "PRLETTERS-D-26-02378R1", "孤字换行", "CORRECTED_2026-10-15"):
        print(f"  {'OK ' if k in h2 else 'BAD'} handoff::{k}")
    print(f"  HANDOFF lines = {len(h2.splitlines())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
