# A23 终审：内容与论证逻辑（2026-10-25，只读）

> 审计者：`p3-stats`。对象：`paper_a2/main_ieee.pdf`（**73 页**，IEEE JOE `26-0663`，在审修订稿）。
> 方法：主文逐节通读 + 重点节（multi-encoder transfer、sonar 结果、discussion/limitations/conclusions、
> data availability）逐句核对 + 数字回查归档（`outputs/analysis/a23_multiencoder_transfer.json`、
> `outputs/sonar_protocol.json`、`outputs/sonar_protocol_full.json`、`a23_certificate_{adapted,control}.json`）
> + 检查 `SUBMISSION/**` 与 `publish_clean/`（v2.5 快照）内容。**未改任何稿件**（只写本笔记）。

---

## 0. 总体结论

数字主体是**扎实的**：我逐项核对了 multi-encoder 段的 21 units / 441 pairs / 4,940 entries /
179 above-chance / 29 survivors / 12-10-6-1 分布 / 27-of-29 σ-relative / 最好对 BA 0.900 与
chance 14.29/14.29/1.49、RemoteCLIP 12.83/11.27/2.43、以及"128 compared values on four units"——
**全部与归档字段一致**。主要问题集中在**新结果的叙述收口**（未进入 abstract/intro contribution/conclusion/
limitations）、**一处 3.4× vs 3.8× 的定义冲突**、**factor-of-two caveat 只写了一个 encoder**、
以及**data availability 对"compiled manuscripts 已入公开库/Zenodo"的过度声明**。

**最强三点**：① 精确预测器在五域四族逐点验证，并如实给出唯一例外（UATD collapse，3/6 λ）；
② domain-relative 适应配方用匹配 schedule + 三 seeds 给出 PEFT vs FullFT 的反例，sonar 与 marine 互为镜像；
③ 溯源纪律好（Appendix A 逐表列 script+archive；multi-encoder 段带 field path；归档与 publish 快照中结果文件哈希一致）。

**最弱三点**：① 新 "transfer" 结论统计上很薄（0.6% 幸存、全部同一 target corpus、source fit 仅 0.5、
target encoder 近 chance，且 27/29 是重标定统计量）；② "every cell of the domain–model matrix" 的措辞
强于枚举证据（38 conditions / 18-18 / 三分域 exact 不是逐 cell 计数）；③ 新结果游离于摘要/贡献/结论/limitations 之外，
加上 64→73 页的修订增量未在稿件内交代（应由 response letter 说明）。

---

## 1. 数字核对（全部通过）

| 论文数字 | 归档字段 | 结果 |
|---|---|---|
| 7 encoders / 21 units / 441 ordered pairs | `conclusion.n_{encoders,units,ordered_pairs}` | ✅ 7 / 21 / 441 |
| 4,940 scored cross-unit entries；21 self-pairs / 260 self entries | `conclusion.n_scored_entries_cross_unit`=4940；`n_scored_entries_self_pairs`=260 | ✅；我复算 420 cross pairs × 13 stats − 520 degenerate = 4940 |
| 179 above chance；29 survive 95% bootstrap | `n_entries_above_chance`=179；`n_entries_surviving_bootstrap`=29 | ✅（我按 cross-unit 非 degenerate 复算 = 29）|
| 12 SigLIP / 10 OceanCLIP / 6 RemoteCLIP / 1 CLIP-L/14；全部 acoustic-sonar target | `transfer.pairs[].by_statistic.*.bootstrap.survives` 重算 | ✅ 12/10/6/1，**29/29** target corpus = `acoustic_sonar` |
| 27 of 29 resolution-normalised，ε/σD ∈ {0.005,0.01,0.02} = 12/10/5 | 同上 | ✅ 27 σ-relative；12/10/5 |
| 最强对 BioCLIP(sonar)→SigLIP(sonar) mass_0p002，BA 0.900，source fit 0.500，ΔCI [+0.100,+0.500] | `best_entry_surviving_bootstrap` | ✅ 0.9 / 0.5 / [0.1,0.5] |
| chance 14.29 / 14.29 / 1.49 % | `limits.class_imbalance.chance_levels_percent` | ✅ 14.2857 / 14.2857 / 1.4925 |
| RemoteCLIP top-1 12.83 / 11.27 / 2.43 % | `encoders.remoteclip.corpora.*.frozen_row.top1` | ✅ 12.828 / 11.273 / 2.425 |
| "max|Δ|=0 over 128 compared values on four units" | `reproduction.pairs_checked`：28+28+36+36 = **128**，`max_abs_diff`=0（4 units） | ✅ |

> 另：`n_degenerate_entries`=533 与 4,940 的口径自洽（cross-unit degenerate 520 + self 13 = 533）——论文未印 533，无须改。

---

## (a) 必须修（矛盾 / 过强主张）

### A1（数字定义冲突）同一 flattening 量同时写成 **3.4×** 与 **3.8×**
- `paper_a2/main_ieee.tex:251`（正文）："on the *balanced* 650-image protocol the flattening is **$3.4\times$ deeper than terrestrial**
  ($0.0239\to0.0063$ vs $0.0216$), mirroring the marine magnitude ($3.6\times$)"。
- 同一节 `:260` 表格行 `SonarCLIP (balanced 650) … flatten **$3.8\times$**`；`:292` 图注 "**$3.8\times$ balanced**, $1.8\times$ full,
  $1.1\times$ terrestrial"；摘要 `:51` "sonar **$3.8\times$** at 650 images vs $1.8\times$ at 2,617"；intro `:73` 同 3.8×。
- 归档 `outputs/sonar_protocol.json`：frozen σm **0.0239**、SonarCLIP σm **0.0063** ⇒ 原始比值 0.0239/0.0063 =
  **3.79（3.8×）**；3.4× 只有把 terrestrial 自己的 1.1× 再除掉（3.79/1.106 = 3.43）才成立。
- **修法**：正文那句改为 "3.8× raw (3.4× after normalising by the terrestrial control's own 1.1×)"，或统一用 3.8×。
  否则 referee 只读一句就会当成矛盾。

### A2 新的 multi-encoder 有界结论没有进入摘要 / 贡献 / 结论 / limitations
- 新结论只存在于 `paper_a2/ext_partII_domains.tex:112-150`（4,940 entries → 29 survivors → "does produce transfer, but only
  inside one regime"，并明确 "the unqualified 'no threshold on M transfers' is therefore not supported"）。
- 但：摘要 `main_ieee.tex:51` 仍是 "**Four findings hold**"，无多编码器发现；
  intro contributions `:72-77` 六条 bullet 无多编码器；
  结论 `:784` "The gap-surgery diagnostic transfers …" 全段无该有界结论；
  limitations `:777` 七条无该条。
- **后果**：读者/审稿人从摘要与结论只看到"transfers everywhere"，而正文中段已经把一个更强否定句撤掉了；
  这是 lead 要求的"bounded claim 是否处处一致"的直接答案：**不一致**。
- **修法**（择一，最小）：在 conclusion 加 1 句（"a widened 7-encoder × 3-corpus test produces transfer on 29 of 4,940
  (pair, statistic) entries, all into the acoustic-sonar corpus"）；limitations 加第 (8) 条；摘要 "Four findings" 若不愿改
  可保持（摘要本来只列四条主发现），但 conclusion 必须有。

### A3 data availability 过度声明：稿件本体不在公开库/Zenodo 快照里
- `main_ieee.tex:839`："All analysis and experiment code, every result JSON … **and the compiled manuscripts are archived in
  the public project repository** https://github.com/MoYUYao666/gap-susceptibility **and in a versioned Zenodo snapshot
  (version DOI 10.5281/zenodo.23632347)**"。
- 核查：`publish_clean/`（v2.5 快照内容）**没有任何 A23 稿件文件**（无 `paper_a2/`，无 `main_ieee.tex/pdf`）——
  发布边界本来就不放稿件本体；`publish_clean` 的 v2.5 tag 时间 **11:13**，而当前 `paper_a2/main_ieee.tex` mtime **12:08**、
  PDF **12:09** ⇒ 即便只谈结果归档，当前 draft 也晚于该快照。
- 归档结果文件本身是同步的：`a23_multiencoder_transfer.json` live 与 `publish_clean/` 内 sha256 前缀同为 `634ef2ef…` ✅。
- **修法**：删 "and the compiled manuscripts"（或改成 "the compiled manuscripts are not part of the public snapshot"）；
  DOI 语句保留（数字本身对，v2.5 = `10.5281/zenodo.23632347`）。
- 与 lead 关注点的关系：**frozen submitted 包（64 页）确认没有 multi-encoder 材料、也没有 archive DOI**；当前 draft
  **没有任何句子暗示 reviewers 看过新材料**（grep `reviewer/revision/resubmi/submitted version` = 0 命中）✅；
  但"compiled manuscripts archived"这句是唯一会被 IEEE 出版合规挑出的过度声明。

### A4 factor-of-two caveat 只点了 RemoteCLIP，而归档显示"several encoders"
- `ext_partII_domains.tex:145-146`："… still limited by … **and by RemoteCLIP**, the encoder that widening adds, a remote-sensing
  fine-tune whose top-1 on these corpora sits within a factor of two of chance (12.83, 11.27 and 2.43 % against 14.29, 14.29
  and 1.49 % chance), so 6 of the 29 survivors take their target from it"。
- 归档 `encoders.*.corpora.*.frozen_row.top1` 与 chance 对比：**不止 RemoteCLIP**——
  SigLIP marine 11.95/14.29、**sonar 8.81/14.29（0.62×）**；CLIP-L/14 marine 26.53、sonar 17.11；
  OceanCLIP marine 12.54；BioCLIP sonar 6.67。尤其重要的是：**29 个幸存者里 12 个的目标编码器是 SigLIP**，
  而 SigLIP 在 sonar 上的 top-1 只有 chance 的 0.62 倍 ⇒ 这条 caveat 目前**把最强的 target 组漏掉了**。
- **修法**：改成 "several encoders sit within a factor of two of chance (RemoteCLIP on all three corpora; SigLIP on marine
  and sonar; CLIP-L/14 on marine and sonar; OceanCLIP on marine; BioCLIP on sonar), and 12 of the 29 survivors take their
  target from SigLIP, whose sonar top-1 is 8.81 % against 14.29 % chance"。
  这是 lead 所说的"第五个 limitation"：它现在只在段内作为第 5 条 caveat，**未进入 Limitations 编号列表**（见 A2）。

---

## (b) 逻辑缺口 / 审稿人会攻击的点

### B1 "every cell of the domain–model matrix" 强于枚举证据
- 摘要 `main_ieee.tex:51`："the exact predictor is verified to $10^{-4}$ **in every cell of the domain--model matrix** except
  the collapsed UATD fine-tune"；结论 `:784` 同义。
- 实际枚举是 "marine 38 plotted conditions ≤1e-4；sonar 18/18；ImageNet-5k/DTD/Food101 exact" —— 这些是**条件/图**，
  不是 5 domains × 4 families = 20 个 cell 的逐 cell 计数；本地归档 `a23_tau_calibration.json` 仅覆盖 BioCLIP↔OceanCLIP。
- **修法**：改为 "in every measured condition" 或补一张逐 cell 表/归档；否则 referee 会要 matrix 明细。

### B2 "sonar 18/18 zero deviation" 与 "collapsed UATD fine-tune (3 of 6 λ)" 并列，指代不清
- 结论 `main_ieee.tex:784`："sonar 18/18 zero deviation … the collapsed UATD domain fine-tune is exact in 3 of 6 λ with
  deviations ≤ 0.016"。UATD **也是 acoustic sonar 数据集**，读者会问"18/18 是否包含 UATD"。
- **修法**：写成 "NKSID sonar 18/18 …；the separate UATD fine-tune …"。

### B3 撤否定的写法像"内部修订痕迹"
- `ext_partII_domains.tex:138-139`："The unqualified ``no threshold on $M$ transfers'' is therefore not supported and is
  replaced by this bounded statement"——但全文没有别处出现这个 unqualified 否定句（我 grep 过：仅此处），读者不知道在撤什么。
- **修法**：改为正面陈述（"widening the test shows transfer in one regime, which bounds the earlier negative reading"），
  或明确 "an earlier version of this analysis"。

### B4 64→73 页的修订增量未在稿件内交代（应由 response letter 承担）
- 无 "reviewer/revision" 字样（✅ 无"reviewers 看过"的暗示），但新增 multi-encoder 段使页数 64→73；
  若 response letter 未逐项声明新增内容，审稿人会发现"材料变多但未说明"。
- 这是流程项，不是稿件缺陷；**建议**在 response letter 中列为新分析并引用 `a23_multiencoder_transfer.json`。

### B5 "128 compared values on four units" —— 已核实 ✅（不是缺口，作为正面记录）
- `ext_partII_domains.tex:147` 的 128 来自 `reproduction.pairs_checked` 28+28+36+36，四 units 的 `max_abs_diff`=0。
  数字有 archive field，通过。

---

## (c) 润色 / 一致性（不影响结论）

1. 摘要 `main_ieee.tex:51` "Four findings hold" 与新增第 5 个有界发现不匹配（见 A2）；若加结论句建议改 "Five findings (the last bounded)"。
2. intro 贡献列表 `:72-77` 缺 multi-encoder bullet（见 A2）。
3. `:267` 表注说 "the full grid **exact in all 18 conditions to four decimals**"，正文 `:166` 一带说 "zero deviation" —— 同一事实两种措辞，统一为 "zero deviation to four decimals"。
4. `:251` "3.4× deeper than terrestrial" 与 table/caption "3.8×" 的术语差异（A1 的具体表现）。
5. limitations 现为 (1)–(7)，编号连续；若加 multi-encoder 条，注意保持编号引用（正文 "Section V-I" 等是 `\ref`，不会因编号变而变化）。

---

## 附：未能核对项（诚实标注）

- **DoRA/POPE 等外部文献数值**：本任务只读本仓库，未联网核对第三方论文；A23 的外部引用数字（如 companion study 的
  59.3%→32.0%）未逐条重查（其上轮已由 repository 台账覆盖）。
- **multi-encoder 幸存者的独立性**：只能按归档复核，无法重跑（7 encoders × 21 units 的原始 embedding 不在本地）。
  论文已把该段写成 bounded statement，这一点是诚实的。
- **"several encoders near chance" 的准确措辞**：我按归档 `frozen_row.top1 / chance_percent` 的比值 ≤2 计算；
  若作者采用别的定义（例如只在 target 为 acoustic_sonar 时算），需要作者确认——但至少 RemoteCLIP 不是唯一一个。

---

# Applied fixes（2026-10-25 第二轮，操作者"全改"）

> 编辑范围：`paper_a2/main_ieee.tex`、`paper_a2/ext_partII_domains.tex`；
> 派生 `paper_a2/abstract.tex` / `abstract.pdf`（用 `tools/build_abstract_standalone.py` 重新生成）；
> staged 包 `SUBMISSION/A23_JOE_next_revision/`（`Manuscript.pdf` 重建 + `SHA256SUMS.txt` 刷新）。
> **`SUBMISSION/A23_JOE/`（冻结包）未动**；未提交。改动后 **main_ieee.pdf = 73 页**（0 errors / 0 overfull）。
> 行号以改动后的 `main_ieee.tex` 为准（行内改写，未增删行处行号不变）。

## (a) 必修项

1. **3.4× vs 3.8× 冲突（A1）** — `main_ieee.tex:251`：删 "3.4× deeper than terrestrial"，统一为
   "the flattening ratio is **3.8×** ($0.0239\to0.0063$, the raw frozen-to-adapted spread, against 1.1× for the
   terrestrial control)"；正文/表 `:260`/图注 `:292`/摘要 `:51`/intro `:73` 现为同一 3.8× 定义；
   来源 `outputs/sonar_protocol.json`（0.0239/0.0063 = 3.79）。
2. **bounded transfer 进入摘要/结论/limitations（A2）** —
   - 摘要 `:51`：`Four findings hold` → **`Five findings hold`** + 第 5 句
     "Fifth, widening the transfer test to 21 encoder–corpus units gives transfer in one regime: 29 of 4,940
     entries survive bootstrap, all with acoustic-sonar targets; several encoders, including SigLIP
     (12 survivors' target), are within a factor of two of chance."
   - 结论 `:784`：新增 "A widened transfer test (7 frozen encoders × 3 corpora) bounds the earlier negative
     reading: 29 of 4,940 cross-unit (pair, statistic) entries keep a bootstrap interval above chance, all with
     acoustic-sonar targets and 27 of them resolution-normalised, while several encoders sit near chance."
   - limitations `:777`：新增 **第 (8) 条**（21 units / 441 pairs；29 of 4,940 survivors；all acoustic-sonar；
     27 resolution-normalised；九配置 median split / 类不平衡 / 单 probe seed / 声明式提取路径 /
     several encoders within 2× chance，含 SigLIP 12/29 与 sonar top-1 8.81% vs 14.29%）。
3. **Data availability 去掉 "compiled manuscripts"（A3）** — `main_ieee.tex:839`：删
   "and the compiled manuscripts"；保留 v2.5 version DOI `10.5281/zenodo.23632347`（数字本身正确）。
   `abstract.tex` 用 `tools/build_abstract_standalone.py` 重生成以匹配新摘要（`verify_a23_fix.py` 的
   `abstract.tex == main_ieee.tex` 检查恢复 PASS）。
4. **factor-of-two 从 RemoteCLIP 扩到 several encoders（A4）** — `ext_partII_domains.tex:138-146`：
   "several encoders whose top-1 sits within a factor of two of chance (RemoteCLIP on all three corpora;
   SigLIP on marine and sonar, the target of 12 of the 29 survivors, at 8.81 % sonar top-1 against
   14.29 % chance; CLIP-L/14 and OceanCLIP on marine, BioCLIP on sonar), with 6 of the 29 survivors taking
   their target from RemoteCLIP"；limitations (8) 同口径复述。

## (b) 逻辑缺口

5. **"every cell of the domain–model matrix" 弱化** — 摘要 `:51` 与结论 `:784` 改
   "**every measured condition** of the domain–model matrix"；结论枚举压缩为
   "(marine 38 conditions ≤10⁻⁴; NKSID sonar 18/18 zero deviation; ImageNet-5k, DTD, Food101 exact;
   the collapsed UATD fine-tune, also acoustic, exact in 3 of 6 λ with deviations ≤0.016)"。
6. **"sonar 18/18" 与 UATD 例外消歧** — `main_ieee.tex:72`、`:784`、`ext_partII_domains.tex:59`
   统一为 "**NKSID** sonar 18/18"；结论注明 UATD 是 "**also acoustic**" 的独立 fine-tune。
7. **撤否定句改为正面陈述** — `ext_partII_domains.tex:138`：删 "The unqualified 'no threshold on M transfers'
   is therefore not supported and is replaced by this bounded statement"，改为
   "The correct statement is therefore bounded: a threshold on $M$ transfers only inside this one regime,
   and the claim that no threshold transfers is not supported"。

## (c) 一致性/压缩

8. **摘要 DTD 全称保留**（`:51`）以通过 `verify_a23_fix.py` 的 text-layer probe；代价由第 5 句压缩抵消。
9. **守 73 页的布局级压缩（不删主张）**：fig1 `0.92→0.84`、fig2 `0.92→0.84`、fig6 `0.90→0.82`、
   fig7 `0.85→0.77`（`:201,305,220,291`）；`Future work`（`:779`）与 Discussion 冗词同义压缩；结论枚举去重。
   重建后 **73 页、0 errors、0 overfull**。

## 验证（base 解释器 `D:\Anaconda\python.exe`）

- `paper_a2/verify_a23_fix.py` → **`ALL CHECKS PASSED`**（含 `abstract.tex == main_ieee.tex`、main PDF 73 页 /
  0 errors / 0 undefined / 0 overfull、frozen archive 37 个哈希未变）。
- `tools/_p1631_a23_next_revision.py --apply` → `Manuscript.pdf` **73 页**（sha256 `7fbfc45f83273d73…`，
  与 `paper_a2/main_ieee.pdf` 一致）、`SHA256SUMS.txt` 6 条刷新；`--verify-tex` 独立 zip 编译 73 页 0 errors。
- `python -m tools.paper_audit audit --profile a23_joe --fail-on NONE` →
  **`BLOCKED grade D pass=57 fail=1 warn=1 manual=9 skip=18 error=0`**；唯一 blocker
  **`A-01 uncommitted changes under paper_a2`**；warn **`I-02 frozen submitted package
  (not compared with the live draft)`**（预期）。报告：`docs/audits/AUD-a23_joe-20261025T083825Z.{md,json}`。

## 未解/需作者确认

- staged 包内 `Supplementary.pdf` 仍是冻结的 43 页审稿人包（按包定义不随本次修改更新，README 已写明）。
- 本笔记中 "several encoders" 依归档比值 ≤2 定义；若作者采用别的定义需作者确认（见上）。

