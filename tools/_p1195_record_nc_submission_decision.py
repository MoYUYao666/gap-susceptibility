# -*- coding: utf-8 -*-
r"""Record the Neurocomputing submission decision and the pre-submission fixes.

    python tools/_p1195_record_nc_submission_decision.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HANDOFF = REPO / "HANDOFF.md"
MAP = REPO / "文件地图.md"
README = REPO / "paper合" / "NC_submission" / "README.md"

ENT = """> **📮 2026-10-18 投稿决策（2026-10-17 23:59 记录）—— 明天投 Neurocomputing**
>
> 操作者决定：**2026-10-18 投 Neurocomputing**（Paper A）。本轮为投前收尾，未改动科学内容。
>
> ### 一、投前修正（2 处）
>
> | 缺陷 | 处理 | 验证 |
> |---|---|---|
> | 两封揭示函仍写 **"383 experiments"** | 改为 **317**（与正文一致）| 重编译后 `cover_letter_nc.pdf` / `cover_letter.pdf` 均 3 页，`383 experiments` = 0、`317` = 1 |
> | **`Cover Letter.pdf` 未被包脚本刷新**（旧文件 125.9 KB，仍是 383 版）| 包脚本补上门户名映射：`highlights_nc.*→Highlights.*`、`cover_letter_nc.pdf→Cover Letter.pdf` | 现为 **128,947 B**，含 317、无 383 |
>
> 附注：稿件 PDF 里 `383` 唯一出现处是梯度范数 **0.383**（合法数值，非计数）。
>
> ### 二、投稿包最终状态（`paper合/NC_submission/`，全部实测）
>
> | 文件 | 状态 |
> |---|---|
> | `Manuscript.pdf` | **70 页**、1,020,808 B；317 出现 2 次、无 "383 experiments" |
> | `Cover Letter.pdf` | **3 页**、128,947 B；含 **P1 被 PR 拒稿的完整披露**（`PR-D-26-10149`）与另 4 篇相关稿件 |
> | `Highlights.pdf` / `.txt` | **5 条**，55–62 字符（≤85 合规）|
> | `latex_source.zip` | **45 个文件**、1.30 MB；临时目录**独立编译 70 页一致** |
>
> ### 三、合规终检（全部通过）
>
> | 条款 | 结果 |
> |---|---|
> | 摘要 ≤250 词 | **209 词** ✅ |
> | Highlights 单独文件、3–5 条、≤85 字符 | **5 条**，最长 62 ✅ |
> | 声明在参考文献之前 | Data availability@95672 < References@120552 ✅ |
> | 编译 | 0 错误 / 0 未定义引用/引文 / 0 Overfull / 0 float-too-large ✅ |
> | 数字一致性 | 正文与揭示函统一 **317 = 221 + 96**；双台账 **76/76**、**96/96** ✅ |
>
> ### 四、上传对照（明日按此提交）
>
> | 门户 slot | 文件 |
> |---|---|
> | Manuscript | `Manuscript.pdf` |
> | Highlights | `Highlights.pdf` 或 `Highlights.txt` |
> | Cover Letter | `Cover Letter.pdf` |
> | LaTeX source（如被要求） | `latex_source.zip` |
>
> ⏰ 已建一条 **2026-10-18 09:00** 的会话内提醒（注明：定时任务属会话作用域，若明日新开会话则不触发，需看本条目）。
>
> **待办（明日）**：上传后**记录稿号**到 `HANDOFF.md` 与 `文件地图.md`。
>

"""

MAPROW = ("62. 📮 **Paper A 投稿：2026-10-18 投 Neurocomputing（已定）** —— 包已就绪：`Manuscript.pdf` **70 页**、"
          "`Cover Letter.pdf` **3 页**（含 P1 被 PR 拒稿的完整披露）、`Highlights` 5 条 ≤62 字符、`latex_source.zip` 45 文件"
          "（独立编译 70 页一致）。投前修掉揭示函的 383 experiments→**317**，并补上门户名映射（此前 `Cover Letter.pdf` "
          "未被刷新）。合规：摘要 **209 词**、声明在参考文献之前、0 错误/0 未定义/0 Overfull。"
          "**明日上传后须把稿号记入本文件与 `HANDOFF.md`。**\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  (dry run)")
        return 0
    h = io.open(HANDOFF, encoding="utf-8").read()
    if "明天投 Neurocomputing" not in h:
        i = h.find("# 项目交接文档")
        j = h.find("\n", i)
        io.open(HANDOFF, "w", encoding="utf-8", newline="").write(h[: j + 1] + "\n" + ENT + h[j + 1:])
        print("  handoff entry added")
    m = io.open(MAP, encoding="utf-8").read()
    if "投 Neurocomputing（已定）" not in m:
        anchor = "61. 🧮 **ODE 计数对账"
        idx = m.find(anchor)
        if idx < 0:
            print("  !! map anchor missing")
            return 1
        end = m.find("\n", idx)
        io.open(MAP, "w", encoding="utf-8", newline="").write(m[: end + 1] + MAPROW + m[end + 1:])
        print("  map row added")
    # keep the package README's page count honest
    if README.exists():
        r = io.open(README, encoding="utf-8").read()
        r2 = re.sub(r"\| Manuscript \| `Manuscript\.pdf` \| [^|]*\|",
                    "| Manuscript | `Manuscript.pdf` | **70 页**（2026-10-17 构建）；含作者信息与全部声明 |", r)
        if r2 != r:
            io.open(README, "w", encoding="utf-8", newline="").write(r2)
            print("  package README page count synced")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
