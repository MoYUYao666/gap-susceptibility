# P3 / A23 / Commentary 升级包方案（2026-10-19）

> 规则同 A1 + Paper A：**只本地、不跑云端**；可用内存 23.9 GB，按峰值 ≤8 GB 排程；输出表格；**无论有没有 revision 都能用**；
> 冻结包（`SUBMISSION/` 与 `_frozen_submitted/`）一律不动，改动只进本地工作副本。
> 三稿当前审计均**无 FAIL**（仅 P2 级警告），所以方案重点是"把最脆弱主张补强"，不是修 bug。

## 一、P3（`paper3/paper_ieee/`，PRL `PRLETTERS-D-26-02378R1` 在审，deadline **2026-11-02**）

**现状**：10 页主稿；主张 = 用跨模态梯度耦合 Γ 零样本分配 rank（无需目标模型搜索）+ 跨架构迁移；已撤回三条过强主张
（视觉 token 预算、分配胜过 uniform、30× 方差比）；审计 0 FAIL，仅 3 个 P2（2 死标签、1 未用 bib、PDF 无 title）。
**归档**：`paper3/scripts/outputs/experiments/` 共 **181 个 JSON**（LLaVA/Qwen/CLIP 各 rank 与 uniform 对照、能量曲线），全部本地可分析。

| # | 升级项 | 现状/差距 | 动作 | 收益 | 本地资源 | 依赖 revision？|
|---|---|---|---|---|---|---|
| P3-P0-1 | **配对显著性** | "分配 vs uniform 不可区分"是撤回后的软肋 | 用归档 theory vs uniform runs 做 paired bootstrap + 效应量/CI | 把"不可区分"写成有区间的诚实结论 | 纯分析，**<20 min**，<1 GB | 否 |
| P3-P0-2 | **临界 rank 族内定位** | $r_c\in[5,6]$ 被质疑取自另一族 | 从 `E2_results.json`/`ers_1epoch_results.json` 在**同族内**重拟合 $r_c$，写清适用范围 | 消掉最锋利的"挪用"批评 | 纯分析，**<30 min** | 否 |
| P3-P0-3 | **AdaLoRA 对照表** | AdaLoRA 被报出更低对齐能量 | 归档 sweep 逐配置差 + CI，做成小表 | 把反例变成"边界条件"而非漏洞 | 纯分析，**<20 min** | 否 |
| P3-P0-4 | **修订版重编译 + 回复骨架** | 已补 IFCloRA/StatLoRA/LoRA-GA² | 10 页重编译（当前 0/0/0），按 objection 写 response 骨架 | 修回可 1 天内交 | 写作 **~1 h** | 是（或改投时用）|
| P3-P1-5 | **审稿意见包** | 无 | 8 条预判（跨架构是否只在 CLIP、Γ 对 rank 敏感性、uniform 对照、评阅周期） | 10 分钟能出初稿 | 写作 **~1.5 h** | 否 |
| P3-P1-6 | **P2 清账** | 2 死标签、1 未用 bib、PDF 无 title | 加 `\ref`、删/引 `sharegpt2023`、`\hypersetup{pdftitle=...}` | 审计变干净 | **<30 min** | 否 |
| P3-P2-7 | **本地 Γ 稳健性**（可选）| Γ 证据来自云端 LLaVA/Qwen | 本地 5 骨干上做 rank 敏感性（已有 embedding，LoRA 小跑）| 补一个"本地可复现"层 | GPU **~40 min**，峰值 ~5 GB | 否 |
| P3-P2-8 | **改投包** | 手工 | `_p1336_build_venue_package.py` 出 Elsevier/Springer 版 | 被拒 1 小时改投 | 无 GPU | 否（通用）|

**预算**：总 ~4–5 h，GPU 仅可选 40 min。

## 二、A23（`paper_a2/`，IEEE JOE `26-0663` 在审，64–66 页）

**现状**：五类感知域（海洋光学、声呐、ImageNet 等）的 gap-surgery 诊断；核心脆弱点 = "只有诊断、没有可用统计量"（AE 会问"那该用什么"）；
审计 0 FAIL，仅 3 个 P2（9 条 `OT1/ptm/m/scit` 字体警告、3 死标签、PDF 无 title）。
**归档**：`outputs/ocean_*.json`（20+ 个，含 **margins**、gap-surgery、多模板、多随机种子、退化、检索）+ `outputs/sonar_*.json`（7 个，含 URPC/PEFT/degradation），全部本地可分析。

| # | 升级项 | 现状/差距 | 动作 | 收益 | 本地资源 | 依赖 revision？|
|---|---|---|---|---|---|---|
| A23-P0-1 | **接入 margin 质量证书** | 现只有"gap 不足"的否证 | 用已有 `ocean_margins*.json`/`sonar_*` 逐域算 $M(\epsilon)$ 与 BA 的相关/选择规则 | 从"诊断"升级为"给出可用证书"，直接补最强短板 | 纯分析，**<30 min** | 否 |
| A23-P0-2 | **跨域阈值迁移** | 缺"绝对阈值不可迁移"的量化 | 每域拟合阈值→跨域评估，报 BA/正例率 | 新增一条可引用结论 | 纯分析，**<30 min** | 否 |
| A23-P0-3 | **对称手术 + 逐域 CI** | gap-surgery 是否双向、CI 是否齐 | 从 `ocean_gap_surgery.json` 检查双向；缺则本地补小实验/补 bootstrap | 消掉"只做单向平移"质疑 | 分析 **<30 min**；如需补实验 GPU ~15 min | 否 |
| A23-P0-4 | **审稿意见包** | 无 | 8 条预判（域少/单一数据集、声呐样本量、surgery 是否只是线性、跨模态可比性）| 修回即用 | 写作 **~1.5 h** | 否 |
| A23-P1-5 | **字体警告修复** | 9 条 `OT1/ptm/m/scit` 未定义 | 改 `\textsc` 用法或 T1 编码，重编译 64 页 0/0/0 | 审计变干净、排版一致 | **<30 min** | 否 |
| A23-P1-6 | **死标签/元数据** | `cor:nocg`/`cor:orth`/`cor:twofield` 未引用；无 PDF title | 加引用 + `\hypersetup` | 同上 | **<20 min** | 否 |
| A23-P1-7 | **周检引用** | 声学跨模态蒸馏（arXiv:2609.31785）等未引 | bib 加 1–2 条 + 一句背景 | 相关工作更新 | **<30 min** | 否 |
| A23-P2-8 | **域外复现** | 五域之间仍同一评测流程 | 在 fathomnet8 / marine_captions 上重跑证书诊断 | 泛化证据（本地数据已有）| GPU **~20 min**，峰值 ~4 GB | 否 |

**预算**：总 ~4–5 h，GPU 最多 ~35 min。

## 三、Commentary（`paper_review_prl/`，PRL `PRLETTERS-D-26-02402` 在审，7 页）

**现状**：*Allocation, not selection: comparability in parameter-efficient multimodal adaptation*；主张 = 多模态 PEFT 论文混淆"容量放哪"与"怎么分"，
POPE/MMBench 数值因基准子集/协议而不可比，提出 **12 条报告项**。审计 0 FAIL，仅 1 个 P2（`fig:decision` 死标签）。
**归档**：无实验归档（评论稿），靠文献 + 三篇自有稿的实证数字。

| # | 升级项 | 现状/差距 | 动作 | 收益 | 本地资源 | 依赖 revision？|
|---|---|---|---|---|---|---|
| C-P0-1 | **与最新工作划界** | Sharma & Saxena 2026（readout 依赖）与 Role/Amblard 期刊版都会被视为"也在谈 gap 修改" | 加引用 + 一段：本文谈**可比较性/报告协议**，不重解 gap | 避免"被抢题"误读 | 写作 **<1 h** | 否 |
| C-P0-2 | **12 条报告项的实证支撑** | 现在多为原则性陈述 | 每条挂一个自有归档数字（prompt 漂移 3.4×、阈值迁移 BA 0.458、选择 regret 0.06 vs 13.8、670 配对/48.5 点）| 评论稿从"清单"变成"有证据的清单" | 纯分析+写作 **<40 min** | 否 |
| C-P0-3 | **POPE/MMBench 说法复核** | 数值需与归档/原文一致 | 逐条核对子集与数值，不能核实的降级为"报告项"而非数字 | 防事实错误 | **<30 min** | 否 |
| C-P1-4 | **审稿意见包** | 无 | 6 条预判（只是清单吗、是否推销自家方法、是否忽略非 PEFT 多模态、POPE 子集依据）| 修回即用 | 写作 **<1 h** | 否 |
| C-P1-5 | **死标签 + 元数据** | `fig:decision` 未引用；无 PDF title | 加引用 + `\hypersetup` | 审计干净 | **<20 min** | 否 |
| C-P1-6 | **周检引用** | Yaras 2024 / Sharma 2026 / Amblard 期刊版未引 | bib 3 条 + 相应句子 | 相关工作最新 | **<40 min** | 否 |
| C-P2-7 | **投稿包重建** | 手工 | `_p1336` 一键出包（7 页 + cover letter + highlights）| 改投/修回即用 | 无 GPU | 否 |

**预算**：总 ~3 h，全本地 CPU。

## 四、总预算与纪律

| 稿 | 总耗时 | GPU | 峰值内存 |
|---|---|---|---|
| P3 | ~4–5 h | 可选 ~40 min | ≤5 GB |
| A23 | ~4–5 h | ≤35 min | ≤4 GB |
| Commentary | ~3 h | 0 | <1 GB |
| **合计** | **~12 h** | **≤75 min** | **<8 GB（上限 23.9 GB）** |

**纪律**：① 一次只跑一个 GPU 任务；② 全部本地，不下载新骨干；③ 冻结包与 `_frozen_submitted/` 不动，改动只进本地工作副本；
④ 每项完成即更新 `HANDOFF.md`、`文件地图.md` 与各稿 `FIXES_*.md` / `RELEASE_NOTES.md`；⑤ 数字必须落归档（沿用 claim-ledger 风格）。

---

## 执行状态（2026-10-19 18:20，全部本地）

| 项 | 状态 | 交付物 |
|---|---|---|
| P3-P0-1 配对区间 | ✅ 完成并**已入稿**：同种子同 rank 配对 $n{=}4$，guided 臂末端能量 $+11.5$，95% CI $[+6.8,+16.2]$（方向不利于 guided） | `outputs/analysis/p3_upgrade_analysis.json`；`sections/experiments.tex` |
| P3-P0-2 族内 r_c | ⚠️ **核验完成、未入稿**：E2 确认 $[5,6]$（r=5 均值 3906 < 3927；r=6 均值 3989 > 3927）；独立 sweep 给出 $[14,16]$（r≤14 收敛、r=16 两/三种子发散、r≥20 全部发散）。两族须在下一版**显式标注协议**后再写，避免自相矛盾 | `docs/P3_UPGRADE_MEMO_2026-10-19.md` |
| P3-P0-3 AdaLoRA | ✅ 核验：归档 $\Delta E=-1468.15$（$3	imes10^{-4}$）与 $-757.30$（$10^{-3}$）与稿件**完全一致**，无需改 | `_p458_adalora_lr*.txt` |
| P3-P0-4 重编译+回复骨架 | ✅ 10 页 0/0/0；回复骨架见 `docs/P3_REVIEWER_OBJECTIONS.md` | `main.pdf` |
| P3-P1-5/6 | ✅ 意见包 8 条；死标签、未用 bib、PDF title 全部清掉 | `docs/P3_REVIEWER_OBJECTIONS.md` |
| P3-P2-7 本地 Γ 控制 | ⏸ **暂缓（有理由）**：通用 CLIP 代理无法验证 LLaVA 协议主张；记录于 memo | — |
| P3-P2-8 改投包 | ✅ `SUBMISSION/_venue_builds/P3_PRL_next/` | — |
| A23-P0-1 证书 | ⚠️ **负结果并记录**：通用 CLIP 在 fathomnet8/NKSID 上 margin 质量饱和（$Mpprox1$，相关性不可定义），原因是从冻结模型精度仅 20–27%；OceanCLIP 权重本地缺失，改用归档 margins 不可行。作为 negative control 归档，不入正文 | `outputs/analysis/a23_certificate_control.json`；`docs/A23_REVIEWER_OBJECTIONS.md` |
| A23-P0-2 阈值迁移 | ✅ **已入稿**：同域 BA 0.83，跨域/跨模型 0.25–0.67（机会 0.50），双向报告 | `a23_threshold_transfer.json`；`ext_partII_domains.tex` |
| A23-P0-3 对称手术+CI | ✅ 归档核验：image-side 12 个幅度 + text-side $\lambda{=}1.0$（clip_frozen 与 sonar_ft 均有） | `sonar_protocol.json`；memo |
| A23-P0-4/P1-5…7 | ✅ 意见包 8 条；死标签引用、PDF title、1 条新引用；字体警告记录为 IEEEtran scit→it 替换（外观无损） | `docs/A23_REVIEWER_OBJECTIONS.md`；`main_ieee.pdf` 64 页 0/0/0 |
| A23-P2-8 域外复现 | ⚠️ 与 P0-1 同一控制，结论为负（饱和），已记录 | 同上 |
| C-P0-1 划界 | ✅ **已入稿**：3 条 2026 引用（Sharma/Yaras/Role-Ambard）+ 一句划界（"解释 gap 为何重要" vs "哪个数字可比"） | `MANUSCRIPT.md`；`_refs_used.json` 48 条 |
| C-P0-2 六实例表 | ⏸ 表格试加后**为守 7 页上限移除**；六实例仍为正文段落，逐条可核对 | `docs/COMMENTARY_REVIEWER_OBJECTIONS.md` |
| C-P0-3 POPE/MMBench 复核 | ✅ 两条头条数字均按原引用标注（LLaVA-1.5 表头三子集；MMBench circular 36.7→2.6），未新增未标注数字 | 同 memo |
| C-P1-4/5/6 | ✅ 意见包 6 条；死标签 `fig:decision` 由 builder 改为 `\ref`；PDF title 元数据 | builder patch |
| C-P2-7 投稿包 | ✅ `SUBMISSION/_venue_builds/Commentary_PRL_next/` | — |
| **页数** | P3 **10 页**；A23 **64 页**；Commentary **7 页**（守上限）；均 0 错误 / 0 未定义 / 0 Overfull | 审计见 `docs/audits/` |

**纪律**：`SUBMISSION/` 冻结包与 `_frozen_submitted/` 未动；新包只写入 `SUBMISSION/_venue_builds/`；全部本地，GPU 仅 A23 控制 ~2 min 与检索无关任务，峰值内存 <4 GB。

---

## 执行状态·续（2026-10-19 18:50，第二轮补做）

| 项 | 状态 | 说明 |
|---|---|---|
| **P3-P0-2**（原"待裁决"）| ✅ **已解决并写入正文** | 追到 `paper3/scripts/run_full_sweep.py`：sweep 用 `run_training.py --epochs 3`，而 E2 族的轨迹在**同 rank 同 seed** 下完全不同（E0 3930.5 vs 3927，轨迹形状不同）⇒ 两族是**不同训练配置**、同一空白图协议。已在结论写入：dense 3-epoch sweep 的临界区间为 $[14,16]$，与 E2 的 $[5,6]$ 不同 ⇒ 临界 rank 连**超参**都随协议变，强化"属于协议不属于模型"的撤回表述 |
| **A23-P0-1**（原"负结果"）| ✅ **升级为适配模型实验并写入正文** | 发现本地其实有 **BioCLIP 基座 + OceanCLIP 权重**（`models/oceanclip-0.15b/`，open_clip 3.3.0）：在 67 类海洋子集与同一 gap-surgery 协议上，margin 质量与精度仅弱相关（$r=-0.35$ / $-0.56$），阈值跨编码器不迁移（BA 0.13–0.50）⇒ 作为"标量证书不能替代域内诊断"的证据写入，与论文结论一致 |
| **A23-P0-2**（扩展）| ✅ 已扩展并写入正文 | 从 8 个密集幅度臂扩到 **12 个归档域臂**（加 4 个 spectrum 臂）：跨域 BA 中位 **0.50**（机会）、范围 0.00–0.83；同时同域拟合降到 0.50–0.63 ⇒ 阈值需要足够幅度点才能拟合，进一步说明"绝对 gap 是各自测量网格的诊断" |
| **A1 的 checkpoint 复算** | ⏸ 不可行 | `outputs/a1_rr_ckpt/` 下无任何 `.pt`（目录为空）⇒ epoch-sweep 的逐 epoch margin 无法重算，监控声明的"内部最优点"验证仍留待未来 |
| P3-P2-7、C-P0-2 | ⏸ 仍暂缓（理由已记录） | 本地 CLIP 代理无法验证 LLaVA 协议；六实例表与 7 页上限冲突 |

**页数/状态**：P3 **10 页**、A23 **65 页**（+1 页）、Commentary **7 页**；均 0 错误 / 0 未定义 / 0 Overfull。P3 与 A23 复审 **READY/A**；Commentary 保持 READY/A。

## Round 5 status (2026-10-20 00:20)

All previously deferred items are now executed locally: P3 extra ranks (7, 8, 10) and a second seed, the exact
permutation test (p=0.33 with the 2+2-seed power limitation stated), the local Qwen2-VL-2B check (inconclusive because the
rank parameter did not vary the adapter; not used as evidence), the A23 order-preservation control and the UATD second
acoustic corpus (out of distribution, reported as a boundary), the A1 early-stopping baselines and the per-epoch checkpoint
hook, and the commentary compliance paragraph (7 pages kept). The public mirror was pushed and GitHub release v2.0 was
created; the Zenodo version DOI is pending because the integration is asynchronous.

## Round 6 status (2026-10-20 08:40)

The five optional upgrades were executed: expanded A1 monitoring (extra seeds and a fourth domain, reported honestly even
though it weakens the subset result), A1 wording now describes the certificate as an in-domain selection statistic rather
than a universally superior stopping rule, A23 tau calibration (the relation transfers up to a linear rescaling, the hard
threshold does not), the corrected Qwen2-VL-2B local check (valid rank variation; both ranks negative, no sign flip up to
r=6, reported as a boundary), and a per-run supplementary table for the P3 re-runs.

> **2026-10-20 22:50 状态**：`PRLETTERS-D-26-02378R1` → **Required Reviews Completed**
> （Oct 20, 2026）；审稿意见已回收，等待编辑裁决。修回件（response 模板/cover letter/10+6 页包）已就绪。

> **2026-10-21 16:00 状态**：P3 **被 PRL 拒稿**（`PRLETTERS-D-26-02378R1`，EIC Yonghuai Liu）。
> 原修回计划（response 模板/cover letter）转为改投基础；改投目标与改稿策略待定。
