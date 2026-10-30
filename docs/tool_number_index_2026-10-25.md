# 工具编号对照索引（2026-10-25）

> **为什么有这个文件**：本轮并行推进时，不同 agent 各自递增编号，导致 **`_p1645`–`_p1652` 每个编号下各有两个
> 不同名的脚本**（文件名不同，**没有任何文件被覆盖**）。HANDOFF / 笔记里的“`_p1645` 修了归档”这类简称，
> 单看编号会指错文件。本表把每个编号映射到**两个完整文件名**，并标明**本轮实际用的是哪一个**。
> 规则：正文引用时**必须写完整文件名**，不要只写编号；本表只做消歧，**不重命名任何文件**。

| 编号 | 文件 A | 文件 B | 本轮实际使用 | 说明 |
|---|---|---|---|---|
| `_p1645` | `_p1645_repair_run_archive_block_maps.py` | `_p1645_stage_pope_archive.py` | **A** | A = 用 `allocation_stage.module_ranks` 确定性重建 `block_maps`（我）；B = POPE 归档暂存（POPE agent） |
| `_p1646` | `_p1646_p3_arm_replicates.py` | `_p1646_inspect_pope_aggregate.py` | **A** | A = 每臂 2 次复现性研究（我）；B = 查看 POPE 聚合（POPE agent） |
| `_p1647` | `_p1647_assemble_retrieval.py` | `_p1647_pope_corrected_metrics.py` | **A** | A = 实例失联后补齐 6 个缺失取回文件（我）；B = POPE 指标修正（POPE agent） |
| `_p1648` | `_p1648_probe_bootstrap_variants.py` | —（无重号） | 未被本轮主流程使用 | 仅探测脚本 |
| `_p1649` | `_p1649_append_round2_zh.py` | `_p1649_pope_supplement_insert.py` | **A** | A = 向云轮笔记追加中文一节（我）；B = 向 P3 补充材料插入 POPE 小节（p3-stats） |
| `_p1650` | `_p1650_fix_pope_acceptance_bool.py` | `_p1650_diagnose_p1640_metric_bug.py` | **A** | A = 修 `bool(哨兵字符串)==True` 的诚实性缺陷（我）；B = 诊断 `_p1640` 指标 bug（POPE agent） |
| `_p1651` | `_p1651_update_phase_close_docs.py` | `_p1651_check_supp_pages.py` | **A** | A = 追加 HANDOFF/文件地图/POPE 笔记（我）；B = 检查补充材料页数（POPE agent） |
| `_p1652` | `_p1652_backfill_v25_doi.py` | `_p1652_probe_pope_pdf_needles.py` | **A** | A = v2.5 DOI 回填（我）；B = 探测 PDF 文案（POPE agent） |
| `_p1660` | `_p1660_audit_doc_fixes.py` | —（本文件作者） | 是 | 本表第 1–6 项文档修订的执行脚本；**编号 1653–1659 已被其他 agent 占用，故跳到 1660** |

**核验命令**（列出每个编号下的所有文件）：
```powershell
Get-ChildItem tools -Filter "_p16*.py" | Where-Object { $_.Name -match '^_p16(4[5-9]|5[0-9])_' } | Sort-Object Name
```
