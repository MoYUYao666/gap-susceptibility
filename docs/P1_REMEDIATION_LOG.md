# P1 整改执行记录（2026-09-18 起）

> 目标：`docs/P1_ADVERSARIAL_REVIEW.md` §7 全部执行完 → 重编译 → 第二轮独立复查。
> 本文件记录**实际改了什么、用什么证据、哪些代理结论被否掉**，避免后续轮次重复劳动或修错方向。

## 一、实验：严格冻结对照（A 方案）

**动机**：`src/lora.py:215-236` 的 `apply_lora_to_model` **不做全局冻结**（Adapter/Prefix 在 `peft_methods.py:107/129` 都先 `requires_grad=False`，LoRA 没有），而 `src/trainer.py:243-244` 用 `get_peft_params` 取**全部** `requires_grad` 参数建优化器 → 历史 "text-only" 跑到的是 96% 的参数。

**脚本**：`experiments/strict_freeze_control.py`（**不改 `src/`**：在 `StrictTrainer.setup_model()` 里、优化器建立之前冻结，只放开 `lora_A/lora_B`）。
**跑法**：`{text_only, both, vision_only} × {42,123,456,789,1024}`，Flickr30k / batch 128 / 10 epoch / 5000 样本（与原协议一致）+ 一条 frozen 参考。
**产出**：`outputs/strict_freeze/**`，每跑记录 `n_trainable_params`、`backbone_delta`（对照 pristine CLIP 的真 ΔW）、`lora_update_norm`、逐层有效秩（init/final）。

**已确认的冒烟结果**（1 epoch/512 样本，仅供 sanity check）：`text_only` 可训 **196,608**（0.13%），**`vis_nonzero=0`** —— 严格冻结下视觉侧确实零更新。

**踩过的坑（勿重犯）**：① 曾用 1 epoch 的 smoke 结果污染 `outputs/strict_freeze/`，导致全量跑把 seed42 当"已完成"跳过 → 已把 smoke 输出重定向到 `outputs/strict_freeze_smoke/`；② `Tee-Object` 在目录不存在时会秒退，启动前必须先建目录。

## 二、已完成的修改（补丁 A / A2 / A3，共 42 处替换，全部计数断言通过）

| 类别 | 内容 | 依据 |
|---|---|---|
| **116 → 117** | 9 处（abstract/intro/exp×3/concl/supp×3/visual_fragility/discussion）+ 目录分区 XIII 的 "7 experiments"→8 | `tools/_p1_count_experiments.py`：13 个分区里 12 个的行数与声明一致，仅 XIII 声明 7 实列 8 |
| **"first systematic study" 去旗** | abstract / intro / conclusion 三处改为 "a systematic study" | Huang et al. ICCV 2025（待补引，见四） |
| **24% → 23.3%** | abstract/intro/conclusion 改为 5-seed 均值口径（`+0.1906±0.00747`，占 frozen 0.8184 的 23.3%） | `outputs/flickr30k_seeds/summary.json` |
| **Adapter 共同基线** | Table 4 行、RQ4 段落、ANOVA 段落、intro 两处：由"各自注入后基线"改为**对照 frozen**（d16 对：text-only **+0.237**、both **+0.500**；7 跑均值 +0.229，**无一配置降低 gap**）；并**撤销** `fix_paper1_round3.py` 装进去的 F=13.37 结论 | `tools/p1_adapter_common_baseline.py`（frozen=0.8184，三个 LoRA 跑互差 0.0002） |
| **DG/CG 相关性** | Table 5、§RQ5、§4.3、intro/conclusion 的对应主张：改用**可复现规则 n=204**（DG −0.714、CG −0.594、偏相关 −0.581、**DG~CG +0.945**、DGΔ +0.134/p=0.055、CGΔ +0.190/p=0.007），并写入"n=81 子集不可重建、已被取代"的披露；删去"DG 显著优于 CG""偏相关 −0.807 证明增量价值" | `tools/p1_dg_r1_recompute.py` → `outputs/analysis/dg_r1_reproducible.json`（含逐行出处 + 6 种口径敏感性表） |
| **fig1** | 重画为**单一数据集**（Flickr30k 全套 + frozen 参考线 + 5-seed 带）；图注写明数据源 | 原生成器 `GF=sorted(glob(...))` 字母序取首个匹配 → coco 覆盖 flickr30k，三条线是 COCO、带子是 Flickr |
| **fig2** | 按可复现规则重画（n=204，r=−0.714/−0.594）；图注同步 | `tools/p1_dg_r1_recompute.py` 输出 |
| **fig3** | Adapter 柱改为共同基线 **+0.237 / +0.500**，并改注记"Positive = gap enlarged relative to the frozen model" | `outputs/analysis/adapter_common_baseline.json` |
| **fig5** | 重画并把 e2 由 "Both-LoRA (α=4)" 改标为 **"Text-only (r=8, α=4)"**；图注同步 | `paper/scripts/dges_improved.py:273-275` 明确定义 `text_alpha4 = (vision=False, text=True)`；e2 的 `n_trainable=145170177`=e3、checkpoint 787KB≪e1 的 1955KB |
| **口径披露** | `methodology.tex` 新增"Disclosure of the fine-tuning convention"段：说明历史 LoRA 跑只冻结被替换的 Linear、其 embedding/LayerNorm 仍可训（记 145,170,177 可训参数），并指向新的严格对照节 | `src/` 源码 + 存档 |
| **Frozen R@1** | intro 的 Text+Vis-L1 句补上"也超过冻结模型本身（R@1=0.617，同协议）" | `outputs/layered_ft_results.json`（Frozen [CG 0.8137, R@1 0.6167]） |
| **yi2025 措辞** | "proved that dimension collapse is the root cause" → "attributes the modality gap to dimension collapse" | 该主张未能独立核实（VPN 挡住 web_fetch） |

## 三、引用修复（四份 bib 同步，标题↔ID 配对校验全过）

`tools/_p1_bib_fix.py` + `tools/_bib_verify.py`；原件备份 `_bibbackup_20260918/`。

- **两个 arXiv ID 互换**（`xu2026vlreasoning` ↔ `morelli2026sparse`）：改了 `paper/`、`paper合/`。
  ⚠️ **代理说 "ap3 也有互换" 是错的** —— `paper_ap3/refs.bib` 本来就是对的（脚本按条目编辑，才没把它改坏）。
- `gao2026uniformity` DOI `2501.00984` → `2602.09507`（`paper/`、`paper合/`；ap3 早已正确）。
- `niss2025reviving` year 2025 → 2026（该文 2026-05-13 才出）。
- `yi2025decipher` 增加 ICML 2026 正式版题名注（`paper/`、`paper2/`、`paper合/`）。

**仍未做（需 VPN 关闭后手动一次）**：补引 Huang et al., *Mind the Gap: Preserving and Compensating for the Modality Gap in CLIP-Based Continual Learning*, ICCV 2025 —— 作者列表未能核实（只有 [CVF 页面](https://openaccess.thecvf.com//content/ICCV2025/html/Huang_Mind_the_Gap_Preserving_and_Compensating_for_the_Modality_Gap_ICCV_2025_paper.html)，`web_fetch` 被劫持 DNS 挡住）。**不得凭猜写作者**。同样待核：`niss2025reviving` 的作者列表。

## 四、被否掉的代理结论（重要）

| 代理结论 | 复核结果 |
|---|---|
| [M5]/[F13] "Figures 2 and 3 are swapped" | **误报**。`\includegraphics` 实为 fig3.png（"Cross-validation" 图注）与 **fig4.png**（"Ablation" 图注），且我目视 fig3.png 确认它就是交叉验证柱状图、与图注一致。代理把 fig4 误记成 fig2。 |
| "ap3 的 refs.bib 也有互换的 ID" | **误报**，见上。 |
| "摘要 59.3% 与表格 59.28% 不一致" | **非缺陷**，四舍五入。 |
| "更正信与稿件数字不一致"（[M16]） | **部分成立但结论不同**：稿件 Table 7 用的是 **50k 全量验证集 + 3 seed 均值**协议，且 `experiments.tex:215`/表注都写明了；08-14 更正信说的是 **14,288 子集**。两者是**两套协议**，稿件内部自洽。→ 处理方式不是改稿件，而是**在返修信里更正协议描述**；另需**登录 EM 确认期刊手上是哪一版**（08-14 版还是 08-22 版）。 |

## 五、第二轮补丁（A5–A7）与 PDF 级复核（教训）

**补丁 A5**：Table 4 的列名是 "Mean CGΔ"，而 A 补丁把 Adapter 行填成了**最佳配置**值（+0.064）→ 改为组均值 **+0.229**（R@1 0.173），最佳配置写进右列；全量微调行改为五种子均值 **+0.191**（R@1 0.597）；表注补 `n`（Adapter 7 / full-FT 5）。

**补丁 A6 + A7：A 补丁漏网的 11 处陈旧值。**
⚠️ **教训（重要）**：A 补丁只做了**源码级**替换与计数断言，编译后发现 PDF 里 `0.827`/`0.807`/`81 experiments` 仍在——它们在 `methodology.tex:28,30`、`discussion.tex:18,36,44`、`supplementary.tex:242,245,247,249,259` 等处。**必须 recompile → `pdftotext` → 在产物文本里按模式扫**，源码断言不能替代产物核对。（同类陷阱：用内存里 `-like` 匹配大段文本会误报缺失；以文件级 `Select-String` 为准。）

**PDF 级复核结果**（`paper/_p1pdf.txt`）：

| 检查 | 结果 |
|---|---|
| 编译 | 40 页，0 error，唯一警告 = 待 Patch B 补的 `sec:strictcontrol` 引用 |
| `0.827` / `0.807` / `81 experiments` / `zero vision-side` / `n=81` | **0 次**（清零） |
| `0.012, p = 0.915`（旧 CGΔ 相关性）/ "non-triviality of our metrics" / "DG is not a redundant proxy" | **0 次**（清零） |
| `24\%`（旧 gap 增幅）/ `-0.100`（旧 Adapter 均值） | 0 次 |
| 新值 | `0.714`（8+ 行）、`0.581`、`0.945`、`0.237`、`23.3`、`117 experiments`、`R@1=0.617`、口径披露段 —— 全部存在 |
| `F = 13.37` | **仍在，但属故意**：新 ANOVA 段明确写"上一版报告过 F=13.37，该结论不成立" |
| `0.199` | 保留于**单跑**语境（Table 2/3 行、SigLIP 小节、5-seed 逐种子表），已在 experiments/discussion 两处标注"单跑 vs 五种子均值"的区别 |

**其他本轮产物**：`paper/cover_letter_revision.tex`（3 页，编译通过）——含姊妹稿披露段 + 主动更正表，供返修时直接改用。

## 六、剩余工作

1. **Patch B（等实验）**：Visual Fragility 机理段、abstract 的 "direct causal evidence"、新增严格对照节 `\label{sec:strictcontrol}` + 表格（当前编译只剩这一条 undefined reference）。
2. **fig11**（唯一剩的图）：`paper/scripts/gsnr_analysis.py:172` 的面板 B 标题算出 "Vis grads contribute <640%"（`(0.56−4.15)/0.56×100` 的量纲错误），且其 "Text-only matches Both" 与稿件自己的脚注（text-only 收敛到更高 loss，4.15 vs 0.56）矛盾。**重生成需跑该脚本 → 占 GPU，必须等严格冻结实验结束后串行执行。**
3. ~~返修封面信草稿~~ ✅ `paper/cover_letter_revision.tex`（3 页，编译通过）。
4. ~~重编译 + PDF 级复核~~ ✅ 见第六节；Patch B 后需再做一次。
5. **第二轮独立子代理复查**（待全部改完）。
6. **ap3 侧**（非本轮）：`04_mechanism.tex:28` 的 BLIP-1→BLIP-2 真身、r=−0.827 归属、封面信披露、`paper合/` 与 P1 的 1,413 词重合改写。
7. **需 VPN 关闭后手动核**：Huang ICCV 2025 的作者列表、`niss2025reviving` 的作者列表。
## 七、第三轮补充（补丁 A8/A9 + highlights + 图-产物核验）

- **补丁 A8**：supplementary 脚注 c 的秩定义（"threshold 0.99 explained variance"）与跟踪代码/图 8 用的定义不同（第三套定义）→ 改为与代码一致的 `exp(-Σ p_i log p_i)`，并写明"legacy 跑会降低它、严格对照完全不变"。
- **补丁 A9**：Connector-S 改引 **IJCAI 2025 正式版**（DOI 10.24963/ijcai.2025/1202，已核）；GTMA 加"IEEE Xplore doc 11463397"注（期刊名未核，**不猜**）；`related_work.tex:20` 与 `visual_fragility.tex:12` 的 `zhu2026fi`（LLM 脆弱性论文）改为显式说明"该结论出自 LLM 场景，我们推测可迁移到视觉编码器"；`visual_fragility.tex:8` 的 "proved" → "attributes"。
- **`paper/highlights.tex` 重写**：原 5 条**全部**含过期主张（first / 116 / r=-0.827 / partial -0.807 / causal evidence）。新 5 条渲染长度 78–85 字符（含项目符号），符合 Elsevier ≤85 限制；已编译 `highlights.pdf`。
- **图-产物核验**：`pdfimages -list` 与源 PNG 尺寸逐一比对 → fig1/fig2/fig3/fig5/fig7 **五张重画图全部确实嵌入**重编译后的 PDF（2051×1151 / 2370×1019 / 2844×1348 / 1841×941 / 1691×1027）。
- **编译状态**：40 页，0 error、0 undefined citation；唯一待办 = Patch B 的 `sec:strictcontrol` 标签。
- **新工具**：`tools/p1_strict_control_summary.py`（严格对照汇总：逐配置 CGΔ/R@1/可训参数/视觉非零张量数/逐层秩变化 + 与 legacy 对比 + LaTeX 表行），幂等，实验结束直接重跑即可。
## 八、Patch B：严格冻结对照与机理重写（2026-09-20）

### 结果（5 seeds，全部完成）

| | 严格冻结（可训 **196,608** = 0.13%） | 旧"text-only"（可训 145,170,177） |
|---|---|---|
| CGΔ | **−0.0465 ± 0.0027** | −0.0458 ± 0.0021（5-seed） |
| R@1 | **0.6238 ± 0.0049** | 0.6210 |
| 视觉侧改动 | **0/199 张量**；逐层有效秩 Δ = **+0.0000** | 全模型 96% 参数在训 |
| 文本侧秩变化 | +0.4612 | — |

**结论**：用 0.13% 的参数、视觉编码器可证明零更新，效果与旧跑几乎一致 → 历史跑多训的 1.45 亿参数对本效应**无贡献**；"protect the visual encoder" 由推断变为实证。

### ⚠️ 未完成的 joint 行（如实记录，勿再重跑）

`both` / `vision_only` 的严格跑**慢约 10 倍**（实测 312–326 s/epoch，text-only 仅 ~30 s/epoch）：视觉塔一旦含可训参数即必须做完整反向传播；text-only 严格跑则整棵视觉塔的反向被跳过（这正是它 6 分钟/跑的原因）。按此速度 10 个跑需 8+ 小时，**本轮放弃**，并在新章节中明写"对照覆盖承载机理主张的 text-only 配置；joint 行留作未来工作，而不是以低种子数硬报"。

### 本轮改动的文件

- 新增 `paper/sections/strict_control.tex`（`\label{sec:strictcontrol}`，Table 8），由 `paper/main_nn.tex` 在 visual_fragility 之前 `\input`；
- 机理表述重写：摘要（"direct causal evidence" → 严格对照）、`introduction.tex` 贡献 7 与第 8 行、`conclusion.tex` 贡献 3 与 5、`visual_fragility.tex` 两处；
- 生成器 `tools/_p1_patch_b.py`（运行时读 `outputs/analysis/strict_control_summary.json` 填数，缺数据则断言失败且**不写盘**）。

### 我自己犯并修掉的两个错（教训）

1. `\begin{tabular}{lcccc}` 声明 5 列而行内 6 个字段 → LaTeX "Extra alignment tab"（已改 `lccccc`，并把生成器同步）。
2. 摘要替换用了**错误的换行位置**导致 0 命中；因为 `_p1_patch_b2.py` 是"全部成功才写盘"，文件**没被改坏**——这种"先断言、后写盘"的写法本次避免了一次半成品编辑。**今后所有补丁脚本都按此模式写。**
## 九、第二轮复查（四份）与补丁 C–G

第二轮派出四个与"验证修复"不同的攻击面：`docs/P1_REVIEW2_{FIXVERIFY,NUMBERS,MECHANISM,ARTEFACTS}.md`。汇总：fix-verify 4 must/6 should（31/34 项已落盘、构建产物 43 页 0 undefined）；numbers 34 PASS/9 INCONSISTENT/2 UNSUPPORTED；mechanism **7 must**/10 should；artefacts 6 must/6 should/9 note。

### 补丁 C（20 处）
Table 1 SigLIP 5→6（使单元格和 = 印出的 117）；n=204 规则补写"排除严格对照"；Table 2 表注写明 Adapter 列用各自注入后基线并交叉引用 Table 4；fig4 图注改为三面板（rank｜α｜模块，原写"α（左）"）；fig1 去掉"monotonic"；`+0.237` 补注 (d=16)；五种子标准差统一为样本标准差（→1.0%）；supplementary 的 "Table 9" 改用 `\ref`；`vitl_frozen` 的 R@1 由 0.000 改 `---`（存档无该值）；full-FT CGΔ 上界 +0.67→+0.66（实测 0.6646/0.2609/0.2672）；结论补回具名例外；相关/讨论各处 yi2025 "证明"→"归因"；删除 `paper/main_nn.abs`；fig11 重生成后图注 1.4×/4.16/0.61。

### 补丁 D/D2（机理重构，**影响结论**）
严格对照的结果**反过来否掉了视觉脆弱性解释**：历史混合 text-only 训了 **95.96%** 的参数（含全部 199 个 `vision_model.*` 张量、视觉秩 9.43→6.16–7.02）却与严格对照（0/199、可训 196,608）结果无差异（−0.0458±0.0021 vs −0.0465±0.0027，**Welch p=0.7017**）→ 视觉侧附带更新**惰性**，真正变量是**适配器放在哪一侧**。摘要/intro/conclusion/§5 全部改写：明确对照为**一臂**、有效秩"不变"降级为**冻结一致性检查**（循环）、不再把梯度分析当收敛证据（视觉梯度 1.4× **更大**）。

### 补丁 E（M4/M5）
分层微调族的 text-only/both 是**未冻结**配置且已发散（CG 1.29、R@1 0.01），而 Text+Vis-L1/L2/L4 冻结 → 引言/讨论/图注补"协议警告"；图 8 面板 (B) 由**只含适配器**的重建算出、与冻结必然重合 → 注明是适配器一致性检查，面板 (D)（实测训练跑）才有效。

### 补丁 F/G（投稿件）
- **稿件原本没有 Funding 与生成式 AI 声明**（A1 有）→ 已补（Elsevier 要求；作者确用 Claude/DeepSeek）。
- Table 1 的 Adapter 最佳 CGΔ 由 −0.217 改 **+0.064**（该表图注承诺"相对冻结基线"）。
- 两条 bib 注改为单行（多行 + 保护括号是排版异常的来源）。
- 2026-08-14 那封更正信里 `$\text{CG}$` 未加载 amsmath → **LaTeX 报错但仍产出 PDF，交上去的那份在该处是残缺的**；已修源码并重编译。
- 返修封面信：删掉"Prefix comparisons"（正文列出 prefix 为未探索），并**新增两行** reconciled 两封 08-14 信（零样本协议 14,288 vs 50k；变化相关性 −0.042/+0.012 → +0.134/+0.190）→ 现 4 页。
- **归档改前遗留物**到 `paper/_superseded_2026/`：`abstract.pdf`（与稿件 9 处矛盾）、`title_page.docx`（Neural Networks／哈工程／旧 ORCID）、`declaration.docx`、`declarationStatement.docx`；并重生成过期的 `declaration.pdf`（原 7-04 哈工程）与 `cover_letter.pdf`（原 8-05）。

### 被否掉的代理结论（第二轮）
- "p = 0.70 应为 0.66–0.67"：**误报**。用样本标准差（0.00303）复算 t=−0.398、**p=0.7017**。
- 第一轮的 [M5]"fig2/fig3 对调"依旧为误报（已目视确认）。

### 我自己的错误（记录）
`re.subn` 的**替换串会处理转义**：`\a`→BEL、`\b`→退格、`\\`→单反斜杠，导致插入的两行表格丢掉 `\addlinespace`/`\bottomrule`。**教训：LaTeX 文本一律用 lambda 作替换**（`re.sub(pat, lambda m: text, s)`），或改用 `str.replace`。

### 仍未完成
① joint 严格臂（今晚，`docs/P1_TONIGHT_RUN.md`）；② Huang et al. ICCV 2025 作者列表（需 VPN）；③ 登录 EM 确认期刊手上是哪一版（08-14 的 14,288 子集 vs 08-22 的 50k 协议）；④ `competing_interests.docx` 内容未核（无法直读二进制，交前请打开确认机构信息）。
## 十、提交版核对（桌面 `PR-D-26-10149.pdf`，2026-09-20 提供）

操作者提供的提交版是 **Editorial Manager 2026-07-24 13:11 生成的合并快照**（40 页，iTextSharp 5.5.13.2），**早于 8-14 两次更正信，也早于本轮整改**。因此审稿人读的就是这一版。探测结果：

| 项 | 7-24 提交版 | 现稿 |
|---|---|---|
| 摘要零样本 | 24%、zero-shot 下降 **53.3%**、text-only 限 **+0.079** / **1.7%** | 23.3%±1.0%；ImageNet-1K 50k：frozen 59.28 / text-only 58.66（−0.62pp）/ both 59.67（+0.39）/ full-FT 2.6%（3 seeds）；DTD/Food101 在 ±0.8pp 内 |
| 零样本基准名 | **CIFAR-100**（DTD、Food101） | **ImageNet-1K**（DTD、Food101） |
| 模型计数 | four models (CLIP ViT-B/32, ViT-L/14, BLIP-1, SigLIP) | three model families (CLIP, BLIP-1, SigLIP) |
| 实验数 | 116（11 处） | 117 |
| DG/CG | r=−0.827 / −0.807（各 12 处） | −0.714 / −0.594 / 偏相关 −0.581；DG~CG +0.945 |
| 措辞 | first systematic study（6 处）、direct causal evidence（4 处） | 均已改（去 first、改为一臂严格对照） |

**关于版本状态的记录（按操作者说明，2026-09-20）**：8-14 已提交过一轮更正。桌面这份是**首次提交**的合并产物——EM 对提交件保留的通常就是首次生成的那份，是否被后续替换件覆盖，从这份 PDF 看不出来，**不据此推断**。因此下表列的是“**首次提交 → 现稿**”的差异，供返修时逐条对照。→ 返修封面信已按 7-24 版重设基准（补丁 H）：新增本信针对哪一版的说明段、新增零样本声明行（53.3%/1.7%/+0.079 → 现 ImageNet 数字）、并把两行 8-14 和解行改写为 as submitted / 8-14 信 / 现稿三段式。**是否现在就在 EM 里补传修订版由操作者决定。**

## 十一、本轮其他非实验收尾

- `competing_interests.docx` **已核**（解包 docx XML 读正文）：仅为标准利益冲突声明，**无机构/日期信息** → 该项关闭。
- **ap3 侧 BLIP 命名已修**：`paper_ap3/` 把第三骨干写成 BLIP-2 (350M, Q-Former) 并引 `li2023blip2`，而它引用的数字（+0.047/+0.152、R@1 0.175）是 P1 的 **BLIP-1** 跑（P1 methodology 自述 cross-attention decoder / BERT text encoder / ITC+ITM+LM = BLIP-1）。已 6 处改为 BLIP-1 + `li2022blip`；ap3 全文现已无 BLIP-2 残留。
- **ap3 仍待办**（其投稿前的自身整改，非本轮）：`01_intro.tex` 等处仍引 P1 已撤销的 `r=−0.827`、以及 116 计数与 Adapter 旧基线值——ap3 准备投时要按 P1 修正后的口径整体重导。
- **Huang et al. ICCV 2025 引用已补**（操作者 2026-09-20 提供确切 bibtex）：新增条目 `huang2025mindgap`（Huang, Cao, Lu, Meng, Yang, Liu；ICCV 2025, pp. 3777--3786），插在 `hu2021lora` 之后保持字母序；引用两处——`related_work.tex` §2.1（"the gap has become an object of intervention rather than only of analysis"）与 `introduction.tex` 的定位句（他们作用于 gap，本文刻画 gap 对"在哪一侧/多大规模/什么秩"的响应）。重建后参考文献 [11]、0 undefined、43 页。**此项关闭。**
<!-- 原记录：~~Huang et al. ICCV 2025 引用仍缺~~：`web_fetch` 被 VPN 劫持 DNS 挡住（ar5iv/arxiv 均解析到非公网 IP），搜索快照从不包含作者行。需关 VPN 后从 [CVF 页面](https://openaccess.thecvf.com//content/ICCV2025/html/Huang_Mind_the_Gap_Preserving_and_Compensating_for_the_Modality_Gap_ICCV_2025_paper.html) 复制 bibtex（arXiv 版为 2507.09118）。
## 十二、轻量实验：参数噪声主张不可复现（2026-09-20）

操作者要求"跑轻量的"，于是只跑了 `noise_sensitivity.py` 的 **[A] 噪声敏感性**（纯前向，2000 样本、batch 64，3 seeds 共约 4 分钟；**[B] 有效秩跟踪会重训并覆盖已归档的 `effective_rank_tracking.json`，故刻意未跑**）。脚本 `tools/p1_noise_seeds.py`，原始单次抽样先存档为 `outputs/noise_sensitivity_pre_seed.json`，逐种子原始值在 `outputs/noise_seeds/`，聚合在 `outputs/noise_sensitivity_seeds.json`。

| σ=0.1 | 视觉编码器注噪 | 文本编码器注噪 | 比值 |
|---|---|---|---|
| 原始单次抽样（论文所引） | R@1 0.705→0.640，降 **9.22%** | 0.705→0.680，降 **3.55%** | **2.6×** ← 论文该数字的来源 |
| **3 seeds（新跑）** | **2.15% ± 4.41** | **−0.01% ± 1.93** | 分母≈0，**无意义** |

- 视觉优于文本的种子数：**2/3**（σ=0.1）；σ=0.01 时 3/3，σ=0.03 时 0/3 —— 排序**不稳定**。
- 另有一个设计弱点：每次运行都重建验证子集（baseline R@1 在 0.685–0.695 间波动），本身放大方差。

**结论：删去"视觉噪声危害 2.6× 于文本"这一主张。** 改动：图 9 图注改为如实描述"这是单次评估 + 三种子复跑不稳定、故不据此下结论"；supplementary 脚注 a 同步；`experiments.tex:6` 的 "causal evidence" → "mechanism probes"；catalog 的 "XII. Causal Evidence" → "XII. Mechanism Probes" 及其脚注引用；`discussion.tex:44` 的 "causal analysis" → "the strict control of Section 5"。

**这条与 §八的机理降级同向**：论文现在的证据基础是"经验规律 + 严格对照"，而不是"因果证据"。图 9 的面板 (B)(C) 来自早期训练跑（未重训），其有效秩结论已在 §八按同一逻辑处理。

## 十三、噪声实验第二轮：把混淆真正消除（2026-09-20 晚）

第一轮（§十二）只固定了"图像集合"，结论是"排序不稳定"。本轮先做了设计审计，发现第一轮的设计本身不成立：

- `tools/p1_noise_fixed_subset.py` 把 loader 只建了一次，但 `src/dataset.py:401/406` 建对象时用的是 `split="train"`，`:422` 又用 `random_split` 把 **train 对象**切成 train/val/test → `val_loader` 迭代的是**带训练增强的数据集**（`get_clip_transform(is_train=(split=="train"))` → `RandomHorizontalFlip` + `ColorJitter`，走 Python `random`）。
- 且 `num_workers` 默认 4、`persistent_workers=True`，增强发生在常驻 worker 进程里，主进程再 seed 也管不到。
- 证据就是它自己的 σ=0 控制：**本应精确等于基线，却给出 0.675–0.695（基线 0.695）**，即"零噪声也有 1.01%±1.09 的下降"。→ 该文件的配对检验无效，只作为"控制暴露设计缺陷"的记录保留，不引用其数字。

第二轮 `tools/p1_noise_fixed_aug.py`：`num_workers=0` + 每次评测前用固定种子重播增强随机流（噪声仍按 seed 各自抽样；`inject_noise_to_encoder` 消耗固定次数的 `randn_like`，随后整体覆盖 RNG 状态，因此两者互不污染）。

结果（`outputs/noise_fixed_aug.json`，基线 R@1 0.6850，5 seeds，σ∈{0, 0.03, 0.1}）：

| σ | 视觉 drop | 文本 drop | 比值 | 配对差(v−t) | 视觉>文本 | 配对 p |
|---|---|---|---|---|---|---|
| 0.000 | 0.00 ± 0.00 | 0.00 ± 0.00 | — | 0.00 | 0/5 | — |
| 0.030 | −1.02 ± 1.76 | −2.19 ± 0.52 | 0.47× | +1.17 ± 1.97 | 3/5 | 0.256 |
| 0.100 | 1.90 ± 1.83 | 2.48 ± 3.25 | 0.76× | −0.58 ± 4.21 | 2/5 | 0.772 |

- **σ=0 的 10 次运行全部精确复现基线**（R@1 均为 0.6850）→ 这一版设计成立，配对检验有效。
- σ=0.1 时视觉侧**并不更脆弱**（1.90% vs 2.48%，p=0.77），甚至略低；σ=0.03 时两者都≈0（负值=基线本身的单次抽样运气）。
- 第一轮看到的"视觉 5.04%"与档案里的"9.22% vs 3.55%、2.6×"都被增强噪声放大过：**档案那个 2.6× 是"未配对 + 单次抽样 + 重抽子集"三重问题的产物**。

改动：supplementary 脚注 `$^a$` 补上配对结果（1.9±1.8 vs 2.5±3.3，p=0.77，并明写"视觉侧不是更敏感的一侧"）；图 9 图注末句改为交叉引用该脚注（`Table~\ref{tab:full_experiments}`），不再重复数字。

遗留（小，自查发现）：脚本判定控制的容差写成 `abs(r["R1"] - baseline) < 1e-9`，而 `rows` 存的是 `round(R@1,4)` → JSON 里 `control_sigma0_reproduces_baseline` 被写成 `false`、打印也显示 FAILED，但逐行数据表明控制通过（10/10 等于 0.6850）。已把容差改为按记录精度比较；**待 GPU 空闲后重跑一次**（约 1.5 分钟）让该字段自洽。

**`outputs/noise_sensitivity.json` 的溯源（核对发布漂移时发现，重要）**：今天 16:31 的种子跑把 live 的这个文件覆盖成了**又一次单抽样**（baseline 0.685；σ=0.1 视觉 0.705，即"**提升** 2.92%"；文本 −2.19%）。论文原先引用的那一次（baseline 0.705；σ=0.1 视觉 **9.2199%**、文本 **3.5461%**，即 2.6× 的来源）已按字节保存在 `outputs/noise_sensitivity_pre_seed.json`；已用 git 校验它与上一版提交里的 `noise_sensitivity.json` **完全相等**（`pre_seed == HEAD` → True），引用来源没有丢失。这次新的单抽样同样不支持"视觉更脆弱"（视觉侧反而比文本侧更好），与本节配对结论一致。

**发布工具修正（两处）**：① `tools/_publish_live_drift.py` 的前缀白名单漏了 `paper`/`tools`/`outputs`/`src`/`experiments`（只扫 142 个文件），今晚改完稿件后它仍报"只有 1 个文件不同"，而 `paper/sections/supplementary.tex` 实测已不同——属**漏报**，已补齐（现扫 1 687 个文件，同一状态报出 7 个不同）。② 漂移工具只遍历 publish HEAD 已跟踪的路径，**看不见全新文件**，故新增 `tools/_publish_new_files.py` 列出"只在 live 存在"的候选文件，提交前两个都跑。

## 十四、DTD / Food101 数值溯源：投稿版与现稿不同，已补披露

- 投稿版（桌面 `PR-D-26-10149.pdf` 抽取文本）脚注写的是：DTD Frozen 43.27 / Text-only 43.33 / Both 42.53，Food101 Frozen 80.60 / Text-only 80.67 / Both 79.73。
- 现稿用的是 DTD 42.87 / 43.30 / 43.03、Food101 82.32 / 81.58 / 81.63（`outputs/dtd_food101_zs_check.json`）；已核验 `paper/figures/fig12_zeroshot_more.png` 的 6 个柱标与 supplementary 脚注 `$^d$` 都是这套，稿件内部自洽。
- 差异原因（代码级）：旧值出自 `paper/scripts/zeroshot_extra.py`，其 `evaluate_zeroshot` 第 64 行**对每个 (配置, 数据集) 组合都重新 `np.random.choice` 抽 1500 张**，既无种子也非配对 → Food101 只抽到约 15 张/类，三个配置根本不在同一批图上。现稿用 `tools/clip_dtd_food101_rerun.py` 跑**完整官方 test split**（DTD 1 880 / Food101 25 250）+ 标准 CLIP 预处理，是有脚本可复现的一版。
- 关键差别：旧值下 Food101 both = 79.73 相对 frozen 80.60 是 **−0.87**，会**超出**稿件"±0.8 个百分点"的说法；全量配对测得最大偏差 **0.74**（Food101 text-only）。
- 改动：`paper/cover_letter_revision.tex` 勘误表新增一行 "DTD / Food101 values"，如实说明旧协议为"每条件重抽 1500 张"并给出两套数值；重编译 `paper/cover_letter_revision.pdf`（4 → 5 页，退出码 0，PDF 文本级核对新行与 "0.74"/"0.87"/"25,250" 均已渲染）。

## 十五、今晚的两项独立复核（2026-09-20 深夜）

### 1. ImageNet 50k 六行全量复现（不重训，30.8 分钟）

`tools/p1_imagenet_verify.py`（只跑 plain 单模板协议；**只读**档案、结果另存，绝不覆写 `outputs/imagenet1k_zs_50k_plain.json`——复核后该文件仍是 8/14 21:45 的 1187 字节原样）。对稿件 Table 7 的 6 行在**完整 50 000 张 val** 上重跑并与档案逐行比对：

| 行 | 重跑 | 档案 | 偏差 |
|---|---|---|---|
| frozen | 59.29 | 59.28 | +0.01 |
| text-only, $r$=8 | 58.68 | 58.66 | +0.02 |
| both, $r$=8 | 59.66 | 59.67 | −0.01 |
| full-FT s42 | 0.13 | 0.13 | 0.00 |
| full-FT s123 | 4.10 | 4.09 | +0.01 |
| full-FT s999 | 3.55 | 3.54 | +0.01 |

- 最大偏差 **0.02 pp**（即 5 万张里 1–10 张图），六行全部复现；full-FT 三 seed 均值重跑 2.59% vs 档案 2.59%（稿件 2.6%）✓。结果：`outputs/imagenet1k_zs_50k_verify.json`。
- **顺带澄清一个可疑点**：both-position 在 14 288 子集与完整 50k 上**都是 59.67**，原本怀疑是陈旧档案被误用（巧合概率不低），复跑证实两者都是真实测量（子集 59.67 = 档案值；全量 59.66/59.67）——只是巧合，不是复用。
- 复跑与档案存在 ≤0.02 pp 的差异，说明这条评测链**并非逐位确定**（CUDA 归约次序等），但远小于任何结论所需精度；不改稿件，仅记录。

### 2. 摘要两项数值独立重算

- **`+0.191 ± 0.008`（full-FT 五 seed 的 CG 增量）**：从 `outputs/flickr30k_seeds/baseline_full_ft/seed{42,123,456,789,1024}/results.json` 重算，CG 均值 **1.0092**、sd(ddof=1) **0.0084** → Δ = **+0.1908**，即冻结基线的 **23.3% ± 1.0 pp** ✓ 与摘要/intro/highlights 完全一致。
- **冻结锚点 `0.8184`**：出自 `outputs/analysis/adapter_common_baseline.json` 的 `frozen_reference_cg`，是**同协议三次**冻结评测的均值（0.8183848 / 0.8184462 / 0.8182860 → 均值 0.81837）。独立跑的 `outputs/flickr30k/baseline_frozen` 给 0.8185005；两者差 1e-4，对任何报到 3 位小数的量无影响。稿件用 0.8184 作为 **Adapter 同协议锚点**是正确的（用它算 5-seed full-FT 也是 +0.1908/+0.1907，同样 →+0.191）。
- **一处过期断言**：`tools/obsolete/audit_fix_regression.py:43` 检查的是 `0.191 \pm 0.007`，与实测 sd 0.0084 不符——**该断言过期，稿件（±0.008）才是对的**，勿据旧脚本"修正"稿件。

### 3. 投稿 PDF 门禁补齐 P1

`tools/audit_submission_pdfs.py` 的 `SETS` 里原本只有 A1 与 A23 两个包，**P1 包从未被门禁检查过**；而且作者/邮箱/位图三项检查硬编码 `name == 'main.pdf'`，P1 的正文叫 `main_nn.pdf`，即使加进去也会被静默跳过。现已按包推断正文与封面信文件名并把 P1 纳入，实测其正文 **43 页 / 25 张嵌入位图 / 禁词 0 命中 / 作者+邮箱+刊名齐备**，勘误信 5 页并含刊名。三包合计 **PROBLEMS: 0**。
