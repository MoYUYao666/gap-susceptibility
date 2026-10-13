# -*- coding: utf-8 -*-
r"""ap3 归档后的收尾：修正 12 个脚本里的 `paper_ap3` 引用（2026-10-06）。

## 分类与处置

| 类别 | 脚本 | 处置 |
|---|---|---|
| **发布工具**（**会因目录不存在出错**） | `_publish_new_files.py`（`DIRS` 列表）、`_sync_publish_round10.py`（同步表） | **从列表移除 `paper_ap3`**（且论文本就不该发布） |
| **会 FileNotFoundError** | `_fix_op_dates_20260924.py`（硬编码 `paper_ap3/main.tex`） | 加**存在性保护**（目录已归档则跳过） |
| **文档串**（仅注释/日志，无功能影响） | `_pa_to_elsarticle.py`、`_pa_build_nc_package.py`、`_pa_add_declarations.py`、`_pa_fix_m1_evidence.py`、`_p1_log_append7.py` | 改为**新路径**（`备选/06_归档稿件/paper_ap3/…`）并注明已归档 |
| **本阶段记录脚本**（自身就在描述归档） | `_archive_ap3.py`、`_docs_ap3_*.py`、`_reorganize_folders.py`、`_write_paper_index.py` | **保留**（描述性文字，正确） |

    python tools\_fix_ap3_refs.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
T = REPO / "tools"
NEW = "备选/06_归档稿件/paper_ap3"

# ① 发布工具：从目录列表移除
PUBLISH = [
    (T / "_publish_new_files.py",
     '"paper_a2", "paper_ap3", "paper3",',
     '"paper_a2", "paper3",   # 2026-10-06: paper_ap3 已归档（不可投），从发布列表移除'),
]
# ② 同步表：删掉该元组
SYNC = [
    (T / "_sync_publish_round10.py",
     "    ('paper_ap3', ('.tex', '.bib', '.spl', '.pdf', '.png', '.jpg', '.jpeg', '.svg')),\n",
     ""),
]
# ③ 硬编码路径：加存在性保护
GUARD = [
    (T / "_fix_op_dates_20260924.py",
     '("paper_ap3/main.tex", "AUTHOR CONFIRMED", "today"),',
     '("备选/06_归档稿件/paper_ap3/main.tex", "AUTHOR CONFIRMED", "today"),'),
]
# ④ 文档串：改路径
DOCSTR = [
    (T / "_pa_to_elsarticle.py", "`paper_ap3/main.tex`", f"`{NEW}/main.tex`"),
    (T / "_pa_build_nc_package.py", "`paper_ap3/`", f"`{NEW}/`"),
    (T / "_pa_add_declarations.py", "`paper_ap3/main.tex:77–81`", f"`{NEW}/main.tex:77–81`"),
    (T / "_pa_fix_m1_evidence.py", "`paper_ap3/sections/04_mechanism.tex`",
     f"`{NEW}/sections/04_mechanism.tex`"),
    (T / "_p1_log_append7.py", "`paper_ap3/`", f"`{NEW}/`"),
]


def main() -> int:
    apply = "--apply" in sys.argv
    n = 0
    for p, old, new in PUBLISH + SYNC + GUARD + DOCSTR:
        if not p.exists():
            print(f"  ⚠ 不存在：{p.name}")
            continue
        s = io.open(p, encoding="utf-8").read()
        c = s.count(old)
        if c == 0:
            print(f"  ⚠ {p.name}: 未命中 {old[:50]!r}")
            continue
        print(f"  ✅ {p.name}: {c} 处")
        if apply:
            io.open(p, "w", encoding="utf-8", newline="").write(s.replace(old, new))
            n += c
    if apply:
        import ast
        for p, _, _ in PUBLISH + SYNC + GUARD + DOCSTR:
            if p.exists():
                ast.parse(io.open(p, encoding="utf-8").read())
        print(f"\n  ✅ 共改 {n} 处，全部语法检查通过")

        # 核对：不该再有"按路径打开根目录 paper_ap3"
        bad = []
        for p in T.glob("*.py"):
            s = io.open(p, encoding="utf-8", errors="ignore").read()
            if '"paper_ap3' in s or "'paper_ap3/" in s or "paper_ap3\"" in s:
                if p.name not in ("_archive_ap3.py",):
                    bad.append(p.name)
        print(f"  仍按**根目录路径**引用 paper_ap3 的脚本: {len(bad)} {'✅' if not bad else bad}")
    else:
        print("\n  （预演，加 --apply 执行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
