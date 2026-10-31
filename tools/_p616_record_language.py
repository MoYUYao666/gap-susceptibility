# -*- coding: utf-8 -*-
r"""Record the language rule and its scope decision in the handoff document.

Operator (2026-10-14):
1. "后续的实验与结果等等都直接用英文来写，你给我输出的结论用中文即可"
2. Scope decision, chosen among four options: "只管今后，存量不动"

    python tools/_p616_record_language.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **🔤 2026-10-14 08:00 —— 操作者立**语言规则**并裁定范围：产出物英文、对话中文、存量不动**
>
> ### 一、操作者要求（2026-10-14）
>
> > **"后续的实验与结果等等都直接用英文来写，你给我输出的结论用中文即可"**
>
> **⇒ 已固化进 `AGENTS.md` 与 `CLAUDE.md`**（两份都是 agent 的读取入口；只记在对话里 = 换会话就丢，
> 本项目已多次因"约定只在聊天里"而返工）。
>
> ### 二、范围裁决（四选一 ⇒ 采纳）
>
> > **"只管今后，存量不动"**
>
> | 对象 | 语言 | 现状 |
> |---|---|---|
> | **今后新建的产出物**（代码/注释/print、结果 JSON、报告、清单、README） | **英文** | ✅ 本会话尾段已按此执行（`_p613`–`_p616` 四个脚本全英文） |
> | **已有存量**：`tools/` 下 **1,320 个含中文 `.py`（328,521 字符）** | **保持原样** | ⏭ **豁免**（历史记录，非维护目标） |
> | **交接文档**（`HANDOFF.md`、`文件地图.md`、`docs/`） | **中文** | 用途是**向操作者汇报** |
> | **对话回复** | **中文** | 结论/进度/决策/报错解释 |
> | **稿件 / 修订包 / GitHub 发布库** | **英文** | ✅ 已完成 |
>
> **⇒ 判据（某文件该用哪种语言）**：**它写给谁看？**
> 给**外部**（期刊/审稿人/公众）⇒ **英文**；给**操作者**（汇报/导航/决策）⇒ **中文**；
> 给**机器**（路径/匹配模式）⇒ **按原样**。
>
> **⚠️ 存量豁免的理由**：`tools/_p4xx_*.py` 是**一次性修订脚本**，价值在于"记录当时怎么做的"；
> **改动它们无收益，且会让 HANDOFF 的按行号引用失效**。
>
> ### 三、唯一例外：**功能数据必须保留中文**
>
> | 类别 | 实例 | 理由 |
> |---|---|---|
> | **真实文件/目录名** | `paper合/`、`outputs/_serial_logs/同秩对照_CLIP_B-32_r4_both.log` | **翻译会打断路径** |
> | **检测/匹配模式** | 占位符正则 `待补\\|待填`、审计禁止串 `公开仓库` | 属**功能**而非文字 |
> | **命令参数里的文件名** | `zip 结果.zip` | 命令行参数 |
>
> **⇒ 判据：改它会不会让程序找不到文件、或改变匹配语义？会 ⇒ 不改；不会 ⇒ 必须改英文。**
>
> ### 四、固化的反例（避免重犯）
>
> **用 PowerShell `Add-Content` 往 UTF-8 文件追加中文 ⇒ GBK 字节混入、文件非法 UTF-8**（我的第 36 个错）。
> **⇒ 向已存在文件追加内容，一律用 Python 显式 `encoding="utf-8", newline=""`。**
>
> ### 五、存量盘点（`tools/_p614`，供日后参考，**本轮不动**）
>
> | 分组 | 脚本数 | 中文字符 |
> |---|---|---|
> | 未归类（无 `_pNNN` 前缀） | 673 | 169,779 |
> | P3 修订（`_p4xx`–`_p5xx`） | 231 | 71,856 |
> | 更早论文（`_p1xx`–`_p3xx`） | 257 | 42,862 |
> | 早期（`_p0xx`） | 145 | 40,281 |
> | 本会话工具（`_p6xx`） | 14 | 3,743 |
> | **合计** | **1,320** | **328,521** |
>
> ### 六、状态
>
> - **规则已生效**：`AGENTS.md` 6,855 字符 / 143 行；`CLAUDE.md` 2,644 字符 / 75 行（均含语言规则 + 范围裁决）
> - **本会话新建产出物**：`RELEASE_NOTES.md`（GitHub 公开，英文）、`_p613`–`_p616` 脚本（英文）
> - **剩余**：① 仓库改公开 ⇒ 拿 Zenodo DOI ⇒ 填三处 ⇒ 重编译重传
>   ② 修订包两份**面向操作者**的文档（`UPLOAD_CHECKLIST.md`、`ARCHIVE_WITH_ZENODO.md`）按新判据**留中文**
>   ③ `p3d_summary.json` 指纹更新 ④ EM 三个回复框 ⑤ 提交
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "操作者立**语言规则**" in t:
        print("  already recorded")
        return 0
    if not a.apply:
        print("  (dry run)")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("操作者立**语言规则**", "只管今后，存量不动", "328,521", "功能数据"):
        print(f"  {'OK ' if k in t2 else 'BAD'} {k}")
    print(f"  HANDOFF lines = {len(t2.splitlines())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
