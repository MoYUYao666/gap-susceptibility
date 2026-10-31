# DSH 环境与科研技能清单（2026-10-17 录入）

> 本文件由 `tools/_p1139_record_skills.py` 生成；事实来源为操作者提供的两张交接卡（见文末）。
> 用途：让后续会话知道**有哪些能力可用、怎么触发、边界在哪**，避免重复摸索。

## 一、环境硬事实

| 项 | 值 |
|---|---|
| 系统 | Windows 11 家庭版 中文版 · AMD64 |
| DSH | 桌面版，profile = `desktop`，Web GUI `http://127.0.0.1:19387` |
| Shell | **PowerShell 7.6.7**（DSH 工具默认）|
| 编码 | UTF-8（Console I/O + `chcp 65001`）；**但双引号内 `` ` `` 与 `$` 仍是特殊字符** ⇒ 内联命令用单引号 |
| Python | 3.14.6（Anaconda `D:\Anaconda`）；**本项目 torch 在 `D:\Anaconda\envs\pytorch`** |
| Node | 24.16.0 |
| LaTeX | TeX Live 2025（`pdflatex` 在 PATH）|
| 浏览器 | Edge（远程调试已开）；CDP 代理 `http://127.0.0.1:3456`（复用登录态）|
| 机构 | University of Southampton · EZproxy `https://soton.idm.oclc.org/login?url=<目标>` |
| 联系邮箱 | `hw4c24@soton.ac.uk`（PubMed / CrossRef 联系用，非账号）|
| 工作区 | `D:\Realdesktop\Wan\Important`（本项目在 `…\Important\New`）|

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
node ~/.dsh/skills/nature-downloader/scripts/batch_download.mjs \
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
| **DSH 技能与环境交接卡（完整版）** | `D:\Realdesktop\Wan\Important\DSH-技能交接卡-完整版.md` | ✅ **现行唯一来源** |
| 科研 skills 交接卡（早期短版）| `D:\Realdesktop\Wan\Important\科研skills-交接卡.md` | ⚠️ **已于 2026-10-17 12:39 合并进完整版并删除**，不再单独存在 |

技能上游：`Yuan1z0825/nature-skills`（19 个 nature-*，Apache-2.0）等 8 个来源；详见完整版卡片第七节。
