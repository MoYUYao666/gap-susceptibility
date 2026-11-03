# -*- coding: utf-8 -*-
r"""Record the P3 numbering conversion (corollaries as corollaries, lemma by section).

    python tools/_p914_record_p3_numbering.py [--apply]
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HANDOFF = REPO / "HANDOFF.md"
MAP = REPO / "文件地图.md"
MARK = "P3 编号体系已改对"

ENT = """> **🔢 2026-10-15 14:30 —— P3 编号体系已改对（Corollary 1–5 成为真环境；Lemma III.1）**
>
> 操作者指令：**「改对」**（针对我上一条列出的两项保留项）。
>
> ### 一、✅ 五条 Corollary 从「小节标题」变成真正的 corollary 环境
>
> | 原（印刷）| 现（印刷）|
> |---|---|
> | `III.D. Corollary 1: First-Order Gradient Flow` | 小节 **`D. First-Order Gradient Flow`** + **`Corollary 1 (First-Order Gradient Flow).`** |
> | `III.E. Corollary 2: Optimal Allocation` | **`Corollary 2 (Optimal Allocation).`** |
> | `III.F. Corollary 3: Alignment Phase Transition` | **`Corollary 3 (Alignment Phase Transition).`** |
> | `III.G. Corollary 4: Cross-Architecture Transfer` | **`Corollary 4 (Cross-Architecture Transfer).`** |
> | `III.H. Corollary 5: Paper 2 as Retrieval Specialization` | **`Corollary 5 (Paper 2 as Retrieval Specialization).`** |
>
> **编号刻意保持 1–5**：`\\newtheorem{corollary}{Corollary}` **另立计数器**（不挂 `[section]`、也不挂
> `[theorem]`），因为**正文与补充材料里已有的"Corollary 4/5"就是按 1–5 手写的**——
> 若挂 `[section]` 会变成 `III.1…III.5` 并**连带改补充材料**。
>
> 正文里手写的 `Corollary~4`（`theory.tex` **2 处**）、`Corollary~5`（`appendix.tex` 1 处）已全部改成
> **`\\ref{}`**；`Corollaries~1 and 2` 改成 `Corollaries~\\ref{cor:gradient-flow} and~\\ref{cor:optimal}`。
> 新增 label：`cor:gradient-flow`、`cor:optimal`、`cor:phase-transition`、`cor:transfer`、
> `cor:retrieval-specialization`。
>
> ### 二、✅ Lemma 改为按节编号：`Lemma III.1.1` → **`Lemma III.1`**
>
> `\\newtheorem{lemma}{Lemma}[section]`（原为 `[theorem]`）。**Theorem 编号未变**（III.1 表示定理、III.2 投影误差界）。
>
> ### 三、⚠️ 顺带修掉两处我自己造成的副作用
>
> | # | 问题 | 修法 |
> |---|---|---|
> | ① | Corollary 3 的**陈述与其后散文重复**（包成环境后同一句出现两次）| `tools/_p909`：删掉散文里那句，段落改为从 "Below $r_c$ LoRA capacity cannot …" 起 |
> | ② | 补充材料里出现 **`Corollary 5 of the main text of the main text of the main text …`**（替换脚本跑了两次）| `tools/_p911`：正则折叠为 `Corollary~5 of the main text`；同时把 `Lemma~2` 改为 **`Lemma~III.1`**（引理改了编号，补充材料要跟）|
>
> ### 四、✅ 复核（`tools/_p910_p3_numbering_check.py`，从 PDF 读）
>
> | 项 | 结果 |
> |---|---|
> | 正文印刷的编号 | corollaries **1–5**、lemma **III.1**、theorems **III.1/III.2** |
> | 旧形态残留 | `Lemma III.1.1` / `Corollary 1: First-Order` / `Corollary 5: Paper`：**均 0** |
> | 未解析引用 | main **0**、supplement **0**（两份均无 `??`）|
> | 补充材料手写指针 | `Lemma III.1 of the main text` ✅、`Corollary 5 of the main text` ✅、无重复尾巴 ✅ |
> | 判定 | **NUMBERING CONSISTENT** |
> | 编译 | `main.pdf` **10 页**、`main_full.pdf` **13 页**、`main_10pp.pdf` **10 页**，三份**均 0 错误 / 0 未定义引用 / 0 未定义引文**；supplement **5 页**同上 |
> | 逐条对应 | `tools/_p893` → **CORRESPONDENCE VERIFIED** |
>
> ### 五、✅ 交付件已刷新 + 申请文本已补记
>
> * `SUBMISSION/P3_PRL_revision/UPLOAD_2026-10-15/`：四个 PDF **已用最终版刷新**（默认名与稿号名 SHA-256 相同）；
> * `EMAIL_TO_EM_2026-10-15.txt`：**新增一段**，向编辑部说明替换件**另含三处排版更正**
>   （定理头空格、corollary 环境化、链接框去除），并**声明不改任何结果/数字/表/图**；已按 80 列重排
>   （`tools/_p913`）。⚠️ **已发出的 EM 查询无法编辑**——此段供**后续回复或补充说明**使用。
>
> **工具**：`_p907`（环境化+计数器）｜`_p908`（三变体编译审计）｜`_p909`（去重）｜`_p910`（编号复核）｜
> `_p911`（补充材料指针）｜`_p912`（申请文本补记）｜`_p913`（80 列重排）｜`_p914`（本条落账）。
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
    row = ("23. 🔢 **P3 编号体系已改对（2026-10-15 14:30）** —— 五条 Corollary 由「小节标题」改为真 "
           "`corollary` 环境（**编号仍 1–5**，`\\newtheorem{corollary}{Corollary}` 另立计数器，避免牵动补充材料）；"
           "`Lemma III.1.1` → **`Lemma III.1`**（改 `[section]`）；正文手写的 `Corollary~4/5` 改 `\\ref{}`。"
           "顺带修 `_p909`（Corollary 3 陈述与散文重复）、`_p911`（补充材料 `of the main text` 重复三次 + "
           "`Lemma~2`→`Lemma~III.1`）。复核 `tools/_p910_p3_numbering_check.py` → **NUMBERING CONSISTENT**；"
           "三份主稿 10/13/10 页、supplement 5 页，**均 0 错误 0 未定义引用**；`_p893` → CORRESPONDENCE VERIFIED。"
           "交付件已刷新；申请文本补记三处排版更正。详见 `HANDOFF.md` 顶部 2026-10-15 14:30 条目。\n")
    anchor = "22. 🔤 **P3 缩进已核 + 三处渲染缺陷已修（2026-10-15 14:25）**"
    idx = mp.find(anchor)
    if idx >= 0:
        end = mp.find("\n", idx)
        mp = mp[: end + 1] + row + mp[end + 1:]
        io.open(MAP, "w", encoding="utf-8", newline="").write(mp)
    else:
        print("  WARN: map item 22 not found")

    h2 = io.open(HANDOFF, encoding="utf-8").read()
    for k in ("编号体系已改对", "Corollary 1 (First-Order Gradient Flow)", "Lemma III.1", "NUMBERING CONSISTENT"):
        print(f"  {'OK ' if k in h2 else 'BAD'} handoff::{k}")
    print(f"  HANDOFF lines = {len(h2.splitlines())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
