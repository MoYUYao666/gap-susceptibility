# -*- coding: utf-8 -*-
r"""Record the scope decision for the language rule: future artifacts only.

Operator (2026-10-14, choosing among four options): "只管今后，存量不动"
- new artifacts are written in English from now on
- the 1,320 existing Chinese tool scripts stay as they are (they are historical records)
- handoff documents (HANDOFF.md, 文件地图.md, docs/) stay in Chinese, since they report
  to an operator who reads Chinese

    python tools/_p615_record_language_scope.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

MARK = "存量不动"
ADD = """
### 范围裁决（2026-10-14）

> 操作者在四个选项中选定：**"只管今后，存量不动"**

| 对象 | 语言 | 说明 |
|---|---|---|
| **今后新建的产出物** | **英文** | 代码/注释/docstring/print、结果 JSON、报告、清单、README |
| **已有存量脚本**（`tools/` 下 1,320 个含中文 `.py`，328,521 字符） | **保持原样** | 它们是**历史记录**（每个会话的修订脚本），不是维护目标；**不要为了统一语言去翻改** |
| **交接文档**（`HANDOFF.md`、`文件地图.md`、`docs/` 工作笔记） | **中文** | 它们的用途是**向操作者汇报**，而操作者读中文 |
| **对话回复** | **中文** | 结论、进度、决策、报错解释 |
| **稿件 / 修订包 / GitHub 发布库** | **英文** | 面向外部；**已全部完成**（`SUBMISSION/P3_PRL_revision/` 的答复件与 `publish_clean/` 均已英文化） |

**⇒ 判据（判断某文件该用哪种语言）**：**它写给谁看？**
给**外部**（期刊/审稿人/公众）⇒ **英文**；
给**操作者**（汇报、导航、决策记录）⇒ **中文**；
给**机器**（路径、匹配模式）⇒ **按原样**。

**⚠️ 存量豁免的理由**：`tools/_p4xx_*.py` 这类脚本是**一次性修订脚本**，
其价值在于"记录当时怎么做的"，**改动它们既无收益、又会让 HANDOFF 的按行号引用失效**。
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  （预演）")
        return 0
    for name in ("AGENTS.md", "CLAUDE.md"):
        p = REPO / name
        if not p.exists():
            continue
        t = io.open(p, encoding="utf-8", errors="replace").read()
        if MARK in t and "范围裁决" in t:
            print(f"  {name}: already records the scope decision")
            continue
        bak = p.with_suffix(p.suffix + ".bak_p615")
        if not bak.exists():
            shutil.copy2(p, bak)
        # insert right after the exception list, i.e. before "## 🔴 发布边界"
        k = t.find("## 🔴 发布边界")
        if k < 0:
            k = t.find("## 关键约束")
        t2 = t[:k] + ADD.strip() + "\n\n" + t[k:] if k > 0 else t.rstrip() + "\n" + ADD
        io.open(p, "w", encoding="utf-8", newline="").write(t2)
        print(f"  {name}: {len(t):,} -> {len(t2):,} chars")
    for name in ("AGENTS.md", "CLAUDE.md"):
        t = io.open(REPO / name, encoding="utf-8").read()
        ok = MARK in t and "范围裁决" in t
        print(f"  {'OK ' if ok else 'BAD'} {name} ({len(t.splitlines())} lines)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
