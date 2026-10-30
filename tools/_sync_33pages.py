# -*- coding: utf-8 -*-
r"""把 Springer 页数 32 → 33 同步到各文档，并在新实验报告里补"已写入正文"段（2026-10-05）。

## 背景

新插入的机制小节使 **Springer 版由 32 页增至 33 页**（NC 版仍 43 页）。
同步文档时发现各文档里写的是 "32 页"，需一并更新，否则再现"文件与实测不符"。

    python tools\_sync_33pages.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

TARGETS = ["文件地图.md", "docs/PAPERA_REVISION_SPEC.md", "docs/PAPERA_PREFLIGHT_AUDIT.md",
           "HANDOFF.md", "tools/_sync_docs_20261005.py"]

APPEND = """

---

## ✅ 已写入正文（2026-10-05，操作者确认）

| 插入位置 | 内容 |
|---|---|
| `theory.tex`（式 `eq:gradflow` 之后、Lemma 之前） | **恒等式直接验证**：9 个配置，cos = **0.998**，中位相对误差 **2.7%** |
| `theory.tex`（"The text-only position"） | `g_v = 0` 的措辞**补上实测支撑**（0.0000） |
| `validation.tex`（新小节 **Measured Gradient Asymmetry**） | 按编码器侧的 `‖g_v‖`/`‖g_t‖` 实测 + **表 `tab:grad_side`** |

**插入脚本**：`tools/_pa_add_verified_theory.py`（带断言，可重跑——理论锚点为
`\\begin{lemma}[Modality Decomposition]`，验证锚点为 `\\subsection{Closing the Empirical--Theory Loop}`）

**编译结果**：NC **43 页** / Springer **33 页**（+1，因新小节与小表）、0 错误、0 未定义引用、
cites 44 = bib 44、表 **9/9** label 一致、悬空 ref 0、摘要仍 **244 词**、终检全绿。

**已核验新内容进入 PDF**：`Measured Gradient Asymmetry`、`13.51`、`15.44`、`12.93`、
`0.998`、`2.7%`、`0.0000` 全部检出。
"""


def main() -> int:
    apply = "--apply" in sys.argv
    n = 0
    for rel in TARGETS:
        p = REPO / rel
        if not p.exists():
            continue
        t = io.open(p, encoding="utf-8").read()
        c = t.count("32 页")
        if c:
            print(f"  {rel}: 32 页 × {c} → 33 页")
            if apply:
                io.open(p, "w", encoding="utf-8", newline="").write(t.replace("32 页", "33 页"))
            n += c
        else:
            print(f"  {rel}: 无 '32 页'")

    rp = REPO / "docs" / "NEW_EXPERIMENTS_20261005.md"
    t = io.open(rp, encoding="utf-8").read()
    if "已写入正文（2026-10-05" not in t:
        print("  ✅ 新实验报告：将追加『已写入正文』段")
        if apply:
            io.open(rp, "w", encoding="utf-8", newline="").write(t.rstrip() + APPEND)
            t2 = io.open(rp, encoding="utf-8").read()
            for k in ("Measured Gradient Asymmetry", "tab:grad_side", "33 页", "0.998"):
                assert k in t2, f"报告断言失败：缺 {k}"
            print("      ✅ 已追加并断言通过")
    else:
        print("  新实验报告：已含该段")
    print(f"\n  共替换 {n} 处" + ("（已写回）" if apply else "（预演）"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
