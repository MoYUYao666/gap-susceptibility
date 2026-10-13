# -*- coding: utf-8 -*-
"""把 P3 的投稿结果（PRLETTERS-D-26-02378）同步进所有记录 P3 状态的文档。

一次性脚本（幂等：已同步过的文件会报 SKIP）。
    python tools/_sync_p3_submission_status.py
"""
from __future__ import annotations

import io
import pathlib

REPO = pathlib.Path(__file__).resolve().parents[1]

MS = "`PRLETTERS-D-26-02378`"
DATE = "2026-09-26 16:22"

EDITS: list[tuple[str, str, str]] = [
    (
        "docs/FAST_PUBLICATION_PLAN.md",
        '| **P3**（`paper3/paper_ieee/`） | IEEE TNNLS **已拒，明确"不要再投修改版"** | ✅ **可以，且无任何冲突** | 无 |',
        '| **P3**（`paper3/paper_ieee/`） | IEEE TNNLS **已拒，明确"不要再投修改版"** | ✅ **已完成改投**：'
        f'**{MS}（Pattern Recognition Letters，{DATE}）** | 无 |',
    ),
    (
        "docs/FAST_PUBLICATION_PLAN.md",
        "- **P3 是唯一无冲突稿件**（TNNLS 已拒、明确不要修改版）→ 改投**不触发**重复投稿问题。",
        "- **P3 是唯一无冲突稿件**（TNNLS 已拒、明确不要修改版）→ 改投**不触发**重复投稿问题。\n"
        f"  ✅ **已于 {DATE} 投出：{MS}（Pattern Recognition Letters，Regular Article）**。\n"
        "  **6 个月时钟自此起算（至 2027-03-26）**，首轮决定预计 2026-12 上旬。",
    ),
    (
        "docs/OA_FUNDING_ROUTES.md",
        "| **P3** | IEEE TNNLS（已拒） | ❌ 同上；改投 Elsevier/Springer 系即落入 ① |",
        f"| **P3** | 🆕 **Pattern Recognition Letters**（{MS}，{DATE} 投；前身 TNNLS 已拒） | "
        "✅ **落入 ①：Elsevier hybrid + 作者为 Southampton 身份 → APC £0**（协议覆盖，见 §2.1） |",
    ),
    (
        "docs/P3_PRL_RETARGET.md",
        '> 目标：**6 个月内见刊、APC £0**。P3 是唯一无在投冲突的稿件（TNNLS 已拒，明确"不要再投修改版"）。',
        '> 目标：**6 个月内见刊、APC £0**。P3 是唯一无在投冲突的稿件（TNNLS 已拒，明确"不要再投修改版"）。\n'
        f"> ✅ **结果：已于 {DATE} 投出 —— {MS}（Pattern Recognition Letters，Regular Article）**。",
    ),
]


def main() -> int:
    n_ok = n_skip = n_miss = 0
    for rel, old, new in EDITS:
        p = REPO / rel
        t = io.open(p, encoding="utf-8").read()
        if new in t:
            print(f"SKIP : {rel}（已同步）")
            n_skip += 1
            continue
        if old not in t:
            print(f"MISS : {rel} | 未找到目标文本：{old[:50]}…")
            n_miss += 1
            continue
        io.open(p, "w", encoding="utf-8", newline="").write(t.replace(old, new, 1))
        print(f"OK   : {rel}")
        n_ok += 1
    print(f"\n合计：同步 {n_ok}／已同步 {n_skip}／未命中 {n_miss}")
    return 1 if n_miss else 0


if __name__ == "__main__":
    raise SystemExit(main())
