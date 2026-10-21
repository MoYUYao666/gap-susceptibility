# -*- coding: utf-8 -*-
r"""Record the P3 soundness-hardening / PRL-resubmission round."""
from __future__ import annotations

import io
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HANDOFF = os.path.join(REPO, "HANDOFF.md")
MAP = os.path.join(REPO, "文件地图.md")
EVID = os.path.join(REPO, "docs", "EVIDENCE_MAP_2026-10-19.md")

ENTRY = """> **🔧 2026-10-21 17:00 —— P3 拒稿后 soundness 加固完成（PRL 再投方案就绪，等你确认）**
>
> 按"路线 1：全部改完再投 PRL"执行，未执行任何投稿动作。加固清单：
>
> | # | 加固 | 位置 |
> |---|---|---|
> | 1 | **claim-status 表**：逐条列"支持 / 不支持 / 仅边界"（负结果成为正文内容）| 补充 **S17** `tab:claims` |
> | 2 | 临界点统计：5 seeds（−23.0±22.3 vs +65.5±38.5）、精确置换 **p=0.008** | 正文 + **S14** |
> | 3 | 协议窗口：r=5 在 n=12 测得 −39.5（默认 n=20 为 −10.5）⇒ 符号边界稳定、幅度变化 | **S16** |
> | 4 | 真实图像对照数字写入 conclusion（instruction +83.0 vs −7.5；caption +66.5 vs −39.5）| 正文 + S7 |
> | 5 | 可用性声明修正：删除 "code upon request" → 公开仓库 + 版本 DOI | conclusion |
> | 6 | 标题副标题重定向：*Identifiability, Negative Results, and Protocol Dependence* | main.tex |
> | 7 | S11 与正文一致：旧两 seed p=0.33 → 五 seed p=0.008 | 补充 S11 |
>
> 结果：正文 **10 页**、补充 **8 页**；`audit_check`/`audit_pdf` **0/0**；新 **cover letter**
> `paper3/paper_ieee/cover_letter_prl_resubmission.pdf`（2 页，含前稿号披露与 5 项改动）；P3 包已重建（10 页 + 8 页 +
> resubmission 信）；五包 staged **1:1**。方案文档：`docs/P3_RESUBMISSION_PLAN_2026-10-21.md`。
>
> **待你决定**：是否按 PRL 新投稿提交（同意后由你通过 EM 提交；备选 SCI：Neural Networks / IVC / KBS）。
>

"""

ROW = ("133. 🔧 **P3 加固 + PRL 再投方案（2026-10-21 17:00）** —— 7 项 soundness 加固（S17 claim-status、5-seed p=0.008、"
       "S16 协议窗口、真实图像数字入 conclusion、可用性声明修正、标题副标题重定向、S11 一致性）；正文 10 页 + 补充 8 页；"
       "resubmission cover letter 2 页；审计 0/0；五包 staged 1:1；**未投稿，待操作者确认**。\n")

EVID_ROWS = """| `docs/P3_RESUBMISSION_PLAN_2026-10-21.md` | P3 拒稿后改投方案（PRL 新投稿 + 备选 SCI） | — |
| S17 `tab:claims` | P3 claim-status 表（支持/不支持/边界） | `docs/P3_SOUNDNESS_HARDENING_2026-10-21.md`（计划）|
"""


def main() -> int:
    h = io.open(HANDOFF, encoding="utf-8").read()
    if "P3 拒稿后 soundness 加固完成" not in h:
        i = h.find("# 项目交接文档")
        j = h.find("\n", i)
        io.open(HANDOFF, "w", encoding="utf-8", newline="").write(h[: j + 1] + "\n" + ENTRY + h[j + 1:])
        print("  handoff updated")
    m = io.open(MAP, encoding="utf-8").read()
    if "P3 加固 + PRL 再投方案" not in m:
        anchor = "132. ❌ **P3 被 PRL 拒稿"
        idx = m.find(anchor)
        assert idx >= 0
        end = m.find("\n", idx)
        io.open(MAP, "w", encoding="utf-8", newline="").write(m[: end + 1] + ROW + m[end + 1:])
        print("  file map updated")
    e = io.open(EVID, encoding="utf-8").read()
    if "P3_RESUBMISSION_PLAN" not in e:
        io.open(EVID, "w", encoding="utf-8", newline="").write(e.rstrip() + "\n" + EVID_ROWS)
        print("  evidence map updated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
