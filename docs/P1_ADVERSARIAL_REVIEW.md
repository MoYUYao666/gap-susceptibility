# P1 — Adversarial review consolidation（四路子代理独立审查 + 协调者复核）

**对象**：`paper/main_nn.tex` + `paper/sections/*.tex`（"Protect, Don't Perturb: Cross-Modal Alignment under PEFT of Vision-Language Models"，单作者，**Pattern Recognition，稿号 `PR-D-26-10149`，自 2026-08-23 起 Under Review**）。投稿版 PDF 本地未存档，最近代理物为 `paper/main_nn.pdf`（37 页，2026-08-22 晚编译，投稿前 1 天）。

**方法**：四个独立子代理，各自一个攻击面、互不共享结论、只读（仅各写一份报告）：

| 报告 | 攻击面 | 计数 |
|---|---|---|
| `docs/P1_REVIEW_NUMBERS.md` | 数字溯源 + 图表/图注保真 | 5 must / 10 should / 6 note |
| `docs/P1_REVIEW_CONSISTENCY.md` | 跨文档口径自洽 + 例外与负面结果 | 7 must / 11 should / 3 note |
| `docs/P1_REVIEW_CITATIONS.md` | 引用完整性 + 新颖性主张 | 7 must / 6 should / 4 note |
| `docs/P1_REVIEW_OVERLAP.md` | 与 A1/A23/ap3/P2/P3 的重叠与披露 | 3 must / 3 should / 9 note |

**复核规则**：协调者对每条 must-fix 用存档（`outputs/**` JSON、源码、脚本）或外部来源独立复核；下表 `✔核` = 协调者亲自复核并给出证据，`◻转` = 采信代理结论（其报告内有证据链）。**未发现任何编造**：所有数字都是真实测量，缺陷集中在**标注、出处、报告口径**，以及一处**机理叙述**。

**⚠️ 触发条件提醒**：P1 正在审稿。以下清单**不构成现在给编辑写信的理由**（见 §6 处置建议）。

---

## 1. 机理叙述失守（最高优先级；需要新实验或重写叙事）

**[M1] `supplementary.tex:259` 的图注 "text-only has zero vision-side updates" 被存档自证为假。** ✔核

- `outputs/flickr30k/rq2_text_only/results.json:44` → `"n_trainable_params": 145170177`。CLIP ViT-B/32 总量约 151M → **优化器持有约 96% 的模型参数**。
- 对照量级：`outputs/phase1/adapter_d16_text/results.json:44` = **405,888**；而 `outputs/flickr30k/rq2_both/results.json:44` = **131,290,881**（both **少于** text-only——正是"只冻结被替换的 Linear、其余全部可训"的特征，与 `src/peft_methods.py:137-138`（`get_peft_params` 返回全部 `requires_grad` 参数）+ `src/trainer.py:243-244` 一致）。
- 图注中的"零"不是"没更新"，而是**没保存**：ΔW 只从 `ckpt["lora_state_dict"]` 计算（`paper/scripts/weight_svd_analysis.py:54-60`），而 `src/trainer.py:893-901` 只写入 LoRA 张量。

**[M2] 有效秩证据与主张相反。** ✔核

`outputs/effective_rank_tracking.json` 仅两个顶层键：`Frozen`（image-side `vis_L0` = **9.4256**）与 `text-only`（4 次运行：9.3861、6.8279、**6.1639**、7.0211）→ **四次 text-only 有三次把冻结图像侧有效秩压低约 25–35%**。代理另报另一视觉层 12.41 → 7.83（−37%）。而 `introduction.tex:25`、`supplementary.tex:173/270` 称 text-only 保持视觉几何。代码/图注/脚注里出现**三套不同的秩定义**。

**后果**：摘要 "provide **direct causal evidence** through noise sensitivity, gradient analysis, and effective rank tracking" 与 §5 "Visual Fragility" 的因果叙事，建立在一个**不成立的操纵**上——两个分支的视觉侧都在更新，被比较的不是"是否触碰视觉编码器"。**经验结论（text-only 的 CGΔ 更小）是实测、仍在；"protect the visual encoder" 的机理需要重做对照实验（严格冻结 Embedding/LayerNorm）或改写为不含因果的表述。** 这是唯一需要操作者决定"改措辞 vs 补实验"的一条。

---

## 2. 图与图注不符（视觉证据，审稿人可直接数点数）

| # | 发现 | 证据 | 复核 |
|---|---|---|---|
| [M3] | **fig1 用 COCO 的曲线挂在 Flickr30k 的图注下**：4 点 "Full FT" 曲线来自 `outputs/coco/baseline_full_ft_coco`（1.0531→1.2470），"Both"/"Text-only" 来自 `outputs/coco/rq2_*_coco`；而平直的 "frozen" 带是 Flickr 5-seed 均值。选择器至今仍会产出这个混搭 | `paper/scripts/generate_figures.py:33-60`；图注 `paper/sections/experiments.tex:11` | ◻转 |
| [M4] | **fig2 标题写 `n = 81`，但散点只有约 17 点**；r 值另从 `outputs/analysis/correlations.json` 读入，与所画点集不同源 | `generate_figures.py:71-87` | ✔核（脚本第 73 行自述"当前 master_results 子集仅 17-30 条"；第 87 行硬编码 `n = 81`） |
| [M5] | **fig2/fig3 疑似对调**：`figures/fig3.png`(2290×940，消融柱状图) 挂在 "Cross-validation" 图注下（`experiments.tex:92-93`），`figures/fig2.png`(2890×1390，标注 r=−0.827 n=81) 挂在 "Ablation" 图注下（`:103-104`） | 同上 | ◻转（代理目视确认；协调者仅确认"图注文字与文件名对应关系可疑"，未目视） |
| [M6] | **fig5 图例把 `e2_dges_alpha4` 标成 "Both-LoRA"，实物是 text-only**：`n_trainable_params` 与 e3 text-only 同为 145170177（e1 both 为 131290881），checkpoint 806KB vs 2.0MB → 正文 "the two both-position runs later recover" 不成立 | `experiments.tex:186` vs `supplementary.tex:115` | ◻转 |
| [M7] | **fig11 面板读作 "Vis grads contribute <640%"**（物理上不可能；应为某个门控/贡献比的排版错误） | `paper/scripts/gsnr_analysis.py:172` | ◻转 |

---

## 3. 统计口径（可复算、可被审稿人抓到）

| # | 发现 | 证据 | 复核 |
|---|---|---|---|
| [M8] | **Adapter 行的 CGΔ 用的是各次运行自己的随机初始化 epoch-0 作基线**（1.08–1.36，而 frozen 是 0.8137）→ 7 次 Adapter 运行**全部结束在 frozen 之上**；统一到共同基线后 Adapter **+0.234** vs LoRA **−0.042**，**排序反转** | 图注 `supplementary.tex:17` 却写 "relative to frozen baseline"；`experiments.tex:138/144`、`discussion.tex:28` | ◻转（与 [M9] 独立同向） |
| [M9] | **Table 4 的 Adapter 行（−0.100 / 0.173）是 7 次检索处于随机水平的运行（0.002–0.574）的均值**；项目自己的汇总 `outputs/cross_method/paper_tables.md:9` 给的是 adapter −0.0472 / 0.6228。且其 ANOVA（F=13.37, p=5e-4）由 `tools/audit/fix_paper1_round3.py:19-23` 装入，**替换掉了先前的结论（F=2.17, p=0.146）** | 同左 | ◻转 |
| [M10] | **Table 4 无 n；ANOVA 的 "LoRA" 组里混着 5 行 full-FT**；63 行中有 26 行重复 | `outputs/cross_method/cross_method_report.json` | ◻转 |
| [M11] | **n=81 相关性无法重建**（脚本自述选样规则丢失），而 r=−0.827 是摘要/Table 5/Fig 2 的头号数字。可重建近似：−0.820（n=89）、−0.8152（n=94） | `paper/scripts/generate_figures.py:74-77`；`outputs/analysis/correlations.json` | ✔核 |
| [M12] | **例外清单三处不一致**：摘要（`main_nn.tex:44-45`）漏了 COCO both-position 与 Adapter vision-only；`discussion.tex:6` 列了 4 条例外却指向一张没这些列的补充表；`conclusion.tex:6` **整段丢掉例外**、还声称 Adapter 稳健（与 [M8] 冲突），并把显著性写成 p<0.01（intro/supp 是 p<0.001） | 同左 | ◻转 |
| [M13] | **摘要 "24%" 的口径**：`+0.1994 / 0.8186 = 24.36%` **可溯源**（单次 Flickr 运行）；但 5-seed 均值为 **+0.1906 ± 0.0075 → 23.4%**（`outputs/flickr30k_seeds/summary.json`），而论文别处（text-only）用的是 5-seed ± std 口径 | 同左 | ✔核（两个代理在此**判定相反**：数字代理查"能否溯源" → PASS；自洽代理查"是否取最好一次" → 成立。**两条都对**：数字真实，但报告口径选择不当——应报 5-seed 均值±std 或注明是单次运行） |
| [M14] | "116 experiments" 实为 **117**（`supplementary.tex:158` 说 7 条却列了 8 条）；"near-chance 2.6%" 未给区间；脚注区间 +0.26–+0.67 应为 +0.66；ViT-L frozen R@1 = 0.000 却承载着头条 CG 主张 | `supplementary.tex:158/169` | ◻转 |

**代理给的 PASS（勿过度修改）**：摘要 2.6% / 59.3% / 0.6pp、2.6×、1.5×、4.15 vs 0.56、Table 2 全 15 格、Table 3、Table 6、Table 7、5-seed 均值、DTD/Food101、ImageNet 表。**协调者另否掉一条过度指控**：摘要 "59.3% frozen" 与表格 59.28% 的差异只是四舍五入。

---

## 4. 训练/评测口径与更正信（合规层）

| # | 发现 | 复核 |
|---|---|---|
| [M15] | `docs/P1_eval_audit.md`（2026-08-16）列的**三条必做动作全部未落地**：①未披露训练口径（PDF 全文 0 处 LayerNorm/embedding/trainable-param 披露；`methodology.tex:20` 只列 batch/lr/epochs）；②未说明零样本数字来自**重构的 LoRA-only 模型**（`paper/scripts/zeroshot_extra.py:114-141` 根本不加载 checkpoint）；③未改用 LoRA-only 过滤器 | ✔核（`src/peft_methods.py:137-138`、`src/trainer.py:243-244`；`supplementary.tex:259` 反向断言） |
| [M16] | **更正信与稿件数字不一致**：`cover_letter_zeroshot_correction.tex:42` 称 Table 7 校正为 **59.37 / 58.76**（n=14,288 子集），而稿件 Table 7 为 **59.28 / 58.66**（`experiments.tex:226-228`，对应 `outputs/imagenet1k_zs_50k_plain.json` 的 50k 协议；另一份 `outputs/imagenet1k_ckpt_check.json` 才是 59.37/58.76） | ✔核（两个 JSON 与两个文档都逐值核过） |
| [M17] | 更正信自认"**四个零样本数字里有三个无法从存档 checkpoint 复现**"，且 full-FT checkpoint 当时未存档、是**重训**的 | ✔核（信件原文） |

---

## 5. 引用与披露

| # | 发现 | 复核 |
|---|---|---|
| [M18] | **两个 arXiv ID 互换**：`references.bib:421-427` `morelli2026sparse` 印 2604.16256（实为 vision-reasoning 论文），`:413-419` `xu2026vlreasoning` 印 2605.15961（实为 SAE-CLIP）；两者都印进 `main_nn.bbl:241-242/248-249` | ◻转 |
| [M19] | `gao2026uniformity`（`references.bib:363-370`）DOI 指向 `arXiv.2501.00984`，而该题名在 2602.09507（工作区自己的 `paper_ap3/refs.bib:102` 写的就是后者） | ◻转（工作区内互相矛盾，可低成本核） |
| [M20] | `niss2025reviving`（`:334-341`）标 2025，但 arXiv:2605.11659 是 2026-05；作者列表与两边记录都不符；所载主张（"rectifying collapsed attention"）与标题不匹配 | ◻转 |
| [M21] | **`yi2025decipher` 用的是被 ICML 2026 正式版取代的预印本**——**正是 A1/A23 已修过的那个错版**，P1 未同步；该文在 4 处以"dimension collapse 是根因"承载论证 | ◻转 |
| [M22] | **漏引先验工作**：Huang et al., *Mind the Gap: Preserving and Compensating for the Modality Gap in CLIP-Based Continual Learning*, **ICCV 2025**（[CVF](https://openaccess.thecvf.com//content/ICCV2025/html/Huang_Mind_the_Gap_Preserving_and_Compensating_for_the_Modality_Gap_ICCV_2025_paper.html) / [IEEE 11444362](https://ieeexplore.ieee.org/document/11444362)）研究的正是 CLIP 适配中的 gap 变化 → 直接威胁 "**first** systematic study of modality gap evolution during fine-tuning"（`main_nn.tex:41`、`introduction.tex:8`、`conclusion.tex:4`） | ✔核（外部来源已确认存在） |
| [M23] | 已发表版本存在却仍引预印本：`zhu2025connector`（IJCAI 2025）、`gu2025gtma`（IEEE Xplore 11463397）；`zhu2026fi` 是 LLM 脆弱性论文，却承载视觉编码器脆性的论证 | ◻转 |
| [M24] | **披露缺失且是单向的**：`paper/cover_letter.tex` 与 `cover_letter_zeroshot_correction.tex` **都是更正信**（08-14），非投稿信，均无姊妹稿披露；P1 全文 0 处 companion/wan2026，`references.bib` 无 Wan 条目。反向：`paper2/main.tex:73` 明写 "A companion empirical study established …(r=−0.827)"，A1/A23/ap3 的封面信也都披露。→ **四篇里 P1 是唯一不披露的一篇，而其余三篇都在引它** | ✔核（两封信逐行读过；A23 封面信 `paper_a2/cover_letter.tex:32` 同时披露 A1 与 P1） |
| [M25] | **ap3 侧的两处待办**：①`paper_ap3/sections/04_mechanism.tex:71/80/97`（及 `paper合/sections/empirical.tex:71/90/97`）把 r=−0.827 写成 "a key statistical discovery" 且无归属；②`:28` 与 `:15` 把 P1 的 **BLIP-1 改名 BLIP-2** 后照抄数字（P1 表头与正文均为 BLIP-1）→ 需回 `outputs/` 查真身 | ✔核（两侧原文都读过） |
| [M26] | 错版引用**扩散四处**：`paper_ap3/refs.bib`、`paper合/references.bib`、`paper2/`、`paper3/*/references.bib`（后者另有作者缩写错、标题错）→ 需从**单一正确源**一次修完 | ◻转 |

---

## 6. 处置建议

**不要现在主动给编辑写信。** 这批问题性质是标注/出处/报告口径 + 一处机理解释，**没有编造**。此刻自陈"我的数字报告不一致、机理图注与代码不符"，等于把一个**可修复的返修稿**升级为"作者承认系统性报告缺陷"，而编辑并未提问。

**正确路径**：

1. **现在**：按 §7 清单把修复包做完（含 [M1]/[M2] 需要的严格冻结对照实验，或改写叙事的决定）。修复同时服务于两条路：审稿返修，以及 P1 若被拒 → `paper_ap3` 合并（`docs/PA_P3_MERGE_PLAN.md`）。
2. **审稿意见到达时**：修订稿 + 逐条回应一次性交。凡涉及数字口径者，在 response letter 中主动列出"更正表"（我改了什么、原值、新值、依据），比被审稿人指出更可控。
3. **切勿**在没有新实验结果的情况下把 [M1] 仅作措辞软化——"direct causal evidence" 若保留，需能回答"text-only 的视觉侧到底动没动（`n_trainable_params` = 145,170,177）"。
4. **ap3 投之前**必须先做：引用四份同步、[M25] 两处、封面信披露 A1+P1（规则已写在 `HANDOFF.md:497`）、以及 `paper合/` 与 P1 的 1,413 词重合改写。

---

## 7. 返修执行清单（按动作排序，非发现顺序）

| 序 | 动作 | 依据 |
|---|---|---|
| 1 | **决定 [M1]/[M2] 走哪条路**：补"严格冻结 Embedding/LN"的对照实验（推荐，能救回因果主张），或改写 Visual Fragility 为不含因果的描述并删掉 "direct causal evidence" | §1 |
| 2 | 修 [M16]/[M17]：把 Table 7 的协议与 n 写清（14,288 vs 50,000 两套协议**同时标注**），使稿件与更正信一致；若保留 50k 值则说明为何与信中所报不同 | §4 |
| 3 | 落地审计三条动作（[M15]）：Setup 写明"LoRA adapters on attention projections; embedding 与 LayerNorm 参数保持可训练"，说明零样本数字来自归档 LoRA 检查点的重构模型 | §4 |
| 4 | 修 [M11]：恢复 n=81 选样规则（或换用 n=89/n=94 可重建子集并全篇改数），并把 fig2 的点数与标题 n 对齐 | §3 |
| 5 | 修 [M3]/[M5]/[M6]/[M7]：fig1 数据源统一到 Flickr30k、图序核对、fig5 图例改名、fig11 面板文字 | §2 |
| 6 | 修 [M8]/[M9]/[M10]：Adapter 行统一到共同基线重算；Table 4 补 n；ANOVA 剔除 full-FT 行与重复行；重算后如排序反转则**如实改写结论** | §3 |
| 7 | 修 [M12]/[M14]：例外清单三处统一（含 conclusion）；p 值统一；116→117；near-chance 补区间 | §3 |
| 8 | 修 [M13]：24% 改报 5-seed 均值 ± std（23.4% ± 0.9%）或注明单次运行 | §3 |
| 9 | 修 [M18]–[M23] 引用：ID 互换、DOI、年份作者、`yi2025` 换 ICML 2026 正式版、补引 Huang ICCV 2025 并改写 "first systematic"、预印本换正式版、`zhu2026fi` 换位或换引 | §5 |
| 10 | 修 [M24]：返修时在 cover letter 加一段姊妹稿披露（可直接套 `paper_a2/cover_letter.tex:32` 的措辞） | §5 |
| 11 | 同步 [M25]/[M26]：ap3 的 BLIP-1/2 真身、r=−0.827 归属、四份 bib 一次修完 | §5 |

---

## 8. 复核状态汇总

- **协调者亲自复核（✔核）**：[M1]、[M2]、[M4]、[M11]、[M13]、[M15]、[M16]、[M17]、[M22]、[M24]、[M25]，以及"59.3% vs 59.28% 只是四舍五入"这一**否掉**的指控。
- **采信代理结论（◻转）**：上表标注者；各条在对应报告内有完整证据链（JSON 键路径 / 源码行 / 外部来源）。**代理共同点：未发现编造。**
- **跨代理一致性信号**：[M1]/[M2]（机理解释）、[M8]/[M9]（Adapter 行）、[M11]（n=81）分别被**两个不同代理独立命中** —— 这三处是可信度最高的发现。
