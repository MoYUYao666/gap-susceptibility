# -*- coding: utf-8 -*-
r"""Point the project instruction files at the skills/environment inventory.

The full inventory lives in `docs/skills_environment_2026-10-17.md`; these agent-facing files only need a
short pointer so a future session knows the capability list exists and where the boundaries are. Appended
idempotently (the section is skipped if its marker is already present).

    python tools/_p1140_point_agents_at_skills.py [--apply]
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MARK = "科研技能与环境清单（2026-10-17 录入）"

SECTION = """## 🧰 科研技能与环境清单（2026-10-17 录入）

完整清单见 **`docs/skills_environment_2026-10-17.md`**（事实来源：`D:\\Realdesktop\\Wan\\Important\\DSH-技能交接卡-完整版.md`）。
**环境**：PowerShell 7.6.7（UTF-8）· Python 3.14.6（`D:\\Anaconda`，**本项目 torch 在 `envs\\pytorch`**）· TeX Live 2025 · Node 24 · Edge + CDP 代理。
**技能 43 个**（`~/.dsh/skills` 33 + `~/.agents/skills` 10）。

本项目最相关的几个，**用之前先 `skill` 加载**：

| 任务 | 技能 |
|---|---|
| 改写/重构稿件章节 | `nature-writing` |
| 润色、精简、LaTeX 排版 | `nature-polishing` |
| 统计报告审查（均值±离散度、重复数、不确定性）| `nature-statistics` |
| 引文逐字段核对 | `nature-ref-verifier` |
| 检索 / DOI / 引文格式 | `nature-academic-search`（或 MCP `mcp__academic-search__*`）|
| 投稿前自审 | `nature-reviewer` |
| 数据/代码可用性声明 | `nature-data` |
| 期刊级配图 | `nature-figure` |

**边界**：无 Elsevier API（`search_scopus`/`search_sciencedirect` 会报错）· arXiv 源常 30 s 超时 · 全文下载必须走已登录的 Edge（Elsevier/Springer/IEEE 加 `--route web_access`）· `cordis.patch.yml` 新增条目必须包在 `insert:` 下。
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    for name in ("AGENTS.md", "CLAUDE.md"):
        f = REPO / name
        if not f.exists():
            print(f"  {name}: missing, skipped")
            continue
        t = io.open(f, encoding="utf-8").read()
        if MARK in t:
            print(f"  {name}: already present")
            continue
        print(f"  {name}: would append {len(SECTION.splitlines())} lines")
        if a.apply:
            io.open(f, "w", encoding="utf-8", newline="").write(t.rstrip("\n") + "\n\n" + SECTION)
            print(f"  {name}: appended")
    if not a.apply:
        print("  (dry run)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
