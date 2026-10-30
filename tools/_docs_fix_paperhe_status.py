# -*- coding: utf-8 -*-
r"""更正 `文件地图.md` 里 `paper合/` 的"已归档 + 已弃用"记载（2026-10-02）。

## 为什么必须改

文件地图是"谁是谁 + 当前待办"的**唯一入口**。它目前仍写：

- L80/L84：`paper合` 于 **2026-09-24 经操作者明确弃用**
- L119：`~~paper合/`（Paper A）~~ … **已归档 + 已弃用**

但 **2026-09-24 之后的事实**是：`paper合/` 已**恢复到仓库根**（`tools/_restore_paperhe.py`，
14 个脚本按字面相对路径打开它），并在 **2026-10-01/02** 被选为**整改主稿**、跑完 SigLIP 反例、
转换成 Elsevier 模板、做出 **Neurocomputing 投稿包**（`paper合/NC_submission/`）。

**规则要求**：过期结论要**标注过期并给出新结论**，不要静默覆盖。故本脚本：
保留原文，**加删除线与过期标记**，并在其后给出新结论。

    python tools\_docs_fix_paperhe_status.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "文件地图.md"

EDITS = [
    # L80：归档说明加过期标记
    ("**已归档、不在根目录**（**2026-09-22** 移入 `备选/06_归档稿件/`",
     "~~**已归档、不在根目录**~~ ⚠️**此条已过期（2026-10-02 更正，见下）** 原记：（**2026-09-22** 移入 `备选/06_归档稿件/`"),
    # L84：paper合 行
    ("| ~~`paper合/`~~ | Paper A = P1+P2（sn-jnl，28 页，65 文件 / 7.6 MB） | 操作者 **2026-09-24** 决定**弃用该路线**（ap3 为唯一合并主线）；与其 P1 的残留重合随之不再处理 |",
     "| ~~`paper合/`~~ ⚠️**已过期**：操作者 2026-09-24 曾决定弃用（ap3 为合并主线），"
     "**但 2026-10-01 起已恢复为主稿**——见下方\"最新状态\" | Paper A = P1+P2 | 见下 |"),
    # L119：表格行
    ("| ~~`paper合/`（Paper A）~~ | P1 + P2 | Springer `sn-jnl` | 28 | **已归档 + 已弃用**（`备选/06_归档稿件/paper合/`） |",
     "| ~~`paper合/`（Paper A）~~ | P1 + P2 | **Elsevier `elsarticle`**（`main_nc.tex`；`main_springer.tex` 保留） | **39**（NC 版）/ 29（Springer 版） | ⚠️**已过期**：**2026-10-02 起为 Neurocomputing 主稿**，投稿包已就绪（`paper合/NC_submission/`） |"),
]

NEW_SECTION = """
---

## 🆕 `paper合/`（Paper A）最新状态 —— 2026-10-02 更正

> **上文"已归档 + 已弃用"的记载已过期**（保留以示历史，勿据其判断当下）。**当前事实**：

| 项 | 状态 |
|---|---|
| 位置 | **已在仓库根**（2026-09-24 经 `tools/_restore_paperhe.py` 恢复；14 个脚本按字面相对路径打开它） |
| 定位 | **Neurocomputing 主稿**（操作者 2026-10-01 选定整改目标） |
| 模板 | **Elsevier `elsarticle`**（`main_nc.tex`，`tools/_pa_to_elsarticle.py` 生成）；Springer 版 `main_springer.tex` 保留 |
| 篇幅 | NC 版 **39 页**（`elsarticle[review]` 单栏双倍行距）｜ Springer 版 29 页 |
| 编译 | 0 错误 ｜ 0 未定义引用 ｜ cites 41 / bib 41 全匹配 |
| 摘要 | **244 词**（Guide 上限 250） |
| 投稿包 | ✅ **就绪**：`paper合/NC_submission/`（Manuscript / Highlights / Cover Letter / latex_source / README） |
| 终检 | `tools/_pa_final_check_nc.py` **全绿** |
| 关键新结果 | **SigLIP 严格冻结对照方向与 CLIP 相反**（配对 t=−52.7，5/5 seeds 一致）→ 位置优势是**架构依赖**的 |
| ⏳ 待决 | **投稿时点**：实证部分与在审 P1（`PR-D-26-10149`）同源，**建议等 P1 决定** |
| 🏃 进行中 | OpenCLIP 严格冻结对照；SigLIP vision_only；严格冻结 rank sweep（见 HANDOFF 2026-10-02 条目） |

> **对 ap3 的影响**：ap3 原为"唯一合并主线"，现 `paper合` 亦为在编主稿。
> 两者的取舍**取决于 P1 的决定**（HANDOFF 2026-10-01 条目已列三种情景）。
"""


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8").read()
    n = 0
    for old, new in EDITS:
        c = t.count(old)
        if c == 1:
            print(f"  ✅ 命中：{old[:52]}…")
            if apply:
                t = t.replace(old, new, 1)
            n += 1
        else:
            print(f"  ⚠ 未命中（{c} 次）：{old[:52]}…")
    if apply and n:
        if "paper合/`（Paper A）最新状态" not in t:
            t = t.rstrip() + "\n" + NEW_SECTION
            print("  ✅ 追加『最新状态』小节")
        io.open(F, "w", encoding="utf-8", newline="").write(t)
        t2 = io.open(F, encoding="utf-8").read()
        assert "此条已过期" in t2 or "已过期" in t2
        assert "paper合/`（Paper A）最新状态" in t2
        assert "NC_submission" in t2
        print(f"  ✅ 已改并断言通过（{len(t2.splitlines())} 行）")
    else:
        print(f"  {n}/{len(EDITS)} 处可改（预演）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
