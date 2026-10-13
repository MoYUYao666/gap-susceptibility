# PR 写作/定位加固：逐条改法 + 可直接粘贴的 LaTeX

**任务**：`task-4`（对 PR 的 R1.4 / R1.5 / R2.1 / R2.2 / R2.4 / R2.5 / R3.1 / R3.3 / R3.4 给出改法）
**对象稿件**：`paper合/`（P1+P2 合并稿，目标 Neurocomputing）。**P1（`paper/`）已冻结，不改。**
**写者边界**：本文档是**唯一**产出物。**未改动任何 `paper合/*.tex`**——合成由 Lead 执行。
**日期**：2026-10-12

---

## 0. 使用说明与三个必须先读的事实

### 0.1 目标文件是**两份镜像**，改一处必须同步另一处

`paper合/sections/*.tex` 与 `paper合/NC_submission/latex_source/sections/*.tex` 目前**逐字节相同**（2026-10-12 实测 SHA256 全等）：

```
introduction SAME   related_work SAME   empirical SAME   theory SAME
validation   SAME   discussion   SAME   conclusion SAME   supplement SAME
main_nc      SAME
```

→ 下述所有行号**均指 `paper合/sections/*.tex`**。若 Lead 只改一处，另一处会与正文脱节。建议改完后重跑镜像复制，并用 `tools/` 下脚本复核。

### 0.2 标题出现在 6 个位置（R2.1 收窄后需同步）

| 文件 | 行 | 说明 |
|---|---|---|
| `paper合/main_nc.tex` | 28 | Elsevier 主标题 |
| `paper合/NC_submission/latex_source/main_nc.tex` | 28 | 镜像 |
| `paper合/main_springer.tex` | 36 | **短标题 + 长标题两处**，须同时改 |
| `paper合/highlights_nc.tex` | 11 | Highlights 页眉 |
| `paper合/cover_letter.tex` | 24 | 投稿信 |
| `paper合/cover_letter_nc.tex` | 24 | 投稿信（NC 版） |

**不要改** `cover_letter*.tex:78` —— 那里引的是**前任稿 P1 的旧标题**，是披露信息，改了反而错。

### 0.3 数字溯源约定

本文档中出现的**每一个数字**都在 §6 给出「文件 + 字段 + 算式」。凡本文档**没有**给出溯源的数字，一律不出现在建议文本里。
⚠️ **`tools/_p250_verify_pr_details.py` / `outputs/analysis/trace_0p079.json` 的字符串模糊匹配不是溯源**（`trace_0p079.json` 的 `string_hits` 有 **40** 条命中、`numeric_hits` 有 **80** 条，绝大多数与 Route D 无关）——本文档用的是**逐 run 相减**。

---

## A. 主表：逐条 = 位置 + 现文（逐字）+ 建议新文 + 理由

> 表中 LaTeX 片段为避免 Markdown 表格竖线冲突，把 `\|` 写成等价的 `\lVert ... \rVert`（LaTeX 语义相同）。§B 给出多行片段的完整可粘贴块。

### A.0 R2.1 — 标题收窄

| ID | 位置 | 现文（逐字） | 建议新文 | 为什么满足审稿人 |
|---|---|---|---|---|
| **T** | `main_nc.tex:28`、`main_springer.tex:36`、`highlights_nc.tex:11`、`cover_letter*.tex:24` | `Protect, Don't Perturb: From Empirical Regularities to a Dynamical Theory of Cross-Modal Alignment under PEFT` | **（推荐 T1）** `Adaptation Site and the Modality Gap: Empirical Regularities and a Gradient-Flow Theory for PEFT of Contrastive Dual-Encoders` | 祈使句 `Protect, Don't Perturb` 是**处方**，且 `under PEFT` 把结论推广到整个 PEFT 家族；T1 主语换成**被测的量**（adaptation site），并把适用范围写进标题（contrastive dual-encoders）。R2 的原话只是"标题概化过度"，本改法直接移除了那个概化成分，而**保留**了"经验规律 + 动力学理论"的实质。备选 T2/T3 见 §B.1 |

### A.1 R1.4 — 过强概化句（16 处，逐句替换）

**A 组：适用范围宽于证据（12 处）**

| ID | 位置 | 现文（逐字） | 建议新文 | 为什么满足审稿人 |
|---|---|---|---|---|
| **G1** | `discussion.tex:20` | `These principles require no architectural modification and apply to any contrastive vision-language backbone.` | `These principles require no architectural modification, and their scope is the setting we measured: contrastive dual-encoders trained with an InfoNCE objective, over the adaptation sites, ranks and two retrieval corpora of Section~\ref{sec:validation}. They do not extend to other encoder families, to non-contrastive objectives such as SigLIP's pairwise sigmoid, or to generation-oriented objectives, and we do not claim that they do.` | R1.4 针对的正是 "applies to any" 句式。改后把"我们测了什么"写成前提，并**显式否定**外推（借用 `paper_a1/main.tex:82` 的 `for no other families` / `we do not make the corresponding claims` 写法） |
| **G2** | `discussion.tex:15` | `\item \textbf{Use text-only fine-tuning as the default.} The theory shows this is not an empirical quirk but a consequence of $g_v = 0$ eliminating the dominant perturbation source. Text-only requires no additional implementation and provides guaranteed alignment protection.` | `\item \textbf{On the contrastive backbones measured here, text-side adaptation is the safer default for gap preservation.} For a given allocation, the theory says why the text-only position removes the dominant perturbation term ($g_v = 0$). That is a statement about a given allocation, not a prediction of which allocation an optimiser will find, and Section~\ref{sec:validation} shows the ordering is not preserved on SigLIP. The recommendation is therefore conditional on the encoder family, and it concerns the gap rather than retrieval: on the two B/32 backbones the arm that minimises the gap is the one that retrieves worst.` | 删掉 `as the default`（无条件处方）与 `guaranteed`（保证）；补上论文自己已有的事实——SigLIP 反向、B/32 上"gap 最小 ≠ 检索最好"。这两句在 `validation.tex:126` 与表注 `tab:position_strict` 里已经写了，改后**内部一致** |
| **G3** | `conclusion.tex:9` | `$\alpha$ is universally negative for PEFT, and $\beta$ is stable across PEFT and full fine-tuning under matched settings ($\beta_{\text{full}} = 0.159$).` | `$\alpha$ is negative in every fitted LoRA configuration in the archived set, on both datasets, and $\beta$ is stable between PEFT and full fine-tuning under matched settings ($\beta_{\text{full}} = 0.159$). This is a property of the configurations measured, not of PEFT as a class: in the archived Adapter fits $40$ of $50$ $\alpha$ values are negative and $10$ are not, and the CLIP BitFit boundary case sits at $\alpha \approx +4\times10^{-4}$.` | **现句与归档矛盾**：`universally` 不成立（§6-P3）。改后仍是正面结论，但把范围钉死在可核的集合上 |
| **G4** | `introduction.tex:13` | `This ODE yields explicit predictions for the full gap trajectory and steady state $DG^*_\infty = DG_0 + \alpha/\beta$ for any PEFT configuration, requiring only the computation of $\Gamma_m$ at initialization.` | `The ODE has a closed-form solution for the full gap trajectory and steady state $DG^*_\infty = DG_0 + \alpha/\beta$. Whether that closed form can be evaluated \emph{before} training is a separate question, and our measurements say that it cannot yet: Section~\ref{sec:discussion} reports that the predicted steady state is biased and that the predicted ordering across configurations is not reproduced, which is why the coefficients reported in Section~\ref{sec:validation} are fitted per run rather than computed at initialization.` | "for any PEFT configuration / requiring only $\Gamma_m$ at initialization" 与 limitation 第六、七条**直接冲突**（论文明说闭式预测有偏、不报闭式值）。改后移除矛盾，并把否证写进 Introduction——正好回应 AE 的 "unreliable generalization" |
| **G5** | `introduction.tex:21` | `We derive Gap Susceptibility $\Gamma_m$ and the first-order ODE governing gap dynamics from gradient flow, providing a unified explanation for all empirical findings. The theory yields explicit predictions without training and recovers prior empirical results as special cases.` | `We derive Gap Susceptibility $\Gamma_m$ and the first-order ODE governing gap dynamics from gradient flow, and show that the empirical regularities of Section~\ref{sec:empirical} follow from it for a stated allocation of perturbation. The gradient-flow identity is exact at the level of a single optimiser step and is verified directly (Section~\ref{sec:theory}); the trajectory-level coefficients $\alpha$ and $\beta$ are fitted per run rather than predicted from gradients, for the reasons set out in Section~\ref{sec:discussion}.` | `all` + `predictions without training` 两句都超出证据。改后把"精确的部分"（单步恒等式，$0.998$）与"拟合的部分"（$\alpha,\beta$）分开——这正是审稿人要的"区分自洽检查与独立验证" |
| **G6** | `theory.tex:119` | `The task gradient concentrates in a low-dimensional subspace regardless of the adapter's capacity. ... This finding has implications beyond our framework, suggesting that commonly used moderate ranks ($r \geq 16$) may be excessive for many vision-language tasks.` | `Within the rank grid measured here ($r \in [1,64]$, CLIP on Flickr30k and MS-COCO), the task gradient concentrates in a low-dimensional subspace and its norm does not grow with configured rank. We term this \textbf{Effective Rank Saturation}, and it implies that beyond a minimal rank threshold, increasing LoRA rank adds parameter freedom without adding gradient capacity in these runs. The claim is bounded by the grid: task, corpus size and encoder family were not varied, so this is a regularity of these configurations rather than a property of vision-language adaptation in general.` | `regardless of` + `many vision-language tasks` 是把单网格结论写成普适律。改后给出网格边界（$r\in[1,64]$、CLIP、两个检索语料），删除"超出本框架"的外推 |
| **G7** | `validation.tex:86` | `This \textbf{Effective Rank Saturation} reveals that the task gradient concentrates in a low-dimensional subspace regardless of adapter capacity.` | `This \textbf{Effective Rank Saturation} shows that, over the ranks measured here, the task gradient concentrates in a low-dimensional subspace and its norm is largely insensitive to adapter capacity.` | 同一句在本文件里另有"across all ranks"的局部用法，删 `regardless of` 即可与证据对齐，不损失论证力 |
| **G8** | `validation.tex:109` | `$\alpha$ is consistently negative for all PEFT configurations on both Flickr30k and COCO, confirming that the protective bound generalizes across datasets.` | `$\alpha$ is negative in every fitted LoRA configuration on both Flickr30k and COCO, so the sign of the protective bound is reproduced on a second corpus. What the second corpus does not supply is an independent retrieval test: on these MS-COCO runs retrieval is at chance (Section~\ref{sec:protocol}), so the COCO evidence bears on the gap trajectory rather than on the gap--retrieval association.` | ① `generalizes` 是概化动词，且只有两个语料；② 更要紧的是 COCO 那批 run 的 $R@1 = 0.0002$ 必须同时披露（见 §A.4），否则这句会被读成"跨语料检索也成立" |
| **G9** | `validation.tex:167` | `Together, these constitute a closed theoretical explanation for the empirical phenomena, validated by 383 experiments spanning three PEFT methods (LoRA, Adapter, BitFit) and two datasets.` | `Together, these constitute one explanation for the empirical phenomena of Section~\ref{sec:empirical} under a stated allocation of perturbation, tested against 383 experiments spanning three PEFT methods (LoRA, Adapter, BitFit) and two datasets. It is not a closed account, and Section~\ref{sec:discussion} lists what it does not yet supply: a predicted steady state, a predicted ordering across configurations, and a rule for which allocation an optimiser will choose.` | `closed theoretical explanation` 与本节后文并列的九条 limitation 自相矛盾。改成"一个解释 + 明列未解决项"，把 AE 的 "unsubstantiated ... claims" 转成主动披露 |
| **G10** | `discussion.tex:56` | `The ODE's steady-state prediction $DG^*_\infty = DG_0 + \alpha/\beta$ can be evaluated at initialization, enabling pre-hoc configuration selection without training---a capability that would complement IIMM's task-level predictions with configuration-level precision.` | `The ODE's steady-state prediction $DG^*_\infty = DG_0 + \alpha/\beta$ would, if it could be computed from gradients at initialization, allow configuration selection without training. Our measurements do not yet support that use: with coefficients predicted rather than fitted, the final $DG^*$ is biased low and the configuration ordering is not reproduced (limitation six above), so closed-form evaluation is a target for future work rather than a capability of the present framework.` | **内部矛盾**：同文件 limitation 第六条刚说"排序不可靠、闭式预测有偏"，紧接着把闭式预测当作未来能力。改后两处一致，并顺手压掉与 IIMM 的隐含比较 |
| **G11** | `main_nc.tex:54--56`；`main_springer.tex:57--59` | `Three consequences follow: adaptation position, since removing the visual gradient term removes the dominant perturbation source; a protective bound for LoRA across ranks; and a task gradient whose effective dimension is set by task structure rather than configured rank.` | `Three consequences follow: for a given allocation of perturbation, adaptation position, since removing the visual gradient term removes the dominant term in that allocation; a protective bound for LoRA across the ranks tested; and, across the rank grid measured here, a task gradient whose effective dimension does not grow with configured rank.` | 摘要里的 "effective dimension is set by task structure rather than configured rank" 是 ERS 的最强表述（同 G6/G7）。加两处限定词即可，摘要长度几乎不变 |
| **G12** | `main_springer.tex:53--55` | `The resulting first-order ODE has a perturbation force that follows from that coupling, and a restoring coefficient that is stable within PEFT while its full-fine-tuning estimate varies with batch. The ODE predicts the full gap trajectory at mean $R^2 = 0.986$ over the LoRA configurations across all tested LoRA configurations, against $0.00$ for a constant baseline and $0.946$ for a linear one.` | `The resulting first-order ODE has a perturbation force that follows from that coupling, and a restoring coefficient that is stable within PEFT while its full-fine-tuning estimate varies with batch. Fitted per run, the ODE reproduces the full gap trajectory at mean $R^2 = 0.949$ over the LoRA runs ($0.953$ on Flickr30k, $0.903$ on MS-COCO), against $0.00$ for a constant baseline and $0.946$ for a linear one.` | **两个问题**：① `0.986` 在归档里**没有任何来源**（`ode_ledger.json:subsets.lora.mean = 0.9486`，$n=55$，**max $=0.9773$**——均值不可能高于该集合的最大值）；② `predicts` 与该稿自己的 limitation 第五条冲突（系数是拟合的）。改后与 `main_nc.tex:51--52` 完全一致，两份主文件不再互相矛盾 |

**B 组：支持强度超过实际支持（4 处）**

| ID | 位置 | 现文（逐字） | 建议新文 | 为什么满足审稿人 |
|---|---|---|---|---|
| **B1** | `empirical.tex:19` | `\textbf{text-only fine-tuning overwhelmingly preserves cross-modal alignment}` | `\textbf{text-only fine-tuning shows the smallest gap increase on every dataset measured in this subsection}` | `overwhelmingly` 是修辞级强度；改成与表注 `tab:position` 一致的、可核的表述（"每一行都是 text-only 最小"确实是被表支撑的） |
| **B2** | `empirical.tex:176` | `(3) \textbf{Full fine-tuning should be avoided for retrieval tasks}---it uniformly degrades alignment regardless of data volume.` | `(3) \textbf{Full fine-tuning is the most damaging option in the retrieval runs measured here}, degrading alignment in every one of them; we did not vary data volume, so we cannot say how the effect scales with it.` | `uniformly` + `regardless of data volume` 两者都没有对应实验（数据量从未作为因子扫描）。改后把"没测的"如实写成没测 |
| **B3** | `introduction.tex:5` | `These findings, collectively termed the Visual Fragility Interpretation, suggest that visual embedding spaces are inherently more sensitive to parameter perturbation than text spaces.` | `These findings, collectively termed the Visual Fragility Interpretation, are evidence consistent with visual-side parameters being the more consequential of the two for alignment under the configurations measured. They are not evidence that visual embedding spaces are intrinsically more noise-sensitive, and the one probe that tested that reading directly found no stable ordering between the two encoders (Section~\ref{sec:empirical}).` | ① `inherently` 是机制性断言；② **与论文自己的证据相反**：`empirical.tex:144` 记录修正后的噪声探针给出 vision $1.90\pm1.83\%$ vs text $2.48\pm3.25\%$，即 text 侧名义上更敏感、该证据线**已撤回**。原句会让审稿人认为没读自己的结果 |
| **B4** | `introduction.tex:20` | `and the Visual Fragility Interpretation, supported by strict-freezing controls and spectral evidence.` | `and the Visual Fragility Interpretation, supported by strict-freezing gradient and effective-rank controls (one earlier noise-sensitivity line is withdrawn rather than used).` | `spectral evidence` 在 §`Visual Fragility` 的三条证据线（噪声已撤回 / 梯度 / 有效秩）里**没有对应物**。改成实际存在的两条，并主动写出撤回事实——正是 R2.4/R3.3 要的"控制不足"回应 |

---

### A.2 R2.2 — 与先前工作的新颖性区分（新增 1 段 + 1 个可选句）

| ID | 位置 | 现状 | 建议 | 为什么满足审稿人 |
|---|---|---|---|---|
| **N1** | `related_work.tex` 末尾（现文件共 53 行，插在第 49 行那段之后、`\subsection{Surveys and Broader Context}`（第 51 行）之前），作为新小节 `\subsection{What This Paper Adds}` | 现有 related work 只做**逐篇陈述**，没有把"本文与它们的差别"集中写成一段；R2.2 说新颖性区分不足 | 见 §B.2 的完整 LaTeX 段 | 该段按**三条最接近的脉络**各给一个明确对照点：① 解释来源（预训练期）vs 本文（下游 PEFT 期的变化率）；② 用 gap 做事的**器件**（Gap-Init / TPC-CMA / IIMM）vs 本文的**可被否证的耦合系数 + ODE**；③ 报告不对称现象 vs 本文给出系数并证明方向不固定。三点都指名具体文献，并**主动说明本文在哪两处已被否证**——把"novelty 不足"转成"novelty 在哪、边界在哪" |
| **N2**（可选） | 同上段末句 | — | `Relative to the empirical characterisation that this work extends, the dynamical theory is the new component, and the empirical sections here are re-measured under the strict-freezing protocol rather than restated.` | 直接回应"合并稿相对前任稿的新增是什么"。**是否写进正文由 Lead 定**：前任稿已在投稿信中披露（`cover_letter*.tex:78`），若希望正文保持不引用自身先前工作，删掉此句即可，N1 段落不依赖它 |

---

### A.3 R2.4 / R3.3 — 九个 `Visual Fragility` 出现点的逐处处置

`Visual Fragility`（大小写不敏感）在**现行 `paper合/sections/*.tex` 中恰好 9 处**（`NC_submission` 镜像另计 9 处）。逐处建议：

| # | 位置 | 现文（逐字节选） | 处置 | 建议新文 / 说明 |
|---|---|---|---|---|
| **V1** | `empirical.tex:140`（小节标题） | `\subsection{Visual Fragility Interpretation}` | **保留，但给标签加限定** | `\subsection{The Visual Fragility Interpretation (an Interpretation, Not a Mechanism)}` —— 标题层面就把它标成"解释"，避免读者在读到 §150 的免责声明之前先接受它是机制 |
| **V2** | `empirical.tex:142` | `We propose the \textbf{Visual Fragility Interpretation}: intervening on the visual side of a vision-language model is what damages cross-modal alignment, whereas leaving it untouched preserves it.` | **必改**（因果措辞最重的一处） | `We use the term \textbf{Visual Fragility Interpretation} for the following reading of the evidence: the alignment benefit we measure is consistent with the adapters' position rather than with the direction of updates to the vision tower, since under strict freezing the text-only arm leaves the vision side untouched by construction. The reading is a description of what the measurements are consistent with, not a demonstrated cause, and Section~\ref{sec:theory} states the condition under which it would follow from gradient geometry.` |
| **V3** | `empirical.tex:150`（前句） | `We emphasize that Visual Fragility is a phenomenological interpretation supported by the evidence above, not a deductively proven mechanism.` | **保留**（已经是合格限定） | 建议在句末补一个可证伪条件，强度更足：`...not a deductively proven mechanism; the measurement that would falsify it is a vision-side intervention that leaves the gap trajectory unchanged, and we report the one probe that failed to support it above.` |
| **V4** | `empirical.tex:150`（后句） | `Section~\ref{sec:theory} provides the formal framework that explains \emph{why} visual fragility emerges from gradient geometry.` | **必改**（与 `validation.tex:161` 冲突） | `Section~\ref{sec:theory} provides the formal framework within which the size of the visual-side perturbation term can be stated for a \emph{given} allocation of perturbation. It does not predict which allocation an optimiser will find, which is why the direction is measured rather than derived (Section~\ref{sec:validation}).` |
| **V5** | `introduction.tex:5` | `...suggest that visual embedding spaces are inherently more sensitive to parameter perturbation than text spaces.` | **必改**（= 主表 B3） | 见 B3。此处的 `inherently` 是全文对 Visual Fragility 最强的机制性表述，且与已撤回的噪声探针结论相反 |
| **V6** | `introduction.tex:20` | `...and the Visual Fragility Interpretation, supported by strict-freezing controls and spectral evidence.` | **必改**（= 主表 B4） | 见 B4：`spectral evidence` 无对应证据线 |
| **V7** | `conclusion.tex:5` | `...and that what damages cross-modal alignment is intervening on the visual side rather than adapting the language side (Visual Fragility Interpretation, supported by strict-freezing controls).` | **必改**（结论处的因果句，最易被引作 claim） | `...and that across the contrastive backbones measured here, the ordering of the three adaptation sites is consistent with visual-side intervention being the more consequential of the two for alignment rather than with language-side adaptation (Visual Fragility Interpretation, Section~\ref{sec:empirical}).` |
| **V8** | `supplement.tex:37`（附录 B 标题） | `\section*{B. Visual Fragility Evidence}` | **保留，改一个词** | `\section*{B. Evidence Behind the Visual Fragility Interpretation}` —— 标题从"证据"（暗示已证实）改为"某解释背后的证据" |
| **V9** | `supplement.tex:39` | `...give the weight-level evidence for the Visual Fragility Interpretation, ...` | **保留，改一个词** | `...give the weight-level measurements relevant to the Visual Fragility Interpretation, ...` —— 与 V8 一致 |

**汇总**：9 处中 **5 处必改**（V2、V4、V5、V6、V7，其中 V5/V6 同时是主表 B3/B4）、**3 处轻改**（V1、V8、V9）、**1 处保留并加强**（V3）。
**术语本身是否换名**（如改为 "visual-side perturbation sensitivity"）**不建议**：那要动 9 处正文 + 交叉引用 + 补充材料，收益低于成本，且 V1/V8 的限定已足够。

---

### A.4 R1.5 / R2.5 — DG 监控定位：核查结果与残留

| ID | 核查项 | 实测结果（2026-10-12） | 处置 |
|---|---|---|---|
| **D1** | `zero-overhead` / `zero overhead` 是否残留 | **0 处**（全部 `paper合/**/*.tex`，含 `main*.tex`、`cover_letter*.tex`） | 无需改；R1.5 的 "zero-overhead 不实" 在合并稿中已不存在 |
| **D2** | `DG-ES`（DG-Guided Early Stopping）是否残留 | **0 处**。唯一命中在 `paper合/figures/_superseded/fig5.svg`（SVG 里的图内文字），而该目录**没有任何 `\includegraphics` 引用**（`grep 'fig5|_superseded'` 在 `paper合/**/*.tex` 命中 0） | 无需改。**建议**顺手把 `figures/_superseded/` 从投稿包剔除以绝后患（不是必须） |
| **D3** | 是否已把"监控 ≠ 停止"写清 | **已写清**：`discussion.tex:17` 末句 `Monitoring DG and stopping on DG are therefore different claims, and only the first is supported here.`，并给出 $42\%$（$40/96$）与"5 条可实现停止规则在至少 $88$ 个可比 run 上更差" | 保留。这是比"重新定位为 PoC"更强的处理，**不需要**再加 PoC 段 |
| **D4** | 是否需要把 PoC 写进 limitation | **不需要新增 PoC 段**；但**有一处残留必须处理**：`discussion.tex:56`（= 主表 G10）"enabling pre-hoc configuration selection without training" 重新把 DG 系结论当作可用能力，且与 limitation 第六条冲突 | 按 G10 替换即可。若 Lead 仍想加一句保险，可在 limitation 列表中追加：`Tenth, we report the DG trajectory as a diagnostic and propose no stopping rule; the five realisable stopping rules we tested were not better than training to convergence, so no decision-rule claim is made anywhere in this paper.`（不引入新数字） |
| **D5** | 数字溯源缺口（供 Lead 决定） | `discussion.tex:17` 的两个数字里，$42\%$ 有归档（`outputs/analysis/monitor_dg_check3.json::argmin_agree_rate = 0.4167`，$n=96$），而 **`88 of 94` 在 `outputs/` 下没有对应归档文件**（来源是 HANDOFF 记录的 v2 实验，见 `HANDOFF.md:4059`） | 按项目「所有数据必须可复现有来源」的规矩，该数字**要么补一个命名归档、要么删除**。删掉后的句子仍完整：`...and each of five realisable stopping rules derived from the DG trajectory ends at a centroid gap worse than training to convergence.` |

---

### A.5 R3.4 — 检索协议澄清（新增 1 段 + 表注补充）

| ID | 位置 | 现状 | 建议 | 为什么满足审稿人 |
|---|---|---|---|---|
| **P1** | `empirical.tex` §Experimental Design 末尾（现第 15 行末，`The complete experiment catalog (383 experiments) is provided in Appendix~A.` 之后）新增一段 `\textbf{Retrieval protocol and its exceptions.}` | 现行稿**只披露了 BLIP-1 的 "R@1 near-random (test set 5K images)"**（`supplement.tex:3` 表注），**没有披露**：① COCO 那批 run 的 $R@1 = 0.0002$；② BLIP-1 用的是**选择性解冻**而非 LoRA 注入；③ 三个非 Flickr30k 行的 $R@1$ 都在随机水平附近 | 见 §B.3 完整 LaTeX 段 | 直接回答 R3.4 的两个点名项（COCO 检索口径 + BLIP-1 选择性解冻），并且把口径说成"三个例外 + 每条的依据"。**关键是主动给出 $R@1$**：审稿人当初就是从 $R@1<0.001$ 推出"跨架构概化过强"的，把数字摆到正文比留在补充材料更可信 |
| **P2** | `empirical.tex:32` 表 `tab:position` 的表注 | 现表注只讲了"早期约定、不隔离 siting choice"，未给检索质量 | 在表注末尾追加：`Recall@1 on these runs is $0.627$, $0.700$ and $0.676$ on the three Flickr30k rows, $0.0002$ on all three COCO rows, $0.001$ and $0.002$ on the two BLIP-1 rows, and $0.0050$ and $0.0025$ on the two ViT-L rows; the retrieval-protocol paragraph in the text explains why those rows carry gap evidence only.` | 让读者在**看到表格的那一页**就知道哪些行不能当检索证据用，避免"表格里并排列出 = 同等可信"的误读 |

---

### A.6 R3.1 — 摘要/结论数值与表格一致：三个数各指哪个 run

| ID | 位置 | 现文（逐字） | 建议新文 | 为什么满足审稿人 |
|---|---|---|---|---|
| **Q1** | `empirical.tex:19`（`+0.079` 所在句） | `Full fine-tuning increases CG by 24\% and collapses zero-shot accuracy to near-chance levels (mean $2.6\%$ over 3 retrained seeds), while text-only LoRA limits CG increase to $+0.079$ and zero-shot degradation to $0.6$ percentage points.` | `Full fine-tuning increases CG by 24\% and collapses zero-shot accuracy to near-chance levels (mean $2.6\%$ over 3 retrained seeds). The text-only figures in this paragraph come from three different runs and should not be combined. The Route~D scaling study's $\alpha{=}64$, $r{=}8$ text-only run increases CG by $+0.079$ while retrieving $R@1 = 0.389$; the default text-only run of Table~\ref{tab:position} \emph{reduces} CG by $-0.064$ while retrieving $0.627$; and the ImageNet zero-shot run changes CG by $-0.066$ with top-1 $58.66\%$ against a frozen $59.28\%$, a drop of $0.6$ points. The sign difference is a difference of configuration, not a contradiction.` | **这正是 R3.1 的质问**："$+0.079$ 与表格 $-0.064/-0.066$ 是否同一配置"——答案是**三个不同 run**（详见 §6）。原句把 $+0.079$（Route D，$\alpha{=}64$）与 $0.6$ 个百分点（ImageNet run）拼在一句里，读者无法核。改后每个数字自带配置与出处 |
| **Q2** | `main_nc.tex:41--43`（摘要） | `Across $n=204$ archived experiments the Distribution Gap predicts retrieval degradation ($r=-0.71$) more strongly than the Centroid Gap ($r=-0.59$), and which part of the model is adapted matters more than how its adapters are configured.` | 保留数字，**建议**在 `discussion.tex:17` 的 $r=-0.71$ 后补 `($n=204$ over the archived table, $n=96$ over the monitored trajectories$)` | 摘要的 $r=-0.71$ 对应 $n=204$（`tab:corr`），`discussion.tex:17` 的 $r=-0.71$ 对应 $n=96$（`monitor_dg_check3.json::corr_dg0_r1 = -0.7081`）。**两个不同的量、四舍五入后同为 `-0.71`**，容易被当成同一数字被两处引用错。补 $n$ 即可区分，不需要改任何数字 |
| **Q3** | `validation.tex:4 / 30 / 39`、`conclusion.tex:9`、`introduction.tex:22`（"43 on Flickr30k, 6 on MS-COCO"） | 五处都写 55 个 run = 43（Flickr30k）+ 6（MS-COCO） | **不改数字，只提请 Lead 核** | `outputs/analysis/ode_ledger.json::subsets` 给的是 `lora n=55`、`lora_flickr n=49`、`lora_coco n=6`；$43+6=49\neq 55$，而 `tools/_claim_ledger.py:219` 用 $0.002$ 容差读 `lora_flickr.mean`，所以**计数不符被容差掩盖了**。这是 R3.1 同类的"数字与表格不一致"，但**我无法从归档判定 43 还是 49 对**——需 Lead 指名脚本后统一 |

---

## B. 可直接粘贴的 LaTeX 块（多行片段）

### B.1 R2.1 标题：三个候选 + 推荐

```latex
% T1 —— 推荐
\title{Adaptation Site and the Modality Gap: Empirical Regularities and a
Gradient-Flow Theory for PEFT of Contrastive Dual-Encoders}

% T1 的 Springer 短标题
\title[Adaptation Site and the Modality Gap]{Adaptation Site and the Modality Gap: Empirical Regularities and a Gradient-Flow Theory for PEFT of Contrastive Dual-Encoders}

% T2
\title{From Adaptation Site to Gap Dynamics: Modality-Gap Regularities and
Their Gradient-Flow Theory under PEFT of Contrastive Dual-Encoders}

% T3
\title{The Modality Gap under PEFT of Contrastive Dual-Encoders:
Adaptation-Site Regularities and a First-Order Dynamical Theory}
```

**推荐 T1**，理由三条：

1. **移除了处方**。`Protect, Don't Perturb` 是祈使句，在标题层就宣称一条行动准则；审稿人只能把它读成"普适原则"，而正文证据是 4 个对比双塔 + 1 个解码器 VLM 的局部检验。
2. **把范围写进标题**。`PEFT of Contrastive Dual-Encoders` 明确了模型族与方法类；解码器 VLM 与 SigLIP 反向这两件事在标题里就不会被读成反例。
3. **保住了实质**。"Empirical Regularities" + "Gradient-Flow Theory" 两半都在，与 `introduction.tex:17` 的 "complete arc from empirical discovery to theoretical explanation" 与 `main_nc.tex` 摘要的三段结构对得上。

T2 的优点是保留 `From ... to ...` 的原文节奏；T3 最短、最中性，适合期刊字数敏感时使用。三者都**不含** `Protect`、`any`、`universal` 或无条件祈使。

### B.2 R2.2 新颖性段落（插在 `related_work.tex` 第 49 行之后）

```latex
\subsection{What This Paper Adds}
\label{sec:novelty}

Three strands above are close enough to the present contribution that the difference
should be stated rather than implied. The first explains where the gap \emph{comes from}:
dimension collapse~\cite{yi2025decipher}, the persistent negative divergence
term~\cite{cai2026geometric} and the gradient-flow account of pre-training~\cite{yaras2026explaining}
all locate its origin in the contrastive objective while the two encoders are being
trained together. This paper starts after that stage, with a frozen pre-trained pair and
an adapter, and asks about the rate at which the gap moves rather than about its origin.
The second strand uses the gap to act on training: Gap-Init~\cite{zhao2026gapinit} aligns
an initialisation with the gap vector, TPC-CMA~\cite{liu2026tpc} uses a centroid/distribution
decomposition for training control, and IIMM~\cite{niss2025iimm} predicts an outcome from a
single forward pass. Those are devices, and what they are judged on is whether they help.
The object derived here is a coupling coefficient,
$\Gamma_m = \lVert\nabla_m DG^*\rVert\cos\phi_m$, and the first-order ODE it generates,
which is meant to be falsifiable rather than useful --- and is reported as falsified in two
places in Section~\ref{sec:validation}. The third strand reports the asymmetry we also
report:~\cite{chen2026dominance} argue that visual-side adjustment is what damages
alignment, and~\cite{sharma2026readout} find that gap interventions help some tasks and
hurt others. What this paper adds there is a measured coefficient behind the asymmetry and
a demonstration that its direction is not fixed, since the same text-side intervention
reduces the gap on one pre-trained pair and increases it on another
(Table~\ref{tab:position_strict}).

% ——— 可选句（是否保留由 Lead 定；前任稿已在投稿信 78 行披露）———
% Relative to the empirical characterisation that this work extends, the dynamical
% theory is the new component, and the empirical sections here are re-measured under
% the strict-freezing protocol rather than restated.
```

### B.3 R3.4 检索协议段（插在 `empirical.tex` 第 15 行之后）

```latex
\textbf{Retrieval protocol and its exceptions.} Recall@$K$ is computed once per evaluation
loader from the full $N\times N$ similarity matrix, with the correct pairing taken as the
diagonal, so $R@1$ at chance is $1/N$. Three rows of Table~\ref{tab:position} were produced
under conditions that a reader of the table cannot infer, and we state them here rather than
leave them to be discovered.

(i) \emph{MS-COCO.} The evaluation loader is the COCO validation split under the same
\texttt{max\_samples} cap as training, so recall on these runs is measured over $5000$
caption rows. On those runs the recorded $R@1$, $R@5$ and $R@10$ are exactly $1/N$, $5/N$
and $10/N$, i.e.\ retrieval is at chance, and the COCO row of Table~\ref{tab:position}
should therefore be read as a gap measurement only.

(ii) \emph{BLIP-1.} LoRA injection through the adapter library is not available for the
model class used, so those arms were produced by \emph{selective unfreezing} of the
\texttt{query} and \texttt{value} projections rather than by injecting LoRA matrices
(\texttt{experiments/blip2\_experiments.py}, line~369, records the substitution). Both arms
expose the same number of trainable parameters ($196{,}672{,}514$), so the comparison is
between two choices of what to unfreeze rather than between two adapter placements, and it
is not directly comparable with the LoRA rows. Its $R@1$ is $0.001$--$0.002$ against a
chance level of $0.0002$ on a $5$K test set.

(iii) \emph{ViT-L.} The two ViT-L runs are likewise near chance ($R@1 = 0.0050$ and
$0.0025$). None of the three exceptions is used as evidence about retrieval; they are
reported because the gap measurements in those rows would otherwise be read as if they came
from the same protocol as the Flickr30k rows.
```

### B.4 R3.4 表注补充（`empirical.tex` 表 `tab:position` 的 `\caption` 末尾追加）

```latex
Recall@1 on these runs is $0.627$, $0.700$ and $0.676$ on the three Flickr30k rows, $0.0002$ on
all three COCO rows, $0.001$ and $0.002$ on the two BLIP-1 rows, and $0.0050$ and $0.0025$ on
the two ViT-L rows; the retrieval-protocol paragraph in the text explains why those rows carry
gap evidence only.
```

---

## C. 为什么这样改能满足各条审稿意见（短理由段）

**R2.1（标题）**：审稿人质疑的不是标题的措辞，而是**标题承诺的范围**。三个候选都做了同一件事：把"该怎么做"换成"我们测了什么"，并把模型族写进标题。这比在正文里加免责句更有效——标题是唯一一定被读到的地方，也是唯一会被引用与索引的地方。

**R1.4（概化过强）+ R3.1（数值不一致）**：这两条在审稿人那里是一件事的两面——"结论太宽"与"数字对不上"。§A.1 的 16 处改动全部遵循同一写法：**先给被测集合，再给结论，最后显式写出不外推到什么**。其中三处（G3、G12、G10）不是修辞问题而是**与归档或与本稿其他段落矛盾**，改掉它们是硬性要求，不是风格偏好。G12 尤其重要：两份主文件的摘要给出 $0.986$ 与 $0.949$ 两个数，而 $0.986$ 高于归档 LoRA 集合的最大值 $0.9773$，审稿人只要抽查一处就会命中。

**R2.2（新颖性区分）**：原 related work 是"按文献陈述"的写法，读完无法回答"那你新在哪"。§B.2 的段落按**三条最接近的脉络**各给一个可检验的差别，并且让"本文已被否证两次"成为 novelty 论证的一部分——这与 `paper_a1` 的处理方式一致（该稿把 $r=1.000$ 主动降级为"自洽检查，非独立验证"，见 `paper_a1/main.tex:222--232`）。

**R2.4 / R3.3（Visual Fragility 被当因果）**：审稿人给的是两条（"仍描述性"、"过度声称因果"），处置不能只是加一句"这是现象学解释"——本稿在 `empirical.tex:150` **已经有**这句了，说明加免责词不够。§A.3 因此分三档：**V2/V4/V7 三处把因果动词换成"证据与……一致"**；**V5 修掉与自身撤回证据相反的"inherently"**；**V6 删掉没有出处的 "spectral evidence"**。剩下 4 处要么本来就是限定句（V3），要么只改标题措辞（V1/V8/V9）。改完 9 处没有一处还把 Visual Fragility 说成机制。

**R1.5 / R2.5（DG 监控）**：核查结论是**"已经不需要再定位为 PoC"**——`zero-overhead` 与 `DG-ES` 在全文各 0 处，且 `discussion.tex:17` 已把"监控"与"停止"拆成两句并给出负面证据（$42\%$ 一致率）。但正因为已经删干净，**残留的 G10（"pre-hoc configuration selection without training"）就成了唯一还在把 DG 结论当可用能力的地方**，而且它与同文件的 limitation 第六条冲突——这是本轮最容易被审稿人抓到的自相矛盾之一。

**R3.4（检索协议）**：审稿人点名的两件事都能在仓库里核实：COCO 的 $R@1 = 0.0002$（等于 $1/5000$）与 BLIP-1 的选择性解冻（脚本第 369 行有明确注释）。**主动写进正文**比等审稿人再问一次好：它同时消解了 R1.4 里"跨数据集概化"与"跨架构概化"的一半压力——因为那些行的证据本来就不是检索证据。

---

## D. 交给 Lead 的边界外事项（我不写这些文件）

1. **标题传播**：见 §0.2，6 处需同步；`cover_letter*.tex:78` 的**前任稿标题不要动**。
2. **前任稿稿号**：R3.1 还提到"封面信稿号与文件不符"。本合并稿的两封投稿信里**没有出现**前任稿的稿号 `PR-D-26-10149`（`cover_letter*.tex:78--83` 只写了"a predecessor manuscript under review at Pattern Recognition"）。建议在那一项补上稿号，让编辑可对照。
3. **页数**：`cover_letter_nc.tex:26` 写 "56 pages"，与 `AGENTS.md` 记录的 2026-10-06 编译 49 页不一致。**这是事实性声明，投递前必须用最终 PDF 实测后改**（我不推测最终页数）。
4. **架构计数**：`main_nc.tex:57` 摘要 "five architectures"、`conclusion.tex:3` "five model architectures"，而 `tab:position_strict` 有 **6 行**（CLIP B/32、OpenCLIP B/32、CLIP B/32$^\dagger$、CLIP B/16$^\dagger$、SigLIP、BioCLIP），`empirical.tex:176` 又自称 "a regularity over seven configurations"，Table 1 另含 CLIP ViT-L/14。"383 experiments over five architectures" 与这两个计数需要 Lead 统一口径（属 R2.3b 的延伸，不在我的条目内）。
5. **`88 of 94`**：`discussion.tex:17` 的这一数字在 `outputs/` 下无归档（见 D5）。补归档或删除。
6. **`figures/_superseded/`**：内含 `DG-ES` 字样的旧图，虽未被任何 `\includegraphics` 引用，建议不出现在投稿包中。

---

## 6. 数字溯源表（本文档所有数字的出处）

| 编号 | 数字 | 文件 : 字段 | 算式 / 值 |
|---|---|---|---|
| **P1** | $+0.079$ | `outputs/route_d/d1_alpha64_text_r8/results.json`（`final_gap.centroid_gap` − `initial_gap.centroid_gap`）；另存于 `outputs/master_results.json::experiments.route_d.d1_alpha64_text_r8.cg_delta` | $0.8975444436 - 0.8183733821 = 0.0791710615$；同 run `R@1 = 0.3890000134`；`n_trainable_params = 145170177` |
| **P2** | $-0.064$ | `outputs/flickr30k/rq2_text_only/results.json` | $0.7548404336 - 0.8183847666 = -0.0635443330$；`R@1 = 0.6270000041`；`n_trainable = 145170177` |
| **P3** | $-0.066$ | `outputs/imagenet_zs/text_only_r8/results.json` | $0.7522164583 - 0.8183194995 = -0.0661030412$；`n_trainable = 6500352` |
| **P4** | $-0.032$ | `outputs/flickr30k/rq2_both/results.json` | $0.7860594978 - 0.8184462786 = -0.0323867808$；`R@1 = 0.700` |
| **P5** | $-0.003$ / $0.676$ | `outputs/flickr30k/rq2_vision_only/results.json` | $-0.002890$；`R@1 = 0.676` |
| **P6** | $-0.041$ / $0.0002$ | `outputs/coco/rq2_text_only_coco/results.json` | $1.0125081539 - 1.0530576706 = -0.0405495167$；`test_metrics.R@1 = 0.00019999999494757503 = \mathrm{float32}(1/5000)$；`R@5 = 0.001 = 5/5000`；`R@10 = 0.002 = 10/5000` |
| **P7** | $-0.052$ / $0.0002$ | `outputs/coco/rq2_both_coco/results.json` | $1.000620 - 1.053058 = -0.052438$；`R@1 = 0.0002`；`n_trainable = 131290881` |
| **P8** | $+0.031$ / $0.0002$ | `outputs/coco/rq2_vision_only_coco/results.json` | $+0.031404$；`R@1 = 0.0002`；`n_trainable = 137398017` |
| **P9** | $+0.047$ / $+0.152$ / $0.0020$ | `outputs/blip2/b4_blip2_lora_text_only/results.json`、`outputs/blip2/b4_blip2_lora_both/results.json` | $1.776947-1.730051=+0.046896$；$1.930720-1.779129=+0.151591$；两臂 `n_trainable = 196672514`（相同）；`final_task_metrics.R@1 = 0.0020`，text-only 的 `test_metrics.R@1 = 0.0010` |
| **P10** | $-0.036$ / $+0.128$ / $0.0050$ / $0.0025$ | `outputs/vitl/vitl_text_only/results.json`、`outputs/vitl/vitl_rank4/results.json` | $-0.035608$（`R@1 0.0050`）；$+0.127908$（`R@1 0.0025`） |
| **P11** | BLIP-1 用选择性解冻 | `experiments/blip2_experiments.py:369` | 代码注释：`# BLIP-1 不支持 apply_lora_to_model，改用选择性解冻`；第 372--380 行对 `text_model`/`vision_model` 的 `query`/`value` 置 `requires_grad_(True)` |
| **P12** | COCO 评测集 = val，$N=5000$ | `src/dataset.py:374--437`（`create_dataloaders`：`if dataset_name == "coco": test_dataset = val_dataset`） | 记录值恰为 $1/N,5/N,10/N$ 的 chance 值 ⇒ $N = 5000$ |
| **P13** | Adapter $\alpha$ 符号：$40/50$ 负 | `outputs/theory/adapter/adapter_all_results.json`（逐条 `alpha`） | $n=50$，负 $40$，非负 $10$（最大 $+0.0608$） |
| **P14** | CLIP BitFit $\alpha$ | `outputs/theory/bitfit/bitfit_results.json` | $+0.0002, +0.0004, +0.0004$（三条），$R^2 = 0.298/0.599/0.843$ |
| **P15** | OpenCLIP BitFit $\alpha$ | `outputs/theory/openclip/openclip_results.json` | $-0.0020/-0.0018/-0.0016$（三条） |
| **P16** | LoRA $R^2$ 三条 | `outputs/analysis/ode_ledger.json::subsets` | `lora.mean = 0.9486154`（$n=55$，`max = 0.9773494`）；`lora_flickr.mean = 0.9541804`（$n=49$）；`lora_coco.mean = 0.9031678`（$n=6$）；`adapter.mean = 0.6694457`（$n=30$）；`full_ft.mean = 0.9217284`（$n=11$） |
| **P17** | $0.986$ 无归档来源 | 同上 + 全库检索 | `outputs/**/*.json` 中不存在 LoRA 均值 $0.986$；且 $0.986 > 0.9773494 = $ `lora.max` |
| **P18** | ImageNet 零样本 $59.28 / 58.66$ | `outputs/imagenet1k_zs_50k_verify.json`（`frozen = 59.28`，`text_only_r8 = 58.66`）；同值亦见 `outputs/imagenet1k_zs_50k_plain.json` | 差 $0.62$ 个百分点（正文写 $0.6$） |
| **P19** | $r=-0.7081$，$n=96$；$42\%$（$40/96$） | `outputs/analysis/monitor_dg_check3.json` | `corr_dg0_r1 = -0.7081100215`，`n_traj = 96`，`argmin_agree_rate = 0.4166667` |
| **P20** | $88/94$ 无 `outputs/` 归档 | `HANDOFF.md:4059`；`tools/_docs_exp5_gpu.py:36` | 仅文档记录，`outputs/` 下无对应文件 |
| **P21** | 严格冻结噪声探针 $1.90\pm1.83\%$ vs $2.48\pm3.25\%$，比 $0.77$ | `paper合/sections/empirical.tex:144`（正文自述）；配置来源同段所述五个种子 | 用于 B3 的"与本稿自身证据相反"论证 |
| **P22** | 梯度流恒等式 $0.998$ / 中位相对误差 $2.7\%$ | `outputs/analysis/claim_ledger.json` 已列；原始 `outputs/theory/gradflow_identity/identity_check.json::cos_pred_vs_actual / median_rel_err` | `0.9977` / `0.0270` |
| **P23** | `zero-overhead` / `DG-ES` 命中数 | 全库 `grep`（2026-10-12） | `paper合/**/*.tex` 各 **0** 处；`DG-ES` 仅在 `paper合/figures/_superseded/fig5.svg`，而该目录无 `\includegraphics` 引用 |
| **P24** | 镜像一致性 | `paper合/sections/*.tex` vs `paper合/NC_submission/latex_source/sections/*.tex` | 8 个 section + `main_nc.tex` SHA256 **全等**（2026-10-12 实测） |
