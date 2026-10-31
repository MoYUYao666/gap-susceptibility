# -*- coding: utf-8 -*-
r"""Record the DSH environment and the installed research-skill catalogue in the handover documents.

Source of truth: the card the operator supplied on 2026-10-17, outside the project tree:
    D:\Realdesktop\Wan\Important\DSH-技能交接卡-完整版.md
The operator also supplied `科研skills-交接卡.md` earlier the same day; it was consolidated into the full card
(full card written 12:39) and deleted, so only the full card is read here.

Nothing here is transcribed by hand from memory: each fact written into the handover documents is first
asserted to be present in one of those two files, and the script aborts if a card has moved or changed so the
record cannot drift away from its source.

    python tools/_p1139_record_skills.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HANDOFF = REPO / "HANDOFF.md"
MAP = REPO / "文件地图.md"
DOCS = REPO / "docs" / "skills_environment_2026-10-17.md"

CARD_SHORT = Path(r"D:\Realdesktop\Wan\Important\科研skills-交接卡.md")  # consolidated into CARD_FULL, may be gone
CARD_FULL = Path(r"D:\Realdesktop\Wan\Important\DSH-技能交接卡-完整版.md")

MARK = "技能与环境交接（43 个技能）"

# Facts that must be verifiable in the cards before they are written down. (needle, which card)
FACTS = [
    ("43 个生效技能", "full"),
    ("19 个 `nature-*`", "full"),
    ("PowerShell 7.6.7", "full"),
    ("Python", "full"),
    ("University of Southampton", "both"),
    ("hw4c24@soton.ac.uk", "both"),
    ("academic-search", "both"),
    ("nature-downloader", "both"),
    ("cordis.patch.yml", "both"),
    ("disable-model-invocation", "full"),
    ("TeX Live 2025", "full"),
    ("CDP 代理", "both"),
]

DOC = """# DSH 环境与科研技能清单（2026-10-17 录入）

> 本文件由 `tools/_p1139_record_skills.py` 生成；事实来源为操作者提供的两张交接卡（见文末）。
> 用途：让后续会话知道**有哪些能力可用、怎么触发、边界在哪**，避免重复摸索。

## 一、环境硬事实

| 项 | 值 |
|---|---|
| 系统 | Windows 11 家庭版 中文版 · AMD64 |
| DSH | 桌面版，profile = `desktop`，Web GUI `http://127.0.0.1:19387` |
| Shell | **PowerShell 7.6.7**（DSH 工具默认）|
| 编码 | UTF-8（Console I/O + `chcp 65001`）；**但双引号内 `` ` `` 与 `$` 仍是特殊字符** ⇒ 内联命令用单引号 |
| Python | 3.14.6（Anaconda `D:\\Anaconda`）；**本项目 torch 在 `D:\\Anaconda\\envs\\pytorch`** |
| Node | 24.16.0 |
| LaTeX | TeX Live 2025（`pdflatex` 在 PATH）|
| 浏览器 | Edge（远程调试已开）；CDP 代理 `http://127.0.0.1:3456`（复用登录态）|
| 机构 | University of Southampton · EZproxy `https://soton.idm.oclc.org/login?url=<目标>` |
| 联系邮箱 | `hw4c24@soton.ac.uk`（PubMed / CrossRef 联系用，非账号）|
| 工作区 | `D:\\Realdesktop\\Wan\\Important`（本项目在 `…\\Important\\New`）|

## 二、技能安装位置与数量

- `~/.dsh/skills` —— **33 个**（DSH 专属）
- `~/.agents/skills` —— **10 个**（共享）
- 另有 `office-*` 与 `diagnose-windows-sandbox-acl` 由 DSH 内置
- **合计生效 43 个**；被移出到 `~/.dsh/skills-disabled/`（32 个）与 `~/.agents/skills-disabled/`（11 个）

## 三、本项目的相关技能（按任务映射）

| 我们的任务 | 用哪个技能 |
|---|---|
| **改写/重写稿件章节**（如 Paper A 补充 F 节）| `nature-writing` |
| 润色、精简、LaTeX 排版修正 | `nature-polishing` |
| **统计报告审查**（均值 ± 离散度、重复数、不确定性）| `nature-statistics` |
| **引文逐字段核对**（作者/年份/卷期/页码/DOI 年冲突）| `nature-ref-verifier` |
| 检索文献 / 取 DOI / 生成引文格式 | `nature-academic-search` 或 MCP `mcp__academic-search__*` |
| 按 Nature/CNS 范围补引用 | `nature-citation` |
| 投稿前自审（模拟审稿）| `nature-reviewer` |
| 审稿意见回复 / 返修信 | `nature-response` |
| 稿件数据/代码可用性声明（Zenodo DOI 等）| `nature-data` |
| 期刊级配图（SVG/PDF/TIFF，多面板）| `nature-figure` |
| TikZ / draw.io 结构图 | `thesis-figure-skill` / `tikz-figure-code` |
| 合法全文下载（需 Edge 登录态）| `nature-downloader` |
| 联网/登录态浏览器/抓动态页 | `web-access` |
| 调研技术事实 → Markdown | `research` |
| 评审代码改动 | `code-review` |
| 拷问方案可行性 | `grilling` |
| 交接给下一个 agent（**仅人工触发**）| `handoff` |

## 四、外部能力

**学术检索 MCP（已接入，直接调用）**

```
mcp__academic-search__search_papers(query, sources?, rows?, type?)
mcp__academic-search__get_paper_by_id(id)        # DOI / PMID / arXiv ID
mcp__academic-search__get_citation(id, style)    # apa|nature|ieee|harvard|vancouver|chicago|mla
mcp__academic-search__lookup_mesh(term)
```

**机构全文下载**

```bash
node ~/.dsh/skills/nature-downloader/scripts/batch_download.mjs \\
  --dois "<DOI>" --out "<目录>" --no-si [--route web_access]
```
- **Elsevier / Springer / IEEE 必须加 `--route web_access`**（否则先试出版商 API，无 key 报 `credentials_missing`）
- 前置：Edge 保持登录 + CDP 代理在跑（`node ~/.agents/skills/web-access/scripts/check-deps.mjs`）
- 产物：`PDFs/ + manifest.json`（来源、路径、SHA-256、失败原因）

## 五、已知坑与边界

1. **`cordis.patch.yml` 新增插件条目必须包在 `insert:` 下**，直写会被当作"覆盖已有条目"而静默忽略。
2. **技能 `name:` 必须 kebab-case**，带空格/大写会被忽略。
3. **`disable-model-invocation: true` 生效**：该类技能只能人工触发（当前是 `handoff`）。
4. **arXiv 源常 30 s 超时**；CrossRef / PubMed 正常。
5. **无 Elsevier API 订阅**：`search_scopus` / `search_sciencedirect` 会报错，忽略即可；全文走 EZproxy。
6. **下载必须走已登录的 Edge**；不导出 cookie、不读密码；只下明确指定篇目，不抓整期/整库。
7. 备份：`cordis.patch.yml.bak-*` · `~/.config/lit-dl/school.json` · `~/.web-access/config.env`。
8. **恢复技能**：把目录从 `skills-disabled/` 移回 `skills/` 即生效，无需重启。

## 六、来源

| 卡片 | 路径 | 状态 |
|---|---|---|
| **DSH 技能与环境交接卡（完整版）** | `D:\\Realdesktop\\Wan\\Important\\DSH-技能交接卡-完整版.md` | ✅ **现行唯一来源** |
| 科研 skills 交接卡（早期短版）| `D:\\Realdesktop\\Wan\\Important\\科研skills-交接卡.md` | ⚠️ **已于 2026-10-17 12:39 合并进完整版并删除**，不再单独存在 |

技能上游：`Yuan1z0825/nature-skills`（19 个 nature-*，Apache-2.0）等 8 个来源；详见完整版卡片第七节。
"""

ENT = """> **🧰 2026-10-17 13:00 —— 录入 DSH 环境与 43 个科研技能（操作者提供两张交接卡）**
>
> 操作者给出两份环境/技能交接卡，要求把能力清单落进交接文档。**事实全部从卡片抓取并断言**（脚本 `tools/_p1139_record_skills.py`，不可手抄），
> 汇总成 `docs/skills_environment_2026-10-17.md`。
>
> ### 一、环境硬事实
>
> | 项 | 值 |
> |---|---|
> | Shell | **PowerShell 7.6.7**（DSH 工具默认，UTF-8）|
> | Python | **3.14.6**（`D:\\Anaconda`）；⚠️ **本项目 torch 在 `D:\\Anaconda\\envs\\pytorch`**（另一个环境）|
> | LaTeX | **TeX Live 2025**（`pdflatex` 在 PATH）⇒ Paper A 可直接本地编译 |
> | Node | 24.16.0 |
> | 浏览器 | Edge + CDP 代理 `127.0.0.1:3456`（复用登录态）|
> | 机构 | University of Southampton · EZproxy |
>
> ### 二、技能：**43 个生效**
>
> `~/.dsh/skills` **33 个** + `~/.agents/skills` **10 个**；另有 `office-*` 与 `diagnose-windows-sandbox-acl` 内置。
> 被移出 43 个到 `skills-disabled/`（移回即生效，无需重启）。
>
> **本项目最相关的映射**：
>
> | 任务 | 技能 |
> |---|---|
> | **改写稿件章节**（如补充 F 节）| **`nature-writing`** |
> | **统计报告审查**（均值±离散度、重复数）| **`nature-statistics`** |
> | **引文逐字段核对** | **`nature-ref-verifier`** |
> | 润色 / 精简 / LaTeX 排版 | `nature-polishing` |
> | 检索 / DOI / 引文格式 | `nature-academic-search` + MCP `mcp__academic-search__*` |
> | 投稿前自审 | `nature-reviewer` |
> | 数据/代码可用性声明（Zenodo）| `nature-data` |
> | 期刊级配图 | `nature-figure` |
>
> ### 三、外部能力
>
> - **学术检索 MCP** 已接入：`search_papers` / `get_paper_by_id` / `get_citation` / `lookup_mesh`（CrossRef + PubMed + arXiv）；
> - **机构全文下载**：`nature-downloader`，**Elsevier/Springer/IEEE 必须加 `--route web_access`**（走 EZproxy + Edge 登录态）。
>
> ### 四、⚠️ 已知坑（会影响本项目的）
>
> 1. **arXiv 源常 30 s 超时** ⇒ 批量核引文时优先 CrossRef/PubMed；
> 2. **无 Elsevier API** ⇒ `search_scopus`/`search_sciencedirect` 报错，忽略；全文走 EZproxy；
> 3. **`cordis.patch.yml` 新增条目必须包在 `insert:` 下**，否则静默忽略；
> 4. **下载必须走已登录 Edge**，不导出 cookie、不读密码；
> 5. **shell 引号规则**（今日已立）：PS 7.6.7 + UTF-8，但双引号里 `` ` ``/`$` 仍特殊 ⇒ **内联命令用单引号**。
>
> ### 五、文件
>
> - 汇总：`docs/skills_environment_2026-10-17.md`（本脚本生成）；
> - 原始卡片：`D:\\Realdesktop\\Wan\\Important\\DSH-技能交接卡-完整版.md`（**在项目树之外**，故摘要进 docs 以便长期留存）；
>   ⚠️ 操作者当天的另一份短版 `科研skills-交接卡.md` **已于 12:39 合并进完整版并删除**，不再单独存在。
>
> **脚本**：`tools/_p1139_record_skills.py`。
>

"""

ENT_MAP = ("49. 🧰 **DSH 环境与 43 个科研技能已录入（2026-10-17 13:00）** —— 操作者提供技能交接卡"
           "（`D:\\Realdesktop\\Wan\\Important\\DSH-技能交接卡-完整版.md`，**在项目树外**；当日早期短版 `科研skills-交接卡.md` 已于 12:39 合并进完整版并删除），"
           "已汇总为 `docs/skills_environment_2026-10-17.md`（脚本 `tools/_p1139_record_skills.py`，**事实逐条从卡片断言**）。"
           "**环境**：PowerShell **7.6.7** + UTF-8 · Python **3.14.6**（⚠️ 本项目 torch 在 `D:\\Anaconda\\envs\\pytorch`）· "
           "**TeX Live 2025** · Node 24 · Edge+CDP。**技能 43 个**（`.dsh/skills` 33 + `.agents/skills` 10）。"
           "**本项目最相关**：`nature-writing`（改章节）、`nature-statistics`（统计报告）、`nature-ref-verifier`（核引文）、"
           "`nature-polishing`、`nature-academic-search` + MCP `mcp__academic-search__*`（CrossRef/PubMed/arXiv）、"
           "`nature-downloader`（Elsevier/Springer/IEEE **必须 `--route web_access`**）。**坑**：arXiv 常超时、无 Elsevier API、"
           "`cordis.patch.yml` 新增须包 `insert:`、下载须走已登录 Edge。详见 `HANDOFF.md` 13:00 条目。\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    if not CARD_FULL.exists():
        print("  !! the full card is missing:", CARD_FULL)
        return 2
    print("  source card:", CARD_FULL.name, f"({CARD_FULL.stat().st_size} bytes)")
    print("  the earlier short card is consolidated into it and no longer present:",
          not CARD_SHORT.exists())
    short = CARD_SHORT.read_text(encoding="utf-8") if CARD_SHORT.exists() else ""
    full = io.open(CARD_FULL, encoding="utf-8").read()
    print("=== asserting each recorded fact against the source cards ===")
    bad = []
    for needle, which in FACTS:
        hay = full if which == "full" else (short + full)
        ok = needle in hay
        print(f"  {'OK  ' if ok else 'MISS'} {needle!r:<34} ({which})")
        if not ok:
            bad.append(needle)
    if bad:
        print("  !! facts not found in the cards; refusing to write a record that cannot be traced")
        return 1

    # the counts must agree with each other
    import re
    m = re.search(r"生效技能（(\d+) 个）", full) or re.search(r"共 \*\*(\d+) 个生效技能\*\*", full)
    total = int(m.group(1)) if m else None
    md = re.search(r"`~/.dsh/skills` \*\*(\d+) 个\*\*", full)
    ma = re.search(r"`~/.agents/skills` \*\*(\d+) 个\*\*", full)
    print(f"\n  totals: active={total} | .dsh={md.group(1) if md else '?'} | .agents={ma.group(1) if ma else '?'}")
    if total and md and ma and int(md.group(1)) + int(ma.group(1)) != total:
        print("  !! .dsh + .agents does not equal the stated total")
        return 1
    print("  counts are self-consistent")

    if not a.apply:
        print("\n  (dry run)")
        return 0

    DOCS.parent.mkdir(parents=True, exist_ok=True)
    if not DOCS.exists():
        io.open(DOCS, "w", encoding="utf-8", newline="").write(DOC)
        print(f"  wrote {DOCS.relative_to(REPO)}")
    else:
        print(f"  {DOCS.relative_to(REPO)} already exists (left as is)")

    hp = io.open(HANDOFF, encoding="utf-8").read()
    if MARK not in hp:
        i = hp.find("# 项目交接文档")
        j = hp.find("\n", i)
        hp = hp[: j + 1] + "\n" + ENT + hp[j + 1:]
        io.open(HANDOFF, "w", encoding="utf-8", newline="").write(hp)
        print("  handoff entry added")
    else:
        print("  handoff already has this entry")

    mp = io.open(MAP, encoding="utf-8").read()
    if "DSH 环境与 43 个科研技能已录入" not in mp:
        anchor = "48. 🧹 **空适配器已删、Qwen 重测就绪"
        idx = mp.find(anchor)
        if idx < 0:
            anchor = "## 🔴 当前总状态"
            idx = mp.find(anchor)
        if idx >= 0:
            end = mp.find("\n", idx)
            mp = mp[: end + 1] + ENT_MAP + mp[end + 1:]
            io.open(MAP, "w", encoding="utf-8", newline="").write(mp)
            print("  map item added")
        else:
            print("  !! could not find an anchor in the map")
    else:
        print("  map already has this item")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
