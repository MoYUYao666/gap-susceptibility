# -*- coding: utf-8 -*-
r"""重建 tools/obsolete/20260929_prl_review/README.md（首次执行时清单被 0 项版本覆盖）。

原因：`_organize_20260929.py` 先移动文件再写清单，第二次运行（幂等检查）时源文件已不在，
`moved` 为空，于是清单被写成"0 项"。本脚本按归档目录的**实际内容**重建清单。

    python tools/_rebuild_archive_manifest.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ARCH = REPO / "tools" / "obsolete" / "20260929_prl_review"

REASONS = {
    "_trim_prl_manuscript.py": "页面压缩第 1 轮；已执行，文本已定稿",
    "_plan_prl_trim.py": "列出可精简项的诊断脚本；已执行",
    "_trim_prl_to_seven_pages.py": "页面压缩第 2 轮；已执行",
    "_fit_prl_seven_pages.py": "页面压缩第 3 轮；已执行",
    "_fit_round5.py": "页面压缩第 4 轮；已执行",
    "_restore_refs_and_trim.py": "补引用第 1 轮；已执行",
    "_restore_refs_round2.py": "补引用第 2 轮；已执行",
    "_add_refs_free.py": "零成本补引用；已执行",
    "_add_citations_3x.py": "为 §3.4–3.6 补引用；已执行",
    "_fix_authorship_form_attribution.py": "⚠️ **归属误记的第 1 次（错误）更正**；结论已被下述脚本推翻，仅留档",
    "_restore_authorship_attribution.py": "**归属改回 P3**（正确结论）；依据已固化进 AUTHORSHIP_FORM_ATTRIBUTION.md",
    "_fix_docs_authorship_note.py": "修两份交接文档的归属表述；已执行",
    "_clean_stale_map_todo.py": "清理文件地图里的过期待办；已执行",
    "_record_review_form_fix.py": "记录综述表日期更正；已执行",
    "_record_p3_form_uploaded.py": "记录 P3 补表完成；已执行",
    "_inspect_form_pdf.py": "诊断 A1 表的字体/日期流机制；结论已固化进 _make_prl_authorship_form.py",
    "_fetch_arxiv_meta.ps1": "arXiv 元数据抓取（PS1 版）；已被 _verify_citations.py 的多源链取代",
    "_crossref_search.ps1": "Crossref 检索（PS1 版）；同上",
    "_lookup_conference.ps1": "会议论文查询（PS1 版）；同上",
    "_organize_archive.py": "早期根目录整理脚本；已执行，其安全规则已记入 _organize_20260929.py docstring",
    "main_prl.abs": "LaTeX 构建残渣（`\\listfiles` 产物），内容为旧版摘要（26 条引用时期口径）",
}

HEAD = """# tools/obsolete/20260929_prl_review —— 归档清单

> 归档日期：2026-09-29 ｜ 执行：`tools/_organize_20260929.py`
> **没有任何文件被删除。** 全部是 move 到此目录，可按本清单原样移回。

## 为何归档

本次会话（PRL 综述从起草到投稿，外加两篇 PRL 稿件的补件处理）产生了一批**一次性脚本**：
页面压缩四轮迭代、补引用三轮、归属误记的三次更正、记录落账两轮。
它们**已执行完毕**，且多数**只对当时的文本状态有效**——日后重跑会产生错误结果。
按仓库既有约定（`tools/obsolete/`）移入归档：保留可追溯性，同时让 `tools/` 根层只剩可重跑管线。

⚠️ **其中两项结论互斥，务必看清**：
`_fix_authorship_form_attribution.py` 是**错误**的那次更正（把 P3 的表判给综述）；
`_restore_authorship_attribution.py` 是**正确**的改回。
**现行结论以 `paper_review_prl/AUTHORSHIP_FORM_ATTRIBUTION.md` 为准**，不要据这两个脚本推断。

## 保留在 tools/ 根层的可重跑管线（本次会话产出）

| 脚本 | 用途 |
|---|---|
| `_verify_citations.py` | 多源引用核验（PASS/WEAK/FAIL + DOI 冲突检测 + arXiv id 校验） |
| `_merge_refs.py` / `_dedupe_and_upgrade_refs.py` / `_quarantine_failed_refs.py` | 合并、去重升级、隔离失败条目 |
| `_check_citation_keys.py` / `_normalize_refs.py` | 引用键一致性检查与括号规范化 |
| `_audit_venues.py` / `_audit_claim_sources.py` | 期刊与论断来源审计 |
| `_extract_used_refs.py` | **从正文抽取实际引用**，生成参考文献表（消除漂移） |
| `_build_prl_tex.py` | markdown → cas-dc LaTeX 并编译 |
| `_make_prl_figure.py` | 生成 Figure 1（决策空间示意图） |
| `_check_manuscript.py` / `_manuscript_diagnostics.py` | 稿件规格与引用密度自检 |
| `_final_check_prl.py` | **投稿前总闸门**（页数/错误/未定义引用/裸星号/门户一致性/图表/引用/自引） |
| `_make_prl_authorship_form.py` | 按指定日期生成 Authorship Confirmation 表（可反复重生成） |
| `_make_prl_em_fields.py` | 生成门户填写字段 |
| `_benchmark_prl_reviews.py` | 拉取同刊综述类文章建立规格基准 |
| `_measure_prl_layout.py` | 量出正文/参考文献各占多少页 |

## 移回方法

```powershell
Move-Item tools\\obsolete\\20260929_prl_review\\<文件名> tools\\
```
"""


def main() -> int:
    apply = "--apply" in sys.argv
    files = sorted(p.name for p in ARCH.iterdir() if p.is_file() and p.name != "README.md")
    missing_reason = [f for f in files if f not in REASONS]
    lines = [HEAD, "", f"## 归档明细（{len(files)} 项）", "",
             "| 文件 | 归档理由 |", "|---|---|"]
    lines += [f"| `{f}` | {REASONS.get(f, '（理由待补）')} |" for f in files]
    text = "\n".join(lines) + "\n"
    print(f"归档目录实有文件: {len(files)} 个")
    if missing_reason:
        print(f"  ⚠ 缺理由: {missing_reason}")
    print(f"清单将写为 {len(text)} 字符")
    if apply:
        (ARCH / "README.md").write_text(text, encoding="utf-8")
        print(f"✅ 已重建 {(ARCH / 'README.md').relative_to(REPO)}")
    else:
        print("（预演，加 --apply 生效）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
