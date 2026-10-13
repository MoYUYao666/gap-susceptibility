# -*- coding: utf-8 -*-
r"""更新 `文件地图.md` 的待办：更正 #2（paper合 过期条目）+ 新增 Paper A 当前待办（2026-10-06）。

## 为什么

`文件地图.md:275` 的待办 #2 写着：

> ✅ **2026-09-24 彻底关闭**：操作者决定 **`paper合` 路线弃用**（该稿 09-22 已归档到
> `备选/06_归档稿件/paper合/`）

**但实况**：`文件地图.md:85` 已更正为"**2026-10-01 起已恢复为主稿**"，
`paper合/` 在根目录、编译 49 页、投稿包齐备。**同一文件内两处矛盾。**

（与刚修的 `AGENTS.md:18` 是同一条过期信息的两处副本。）

## 修法（按项目规则：追加、不重写；过期须标注）

1. 在 #2 后**就地追加"⚠️ 本条已过期"**，给出新结论并指向 `AGENTS.md` 与本文件的更正段；
2. 新增一条 **Paper A（`paper合/`）当前待办**，列明**已完成 / 待操作者决定 / 阻塞项**。

    python tools\_docs_fix_filemap_todo.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "文件地图.md"

ANCHOR = ("   注：若日后重启该稿，必办项（旧 116 篇目录、\"Causal Evidence\" 标题、废弃的 Adapter 旧口径、"
          "约 1,053 词重合、`tools/audit/` 路径改回）已整理在 `docs/PAPERHE_OVERLAP_RESOLUTION.md` §4。")

ADD = ANCHOR + """
   > **⚠️ 本条已过期（2026-10-06 更正）**：`paper合/` **已于 2026-10-01 恢复为主稿**（见 `L85` 与本文件
   > 「🆕 `paper合/`（Paper A）最新状态」段）。**"路线弃用"不再成立**——
   > 该稿现为**根目录的当前主稿**，2026-10-06 编译 **49 页**、`NC_submission/` 投稿包齐备。
   > 同时 **`paper_ap3/` 已归档到 `备选/06_归档稿件/`**（因含 P3，合并投出构成重复投稿）。
   > 同一过期信息的另一处副本 `AGENTS.md:18` **已于同日更正**。
2b. 🆕 **Paper A（`paper合/`）当前待办** —— 2026-10-06
   **✅ 已完成（附证据）**：图**全部改 Times New Roman + 尺寸精确对齐**（16/16 缩放 1.00×、
   `pdffonts` 实测无 DejaVu）｜ 附录 B 两张**不可读的 1×3 面板图**已**拆为 6 张单面板**并逐张目视复核 ｜
   Figure 10 **改画有效秩变化**（原图画的是恒为 0 的张量计数、**图注还写反了**）｜
   Figure 14/15 图例**移出绘图区** ｜ 图**改矢量为 PDF**，`latex_source.zip` **5.4 MB → 1.1 MB**
   （修掉打包脚本两处累积缺陷）｜ 下线图 **22 个**移入 `figures/_superseded/`
   （**只移不删**）｜ 编译 **NC 49 页 / Springer 37 页、0 错误、0 未定义引用**、无页越界、
   投稿包重建、终检全绿。
   **🔴 待操作者决定**：**目标刊**——`docs/PAPERA_VENUE_OPTIONS.md`。
   ① **同刊争议已更正**：Elsevier 的 "Co-submission" 政策讲的是**数据/方法配套短文**，
   **不禁止同刊多篇研究论文**；只要求**如实披露**。② 免 APC 且**未拒过本线工作**的候选 **5 个**：
   **KBS、ESWA、IVC、CVIU、Information Fusion**。③ 另需 **P1（`PR-D-26-10149`）的决定**——
   它决定投稿时点。
   **⏳ 阻塞项**：候刊 **Guide for authors PDF**（优先 **KBS、ESWA、CVIU**；IVC 已有存档
   `期刊指南/_guide_ivc.txt`）——**无官方 Guide 无法产出符合本项目标准的对比表**
   （ScienceDirect 官方页 HTTP 403、第三方站 HTTP 429/口径不一，**按规则不用第三方数字填空**）。"""


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8").read()
    if "本条已过期（2026-10-06 更正）" in t:
        print("  已更新，跳过")
        return 0
    c = t.count(ANCHOR)
    if c != 1:
        print(f"  ⚠ 未唯一命中（{c} 次）")
        return 1
    print("  ✅ 命中待办 #2 锚点")
    if apply:
        t2 = t.replace(ANCHOR, ADD, 1)
        io.open(F, "w", encoding="utf-8", newline="").write(t2)
        t3 = io.open(F, encoding="utf-8").read()
        for k in ("⚠️ 本条已过期（2026-10-06 更正）", "paper合/`）当前待办",
                  "5.4 MB → 1.1 MB", "不禁止同刊多篇研究论文", "KBS、ESWA、IVC、CVIU"):
            assert k in t3, f"断言失败：缺 {k}"
        print(f"  ✅ 已更新并断言通过（{len(t3.splitlines())} 行）")
    else:
        print("  （预演）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
