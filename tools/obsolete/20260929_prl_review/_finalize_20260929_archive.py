# -*- coding: utf-8 -*-
r"""最后一步：把 `_archive_organizers.py` 自身也归档，并按归档目录**实际内容**重写清单。

    python tools/_finalize_20260929_archive.py [--apply]
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ARCH = REPO / "tools" / "obsolete" / "20260929_prl_review"
SELF_NAME = "_finalize_20260929_archive.py"

HEAD = """# tools/obsolete/20260929_prl_review —— 归档清单

> 归档日期：2026-09-29 ｜ 起因：PRL 综述从起草到投稿 + 两篇 PRL 稿件的补件处理
> **没有任何文件被删除。** 全部是 move 到此目录，可按本清单原样移回。

## 为何归档

本次会话产生了一批**一次性脚本**：页面压缩四轮迭代、补引用三轮、归属误记的三次更正、记录落账两轮。
它们**已执行完毕**，且多数**只对当时的文本状态有效**——日后重跑会产生错误结果。
按仓库既有约定（`tools/obsolete/`）移入归档：保留可追溯性，同时让 `tools/` 根层只剩可重跑管线。

⚠️ **两项结论互斥，务必看清**：
`_fix_authorship_form_attribution.py` 是**错误**的那次更正（把 P3 的表判给综述）；
`_restore_authorship_attribution.py` 是**正确**的改回。
**现行结论以 `paper_review_prl/AUTHORSHIP_FORM_ATTRIBUTION.md` 为准**，不要据这两个脚本推断。

⚠️ **本目录内含生成本清单的脚本**（`_organize_20260929.py`、`_rebuild_archive_manifest.py`、
`_archive_organizers.py`、`_finalize_20260929_archive.py`）——它们已执行完毕，留此备查。

## 保留在 tools/ 根层的可重跑管线（本次会话产出）

| 脚本 | 用途 |
|---|---|
| `_verify_citations.py` | 多源引用核验（PASS/WEAK/FAIL + DOI 冲突检测 + arXiv id 校验） |
| `_merge_refs.py` / `_dedupe_and_upgrade_refs.py` / `_quarantine_failed_refs.py` | 合并、去重升级、隔离失败条目 |
| `_check_citation_keys.py` / `_normalize_refs.py` | 引用键一致性检查与括号规范化 |
| `_audit_venues.py` / `_audit_claim_sources.py` | 期刊与论断来源审计 |
| `_extract_used_refs.py` | **从正文抽取实际引用**生成参考文献表（消除漂移） |
| `_build_prl_tex.py` | markdown → cas-dc LaTeX 并编译 |
| `_make_prl_figure.py` | 生成 Figure 1（决策空间示意图） |
| `_check_manuscript.py` / `_manuscript_diagnostics.py` | 稿件规格与引用密度自检 |
| `_final_check_prl.py` | **投稿前总闸门**（页数/编译错误/未定义引用/`[?]` 标记/裸星号/门户一致性/图表/引用/自引）；缺 `.log` 时**自愈重编译** |
| `_make_prl_authorship_form.py` | 按指定日期生成 Authorship Confirmation 表（可反复重生成） |
| `_make_prl_em_fields.py` | 生成门户填写字段 |
| `_benchmark_prl_reviews.py` | 拉取同刊综述类文章建立规格基准（引用数中位 55／四分位 37–59） |
| `_measure_prl_layout.py` | 量出正文/参考文献各占多少页 |

## 移回方法

```powershell
Move-Item tools\\obsolete\\20260929_prl_review\\<文件名> tools\\
```
"""

# 逐项归档理由
REASONS = {
    "_trim_prl_manuscript.py": "页面压缩第 1 轮；已执行，文本已定稿",
    "_plan_prl_trim.py": "列出可精简项的诊断；已执行",
    "_trim_prl_to_seven_pages.py": "页面压缩第 2 轮；已执行",
    "_fit_prl_seven_pages.py": "页面压缩第 3 轮；已执行",
    "_fit_round5.py": "页面压缩第 4 轮；已执行",
    "_restore_refs_and_trim.py": "补引用第 1 轮；已执行",
    "_restore_refs_round2.py": "补引用第 2 轮；已执行",
    "_add_refs_free.py": "零成本补引用；已执行",
    "_add_citations_3x.py": "为 §3.4–3.6 补引用；已执行",
    "_fix_authorship_form_attribution.py": "⚠️ 归属误记的**第 1 次（错误）更正**；已被推翻，仅留档",
    "_restore_authorship_attribution.py": "**归属改回 P3**（正确结论）；依据已固化进 AUTHORSHIP_FORM_ATTRIBUTION.md",
    "_fix_docs_authorship_note.py": "修两份交接文档的归属表述；已执行",
    "_clean_stale_map_todo.py": "清理文件地图里的过期待办；已执行",
    "_record_review_form_fix.py": "记录综述表日期更正；已执行",
    "_record_p3_form_uploaded.py": "记录 P3 补表完成；已执行",
    "_inspect_form_pdf.py": "诊断 A1 表的字体/日期流机制；结论已固化进 _make_prl_authorship_form.py",
    "_fetch_arxiv_meta.ps1": "arXiv 元数据抓取（PS1 版）；已被 _verify_citations.py 的多源链取代",
    "_crossref_search.ps1": "Crossref 检索（PS1 版）；同上",
    "_lookup_conference.ps1": "会议论文查询（PS1 版）；同上",
    "_organize_archive.py": "早期根目录整理脚本；已执行，其安全规则已记入本次整理脚本 docstring",
    "_organize_20260929.py": "本次整理的执行脚本；已执行",
    "_rebuild_archive_manifest.py": "重建被 0 项版本覆盖的清单；已执行",
    "_archive_organizers.py": "把整理脚本自身归档；已执行",
    SELF_NAME: "本脚本，执行完即归档",
    "main_prl.abs": "LaTeX 构建残渣（`\\listfiles` 产物），内容为旧版摘要（26 条引用时期口径）",
}


def main() -> int:
    apply = "--apply" in sys.argv
    me = REPO / "tools" / SELF_NAME
    if me.exists():
        tracked = subprocess.run(["git", "ls-files", "--error-unmatch", f"tools/{SELF_NAME}"],
                                 cwd=REPO, capture_output=True).returncode == 0
        print(f"  归档自身：{SELF_NAME}（{'git mv' if tracked else 'move'}）")
        if apply:
            if tracked:
                subprocess.run(["git", "mv", f"tools/{SELF_NAME}", str((ARCH / SELF_NAME).relative_to(REPO))],
                               cwd=REPO, capture_output=True)
            else:
                shutil.move(str(me), str(ARCH / SELF_NAME))
    else:
        print(f"  跳过（不存在）：{SELF_NAME}")

    if apply:
        files = sorted(p.name for p in ARCH.iterdir() if p.is_file() and p.name != "README.md")
        miss = [f for f in files if f not in REASONS]
        lines = [HEAD, "", f"## 归档明细（{len(files)} 项）", "", "| 文件 | 归档理由 |", "|---|---|"]
        lines += [f"| `{f}` | {REASONS.get(f, '（理由待补）')} |" for f in files]
        (ARCH / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"  ✅ 清单已重写：{len(files)} 项" + (f"，⚠ 缺理由 {miss}" if miss else ""))
    else:
        print("（预演，加 --apply 生效）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
