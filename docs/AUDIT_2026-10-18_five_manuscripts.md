# 五稿并行复核（2026-10-17 深夜 / 2026-10-18 投前）

> 触发："更新进度并再次审核，包括 paper合、paper3、A1、A23 和 PRL 的那篇综述"。
> 方法：本地只读复核 + 独立编译/门禁；外部仅核实 GitHub 仓库可见性与 Zenodo DOI 元数据。
> 结论先行：**Paper A 可投（明日 Neurocomputing）**；**P3 与其余三稿在审、冻结不动**，但 PRL Commentary 的
> **已投 PDF 有若干可见缺陷**（详见 §5），只能在修回/重投时修；文档层若干陈旧条目已在本轮同步。

## 1. Paper A（`paper合/`）—— 明日投 Neurocomputing

| 项 | 实测 | 判定 |
|---|---|---|
| 页数 | NC **70 页** / Springer **50 页**（pdfinfo） | PASS |
| 编译 | 两版均 0 错误 / 0 未定义引用 / 0 未定义引文 / 0 Overfull（当日 21:37 构建日志，与 PDF 同秒） | PASS |
| 摘要 | **231 词**（源码口径：公式按 1 词；≤250） | PASS |
| Highlights | 5 条，最长 **62** 字符（≤85）；PDF/txt 哈希一致 | PASS |
| 参考文献 | **52** 条 = 52 个 cite key，0 缺失 / 0 未引用 | PASS |
| 声明顺序 | Data availability / Funding / Competing / CRediT / AI 全部在 References 之前 | PASS |
| 双台账 | `_claim_ledger_paperA.py` **76/76 PASS, 0 GAP**；`_claim_ledger.py` **96/96** | PASS |
| 投稿包 | 45 文件；独立临时目录编译 **70 页 0 错误**；Manuscript/Cover Letter/Highlights 与 live 哈希一致 | PASS |
| 一致性门禁 | `tools/_p1181_verify_paperA_consistency.py` **0 failure**（含**动态**页数/摘要词数检查） | PASS |
| 数据声明 | GitHub 仓库 PUBLIC；E/G 记录（`vlm_clean_summary.json`、`canonical_caption_metric.json`、`vlm_clean_cloud/` 53 项、`full_coco.json`）已在公开仓库；Zenodo DOI 存在 | PASS |

**本轮发现并修复**（若不修，明日提交件会带错）：
1. 两封 cover letter 仍写 "**The manuscript is 68 pages**"，实际 **70 页** → 已按构建实测回写并重编译；
2. cover letter 摘要词数 234（与实测 231 不符）→ 统一为 **231**；
3. `NC_submission/README.md` 严重过期（68 页 / 234 词 / 48 文献 / 383=221+162 / 74/74）→ 按实测重生成
   （**70 页 / 231 词 / 52 文献 / 317=221+96 / 76/76**）；
4. `_p1178` 模板中的 383/162 口径 → **317=221+96**；`_p1176`、`_p1181` 同步更新（门禁新增动态页数/词数断言，防止同类回归）。

## 2. Paper 3（`paper3/paper_ieee/`）—— 在审、冻结

| 项 | 实测 | 判定 |
|---|---|---|
| 页数 | main **10** / main_full **13** / main_10pp **10** / supplement **6** | PASS |
| 审计 | `audit_check.py` **72 PASS / 0 FAIL / 0 WARN**；`audit_pdf.py` **98 PASS / 0 FAIL / 0 WARN** | PASS |
| 提交件冻结 | CORRECTED_2026-10-15 与 UPLOAD_2026-10-15 的 main/supplement **SHA-256 未变**（b96f…/e9b7…） | PASS |
| 本地 vs 提交 | 本地构建已修 \nabla/Overfull（供下一轮），与提交件按预期不同；`_p1172` 以 INFO 记录 | PASS（符合设计） |
| 遗留 | 提交版 PDF 摘要仍印 "abla"（在审冻结，下一轮修订修）；CORRECTED/UPLOAD 的 README 写 supplement "5 页"（实 6），属 SUBMISSION 冻结区未动 | 记录 |

## 3. A1（`paper_a1/`）—— Neural Networks `NEUNET-D-26-09426` **桌面拒稿（2026-10-18）**

| 项 | 实测 | 判定 |
|---|---|---|
| 主 PDF | `main.pdf` **42 页**、798,566 B、2026-10-12 02:06（elsarticle，`\journal{Neural Networks}`） | PASS |
| 系统投稿件 | `docs/_inbox/NEUNET-D-26-09426.pdf` = `docs/reviews/A1_NEUNET-D-26-09426/submission.pdf`（SHA-256 相同，51 页：系统页+信+highlights+42 页正文+4 图+declaration） | PASS |
| 编译 | 日志与 PDF 同秒；0 错误 / 0 未定义引用 / 0 未定义引文 / 0 Overfull（4 条 hyperref warning 属无害） | PASS |
| 摘要 | 212 词（去公式）/ 229（公式算 1 词）/ 249（项目粗口径），三种均 ≤250 | PASS |
| 关键词/Highlights | 5 个关键词；5 条 highlights，最长 **69** 字符（≤85） | PASS |
| 参考文献 | 内联 thebibliography **56 条 = 56 cite key**（0 missing / 0 unused）；2 条作者不可考标 Anon. | PASS（2 Anon. 记录） |
| 声明顺序 | Competing / Funding / AI 均在 thebibliography 之前 | PASS |
| 合规缺口 | NN Guide **Option C** 要求数据存放+链接或"不能共享"说明；稿件与包内**无 Data availability 节**（EM 表单是否另填不可见） | **WARN（修回时补）** |
| 日期口径 | 系统包 p51 declaration 为 **12 Oct**；上传的 cover letter 与 `declaration.pdf` 为 **10 Oct**（混版） | WARN（修回时统一） |
| 文档 | `paper_a1/README_是哪篇.md` 仍写 Neurocomputing/40 页/不在推进队列（全面过期）；`文件地图.md` A1 段仍写"ATS 转投待确认" | 已在本轮更新 |

## 4. A23（`paper_a2/`）—— IEEE JOE `26-0663` 在审

| 项 | 实测 | 判定 |
|---|---|---|
| 提交主 PDF | `main_ieee.pdf` **64 页**、1,250,435 B、2026-09-22（IEEEtran 单栏 12pt 双倍行距+连续行号）；与 `SUBMISSION/A23_JOE/current/` 哈希一致 | PASS |
| 编译 | 与 PDF 同秒；0 错误 / 0 未定义引用 / 0 未定义引文 / **0 Overfull** / 0 Float too large | PASS |
| 摘要 | 176 词（去公式）/ 195（公式算 1 词），JOE 要求 150–250 | PASS |
| 关键词 | 5 个（JOE L44 允许 3–5；L40 另写 3–4，指南自身矛盾） | PASS（口径 WARN） |
| 参考文献 | 内联 **29 条 = 29 cite key**，0 missing / 0 unused | PASS |
| 声明顺序 | Data availability / Funding / Competing / CRediT / Acknowledgements（含 AI 披露）均在文献前 | PASS |
| 补充材料 | `SUPPLEMENTARY_FOR_REVIEWERS.pdf` **43 页**（1 索引 + 2–3 OE 决定信 + 4–43 同伴稿） | PASS（`文件地图.md` 旧写 50 页，已改） |
| 小瑕疵 | 摘要 `UATD`/`DTD` 未展开；1 条 DOI 文本层下划线缺失（`...-78444-6_15` → 提取为 "…-6 15"）；封面信日期 9/22 CST vs 门户 9/21（已有时区解释） | WARN（非阻断） |

## 5. PRL Commentary（`paper_review_prl/`）—— `PRLETTERS-D-26-02402` 在审

| 项 | 实测 | 判定 |
|---|---|---|
| 提交件 | `UPLOAD/Manuscript.pdf` **7 页**（279,284 B，2026-09-28 22:29:59）；与 `SUBMISSION/Review_PRL/` 逐字节一致 | PASS |
| 独立复编译 | 临时目录两遍编译 → 7 页、279,284 B，文本 SHA-256 与上传件**完全一致** | PASS（可复现） |
| 合规 | 摘要 **224** 词；43 条引用 43/43 自洽；Highlights 5 条（71/54/63/63/63）；关键词 PDF 5 个 | PASS |
| 编译 | 0 错误 / 0 未定义引用/引文；**2 处 Overfull**（123.6pt @ `\maketitle`、21.9pt 表 1） | FAIL（排版） |
| **§4 清单渲染损坏（最严重）** | 源 `MANUSCRIPT.md` 的 1–12 清单被生成器 `_build_prl_tex.py` 渲染成 **4 组各自从 1 编号的 18 个条目**，与正文 "items 6/8/12" 及表 2 映射完全脱节 | **FAIL（修回必改）** |
| 章节号双写 | 15 个标题全部 "1. 1. Introduction" 式叠加 | FAIL |
| 压缩丢引用 | 09-28 22:15 压缩时删除 `xin2024vpeftsurvey`、`shao2025tokencompression` ⇒ "two cover … respectively" 只剩 1 条、表 1 第 3 行留空 | FAIL（主张与引用不匹配） |
| 转换残留 | `<scp>AutoPEFT</scp>`、`&amp;`、空 `ORCID(s):` | WARN |
| 声明 | 稿内无 Declaration/Data availability 等段（只在 EM 门户字段） | WARN（对照 PRL Guide 再定） |
| 封面信 | 仍用旧标题 "…a critical review of parameter-efficient adaptation for multimodal models" vs 稿件 "…comparability in parameter-efficient multimodal adaptation" | FAIL（上传件不一致） |
| 文档 | UPLOAD 实际 **5 件**（文档写 6）；引用数 26/35 旧值（实 43）；SPEC 235 词/3,742 词旧值（实 224/3,698） | 已在本轮记录并注明 |

**处置**：稿在审，按纪律**不改动**；上表为修回/重投时的优先修复清单（先修生成器，再重跑页数/编译门禁；
现有 `_final_check_prl.py` 会误报"全部通过"——它不检查清单编号、章节号、Overfull、关键词、声明段与封面信标题）。

## 6. 文档同步（本轮）

- `HANDOFF.md` 顶部新增本阶段条目；
- `文件地图.md` 状态块更新到 2026-10-18（五稿并列），编号条目追加；
- `哪篇是哪篇.md` 全量重写（A1 已转 Neural Networks、P1 已拒、Paper A 70/50、P3 10 页等）；
- `paper_a1/README_是哪篇.md` 更新为当前事实；
- 更正 `文件地图.md` 中 A23 补充材料 "50 页" → **43 页**。

## 7. 下一步

1. **2026-10-18：按 `paper合/NC_submission/README.md` 上传 Paper A（Neurocomputing）→ 落稿号**；
2. A1：修回时补 Data availability（NN Option C）+ 统一 12 Oct 日期；
3. A23：修回时展开摘要缩写、修 1 条 DOI；
4. PRL Commentary：若获修回/重投，按 §5 清单修（先 `_build_prl_tex.py` 生成器）；
5. P3：等编辑部，下一轮修订修 "abla" 并更新替换件。

## 8. 修复结果（2026-10-18，"全部修好"）

> Paper A / P3 的本轮已在 §1–§2 复核；A1 / A23 / PRL Commentary 的**本地工作副本**已按 §3–§5 清单修复并重建。
> **已投出/提交的冻结件一律未动**（SUBMISSION/ 与 PRL 的 UPLOAD/ 哈希逐一复核不变）；所有改动的证据在各自目录的 `FIXES_2026-10-18.md`。

### 8.1 A1（`paper_a1/`）

| 修复 | 结果 |
|---|---|
| 新增 Data availability 节（NN Option C） | `main.tex:605`，位于 Funding 之后、生成式 AI 声明之前（参考文献前）；链接 GitHub 仓库 + Zenodo DOI |
| 日期统一 | `cover_letter.tex` 与 `declaration.tex` 由 10 Oct → **12 October 2026**，重编译 |
| P1 状态与伴稿标题 | cover letter 改为 "rejected after peer review"；伴稿改用新标题 *Adaptation Site and the Modality Gap…*；文献 `wan2026protect` 同步（"Manuscript submitted for publication"） |
| 数据句一致化 | 结论与 cover letter 的 "发表后公开" 改为与 Data availability 一致 |
| 重建验证 | main **42 页**、cover letter **2 页**、declaration **1 页**；均 0 错误 / 0 未定义 / 0 Overfull |
| 冻结 | `SUBMISSION/A1_NeuralNetworks/` 16 文件 SHA-256 全部不变 |
| 残余 | 工作副本 `declaration_of_interest.docx` 仍是 09-16 旧版（12-Oct 版只冻结在 SUBMISSION）→ 修回时用 Elsevier 工具重生成 |

### 8.2 A23（`paper_a2/`）

| 修复 | 结果 |
|---|---|
| 摘要缩写 | `main_ieee.tex:44`：`Describable Textures Dataset (DTD)`、`Underwater Acoustic Target Detection (UATD)`（依据本稿引用的数据集论文/官方页，非猜测） |
| DOI 文本层 | 第 918 行参考条目改用 T1 编码 + `\\href`：`10.1007/978-3-031-78444-6_15` 完整出现在文本层，断串为 0 |
| abstract.tex/pdf | 刷新为 IEEEtran 独立页（旧版仍写 Ocean Engineering / 7 关键词）；**`tools/build_abstract_standalone.py` 已改**：`paper_a2` 改从 `main_ieee.tex` 提取 title/author/abstract/IEEEkeywords，重跑不再回退 |
| cover letter | 补上 "collapsed UATD fine-tune 是唯一例外" 以匹配摘要/结论；加 `\\sloppy` 消掉 2 处 Overfull |
| 重建验证 | `main_ieee.pdf` **64 页**、0 错误 / 0 未定义 / **0 Overfull**；行号 1–1181 连续、单栏 12pt、页码 1–64 保留；`verify_a23_fix.py` 29 项断言全 PASS |
| 冻结 | `SUBMISSION/A23_JOE/` 37 文件 SHA-256 全部不变 |

### 8.3 PRL Commentary（`paper_review_prl/` + `tools/_build_prl_tex.py`）

| 修复 | 结果 |
|---|---|
| §4 清单 | 生成器把 4 组重编号合并为**一个 1..12 enumerate**（续行并回条目；构建断言 12 项） |
| 章节号双写 | 生成器剥离 MANUSCRIPT.md 的手写编号，15 个标题单一编号 |
| 丢引 | 恢复 `xin2024vpeftsurvey`（§1 "…respectively [40, 41]"）与 `shao2025tokencompression`（表 1 第 3 行 [33]）；文献 **43 → 45 条** |
| 渲染残留 | `<scp>`、`&amp;`、空 `ORCID(s):` 全部清除；表格题注挂浮动体、表 1 改 `tabularx`；natbib `sort&compress` |
| 封面信 | 改用终稿标题并重编译（2 页）；生成器新增 "标题不一致即失败" 门禁 |
| Overfull | **2 → 0**（`\\maketitle` 123.6pt 与表 1 21.9pt） |
| 声明 | 按 PRL Guide 补 Declarations（竞争利益/Funding/Data availability/CRediT）+ 独立 GenAI 节，均在参考文献前 |
| 重建验证 | `main_prl.pdf` **7 页**（1 highlights + 6 正文）、0 错误 / 0 未定义 / 0 Overfull；清单 1..12、无章节号双写、无 HTML 残留、45 条文献 |
| 门禁 | `tools/_final_check_prl.py` 已补上原盲区（Overfull / 章节号 / 清单编号 / HTML 残留 / 声明位置 / 封面信标题），现 **全部通过** |
| 冻结 | `paper_review_prl/UPLOAD/` 5 件与 `SUBMISSION/Review_PRL/` 23 件 SHA-256 全部不变 |
| 判断项 | ① 加入声明后 7 页装不下，图宽 **0.92→0.75**（未删正文/highlights）；② 4 条声明合并为一节、GenAI 独立；**Funding "无资助" 与 GenAI（Claude+DeepSeek）为作者声明，建议操作者确认**；③ §2.2 重复子句去重后，CLIP-Adapter/ARD-LoRA 与 "主/次奇异分量初始化" 表述需作者返修时重新拆分 |

### 8.4 说明

- 上述 A1/A23/PRL 的修改只落在**本地工作副本**；本轮不重投、不替换在审稿件。
- 各稿 PDF 被 `.gitignore` 忽略（`*.pdf`），入库的是 tex/md/证据文档；提交文件在磁盘上可交付。
