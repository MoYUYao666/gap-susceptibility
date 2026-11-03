# -*- coding: utf-8 -*-
r"""Refresh the stale residual-risk section after the ODE-count decision.

`docs/PAPERA_REVISION_SPEC.md` §8.5 still says the 383/162 ODE gap is unresolved and that the submission window is
blocked by A1's Neurocomputing deadline. Both statements are now out of date: the paper adopts the 96 archived fits
(383 -> 317, recorded in _p1179/_p1180), and A1 was transferred to Neural Networks, which removes the same-journal
constraint. History is kept; the new state is appended rather than overwritten.

    python tools/_p1191_refresh_residual_risks.py [--apply]
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SPEC = REPO / "docs" / "PAPERA_REVISION_SPEC.md"
COV = REPO / "docs" / "PAPERA_PR_REVIEW_COVERAGE_2026-10-17.md"

NOTE = """
> **🔄 2026-10-17 23:20 更新（以下三条按最新事实改写，原文保留在上方作历史）**
>
> | 项 | 最新状态 |
> |---|---|
> | 383 / 162 个 ODE 拟合 | **已结案**：归档只有 96 条逐 run 记录（+111 条全量轨迹见 `ode_ledger_all.json`），操作者选定 96 口径 ⇒ 正文改为 **317 = 221 + 96**、α 符号统一为 **92/96**（脚本 `_p1176`–`_p1180`；`HANDOFF.md` 22:20 条目）|
> | 目标刊与投稿时点 | **约束已变**：A1 已转投 **Neural Networks**（不再与 Neurocomputing 同刊），P1 已拒。因此原"避开 A1 的 11-08 确认期"理由**消失**；Paper A 的 Neurocomputing 投稿时点现在**只由操作者决定**，包已就绪（70 页 NC / 50 页 Springer，台账 76/76）|
> | 解码器两实验符号相反 | 仍为本轮无法分离的归因问题，正文已如实限定（不变）|
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  (dry run)")
        return 0
    t = io.open(SPEC, encoding="utf-8").read()
    if "以下三条按最新事实改写" not in t:
        anchor = "### 8.6 第二轮一致性修复"
        i = t.find(anchor)
        if i < 0:
            print("  !! anchor not found")
            return 1
        io.open(SPEC, "w", encoding="utf-8", newline="").write(t[:i] + NOTE.strip() + "\n\n" + t[i:])
        print("  §8.5 note appended")
    c = io.open(COV, encoding="utf-8").read()
    if "评审建议落实情况（23:20 复核）" not in c:
        tail = """

## 六、评审建议落实情况（2026-10-17 23:20 复核）

| 建议 | 状态 | 证据 |
|---|---|---|
| ① 局限节补替代解释 | **已落实** | `discussion.tex` Thirteenth：「Regularisation strength」/「correlational」/「not as an established mechanism」三处均命中 |
| ② 补充补配置对照表 | **已落实** | `supplement.tex` A.1 + `tab:config_groups`，四组齐全，正文 `empirical.tex` 有 `\\ref` |
| ③ `+0.079` 根因改写 | **已落实** | `empirical.tex`：「degenerate fit」+「validation loss of $2.33$」 |

复核脚本：`tools/_p1182_audit_against_pr_review.py`（构造命中）、本文件五点五节（数值依据）。
"""
        io.open(COV, "w", encoding="utf-8", newline="").write(c.rstrip("\n") + tail)
        print("  coverage doc status table appended")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
