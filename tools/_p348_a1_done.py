# -*- coding: utf-8 -*-
r"""修正 `_p347` 的第 8 项误判，并落账 A1 状态（2026-10-12）。

## 误判原因（我的错）

`_p347` 把 "four decimals 出现 0 次" 当作 item 8 完成的判据。但稿中那处 `four decimals`
**用在另一个量上**：

> $\tau$ ... the bias-field Pearson is $1.0000$ **to four decimals** in every seed, not exactly
> $1$ (stored mean $0.9999917$, sd $5.5\times10^{-7}$)

→ 归档 `outputs/a1_multiseed.json` 的 `0.9999917` **确实是四位小数** → **该表述正确，不该改**。

而 item 8 真正要改的目标（`$r{=}1.000$` 的精度声明）已在 `main.tex:33` 用
**"matches measurement to three decimals ($r{=}1.000$)"** 正确表述。

→ **A1 的 10 项执行清单全部完成**（9 项直接通过 + item 8 经复核实为已完成）。

    python tools\_p348_a1_done.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **✅ 2026-10-12（续）—— A1（`paper_a1/`）的改写执行清单**全部完成**；A1 已达到可投状态**
>
> ### 判据来源
>
> `docs/A1_REFRAME_PLAN.md` §四 的 10 项清单，**逐条在稿中找证据核实**
> （不按时间戳推断）；核实脚本 `tools/_p347_verify_a1_done.py`。
>
> | # | 清单项 | 核实结果 |
> |---|---|---|
> | 1 | 按组内 τ 结果定标题 | ✅ 已定：*Order Preservation Tracks Zero-Shot Accuracy under Classification Fine-Tuning: Why the Modality Gap Is Not a Universal Health Metric*（**不再承诺 monitor**） |
> | 2 | 组内 n=30 重算 τ | ✅ 已完成（`tools/_p218`/`_p219`；100 个逐 epoch 检查点） |
> | 3 | 组内（within-dataset）分析写入 | ✅ 稿中 4 处 |
> | 4 | 摘要首句改 "necessary, not sufficient" | ✅ `main.tex` 摘要 |
> | 5 | "zero-overhead monitor" 改写 | ✅ 稿中 **0 处** |
> | 6 | 写入数据集混杂（Simpson） | ✅ 已写入 |
> | 7 | `highlights.tex` 的 r=1.000 加限定 | ✅ `1.000` 在 highlights 中 **0 处**，且含限定词 |
> | 8 | "four decimals" → "three decimals"（0.0019） | ✅ **已完成**；稿中另有一处 `four decimals` 用在**别的量**上（多 seed Pearson $1.0000$，归档 `0.9999917`，**确为四位小数**）→ **正确，不改** |
> | 9 | 检索表述按自家数据修正 | ✅ 摘要含 *"…the gap the better retrieval one, giving a task-sensitivity ordering (centroid < zero-shot < retrieval)"* |
> | 10 | 摘要/正文同步 + 重编译 + 门禁 | ✅ **42 页**，**0 错误 / 0 未定义** |
>
> ### ⚠️ 我的一处误判（本阶段第 8 个错）
>
> `_p347` 把 "`four decimals` 出现 0 次" 当作 item 8 的完成判据 → 误报 🔴。
> 实际那处用在**另一个量**上且**数值正确**（`0.9999917` 确为四位小数）。
> **教训重申：判据必须绑定"目标量"而非"字符串出现次数"。**
>
> ### A1 当前就绪度
>
> | 项 | 值 |
> |---|---|
> | 目录 | `paper_a1/` |
> | 模板 | `\\documentclass[review,authoryear]{elsarticle}` |
> | `\\journal{}` | **Neural Networks** |
> | 页数 / 编译 | **42 页**，0 错误 / 0 未定义 |
> | 摘要 | **249 词** |
> | 投稿件 | `main.tex` / `cover_letter.tex` / `declaration.tex` / `highlights.tex` / `abstract.tex`（均 2026-10-11 23:13–23:14 生成 PDF） |
> | 稿内刊名残留 | 仅 2 处 **参考文献**里的 `Pattern Recognition Letters`（参考文献条目，**正确，不该改**） |
> | **状态** | ✅ **改完，可投**（走 Elsevier ATS 转投，**须 2026-11-08 23:59 前确认**） |
>
> ### `paper合`（Paper A）与 A1 的分工（当前安排）
>
> | 稿 | 状态 | 下一步 |
> |---|---|---|
> | **`paper合`（Paper A = P1+P2 合并）** | **从未投稿**；PR 对 P1 的全部意见已改入（26/26 核验通过）；NC **60 页** / Springer **44 页**，0 错 | **待操作者决定投稿时点与目标刊**（就地缘关系需披露与 A1 的关系） |
> | **`paper_a1`（A1）** | **改完可投**；目标 **Neural Networks**（ATS 转投） | **须在 2026-11-08 前确认 ATS 转投** |
>
> **注意**：Paper A 与 A1 是**不同的工作线**（Paper A = P1+P2 的 gap 动力学；A1 = τ 秩序保持
> 与零样本一致性）。**A1 投出不需要等 Paper A。**
"""


def main() -> int:
    if "--apply" not in sys.argv:
        print("  （预演）")
        return 0

    # 1) 修 _p347 的第 8 项判据
    p347 = REPO / "tools" / "_p347_verify_a1_done.py"
    t = io.open(p347, encoding="utf-8").read()
    old = ('    checks.append(("8 \'four decimals\' 已改（应为 0，且 \'three decimals\' >0）",\n'
           '                   fd == 0, f"four={fd} ｜ three={td}"))')
    new = ('    # item 8 的判据必须绑定「目标量」（摘要里 $r{=}1.000$ 的精度声明），\n'
           '    # 而不是「four decimals 出现次数」——稿中另有一处 four decimals 用在\n'
           '    # 多 seed Pearson $1.0000$（归档 0.9999917）上，那句话是正确的。\n'
           '    hdr = ab[:600]\n'
           '    checks.append(("8 摘要精度声明已改（three decimals 且无 four decimals）",\n'
           '                   ("three decimals" in hdr) and ("four decimals" not in hdr),\n'
           '                   "摘要内 three=" + str(hdr.count("three decimals")) + " ｜ "\n'
           '                   "全文 four=" + str(fd) + "（另一处用在多 seed Pearson，正确）"))')
    if old in t:
        io.open(p347, "w", encoding="utf-8", newline="").write(t.replace(old, new))
        print("  ✅ _p347 的第 8 项判据已修正")
    else:
        print("  ⚠️ _p347 判据未匹配，需人工处理")

    # 2) HANDOFF
    hp = REPO / "HANDOFF.md"
    h = io.open(hp, encoding="utf-8").read()
    if "A1（`paper_a1/`）的改写执行清单**全部完成**" in h:
        print("  HANDOFF 已记录")
    else:
        i = h.find("# 项目交接文档")
        j = h.find("\n", i)
        io.open(hp, "w", encoding="utf-8", newline="").write(h[:j + 1] + "\n" + ENT + h[j + 1:])
        print("  ✅ HANDOFF 已追加")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
