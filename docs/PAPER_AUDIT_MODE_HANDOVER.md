# 论文审核模式（Paper Audit Mode）—— 完整交接与提示词

> 版本 1.0 ｜ 2026-10-18 ｜ 适用：本仓库（Cross-Modal Alignment under PEFT）的稿件审核
> 本文档有两种用法：
> 1. **直接复制 §1 的提示词**，交给"创造模式"（新会话 / 另一个 agent）从零或半从零创建这套模式；
> 2. **把整份文档作为交接规格书**，按 §3–§14 逐条验收。
>
> 当前仓库里**已经有一份实现**（§16 给出路径与基线）；创造模式可以"复刻并独立验证"，也可以"在现有实现上补齐"。两种都要求按 §3 的 Definition of Done 交付证据。

---

## 1. 可直接粘贴的提示词（给创造模式）

```text
你在仓库 D:\Realdesktop\Wan\Important\New（Cross-Modal Alignment under PEFT，Windows + PowerShell 7 + Python 3.14 + TeX Live 2025）中创建一个名为 Paper Audit Mode 的"论文审核模式"。

目标：把"审一篇稿子"固化成可复跑、可追溯、有判定标准的流程。审核轮不改稿；修复另开修复轮并留证据。全程离线，不依赖第三方 Python 包。

必须交付：
1. tools/paper_audit/ Python 包（可用 `python -m tools.paper_audit` 调用），文件包括：
   __init__.py、__main__.py、cli.py、model.py、registry.py、profiles.py、texutil.py、checks.py、report.py、README.md、templates/、freeze/。
2. 检查注册表：86 条检查，分 A-J 十个维度（A 可复现/取证，B 构建，C 结构，D 期刊合规，E 文献，F 数字溯源与一致性，G 排版渲染，H 数据/伦理/声明，I 投稿包与冻结安全，J 证据与交接）。每条检查必须有唯一 id、维度、严重度（P0/P1/P2/P3）、标题、方法说明；能自动化的必须实现，不能自动化的标 MANUAL 并写清需要什么证据。
3. 9 个 profile：paperA_nc（Paper A/Neurocomputing）、paperA_springer、p3_prl（P3/PRL）、a1_nn（A1/Neural Networks）、a23_joe（A23/IEEE JOE）、prl_commentary（PRL Commentary），以及 generic_elsevier / generic_ieee / generic_prl 三个模板。每个 profile 至少配置：manuscript 路径、tex/pdfs/logs、页数/摘要词数/关键词/highlights/盲审等 limits、required_sections、required_declarations、forbidden_strings、key_numbers、claim ledger 与一致性门禁命令（供 F-04/F-05 执行并校验预期字符串）、freeze_paths、包目录与门户名映射、build_command、staged_command。
4. CLI 契约：
   - `python -m tools.paper_audit list-profiles`
   - `python -m tools.paper_audit list-checks [--dimension A] [--json]`
   - `python -m tools.paper_audit freeze --profile <id> [--write]`
   - `python -m tools.paper_audit audit --profile <id> [--staged] [--out DIR] [--fail-on P0|P1|NONE] [--command-timeout N]`
   - `python -m tools.paper_audit selftest`
   - `python -m tools.paper_audit render-template --kind audit|fix|readiness`
   - audit 默认写 docs/audits/AUD-<profile>-<UTC>.md 和 .json；默认 --fail-on P1，有 P0/P1 FAIL 时退出码 1。
5. 报告：JSON 是机器可读的单一真相源，至少含 audit_id、profile、manuscript、generated_at、git_commit、git_branch、git_dirty、verdict、grade、counts、environment、commands、artifacts（SHA-256）、findings（check_id/dimension/severity/title/status/message/evidence/remediation）、checks（注册表快照）；Markdown 报告含判定、blocker、十维覆盖表、逐条 findings、命令、环境、哈希。
6. 判定规则：P0/P1 FAIL 或 ERROR = BLOCKED（grade D）；仅 P2 FAIL = READY-WITH-MINOR（B）；否则 READY（A）。SKIP 不等于 PASS；MANUAL 必须具名审核人签收。
7. 冻结机制：freeze --write 为冻结件（SUBMISSION/、PRL 的 UPLOAD/）记录逐文件 SHA-256；audit 的 I-04 重新计算并报告 added/removed/changed，任何变化都是 P0。不得改动已投出的冻结件。
8. 三套模板：审核报告（AUDIT_REPORT_TEMPLATE.md）、修复证据（FIX_EVIDENCE_TEMPLATE.md，要求 check id + file:line before/after + 验证命令 + 冻结哈希）、投稿就绪清单（SUBMISSION_READINESS_TEMPLATE.md）。
9. 中文协议文档 docs/PAPER_AUDIT_MODE.md：核心原则（证据优先、冻结优先、不自我认证、修复与审核分离、文档收尾）、严重度/判定、A-J 维度表、86 条检查全表、9 阶段流程（冻结基线→加载→采集→构建验证→数字溯源→包/冻结→报告→修复轮→签收复跑→归档）、角色分离、命令速查、新增稿件/检查/模板的方法、禁止事项、口径变更记录、当前基线。
10. 一个可被 DSH 加载的 skill：~/.dsh/skills/paper-audit/SKILL.md（YAML frontmatter：name/description/compatibility/metadata；正文写触发词、首步命令、profile 表、判定、冻结纪律、修复轮、自检与报告要求；触发词包含"论文审核/复审/投稿前终检/在审稿冻结检查/逐条核对"）。
11. 把首轮全量审核报告归档到 docs/audits/ 并生成 README.md 索引；运行 selftest 并记录结果。

硬性约束：
- 不修改任何稿件；不改冻结件；不为了让门禁通过而修改检查口径/严重度。
- 离线：只用标准库 + TeX Live 的 pdfinfo/pdftotext/pdffonts/pdflatex。
- Windows/UTF-8 兼容；命令输出英文（报告与代码英文，协议文档中文）。
- 每条 PASS/FAIL 必须可指到证据（文件、日志计数、命令输出、SHA-256）；禁止"应该没问题"。
- 实现前先读本仓库已有参考实现（若存在）：tools/paper_audit/ 与 docs/PAPER_AUDIT_MODE.md；逐文件对比并说明复刻差异。

验收（必须逐条执行并贴输出）：
1) python -m tools.paper_audit selftest → 注册表 86 条、9 个 profile、模板齐全、冻结文件哈希全部校验通过；
2) 对 6 个稿件 profile 跑 audit --fail-on NONE → 0 个 P0/P1 FAIL，判定全部 READY 或 READY-WITH-MINOR，报告 JSON/MD 落盘；
3) 对 paperA_nc 跑 audit --staged → 独立编译检查（I-03）PASS；
4) 报告归档 docs/audits/ 并有 README 索引；
5) git status 干净（除报告/工具/文档外无稿件改动）；
6) 输出最终验收表：profile / audit id / verdict / pass / fail / warn / manual / skip / 报告路径。
```

> 使用提示：若创造模式所在会话看不到本仓库历史，把本文件一起发过去；§3–§14 是它的规格书，
> §15 是已知坑，§16 是当前实现的基线，§17 是扩展方式。

---

## 2. 背景与目标

### 2.1 为什么需要

本仓库同时维护 5 篇稿件（Paper A、P3、A1、A23、PRL Commentary），状态各异：
有的在审（冻结）、有的待投、有的刚做完修回。此前的审核靠一次性脚本与人工清单，
存在三个问题：

1. **不可复跑**：换一个会话/一个 agent 就不知道上次怎么审的；
2. **口径漂移**：页数、摘要词数、实验计数、退役措辞容易在多次修改后复活；
3. **责任不清**：报告说"已核对"，但没有证据；冻结件有没有被动过无人校验。

### 2.2 目标

| 目标 | 落地方式 |
|---|---|
| 标准化 | 86 条检查 + 固定严重度 + 固定判定规则 |
| 可执行 | 一条 CLI 命令 + 机器可读 JSON |
| 可复现 | 报告记录 commit/环境/命令/哈希 |
| 可交接 | 中文协议 + 模板 + skill + 归档报告 |
| 可扩展 | registry/profiles 数据驱动，新增稿件不改引擎 |
| 安全 | 冻结件 SHA-256 基线与 I-04 校验 |

### 2.3 不做什么

- 不审"科学想法是否新颖"（那是同行评审/`nature-reviewer` 的职责）；
- 不替代人工判断（MANUAL 项必须签收）；
- 不修改稿件（审核轮只读；修复是独立修复轮）；
- 不联网查期刊 Guide 或文献（离线；期刊规则写进 profile）。

---

## 3. 验收标准（Definition of Done）

| # | 项 | 验证方式 | 通过标准 |
|---|---|---|---|
| D1 | 包可导入、CLI 可用 | `python -m tools.paper_audit list-profiles` | 列出 9 个 profile，无异常 |
| D2 | 注册表完整 | `list-checks` / `selftest` | 86 条，id 唯一，维度合法，severity 合法 |
| D3 | 检查可执行 | 任一 profile 跑 audit | findings 覆盖 86 条，无 ERROR，SKIP 均有原因 |
| D4 | 报告结构 | 检查 JSON | 含 §9 全部字段；Markdown 含判定/blocker/十维表/命令/环境/哈希 |
| D5 | 判定正确 | 构造一个 P1 FAIL（可临时删 bib 条目于临时副本） | verdict=BLOCKED，退出码 1（--fail-on P1） |
| D6 | 冻结校验 | 修改冻结文件副本/临时 profile | I-04 FAIL 且 severity=P0 |
| D7 | 构建检查 | 有 log 的 profile | B-01..B-09 有明确 PASS/FAIL，不误报 |
| D8 | 数字溯源 | paperA/p3/a23/prl profile | F-04/F-05 运行配置的门禁并校验预期字符串 |
| D9 | 独立编译 | paperA_nc `--staged` | I-03 PASS（或 profile 无 staged_command 时 SKIP 并说明） |
| D10 | 模板齐全 | `render-template` 三种 | 均输出非空 Markdown |
| D11 | 协议完整 | 人工检查 `docs/PAPER_AUDIT_MODE.md` | 含 86 条全表 + 9 阶段 + 角色 + 禁止事项 |
| D12 | skill 可加载 | 在 DSH 中调用 `paper-audit` | 返回 SKILL.md 正文，无报错 |
| D13 | 首轮基线 | 6 profile 全跑 | 0 个 P0/P1 FAIL；报告归档 + 索引 |
| D14 | 仓库整洁 | `git status` | 除工具/文档/报告外无稿件改动；冻结件哈希不变 |

```text
# D1-D14 一次性验证
python -m tools.paper_audit selftest
python -m tools.paper_audit list-profiles
foreach ($p in @('paperA_nc','paperA_springer','p3_prl','a1_nn','a23_joe','prl_commentary')) {
  python -m tools.paper_audit audit --profile $p --out docs/audits --fail-on NONE
}
python -m tools.paper_audit audit --profile paperA_nc --staged --out docs/audits --fail-on NONE
python -m tools.paper_audit selftest
```


---

## 4. 目录结构与文件清单

```text
tools/paper_audit/
  __init__.py          # 版本号
  __main__.py          # python -m 入口
  cli.py               # argparse：audit/list-profiles/list-checks/freeze/selftest/render-template
  model.py             # Severity/Status/Check/Finding/Report；判定与 grade；as_dict
  registry.py          # 86 条 Check 的单一来源（id/dimension/severity/title/method/automated）
  profiles.py          # 9 个 profile + BASE_LIMITS/BASE_PROFILE
  texutil.py           # LaTeX 文本工具：include 展开、摘要、关键词、cite/bib、label/ref、DOI、占位符、CJK、重复句
  checks.py            # build_context + 86 个 handler + freeze 工具 + run_audit
  report.py            # Markdown 渲染 + JSON 写出 + 终端摘要
  README.md            # 英文工具说明（快速开始/严重度/维度/profile/扩展/限制）
  templates/
    AUDIT_REPORT_TEMPLATE.md
    FIX_EVIDENCE_TEMPLATE.md
    SUBMISSION_READINESS_TEMPLATE.md
  freeze/
    p3_prl.json        # 10 files
    a1_nn.json         # 16 files
    a23_joe.json       # 37 files
    prl_commentary.json# 28 files
docs/PAPER_AUDIT_MODE.md        # 中文协议
docs/audits/                    # 归档报告（AUD-*.json/.md + README.md 索引）
~/.dsh/skills/paper-audit/SKILL.md   # DSH skill（仓库外）
```

**行数参考**（便于估工）：registry ≈ 240 行；profiles ≈ 250 行；texutil ≈ 260 行；
checks ≈ 1300 行；report ≈ 140 行；cli ≈ 210 行；model ≈ 130 行。

---

## 5. 检查注册表（86 条全表）

> 实现时以本表为唯一来源；id 连续、维度明确、严重度要有理由。表中"自动=否"的检查
> 在引擎里返回 MANUAL，并写清需要审核人看什么证据。

### A. Reproducibility and provenance（8 条）

| id | 严重度 | 自动 | 检查项 | 方法 |
|---|---|---|---|---|
| A-01 | P1 | 是 | Git working tree is clean for the manuscript paths | git status --porcelain limited to the manuscript directory is empty |
| A-02 | P3 | 是 | Audit records the git commit, branch and timestamp | git rev-parse HEAD / branch --show-current captured in the report |
| A-03 | P2 | 是 | A build command is documented for this profile | profile.commands contains a build entry or README documents the build |
| A-04 | P1 | 是 | The PDF is not older than the LaTeX sources | mtime(pdf) >= max(mtime(*.tex, *.bib, figures referenced by included sources)) |
| A-05 | P2 | 是 | Compilation log belongs to the current PDF | mtime(pdf) and mtime(log) differ by less than 120 s |
| A-06 | P3 | 是 | Environment recorded (pdflatex, python, OS, git) | versions captured in the report metadata |
| A-07 | P2 | 是 | Documented build cannot silently change tracked sources | the build entry writes only generated artifacts (manual review if custom) |
| A-08 | P2 | 是 | No untracked artifacts inside the manuscript directory | git status shows no untracked build products under the manuscript dir |

### B. Build and compilation integrity（10 条）

| id | 严重度 | 自动 | 检查项 | 方法 |
|---|---|---|---|---|
| B-01 | P0 | 是 | Compilation finished without errors | count of lines starting with '!' in the latest log == 0 |
| B-02 | P0 | 是 | No undefined references | count of 'Reference ... undefined' == 0 |
| B-03 | P0 | 是 | No undefined citations | count of 'Citation ... undefined' == 0 |
| B-04 | P1 | 是 | No overfull horizontal boxes | count of 'Overfull \hbox' == 0 |
| B-05 | P1 | 是 | No floats larger than the text block | count of 'Float too large' == 0 |
| B-06 | P2 | 是 | No unresolved LaTeX warnings | 'LaTeX Warning' lines reviewed; each must be explained |
| B-07 | P1 | 是 | No 'Rerun to get' request left in the log | the final pass converged |
| B-08 | P2 | 是 | Page count in the log equals the PDF page count | parse 'Output written on ... (N pages' and compare with pdfinfo |
| B-09 | P2 | 是 | No font warnings that indicate substitution | LaTeX Font Warning lines are empty or explained |
| B-10 | P1 | 是 | A clean-room rebuild reproduces the expected page count | copy sources to a temp dir, compile from scratch, compare pages (--staged) |

### C. Structure and completeness（10 条）

| id | 严重度 | 自动 | 检查项 | 方法 |
|---|---|---|---|---|
| C-01 | P1 | 是 | All profile-required sections are present | search the merged sources for each entry of profile.required_sections |
| C-02 | P0 | 是 | An abstract is present and unique | exactly one abstract environment/command as declared by the profile |
| C-03 | P1 | 是 | Keywords are present | keyword block found in the sources |
| C-04 | P0 | 是 | A bibliography is present | external .bib or inline thebibliography found |
| C-05 | P2 | 是 | Every figure and table is referenced in the text | all figure/table labels appear in at least one \ref |
| C-06 | P2 | 是 | No unresolved cross-reference in the PDF | PDF text contains no '??' or '(?)' |
| C-07 | P2 | 是 | No dead labels in the included sources | labels defined in included files but never referenced (ignoring external references) |
| C-08 | P0 | 是 | Declarations precede the bibliography | position of the first declaration < position of the bibliography |
| C-09 | P0 | 是 | All profile-required declarations are present | each entry of profile.required_declarations is found |
| C-10 | P1 | 是 | Title, authors and affiliations are present | \title / \author / affiliation block found |

### D. Journal / venue compliance（10 条）

| id | 严重度 | 自动 | 检查项 | 方法 |
|---|---|---|---|---|
| D-01 | P0 | 是 | Page count respects the venue limit / target | pdfinfo pages compared with profile.limits.pages_max / pages_target |
| D-02 | P0 | 是 | Abstract word count respects the venue limit | source-side count (math expressions count as one token) <= limits.abstract_words_max |
| D-03 | P1 | 是 | Keyword count within the venue range | number of keywords between limits.keywords_min and limits.keywords_max |
| D-04 | P1 | 是 | Highlights within the venue rules | count and per-item character count within profile.limits.highlights_* |
| D-05 | P1 | 是 | Blinding rule respected | if limits.blinded: author names / affiliations / acknowledgements must be absent |
| D-06 | P1 | 是 | Title within the venue character limit | len(title) <= limits.title_chars_max (when set) |
| D-07 | P2 | 是 | Supplementary material page count as declared | pdfinfo of the supplementary PDF compared with the profile / README |
| D-08 | P2 | 是 | Portal file names and item types are respected | package files use the portal-facing names (Manuscript / Cover Letter / Highlights ...) |
| D-09 | P1 | 是 | Cover-letter claims agree with the built manuscript | page count, abstract words and headline counts extracted from the cover letter are re-measured |
| D-10 | P2 | 是 | Declarations use the wording required by the venue | manual review of funding / competing-interest / AI-disclosure phrasing |

### E. References and citations（10 条）

| id | 严重度 | 自动 | 检查项 | 方法 |
|---|---|---|---|---|
| E-01 | P0 | 是 | Every cited key exists in the reference database | cite keys - bib keys == empty |
| E-02 | P2 | 是 | No unused bibliography entries | bib keys - cite keys == empty (or each unused entry explained) |
| E-03 | P1 | 是 | Inline bibliography matches the cited keys | count of \bibitem equals distinct cite keys and all aux citation numbers resolve |
| E-04 | P2 | 是 | Citation numbering is contiguous in the PDF | max numeric citation marker equals the number of references |
| E-05 | P2 | 是 | DOIs are syntactically valid | every '10.<prefix>/<suffix>' DOI matches a conservative regex |
| E-06 | P2 | 是 | Software / data citations include a URL or DOI | manual review of dataset and software references |
| E-07 | P1 | 是 | No duplicate bibliography entries | same DOI or normalised title appearing twice |
| E-08 | P3 | 是 | Self-citations recorded (blinding / disclosure) | list of candidate self-citations for manual review |
| E-09 | P2 | 是 | Reference ordering matches the style | numeric styles sorted; author-year styles alphabetical (manual if style unclear) |
| E-10 | P2 | 是 | Every reference item has authors, title, venue and year | manual spot check or parser for the active bibliography style |

### F. Content consistency and number traceability（10 条）

| id | 严重度 | 自动 | 检查项 | 方法 |
|---|---|---|---|---|
| F-01 | P0 | 是 | No placeholders or unresolved markers | TODO / TBD / FIXME / XXX / [?] / ?? / lorem ipsum / 待补 found in sources or PDF |
| F-02 | P1 | 是 | No CJK characters in the manuscript sources | regex scan of included .tex files (comments included) |
| F-03 | P1 | 是 | No corrupted LaTeX tokens in the PDF | known broken tokens such as 'abla', 'nablaM', '<abla' absent from the PDF text |
| F-04 | P0 | 是 | Configured numerical claim ledgers pass | profile.commands: claim-ledger scripts exit 0 and print the expected pass count |
| F-05 | P0 | 是 | Configured consistency gates pass | profile.commands: consistency gates exit 0 |
| F-06 | P1 | 是 | Key numbers appear in the expected contexts | each value from profile.key_numbers is present in the listed files |
| F-07 | P1 | 是 | No stale counts or retired wording | profile.forbidden_strings absent from sources, cover letter and PDF |
| F-08 | P2 | 是 | No duplicated sentences | normalised sentences longer than 15 words appearing more than once |
| F-09 | P1 | 是 | Cover-letter page / word / experiment claims are true | re-measured against the built PDF and the claim ledger |
| F-10 | P1 | 是 | No question-mark artefacts in the PDF | isolated '?' markers that indicate missing references or data |

### G. Typography and PDF rendering（8 条）

| id | 严重度 | 自动 | 检查项 | 方法 |
|---|---|---|---|---|
| G-01 | P2 | 是 | No double-numbered section headings | regex for headings such as '1. 1. Introduction' in the PDF text |
| G-02 | P1 | 是 | No HTML / XML markup in the PDF | <scp>, <i>, <b>, &amp;, &lt;, &gt; absent |
| G-03 | P1 | 是 | No literal LaTeX commands in the PDF | strings such as \cite, \ref, \nabla, \textbf absent from the text layer |
| G-04 | P2 | 是 | All fonts are embedded | pdffonts shows no 'no' in the embedded column |
| G-05 | P2 | 是 | PDF metadata title / author match the manuscript | pdfinfo Title / Author compared with the source \title / \author |
| G-06 | P2 | 是 | No blank pages except intentional ones | pages with fewer than 20 extracted characters, excluding declared exceptions |
| G-07 | P2 | 是 | List numbering is monotone | manual review of long checklists and enumerated contributions |
| G-08 | P3 | 是 | Line and page numbers behave as the venue expects | page numbers present; line numbers continuous if required by the profile |

### H. Data, ethics and declarations（7 条）

| id | 严重度 | 自动 | 检查项 | 方法 |
|---|---|---|---|---|
| H-01 | P0 | 是 | Data availability statement present | required by profile; must state where the data/results live |
| H-02 | P2 | 是 | Data statement links are well formed | every URL / DOI in the data statement syntactically valid |
| H-03 | P1 | 是 | Generative-AI disclosure present if the profile requires it | declaration found and mentions the tools used |
| H-04 | P1 | 是 | Competing-interest declaration present | declaration found |
| H-05 | P1 | 是 | Funding declaration present | declaration found |
| H-06 | P2 | 是 | CRediT / author-contribution statement present if required | declaration found |
| H-07 | P3 | 是 | Ethics / consent statement present if applicable | manual: no human-subject data in this project; record N/A |

### I. Submission package and freeze safety（8 条）

| id | 严重度 | 自动 | 检查项 | 方法 |
|---|---|---|---|---|
| I-01 | P0 | 是 | Submission package contains the expected files | profile.package contains all expected portal items |
| I-02 | P1 | 是 | Package copies match the live manuscript files | sha256(package file) == sha256(live source) for each mapped pair |
| I-03 | P1 | 是 | Package LaTeX source compiles standalone | independent temp-dir compile of the package source (--staged) |
| I-04 | P0 | 是 | Frozen submission artefacts are unchanged | sha256 tree equals tools/paper_audit/freeze/<profile>.json |
| I-05 | P2 | 是 | Package file sizes within portal limits | every file <= profile.limits.portal_size_mb |
| I-06 | P2 | 是 | Package README states the measured facts | page count / word count / ledger numbers recomputed and compared |
| I-07 | P2 | 是 | Source archive is valid and complete | zipfile.testzip() is None and entry count matches the source tree |
| I-08 | P2 | 是 | No manuscript / PDF leaks into the public repository mirror | publish_clean contains no paper* / main*.tex / main*.pdf (profile.public_mirror) |

### J. Evidence and hand-off documentation（5 条）

| id | 严重度 | 自动 | 检查项 | 方法 |
|---|---|---|---|---|
| J-01 | P1 | 是 | Claim-ledger evidence file exists and is current | outputs/analysis claim-ledger JSON newer than the manuscript sources |
| J-02 | P2 | 是 | An audit report is archived with a stable identifier | this report is written to docs/audits/ and the JSON carries the git commit |
| J-03 | P2 | 是 | HANDOFF.md and 文件地图.md record the current status | manual: the latest status block mentions the profile label and date |
| J-04 | P3 | 是 | A fix-evidence file exists for the latest fix round | FIXES_<date>.md present in the manuscript directory when fixes were made |
| J-05 | P2 | 是 | The audit itself is reproducible | the report lists every command executed and the environment versions |

**合计 86 条。**

---

## 6. 严重度、判定与退出码

| 严重度 | 含义 | 是否阻断 |
|---|---|---|
| P0 | 事实/合规硬伤，或冻结件被改 | 是 |
| P1 | 读者/编辑可见的缺陷，或主张与证据不一致 | 是 |
| P2 | 质量/一致性问题，能修则修 | 否（记录） |
| P3 | 信息 | 否（记录） |

| 状态 | 含义 |
|---|---|
| PASS | 自动证据满足通过条件 |
| FAIL | 自动证据显示不满足 |
| WARN | 需要人看一眼的疑点（不阻断） |
| SKIP | 不适用/文件缺失/工具缺失（必须写原因，不能当 PASS） |
| MANUAL | 无法自动判定，必须具名审核人签收 |
| ERROR | 检查自身异常（视为工具缺陷） |

判定：`BLOCKED`（有 P0/P1 FAIL/ERROR，grade D）；`READY-WITH-MINOR`（仅 P2 FAIL，grade B）；
`READY`（无 FAIL，grade A）。退出码：`--fail-on P1`（默认）有 P0/P1 失败返回 1；
`--fail-on P0` 只看 P0；`--fail-on NONE` 仅审阅、不可作放行依据。

**MANUAL 处理**：报告 §3 逐条写"谁、何时、看了什么证据、结论"；未签收不算通过。

---

## 7. Profile 规范

### 7.1 字段

| 字段 | 类型 | 说明 |
|---|---|---|
| id/label | str | 唯一 id 与展示名 |
| manuscript | str | 稿件目录（仓库相对） |
| tex | list[str] | 主 tex 文件（**第一个是 primary**，内容分析只用 primary 及其 include） |
| pdfs/logs | list[str] | 相对稿件目录 |
| package | str/None | 包目录；先按仓库根解析，不存在再按稿件目录解析 |
| package_expected | list[str] | 门户期望文件名 |
| package_map | list[[pkg, live]] | 包内文件 → live 源文件（哈希比对；冻结包跳过） |
| package_frozen | bool | 提交包是冻结件时置 true（I-02/I-06 跳过，交给 I-04） |
| supplementary | str/None | 补充材料 PDF |
| cover_letter / highlights | str/None | 相对稿件目录 |
| abstract_style | "env" / "command" | elsarticle/IEEE 用 env；Springer 用 command |
| limits | dict | pages_max/pages_target/abstract_words_max(+min)/keywords_min,max/highlights_min,max/highlight_chars_max/title_chars_max/blinded/portal_size_mb |
| required_sections | list[str] | C-01 用（子串匹配 section 标题） |
| required_declarations | list[str] | C-08/C-09/H-01/H-03..H-06 用 |
| forbidden_strings | list[str] | F-07；退役计数/措辞（大小写不敏感） |
| key_numbers | dict[value → files/dirs] | F-06；关键数字必须仍出现在指定路径 |
| commands | list[{name,cmd,expect,kind}] | F-04（ledger）/F-05（gate）；校验 rc==0 且 expect 出现在输出 |
| freeze_paths | list[str] | I-04；冻结件文件/目录 |
| freeze_manifest | str | 默认 tools/paper_audit/freeze/<id>.json |
| build_command / staged_command / staged_expect | list/str | A-03 文档化；B-10/I-03 独立编译 |
| public_mirror | str | I-08；公共镜像目录（默认 publish_clean） |
| notes | str | 供人读 |

### 7.2 9 个 profile

| profile | label | manuscript | tex | pdf | package | frozen paths | commands |
|---|---|---|---|---|---|---|---|
| a1_nn | A1 - Neural Networks (elsarticle review) | paper_a1 | main.tex | main.pdf<br>cover_letter.pdf<br>declaration.pdf<br>highlights.pdf<br>abstract.pdf | SUBMISSION/A1_NeuralNetworks | SUBMISSION/A1_NeuralNetworks | - |
| a23_joe | A23 - IEEE Journal of Oceanic Engineering (IEEEtran) | paper_a2 | main_ieee.tex | main_ieee.pdf<br>cover_letter.pdf<br>abstract.pdf | - | SUBMISSION/A23_JOE | A23 fix verification |
| generic_elsevier | Generic Elsevier manuscript (elsarticle) | . | - | - | - | - | - |
| generic_ieee | Generic IEEE manuscript (IEEEtran) | . | - | - | - | - | - |
| generic_prl | Generic Pattern Recognition Letters manuscript (cas-dc) | . | - | - | - | - | - |
| p3_prl | Paper 3 - Pattern Recognition Letters (IEEEtran) | paper3/paper_ieee | main.tex<br>main_10pp.tex<br>main_full.tex | main.pdf<br>main_10pp.pdf<br>main_full.pdf<br>supplementary/supplementary.pdf | - | SUBMISSION/P3_PRL_revision/CORRECTED_2026-10-15<br>SUBMISSION/P3_PRL_revision/UPLOAD_2026-10-15 | P3 audit_check, P3 audit_pdf |
| paperA_nc | Paper A - Neurocomputing (elsarticle) | paper合 | main_nc.tex | main_nc.pdf | NC_submission | - | Paper A claim ledger, Main claim ledger, Paper A consistency gate |
| paperA_springer | Paper A - Springer variant (sn-jnl) | paper合 | main_springer.tex | main_springer.pdf | - | - | Paper A claim ledger, Main claim ledger, Paper A consistency gate |
| prl_commentary | PRL Commentary - Pattern Recognition Letters (cas-dc) | paper_review_prl | main_prl.tex | main_prl.pdf<br>cover_letter.pdf<br>highlights.pdf | - | paper_review_prl/UPLOAD<br>SUBMISSION/Review_PRL | PRL final check |

### 7.3 limits

| profile | pages_max | abstract_words | keywords | highlights | blinded | portal_size_mb |
|---|---|---|---|---|---|---|
| a1_nn | - | --250 | 1-6 | 3-5, max 85 chars | no | 50 |
| a23_joe | - | 150-250 | 3-5 | - | no | 50 |
| generic_elsevier | - | --250 | 1-8 | - | no | 50 |
| generic_ieee | - | --250 | 1-8 | - | no | 50 |
| generic_prl | - | --250 | 1-8 | - | no | 50 |
| p3_prl | 10 | --250 | 1-6 | - | no | 50 |
| paperA_nc | - | --250 | 1-6 | 3-5, max 85 chars | no | 50 |
| paperA_springer | - | --250 | 1-6 | 3-5, max 85 chars | no | 50 |
| prl_commentary | 7 | --250 | 5-7 | - | no | 50 |

### 7.4 关键约定

- **primary tex**：内容分析（摘要/关键词/cite/label/重复句/占位符）只用第一个 tex 及其
  `\input` 闭包，避免 P3 三个版本互相重复导致误报；
- **package_frozen**：在审稿件的包是"已投出"版本，与 live 工作副本不同是正常的，
  必须置 true；冻结校验交给 I-04；
- **forbidden_strings 要精确**：不要写"five seeds"这种合法措辞（本项目正文合法使用
  five-seed/five seeds）；写"five random seeds"或退役的旧句；
- **key_numbers 要可定位**：列出文件或目录，值为字符串子串匹配；
- **staged_command**：应是无副作用（不写 live 目录）的独立编译命令，输出里要有
  `staged_expect`（如 "staged build OK"）。

---

## 8. CLI 契约

| 命令 | 参数 | 行为 | 退出码 |
|---|---|---|---|
| list-profiles | — | 表格：profile/label/manuscript | 0 |
| list-checks | --dimension A-J；--json | 列注册表 | 0 |
| freeze | --profile；--write | 写/校验基线；打印文件数或差异 | 0/1 |
| audit | --profile；--staged；--out；--fail-on；--command-timeout | 跑 86 条，写 MD+JSON，终端摘要 | 0/1 |
| selftest | — | 注册表/模板/profile/freeze 校验 | 0/1 |
| render-template | --kind audit/fix/readiness | 打印模板 | 0/1 |

stdout 摘要格式：

```text
<label>    READY  grade A  pass=66 fail=0 warn=2 manual=10 skip=8 error=0
markdown: <path>
json:     <path>
reproduce: python -m tools.paper_audit audit --profile <id>
```


---

## 9. 报告 JSON schema

| 字段 | 类型 | 说明 |
|---|---|---|
| audit_id | str | AUD-<profile>-<UTC> |
| profile / profile_label | str | |
| manuscript | str | |
| generated_at | str | 本地时区 ISO |
| git_commit / git_branch / git_dirty | str/str/bool | 审核时状态 |
| verdict / grade | str | READY / READY-WITH-MINOR / BLOCKED；A/B/D |
| counts | dict | {"PASS":n,"FAIL":n,"WARN":n,"SKIP":n,"MANUAL":n,"ERROR":n} |
| environment | dict | python/platform/pdflatex/pdfinfo/git |
| commands | list[str] | 实际执行的 profile 门禁命令 |
| artifacts | dict[path→sha256] | 各 PDF 哈希 |
| findings | list | 见下 |
| checks | list | 注册表快照（id/dimension/severity/title/method/automated） |

finding 字段：check_id、dimension、severity（P0-P3）、title、status（PASS/FAIL/WARN/SKIP/MANUAL/ERROR）、
message、evidence（≤600 字，可多行）、remediation。

Markdown 报告固定七节：1 Verdict / 2 Coverage by dimension / 3 Findings（按维度+状态）/
4 Commands executed / 5 Environment / 6 Artefacts / 7 Check registry。

---

## 10. 冻结与基线流程

1. 确认冻结件内容 = 已投出/已上传版本；
2. `freeze --profile <id> --write` 写 `freeze/<id>.json`：
   `{"profile","created_at","paths":[...],"entries":{rel_path: sha256, ...}}`；
3. 每次 audit 的 I-04 重算 tree_hashes，比较 added/removed/changed；任何非空 = P0 FAIL；
4. **替换版本**：先由操作者决定 → 更新冻结件 → 重新 freeze → 在 HANDOFF 记一行
   （日期、替换原因、新基线文件数）；
5. 现有基线文件数：p3_prl 10、a1_nn 16、a23_joe 37、prl_commentary 28（共 91）。

---

## 11. 三套模板

| 模板 | 必填内容 |
|---|---|
| AUDIT_REPORT_TEMPLATE.md | 报告头（audit id/profile/manuscript/时间/commit/审核人/判定）、执行摘要、P0/P1 blocker 表、警告与 MANUAL 表、十维覆盖表、证据附录（JSON 路径/命令/环境/哈希/freeze）、签收表 |
| FIX_EVIDENCE_TEMPLATE.md | 范围与冻结约束、变更表（#/check id/severity/file:line/before/after/why）、验证表（命令/期望/实测/通过）、残余项与判断 |
| SUBMISSION_READINESS_TEMPLATE.md | 文件/合规/文献/数字/渲染/包/冻结/记录 八行检查表 + 最终门禁 + 签收表 |

---

## 12. 协议文档大纲（docs/PAPER_AUDIT_MODE.md）

必须包含以下章节（中文，面向操作者）：

1. 适用场景（投稿前/修回/冻结检查/独立复核/交接）
2. 核心原则（证据优先、冻结优先、数字可溯源、不自我认证、严重度固定、修复与审核分离、文档收尾）
3. 判定与门禁（BLOCKED/READY-WITH-MINOR/READY；MANUAL 处理）
4. 审核维度 A-J（核心问题 + 主要证据）
5. **86 条检查全表**
6. 标准流程 9 阶段：
   0 冻结与基线 → 1 加载模式/profile → 2 采集与静态检查 → 3 构建验证（--staged）
   → 4 数字与内容溯源 → 5 冻结与包校验 → 6 报告定稿 → 7 修复轮 → 8 签收与放行 → 9 归档与文档同步
7. 角色与职责分离（审核员/修复者/负责人/模式维护者，各自"不得做"）
8. 命令速查
9. 新增稿件/检查/模板的方法
10. 口径变更记录（append-only 表）
11. 当前基线（各 profile 报告 id/判定/counts）
12. 禁止事项（改口径过审、冻结件上顺手修、SKIP 当 PASS、无证据"已核对"、NONE 当放行、audit 轮改稿）

---

## 13. skill 安装要求

- 路径：`~/.dsh/skills/paper-audit/SKILL.md`
- YAML frontmatter：`name: paper-audit`；description 含"86-check registry / ten dimensions /
  BLOCKED/READY-WITH-MINOR/READY / JSON+Markdown report"与中文触发词
  （论文审核、复审、投稿前终检、在审稿冻结检查、逐条核对）；compatibility 说明 Python+TeX Live、离线、仓库根运行；metadata.short-description。
- 正文：When to use / First steps / Profiles 表 / Severity 与 verdict / Freeze discipline /
  Fix round / Commands / Built-in claim ledgers / Report quality bar。
- 安装后在 DSH 会话中应能通过 skill 名称加载（本仓库已实测）。


---

## 14. 验收与自检

```bash
python -m tools.paper_audit selftest
# 期望：registry checks: 86 / profiles: 9 / templates: OK / frozen files verified: 91 / SELFTEST PASSED

foreach ($p in @('paperA_nc','paperA_springer','p3_prl','a1_nn','a23_joe','prl_commentary')) {
  python -m tools.paper_audit audit --profile $p --out docs/audits --fail-on NONE
}
# 期望：6 份报告，0 个 P0/P1 FAIL，verdict 全部 READY；退出码 0（--fail-on NONE）

python -m tools.paper_audit audit --profile paperA_nc --staged --out docs/audits --fail-on NONE
# 期望：I-03 PASS（staged compile 通过）

python -m tools.paper_audit render-template --kind readiness | Select-Object -First 4
# 期望：非空 Markdown

git status --porcelain   # 期望：只有工具/文档/报告；稿件与冻结件无改动
```

首轮基线（本仓库 2026-10-18 实测，作为参考值）：

| profile | 判定 | pass/fail/warn/manual/skip |
|---|---|---|
| paperA_nc（含 --staged） | READY (A) | 66/0/2/10/8 |
| paperA_springer | READY (A) | 53/0/3/9/21 |
| p3_prl | READY (A) | 47/0/3/9/27 |
| a1_nn | READY (A) | 59/0/2/9/16 |
| a23_joe | READY (A) | 55/0/3/9/19 |
| prl_commentary | READY (A) | 53/0/3/9/21 |
| selftest | PASS | 86 checks / 9 profiles / 91 frozen files |

---

## 15. 实现注意事项（踩过的坑）

1. **Windows + PowerShell 7 + UTF-8**：内联 `python -c` 一律用单引号包裹，避免反引号/`$` 被
   PowerShell 解释；写文件用 Python `encoding="utf-8"`（不要用 Add-Content 追加中文）。
2. **不要引第三方依赖**：只用标准库 + TeX Live 命令行；否则在别的机器上无法复现。
3. **生成 Python 源码时的反斜杠**：用模板批量生成 .py 时极易多转义（把 `\d` 写成 `\\d`）；
   写完后必须 `python -m py_compile` 并跑真实 profile 验证（本实现曾因此把 DOI/引用正则写坏）。
4. **P3 多版本**：main.tex/main_10pp.tex/main_full.tex 同时存在时，内容分析只用 primary，
   否则摘要/重复句/引用计数会按版本数倍增。
5. **包路径解析**：`package` 可能相对仓库根（SUBMISSION/...）也可能相对稿件目录（NC_submission）；
   先试仓库根，不存在再试稿件目录。
6. **冻结包 vs live**：在审稿件的包与工作副本哈希不同是正常的；用 `package_frozen: true` 跳过
   I-02/I-06，否则每次都误报。
7. **中文注释**：visible 文本（展开 include 后已去注释）出现 CJK = FAIL；仅注释里出现 = WARN
   （不渲染，不影响投稿，但项目规则要求干净）。
8. **DOI 正则**：排除反斜杠、`]`、`)`、`}`、空白、逗号、分号，并 rstrip 句号；
   PDF 文本层里 DOI 可能被断行或下划线丢失（A23 已修）。
9. **引用/文献计数**：过滤 `\providecommand{\citep}[1]{\cite{#1}}` 之类的 `#1` 假 key。
10. **启发式无法可靠判定的检查**（如数字引用连续性 E-04）宁可 MANUAL，不要 FAIL 误伤。
11. **SELFTEST 必须真校验**：不能只打印"OK"；要检查注册表唯一性、模板存在、freeze 基线
    与当前冻结件一致。
12. **报告要能当证据**：JSON 里必须有 commit/命令/环境/哈希；Markdown 里每条 finding 必须有
    evidence/remediation；不要写"已核对"。
13. **文档收尾**：每次审核/修复阶段结束，更新 HANDOFF.md、文件地图.md、docs/audits/，
    并把报告 JSON 与改动一起 commit。

---

## 16. 当前实现参考（本仓库，2026-10-18）

- 工具包：`tools/paper_audit/`（86 checks、9 profiles、freeze 4 份基线、3 模板）
- 协议：`docs/PAPER_AUDIT_MODE.md`
- 归档：`docs/audits/`（6 份 AUD-*.json/md + README 索引）
- skill：`~/.dsh/skills/paper-audit/SKILL.md`
- 提交：`99e753b` "Add the Paper Audit Mode: 86-check standardised manuscript audit toolkit"
- 首轮基线：见 §14；报告 JSON 里记录的 git commit 为运行时的仓库状态
  （d3f6015），工具与报告同 commit 提交。

**复刻建议**：若只是"再造一个同样的模式"，直接按 §1 提示词 + §5 注册表 + §7 profile
矩阵 + §9 报告 schema 实现；§16 的现有实现可用于逐行对照，但不要照抄其中
与 Windows/本仓库路径绑定的部分（§15 已列）。

---

## 17. 扩展方法

- **新稿件/新期刊**：复制相近 profile，改 manuscript/tex/pdfs/logs/limits/commands/freeze_paths/
  package*；先 `--fail-on NONE` 校准（SKIP 过多 = 路径没配好），再定稿。
- **新检查**：registry 加 Check（id 连续、维度/严重度合理）；checks.py 加 handler 或标 MANUAL；
  `list-checks` 确认注册；跑一个真实 profile 验证不误报。
- **新模板**：放 templates/ 并在 cli.py 的 render-template 注册。
- **口径变更**：只允许在"模式维护"场景改 registry/profiles，且必须记录在协议 §9/§10 的
  变更表里；审核轮不得改口径。

---

## 附录 A：命令速查

| 目的 | 命令 |
|---|---|
| 列 profile | `python -m tools.paper_audit list-profiles` |
| 列检查 | `python -m tools.paper_audit list-checks [--dimension A] [--json]` |
| 完整审核 | `python -m tools.paper_audit audit --profile <id>` |
| 独立编译 | `python -m tools.paper_audit audit --profile <id> --staged` |
| 只看 P0 退码 | `python -m tools.paper_audit audit --profile <id> --fail-on P0` |
| 冻结基线 | `python -m tools.paper_audit freeze --profile <id> --write` |
| 校验冻结 | `python -m tools.paper_audit freeze --profile <id>` |
| 自检 | `python -m tools.paper_audit selftest` |
| 模板 | `python -m tools.paper_audit render-template --kind audit|fix|readiness` |

## 附录 B：首轮全量报告清单（2026-10-18）

| profile | report id | verdict |
|---|---|---|
| paperA_nc | AUD-paperA_nc-20261018T042229Z | READY (A) |
| paperA_springer | AUD-paperA_springer-20261018T042233Z | READY (A) |
| p3_prl | AUD-p3_prl-20261018T042235Z | READY (A) |
| a1_nn | AUD-a1_nn-20261018T042239Z | READY (A) |
| a23_joe | AUD-a23_joe-20261018T042246Z | READY (A) |
| prl_commentary | AUD-prl_commentary-20261018T042248Z | READY (A) |

## 附录 C：本交接文档的维护

- 更新时机：registry/profile/CLI/schema 任一变化时；
- 维护要求：append-only，历史口径不删，过期结论标注"已过期（日期）"；
- 与 `docs/PAPER_AUDIT_MODE.md` 的关系：本文件=交接给创造模式的"规格书+提示词"；
  协议文档=日常操作手册；两者冲突时以 registry/profiles 的**代码实现**为准，并同步修正两份文档。
