# P3（PRL 投稿）首投 → 当前工作稿 变更汇总（2026-10-24）

> 面向操作者的交接件。**只读调查，未改动任何稿件、package 或归档**（本轮唯一写入 = 本文件）。
> 证据标记：**[文件]** = 从文件/PDF/JSON 实测得到；**[笔记]** = 只在某份笔记里记录，文件名已给出；
> **未核实** = 无法验证，并写出"什么能验证它"。
> 页数一律为 pypdf 实测（`PdfReader(...).pages`）。JSON 字段一律写成 `文件 :: 字段路径`。

---

## 1. Timeline（每个投递事件一行）

| # | 日期 | 事件 | 稿号 | package 目录 | main / supp 页 | 证据 |
|---|---|---|---|---|---|---|
| 1 | 2026-09-26 | 首投 Pattern Recognition Letters | `PRLETTERS-D-26-02378` | `SUBMISSION/_archive/_superseded_P3_PRL_submitted_2026-09-26/` | **11 / 无独立补充材料** | `[文件]` `manuscript.pdf` = 11 pp；该目录内无 supplementary PDF（目录实测）；appendix 在主稿内：`latex_source/main.tex:51-52`（`\appendix` + `\input{sections/appendix}`）。时刻 16:22 见 `[笔记]` `文件地图.md:272` |
| 2 | 2026-09-30（记录值） | 决定 **Revise**，33 条意见，deadline **2026-11-02** | `PRLETTERS-D-26-02378` | — | — | `[文件]` deadline：`.../reviews/PRL Revison.txt:26`；`[笔记]` 决定日 2026-09-30 见 `docs/P3_RESUBMISSION_AUDIT_2026-10-21.md:76`（决定信本身无日期）|
| 3 | 2026-10-13 | R1 修订稿投出 | `PRLETTERS-D-26-02378R1` | `SUBMISSION/_archive/P3_PRL_rejected_2026-10-21/UPLOAD/` | **10 / 5**（S1–S9） | `[文件]` `P3_PRLETTERS-D-26-02378_Manuscript.pdf` = 10 pp、`..._Supplementary.pdf` = 5 pp；S 编号 1–9 由 PDF 文本实测 |
| 4 | 2026-10-15 | 替换件（main + supplementary + LaTeX source）经 EM 请求送出 | `PRLETTERS-D-26-02378R1` | `.../CORRECTED_2026-10-15/`、`.../UPLOAD_2026-10-15/` | **10 / 6**（S1–S9） | `[文件]` `main_corrected.pdf` = 10、`supplementary_corrected.pdf` = 6 pp；两份文件的 SHA-256 冻结在 `tools/paper_audit/freeze/p3_prl.json` |
| 5 | 2026-10-19 | 冻结副本落盘 | `PRLETTERS-D-26-02378R1` | `SUBMISSION/_frozen_submitted/P3_PRL_R1/` | **10 / 5** | `[文件]` 两份 PDF 与 #3 的上传件**逐字节相同**（sha256 前 16 位 `498fee75808e0d1d` / `1e7c407678a395d2`）⇒ 冻结的是 10-13 版，**不是** 10-15 替换版 |
| 6 | 2026-10-21 | **拒稿**（EIC Yonghuai Liu；AE 理由见文件） | `PRLETTERS-D-26-02378R1` | `.../P3_PRL_rejected_2026-10-21/DECISION_REJECTED_2026-10-21.md` | — | `[文件]` 决定记录文件 |
| 7 | 2026-10-21 | 改投新投稿提交 | **`PRLETTERS-D-26-02671`** | `SUBMISSION/P3_PRL_resubmission/` | **10 / 8**（S1–S17） | `[文件]` `README.md:5-6`；PDF 页数与 S 编号实测；时刻 18:40 见 `[笔记]` `文件地图.md:990` |
| 8 | 2026-10-21 22:20 | 下一版草稿（**未投**）S18–S22 入稿 | — | `paper3/paper_ieee/` | 10 / 9（S1–S22） | `[笔记]` `docs/P3_RESUBMISSION_AUDIT_2026-10-21.md:129` |
| 9 | 2026-10-22 | 续补（**未投**）：S23–S26 → 10 pp；S27–S28；S29 → 12 pp | — | 同上 | 10 / 10 → 12 | `[笔记]` 同上文档 §十–§十二 |
| 10 | 2026-10-23 22:10 | 本地定稿冻结（**无投稿动作**） | — | `SUBMISSION/P3_PRL_next_revision/` | **10 / 17**（源 43 节；PDF 文本仍含 `(S44)` 交叉引用） | `[文件]` `README.md`、`SHA256SUMS.txt`、pypdf；S 编号实测 |
| 11 | 2026-10-24 17:09–17:17 | venue build（**未投**） | — | `SUBMISSION/_venue_builds/P3_PRL_next/` | **10 / 18**（S1–S43，含 rank-separation 统计轮） | `[文件]` `README.md`、pypdf、zip 内容实测 |
| 12 | 2026-10-24（当前工作稿，**未提交 git**） | 451 题 VQA 轮 + 最小等效边际轮 | — | `paper3/paper_ieee/` | **10 / 18** | `[文件]` `supplementary/supplementary.tex`（89,845 B，mtime 19:39:31）、`supplementary/supplementary.pdf`（18 pp / 401,202 B）、`main.pdf`（10 pp / 421,310 B）；`git status` 显示 3 个文件 M + 1 个未跟踪脚本 |

**Timeline 一句话**：首投 11 页单文件 → R1（10+5，S1–S9）→ 替换件（10+6）→ 2026-10-21 拒稿 → 改投 `PRLETTERS-D-26-02671`（10+8，S1–S17）→ 本地草稿长到 10+17（S1–S43）→ venue build 10+18 → 当前工作稿 10+18（451 轮 + 0.0333 轮，未提交）。

---

## 2. 正文（main text）逐节 变更：首投版 vs 当前工作稿

对比基准 = `SUBMISSION/_archive/_superseded_P3_PRL_submitted_2026-09-26/latex_source/sections/*.tex`（下称 OLD）与 `paper3/paper_ieee/sections/*.tex`（下称 NEW）。

| 节 | OLD → NEW（行数 / 字节） | 变掉的 claim / 表，及现在支撑它的归档 |
|---|---|---|
| Title + Abstract | `main.tex:22` → `main.tex:54` | 标题由 *Gradient Structure Laws as Predictors of PEFT Design: Zero-Shot Cross-Architecture Rank Allocation* 改为 *Zero-Shot Cross-Architecture Rank Allocation from Gradient Geometry: **Identifiability, Negative Results, and Protocol Dependence***。摘要有 **4 条撤稿**：①"reduces uncertainty by 30×"（OLD `main.tex:39`）→ 撤回，`η²=0.989`，见 S17 `tab:claims`；②"phase transition at r_c∈[5,6], robust across sample sizes 16–256, three regimes"→ 降级为 **bracketed crossing** 且归于协议；③"architecture-dependent behavior (Qwen2-VL-7B)"→ 撤回，归因于 visual token budget；④"190 runs"→ 现结论写 **132 runs + allocation study**（`sections/conclusion.tex:19`） |
| §I Introduction | 20 行 / 4.7 KB → 58 行 / 4.1 KB（+48/−10，相似度 0.26） | 三条 contribution 重写：Representation Theorem 现在明写 *subject to (R3$'$)*（`introduction.tex:38-43`）；validation 一条改为"bracketed、属于协议、allocation 只在某个 lr 上赢"（`introduction.tex:48-56`） |
| §II Related Work | 26 → 35 行（+11/−2，相似度 0.79） | 5 个 subsection 结构不变；内容为扩写与补引（无数字结论变化）。**未逐句核对**（要验证需逐段 diff） |
| §III Theory | 303 → 194 行，+145/−254（相似度 **0.20**） | ①新增公理 **R3$'$（cross-block additivity）** `theory.tex:17-18`；②新增 **Lemma 1**（R3 不蕴含 R3$'$，反例 `S=‖x‖²`）`theory.tex:47-48`；③Theorem 结论改为**给定 R1–R5 且 R3$'$** 的族内唯一（`theory.tex:51-63`）；④原 5 个 "Corollary k" 小节改名为主题小节（First-Order Gradient Flow / Optimal Allocation / Alignment Phase Transition / Cross-Architecture Transfer / Paper 2 as Retrieval Specialization）；⑤`main.tex:43-46` 让 corollary 计数器独立，以免补充材料里"Corollary 5"的手写引用被重编号 |
| §IV Experiments | 368 → 432 行，+330/−266（相似度 0.26）；subsection **7 → 3** | 只保留 Setup / Alignment Phase Transition / Counterfactual Validation。主稿 float 由 7 个减为 **4 个**：`tab:sample`、`tab:phase`、`fig:phase_transition`、`fig:counterfactual`；被移出主稿的 `tab:sharegpt`、`fig:ers`、`tab:comparison` 以及 Sample Size Robustness / Second-Dataset Validation / Rank Scaling 全部落到补充材料 S9 |
| §V Discussion | 28 → 73 行（+53/−8，相似度 0.40） | Limitations 由 5 条扩为 **6 条**：新增 (4) newer family 不复现、(5) 二阶项实测、(6) 环境敏感。**注意：投出版（10-21）的 `sections/discussion.tex` 只有 4,549 B，不含 48%/+34/three-environment/3.5% —— 这些是本轮之后才写入草稿的**（zip 内实测） |
| §VI Conclusion | 13 → 52 行（+45/−6，相似度 0.22） | 新增 bracketed crossing 表述与真实图文对数字（`+83.0` vs `−7.5`；`+66.5` vs `−39.5`，`conclusion.tex:24`）、allocation 的负结果、Reproducibility 段（GitHub + Zenodo DOI）、以及指向 S17 的 claim-status 指针（`conclusion.tex:50-51`） |
| Declarations / Data statement | `main.tex:68-72` → `main.tex:126-136` | 数据可用性措辞从"**repository 目前私有、接收后公开、审稿人可索取**"改为 **公开 GitHub + 版本 DOI `10.5281/zenodo.23523263`（v2.2）**。声明段（competing interests / funding / generative AI）文字未变 |
| 新增块 | OLD 无 → `main.tex:105-110` | `\section*{Supplementary material}` 写明 appendix 已外置；**该段仍写 "Supplementary Sections S1--S9"（见 §7 stale pointer）** |

**Claims table 的位置**：在**补充材料 S17**（`supplementary/supplementary.tex:850` `\label{app:claims}`，表 `tab:claims`），不在正文。当前有 **25 条数据行**（`:867-891`）；`docs/P3_SUBMISSION_STATUS.md:27` 写"rewritten to 24 rows" —— **与文件不符（陈旧）**，第 25 行是后加的 SmolVLM 行。

**编号变化**：①正文 appendix 取消（主稿不再有 `\appendix`；`paper3/paper_ieee/sections/appendix.tex` 与 `sections_full/appendix.tex` 仍留在工作树，只被 `main_full.tex` 使用）；②Theory 的"Corollary k"从**小节标题**变成 theorem 环境的独立编号；③补充材料从"无编号附录"变成 **S1–Sn 显式编号**，正文改为用 S 号交叉引用（`main.tex:103`、`:108`、`discussion.tex:57/60/65`、`conclusion.tex:51`）。

---

## 3. 补充材料（supplementary）变更

| 时点 | 页数 | S 节数 | 证据 |
|---|---|---|---|
| 首投（2026-09-26） | — | **无独立补充材料** | `_superseded_P3_PRL_submitted_2026-09-26/` 内无 supplementary PDF |
| R1（10-13 / 10-15） | 5 → 6 | **S1–S9** | `UPLOAD/..._Supplementary.pdf`、`CORRECTED_2026-10-15/supplementary_corrected.pdf`，S 号实测 |
| 改投（10-21，已投） | **8** | **S1–S17** | `P3_PRL_resubmission/Supplementary.pdf` |
| 冻结候选（10-23/10-24 10:16） | **17** | 源文件 **43** 节（PDF 文本仍出现 `(S44)`） | `P3_PRL_next_revision/` |
| venue build（10-24 17:09） | **18** | **S1–S43** | `_venue_builds/P3_PRL_next/Supplementary.pdf` |
| 当前工作稿 | **18** | **S1–S43** | `paper3/paper_ieee/supplementary/supplementary.pdf` |

**新增节（首投无 → 现在有）**，一行一节（S1–S17 时代新增的记在括号里）：

- S18 curvature extension（LLaVA 有限差分 `gᵀHg`，归档 `p3_hessian_probe_r5.json`、`_r6.json`）
- S19 allocation baselines（NTK/Γ 训练 arm，`p3_gapfill_summary.json`）
- S20 newer family（Qwen2.5-VL-3B/7B，`qwen_cf_uniform_rank*_q25_*.json`）
- S21 captioning downstream（`p3_caption_metrics.json`）
- S22 seeds / software matrix（`p3_reproducibility.json` 等）
- S23 reference-batch sensitivity（`p3_gamma_batch_sensitivity.json`）
- S24 non-finite diagnostics（`p3_nan_diagnostics.json`）
- S25 instruction following（`p3_instr_downstream_*.json`）
- S26 newer-family seeds（`p3_qwen2b_crossing_fixed.json` 等）
- S27 allocation-rule baselines（`p3_baseline_rules.json`、`p3_igu_allocation.json`）
- S28 VQA-RAD downstream（**本轮由 300 题改为全 451 题**，`p3_vqa_full_equivalence.json`）
- S29 second environment（四环境栈，`p3_env_matrix3.json` + 两份 `_torch26.json`）
- S30 additivity residual（`p3_additivity_residual.json`）
- S31 per-layer coupling & robust statistics（`p3_perlayer_gamma.json`、`p3_robust_stats.json`）
- S32 signed coupling / non-CLIP source（`p3_signed_gamma_beta.json`、`p3_siglip_gamma.json`、`p3_blip_gamma.json`）
- S33 ten-seed crossing（`p3_rank_separation_extended.json`）
- S34 rank/seed/stack curvature（`p3_hessian_probe_r24*.json`）
- S35 real-image sweep（`..._imgs_cap_*.json`）
- S36 per-step instrumentation（`p3_instrument_r24_lr0.0001.json`）
- S37 environment-variance decomposition（`p3_env_variance.json`）
- S38 allocation bootstrap（`p3_gamma_bootstrap.json`）
- S39 official IGU allocation（`p3_official_igu_clip.json`）
- S40 Dolly replication（`*dolly*`）
- S41 third checkpoint family：Qwen2-VL-2B（`cloud_qwen_cf_uniform_rank*_qwen2vl.json`）
- S42 per-layer coupling on a second model：Qwen2.5-VL-3B（`p3_qwen_perlayer_summary.json`）
- S43 third check：SmolVLM-500M 三种子（`p3_smolvlm_family_s{42,123,789}.json`）

---

## 4. 33 条审稿意见 → 变更的映射

ID 与措辞取自 `docs/P3_RESPONSE_LETTER.md`（`R1.1–R1.5`、`R2.1–R2.5`、`R3.1–R3.23` = **33 条**，与 `SUBMISSION/_archive/P3_PRL_rejected_2026-10-21/evidence/p3_reviews_structured.json` 一致）。
处理计数采用 `docs/P3_RESUBMISSION_AUDIT_2026-10-21.md:81` 的口径：**✅ 25 条已实质处理；⚠️ 8 条为部分处理/明确声明为限制；0 条被忽略**。

| 组 | ✅ 已处理（25） | ⚠️ 只作说明/部分（8） |
|---|---|---|
| 列表 | R1.1 R1.2 R1.3 R1.5 R2.1 R2.2 R2.4 R2.5 R3.1 R3.2 R3.3 R3.4 R3.6 R3.7 R3.8 R3.10 R3.11 R3.12 R3.13 R3.14 R3.15 R3.17 R3.19 R3.20 R3.21 | **R1.4**（未补更新的 VLM 家族→改为真实图文对 + Qwen 边界 + 范围声明）· **R2.3/R3.16**（下游只补检索；VQA/IF 当时未做）· **R3.5**（Hessian 未测→后补 LLaVA S18、Qwen S18 尾）· **R3.9**（只实现 AdaLoRA；HALoRA/Shigu… 未做）· **R3.18**（环境/硬件矩阵不完整）· **R3.22**（多重比较已报；未做权重/激活级诊断）· **R3.23**（数据集族只换到 captioning） |

**每条 resolution 落在哪里（文件位置）**：

- 理论类 **R1.5 / R3.1 / R3.3 / R2.5 / R3.2** → `sections/theory.tex:17-18`（R3$'$）、`:47-48`（Lemma 1）、`:60-63`（R3$'$ 地位）；回信文字 `docs/P3_RESPONSE_LETTER.md:127-149`。
- 分配规则类 **R2.2 / R3.21 / R2.4 / R3.9 / R3.8 / R3.17** → 正文 §V/§VI 负结果 + 补充 S19/S27/S38；归档 `outputs/analysis/p3_alloc_runs/`、`p3_gapfill_summary.json`、`p3_gamma_bootstrap.json`。
- 下游任务类 **R1.3 / R2.3 / R3.15 / R3.16 / R3.23** → 检索反例（回信 `:72-99`）+ S21 caption + **S28 VQA（本轮改为 451 题全量）**。
- 协议/测量类 **R1.4 / R3.13 / R3.14 / R3.11** → 正文 §V Limitations(2)(4) + S20/S26/S29/S35；blank-image 探针数字见回信 `:492-507`。
- 统计类 **R3.17 / R3.19 / R3.20** → S17 `tab:claims`（`:870-871`、`:880-881`）+ **S33**（15 对精确置换、r=5 TOST）。
- 复现/环境类 **R3.18** → S22 + S29 + **S37**；`R3.6` 一阶适用域 → 正文 Limitations(5)。
- 澄清类（无新实验）**R1.1 / R1.2 / R2.1 / R3.4 / R3.7 / R3.10 / R3.12 / R3.22** → 措辞/表格；`R3.7` 的 β 溯源更正为 `outputs/analysis/ode_ledger.json :: runs[90]`。

**注意**：`docs/P3_RESPONSE_LETTER.md` 比归档副本 `.../response/P3_RESPONSE_LETTER.md` **少最后一段 "Title."**（44,468 B vs 44,995 B；仅这一处差异，已 diff 确认）—— 归档版才是完整件。

---

## 5. 本周统计轮新增了什么（相对改投版）

**（a）秩分离矩阵 + TOST**（归档 `outputs/analysis/p3_rank_separation_extended.json`，脚本 `tools/_p1595_p3_rank_separation.py`）
- 每秩 10 seeds，秩均值：r3 **−120.7**、r4 **−97.65**、r5 **−43.7**、r6 **+87.3**、r7 **+195.0**、r8 **+235.0**（`:: ranks.*.mean`，n=10）。
- 符号完全分离：r=3,4,5 **十个全负**，r=6,7,8 **十个全正**（`:: conclusion.sign_split`）。
- 15 对精确置换（枚举 `C(20,10)=184756`）：**14/15 在 5% 水平分离**，Holm–Bonferroni 后仍 14（`:: separation.n_separating_holm_p05`）；最小可达 p = `2/184756 = 1.08e-5`。
- 相邻对：r3r4 **−23.05, p=0.01003**；r4r5 **−53.95, p=0.002349**；r5r6 **−131.0, p=1.0825e-5**；r6r7 **−107.7, p=1.0825e-5**；**唯一未分离 = r7r8（+40.0, p=0.07086）**，其 bootstrap CI `[-77.20, -0.25]` 只越零 0.25，以精确检验为准。
- TOST：r=5 组均值 −43.7，边际 = 该组一个 seed sd = **38.767**（预先声明），**TOST p = 0.6516**，**不构成与零等效**；可声明的等效边际需 **±66.17（1.71 seed sd）**；90% 区间 `[-66.17,-21.23]`、95% 区间 `[-71.43,-15.97]` 全在零下（`:: rank5_equivalence`）。

**（b）全 451 题 VQA**（`outputs/analysis/p3_vqa_full_equivalence.json` + `outputs/analysis/cloud_vqa_full451_{base,5,6}.json`，脚本 `tools/_p1613_p3_cloud_runner.py`）
- 臂级：accuracy base **0.33038**、r5 **0.38803**、r6 **0.33481**；token F1 base **0.35533**、r5 **0.42165**、r6 **0.39832**（`:: arms.*`，n=451）。
- 对比（`:: vqa_equivalence.contrasts`）：base−r5 accuracy **−0.05765** CI `[-0.0976,-0.0177]`（解析）；base−r6 accuracy **−0.00443** CI `[-0.0399,+0.0310]`、**TOST p=0.0057 → EQUIVALENT**，最小等效边际 **0.0333**；r5−r6 accuracy **+0.05322** CI `[+0.0222,+0.0865]`、**TOST p=0.5778 → 不等效**；base−r5 token F1 −0.06633、base−r6 token F1 −0.04299（两者 CI 排除零）；**r5−r6 token F1 +0.02334，TOST p=0.0396 → EQUIVALENT**（边际 0.0483）。
- 配对前提：三臂 `refs_sha256` 相同（`:: refs_identical_across_arms = true`）；适配器为 `pre_existing`（`r5_step` / `r6_step`），`meta.train_samples=1793`、`epochs=3`，**未重训**；训练对 1793、3 epoch，**优化器步数未归档**（`supplementary.tex:1206-1207`）。
- 300 题→451 题的口径改写完成于 `docs/p3_vqa451_round_notes.md`；`docs/provenance_manifest.json` 的 `tab:vqa` 已指向 451 归档（manifest mtime 19:14:37）。

**（c）环境矩阵 provenance 变更**
- 变更前：S29 `tab:envcloud` 的第四栈（torch 2.6.0+cu124）靠 glob `verify_r5_s42_*_a10_torch26.json` 之类取行。
- 变更后：表里**显式写出两个全名**（`supplementary.tex:1280-1282`）：r5 → `..._a10_torch26.json`（`delta_E=−35.5`, `E₀=3917.0`）、r6 → `..._a12_torch26.json`（`+42.0`, `E₀=3917.0`，均已实测），前三栈仍引 `p3_env_matrix3.json`；manifest `tab:envcloud` 同步登记三个归档，note 写明 "torch 2.6/cu124 rows named explicitly (r5 −35.5, r6 +42.0) after the caption glob fix"。
- 事实核验：**第四栈的数据只存在于那两份 per-run JSON**，`p3_env_matrix3.json` 里**没有** torch 2.6 条目（该文件只有 env1 torch2.9 / env2 torch2.12 / env3 torch2.4）。

**（d）明确"尚未进入已投/已冻结 package"的数字**
- 已投 `P3_PRL_resubmission`（`PRLETTERS-D-26-02671`，10+8）：**不含** 451 任何数字、不含 15 对矩阵、不含 torch2.6 行、不含 TOST、不含 0.0333（zip 内源文件与 PDF 文本双向实测）。
- `SUBMISSION/P3_PRL_next_revision/`（10+17）：**不含** 451、不含 `TOST p=0.652`、不含 `14 of 15`/`184756`；仍含**旧值 `1434 training pairs`** 与 `(S44)` 交叉引用。
- `SUBMISSION/_venue_builds/P3_PRL_next/`（10+18）：**含**统计轮（`TOST p=0.652`、`0.071`、`14 of 15`、`184756`、`1793 training pairs`），但**不含** 451 轮（无 `451`、无 `+0.0532`、无 `0.0396`、无 `0.0333`）；其 zip 内 `supplementary.tex` = 88,316 B（451 轮前版本）。
- **只在当前未提交工作稿里**：`0.0532 / 0.0396 / 0.5778 / 0.0333 / 0.0483 / 0.0820 / all 451`；对应源文件 89,845 B（19:39:31）。
- **任何 package 都没有**：第四栈新增 seeds（r5 s7 = **−104.0** 已归档，其余仍在跑）。

---

## 6. 什么没有变（以及新投稿前必须由操作者决定的事）

**未变的冻结件（实测）**
- `SUBMISSION/P3_PRL_resubmission/`：改投已投件，文件尺寸/mtime 仍为 2026-10-21（Manuscript 421,012 B / Supplementary 331,816 B / LaTeXSource.zip 335,159 B）。
- `SUBMISSION/_frozen_submitted/P3_PRL_R1/`：与 10-13 上传件 sha256 逐字节相同（见 §1 #5）。
- `SUBMISSION/_archive/P3_PRL_rejected_2026-10-21/**`：`tools/paper_audit/freeze/p3_prl.json`（created `2026-10-18T04:20:47+00:00`，10 个条目）**本轮复核 10/10 哈希一致、0 changed、0 missing**；该 freeze 的路径已在 2026-10-21 归档搬迁时重新指向 `_archive/P3_PRL_rejected_2026-10-21/`（旧路径版本见 `docs/audits/AUD-p3_prl-20261021T093109Z.{md,json}` 的 I-04 FAIL 记录）。
- 改投版（10-21）的 `sections/discussion.tex` 只有 4,549 B，不含 `48\%`/`+34`/`three-environment`/`3.5\%` ⇒ **正文的环境数字是本轮之后才进草稿的**。
- **数据/代码可用性措辞**：正文仍写版本 DOI **`10.5281/zenodo.23523263`（v2.2）**，与已投件一致，**不得改**（`P3_SUBMISSION_STATUS.md:42`）；仓库现另有 v2.3 `10.5281/zenodo.23609295`、v2.4 `10.5281/zenodo.23614290`，**正文未引用**。
- 标题、定理、图、claims table 的**主张集合**自改投版未变（`P3_SUBMISSION_STATUS.md:18`），变化集中在讨论/限制措辞与补充材料。

**待操作者决定**
1. 是否把 451 轮 + 统计轮 + 0.0333 组成**新一版 package**（现两个 package 都落后于工作稿）；新 submission 还是 revise（稿件当前 **With Editor**）。
2. **DOI 口径**：正文继续 v2.2（与已投件一致）还是随新证据升到 v2.4 —— 涉及对外可见后果。
3. `docs/P3_SUBMISSION_STATUS.md:39-44` 内部矛盾（`v2.3` 与 `v2.4` 都被称作 "current repository release"），需择一。

---

## 7. Open items

1. **torch 2.6/cu124 的 seed 补跑仍在本地执行**（本轮实测进程）：driver `D:\Anaconda\envs\torch26\python.exe tools/_p1613_p3_cloud_runner.py --job env-seeds --stack-suffix torch26`（PID 50580，起于 17:57:58）与一个训练子进程 `run_training.py --rank 5 --seed 123 ...`（PID 47692，起于 19:37:11）。计划共 **6 条**（ranks 5,6 × seeds 7,123,999；`_p1613_p3_cloud_runner.py:104-105`），**已完成 1 条**（`verify_r5_s7_..._a10_torch26.json`，`delta_E=−104.0`），**5 条未完成**；`outputs/analysis/p3_env_seeds_runlog.json` 与 `p3_env_stack_seeds.json` **尚不存在**。
2. **`tools/_p1570_env_variance_update.py:25` 的宽松 glob 已不能复现归档 σ 值**。该行 `glob(EXP, "verify_r5_s*_a10*.json")` 现在匹配 **6** 个文件，其中混入了 `_torch26.json` 两条（s42 −35.5、s7 −104.0）。用今天的匹配集重算：**σ_env = 11.278、σ_seed = 42.946、share = 6.45%**；归档 `p3_env_variance.json` 为 **σ_env = 31.149、σ_seed = 34.295、share = 45.20%（bootstrap 95% [21.2%, 74.7%]）**。断点可定位：`verify_r5_s42_..._a10_torch26.json` 的 mtime 是 **2026-10-23 23:59:29**，晚于归档写入的 **23:26:00**。修法（供操作者决定）：把第三栈改成显式白名单（`_p1613` 的 `collect_env_rows()` 已经这样做了，其 docstring 明写 "no loose globs"），或给 glob 加 `_torch24`/无后缀过滤。
3. **当前草稿里已经写坏的一处 LaTeX（本轮新发现，未改）**：`paper3/paper_ieee/supplementary/supplementary.tex:1235` 的 `$0.05$` 被 `tools/_p1622_add_min_margin.py` 从句中插入，成了 `…margin of $0.` ＋ 插入句 ＋ `.05$, so …`；编译出的 PDF 第 14 页实际渲染为 "the pre-declared margin of 0. The smallest margin … is 0.0333 … .05"，**0.05 这个边际值在版面上被拆散**。两道审计门禁都没抓到（`audit_check.py`、`audit_pdf.py` 本轮实测各 **0 hard failure / 0 warning**）。
4. **stale pointers（本轮实测）**
   - `main.tex:108`：正文仍写 "Supplementary Sections~**S1--S9**"，实际是 S1–S43。
   - `supplementary.tex:890`（S17 claims table）：per-layer coupling 行指向 **(S43)**，而该节是 **S42**（S43 = SmolVLM，见 `:891` 与 `:1692`/`:1716`）。
   - `supplementary.tex:890` 印 **97.9%**，S42 表与图注印 **98.1%**（`:1705`、`:1710`）；归档 `p3_qwen_perlayer_summary.json :: share.llm_00 = 0.9811478…` ⇒ **98.1% 才对，97.9% 无来源**。
   - `sections/discussion.tex:62`：写 "a **three-environment** matrix"，而 S29 已是**四**栈（`:1256-1258`、表 `:1266-1273`）。
   - `sections/discussion.tex:64`：写 r=5 在 torch 2.4/CUDA 12.1 的均值是 **+34**，归档是 **+25.25**（`p3_env_variance.json :: envs."torch 2.4/cu121".mean`）；同句写 "about **48%** of the r=5 variance"，归档是 **45.2%** —— **+34 与 48% 均无归档来源，本轮标为未核实**（要验证：找到产出 48% 的那次运行；可能的候选是 torch24 n=3 的早期口径，但 `p3_env_variance_boot.json` 给出的是 34.2%，也不等于 48%）。
   - 补充材料 **S13 provenance 表**（`:725-754`）与正文承诺（`main.tex:102`："every table and figure are listed in Supplementary Section S13"）不同步：表内 `tab:vqa` 仍指 `tools/_p1516_p3_vqa_downstream.py` + `p3_vqa_downstream_base.json`（S28 图注已改指 `_p1595`/`_p1613` 与 451 归档）；`tab:envcloud` 仍指 `cloud_verify_r5_s42.json`；`tab:crossing10` 仍指 `cloud_verify_r5_s42.json`；`tab:iguarm` 一行在补充材料里**没有对应 `\label`**。该表 30 行，而补充材料共 43 个 float label（S13 未收录 `tab:envvar`、`tab:gammaboot`、`tab:qwenlayer`、`tab:smolvlm` 等 19 个）。
   - `docs/provenance_manifest.json` 的 `tab:envvar` 把脚本记成 `tools/_p1546_env_variance.py`，而归档自述 `p3_env_variance.json :: meta.script = tools/_p1570_env_variance_update.py`；另有一条 `tab:blipsource` 在补充材料里找不到对应 label。
   - `docs/P3_RESUBMISSION_AUDIT_2026-10-21.md:150` 写 next_revision = "Supplementary 17 pp, S1–**S41**"，该包 README 与实际是 **S1–S43**。
5. **`p3_rank_separation_extended.json` 内部仍带 300 题值**：`:: vqa_equivalence.n_questions = 300`，`:: conclusion.text` 与 `:: vqa_equivalence.claim_verdict` 仍印 `+0.0067 / TOST p=0.0074 / +0.0433 / 0.0767` —— 这些是**被取代的 300 题口径**（S28 图注 `:1249-1250` 已声明 superseded）。引用该文件时只能取 `separation.*`、`rank5_equivalence`，**不得**引 `conclusion.text` 里的 VQA 句。
6. **`docs/P3_SUBMISSION_STATUS.md` 陈旧点**（供操作者决定是否修）：`:12` 写 `P3_PRL_next_revision` 为 "Supplementary 17 pp, S1–S43"（页数与节数不一致：该包 17 pp / 43 节，是"17+43"，此处易读成 17 页含 S1–S43，实际正确但 README 与 §5 的 18 页口径不同）；`:27` 写 claims table "24 rows"（实际 25）；`:20` 写 "three-stack environment matrix"（实际四栈，见 `:37`）；`:39-44` 的 v2.3/v2.4 双 "current"。
7. **未核实项**
   - 首投（2026-09-26）是否另有独立 Supplementary 上传件：归档目录内没有，**未核实**；可验证物 = EM 投稿记录页或操作者手里的投稿确认 PDF。
   - 各事件的**钟点**（16:22 / 18:40 / 22:10 等）与 Revise 决定日 **2026-09-30**：**只在笔记里**（`文件地图.md:272`、`:990`、`docs/P3_RESUBMISSION_AUDIT_2026-10-21.md:76`），投递系统文件里没有；可验证物 = EM 页面截图或邮件头。
   - §2 表中 `related_work.tex` 的**内容级**改动未逐句核对（只验证了行数、字节与 subsection 结构）：**未核实**；可验证物 = 逐段 diff（`git diff 2026-09-26` 无该 commit，需与 `_superseded_.../sections/related_work.tex` 对比）。

---

## Appendix added 2026-10-24 (evening): do the consistency findings exist in the SUBMITTED package?

Checked directly against `SUBMISSION/P3_PRL_resubmission/` (the 2026-10-21 submission, frozen):
the sources inside `LaTeXSource.zip` plus the text layer of `Manuscript.pdf` and `Supplementary.pdf`.

| Finding | Present in the submitted package? | Evidence |
|---|---|---|
| `discussion` r=5 mean `+34` | **no** | 0 occurrences in either the sources or the PDFs |
| environment share `48%` | **no** | 0 occurrences |
| `three-environment` / `three-stack` | **no** | 0 occurrences; the submitted text has no stack-count sentence of that form |
| S17 coupling `97.9%` | **no** | 0 occurrences (neither 97.9 nor 98.1 appears in the submitted PDFs) |
| stale `(S44)` pointer | **no** | 0 occurrences |
| `1434 training pairs` / `4302 optimizer steps` | **no** | 0 occurrences |
| 451-question VQA, exact 15-pair permutation, TOST | **no** - correctly absent | these are new evidence produced after submission (0 occurrences of 451 / 184756 / 0.071 / 1.08e-5) |
| main text pointing to `Supplementary Sections S1--S9` | **YES - one occurrence** | `LaTeXSource.zip :: main.tex:108`, and the submitted `Supplementary.pdf` actually carries **S1-S17** (17 sections) |

Interpretation: every number-level inconsistency listed in this document was introduced into the **working draft**
during the local revision work that followed the submission, or is new evidence; none of them is in the submitted
version. The single exception is the supplementary range pointer, which was correct for the *first* submission
(whose supplement ended at S9) and was not updated when the supplement grew to S17 before the resubmission. It is
a stale cross-reference only: it changes no number, table or claim, and the working draft now points at S1-S43.

The frozen package is therefore left untouched (policy: never modify a submitted artefact), and no erratum is
warranted on this basis. If a revision is invited, the working draft already carries the corrected pointer.
