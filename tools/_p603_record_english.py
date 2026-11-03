# -*- coding: utf-8 -*-
r"""落账：GitHub 库全英文化（2026-10-14）。

    python tools\_p603_record_english.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SLUG = "MoYUYao666/gap-susceptibility"

ENT = """> **🔤 2026-10-14 06:00 —— GitHub 库**全英文化**（342,221 → 27 个中文字符）**
>
> ### 一、操作者要求与裁决
>
> > **"注意要全英文"** ⇒ 我按范围清点后请操作者选定，**采纳："排除 tools/obsolete/，其余全译"**。
>
> ### 二、清点（分层）
>
> | 范围 | 含中文 | 处置 |
> |---|---|---|
> | **B1 投稿件源**（`paper3/paper_ieee/`） | **1 个 / 72 字符** | ✅ **已全译**（`main_full.tex` 的文件头注释） |
> | **A GitHub 库**（已跟踪 2,403 个） | **1,389 个 / 342,221 字符** | ✅ 见下 |
> | B2 修订包（`SUBMISSION/`） | 13 个 | ⚠️ 多为内部报告（`evidence/`），**不对外**；`README`/`UPLOAD_CHECKLIST`/`ARCHIVE_*` 待操作者定 |
>
> ### 三、✅ 执行（三步）
>
> | 步 | 动作 | 效果 |
> |---|---|---|
> | ① | **排除 `tools/obsolete/`**（1,314 个一次性脚本 → 本地 `_removed_from_publish/tools_obsolete/`） | 中文字符 342,221 → **28,596**（**94%** 在存档脚本里，且它们本就不是维护目标） |
> | ② | **`tools/`+`src/`+`exp/`+`experiments/`+`outputs/` 全译**（三轮并行 workflow，**25/25 批成功**） | 28,596 → **105** |
> | ③ | 自处理收尾 12 个（含"中文在键上"的） | 105 → **27** |
>
> **⇒ 最终：9 个文件 / 27 个中文字符**，**全部是功能数据**：
>
> | 类别 | 文件 | 为何不能译 |
> |---|---|---|
> | **磁盘目录名 `paper合/`** | `audit/fix_paperA_round3.py`、`audit/check_paperA.py`、`audit/audit_citations.py`、`audit/verify_citations.py`、`audit/verify_dblp.py`、`audit/find_bib_placeholders.py` | **翻译会打断路径**（该目录真叫这个名字，且在发布库之外） |
> | **占位符检测正则** `待补\\|待填` | `ap3_fulltext_lint.py` | 功能性匹配模式 |
> | **审计的禁止串** `公开仓库` | `audit_submission_pdfs.py` | 审计工具的匹配列表 |
> | **shell 里的 zip 文件名** | `exp/README.md` | 命令行参数 |
>
> ### 四、✅ 完整性核验（**关键：翻译不能改代码**）
>
> | 检查 | 结果 |
> |---|---|
> | **`.py` 语法** | **232 / 232 通过**（`ast.parse`） |
> | **`.json` 解析** | **813 / 813 通过**（`json.loads`） |
> | 各批的**代码不变性**核验 | 多个 agent 独立做了 **token 流对比 / AST 掩码对比 / dict 键多重集对比** ⇒ **标识符、数字、键、路径、结构全部一致** |
> | 行尾（repo 混合 LF/CRLF） | 逐文件按**原字节**保留（agent 报告有多起"编辑工具把 CRLF 规范化"被自查追回） |
> | 断头命令（`abla`/`oindent`） | 各批均扫描：**0 处**，且未引入 |
> | 中文标点 | 转 ASCII（`（）`→`()`），数学记号（τ λ σ Γ ΔE ∇ → ≈）**保留** |
>
> ### 五、🔴 顺带修一个**自 2026-09-24 首次提交就存在**的编码错误
>
> `outputs/theory/beta_pilot/beta_pilot_results.json` **不是合法 UTF-8**：
> 字节 `0xA1 0xAA` 是 **GBK 的 em dash `—`**，被当 UTF-8 写出 ⇒ 解码失败。
> **⇒ 经典"GBK 读 / UTF-8 写"双编码事故**（本项目已知类型，见 `AGENTS.md` 的编码纪律）。
> **已修**（`tools/_p601`）：按 GBK 解回 `—` 再以 UTF-8 写出 ⇒ 现为**合法 UTF-8 + 合法 JSON**。
>
> ### 六、推送与发布
>
> | 项 | 结果 |
> |---|---|
> | 提交 | **`1ec23d1`**（`7755f70..1ec23d1`）：**1,314 删除 + 210 修改** |
> | tag | 已重打到 **`1ec23d1`** |
> | Release | 已重建：`isDraft: false`、`Latest` |
> | 远端 | `main = 1ec23d1` |
>
> **Release**：https://github.com/MoYUYao666/gap-susceptibility/releases/tag/v1.0-prl-revision
>
> ### 七、⚠️ 一处待操作者定
>
> **修订包 `SUBMISSION/P3_PRL_revision/` 里还有 13 个含中文的文件**（32,354 字符），
> 其中 `evidence/P3_EXPERIMENTS.md`（11,220）、`P3_STATS.md`（7,160）、`P3_DOWNSTREAM.md`（5,796）
> 是**内部补实验报告**，`response/P3_REVIEW_RESPONSE.md` 是应答工作文档 —— **都不交给审稿人**
> （交的是 `P3_RESPONSE_LETTER.md`，已全英文）。
> **但 `README.md`（787）、`UPLOAD_CHECKLIST.md`（763）、`ARCHIVE_WITH_ZENODO.md`（469）是给操作者看的**。
> **⇒ 待定：这三份是否也要英文？**（若日后要给编辑部看，建议英文化。）
>
> ### 八、状态
>
> - **投稿件**：**10 页 / 0 错 / 0 未定义 / 0 中文**
> - **GitHub**：`main = 1ec23d1`，Release `v1.0-prl-revision` 已发布，**仓库仍私有**
> - **剩余**：① 仓库改公开 ⇒ 拿 Zenodo DOI ⇒ 填三处 ⇒ 重编译重传
>   ② 修订包三份文档是否英文化 ③ EM 三个回复框 ④ 提交
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "全英文化" in t:
        print("  已记录")
        return 0
    if not a.apply:
        print("  （预演）")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("全英文化", "342,221 → 27", "1ec23d1", "双编码事故", "必看/待定"):
        print(f"  {'✅' if k in t2 else '🔴'} {k}")
    print(f"  HANDOFF 行数 = {len(t2.splitlines())}")
    r = subprocess.run(["gh", "release", "view", "v1.0-prl-revision", "--repo", SLUG,
                        "--json", "isDraft,tagName"], capture_output=True)
    print(f"  Release：{r.stdout.decode('utf-8', errors='replace').strip()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
