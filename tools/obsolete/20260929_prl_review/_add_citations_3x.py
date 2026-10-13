# -*- coding: utf-8 -*-
r"""第四轮：为 §3.4–§3.6 补上支撑引用（此前这三节零引用却断言"文献没做 X"）。

诊断依据：`tools/_manuscript_diagnostics.py` 显示 §3.4/§3.5/§3.6 引用密度为 0.0/千词，
而它们各自断言"文献未系统区分/未报口径/未说清冻结范围"——**无引用的否证式断言最易被审稿人攻击**。
库中已有对口文献（数值稳定性 4 篇、方差与统计效力 5 篇），直接挂到既有句子上，不增篇幅。

    python tools/_add_citations_3x.py [--apply]
"""
from __future__ import annotations

import io
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MD = REPO / "paper_review_prl" / "MANUSCRIPT.md"

EDITS: list[tuple[str, str]] = [
    # §3.4：数值失效可用"低精度训练为何失败"一类工作说明实现原因确实存在
    ("it carries no information about the method. The distinction changes",
     "it carries no information about the method, and the mechanisms by which such values arise are\nstudied in their own right [qiu2025lowprecision; golden2024flashattentionstable; budzinskiy2025numerical].\nThe distinction changes"),
    # §3.5：方差报告与多种子问题有成熟文献
    ("and a reader\nrecomputing a published interval from the underlying runs can obtain a different value and conclude\nthat the paper is inconsistent when it is merely unspecified.",
     "and a reader\nrecomputing a published interval from the underlying runs can obtain a different value and conclude\nthat the paper is inconsistent when it is merely unspecified — a discrepancy of exactly the kind the\nbenchmark-variance literature warns about [bouthillier2021variance; d2020underspecification;\ndror2018significance]."),
    # §3.6：冻结范围的做法不一，有文献可依
    ("These are different interventions with different effective budgets, and the phrase\n\"frozen encoder\" does not distinguish them.",
     "These are different interventions with different effective budgets, and the phrase\n\"frozen encoder\" does not distinguish them; the same ambiguity appears in vision-language designs that\nfreeze components selectively [li2023blip2]."),
]


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(MD, encoding="utf-8").read()
    n = 0
    for old, new in EDITS:
        if old in t:
            t = t.replace(old, new, 1); n += 1
        else:
            print(f"  ⚠ 未命中: {old[:58]}…")
    keys = set()
    for m in re.finditer(r"\[([^\]\[]+)\]", t):
        if "://" in m.group(1):
            continue
        for part in re.split(r"[;,]", m.group(1)):
            k = part.strip()
            if re.match(r"^[a-z][a-z0-9_]*\d[a-z0-9_]*$", k):
                keys.add(k)
    print(f"\n补引用 {n}/{len(EDITS)} 处 ｜ 唯一 key {len(keys)} 条")
    if apply:
        io.open(MD, "w", encoding="utf-8", newline="").write(t)
        print("已写入")
    else:
        print("（预演，加 --apply 生效）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
