# -*- coding: utf-8 -*-
r"""更正 `AGENTS.md` 里关于 `paper合/` 的**过期条目**（2026-10-06）。

## 问题

`AGENTS.md:18` 仍写：

> 已归档、不再推进：`备选/06_归档稿件/paper合/`（Paper A，**已弃用**）、`paper_a4/`

但实况：

- `paper合/` **在根目录**，编译 **49 页**，`NC_submission/Manuscript.pdf` 齐备；
- `文件地图.md:85` 已更正：**"⚠️ 已过期：操作者 2026-09-24 曾决定弃用（ap3 为合并主线），
  但 2026-10-01 起已恢复为主稿"**；
- `paper_ap3/` 反而**在 `备选/06_归档稿件/`**（因含 P3，重复投稿风险）。

**→ `AGENTS.md` 的这条与 `文件地图.md` 直接冲突**，且违反项目规则
「过期结论要**标注过期并给出新结论**，不要静默覆盖/留存」。

## 修法

按"追加不重写 + 标注过期"的原则改写该行，并让 `AGENTS.md` 的目录表与实况一致。

    python tools\_docs_fix_agents_stale.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
A = REPO / "AGENTS.md"

OLD = "- 已归档、不再推进：`备选/06_归档稿件/paper合/`（Paper A，**已弃用**）、`paper_a4/`"

NEW = ("> **⚠️ 本节已于 2026-10-06 更正（原条目过期）**\n"
       "> 原记：\"已归档、不再推进：`备选/06_归档稿件/paper合/`（Paper A，**已弃用**）、`paper_a4/`\"\n"
       "> **实况**：`paper合/` **在根目录且为当前主稿**——2026-09-24 曾决定弃用（改以 ap3 为合并主线），\n"
       "> 但 **2026-10-01 起恢复为主稿**；截至 2026-10-06 编译 **49 页**，`NC_submission/` 投稿包齐备。\n"
       "> 反而 **`paper_ap3/` 已在 `备选/06_归档稿件/`**——因其**含 P3 内容**（P3 正投 PRL），\n"
       "> 合并投出构成重复投稿。权威状态见 `文件地图.md`（冲突时以它为准）。\n"
       "> **仍未推进**：`paper_a4/`。")

OLD_L15 = "- `paper/` Paper 1（PR，elsarticle）；`paper_a1/` A1（Neurocomputing）；`paper_a2/` A23（海洋/声呐，IEEE JOE `26-0663`）；`paper_ap3/` ap3（**唯一合并主线**，P1+P2+P3，待 P1 出决定）；`paper3/paper_ieee/` Paper 3（TNNLS，已拒）"

NEW_L15 = ("- `paper/` Paper 1（PR，elsarticle，`PR-D-26-10149`）；`paper_a1/` A1（Neurocomputing，`NEUCOM-D-26-20952`）；"
           "`paper_a2/` A23（海洋/声呐，IEEE JOE `26-0663`）；**`paper合/` Paper A = P1+P2（当前主稿，目标 Neurocomputing）**；"
           "`备选/06_归档稿件/paper_ap3/` ap3（P1+P2+P3，**因含 P3 不可投**，已归档）；`paper3/paper_ieee/` Paper 3（TNNLS 已拒 → 改投 PRL `PRLETTERS-D-26-02378`）")


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(A, encoding="utf-8").read()
    n = 0
    for old, new, why in ((OLD_L15, NEW_L15, "目录行（补 paper合 与真实刊号）"),
                          (OLD, NEW, "归档行（标注过期 + 给新结论）")):
        c = t.count(old)
        if c == 1:
            print(f"  ✅ {why}")
            if apply:
                t = t.replace(old, new, 1)
            n += 1
        else:
            print(f"  ⚠ {why}：命中 {c} 次")
    if apply and n:
        io.open(A, "w", encoding="utf-8", newline="").write(t)
        t2 = io.open(A, encoding="utf-8").read()
        assert "已弃用**）、`paper_a4/`" not in t2, "旧条目仍在"
        for k in ("已于 2026-10-06 更正", "2026-10-01 起恢复为主稿", "因含 P3 不可投", "NEUCOM-D-26-20952"):
            assert k in t2, f"断言失败：缺 {k}"
        print(f"  ✅ 已改 {n} 处并断言通过")
    else:
        print(f"\n  {n}/2（{'预演' if not apply else '部分失败'}）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
