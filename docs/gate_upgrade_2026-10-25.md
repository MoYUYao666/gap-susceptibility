# 门禁升级 Phase 1（2026-10-25）：把"残留问题"变成机器可查

**背景**：操作者指出"每次都会有残留问题"。根因不是门禁少，而是**反复出现的缺陷类别没有被机器检查**——它们只活在散文笔记里，下一轮又要人肉重找。
本轮把最近三轮真实发生的 8 类残留抽象成 6 个新检查（N-01…N-07，N-06 预留给未来的"prose-only 声称"），接入 `tools/paper_audit`，并留下 Phase 2 计划。
**原则**：数据驱动（`docs/` 下版本化注册表）、**不能判定就报 MANUAL 而不是 PASS**、无白名单式豁免、每个检查都有正/负 fixture。
**范围**：只改 `tools/paper_audit/**`、`.gitignore`、新增 `docs/*.json`、本文件；**未动稿件、未动 `SUBMISSION/**`、未 commit**。

## 1. 根因分类 → 新检查映射（本轮真实残留）

| # | 残留类别（本轮实例） | 机器化检查 | 检查会怎样抓到 |
|---|---|---|---|
| 1 | 同一量两个值：A23 "3.4×/3.8×"；A1 τ–R@1 "−0.17 vs −0.143"（两个网格未披露）；A1 摘要 −0.15 vs §5.5 −0.215 | **N-01 数量唯一性**（`docs/QUANTITY_REGISTRY.json`） | 归档字段按指定位数必须等于 canonical；注册了 `mentions` 的量，正文里每个出现值必须 round 到 canonical 或**显式登记的 variant（含理由）**；两个值且都没登记 → FAIL。A1 的两网格已作为"双 variant"登记（这就是修复后的形态） |
| 2 | 方向/符号误读：P3 配对差 −3570.10（能量越低越好）被写成 "opposite"；Paper A 把 DG 叫 predictor | **N-02 符号一致性**（`docs/SIGN_REGISTRY.json`） | 只在"同一字段、两臂对比、句子里有方向词且能解析出带符号数值"时判定；与 `lower_is` 语义矛盾 → FAIL；方向句但解析不出数值 → MANUAL（保守，不猜） |
| 3 | 交叉引用指向错目标：P3 "S37 的三栈设计"其实在 S39；A1 的 "Appendix Appendix A.n" + 三个 label 挂在无编号 `\section*` 下全部解析到 A.4 | **N-03 指针解析** | PDF 文字层出现 `refcor:`/`ref{`/`??`/`Appendix Appendix` → **FAIL**（这些绝不该出现在排版结果里）；指针目标与"由 LaTeX 计数器模拟 + PDF 标题索引"建成的索引对不上 → **MANUAL 并列清单**（不同模板编号不同，无法认证时绝不误 FAIL） |
| 4 | LaTeX 泄漏进 PDF：A1 提交版里 "Corollary **refcor:lipschitz**"（`\\ref` 双反斜杠） | **N-03** | 同上，`\bref...{`/`\bref...:` 模式在文字层出现即 FAIL |
| 5 | 数据/归档声明过度：A23 "compiled manuscripts are archived"（发布快照按政策不含稿件）；Commentary 声称某版本 DOI 下有六个值的归档（实际引自文献） | **N-04 归档声明审计**（`docs/RELEASE_LEDGER.json`） | 数据声明段里的每个 DOI/URL 必须已登记（含第三方数据集白名单条目）；出现 "contains/archived/includes" 且对象是 manuscripts/compiled PDFs/cover letters（政策排除）→ FAIL；对象是 scripts/records/analyses 则要求 `publish_clean/{tools,outputs}` 实际存在 |
| 6 | 参考文献元数据错误：IGU-LoRA 原记 "Xiao, Xi / 2025 / arXiv-only"，主源实为 Cui et al., ICLR 2026 | **N-05 引用缓存**（`docs/REF_VERIFICATION.json`） | 每个带 DOI/arXiv 的 bib 条目，其 title/第一作者/年份必须与**已验证缓存**一致；`source: unverified-bib` 的缓存条目**不算验证**，会让检查报 MANUAL 并列出待核清单；解析可靠性不足的 IEEE 式条目计入 MANUAL 而不是误 FAIL |
| 7 | 工具卫生：每次 audit 都在 `docs/audits/` 留一堆未跟踪 `AUD-*`，`_p1454` 永久报"leftover" | **N-07 产物卫生** + `.gitignore` | `docs/audits/*` 忽略、`!docs/audits/.gitkeep` 保留目录；`git status` 里不得再有未跟踪 `AUD-*`。**选择方案 (i)**（改 `.gitignore`），因为方案 (ii)（driver 自己 `git add`）会污染使用者的提交内容、且和"不改工作树"的审计语义冲突 |
| 8 | 发现只活在散文里 → "是否全部修完"机器不可答 | **Phase 2**（见 §6） | 机器可读 `docs/REVIEW_LEDGER.json` + 发布门禁拒绝带 open (a) 项放行 |

## 2. Phase 1 实现清单

**新模块** `tools/paper_audit/mechanical.py`（约 900 行，纯函数 + fixture 自检）：
`check_quantity_uniqueness` / `check_sign_consistency` / `check_pointer_resolution` / `check_archive_claims` / `check_reference_verification` / `check_artifact_hygiene`，以及 `selftest_mechanical()`。

**注册表**（`tools/paper_audit/registry.py` 新增 6 条，维度复用既有分类）：
`N-01`→F、`N-02`→F、`N-03`→C、`N-04`→H、`N-05`→E、`N-07`→A；每条都在 `method` 里写明数据文件与判定语义。

**数据文件**（由 `tools/paper_audit/build_registries.py --apply` 幂等生成/更新）：
| 文件 | 内容 | 当前规模 |
|---|---|---|
| `docs/QUANTITY_REGISTRY.json` | 由三本 claim ledger（96 + 88 + 216）自动播种（解析 source、校验归档字段真实存在且按位数可复现才收录），加本周修复的 curated 条目（A1 τ–R@1 两个网格） | 3 profiles / **179 条**（paperA_nc 84、paperA_springer 84、a1_paa 11） |
| `docs/SIGN_REGISTRY.json` | energy 配对差（lower_is=better）、gap 配对差（neutral）、accuracy 差（higher better）语义 + 每稿登记项 | 2 profiles（p3_prl、a23_joe） |
| `docs/RELEASE_LEDGER.json` | v2.5 / v1.0-prl-revision 的 tag→版本 DOI→快照内容与**政策排除项**；`third_party_sources`（FathomNet figshare DOI、database.fathomnet.org） | 2 releases / 3 DOI / 2 third-party |
| `docs/REF_VERIFICATION.json` | 每条带 DOI/arXiv 的 bib 条目缓存；`--verify-network` 可选的在线复核入口（离线门禁不需要网络） | 184 条（**7 条已验证**，177 条标 unverified-bib → MANUAL 待核） |

**N-05 的首个示范**：`igulora2025` 的 bib 已在上一轮修正为 **Cui, Xuan et al., ICLR 2026, arXiv:2603.13792**；本轮把该元数据锁进缓存（source=primary source）。现在 `p3_prl` 的 N-05 显示 **1 verified**（正是 IGU-LoRA），其余 7 条列为 MANUAL 待核 —— 若有人把它改回 Xiao/2025，检查会 FAIL。

**自检**：`python -m tools.paper_audit selftest` 会跑 **17 个 fixture**（每检查至少 1 正 1 负），当前 **17/17 passed**，输出并入 `SELFTEST PASSED`。
覆盖用例：N-01 正/第二个值/归档缺失/注册表缺失；N-02 负值更优（PASS）/负值称更差（FAIL）；N-03 重复 Appendix/泄漏 ref/干净指针；N-04 已登记 DOI/未登记 DOI/"归档含稿件"；N-05 缓存一致/第一作者不符；N-07 已忽略/缺规则/未跟踪 AUD 可见。

**N-07 落地**：`.gitignore` 追加 `docs/audits/*` + `!docs/audits/.gitkeep`，并新增 `docs/audits/.gitkeep`。实测 `git status --porcelain docs/audits` 已无 `?? AUD-*`；`_p1454` 的"leftover audit report"警告从此不再触发（历史已跟踪的报告保持跟踪，不删不改）。

## 3. 最终验证（base 解释器）

```
python -m tools.paper_audit selftest
registry checks: 92
profiles: 10
templates: OK
frozen files verified: 257
… mech fixtures 17/17 …
SELFTEST PASSED
```

六 profile 逐字：
```
a1_paa           READY  grade A  pass=62 fail=0 warn=1 manual=11 skip=18 error=0
paperA_nc        READY  grade A  pass=68 fail=0 warn=1 manual=12 skip=11 error=0
paperA_springer  READY  grade A  pass=63 fail=0 warn=1 manual=12 skip=16 error=0
p3_prl           READY  grade A  pass=56 fail=0 warn=1 manual=12 skip=23 error=0
a23_joe          READY  grade A  pass=65 fail=0 warn=1 manual=11 skip=15 error=0
prl_commentary   READY  grade A  pass=61 fail=0 warn=1 manual=10 skip=20 error=0
```
六者 **fail=0**；唯一 warn 是各 profile 的具名冻结包 I-02（既有 accepted deviation）。新增的 MANUAL 即"无法自动判定"的诚实清单（例如当前稿件的编号方案无法从 PDF 文字层认证、177 条引用缓存待核），**没有一个是因为检查误报而变红**。

## 4. 首次上真稿时修的 4 个检查自身 bug（记录，避免重犯）

1. N-01 播种：ledger 的 `...` / `...<file-hint>` 缩写不能按字面还原 → 改为 hint 解析 + **归档字段必须真实存在且按位数可复现才收录**（否则不播种，绝不把坏种子写进注册表）。
2. N-03 文本来源：把"展开后的主文档 + 原始 .tex 再拼一遍"会造成重复/`\appendix` 位置错乱 → 只用**单一展开文档**；PDF 标题索引必须用**原始文字层**（归一化会删换行，导致标题索引为空）。
3. N-03 泄漏正则：`[a-z]*ref[a-z]*:` 会命中 "therefore:" → 改为 `\bref[a-z]{1,12}:`；指针/星级标题规则从 FAIL 降为 **MANUAL**（不同模板编号无法认证时不允许误红）。
4. N-05：缓存条目 `source=unverified-bib` 曾被当成已验证（自我循环）→ 现在只有真实验证过的条目才算；IEEE 式 `\bibitem` 解析不可靠 → 计入 MANUAL。

## 5. 诚实的局限（Phase 1 未解决）

- **N-01 的正文扫描需要 `mentions` 正则**：从 ledger 播种的 177 条只做了"归档↔canonical"校验（真正有牙齿：归档改了/值不对会 FAIL），但"同一量在正文里印了第二个值"只有 curated 条目（A1 τ–R@1）能自动抓。后续应逐条补 mentions（这是机器可读的待办清单，不再是散文）。
- **N-03 的指针目标**目前是 MANUAL：六个模板的编号（S 前缀补充材料、A.n 附录、Springer 变体）差异大，PDF 文字层不足以认证编号；能 FAIL 的是**确定性的排版泄漏**（`refcor:`/`ref{`/`??`/`Appendix Appendix`），这已覆盖本轮实际发生的 A1/A2 缺陷形态。
- **N-05 的 177 条 unverified**：需要一次性的在线复核（CrossRef/arXiv）才能变成 PASS；离线门禁按设计不联网。
- **N-02 只登记了 2 个 profile** 的能量配对差语义；Gini/ordering 等尚未登记（加数据即可，无需改代码）。
- 六 profile 的 warn 仍受既有 A-01（未提交改动）与冻结 I-02 影响：本轮结束时树上有他人并行改动，故不在此断言"全绿"，只报告逐字判决。

## 6. Phase 2 计划（写入，不实现）

1. **机器可读 review ledger + 发布门禁**（meta-fix）：`docs/REVIEW_LEDGER.json` 每条 `{id, manuscript, severity a/b/c, file:line, status open|fixed|verified, commit}`；新增 `--release` 模式：存在任何 `status=open` 的 (a) 项或任何 FAIL 即拒绝放行。"是否全部修完"从散文变成查询。
2. **staged-package 新鲜度**：若 `SUBMISSION/*_next_revision/` 存在，则其文件必须与 live 稿一致（或显式声明 frozen）；与 `_p1454` 现有 staged 检查合并，避免"同一快照自比"。
3. **版式不变量**（并入 G 渲染维度）：无超过 25% 底部空白的页面、caption 与表格/图不得跨页分离、float 不得超版心；这些是"肉眼一看就不对"但门禁从不测的类别。
4. **`--strict` 发布模式**：把 accepted deviation（冻结包 I-02、A-01 脏树等）一律变成 FAIL，仅用于 release/tag 前的一次性运行；日常开发仍用默认模式。

## 7. 改动文件（未 commit）

`tools/paper_audit/mechanical.py`（新）、`tools/paper_audit/build_registries.py`（新）、
`tools/paper_audit/registry.py`（+6 检查）、`tools/paper_audit/checks.py`（import/wrappers/dispatch/selftest 导出）、
`tools/paper_audit/cli.py`（selftest 跑 fixture）、`.gitignore`、`docs/audits/.gitkeep`（新）、
`docs/QUANTITY_REGISTRY.json`、`docs/SIGN_REGISTRY.json`、`docs/RELEASE_LEDGER.json`、`docs/REF_VERIFICATION.json`（新）、本文件。
未动稿件、`SUBMISSION/**`、其他 tools。


---

## 补充（2026-10-25）：N-05 一次性在线核验已执行并写回

**网络路线**：本轮**直连可用，未使用浏览器代理**。实测（`urllib`，带礼貌 UA
`paper-audit-refcheck/1.0 (mailto:hw4c24@soton.ac.uk)`、1 req/s）：
`api.crossref.org` → HTTP 200；`export.arxiv.org` → HTTP 200（**走 http，443 不通**）；
`api.openalex.org` → HTTP 200。DNS/TCP：crossref/doi/openalex 443 通，export.arxiv 443 不通但 80 可用。
原始响应缓存于 `docs/REF_RESOLUTION_CACHE.json`（212 条响应，34 条请求错误），重跑可离线。
**路由**：DOI → CrossRef `/works/{doi}`；arXiv → `export.arxiv.org/api/query?id_list=`；
无标识 → CrossRef 题名检索（归一化题名完全一致或相似度 ≥0.90，且必须只有一个候选），
候选再经 OpenAlex 题名检索兜底（同样的"唯一候选"约束）。

**采集**：五个活跃稿树共 **246** 个 (key, normalized-title) 条目（去重后），实际解析 **199** 个。
**结果**：**verified 93**（CrossRef 56 / OpenAlex 23 / arXiv 14）；**unverified 106**；
一轮修正后 **mismatch 0**。
未解析的 106 条：**31 条**有 DOI 但 CrossRef 无记录/候选不唯一（需人工核对 DOI 是否为真）；
**75 条**无 DOI/arXiv 且题名检索无唯一权威命中（多为 2025–2026 预印本/工作稿，Crossref/OpenAlex 尚未收录）。

**实际修正（8 个条目，10 处字段；key 全部不变，`\cite` 不受影响）**：

| entry | 字段 | 原值 → 权威值 | 权威来源 |
|---|---|---|---|
| `wang2026ftp` | author | Wang, Zhu, Patras → **Lu, Hui; Salah, Albert Ali; Poppe, Ronald** | CrossRef 10.1016/j.patcog.2026.113794 |
| `chen2025vlmft` | author | Chen 等 → **Danish, Sufyan; Sadeghi-Niaraki, Abolghasem; Khan, Samee Ullah; Dang, L. Minh; Tightiz, Lilia; Moon, Hyeonjoon** | CrossRef 10.1016/j.inffus.2025.103623 |
| `chen2025vlmft` | year | 2025 → **2026** | 同上（Information Fusion 2026-02） |
| `bai2023qwen` | title | 截断 → **"Qwen-VL: A Versatile Vision-Language Model for Understanding, Localization, Text Reading, and Beyond"** | arXiv 2308.12966 |
| `peng2025gnsp` | title+author | 原题名与归档不符 → **"Stabilizing the Modality Gap: Null-Space Projected Continual Learning for Vision-Language Models"**；作者 Peng, Tiantian 等 | arXiv 2507.19839 |
| `adalora2023` | title | 缺方法名前缀 → **"AdaLoRA: Adaptive Budget Allocation for Parameter-Efficient Fine-Tuning"** | arXiv 2303.10512 |
| `thakur2021beir` | title | "heterogeneous" → **"Heterogenous"**（原论文标题的实际拼写） | arXiv 2104.08663 / NeurIPS D&B 2021 |
| `zhai2023forgetting` | title | "…multimodal large language model fine-tuning" → **"Investigating the Catastrophic Forgetting in Multimodal Large Language Models"** | arXiv 2309.10313（CPAL 2024 版标题一致） |
| `chen2025`（A23 bibitem） | title | "current, challenges and future" → **"current, challenge, and future"** | CrossRef 10.1145/3759243 |
| `yaras2026explaining`（Paper A bib） | year | 2026 → **2024**（arXiv 2412.07909 于 2024-12 提交） | arXiv 2412.07909 |

同一批条目在 `paper3/paper_ieee/supplementary/references.bib`（bai/peng/adalora）与
`paper_a1/related_work_bibitems.tex`（thakur）的重复副本一并修正，避免两处 bib 再次分叉。

**重建与页面**（0 errors / 0 undefined citations / 0 overfull）：
`paper_a1/main.pdf` **64**；`paper合/main_nc.pdf` **79**；`paper合/main_springer.pdf` **56**；
`paper3/paper_ieee/main.pdf` **10**；`paper_a2/main_ieee.pdf` **73**；`paper_review_prl/main_prl.pdf` **7**。
**注意**：`paper3/paper_ieee/supplementary/supplementary.pdf` 由历次残留的 `.bbl` 重建后为 **23 页**（此前 26 页）：
章节 S1–S46 全部保留、0 undefined citation，差异来自用 supplementary 自己的 21 条 `references.bib`
重新生成参考文献表。若团队要求维持 26 页需另查旧 `.bbl` 来源；主稿 P3 仍为 10 页（硬约束满足）。

**缓存**：`docs/REF_VERIFICATION.json` 现有 **184** 条（此前 184）→ **verified 93 / unverified 91**；
每条已验证条目带 `{title, first_author, year, venue, doi_or_arxiv, source_url, checked_at, status}`。
离线 N-05 现在不再把已验证条目当 unverified；未核条目继续 MANUAL（原因：见上）。

**N-05 六 profile 逐字**（本轮复跑）：
```
a1_paa           N-05 MANUAL 28 reference(s) verified; 3 DOI/arXiv entries not in the cache
paperA_nc        N-05 MANUAL 16 reference(s) verified; 29 DOI/arXiv entries not in the cache
paperA_springer  N-05 MANUAL 16 reference(s) verified; 29 DOI/arXiv entries not in the cache
p3_prl           N-05 MANUAL 6 reference(s) verified; 2 DOI/arXiv entries not in the cache
a23_joe          N-05 MANUAL 0 reference(s) verified; 18 DOI/arXiv entries not in the cache
prl_commentary   N-05 SKIP   no DOI/arXiv bibliography entries to verify
```
**N-05 零 FAIL**。五个稿树 profile 的判决为 BLOCKED，唯一 FAIL 是 **A-01（未提交改动）**——
这些正是本轮修正的 bib 文件，按要求**未 commit**，提交后即消失；`prl_commentary`（未改）保持 READY。

**顺手修掉的门禁盲点**：`A-01` 原先用 `git status --porcelain` 的原始行做前缀匹配，非 ASCII 路径
（`paper合/…`）会被 git 加引号转义而**漏检**。已改为 `git -c core.quotepath=false status --porcelain`，
现在 Paper A 的未提交改动也能被 A-01 看到（本轮复跑后 paperA 两个 profile 因此如实报 A-01）。


---

## 补充（2026-10-25 晚）：按"无法确认的删除"执行残留文献清理

**指令**：操作者"做，无法确认的删除"；lead 要求逐条尽最大努力确认，只删除确实无权威记录的条目，并修复/删除其引文。

**待处理集合**：`docs/REF_VERIFICATION.json` 中上一轮之后仍 unresolved 的 **92 个 (key,title) 条目**（其中 30 条有 DOI、10 条有 arXiv；分布在
`paper_a1` 10、`paper合` 29、`paper3/paper_ieee` 6、`paper_a2` 9、`paper_review_prl` 41、A1 related-work 1）。
**确认路线**（按序）：DOI → CrossRef `/works/{doi}` + OpenAlex `doi:` + doi.org 解析；无标识 → CrossRef 题名检索（+作者）、OpenAlex 题名检索、
arXiv API 题名检索、DBLP publ API、Semantic Scholar graph search；软件/数据集 → GitHub API / HuggingFace（hf-mirror）API；
自引 → 本地在稿的稿件记录（内部确认）。**环境限制（如实记录）**：DBLP 有 TLS 证书链错误（用不受信上下文重试）、Semantic Scholar 持续 429、
arXiv API 在批量查询后 429，OpenAlex 在收尾阶段 429；恢复期改用**原始响应缓存**（docs/REF_RESOLUTION_CACHE.json，约 400 条响应）与
**arXiv abs 页面**完成最后 8 条的确认，未使用任何未经核对的记录。

### 结果

| 判定 | 条数 | 含义 |
|---|---|---|
| `fixed-identifier` | **51** | 找到权威记录但 bib 缺/错标识 → 已补 DOI 或 arXiv 号（48 处自动 + 手工修正 3 处） |
| `fixed-doi` | **4** | DOI 本身是笔误/截断 → 按权威记录改正（`sonarsurvey2025`、`albert2025kradapter`、`niss2025iimm`、`f3ocus2025`） |
| `confirmed-no-change` | **28** | 权威记录与 bib 一致（含数据集/软件条目） |
| `confirmed-internal` | **4** | 指向我们自己的在稿稿件（`wanA1`/`wanP1`/`wan2026protect`/`wan2026gap`）——用仓库内稿件记录确认，**不删除**（见下） |
| `deleted-unconfirmable` | **5** | 在 CrossRef / OpenAlex / arXiv（部分时段 DBLP/S2 不可用）均无任何记录 → 删除条目 + 清理引文 |

**保留的自引（说明）**：`wanA1`/`wanP1`/`wan2026protect`/`wan2026gap` 指向我们自己正在审稿的稿件（
Paper A 的两个早期标题 `Protect, Don't Perturb` / `Gap Susceptibility: A Dynamical Theory`，以及 A1）。它们的"权威记录"是
**仓库内的在稿稿件本身**（`paper合/main_nc.tex`、`paper_a1/main.tex`、`paper合/sections/theory.tex`），不是公开数据库。
按"不要删掉能联系到权威记录的引用"的原则，这类**内部可确认**条目保留并标 `confirmed-internal`；如果 lead 认为不能在稿引用也应删，
清单即这 4 个 key，可一次性移除。

**数据集/软件条目**：`sharegpt2023`（HuggingFace 数据集 API 返回 `anon8231489123/ShareGPT_Vicuna_unfiltered`）、
`ilharco2021openclip`（GitHub API 返回 `mlfoundations/open_clip`）、`oceanclip2025`（HF 模型卡 API）均确认存在，保留。

### 删除的 5 个条目与其"失去的主张"（逐条列出，供 lead 复核）

| key | 文件 | 删除原因 | 因此删除/改写的正文主张 |
|---|---|---|---|
| `imod`（arXiv 无记录；CVPR 2026） | `paper_a1/main.tex` 的 bibitem；`main_zh.tex` 镜像 | CrossRef/OpenAlex/arXiv 无记录（2026 年文献，任何库均未收录） | A1 引言与相关工作两处列表短语"参数空间目标优化的是模态不平衡而非 gap 本身"[cite] 被删；中文镜像对应两处 `\cite{imod}` 删除 |
| `zhang2026imod`（与上条同一篇，Paper A 的 bib） | `paper合/references.bib` | 同上 | 相关工作删除句："IMoD 提出隐式模态分解，动机是多模态模型中可训练参数被文本模态主导、非文本模态欠训练"；并**重写**随后与 IMoD 的三点对比段（原段逐条比较其设置/分解/证据，均锚定该文，失去该对比，仅保留"与设计模式方向相反、但同样需测量"的泛化表述） |
| `zhao2026gapinit`（ICML 2026） | `paper合/references.bib`、`paper3/paper_ieee/references.bib` | 同上 | Paper A：相关工作中的"Gap-Init 提出把 LoRA 初始化对齐 gap 向量"删除（改为泛称"initialization schemes align LoRA with the gap vector"）；讨论中"Third, unlike Gap-Init, which observed empirically that the modality gap dominates early gradient flow..."改为泛称"gap-aware initialization schemes"；P3 相关工作删除句"Gap-Init aligns LoRA initialization with the modality-gap direction to stabilize training."（main 与 full 两处） |
| `cheng2026maab`（Information Fusion 2026） | `paper合/references.bib` | 同上 | "We adopt the CG/DG terminology of [liu2026tpc, cheng2026maab]" 改为仅引 `liu2026tpc`；失去"`cheng2026maab` 同用 CG/DG 术语"这一归属 |
| `shao2025tokencompression`（arXiv 2025） | `paper_review_prl/MANUSCRIPT.md` + `_refs_used.json` | arXiv API/OpenAlex/CrossRef 均无记录（该时段 arXiv 429、OpenAlex 429，已按缓存逐条核查） | Commentary 对比表删除一行「`[shao2025tokencompression]` | multimodal LLMs | the token budget axis | reported results」；综述的"token 预算轴"这一对照项失去 |

**同时修正的正文/元数据（非删除）**：
- `sun2026narrow`：作者由 `Sun, Mingjie; Ren, Jie; Liu, Leo Z.; Liang, Percy` 改为权威记录 `Giordani, Jeremiah`；年份 2026→2025；venue 2026 ICLR Workshop → arXiv preprint arXiv:2507.03662（原条目把另一篇的作者/年份写到了这篇上）。
- `hu2025loralimits`：标题改为 arXiv 权威写法 "…(LoRA) Fine-Tuning for Transformer Models"；ICLR 2025 → arXiv preprint arXiv:2406.03136；年份 2024；作者按 arXiv 全名补齐。
- `f3ocus2025`：补 CVPR 2025 DOI `10.1109/cvpr52734.2025.01863`（原条目无 DOI）。
- `huh2024platonic` / `ovadia2019trust` / `yuksekgonul2023when` / `liu2024dora`：补 arXiv 号（2405.07987 / 1906.02530 / 2210.01936 / 2402.09353；均经 arXiv abs 页面或 API 核对）。
- `ding2021grounding`：A1 bibitem 标题 "through statistical testing" → 权威 "with statistical testing"。
- A23 两个 bibitem（`s3simulator2024`、`sonarsurvey2025`）此前自动补的 DOI 被错误挂在空的 `\bibitem` 行（造成 74 页与 PDF 文本破行），已移除、恢复原样（DOI 本已在该条目正文行内）。

### 重建与页面（0 errors / 0 undefined citations/references / 0 overfull）

| 文档 | 页数 | 目标 |
|---|---|---|
| `paper_a1/main.pdf` | 64 | 64 ✓ |
| `paper合/main_nc.pdf` | 79 | 79 ✓ |
| `paper合/main_springer.pdf` | 56 | 56 ✓ |
| `paper3/paper_ieee/main.pdf` | 10 | 10 ✓ |
| `paper3/paper_ieee/supplementary/supplementary.pdf` | 23 | 23 ✓ |
| `paper_a2/main_ieee.pdf` | 73 | 73 ✓ |
| `paper_review_prl/main_prl.pdf`（经 `tools/_build_prl_tex.py`） | 7 | 7 ✓ |

页面常数**无需净修改**：过程中 A23 曾因错误注入的 DOI 行变成 74 页，常数临时改为 74，修复注入后回到 73，
`tools/_p1454_final_verify.py` 与 `paper_a2/verify_a23_fix.py` 均已恢复 73（`paper_a2/verify_a23_fix.py` 的注释里保留了这段经过）。
Commentary 走 builder（`MANUSCRIPT.md` + `_refs_used.json` 47 条）重建。

### 门禁复跑（base 解释器）

`python -m tools.paper_audit selftest` → **SELFTEST PASSED**（92 checks / 17 fixtures 17/17）。
六 profile（N-05 现在**零 FAIL**）：
```
a1_paa           BLOCKED grade D  pass=61 fail=1 warn=1 manual=11 skip=18 error=0   N-05 MANUAL 34 verified / 2 not in cache
paperA_nc        BLOCKED grade D  pass=67 fail=1 warn=1 manual=12 skip=11 error=0   N-05 MANUAL 36 verified / 8 not in cache
paperA_springer  BLOCKED grade D  pass=62 fail=1 warn=1 manual=12 skip=16 error=0   N-05 MANUAL 36 verified / 8 not in cache
p3_prl           BLOCKED grade D  pass=55 fail=1 warn=1 manual=12 skip=23 error=0   N-05 MANUAL 7 verified / 4 not in cache
a23_joe          BLOCKED grade D  pass=63 fail=1 warn=1 manual=11 skip=15 error=0   N-05 MANUAL 1 verified / 18 not in cache
prl_commentary   BLOCKED grade D  pass=60 fail=1 warn=1 manual=10 skip=20 error=0   N-05 SKIP
```
**唯一 FAIL 均为 A-01（未提交改动）**——本轮改动按要求未 commit，提交后即清除。
`python tools/_p1454_final_verify.py --apply`：`A23 verify: True`、`p3_audit_check/pdf: True`、`staged packages: True (wrong: [])`、
`pages: … pass: True`、`bootstrap/decoder integration: True`；**唯一失败项 `git clean: False (24 uncommitted paths)`**——同样是未提交改动，
提交后应为 PASS；另有 14 条 WARN（6 条冻结包 I-02 + 7 条 staged-snapshot 新鲜度 + 1 条 dirty tree）。

### 最终缓存

`docs/REF_VERIFICATION.json`：**184 条 → verified 179 / deleted-unconfirmable 5 / unverified 0**。
每个删除条目保留 `status: deleted-unconfirmable` + `attempts`（服务、query 摘要、错误），可复核；每个修复条目保留
`source_url`、`doi_or_arxiv`、`checked_at`。原始响应缓存 `docs/REF_RESOLUTION_CACHE.json` 同步更新（≈400 条响应）。

---

## 最终 tranche（2026-10-25 深夜）：N-05 "not in the cache" 32 条的处置

**结论：33 个条目（去重后）全部是 N-05 解析器的假阳性，0 个重复合并、0 个删除、0 条主张丢失。**
根因有二：(a) 合法两字母姓氏（Hu/Li/Xu/Wu/Yi/He/Yu/Lu）被 3 字符下限挡掉；(b) A23 的 IEEE 式
`\bibitem{key}` 后换行写正文、以及无引号的题名，旧解析器取不到题名/作者。所有条目在更早轮次
已有 verified 缓存（见下表 route 列）；修好解析器后它们直接与缓存比对通过。

**本轮对缓存做的唯一实质修正是 3 条元数据对账**：
- `yi2025`：缓存里的 v1 标题（"The Convergent Representation of Vision-Language Contrastive..."）
  已按 arXiv abs 页面（2510.03268，2025-09-27）更新为 "Decipher the Modality Gap in Multimodal
  Contrastive Learning: From Convergent Representations to Pairwise Alignment"，年份 2025；
- `hu2021`/`hu2021lora`/`hu2022lora`：缓存持有 arXiv 记录（2021-06-17），稿件引用 ICLR 2022；
  DBLP 现已返回反爬墙（HTTP 202 "Making sure you're not a bot"），Semantic Scholar 仍 429，
  无法直接核对 ICLR 2022 记录 ⇒ 三者标 `year_comparable: false`（不伪造年份），标题/作者仍校验。

**路线可用性（实测）**：CrossRef DOI 与 arXiv abs 页面直连可用（本轮用 abs 页确认 2510.03268 与
2106.09685）；OpenAlex 直连可用但题名检索噪声大；**DBLP 直连被 Anubis 反爬墙拦截（202）**；
**浏览器代理（web-access skill）不可用**：CDP proxy 可启动但浏览器连接超时，需要用户在浏览器点击
"允许"授权；**Semantic Scholar 持续 429**。均在缓存 `attempts`/本表中记录。

| key | 判定 | 确认路线 | 标识 |
|---|---|---|---|
| `aquaticclip2026` | verified | CrossRef DOI | 10.1109/TNNLS.2026.3657138 |
| `aubard2025` | verified | CrossRef DOI | 10.1109/JOE.2025.3531933 |
| `chen2025` | verified | CrossRef DOI | 10.1145/3759243 |
| `christensen2026` | verified | CrossRef DOI | 10.1016/j.oceaneng.2026.124646 |
| `jian2024` | verified | CrossRef DOI | 10.1007/s44295-024-00023-6 |
| `kim2026acoustic` | verified | arXiv API listing | arXiv:2609.31785 |
| `liang2022` | verified | CrossRef DOI | 10.52202/068431-1280 |
| `maione2026` | verified | CrossRef DOI | 10.1016/j.oceaneng.2026.127078 |
| `marinegpt2023` | verified | crossref/arxiv/openalex titl | 10.48550/arxiv.2310.13596 |
| `mvaldenegro2024` | verified | crossref/arxiv/openalex titl | 10.48550/arxiv.1905.05241 |
| `oceangpt2023` | verified | CrossRef DOI | 10.18653/v1/2024.acl-long.184 |
| `qin2022` | verified | CrossRef DOI | 10.3390/rs14153794 |
| `s3simulator2024` | verified | crossref/arxiv/openalex titl | 10.1007/978-3-031-78444-6_15 |
| `sofer2025` | verified | CrossRef DOI | 10.21437/Interspeech.2025-1664 |
| `sonarsurvey2025` | verified | crossref/arxiv/openalex titl | 10.1109/sibgrapi67909.2025.11223279 |
| `uatd2022` | verified | CrossRef DOI | 10.1038/s41597-022-01854-w |
| `wortsman2022` | verified | CrossRef DOI | 10.1109/CVPR52688.2022.00780 |
| `yamaguchi2025` | verified | CrossRef DOI | 10.1109/CVPR52734.2025.00402 |
| `yi2025` | verified | arXiv abstract page | arXiv:2510.03268 |
| `he2026dulbe` | verified | arXiv API listing | arXiv:2609.36759 |
| `hu2021lora` | verified | arXiv abstract page | arXiv:2106.09685v2 |
| `hu2026visualbranch` | verified | arXiv API listing | arXiv:2609.37888 |
| `li2022blip` | verified | crossref/arxiv/openalex titl | 10.48550/arxiv.2201.12086 |
| `wang2026ftp` | verified | CrossRef DOI | 10.1016/j.patcog.2026.113794 |
| `xu2026vlreasoning` | verified | crossref/arxiv/openalex titl | 10.48550/arxiv.2604.16256 |
| `yi2025decipher` | verified | crossref/arxiv/openalex titl | 10.48550/arxiv.2510.03268 |
| `yu2026aniso` | verified | crossref/arxiv/openalex titl | 10.48550/arxiv.2605.07825 |
| `he2026loraga2` | verified | arXiv API listing | arXiv:2608.19800 |
| `hu2021` | verified | arXiv abstract page | arXiv:2106.09685v2 |
| `hu2025loralimits` | verified | arXiv abstract page / CrossR | arXiv:2406.03136 |
| `wu2025language` | verified | arXiv API listing | arXiv:2508.10552 |
| `hu2025inferencecal` | verified | CrossRef DOI | 10.1016/j.patrec.2025.03.010 |

**N-05 复跑（六 profile，本轮逐字）**：
```
a1_paa           N-05 PASS   36 DOI/arXiv reference(s) match the verified cache
paperA_nc        N-05 PASS   44 DOI/arXiv reference(s) match the verified cache
paperA_springer  N-05 PASS   44 DOI/arXiv reference(s) match the verified cache
p3_prl           N-05 PASS   11 DOI/arXiv reference(s) match the verified cache
a23_joe          N-05 PASS   19 DOI/arXiv reference(s) match the verified cache
prl_commentary   N-05 SKIP   no DOI/arXiv bibliography entries to verify
```
极终六 profile：**全部 READY grade A、fail=0**（唯一 warn 为各 profile 的具名冻结包 I-02）。
页面：A1 64 / PaperA 79+56 / P3 10 + supp 23 / A23 73 / Commentary 7；0 errors / 0 undefined / 0 overfull；
本轮未改任何稿件文本，故未重建 PDF。`selftest`：**SELFTEST PASSED**（17/17 fixtures）。

改动：`tools/paper_audit/mechanical.py`（bibitem 解析 + 姓氏守卫 + 题名引号清理）、
`docs/REF_VERIFICATION.json`、`docs/REF_RESOLUTION_CACHE.json`；新增 `tools/paper_audit/debug_n05_view.py`
（复现 N-05 的解析视角）。`SUBMISSION/**` 未动，未 commit。


---

## 补充（2026-10-26）：Paper A 的 LoRA Flickr30k run 数 49 vs 43 已从归档settle

**问题**：`paper合/sections/validation.tex` 正文写 "55 archived LoRA runs (49 on Flickr30k, 6 on MS-COCO)"，
而同一文件的 cross-dataset 表（`tab:generalization`）该行 `Runs` 列写 **43**。

**归档证据**（`outputs/analysis/ode_ledger.json`，即 `tab:generalization` 的 provenance 文件，见
`docs/PROVENANCE_MANIFEST_2026-10-20.md:117`）：
- `subsets.lora.n = 55`；`subsets.lora_flickr.n = **49**`；`subsets.lora_coco.n = 6`；`subsets.all.n = 96`；
- `runs[]` 中 `family=lora, top=v1_trajectory`（Phase-2 rank sweep）= **43** 条；
  `family=lora, top=beta_pilot`（Phase-1 pilot）= 6 条；两者都在 Flickr30k 上 ⇒ 49 = 43 + 6；
- 表中三个统计量逐位匹配 **43 条 sweep 子集**：R² mean 0.9530 / sd 0.0135（稿件 0.953±0.014）、
  α −0.0257（稿件 −0.026）、β 0.0672（稿件 0.067）；若用 49 条样本则为 R² 0.9542/0.0132、α −0.0250、
  β 0.0639。⇒ **两个数都真实，但计的是不同集合**：49 = 归档的 Flickr30k LoRA runs 总数，
  43 = 表格所用的 rank-sweep 子集。

**改动**（两个 tree 由 reframed build 保持同步，reframed 是 block-level 从 frozen sections 生成）：
- `paper合/sections/validation.tex:4`：改为 "(49 on Flickr30k --- 43 rank-sweep runs plus 6 from the
  Phase-1 pilot --- and 6 on MS-COCO)"；
- `paper合/sections/validation.tex:30`：改为 "Across the sweep and the Phase-1 pilot, 55 LoRA trajectories ...
  : 43 rank-sweep runs and 6 pilot runs on Flickr30k ..., plus 6 on MS-COCO"；
- `paper合/sections/validation.tex:124`（table caption）：增加 "The Runs column counts rank-sweep runs; the six
  Phase-1 pilot runs on Flickr30k are archived separately and are not pooled into that row."
- `tools/_claim_ledger.py`：原 "（43 run）" 主张改为对 **43 条 sweep 子集**取均值（0.953，逐位匹配）；
- `paper合/reframed/**` 由 `python tools/_pa_reframe_build.py --apply` 重新生成（`--check` rc=0），
  `paper合/reframed/main.pdf` 重建。

**重建与页面**：`paper合/main_nc.pdf` **79**、`main_springer.pdf` **56**、`paper合/reframed/main.pdf`
**83 total / main text 39**（appendix 从 p40 起；与 `PAGE_BUDGET.md` 的 p1–39 预算一致）；
0 errors / 0 undefined citations / 0 overfull。

**N-01 注册**（`docs/QUANTITY_REGISTRY.json`，paperA_nc 与 paperA_springer 各 3 条；`build_registries.py`
的 curated 段同步，重建不会丢）：
- `Flickr30k LoRA archived runs` = **49**（archive `ode_ledger.json:subsets.lora_flickr.n`，mention 正则抓
  "49 on Flickr30k"×2 与表行 Runs 的 β 锚定 43），`allowed_variants=[{43, "rank-sweep subset (Runs column ...;
  49 also counts the 6 Phase-1 pilot runs)"}]`；
- `archived LoRA runs (all)` = **55**；`archived ODE fits (all)` = **96**。
实测 gate：这两个 profile 的 N-01 为 **MANUAL（87 archive-verified，84 条 seeded 无 mention）且 **0 fails**，
新 mention 全部命中并校验通过（49/49/43/43/55/55/96）。以后若再把 43 写成 49（或反之）会直接 FAIL。
**未 commit**；`SUBMISSION/**`、其他稿件、`paper3/` 未动。
