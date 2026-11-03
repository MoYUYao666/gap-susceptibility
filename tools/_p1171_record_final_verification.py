# -*- coding: utf-8 -*-
r"""Close out the 2026-10-17 end-to-end verification: structure index, handover entry, status refresh.

Records what was verified this round (both papers, both PDFs, both claim ledgers, the refreshed submission package,
the archive move) and installs a top-level structure section in the navigation document, since "现在太乱了" was the
operator's framing of the workspace itself.

    python tools/_p1171_record_final_verification.py [--apply]
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MAP = REPO / "文件地图.md"
HANDOFF = REPO / "HANDOFF.md"
MARK = "收尾核验（Paper A + Paper 3 + PDF + 包 + 整理）"

STRUCTURE = """## 🗂️ 工作区结构（2026-10-17 整理后；**未删除任何文件**）

> 本节由 `tools/_p1171_record_final_verification.py` 写入，是"东西在哪"的第一入口。

| 目录 | 是什么 | 纪律 |
|---|---|---|
| `paper合/` | **Paper A 主稿**（`sections/` 源、`main_nc.pdf` 67 页、`main_springer.pdf` 49 页、`NC_submission/` 投稿包）| 稿件树，按路径被文档引用 |
| `paper3/paper_ieee/` | **Paper 3**（PRL 在审 `…02378R1`，`main.pdf` 10 页）；已有 `_bak_archive/` 自身归档 | **已投审，不改动** |
| `paper_a1/`、`paper_a2/`、`paper/`、`paper2/`、`备选/` | A1 / A23 / P1 / P2 / 归档合并稿 | 各自独立 |
| `tools/` | **1,402 个一次性会话脚本** + 门禁/构建/分析脚本 | **不移动**：HANDOFF/docs 按路径+行号引用，账本读其中产物路径 |
| `outputs/` | 结果归档（JSON 为主）与**数字溯源** | **不移动**：账本与稿件数字指向此处字段 |
| `outputs/llava_canonical_cloud/` | **LLaVA 9 个适配器（唯一副本）** + 12 条记录 | 只此一份，已同时入备份快照 |
| `outputs/vlm_clean_cloud/` | Qwen2-VL-2B 修正后 39 条记录 + 日志 | E 节数字来源 |
| `data/`、`models/` | 数据集与权重（本地）| 操作者指定**保留** |
| `backups/` | 最新全量快照 `snapshot_FULL_20261017_after_cleanup`（4.25 GB，校验通过）| 旧快照已由新快照取代 |
| `_archive/` | **归档区（没有任何文件被删除）**：208 个 `*.bak*` 与 4 个临时物，保留原相对路径，附 `MOVED.tsv` 映射与还原方法 | 见 `_archive/README.md` |
| `docs/` | 决策、审计、阶段交付文档 | 按阶段更新 |
| `publish_clean/` | GitHub 发布镜像 | 发布边界规则 |
| `SUBMISSION/` | 已投出的投稿包（P3 PRL 等）| **不得改动** |

**根目录只保留**：`AGENTS.md`、`CLAUDE.md`、`HANDOFF.md`、`文件地图.md`、`README.md`、`哪篇是哪篇.md`、`requirements*.txt`、`.gitignore` 与上述目录。

"""

ENT = """> **✅ 2026-10-17 20:15 —— 收尾核验：Paper A + Paper 3 + PDF + 投稿包 + 工作区整理**
>
> ### 一、Paper A：数据、逻辑、PDF 全部更新并核验
>
> | 项 | 结果 |
> |---|---|
> | 补充 **E 节**（Qwen2-VL-2B）| 用干净口径重写：frozen $0.7778$；**both 98.57±0.44%、text 96.74±0.29%、vision 89.41±1.01%**，三臂 seed 范围**互不重叠**；并**明确写出旧构造的缺陷**（以第 1 epoch 为基线、文本侧含 193 个图像 token、两随机投影 ⇒ 恒 DG\\*≈2.0）|
> | 补充 **G 节**（LLaVA-7B）| 由"scoped null result"改为**生成目标下的独立观察**：vision **+121.5±16.3%** > both +95.7±7.9% > text +73.3±7.5%，text/both 区间不重叠；并说明**两表不比较量级**、只比较"哪一侧影响更大"，结论为**视觉侧最不可控** |
> | `discussion.tex` ¶32 | 同步替换：删除旧的 18.0/66.5/87.9 与 LLaVA "null" 句，改为两解码器实验的新读数与合并解读 |
> | 数字溯源 | 改写脚本**从归档现算**、不手抄；`_claim_ledger_paperA.py` 新增 16 条断言 ⇒ **74/74 PASS，0 GAP**；主台账 **96/96** |
> | 编译 | `main_nc.pdf` **67 页**、`main_springer.pdf` **49 页**，两者 **0 错误 / 0 未定义引用 / 0 未定义引文 / 0 Overfull**，bib 48/48 |
> | 渲染 | 逐页渲染核验 E 表（`Table 9`，6 列）、G 节、G 表（`Table 10`，4 列）；并修掉**全补编图表编号的前导点**（`Table .8`→`Table 8`、`Figure .9`→`Figure 9`）|
>
> ### 二、投稿包已刷新并**独立编译验证**
>
> `NC_submission/`：`Manuscript.pdf` **67 页**（已同步）、`latex_source/` + `latex_source.zip`（**45 文件**），
> 在临时目录**独立编译通过**（0 错误 / 0 未定义 / **67 页一致**），README 页数同步。
> 旧打包脚本 `_pa_build_nc_package.py` 有个隐患（zip 与 README 仅在 `figures/_superseded` 存在时才写），已用
> `tools/_p1169_refresh_nc_submission.py` 取代，该脚本带**独立编译断言**。
>
> ### 三、Paper 3 核验（只核验、不改动——已在审）
>
> | 项 | 结果 |
> |---|---|
> | PDF | `main.pdf` **10 页**、`main_10pp.pdf` 10 页、`main_full.pdf` 13 页；**0 错误 / 0 未定义引用/引文**（2 处轻微 overfull）|
> | 结构审计 | 图/表/定理/公式环境**全部配平**；章节齐全 |
> | ⚠️ 审计脚本期望值**过期** | `audit_check.py` 报 6 项、`audit_pdf.py` 报 19 项 MISS（`ShGPT`、`ERS`、`Gamma` 等）；实测这些串在当前稿件中出现 **0 次** ⇒ **是脚本期望值来自更早草稿，不是稿件数据错误**；因稿件在审，**不改稿件**，仅记录 |
>
> ### 四、工作区整理（**未删除任何文件**）
>
> | 动作 | 结果 |
> |---|---|
> | 新增 `_archive/` | 移入 **208 个 `*.bak*` + 4 个临时物**（3.4 MB），**保留原相对路径**，附 `MOVED.tsv` 映射与还原命令 |
> | 顶层结构索引 | 在 `文件地图.md` 顶部新增「工作区结构」表，写明各目录用途与"不动"纪律 |
> | 不动 | `tools/`（1,402 脚本被按路径引用）、`outputs/`（溯源）、`data/`、`models/`、`paper*`、`publish_clean/`、`SUBMISSION/` |
>
> ### 五、当前就绪度
>
> - **Paper A 可投**：67 页（NC）/ 49 页（Springer），双台账全过，投稿包已建并验证独立可编译；
> - **Paper 3**：PRL `PRLETTERS-D-26-02378R1` 在审，投稿件冻结；
> - ⚠️ 唯一待办：`audit_check.py` / `audit_pdf.py` 的期望值需按当前 10 页版更新（不影响已投稿件，属**下一轮修订**准备）。
>
> **脚本**：`_p1166`（改写 E/G）｜`_p1167`（同步 discussion）｜`_p1168`（台账断言）｜`_p1169`（投稿包刷新+独立编译验证）｜`_p1170`（整理）｜`_p1171`（本条）。
>

"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  (dry run)")
        return 0

    mp = io.open(MAP, encoding="utf-8").read()
    if "工作区结构（2026-10-17 整理后" not in mp:
        i = mp.find("# ")
        j = mp.find("\n", i)
        mp = mp[: j + 1] + "\n" + STRUCTURE + mp[j + 1:]
        io.open(MAP, "w", encoding="utf-8", newline="").write(mp)
        print("  structure index added to 文件地图.md")
    else:
        print("  structure index already present")

    hp = io.open(HANDOFF, encoding="utf-8").read()
    if MARK not in hp:
        i = hp.find("# 项目交接文档")
        j = hp.find("\n", i)
        hp = hp[: j + 1] + "\n" + ENT + hp[j + 1:]
        io.open(HANDOFF, "w", encoding="utf-8", newline="").write(hp)
        print("  handoff entry added")
    else:
        print("  handoff already has the entry")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
