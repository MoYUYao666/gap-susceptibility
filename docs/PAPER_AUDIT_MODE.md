# 论文审核模式（Paper Audit Mode）

> 版本 1.0 ｜ 2026-10-18 建立 ｜ 工具：`tools/paper_audit/` ｜ 报告归档：`docs/audits/`
>
> **一句话**：把"审一篇稿子"变成一个**可复跑、可追溯、有判定标准**的流程——
> 一条命令跑完 A-J 十个维度，输出 JSON+Markdown 报告，按 P0/P1/P2/P3 严重度给出
> **BLOCKED / READY-WITH-MINOR / READY** 结论；修复必须另开"修复轮"并留下证据文件。

## 1. 适用场景

| 场景 | 用法 |
|---|---|
| 投稿前终检 | 对目标 profile 跑 full audit，P0/P1 全清才允许上传 |
| 修回/替换件 | 改完稿重跑；对比"上一份报告"确认没有回归 |
| 在审稿冻结检查 | `freeze` 基线 + I-04 冻结校验，确保 SUBMISSION/UPLOAD 一字未动 |
| 独立复核 | 第二名审核员（人或 agent）用同一 profile 复跑，对比 JSON 差异 |
| 交接 | 报告 JSON 记录 commit / 环境 / 命令，下一会话可逐条复现 |

## 2. 核心原则（不可协商）

1. **证据优先（evidence-first）**：每个 PASS/FAIL 必须能指到文件、命令输出或哈希；
   报告里不写"应该没问题"，只写"在哪测到、测到什么"。
2. **冻结优先（freeze-first）**：在审稿件的 `SUBMISSION/`、`UPLOAD/`、包内冻结件
   **只读**；任何对冻结件的改动都是 P0。需要替换版本时，先由操作者决定，重新 freeze 基线并记录。
3. **数字必须可溯源**：稿件数字只能来自 claim ledger / 归档 JSON；
   审核模式负责验证"门禁是否通过、关键数字是否还在、退役口径是否绝迹"，不负责编数。
4. **不自我认证**：写稿的人不给自己签"通过"；MANUAL 项必须有**具名审核人**的明确结论。
5. **严重度固定**：
   - **P0 = 阻断**（事实/合规硬伤，或冻结件被改）；
   - **P1 = 重大**（读者/编辑可见的缺陷，或主张与证据不一致）；
   - **P2 = 次要**（质量/一致性，能修则修，不阻断）；
   - **P3 = 记录**。
6. **修复与审核分离**：审计轮**不改稿**；修复轮只改审计报告点名的项，并写
   `FIXES_<date>.md`（模板见 `tools/paper_audit/templates/FIX_EVIDENCE_TEMPLATE.md`）。
7. **文档收尾**：审核完成必须同步 `HANDOFF.md`、`文件地图.md`、`docs/audits/`；
   报告 JSON 与稿件改动同一个 commit。

## 3. 判定与门禁

| 判定 | 条件 | 动作 |
|---|---|---|
| **BLOCKED**（grade D） | 任一 P0/P1 为 FAIL/ERROR | 停止上传/提交；开修复轮；修完复跑 |
| **READY-WITH-MINOR**（grade B） | 仅 P2 FAIL | 可提交；P2 进待办，记录在报告 §3 |
| **READY**（grade A） | 无 P0/P1/P2 FAIL（WARN/SKIP/MANUAL 允许） | 可提交；MANUAL 项须签收 |

命令退出码：`--fail-on P1`（默认）= 有 P0/P1 失败则退 1；`--fail-on P0` 只看 P0；
`--fail-on NONE` 仅供审阅，不可作为放行依据。

**MANUAL 项处理**：报告 §3 必须逐条写"谁在什么时候、看了什么证据、结论是什么"；
未签收的 MANUAL 项不算通过。

## 4. 审核维度（A-J）

| 维度 | 名称 | 核心问题 | 主要证据 |
|---|---|---|---|
| A | 可复现性与取证 | 树是否干净？PDF 是否比源文件新？环境是否记录？ | git status/commit、mtime、pdflatex 版本 |
| B | 构建完整性 | 编译有没有错误/未定义/Overfull/不收敛？ | .log 计数、pdfinfo 页数 |
| C | 结构与完整性 | 章节/摘要/关键词/文献/声明顺序是否齐？ | 源文件扫描 + PDF 文本 |
| D | 期刊合规 | 页数/摘要词数/关键词/highlights/盲审/门户命名是否合规？封面信数字对不对？ | pdfinfo、源码计数、包清单 |
| E | 参考文献 | 引用是否都有条目？有没有孤儿条目/重复/坏 DOI？ | bib/cite 集合、PDF 文本 |
| F | 内容一致与数字溯源 | 有无占位符/中文/坏 token？台账与门禁过不过？关键数字在不在？退役口径有没有复活？ | profile.commands、forbidden_strings、key_numbers |
| G | 排版与渲染 | 章节号双写/HTML 残留/字面 LaTeX/字体嵌入/元数据/空页？ | PDF 文本、pdffonts、pdfinfo |
| H | 数据、伦理与声明 | 数据可用性/AI 披露/利益冲突/资助/CRediT 是否齐且措辞合规？ | 声明文本、链接语法 |
| I | 投稿包与冻结安全 | 包文件齐不齐？哈希对不对？独立编译过不过？冻结件有没有变？ | 包目录、SHA-256、freeze manifest、zip 校验 |
| J | 证据与交接 | 台账证据是否新鲜？报告是否归档？HANDOFF/文件地图是否同步？修复证据在不在？ | 文件时间、报告 JSON、FIXES 文档 |

完整检查清单（含每条 check 的 id、严重度、方法）由注册表生成：

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

**合计 86 条检查。**

## 5. 标准流程（9 个阶段）

### 阶段 0：冻结与基线（一次性 / 每次替换版本后）

```
python -m tools.paper_audit freeze --profile <profile> --write
```

- 确认 `SUBMISSION/`、`UPLOAD/` 当前内容就是"已投出/已上传"的版本；
- 基线写入 `tools/paper_audit/freeze/<profile>.json`（逐文件 SHA-256），与审核报告一起提交；
- 在 `HANDOFF.md` 记一行"freeze 时间 + 覆盖哪些文件"。

### 阶段 1：加载模式与 profile

```
python -m tools.paper_audit list-profiles
python -m tools.paper_audit list-checks --dimension I
```

- 明确本次审的对象（稿件目录、目标刊、是否在审、哪些是冻结件）；
- 若稿件/期刊不在表里，先在 `profiles.py` 加 profile（见 §8）。

### 阶段 2：采集与静态检查

```
python -m tools.paper_audit audit --profile <profile> --fail-on NONE
```

- 先看报告 §1 判定与 §2 blocker，再看 §3 findings 全表；
- SKIP 必须能解释（文件不存在/该刊不要求/工具缺失）；不能把 SKIP 当 PASS。

### 阶段 3：构建验证（可选但推荐）

```
python -m tools.paper_audit audit --profile <profile> --staged
```

- `--staged` 调 profile 的 `staged_command`（如 Paper A 的包独立编译脚本）验证
  "从源码独立重建可得到相同页数"；没有配置则该检查 SKIP；
- 正式投稿前必须至少做过一次 clean-room 构建（B-10/I-03 通过或被具名豁免）。

### 阶段 4：数字与内容溯源

- F-04/F-05 会跑 profile 配置的 claim ledger 与一致性门禁；失败即 P0；
- 人工核对 `key_numbers` / `forbidden_strings` 的采样上下文（报告只证明"在/不在"，
  语义是否用对由审核人判断——记 MANUAL）；
- 对封面信、highlights、摘要中的数字，逐一对应到正文/台账（D-09/F-09 自动查页数与词数）。

### 阶段 5：冻结与包校验

- I-04 必须 PASS；任何 changed/removed 都是 P0；
- I-01/I-02/I-05/I-06/I-07 覆盖包完整性、哈希、大小、README、zip；
- 在审稿若包是冻结件，`package_frozen: true`（不比对 live 哈希，交给 I-04）。

### 阶段 6：报告定稿

- 报告默认写 `docs/audits/AUD-<profile>-<UTC>.md/.json`；
- 报告 §6/§7 保留命令、环境、artefact 哈希与完整注册表；
- 把 §2/§3 的每条结论写成"可执行动作"（负责人 + 截止时间），不要写"需注意"。

### 阶段 7：修复轮（若 BLOCKED / 有 P1）

1. 为每个 FAIL 建一条修复项（check id + 文件:行 + before/after + 验证命令）；
2. 只改**本地工作副本**；冻结件不动；
3. 修复后重跑同一 profile，把新报告 JSON 与 `FIXES_<date>.md` 一起提交；
4. 审核员**复跑**并对 diff 做抽查（不采信修复者的口头结论）。

### 阶段 8：签收与放行

- 确认没有 P0/P1 FAIL；MANUAL 项逐条签收；P2 入待办；
- 报告 JSON 的 `verdict` 字段作为放行依据；
- 在 `HANDOFF.md` 记"审核轮次 / 报告路径 / 判定 / 残余项"。

### 阶段 9：归档与文档同步

- 报告、FIXES、freeze 基线、稿件源一起 commit（PDF 按仓库惯例 gitignore）；
- 更新 `文件地图.md` 的稿件状态块（当前页数/审计结论）；
- 若目标刊/状态变化，同步 `哪篇是哪篇.md`。

## 6. 角色与职责分离

| 角色 | 职责 | 不得做 |
|---|---|---|
| 审核员（independent auditor） | 跑模式、写报告、判定、签收 MANUAL | 修改稿件、给自己写的稿签"通过" |
| 修复者（fixer） | 按报告逐项修复、写 FIXES 证据、重编译 | 自行改判定、跳过验证 |
| 负责人 / 通讯作者 | 决定投稿时点、冻结件是否替换、P2 取舍 | 让未签收的 MANUAL 项放行 |
| 模式维护者 | 维护 registry/profiles/模板/文档 | 在审核轮里改检查口径以"过审" |

同一会话里可以一人分饰多角，但**报告必须写明**"谁审的、谁修的、谁签的"；
关键投稿（P0/P1）建议至少一次**跨会话复跑**。

## 7. 命令速查

| 目的 | 命令 |
|---|---|
| 列 profile | `python -m tools.paper_audit list-profiles` |
| 列检查项 | `python -m tools.paper_audit list-checks [--dimension A] [--json]` |
| 完整审核 | `python -m tools.paper_audit audit --profile <profile>` |
| 独立编译 | `... audit --profile <profile> --staged` |
| 只看 P0 退码 | `... audit --profile <profile> --fail-on P0` |
| 记录冻结基线 | `python -m tools.paper_audit freeze --profile <profile> --write` |
| 校验冻结 | `python -m tools.paper_audit freeze --profile <profile>` |
| 取模板 | `python -m tools.paper_audit render-template --kind audit|fix|readiness` |
| 自检工具链 | `python -m tools.paper_audit selftest` |

## 8. 新增稿件 / 检查 / 模板

- **新稿件或新期刊**：复制 `profiles.py` 中相近 profile，填 `manuscript/tex/pdfs/logs/limits/commands/freeze_paths/package*`；
  先跑 `--fail-on NONE` 校准（SKIP 过多说明路径没配好），再定稿。
- **新检查**：在 `registry.py` 加 `Check`（id 连续、维度明确、严重度要有理由）；
  在 `checks.py` 加 handler 或标记 MANUAL；跑 `list-checks` 确认注册成功。
- **新模板**：放 `tools/paper_audit/templates/` 并在 `cli.py` 的 `render-template` 注册。
- 改动后至少对一个真实 profile 跑通，并把改动的口径写进本文件 §9。

## 9. 口径变更记录（append-only）

| 日期 | 变更 | 理由 |
|---|---|---|
| 2026-10-18 | v1.0：建立 A-J 十维、86 条检查、6 个 profile、freeze 基线、三套模板 | 五稿复核后固化流程 |
| 2026-10-18 | v1.0.1：B-10 的 `message` 规范化为字符串；Paper A 独立编译的页数统计改用 `pdfinfo`（去掉 `pypdf`） | 报告 schema 一致 + 满足"只用标准库 + TeX Live"约束；**不改变检查口径、严重度与判定** |
| 2026-10-18 | v1.0.2（加固，不改严重度）：`freeze` 校验有漂移时退 1；I-08 前缀匹配 `main_nc/main_prl/main_ieee/main_10pp/...`；J-02/J-05/B-08/C-02/D-01/I-06 不再在缺少证据时给 PASS；任何 ERROR 一律 BLOCKED；`audit_id` 进入 `Report` schema；registry 的 9 条纯 MANUAL 检查标 `automated=False`；generic profile 说明改为"复制后填写" | 独立复核发现的假 PASS/自证风险；**严重度、判定与预期字符串均未改动** |

## 10. 当前基线（2026-10-18 加固轮 Round 3）

> **Round 3 · 加固后复跑（2026-10-18T04:42Z）**：完成 §9 v1.0.2 的工具链加固后，从当前工作树
> 重跑全部 profile。**5 稿 READY (A)、0 FAIL**；**A1 为 BLOCKED (D)**：其摘要被 12:38 的外部
> 改稿扩到 **264 词**（上限 250），D-02 为 P0。`selftest` 通过（86 条检查、9 个 profile、
> 3 套模板、**91** 个冻结文件哈希）；`paperA_nc --staged` 的 **I-03 PASS**（0 错误 / 0 未定义 /
> 0 Overfull，70 页 = 期望页数）。报告 JSON/MD 与索引见 `docs/audits/`。
>
> **A1 是外部改动引入的真实回归**：04:35Z 复核轮时 A1 为 READY (A)（42 页、摘要 231 词，
> `AUD-a1_nn-20261018T043515Z`）；12:38 另一工作流在 `paper_a1/main.tex` 新增匹配 gap 段落后，
> 摘要变为 **264 词**。审核轮**没有改稿**；修复必须另开修复轮（删减摘要 ≥15 词、重建 PDF、
> 复跑 `a1_nn`，并留下 `FIXES_<date>.md`）。

| profile | 报告 ID（Round 3） | 判定 | pass / fail / warn / manual / skip |
|---|---|---|---|
| `paperA_nc`（`--staged`） | AUD-paperA_nc-20261018T044244Z | READY (A) | 66 / 0 / 2 / 10 / 8 |
| `paperA_springer` | AUD-paperA_springer-20261018T044217Z | READY (A) | 53 / 0 / 3 / 9 / 21 |
| `p3_prl` | AUD-p3_prl-20261018T044219Z | READY (A) | 47 / 0 / 3 / 9 / 27 |
| `a1_nn` | AUD-a1_nn-20261018T044223Z | **BLOCKED (D)** | 58 / 1 / 2 / 9 / 16 |
| `a23_joe` | AUD-a23_joe-20261018T044231Z | READY (A) | 55 / 0 / 3 / 9 / 19 |
| `prl_commentary` | AUD-prl_commentary-20261018T044232Z | READY (A) | 53 / 0 / 3 / 9 / 21 |

> `paperA_nc` 的非 staged 对照报告为 AUD-paperA_nc-20261018T044213Z（B-10/I-03 为 SKIP，
> 与"未请求独立编译"一致）。

**历史轮次**：Round 2（04:35Z）6 稿全 READY (A)、0 P0/P1，报告 ID 为
`AUD-<profile>-20261018T0435xxZ`；Round 1（04:22Z）同样 6 稿全 READY (A)，ID 为
`AUD-<profile>-20261018T0422xxZ`。两轮报告均保留在 `docs/audits/`，用于对比回归。

> 基线只说明"自动检查未发现 P0/P1 问题"；**MANUAL 项仍需具名审核人签收，SKIP 不等于 PASS**。

## 11. 禁止事项

1. **不得**为了让门禁通过而修改 registry 的严重度/预期值；
2. **不得**在冻结件上"顺手"修复；替换版本必须走操作者决定 + 重新 freeze；
3. **不得**用 SKIP 冒充 PASS；SKIP 必须写明原因；
4. **不得**在报告里写没有证据的"已核对"；
5. **不得**把 `--fail-on NONE` 的结果当作放行依据；
6. **不得**在 audit 轮改稿（修复必须另开修复轮，并留 FIXES 证据）。

## 12. 标准模式下的审核流程（当前推荐）

> DSH 原生模式（preset / plugin / 页面）已于 2026-10-18 按操作者要求移除；
> 审核流程回到 **标准模式 + `paper-audit` skill + Python CLI**。skill 仍在
> `~/.dsh/skills/paper-audit/SKILL.md`，CLI 与报告没有任何变化。

### 12.1 触发方式

在**标准模式会话**里任选其一：

- 直接说触发词：**“用 paper-audit skill 对 paperA_nc 做投稿前终检”**；
- 或先显式加载 skill：`skill paper-audit`，再按 SKILL.md 执行；
- 或只跑命令（不经过模型）：见 12.2。

### 12.2 最小命令序列

```bash
# 1. 工具链自检（86 checks / 9 profiles / 91 frozen files）
python -m tools.paper_audit selftest

# 2. 审阅模式：只记录、不因 P0/P1 退码；用于先看全貌
python -m tools.paper_audit audit --profile paperA_nc --fail-on NONE

# 3. 放行门禁：默认 --fail-on P1，有 P0/P1 FAIL 退 1
python -m tools.paper_audit audit --profile paperA_nc

# 4. 独立编译（可选；I-03 / B-10）
python -m tools.paper_audit audit --profile paperA_nc --staged

# 5. 在审稿冻结校验
python -m tools.paper_audit freeze --profile p3_prl
```

### 12.3 读结果

- 报告：`docs/audits/AUD-<profile>-<UTC>.json` 与 `.md`；索引 `docs/audits/README.md`；
- 先看 §1 verdict 与 blocker，再看 §3 逐条 findings；
- **SKIP 不等于 PASS**；**MANUAL 必须具名审核人签收**；P2 WARN 进待办；
- 放行依据是 JSON 的 `verdict`，不是 `--fail-on NONE` 的退出码。

### 12.4 修复轮（若 BLOCKED）

审核轮不改稿；修复另开一轮：

1. 按报告列出每个 P0/P1 FAIL 的 check id；
2. 只改本地工作副本，冻结件不动；
3. 写 `FIXES_<date>.md`（模板 `tools/paper_audit/templates/FIX_EVIDENCE_TEMPLATE.md`）；
4. 复跑同一 profile，把新报告 JSON 与 FIXES 一起提交。

### 12.5 一次性提示词（可直接粘到标准模式）

```text
用 paper-audit skill 审 paperA_nc：
1) 先跑 python -m tools.paper_audit selftest；
2) 再跑 python -m tools.paper_audit audit --profile paperA_nc --fail-on NONE；
3) 再跑 python -m tools.paper_audit audit --profile paperA_nc --staged；
4) 读 docs/audits/ 下最新 JSON/MD，汇总 verdict、P0/P1 blocker、MANUAL 项；
5) 不要改稿；如 BLOCKED，只给出按 check id 的修复建议。
```
