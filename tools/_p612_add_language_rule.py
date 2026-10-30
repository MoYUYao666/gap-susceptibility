# -*- coding: utf-8 -*-
r"""把"产出物一律英文、对话回复用中文"固化为项目规则（2026-10-14）。

## 操作者要求

> **"后续的实验与结果等等都直接用英文来写，你给我输出的结论用中文即可"**

## 为什么必须写进 `AGENTS.md`

这是**长期约定**，不是本轮的一次性任务。**只记在对话里 = 换个会话就丢**
（本项目已多次因"约定只在聊天里"而返工）。**⇒ 写进 `AGENTS.md` 与 `CLAUDE.md`**（两份都是 agent 的读取入口）。

    python tools\_p612_add_language_rule.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

RULE = """
## 🔴 语言规则（用户明确要求，最高优先级）

> **"后续的实验与结果等等都直接用英文来写，你给我输出的结论用中文即可"** —— 2026-10-14 操作者原话

**产出物一律英文**（写进文件的东西）：

| 范围 | 要求 |
|---|---|
| **代码** | 变量名、函数名、注释、docstring、`print`/`argparse` 消息 **全英文** |
| **实验结果与归档** | JSON 的**键与值**、字段说明、`note`/`desc` 类字段 **全英文** |
| **脚本输出** | 控制台/日志文字 **全英文** |
| **文档** | `README.md`、`docs/*.md`、报告、清单 **全英文**（若该文档面向外部或长期留存） |
| **稿件** | 本来就是英文，**不得出现中文**（含注释、宏定义、`%` 注释） |
| **GitHub 发布库** | **全英文**；**唯一例外**见下 |

**唯一例外（必须保留中文）——"功能数据"**：

- **真实存在的文件/目录名**（如 `paper合/`、`outputs/_serial_logs/同秩对照_*.log`）
  ⇒ **翻译会打断路径**，必须原样保留
- **检测/匹配用的正则模式与字符串列表**（如占位符检测器里的 `待补|待填`、
  审计工具的禁止串 `公开仓库`）⇒ 属**功能**而非文字
- **shell 命令里作为参数的文件名**（如 `zip 结果.zip`）

**⇒ 判据：改它会不会让程序找不到文件、或改变匹配语义？会 ⇒ 不改；不会 ⇒ 必须改英文。**

**对话回复用中文**（说给操作者听的东西）：结论、进度、决策、报错解释 —— **中文**。
**报告与消息里的技术名词、文件名、代码片段照原样**（不硬译）。

**⚠️ 引用既有中文文档时**：可以引用，但**新建的产出物一律英文**。
**⚠️ 反例（本项目已发生）**：用 PowerShell `Add-Content` 往 UTF-8 文件追加中文 ⇒ **GBK 字节混入、文件非法 UTF-8**
⇒ **向已存在文件追加内容，必须用 Python 显式 `encoding="utf-8"`**。
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  （预演）")
        return 0
    done = []
    for name in ("AGENTS.md", "CLAUDE.md"):
        p = REPO / name
        if not p.exists():
            print(f"  ⚠️ 无 {name}")
            continue
        t = io.open(p, encoding="utf-8", errors="replace").read()
        if "语言规则（用户明确要求" in t:
            print(f"  {name}：已含该规则")
            continue
        bak = p.with_suffix(p.suffix + ".bak_p612")
        if not bak.exists():
            shutil.copy2(p, bak)
        # 插到"发布边界"之前（语言规则与产出物相关，紧跟其后合适）
        k = t.find("## 🔴 发布边界")
        if k < 0:
            k = t.find("## 关键约束")
        if k < 0:
            t2 = t.rstrip() + "\n" + RULE
        else:
            t2 = t[:k] + RULE.strip() + "\n\n" + t[k:]
        io.open(p, "w", encoding="utf-8", newline="").write(t2)
        done.append(name)
        print(f"  ✅ {name}：{len(t):,} → {len(t2):,} 字符")
    for name in done:
        t = io.open(REPO / name, encoding="utf-8").read()
        ok = "语言规则（用户明确要求" in t and "功能数据" in t and "PaperPowerShell" not in t
        print(f"  {'✅' if ok else '🔴'} {name} 复核（含规则与例外）｜ {len(t.splitlines())} 行")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
