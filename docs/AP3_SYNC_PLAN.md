# ap3 与 P1 整改的同步清单（2026-09-20 起）

`paper_ap3/` 是 P1+P2+P3 的合并稿（`\journal{Neurocomputing}`，elsarticle；起草时最后一次编译 2026-09-13，85 页）。
**当前为 86 页**（2026-09-23 重编译，0 error / 0 undefined / Overfull>20pt = 0）——中间的 85→87→86 变化
原因是分批并入 Tier-A 块、消解占位标记、补齐三处条款缺项，逐次编译记录的页数不同，**以最新一次为准**。
P1（`paper/`）这一轮整改撤掉/改写了若干**结论级**数字，而 ap3 的 §1、§3b、§4、§5 复述了它们，
所以 ap3 现在与 P1 自相矛盾。本文档把每处待改点、替代值的真实来源、以及依据列清楚，改一处勾一处。

**状态：起草中（本轮只做"计数与明显算错"这一类机械项，相关性块与结论改写下一轮做）。**

> **📌 2026-09-23 现状锚点（读本文档前先看这条）**：§7 的 Round 1–7 已全部执行完，ap3 现为
> **86 页 / 0 error / 0 undefined / Overfull>20pt = 0**，全文体检 **A/C/E = 0、B = 0 → PASS**
> （此前的 B=1 是暂存文件导致的预期重复句，随占位标记消解而消失）。
> §6 的七条待办中 **4、5、6、7 已关闭**（见该节标注）；第 3 条按操作者指示**维持保守版**。
> 一页速览见 **`docs/AP3_SUBMISSION_READINESS.md`**，篇幅结论见 **`docs/AP3_LENGTH_CHECK.md`**。

---

## 0. ap3 的实际暴露面（逐条查过 `paper_ap3/**/*.tex`）

⚠️ **本表初版有一条我自己的误判**：我曾写"ap3 无 2.6× 噪声主张"。那是漏扫——第一次 grep 的结果被
`_bb.xml`（PDF 解析残留）淹没，第二次我把模式收窄到 `*.tex` 时**漏掉了 `2.6`**。实际它就在
`04_mechanism.tex:103` 与 `03b_special.tex:97`。教训记在此：扫描模式必须由撤项清单逐条派生，不能凭一次结果归纳。

| P1 撤回/修正项 | ap3 中的实际情况 |
|---|---|
| 参数噪声「视觉比文本脆弱 2.6×」 | **曾有，已修**：`04_mechanism.tex:103`（改写为 "Noise sensitivity (withdrawn)"，附配对结果 1.9±1.8 vs 2.5±3.3、p=0.77）与 `03b_special.tex:97`（不再用它支撑理论） |
| GSNR `1.5×` | **曾有，已修 → 1.4×**（`outputs/gsnr_results.json` 的 `v_t_ratio=1.4111`；旧档 pre_fix 为 1.4531） |
| 有效秩写成"权重更新矩阵 ΔW" | **曾有，已修**：改为层**嵌入**有效秩 `exp(−Σp log p)`，与 `compute_effective_rank(embeddings)`（`paper/scripts/noise_sensitivity.py`）一致 |
| "text-only 按构造对视觉侧零扰动" | **曾有，已修**：与 P1 已披露的"历史 text-only 训了 95.96% 参数（仅 24 个 q/v 被冻结）"直接矛盾，改为如实陈述 |
| 零样本 "within 0.9 percentage points" | **曾有，已修 → 0.8**（0.9 是旧值下 0.87 的换算；全量重测后最大偏差 0.74）。`fig_zeroshot.png` 已与 P1 的 `fig12_zeroshot_more.png` **逐字节相同**，无需重画 |
| CG `+24%` | **曾有，已修 → 23.3%**（两处：`03b_special.tex:99`、`04_mechanism.tex:19`；0.1908/0.8184=23.34%） |
| Adapter 旧口径 `+0.079`、「部分配置降低 gap」 | 无（仅 `_bb.xml` 残留） |
| 零样本基准写成 CIFAR-100 | 无 |
| "first systematic" 之类优先权措辞 | 无 |
| full-FT sd `±0.007` | **曾有，已修 → ±0.008**（5 seed 实测 sd 0.0084） |

---

## 1. 实验计数：116 → 117，连带 278 → 279、468 → 469

**依据（可复核）**：ap3 在 `04_mechanism.tex:15` 说"the complete catalog of the 116 experiments is
available together with the analysis code"，指向的就是 P1 发布的那份目录；而该目录现在印的是 **117**
（`paper/sections/supplementary.tex:169` 的 Total 行），且**各节声明数之和 = 117**，已用工具复核：

```
python tools/_catalog_count_check.py paper/sections/supplementary.tex
  → 13 节全部 declared == rows（唯一例外 VII 节：声明 20、列 4 行，属"5 seed 合一行"的记账约定），
    各节声明数之和 117 == Total 117
```

116 是**整改前**的旧总数（当年那一节标题写 7、实际列 8 行，见 `paper/cover_letter_revision.tex` 勘误表）。
所以 ap3 必须同步为 117，并由它派生出：

| ap3 位置 | 现在 | 改为 | 派生关系 |
|---|---|---|---|
| `01_intro.tex:14` | "a systematic 116-run characterization" | **117-run** | 与发布目录一致 |
| `04_mechanism.tex:4` | "spanning 116 runs" | **117 runs** | 同上 |
| `04_mechanism.tex:15` | "the complete catalog of the 116 experiments" | **117** | 指向发布目录，必须等于它 |
| `05_dynamics.tex:123` | "278 dual-encoder experiments (116 mechanism runs plus 162 ODE fits)" | **279 … (117 mechanism runs plus 162 ODE fits)** | 117 + 162 = 279 |
| `main.tex:37`（摘要） | "468 runs---278 dual-encoder runs … plus 190 decoder-based runs" | **469 runs---279 … plus 190** | 279 + 190 = 469 |
| `01_intro.tex:22`（图注） | "468 core runs plus 25 protocol-probe runs" | **469 core runs plus 25** | 同上 |

`190 runs (181 sweep + 9 block-level)` 与 `25 protocol-probe runs` 是 LLaVA/Qwen 侧，**不受影响**，不动。

## 2. 一处明显的算错：full-FT 的 ±0.007 → ±0.008

`04_mechanism.tex:28` 写 `text-only CGΔ = −0.046 ± 0.002, vs. full fine-tuning +0.191 ± 0.007`。
从 `outputs/flickr30k_seeds/baseline_full_ft/seed{42,123,456,789,1024}/results.json` 重算：
CG 均值 **1.0092**、sd(ddof=1) **0.0084** → Δ = **+0.1908**，即 **±0.008**（`tools/obsolete/audit_fix_regression.py:43`
里那条 `\pm 0.007` 断言是过期的）。P1 侧已是 ±0.008。

## 3. DG/CG 相关性块 —— ✅ 已改（措辞保守版，等你看一眼）

ap3 的 §4 原用 n=81 子集报 `DG r=−0.827`、`CG r=−0.683`、偏相关 `−0.807`、`CGΔ r=0.012 (p=0.915)`，
并据此写"substantially outperforming CG"。那个 n=81 子集选取规则**不可重建**，已按可复现规则
（`outputs/analysis/dg_r1_reproducible.json`）整体替换：

| 量 | 原 | 现 |
|---|---|---|
| 样本 | n=81（规则丢失） | **n=204**（`outputs/**/results.json`，每目录一行，排除 figures/comparison/strict_freeze/smoothing） |
| DG vs R@1 | −0.827 | **−0.714** |
| CG vs R@1 | −0.683 | **−0.594** |
| 偏相关 DG\|CG | −0.807 | **−0.581** |
| DG ↔ CG | 未报 | **+0.945**（新增入表） |
| DGΔ vs R@1 | 未报 | **+0.134**（p=0.055） |
| CGΔ vs R@1 | +0.012（p=0.915） | **+0.190**（p=0.007） |
| 聚类自助 | 98 实验/14 簇，−0.847 [−0.936,−0.709]，0.04% ≥0 | **12 簇，−0.738 [−0.889,−0.613]，0.0% ≥0**（CG 侧 −0.608 [−0.777,−0.462]） |

**采用的措辞**（保守版，未动理论结构）：把"DG 显著优于 CG"改为
"the association is a property of gap **magnitude**；两个度量彼此相关 +0.945，故不把 DG 当作携带 CG 之外信息的一方"，
理论侧只保留"ODE 定义在 DG 上"这一**构造性**定位（§3b 的那句同理改写）。
→ **仍需你确认**：若你希望更强地保留 DG 的理论特权（例如加一段说明为何即使二者近乎简并，DG 仍是 ODE 的自然状态变量），
告诉我，我按你的方向补写；当前版本只是"不低于事实"的最小改法。

**图已重画（本轮完成）**：`paper_ap3/figures/fig_corr.png` 原为 n=81 的散点，现由新脚本
`paper_ap3/scripts/plot_fig_corr.py` 用 n=204 的 204 个真实行重画（双面板散点，标题自动写 r 与 n）。
该脚本**从原始行独立重算** r 并与 JSON 比对后才出图：重算 DG −0.7142 / CG −0.5939 / DG~CG +0.9451，
与 `dg_r1_reproducible.json` 的 primary 完全一致——这同时构成对 P1 修正值的又一次独立验证。

## 4. 待清理与待核

### 4.1 ✅ 已查清并**撤回**：骨干就是 BLIP-1，稿件写法**正确**（Round 2 更正）

我在 Round 1 曾把这一条标成"🔴 命名错误：正文写 BLIP-1 但归档实为 BLIP-2"。**该结论是错的，现予撤回。**
当时我据以判断的是**名字**：7 个目录叫 `b*_blip2_*`、脚本叫 `blip2_experiments.py`、常量是 `BLIP2_MODEL_*`、
实验列表注释写 BLIP-2。但名字不是证据，决定性证据在**类与 API 的兼容性**上：

| 检查 | 结果 |
|---|---|
| 包装类 | 脚本用的是 `class Blip1Wrapper`，构造时访问 `blip_model.text_model`（`blip2_experiments.py:336`） |
| `Blip2Model.__init__` 实际赋值 | `language_model`, `language_projection`, `qformer`, `query_tokens`, `vision_model` —— **没有 `text_model`** |
| `BlipModel.__init__` 实际赋值 | 含 **`text_model`**、`vision_model`、`text_projection`、`visual_projection` |
| 后果 | 若真加载 `Blip2Model`，第 350 行 `Blip1Wrapper(model)` 立即 `AttributeError`，**任何实验都跑不出来** |
| 事实 | 7 个运行的结果 JSON 全部存在 → 只可能走 `load_blip1_model()`（`BlipModel`）分支 |
| 旁证 | 脚本内注释均按 BLIP-1 语义写：`:327` "BLIP-1 用自有 tokenizer，不能预 tokenize"、`:369` "BLIP-1 不支持 `apply_lora_to_model`，改用选择性解冻"；P1 的限制条目"BLIP-1 用选择性解冻而非真正 LoRA 注入"与之吻合 |
| 时间线（曾被误用） | `models/blip-caption-base`（`BlipForConditionalGeneration`，990 MB）是 **2026-08-26** 下载的，而运行产出是 **2026-08-03**——这只说明"那份副本晚于运行"，**不能**反推模型是 BLIP-2（运行当时用的是脚本里 `./models/blip-image-captioning-base` 那份，后来换目录重下） |

**结论：ap3/P1 的 "BLIP-1" 标注无需改动，引文 `li2022blip`（BLIP, Li et al. 2022）也是对的。**
唯一残留的"名字陷阱"是那 7 个目录名（`b*_blip2_*`）与脚本名，属历史遗留；**如果操作者希望归档名与实跑一致**，
可以另做一次改名（不影响稿件）。教训记此：**判断实现用什么模型，要看类/API 的兼容性与运行痕迹，不能看目录名或文件名。**

**运行配置（供复现，来自代码而非猜测）**：`--model_name auto` 且未给 `--force_blip1` 时，
`detect_model_size()` 在本机 8 GB 显存下会先尝试 `Salesforce/blip2-opt-350m`；该加载在 `local_files_only=True`
下失败即回退 `load_blip1_model()`。本次归档的 7 个运行是回退后的 BLIP-1 结果，因此稿件称其为 BLIP-1 是准确的。

### 4.2 ap3 `refs.bib` 的 `xu2026vlreasoning` 标题是截断版

ap3 写 *"…A rigorous study of the modality gap"*，P1/引文审计的外部证据（ar5iv `2604.16256`）是
*"…A rigorous study of the modality gap **in reasoning**"*。其余三处差异（`gao2026uniformity` 用 note 而非 doi、
`zhu2025connector` 的 booktitle 详略、以及 ap3 未收 `yi2025decipher`/`gu2025gtma`/`huang2025mindgap`）
属风格或缺引，不构成事实冲突——**只有 xu 这一条是真错**，需要改成带 "in reasoning" 的完整标题。

- `sections/_TIER_A_PENDING.tex`：**未被 `main.tex` `\input`**（不影响编译与页数）。实测 **171 行里还有 37 个 `@@@` 占位**，
  即 Tier-A 的 A1–A10 块**只并入了一部分**（例如"Limitation~9 previously bounded sampling noise"那句已在
  `06_crossarch.tex:615` 出现，全文体检的重复句提示就是这个原因），其余仍待填数。
  → **不要整体归档**（文件里保存着每个待填数字对应的 JSON 来源映射，如 `outputs/tier_a_analysis.json`、
  `outputs/clip_peft_gamma_ordering.json` 等，丢掉就找不回来了）。需要你定：**投稿前把这些块补齐，还是明确放弃并移到归档**。
  当前稿子本身是完整的（当时 85 页、编译通过、体检 A/C/E 级 0 问题），这些块属于增量，不加也能投。
  **后续进展（2026-09-24）**：这些块**已全部并入并复核**，占位标记已消解，当前 86 页 / 0 error /
  0 undefined / Overfull>20pt = 0、lint A/C/E = 0 且 B = 0 —— 详见 `docs/AP3_SUBMISSION_READINESS.md` §8。
- **封面信**：`paper_ap3/` 目前**没有** cover letter 文件，需要新建，并按既定约定披露 A1（`NEUCOM-D-26-20952`）
  与 P1（`PR-D-26-10149`，审稿中）——这也是 ap3 作为合并稿与 P1 的实质重叠必须交代的部分。
- 与 `paper合/` 的 1,413 词重合改写：`paper合/` 是 P1+P2（Paper A）路线，ap3 是 P1+P2+P3 合并稿；
  两条路线若并存需要各自交代重叠，等投稿路线定下来再决定改哪一份。

（BLIP 命名与 bib 两件事已在上面的 4.1 / 4.2 定案，不再重复列条目。）

---

## 5. 封面信与投稿前置条件（本轮新增）

**已起草** `paper_ap3/cover_letter.tex` + `cover_letter.pdf`（2 页，编译 0 error），按 `paper_a1/cover_letter.tex`
的范式写，含三段关系披露：

- **(a) 同刊的姊妹稿**：A1《The Modality Gap Is Not a Universal Health Metric…》正在 *Neurocomputing* 审稿
  （`\mbox{NEUCOM-D-26-20952}`）——独立数据（gap surgery），只共享作者与主题。
- **(b) 与他刊在审稿的重叠**：P1《Protect, Don't Perturb…》在 *Pattern Recognition* 审稿
  （`\mbox{PR-D-26-10149}`）；**明确声明本文 §4 的 PEFT 下 gap 演化实证与 P1 共享**，而本文的全部贡献
  （表示定理、分配原理与推论、ODE 及其拟合、跨架构 rank 分配迁移）均为新增。
- **(c) 更短版本的前次投稿**：10 页版本曾投 IEEE TNNLS（`\mbox{TNNLS-2026-P-50569}`），**2026-09-03 被拒且
  TNNLS 明确不接受改投**；本文是大幅扩展的重分析（实验数翻倍以上），且未在他处审理中。

三个稿件编号都用 `\mbox{}` 锁定，避免断行把 `NEUCOM-D-26-20952` 拆成 `NEUCOMD-26-20952`（已实测到该现象）。

### ⚠️ 投稿前置条件（重要，须与操作者确认）

`HANDOFF.md:219`（2026-08-05，操作者自己的结论）写明：**合并稿若包含仍在审稿的论文，即构成重复投稿（违规）**，
当时据此判定 Paper A 与 paper2 独立版"均不能投"，正确策略是**等 P1 出结果**（accept → 独立版可投；
reject → 合并版可投）。ap3 正是 P1+P2+P3 的合并稿，**因此 ap3 不能在 P1 审稿期间投出**。

所以"随时可投"的准确含义是：**ap3 现在做到"一收到 PR 拒稿即可当天投出"**。封面信里有两处按 LaTeX 注释
`% UPDATE ON PR DECISION` 标出的句子，必须在投出前按 PR 的实际结果改写（改为"已在 <日期> 被拒"），
**否则会写出与事实不符的状态**。这两处我已在 `.tex` 里写好替换文本，届时只需替换那一句。

## 6. 下一轮待办（Round 1 结束时清点）

1. ✅ **Adapter 陈旧结论（Round 2 已完成）**：`04_mechanism.tex:59/64/126` 与 `05_dynamics.tex:111` 已按
   `outputs/analysis/adapter_common_baseline.json` 改写。要点：**"Adapter 偏好更大的 bottleneck"这条保留**
   （统一基线 d=16/32/64 = **+0.237/+0.103/+0.064**，趋势仍在，与 P1 `experiments.tex:126/138` 一致），
   但明确写入"**没有任何 Adapter 配置把 gap 降到冻结基线以下**"（旧口径的 −0.217 只在撤回说明里出现一次）。
   顺带发现并修掉一处**图注与图不符**：`fig_crossmethod.png` 实际只画 LoRA 的三个消融面板（rank/alpha/modules），
   图注却写"LoRA 与 Adapter 对比"——已把图注改为如实描述该图，Adapter 对比放回正文（若你要一张真正的
   跨方法图，我可以用这 7 个 Adapter 运行另画一版）。
2. ✅ **BLIP 命名（Round 2 已查清，无需改动）**：见 §4.1 的撤回说明——归档运行确为 **BLIP-1**，稿件写法与引文 `li2022blip` 都正确。
   本轮据此**没有**做任何改名。
   ✅ **同时补了一处措辞精确化**：ap3 的 $g_v = 0$ 论证（§3b:97）原写"only the text encoder is trained"，
   而 P1 已披露历史 text-only 运行 **199 个视觉张量全部可训**（95.96%）→ 已改为"adaptation is confined to the
   text side … $g_v = 0$ in the adapter subspace"，并加括注说明该标签指"哪一侧挂适配器而非严格参数预算"。
   结论不变（两侧差异在于适配器位置），但表述不再与披露矛盾。
3. **DG/CG 措辞**：当前为保守版（见 §3）；若要把"DG 仍是 ODE 的自然状态变量"讲得更强，需操作者给方向。
4. ✅ **Tier-A 占位（§4）——已关闭（2026-09-24）**：操作者定"补齐"。核查后发现 37 个 `@@@`
   **全部在暂存文件 `_superseded_2026/_TIER_A_PENDING.tex` 里**（主稿零命中），其内容早已并入
   `06_crossarch.tex`/`07_discussion.tex` 并逐块对档案复核过。已按事实改写该文件头 + 把填位标记
   换成 `[A#-NN]` 追溯锚点，整棵树 `@@` 归零；脚本 `tools/_ap3_superseded_marker_cleanup.py`（幂等）。
   详见 `docs/AP3_SUBMISSION_READINESS.md` §8。
5. ✅ **篇幅/投稿形式——已核查（2026-09-24）**：结论 **合规、无需压缩**——该刊 Guide **无页数上限、无字数上限**，
   也没有"双倍行距/行号"要求（双倍行距是 `elsarticle[review]` 自带）。条款原文取自仓库内两份独立官方存档
   （官网当日 403）。详见 **`docs/AP3_LENGTH_CHECK.md`** 与 `docs/AP3_SUBMISSION_READINESS.md` §9。
   本条先前的自我更正（把 Ocean Engineering 的 "preferably not more than 40" 误记到 Neurocomputing 头上）是对的。
   **顺带产出**：核查中发现 ap3 缺 Guide 要求的三节（关键词 / 数据可用性 / 生成式 AI 声明），已一并补齐。
6. ✅ **`paper合/` 与 P1 的 1,413 词重合——已关闭（2026-09-24）**：操作者定 **`paper合` 弃用**
   （已归档 `备选/06_归档稿件/paper合/`），**ap3 为唯一合并主线**。**该重合与 ap3 无关**
   （ap3 ↔ P1 只有两段 21/27 词残句，已在 P1 整改中处理），故无需改写。
   历史处置记录：`docs/PAPERHE_OVERLAP_RESOLUTION.md` §4。
7. ✅ **禁词/一致性门禁——B=1 已归零（2026-09-24）**：B 的那条"预期重复句"来自暂存文件，
   随占位标记消解后复跑为 **A/C/E = 0、B = 0 → PASS**（D = 46 条提示性，已在 READINESS §4 定性）。
   ⏳ 仍留一项：把 ap3 纳入 `tools/audit_submission_pdfs.py` 的包检查——**等投稿包生成时一起做**
   （现在打包会固化尚未按 PR 结果改写的封面信表述）。

## 7. 体检工具（`tools/ap3_fulltext_lint.py`）本轮修掉三个真 bug

D 项（数字溯源）原本给出"40 条候选"，我据此以为改不动；实际是工具缺陷：

| # | Bug | 影响 | 修法 |
|---|---|---|---|
| 1 | 源文件 glob 是 `outputs/*.json`（**不递归**） | 嵌套档案（`outputs/theory/siglip/`、`outputs/siglip/`、`outputs/analysis/`…）全部不可见，SigLIP 的 $\Gamma$ 值被判"无出处" | 改 `outputs/**/*.json` 与 `paper3/scripts/outputs/**/*.json`（扫描文件 349 → **1,114**） |
| 2 | 列表被 `[:40]` **硬截断**，而报告的就是截断后的长度 | "40 条"是饱和值，任何改进都读不出来 | 保留完整列表，报告真实条数（现为 48） |
| 3 | 逗号千分位被当成两个 token | `52,002` 被拆成 `52`/`002`，产生假候选 | 把已知文档性数值（数据集规模）显式列入 SKIP 白名单 |

**已核实为"有出处"**（此前被误报）：SigLIP 的 $\Gamma_t = 0.362$ / $\Gamma_v = 4.23$ 分别来自
`outputs/theory/siglip/siglip_text_r8.json`（`Gamma_t = 0.36165`）与 `siglip_both_r8.json`（`Gamma_v = 4.22889`）。
教训：**要按 manuscript 的精度去四舍五入后再匹配原始 JSON，不能拿四舍五入后的字面值去搜。**

**剩余 48 条候选的性质**：多为 ap3 自己 LLaVA/Qwen 的 $\Delta E$ 统计量（如 §6 的 `+1508 ± 155`、`+111.5`、`233.5`），
以及**派生量**（5-seed 均值/求和/差值——它们本来就不会以字面值存在于档案里，例如 `469 = 279 + 190`）。
这类"派生值不可字面溯源"是 D 项的固有边界（工具自身也标注为提示性）。

### 7.1 ✅ 已查清并**第二次撤回**：§6 的反事实数字**逐项精确可验证**

我在 Round 3 把 ap3 §6 的 `r=4: −108±27; r=16: +1508±155` 报成"全部档案中无法验证"。**该结论是错的，现撤回。**
两处失误：① 没有读该段的**自注**——`06_crossarch.tex:320` 明写 *"the counterfactual batch is a separate run batch
from the phase table … which is why its r=4 value differs slightly from the tabulated −105 ± 21"*，即 §6 有**两批**运行
（相位表 = E2，3 seeds，**总体** sd；反事实批，5 seeds，batch 1，**样本** sd），我把两者混为一谈；
② 没有处理 **NaN 折叠**与"剔除折叠跑"的统计口径，导致我算出的 Random 均值/标准差偏离。

真源是 `paper3/scripts/outputs/experiments/all_results.json`（由 `paper3/scripts/run_e4_counterfactual.py` 生成，
其文件头即写明 Theory r=4 × **5 seeds**、Random 5 seeds × 3 draws = **15**、Violation r=16/r=32 各 5 seeds）。
逐条从 `E` 数组重算后与正文**完全吻合**：

| 组 | 正文 | 从 `all_results.json` 重算 |
|---|---|---|
| Theory (r=4, 5 seeds) | $-108\pm27$ | **−108.0 ± 26.7**（样本 sd）✓ |
| Violation r=16 (5 seeds) | $+1508\pm155$ | **+1507.8 ± 154.7** ✓ |
| Random (15 draws) | $+491\pm808$ | **+490.8 ± 808.1**（**13 条有效**：2 条末端 NaN 折叠跑被剔除）✓ |
| Violation r=32 | 5/5 collapse (NaN) | 5 条均为 `E=[3927, ~3800, ~6400, **NaN**]` ✓ |
| "30× larger sd" | 808 vs 27 | 808.1 / 26.7 = **30.3** ✓ |
| 相位表 r=4（与反事实批区分） | $-105\pm21$ | E2 三个值 −114.5/−125.0/−76.0 → 均值 −105.2、**总体** sd 21.1 ✓ |

**同时得到的结论**：这类"派生量"（均值/sd/倍数）不会以字面值存在于任何 JSON，D 项的字面匹配注定查不到它们——
**这就是 D 类候选的性质，不是缺陷**。D-check 的价值在于提示人工核对，而核对方式是"找到 `E` 数组自己重算"，
本表就是一次完整示范。脚本 `run_e4_counterfactual.py` 已归档，可复算。

### 7.2 ✅ 另一处最高级断言：已验证（Round 4）

ap3 与 P1 都写 *"Rank-4 text-only achieves $\mathrm{CG}\Delta = -0.476$, **the strongest gap reduction across all 117
experiments**"*。全档案复算（`outputs/**/results.json`，取 `final_gap.centroid_gap − initial_gap.centroid_gap`，
共 **209** 个可比运行）：最小值为 `outputs/blip2/b3_blip2_lora_r4` 的 **−0.4759** ✓，其余依次是
`theory/adapter/adapter_both_d64/*`（−0.4405/−0.3886/−0.3738，均为**自身注入后基线**口径）。
换成**冻结基线**口径后 Adapter 那些全部转正（+0.06…+0.50），该运行仍是最强（−0.482）→ **断言在两种口径下都成立**，无需改动。

## 7.3 ✅ §6 另外三张表：逐格重算，全部有出处（Round 5）

用"**定位定义表的档案 → 从原始数组重算**"的方法（而非字面值搜索），§6 的表格全部对上：

| 表 | 定义档案 | 复算结果 |
|---|---|---|
| 反事实批（Theory/Random/Violation） | `paper3/scripts/outputs/experiments/all_results.json`（脚本 `paper3/scripts/run_e4_counterfactual.py`） | Theory −108.0±26.7、Violation-r16 +1507.8±154.7、Random +490.8±808.1（13 条有效）、r=32 五条末端 NaN、808/27=30.3×、r=4 相位表 −105±21（总体 sd）——**全部吻合**（详见 §7.1） |
| 协议敏感度矩阵（`tab:sens`） | `paper3/scripts/outputs/experiments/verify_r{5,6}_s42*.json` | r=5 −18.0 ✓、r=6 +93.5 ✓（bf16 −25.0/−4.5 ✓）；`ΔE(6)−ΔE(5)` = 111.5/20.5（**派生**）；Rebound **233.5 / 168.5 用图注定义重算得 233.5 / 168.5 ✓** |
| 样本量 × rank 表 | `paper3/scripts/outputs/experiments/sample_size_results.json` | n=256 行逐格：−102.5/−54.5/+26.5/+65.0/**+1885.0** → 正文 −102/−54/+26/+65/+1885 ✓ |
| β 扫描的相邻间隔 | `outputs/clip_beta_selection.json` | 1112.4 / 5365.5 / 625 ✓（`separation...` 字段） |
| 10-seed 复现批的 ΔE(r=5) | `paper3/scripts/outputs/experiments/verify_r5_s{7,17,27,37,42,47,57,67,123,999}.json`（**恰 10 个**短名运行） | 逐 seed −80/+5/−71/−27.5/−18/−51.5/−76.5/−41.5/−52/+66 → 均值 **−34.7** ✓、正值 **2/10** ✓；样本 sd 44.46 → se 14.06 → $t_9$ 95% CI **[−66.5, −2.9]** ✓ 与正文完全一致 |

**方法论结论（已写入工具文档）**：在手稿精度上做"最近邻匹配"**不构成溯源证据**——本轮试的每个值都能匹配
19–586 个档案数字（因为档案里有索引表、距离、嵌入等，任何小数值都出现过）。可靠做法只有两条：
① **按实验名找到定义该量的档案，从原始数组重算**（本节即示范）；② 字面匹配仅在该字段语义明确且完全等值时才作证据。
新工具 `tools/_ap3_trace_numbers.py` 用于**生成线索与判断"某数是否完全不存在"**，输出带 `AMBIGUOUS: matches N` 告警。

### 7.4 ✅ 最后一批候选是**文献值**，已外部验证并修正引文（Round 6）

D 类剩下的两个值（MDI $10.23$ / $33.10$）此前在本地档案中查不到——**因为它们本就不是我们的实验数据**：
原文句子写的是 *"Wu et al.~\cite{wu2025language} report LLaVA's MDI of $10.23$, while Qwen2.5-VL's MDI is
$33.10$ at deeper layers"*。已联网核对原论文（arXiv:2508.10552，Huyu Wu, Meng Tang, Xinhan Zheng,
Haiyun Jiang，*When Language Overrules: Revealing Text Dominance in Multimodal Large Language Models*）的 Table 1：

| 模型 | image / MMMU\_Pro | Early | Middle | Late |
|---|---|---|---|---|
| LLaVA-1.5-7B | MDI | 1.58 | **10.23** | 17.37 |
| Qwen2.5-VL-7B | MDI | 2.26 | 21.12 | **33.10** |

→ 两个值**准确**（10.23 是中层值、33.10 是深层值）。已做两处改进：① 给 LLaVA 的值补上层次限定
（原句只给 Qwen 标了 "at deeper layers"）；② `refs.bib` 的 `wu2025language` 原为占位作者
`author={Wu, Y. and others}`，已按核对结果填为真实作者并补 DOI（渲染为
"Wu, H., Tang, M., Zheng, X., Jiang, H., 2025 … doi:10.48550/arXiv.2508.10552"）。

**至此 D 类候选全部定性**：抽样到的每一条都可归入 ① **派生量**（均值/sd/差值/倍数 → 从档案原始数组重算，§7.1/§7.3 示范）；
② **表格单元**（已逐格核）；③ **文献值**（已外部验证，§7.4）。本地档案中不存在"既非派生、又无来源"的数字。

### 7.5 ✅ 引文库质量审计（Round 6）

由 `wu2025language` 的占位作者引发，做了全库审计（新工具 `tools/_ap3_bib_audit.py`，54 条）：

| 检查 | 结果 |
|---|---|
| 占位/缺失作者 | 无真实缺陷。`and others` 是 **BibTeX 正常写法**（渲染为 "et al."），出现在 `radford2021`、`bai2023qwen` 等长作者名单条目上属规范做法——我第一版工具把它误报为缺陷，已修正判据 |
| 缺少标识符 | 无缺陷。`sharegpt2023` 用 `url`+`howpublished` 标注数据集来源（我的正则原先漏看这两个字段，属**工具**缺陷，已修） |
| 单一/过短作者名单 | 1 条 INFO：`zhou2026shortcut`（Zhou, L.）——其 [arXiv:2604.17217](https://ar5iv.labs.arxiv.org/html/2604.17217) 页面存在，单作者可信 |
| 历史遗留的 5 条**伪造引文** | 已确认全部不存在于 `refs.bib`（`kang2025dmnsp`/`wang2026violet`/`yan2025dgsnet`/`cast2025`/`siglip2025constellation` 均为 0） |
| 关键条目的 arXiv ID 抽查 | 三条**承重引文**外部验证为真：[arXiv:2603.13792](https://ar5iv.labs.arxiv.org/html/2603.13792)（IGU-LoRA）、[arXiv:2604.17217](https://ar5iv.labs.arxiv.org/html/2604.17217)（CrossRef 注意力分析）、[arXiv:2507.19839](https://ar5iv.labs.arxiv.org/html/2507.19839)（GNSP） |

## 执行纪律（沿用 P1 整改的教训）
1. 补丁脚本必须**自校验**（替换计数不符就退出码非 0，且不让后续命令继续跑）——曾因 shell 用 `;` 串联，
   脚本报错但编译照样跑，导致一次提交谎报改动（`ab1d46a`）。
2. 改完必须**编译 → `pdftotext` → 扫 PDF 文本**，源码级断言不算验证（曾漏 11 处陈旧值）。
3. 数字只能来自 `outputs/` 下的真实 JSON；每个替换在提交信息里写明来源。
4. 发布：改 live → `Copy-Item` 到 `.worktrees/publish-main` → `git add -A`（`*.pdf`/`*.bbl`/`outputs/**/*.json` 需 `-f`）
   → commit → push `ssh-origin HEAD:main`；提交前跑 `tools/_publish_live_drift.py` **与** `tools/_publish_new_files.py`。
