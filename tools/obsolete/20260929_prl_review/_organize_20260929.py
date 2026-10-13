# -*- coding: utf-8 -*-
r"""整理本次工作产生的文件（2026-09-29）。

## 设计原则（沿仓库既有约定）

1. **不删任何文件**。只做 rename/move；构建残渣移入归档目录而非删除。
2. **不移动被文档按行号引用的证据**。根目录的 `_guide*.txt` / `_oe_guide.txt` 等已由
   `tools/_organize_archive.py` 的规则判定"必须留在原地"（`docs/` 多处按 `:行号` 引用），本次不动。
3. **可重跑管线留在 `tools/` 根层**，与既有 368 个脚本一致；**避免打断文档里的路径引用**。
4. **一次性脚本移入 `tools/obsolete/<日期>_<主题>/`**（仓库已有 `obsolete/` 约定）。
5. 交付件不进 git（`.gitignore` 含 `*.pdf`），故对未跟踪文件用普通 move。

## 动作清单

A. `paper_review_prl/main_prl.abs` → 归档（LaTeX 构建残渣，且内容口径已陈旧）
B. `paper_review_prl/Authorship Confirmation (review, 2026-09-28).pdf`
   → 重命名加 `PENDING` 前缀（它是**待上传**件，此前命名看不出状态）
C. 19 个一次性脚本 + `_organize_archive.py` → `tools/obsolete/20260929_prl_review/`
D. 写归档清单，说明每项为何归档、如何移回

    python tools/_organize_20260929.py            # 预演
    python tools/_organize_20260929.py --apply
"""
from __future__ import annotations

import io
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ARCH = REPO / "tools" / "obsolete" / "20260929_prl_review"

# A. 构建残渣 → 归档
ARTIFACTS = [REPO / "paper_review_prl" / "main_prl.abs"]

# B. 重命名（待上传件加状态前缀）
RENAMES = [
    (REPO / "paper_review_prl" / "Authorship Confirmation (review, 2026-09-28).pdf",
     REPO / "paper_review_prl" / "PENDING-UPLOAD Authorship Confirmation (review, 2026-09-28).pdf"),
]

# C. 一次性脚本 → 归档。每项的归档理由写进清单。
ONE_OFF = {
    # 页面压缩的多次迭代：最终态已定（7 页），这些变换脚本只对当时的文本有效
    "_trim_prl_manuscript.py": "页面压缩第 1 轮；已执行，文本已定稿",
    "_plan_prl_trim.py": "列出可精简项的诊断脚本；已执行",
    "_trim_prl_to_seven_pages.py": "页面压缩第 2 轮；已执行",
    "_fit_prl_seven_pages.py": "页面压缩第 3 轮；已执行",
    "_restore_refs_and_trim.py": "补引用第 1 轮；已执行",
    "_restore_refs_round2.py": "补引用第 2 轮；已执行",
    "_add_refs_free.py": "零成本补引用；已执行",
    "_add_citations_3x.py": "为 §3.4–3.6 补引用；已执行",
    "_fit_round5.py": "页面压缩第 4 轮；已执行",
    # 归属误记处理链：其中 _restore_* 与 _fix_* 结论互斥，留着会误导
    "_fix_authorship_form_attribution.py": "归属误记的第 1 次（错误）更正；已被后者取代，留档备查",
    "_restore_authorship_attribution.py": "归属改回 P3；结论已写入 AUTHORSHIP_FORM_ATTRIBUTION.md",
    "_fix_docs_authorship_note.py": "修两份交接文档的归属表述；已执行",
    "_clean_stale_map_todo.py": "清理文件地图里的过期待办；已执行",
    "_record_review_form_fix.py": "记录综述表日期更正；已执行",
    "_record_p3_form_uploaded.py": "记录 P3 补表完成；已执行",
    # 一次性诊断
    "_inspect_form_pdf.py": "诊断 A1 表的字体/日期流机制；结论已固化进 _make_prl_authorship_form.py",
    # 被 Python 版取代的 PS1
    "_fetch_arxiv_meta.ps1": "arXiv 元数据抓取（PS1 版）；已被 _verify_citations.py 的多源链取代",
    "_crossref_search.ps1": "Crossref 检索（PS1 版）；同上",
    "_lookup_conference.ps1": "会议论文查询（PS1 版）；同上",
    # 本仓库早期的整理脚本（一次性执行）
    "_organize_archive.py": "早期根目录整理脚本；已执行，其安全规则已记入本脚本 docstring",
}

MANIFEST = """# tools/obsolete/20260929_prl_review —— 归档清单

> 归档日期：2026-09-29 ｜ 执行：`tools/_organize_20260929.py`
> **没有任何文件被删除。** 全部是 move 到此目录，可按本清单原样移回。

## 为何归档

本次会话（PRL 综述从起草到投稿 + 两篇稿件的补件处理）产生了一批**一次性脚本**：
页面压缩的四轮迭代、补引用的三轮、归属误记的三次更正、两轮记录落账。
它们**已经执行完毕**，且多数只对**当时的文本状态**有效——若日后重跑会产生错误结果。
按仓库既有约定（`tools/obsolete/`）移入归档，保留可追溯性，同时让 `tools/` 根层只剩可重跑管线。

⚠️ **其中两项的结论互斥，务必看清**：
`_fix_authorship_form_attribution.py` 是**错误的**那次更正（把 P3 的表判给综述）；
`_restore_authorship_attribution.py` 是**正确的**改回。**现行结论以
`paper_review_prl/AUTHORSHIP_FORM_ATTRIBUTION.md` 为准**，不要据这两个脚本推断。

## 移回方法

```powershell
Move-Item tools\\obsolete\\20260929_prl_review\\<文件名> tools\\
```
"""


def git_mv(src: Path, dst: Path) -> None:
    """已跟踪文件用 git mv（保留历史），未跟踪的用普通 move。"""
    tracked = subprocess.run(["git", "ls-files", "--error-unmatch", str(src)],
                             cwd=REPO, capture_output=True).returncode == 0
    dst.parent.mkdir(parents=True, exist_ok=True)
    if tracked:
        subprocess.run(["git", "mv", str(src.relative_to(REPO)), str(dst.relative_to(REPO))],
                       cwd=REPO, check=True, capture_output=True)
        print(f"    git mv  {src.name} → {dst.relative_to(REPO)}")
    else:
        shutil.move(str(src), str(dst))
        print(f"    move    {src.name} → {dst.relative_to(REPO)}")


def main() -> int:
    apply = "--apply" in sys.argv
    if not apply:
        print("（预演；加 --apply 生效）\n")

    # A. 残渣
    print("A. 构建残渣 → 归档")
    for p in ARTIFACTS:
        if p.exists():
            print(f"    {p.relative_to(REPO)}  → {ARCH.name}/")
            if apply:
                git_mv(p, ARCH / p.name)
        else:
            print(f"    跳过（不存在）：{p.name}")

    # B. 重命名
    print("\nB. 待上传件加状态前缀")
    for old, new in RENAMES:
        if old.exists():
            print(f"    {old.name}\n      → {new.name}")
            if apply:
                git_mv(old, new)
        else:
            print(f"    跳过（不存在或已改名）：{old.name}")

    # C. 一次性脚本
    print(f"\nC. {len(ONE_OFF)} 个一次性脚本 → tools/obsolete/{ARCH.name}/")
    moved, missing = [], []
    for name, reason in ONE_OFF.items():
        src = REPO / "tools" / name
        if src.exists():
            moved.append((name, reason))
            if apply:
                git_mv(src, ARCH / name)
        else:
            missing.append(name)
    if missing:
        print(f"    （{len(missing)} 个不存在，跳过）：{', '.join(missing)}")

    # D. 清单
    if apply:
        lines = [MANIFEST, "\n## 归档明细（%d 项）\n" % len(moved),
                 "| 文件 | 归档理由 |", "|---|---|"]
        lines += [f"| `{n}` | {r} |" for n, r in moved]
        if ARTIFACTS:
            lines += ["", "## 另归档的构建残渣", "",
                      "| 文件 | 理由 |", "|---|---|",
                      "| `paper_review_prl/main_prl.abs` | LaTeX 构建残渣（`\\listfiles` 产物），"
                      "内容为旧版摘要（26 条引用时期口径） |"]
        (ARCH / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"\nD. 已写归档清单：{(ARCH / 'README.md').relative_to(REPO)}")
    else:
        print(f"\nD. （预演）将写清单到 tools/obsolete/{ARCH.name}/README.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
