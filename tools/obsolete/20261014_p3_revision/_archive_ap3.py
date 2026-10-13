# -*- coding: utf-8 -*-
r"""把 ap3 归档进 `备选/06_归档稿件/`（2026-10-06，操作者指示："不可投放进备选"）。

## 为什么

`paper_ap3/`（P1+P2+P3 合并稿，86 页）**已确认无可投路径**（含 P3 内容，而 P3 已投 PRL 在审 →
一稿两投）。操作者指示归档。`备选/06_归档稿件/` 已有先例（`paper_a4/`）。

## 关键：20+ 个 ap3 专用脚本按字面路径读它

实测（`grep 'paper_ap3'`）：
`ap3_compile_check.py`、`ap3_fulltext_lint.py`、`audit_citation_coverage.py`、`audit_mechanics.py`、
`clip_ap3_overview.py`、`fix_discussion_paragraph.py`、`_ap3_bib_audit.py`、`_ap3_blip_fix.py`、
`_ap3_compliance_quickcheck.py`、`_ap3_fix_tail.py`、`_ap3_patch_*.py`（9 个）、`_ap3_sync_check.py`、
`_ap3_superseded_marker_cleanup.py` …… **这些全是 ap3 专用工具**（审计/打补丁/编译），
**ap3 归档后它们已无对象** → **一并归档**，避免留下"指向不存在目录"的脚本。

**通用的只有 2 个**：`_bib_verify.py`、`_p1_bib_fix.py`（读 `paper_ap3/refs.bib` 做 bib 核对/修复）——
`paper合/references.bib` 是它的**等价后继**（同一工作线的现役 bib），故**改指 `paper合/references.bib`**。

## 保留的交叉引用（**不改**）

`_a1_cover_letter_fix.py`、`_fix_round2.py`、`audit_submission_pdfs.py`、`_patch_audit_script.py` 里的
`'paper_ap3'` 是**禁用词表**（确保投稿件不提及它）——**字符串，非路径**，归档后仍然正确。

    python tools\_archive_ap3.py [--apply]
"""
from __future__ import annotations

import io
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DEST = REPO / "备选" / "06_归档稿件" / "paper_ap3"

# ap3 专用脚本（一并归档）
AP3_TOOLS = [
    "ap3_compile_check.py", "ap3_fix_stray_pystring.py", "ap3_fulltext_lint.py",
    "audit_citation_coverage.py", "audit_mechanics.py", "audit_submission_pdfs.py",
    "clip_ap3_overview.py", "fix_discussion_paragraph.py",
    "_ap3_bib_audit.py", "_ap3_blip_fix.py", "_ap3_compliance_quickcheck.py", "_ap3_fix_tail.py",
    "_ap3_patch_adapter.py", "_ap3_patch_corr.py", "_ap3_patch_counts.py", "_ap3_patch_mdi.py",
    "_ap3_patch_mechanism.py", "_ap3_patch_protocol.py", "_ap3_patch_tiera.py",
    "_ap3_superseded_marker_cleanup.py", "_ap3_sync_check.py",
]

# 通用脚本：改指 paper合/references.bib
RETARGET = ["_bib_verify.py", "_p1_bib_fix.py"]

BIB_NOTE = ("# 2026-10-06 归档 ap3：`paper_ap3/` 已移入 `备选/06_归档稿件/paper_ap3/`（不可投）。\n"
            "# 该 bib 的等价后继是现役的 `paper合/references.bib`，故改指后者。\n")


def main() -> int:
    apply = "--apply" in sys.argv
    src = REPO / "paper_ap3"
    if not src.exists():
        print("  ⚠ paper_ap3/ 不存在（可能已归档）")
    tools_present = [t for t in AP3_TOOLS if (REPO / "tools" / t).exists()]
    retarget_present = [t for t in RETARGET if (REPO / "tools" / t).exists()]

    print("=== 计划 ===")
    print(f"  移动 paper_ap3/ → 备选/06_归档稿件/paper_ap3/（{len(list(src.rglob('*'))) if src.exists() else 0} 项）")
    print(f"  归档 ap3 专用脚本 {len(tools_present)} 个 → 备选/06_归档稿件/ap3_工具/")
    print(f"  改指 bib 的通用脚本 {len(retarget_present)} 个：{retarget_present}")
    print("  保留禁用词表里的 'paper_ap3' 字符串（非路径，仍正确）")
    if not apply:
        print("\n  （预演，加 --apply 执行）")
        return 0

    # ① 移动目录
    if src.exists():
        DEST.parent.mkdir(parents=True, exist_ok=True)
        if DEST.exists():
            print("  ⚠ 目标已存在，跳过移动")
        else:
            shutil.move(str(src), str(DEST))
        assert not src.exists() and DEST.exists(), "移动失败"
        print(f"  ✅ 已归档 → 备选/06_归档稿件/paper_ap3/")

    # ② 归档专用脚本
    tdir = REPO / "备选" / "06_归档稿件" / "ap3_工具"
    tdir.mkdir(parents=True, exist_ok=True)
    moved = 0
    for t in tools_present:
        shutil.move(str(REPO / "tools" / t), str(tdir / t))
        moved += 1
    print(f"  ✅ 已归档 {moved} 个 ap3 专用脚本")

    # ③ 通用脚本改指 bib
    for t in retarget_present:
        p = REPO / "tools" / t
        s = io.open(p, encoding="utf-8").read()
        c = s.count("paper_ap3/refs.bib")
        if c:
            s = s.replace("paper_ap3/refs.bib", "paper合/references.bib")
            io.open(p, "w", encoding="utf-8", newline="").write(s)
            s2 = io.open(p, encoding="utf-8").read()
            assert "paper_ap3/refs.bib" not in s2, f"{t} 仍有旧路径"
            import ast
            ast.parse(s2)
            print(f"  ✅ {t}: paper_ap3/refs.bib → paper合/references.bib（{c} 处）")

    # ④ 归档说明
    note = (DEST.parent / "AP3_归档说明.md")
    io.open(note, "w", encoding="utf-8", newline="").write(
        "# ap3 已归档（2026-10-06）\n\n"
        "> 操作者指示：「**不可投放进备选**」。\n\n"
        "## 这是什么\n\n"
        "`paper_ap3/` = **P1 + P2 + P3 合并稿**（Elsevier `elsarticle`，86 页）。\n\n"
        "## 为什么不可投\n\n"
        "| 原因 | 说明 |\n|---|---|\n"
        "| **含 P3 内容** | `sections/` 里 Representation Theorem 9 处、GFAP 11 处，与 `paper3/` 重叠 |\n"
        "| **P3 已在审** | P3 已投 **PRL `PRLETTERS-D-26-02378`**（2026-09-28）→ 投 ap3 即**一稿两投** |\n"
        "| **去掉 P3 亦无用** | 去掉后等同 `paper合/`（P1+P2，45 页），而后者已在编 |\n\n"
        "## 同目录还有\n\n"
        "- `ap3_工具/`：**ap3 专用脚本 20+ 个**（审计、打补丁、编译检查）。ap3 归档后它们已无对象，故一并移入。\n"
        "- 通用脚本（`_bib_verify.py`、`_p1_bib_fix.py`）**未归档**，但已把 `paper_ap3/refs.bib` 改指\n"
        "  **`paper合/references.bib`**（等价后继）。\n\n"
        "## 保留的引用\n\n"
        "`_a1_cover_letter_fix.py`、`_fix_round2.py`、`audit_submission_pdfs.py`、`_patch_audit_script.py` 里的\n"
        "`'paper_ap3'` 是**禁用词表**（确保投稿件不提及它）——字符串，非路径，归档后仍正确。\n\n"
        "## 复核\n\n"
        "```powershell\n"
        "python tools\\_write_paper_index.py --apply   # 重建根目录索引\n"
        "```\n")
    print(f"  ✅ 已写归档说明 备选/06_归档稿件/AP3_归档说明.md")

    # ⑤ 核对
    print("\n=== 核对 ===")
    left = [t for t in AP3_TOOLS if (REPO / "tools" / t).exists()]
    print(f"  tools/ 残留 ap3 专用脚本: {len(left)} {'✅' if not left else left}")
    bad = []
    for p in (REPO / "tools").glob("*.py"):
        s = io.open(p, encoding="utf-8", errors="ignore").read()
        if "paper_ap3/" in s:
            bad.append(p.name)
    print(f"  仍按路径引用 paper_ap3/ 的脚本: {len(bad)} {'✅' if not bad else bad}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
