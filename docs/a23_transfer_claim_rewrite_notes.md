# A23 迁移主张改写记录（2026-10-25）

本轮把 `paper_a2/ext_partII_domains.tex` 里**"没有任何 M 阈值可跨域/跨编码器迁移"**的句子
替换为"**迁移确实存在，但只落在一个方向上（目标是声呐语料、统计量以 σ 相对族为主）**"的有界陈述。
所有数字来自 `outputs/analysis/a23_multiencoder_transfer.json`（`tools/_p1614_a23_multi_encoder_transfer.py` 产出）。
归档 sha256 = `E7710EE1062BA616F4C7C6EB2330321BE7999C151FC41BDFD9B93FCC97294603`（4,984,242 B，
`meta.finished_at = 2026-10-25T07:29:41+0800`，已随提交 `ec27c94b` 入库）。
**该文件在本轮被别的 agent 重写过两次**（07:23:41 的 18 单元版、07:28:12 的 1 单元中间态、07:29:41 的 18 单元版）；
我已用"整份 JSON 逐字段比较"确认 07:23:41 与 07:29:41 两版**内容完全一致**，本记录的每个数字在磁盘当前版本里逐条复查过。

## 1. 改动清单

| 文件 | 动作 | 现在 sha256（前 16 位） |
|---|---|---|
| `paper_a2/ext_partII_domains.tex` | 换句（122–145 行）+ Source 行补字段路径（146–158 行）+ 两处配套限定（87–88、118–119、161–162 行） | `ADD2043C4E84C756` |
| `paper_a2/verify_a23_fix.py` | **只改页数常量** `PAGES` 72 → 73（含注释里一行说明） | `0710DFE94B3986A7` |
| `docs/provenance_manifest.json` | `A23.floats[tab:calib_lodo].note` 重写（脚本 + 归档 + 字段路径 + 新计数 + 边界），`status` 仍为 `verified` | `D5F74C085EA9DE04` |
| `docs/a23_multiencoder_rerun_notes.md` | 仅**追加**一节整合记录（第 9 节） | — |
| `docs/a23_transfer_claim_rewrite_notes.md` | 本文件（新建） | — |

`paper_a2/main_ieee.tex` **未改**：全稿检索（`no threshold` / `portable threshold` / `a23_multiencoder` / `_p1614` /
`cross-domain transfer`）在该文件与 `abstract.tex` 中**零命中**，该主张只出现在 `ext_partII_domains.tex`（由
`main_ieee.tex:637` 的 `\input` 引入），也没有列这张主张的 Source 行或图形来源表条目需要改。

## 2. 旧句 → 新句

**旧句（`git show HEAD:paper_a2/ext_partII_domains.tex` 第 121–133 行，1,387 字符；结论"无迁移"）**

> Widening the same test to every ordered pair of encoder--corpus units available locally ($3$ frozen encoders---the
> generic-CLIP control and the two adapted encoders---over $3$ corpora, i.e.\ $5$ units and all $25$ ordered pairs,
> each scored on $13$ threshold statistics) **leaves the verdict unchanged**: of the $260$ scored cross-unit
> (pair, statistic) entries $7$ reach a nominally above-chance balanced accuracy (chance $0.50$) and **none** keeps
> its $95\,\%$ interval above chance under an image-level bootstrap ... the strongest nominal entry (OceanCLIP on the
> marine subset $\to$ generic CLIP on the optical corpus at $\varepsilon=0.01$) reaching balanced accuracy $1.000$
> from a source fit of $0.500$ with a (balanced accuracy $-$ chance) interval of $[-0.150,+0.500]$ that includes zero.
> ... This selection is partial---$5$ of the $21$ encoder--corpus units of the registered grid---so **the negative
> claim is widened only as far as this selection supports it**.

**新句（`paper_a2/ext_partII_domains.tex` 第 122–145 行，2,460 字符，比旧句长 1.8 倍）**

> Widening the same test to every ordered pair of encoder--corpus units available locally ($6$ frozen
> encoders---the generic-CLIP control, the two adapted encoders and three further frozen backbones---over $3$
> corpora, i.e.\ $18$ units and all $324$ ordered pairs, each scored on $13$ threshold statistics; the $18$
> self-pairs, $221$ scored entries, are excluded by construction) **does produce transfer, but only inside one
> regime**. Of the $3536$ scored cross-unit (pair, statistic) entries $124$ reach a nominally above-chance balanced
> accuracy (chance $0.50$) and $19$ keep their $95\,\%$ interval above chance under an image-level bootstrap
> ($2{,}000$ draws, the source threshold refitted on each source resample; paired when source and target share a
> corpus, independent otherwise). **Every survivor has an acoustic-sonar target---$11$ on SigLIP, $8$ on
> OceanCLIP---and the optical and the 67-class rare-species targets contribute none**; $18$ of the $19$ are the
> resolution-normalised statistics $M(\varepsilon/\sigma_D)$ at $\varepsilon/\sigma_D\in\{0.005,0.01,0.02\}$
> ($9$, $7$ and $2$ entries, with $\sigma_D=1-\mathrm{mean}_i\max_{c\neq y_i}s_i(c)$ formed inside each unit), so
> what transfers is a resolution fixed to the unit's own score scale---the regime isolated above---not an absolute
> $\varepsilon$. The strongest survivor (BioCLIP on the sonar corpus $\to$ SigLIP on the sonar corpus at
> $\varepsilon=0.002$) reaches balanced accuracy $0.900$ from a source fit of $0.500$ with a (balanced accuracy $-$
> chance) interval of $[+0.100,+0.500]$; **a source fit at chance level means that what crosses encoders and corpora
> is the _direction_ (lower $M$ = healthier), not a calibrated operating point**. The unqualified "no threshold on
> $M$ transfers" is therefore not supported and is replaced by this bounded statement, still limited by the nine
> configurations per unit that define the label (a median split, so the target balanced accuracies $0.700$--$0.900$
> are granular to $1/4$--$1/5$), by class-imbalanced corpora (sonar floats $951/1783$ images; marine $7$--$61$
> images per class; the rare-species subset at $1.49\,\%$ chance), by a single probe split seed for the probe-based
> encoders, and by reading each encoder through a declared extraction path rather than its project's official
> reference pipeline, although the units shared with the two certificates reproduce them exactly
> ($\max|\Delta|{=}0$ over $128$ compared values on four units).

配套限定（同一段，避免与新句矛盾）：
① 第 87 行小标题句 → "Thresholds transfer within a domain, not across domains or models**---with one bounded
exception for the margin mass below**"（旧句是无条件断言，若不改会与同段新句互相打脸）；
② 第 118–119 行 "does not yield a **portable** threshold" → "**portable absolute** threshold"（新句报告的正是
"σ 相对"这一族可迁移，保留"绝对 ε 不可迁移"这一条）；
③ Source 行末句 "a within-domain, order-based diagnostic rather than a portable scalar" → "an order-based,
mainly within-domain diagnostic: the one bounded scalar transfer reported above is a direction, not a portable level"。

## 3. 幸存者算术（自对排除，可逐条复核）

规则：**幸存者 = `bootstrap.survives == true` 且 `self_pair == false`**（自对 = 同一单元两侧，源在自己语料上
in-sample 拟合与打分，按 `transfer.summary.self_pairs_excluded_from_the_claim` 从不计入迁移）。
脚本侧证据：`tools/_p1614_a23_multi_encoder_transfer.py:1560-1580`
（`flat`/`flat_self` 两条列表，`above`/`survivors` 只从 `flat` 取）。

| 量 | 值 | 归档字段 |
|---|---|---|
| 单元 / 有序对 | 18 / **324** | `transfer.n_units`, `transfer.n_pairs` |
| 自对（排除） | **18** 对，**221** 条已评分条目 | `transfer.self_pairs`, `transfer.summary.n_scored_entries_self_pairs` |
| 跨单元对 | **306** | `transfer.cross_unit_pairs` |
| 已评分跨单元条目 | **3536**（=306×13 − 442 退化） | `conclusion.n_scored_entries_cross_unit` |
| 名义高于 chance(0.50) | **124** | `conclusion.n_entries_above_chance` |
| **通过图像 bootstrap（跨单元）** | **19** | `conclusion.n_entries_surviving_bootstrap` |
| 同上（**不排除**自对：19 + 10 = 29） | 29（其中自对 10） | `transfer.pairs[].by_statistic.*.bootstrap.survives` 自行汇总 |
| 判定 | `yes for at least one pair` | `conclusion.answer` |

- 19 / 3536 = **0.54%**（名义率 124 / 3536 = 3.51%）。
- 19 条落在 **9 个有序 (源单元 → 目标单元) 组合**上、**2 个目标单元**上：
  `siglip-base-patch16-224__acoustic_sonar` 11 条、`oceanclip__acoustic_sonar` 8 条。
- 源侧：编码器 `clip-vit-base-patch32` 7 / `bioclip` 6 / `clip-vit-large-patch14` 5 / `siglip-base-patch16-224` 1；
  语料 `acoustic_sonar` 10 / `rare_species` 9（后 9 条是**跨语料**、`paired=false` 的独立 bootstrap）。
- 目标 BA 分布：0.700 ×8、0.800 ×4、0.900 ×7；(目标 BA − chance) 区间下界：+0.100 ×1、+0.1667 ×8、
  +0.175 ×6、+0.25 ×4（**全部严格 > 0**，即 `survives` 的判据）。
- 单元量级：`acoustic_sonar` n=1,783 图 / 7 类（top-1 chance 14.29%），`rare_species` n=1,608 图 / 67 类
  （1.49%）；迁移判别的 chance 是 **平衡准确率 0.50**（九配置中位切分）。
- 退化条目 455（其中跨单元 442）：中位切分后某一类为空，`target_BA = null`，不参与评分。

## 4. 边界：幸存者集中在唯一一个目标语料

**19/19 的目标语料都是 `acoustic_sonar`**；目标语料为 `marine_optical` 或 `rare_species` 的跨单元幸存者为 **0**。
统计量族上 **18/19 是 σ 相对族**（`mass_sigmarel_0p005` 9、`_0p01` 7、`_0p02` 2），
只有 1 条是绝对网格（`mass_0p002`，即最强的那条：`bioclip__acoustic_sonar → siglip-base-patch16-224__acoustic_sonar`，
目标 BA 0.900、源拟合 BA 0.500、阈值 0.96859、ΔCI95 **[+0.100, +0.500]**、`p_delta_gt_zero = 0.992`、
`paired=true`）。源拟合恰在 chance ⇒ 迁移的是**方向**（M 低 = 健康）而不是水平；正文已把这个性质写进去，
没有把它说成"可移植的标量证书"。
**未写进正文**但仍在归档里的对照组（旧句的主角）：`conclusion.best_pair_point_estimate` =
`oceanclip__rare_species → clip-vit-base-patch32__marine_optical`、`mass_0p01`、BA 1.000、ΔCI95
[−0.166875, +0.500]、`p=0.499`（名义最强但**未通过**）；新句以"19 条幸存"为主线，故未引用该条，避免再次
用单个名义极值讲故事。

## 5. 页数与编译

| 项 | 结果 |
|---|---|
| `pdflatex -interaction=nonstopmode main_ieee.tex` ×2（在 `paper_a2/`） | 两次 exit 0 |
| 页数 | **72 → 73**（`Output written on main_ieee.pdf (73 pages, 1275050 bytes)`） |
| LaTeX error | 0（`^! ` 零命中） |
| undefined references / citations | 0 / 0 |
| overfull hbox | 0（只有 underfull，含新段所在段 88–167 行的若干条，均非 overfull） |
| rerun 请求 | 无 |
| `verify_a23_fix.py` | `PAGES` 常量 72 → 73；**ALL CHECKS PASSED**（31 项） |

页数**确实变化**（72→73），因此按任务允许改了 `verify_a23_fix.py` 的页数常量（改的是常量与其注释，未动任何
检查逻辑）。增量来源：新句比旧句长 ≈1,073 字符，Source 行字段路径再长 ≈600 字符，跨了一个分页边界。

## 6. 门禁结果（逐条）

| 门禁 / 命令 | 结果 |
|---|---|
| `pdflatex … main_ieee.tex` ×2（`paper_a2/`） | exit 0；73 页；0 error / 0 undefined ref / 0 undefined cite / 0 overfull |
| `python paper_a2/verify_a23_fix.py` | **ALL CHECKS PASSED**（含 73 页、US letter、行号连续、12pt 正文、37 个冻结归档 SHA-256 未变） |
| `python -m tools.paper_audit audit --profile a23_joe --fail-on NONE` | 退出码 0；`BLOCKED` grade D，**pass=57 / fail=1 / warn=0 / manual=9 / skip=19 / error=0**；唯一 FAIL 为 `A-01`"Git working tree is clean for the manuscript paths"（列出 `M paper_a2/ext_partII_domains.tex`、`M paper_a2/verify_a23_fix.py`）——**即任务预告的"未提交前必然 git-dirty"，待 lead 提交后消失**。报告：`docs/audits/AUD-a23_joe-20261024T233441Z.{json,md}` |
| `python tools/_p1428_provenance_gate.py` | **gate: PASS**（A23: floats=34 manifest=34 missing=0 pending=0 broken_paths=0；四篇合计同样 0/0/0） |

## 7. 无法溯源 / 未做的事（诚实标注）

1. **机制未溯源**：为什么只有"朝向声呐语料"的迁移成立（且源侧可以来自 67 类稀有物种语料），归档只给现象，
   没有给出机制证据。正文因此**只陈述边界，不解释成因**，也没有写"声呐域更容易"之类的因果话。
2. **RemoteCLIP 的排除理由不是我的证据**：本轮选择是 6/7 编码器（`meta.selection.encoders`、
   `limits.encoder_count.n_selected=6`），第 7 个 `remoteclip` 未入选；它的权重能否取到、以及"21 单元误跑"
   一事，均来自另一路 agent 的 `docs/a23_multiencoder_rerun_notes.md` §7.1，**我没有独立复验**，正文也未提及。
3. **`transfer.summary` 的历史含义**：本轮磁盘上该块与 `conclusion` 一致（我逐字段核对过），
   但 07:28:12 那个 1 单元中间态里 `summary`/`conclusion` 曾是"1 单元"的数字；正文与 manifest **只引
   `conclusion.*` 与 `transfer.{self_pairs,cross_unit_pairs}`**，不用任何中间态数字。
4. **单种子探针未被重跑**：DINOv2 三个单元仍是 seed 0 单次切分（`limits.probes.single_seed`），
   换切分会不会改变"目标语料只有声呐"这一边界**未做实验**，正文以"single probe split seed"如实标注为限制。
5. **`zh_ext_partII_domains.tex` 未同步**：中文镜像里根本没有这一段的迁移主张（检索零命中），且它不在本轮
   写范围内，故未改。
6. **未改 `main_ieee.tex`**：见第 1 节末（零命中，无需改）；页码/来源表条目也不涉及该主张。
7. **未改 `SUBMISSION/**`**：`verify_a23_fix.py` 的 37 个冻结哈希全绿，投稿包仍是 2026-10-24 的冻结态；
   本轮的稿件改动**尚未进入投稿包**（需要 lead 决定是否重建包）。

## 8. 复核命令

```powershell
# 归档（本轮数字的唯一来源）
python -c "import json;d=json.load(open('outputs/analysis/a23_multiencoder_transfer.json',encoding='utf-8'));print(d['conclusion']['answer'],d['conclusion']['n_entries_above_chance'],d['conclusion']['n_entries_surviving_bootstrap'])"
# 编译 + 逐项自检
cd paper_a2; pdflatex -interaction=nonstopmode main_ieee.tex; pdflatex -interaction=nonstopmode main_ieee.tex; python verify_a23_fix.py
# 两道门禁
python -m tools.paper_audit audit --profile a23_joe --fail-on NONE
python tools/_p1428_provenance_gate.py
```

## 9. 18 单元 → 21 单元切换记录（2026-10-25，RemoteCLIP 归位后）

**触发**：07:39 由 lead 侧跑完全网格并**整份覆写** `outputs/analysis/a23_multiencoder_transfer.json`
（`meta.finished_at = 2026-10-25T07:39:56+0800`，`generator = tools/_p1614_a23_multi_encoder_transfer.py`，
script sha1 `ee174963df00583822b4d70f30f8da450dda3fbb`，`meta.git = a834c33e…` 且 `dirty = false`）：
7 编码器 × 3 语料 = 21 单元。第 1 节写下的 18 单元数字（3536 / 124 / 19 / 11+8）**自此没有任何 live
archive 可指**（只存在于 `git show HEAD:outputs/analysis/a23_multiencoder_transfer.json`），按"每个数字必须能
指名归档字段"的直接要求，正文、manifest 与本记录同轮切到 21 单元。
**本节取代第 1、3、4 节的计数与 §7 第 2 条的"RemoteCLIP 未复验"结论；第 2 节的旧句引文保留为历史。**

### 9.1 新计数（全部来自 21 单元归档，已逐条复算）

| 量 | 18 单元（旧） | 21 单元（新） | 归档字段 |
|---|---|---|---|
| 编码器 / 语料 / 单元 | 6 / 3 / 18 | **7 / 3 / 21** | `conclusion.n_encoders`, `n_corpora`, `n_units` |
| 有序对 | 324 | **441** | `conclusion.n_ordered_pairs`, `transfer.n_pairs` |
| 自对（排除） | 18 对 / 221 条 | **21 对 / 260 条** | `transfer.self_pairs`, `transfer.summary.n_scored_entries_self_pairs` |
| 跨单元对 | 306 | **420** | `transfer.cross_unit_pairs` |
| 已评分跨单元条目 | 3536 | **4940** | `conclusion.n_scored_entries_cross_unit` |
| 名义高于 chance | 124 | **179** | `conclusion.n_entries_above_chance` |
| bootstrap 幸存（跨单元） | 19 | **29** | `conclusion.n_entries_surviving_bootstrap` |
| 退化条目 | 455（跨单元 442） | **533（跨单元 520 + 自对 13）** | `transfer.summary.n_degenerate_entries` |
| 幸存者目标编码器 | SigLIP 11 / OceanCLIP 8 | **SigLIP 12 / OceanCLIP 10 / RemoteCLIP 6 / CLIP-L/14 1** | `transfer.pairs[]` 聚合 |
| 幸存者统计量族 | σ 相对 18 + 绝对 1 | **σ 相对 27（12/10/5）+ 绝对 2** | `transfer.pairs[]` 聚合 |
| 判定 | yes for at least one pair | yes for at least one pair（**不变**） | `conclusion.answer` |

- **自对排除算术**（可复核）：441 × 13 = 5733 条总条目；非退化 5733 − 533 = 5200 = 4940（跨单元）+ 260（自对）。
  另一条路径：跨单元 420 × 13 = 5460；5460 − 520（跨单元退化）= 4940。
- **幸存者算术**：29 = 27（σ 相对：`mass_sigmarel_0p005` 12 / `_0p01` 10 / `_0p02` 5）+ 2（绝对：`mass_0p002`、
  `mass_0p01`）；目标语料 **29/29 全是 `acoustic_sonar`**（`marine_optical`、`rare_species` 作目标 0 条）；
  源语料 `acoustic_sonar` 16 / `rare_species` 13；成对 bootstrap 16 / 非成对 13。
- **最强幸存者两版相同**：`bioclip__acoustic_sonar → siglip-base-patch16-224__acoustic_sonar`、`mass_0p002`、
  目标 BA 0.900、源拟合 BA 0.500、ΔCI95 **[+0.100, +0.500]**、`p_delta_gt_zero 0.992`、源/目标各 9 个不同取值
  （`conclusion.best_surviving_pair`；按 `survivors.sort(key=-target_BA)` 的稳定排序取首位，BA 0.900 共 7 条并列）。
- **新增边界**：6 条幸存者的**目标单元**是 RemoteCLIP（全部落在 sonar 目标上）。

### 9.2 RemoteCLIP 健康检查（本轮独立复验，取代 §7 第 2 条）

| 语料 | RemoteCLIP top-1 | chance | 复现行 |
|---|---|---|---|
| marine_optical | 12.828 % | 14.2857 % | 无（`reproduction.reference = null`） |
| acoustic_sonar | 11.273 % | 14.2857 % | 无 |
| rare_species | 2.425 % | 1.4925 % | 无 |

三个语料都在 chance 的 2 倍以内 ⇒ **触发 lead 给的 STOP 条件**（"看起来像未训练模型"）。但"权重没加载
⇒ 21 单元 run 无效"这一推断被四组证据**证伪**：

1. `models/RemoteCLIP/RemoteCLIP-ViT-B-32.pt` sha256 =
   `60014e395d930a3f2963d1d89c8522bf4ad56775571e4356e866864789af85c4`（605,208,421 B），与 HF 镜像 API
   列出的官方 LFS oid（`chendelong/RemoteCLIP/tree/main`，2026-10-25 查询）逐位一致；
2. 归档 `encoders.remoteclip.corpora.*.model_source.load_report`：302 keys，missing 0 / unexpected 0；
3. 该 checkpoint 是 OpenAI CLIP ViT-B/32 的**真·微调**：与 `models/clip-vit-base-patch32/pytorch_model.bin`
   逐张量 cos 0.9955–1.000（token/class embedding 1.0000、attn q/k/v 0.997、mlp 0.997–0.999、两个 projection
   转置后 0.9989 / 0.9987），`logit_scale = 4.6037 ≈ ln 100`；随机初始化对照 cos ≈ 0；
4. 同一 harness 对照（marine_optical，343 图）：把 OpenAI CLIP ViT-B/32 权重按 open_clip 布局转换
   （302/302 keys）后得 **26.53 %**（GELU）/ **20.70 %**（QuickGELU）；RemoteCLIP 得 **12.83 %**（GELU，
   与归档小数点后两位一致）/ **14.29 %**（QuickGELU）。差异来自 checkpoint 本身，不来自加载或 harness。

**未归档**的补充判断（只用于本轮裁决，不入稿）：ImageNet-1k val shard 0（3,572 图，chance 0.10 %）上
OpenAI CLIP 60.13 %、RemoteCLIP 18.76 %（QuickGELU）⇒ RemoteCLIP 仍是 188× chance 的可用零样本分类器，
只是遥感微调把自然图像能力压到 18.76 %，故在这三个非遥感语料上落到 chance 上下。

**裁决**：21 单元 run 在"权重是否加载"意义上有效 ⇒ 按 (A) 分支写 21 单元，并把该编码器写成**第五条 limits**
（"top-1 within a factor of two of chance"）；ImageNet 数字因未归档不入稿。

### 9.3 正文改动与页数

- `paper_a2/ext_partII_domains.tex`：122–147 行换数字并新增第五条 limits；Source 行（148–165 行）改为
  21 单元字段路径（`conclusion.{n_encoders,n_units,n_ordered_pairs,n_scored_entries_cross_unit,
  n_entries_above_chance,n_entries_surviving_bootstrap,best_surviving_pair.{target_BA,source_fit_BA,delta_ci95}}`、
  `transfer.{self_pairs,cross_unit_pairs,summary.n_scored_entries_self_pairs}`、
  `limits.{probes.single_seed,class_imbalance.corpus_class_counts}`、
  `encoders.<encoder>.corpora.<corpus>.{frozen_row.top1,chance_percent,reproduction.max_abs_diff}`）。
- 页数：**73 页（与上一轮相同，未变）** ⇒ `paper_a2/verify_a23_fix.py` 的 `PAGES` 常量**无需改动，本轮未动该文件**。

### 9.4 门禁（本轮实测）

| 门禁 / 命令 | 结果 |
|---|---|
| `pdflatex -interaction=nonstopmode main_ieee.tex` ×2（`paper_a2/`） | 两次 exit 0；`Output written on main_ieee.pdf (73 pages, 1275901 bytes)` |
| LaTeX log | 0 error / 0 undefined reference / 0 undefined citation / 0 overfull hbox / 0 overfull vbox / 0 rerun；42 条 underfull，**其中 13 条落在本段**（"paragraph at lines 88--176"，含 Source 行 `\texttt` 字段列表；上一轮 §5 已记录该段存在同类 underfull） |
| `python paper_a2/verify_a23_fix.py` | **ALL CHECKS PASSED**（29 项 PASS；含 73 页、US letter、行号连续、12 pt 正文、37 个冻结归档 SHA-256 全绿） |
| `python -m tools.paper_audit audit --profile a23_joe --fail-on NONE` | 退出码 0；`BLOCKED` grade D，**pass=57 / fail=1 / warn=0 / manual=9 / skip=19 / error=0**；唯一 FAIL 是 `A-01`（`M paper_a2/ext_partII_domains.tex`，即预期的未提交 dirty）；报告 `docs/audits/AUD-a23_joe-20261025T001344Z.{json,md}` |
| `python tools/_p1428_provenance_gate.py` | **gate: PASS**（A23: floats=34 manifest=34 missing=0 pending=0 broken_paths=0；四篇合计同样 0/0/0） |

### 9.5 未溯源 / 诚实标注（本轮）

1. **分项计数是聚合值**：12/10/6/1、12/10/5、16/13 不是归档中的标量字段，由
   `transfer.pairs[].{target_encoder,source_corpus,self_pair} × by_statistic.*.bootstrap.survives`
   （仅非自对）聚合得到；聚合规则已写进 `docs/provenance_manifest.json` 的 `tab:calib_lodo` note。
2. **RemoteCLIP 的 ImageNet 数字未归档**：60.13 % / 18.76 % 是一次性 inline 复验（`data/imagenet_hf`
   validation-00000-of-00014.parquet，3,572 图），只用于判断、不入稿、也不进 manifest。
3. **RemoteCLIP 无历史复现行**：`_p1344` / `_p1352` / `_p1472` 都不含该单元，`reproduction.reference` 为
   `null`，故它是本格子里唯一**无法与旧归档交叉验证**的编码器；可交叉验证的四个单元仍是 `max|Δ| = 0`。
4. **本轮未改**：`paper_a2/verify_a23_fix.py`（页数未变）、`paper_a2/main_ieee.tex`、`SUBMISSION/**`
   （37 个冻结哈希全绿）、中文镜像 `zh_ext_partII_domains.tex`。
5. **`transfer.summary.survivors` 只列前 10 条**（脚本 `survivors[:10]`），29 条必须自行聚合
   `transfer.pairs[]`；正文与 manifest 引用的分项计数均按此聚合得到。
