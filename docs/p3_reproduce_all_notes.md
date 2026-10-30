# P3 全量复现台账 — 工作笔记（2026-10-24）

**产出件**：`tools/_p1637_p3_reproduce_all.py`、`paper3/REPRODUCE.md`、
`outputs/analysis/p3_reproduce_manifest.json`。
**本次未改动任何稿件/归档**（工具本身只读归档）。

---

## 1. 台账计数（本机实测）

运行：`python tools\_p1637_p3_reproduce_all.py`（退出码 1，因为有 MISMATCH）

| 状态 | 条数 |
|---|---|
| `OK` | **832** |
| `MISMATCH` | **2** |
| `UNSOURCED` | **45** |
| `UNCHECKED` | 0 |
| 合计 | **879** |

**30 / 46 个小节完全有源**（主文按 MAIN-Abstract/I/Table-I/Table-II/III/IV-B/IV-E/V/VII/Data
分组，补充材料按 S4–S43 分组，见 `--summary`）。

---

## 2. ⚠️ 最重要的发现：稿件正在被并发修改

我读取稿件时，**另一个会话正在改同一批文件**。实测：

```
git status --porcelain
 M paper3/paper_ieee/sections/experiments.tex          (22:11:59)
 M paper3/paper_ieee/sections_full/experiments.tex     (22:12:09)
 M paper3/paper_ieee/supplementary/supplementary.tex   (22:11:16)
```

**后果（可直接导致投稿被退）**：`supplementary.tex` 从我第一次扫描时的 **43 个编号 section**
变成了 **46 个**——中间插入了 3 个新小节（S20 配对再分析、S35 临界秩不是一个数、
S46 适用范围边界），后面全部后移。于是：

| 稿件里写的 | 文件里现在实际是 |
|---|---|
| 正文 `main.tex:108` "Supplementary Sections **S1--S43**" | 文件有 **46** 个编号 section |
| `discussion.tex` "does not replicate (**Section~S20**)"（指 Qwen2.5-VL） | **S20** 现在是"配对再分析"，Qwen2.5-VL 已移到 **S21** |
| `discussion.tex` "(**Section~S18**)"（指二阶占比） | **S18** 现在是"一阶近似的曲率"，仍是曲率，但需复核编号 |
| 我台账里 S11/S12/S13… 的编号 | 与文件当前编号**整体错位** |

**建议（未擅自施行）**：改用 `\label`/`\ref` 交叉引用，或公布前统一重编号并复核主文里
所有 `Section~S\d+` 指针。当前主文有 6 处硬编码 S 编号。

> 台账里的 `section` 字段（S4、S11、S33…）是**按稿件原文所述主题**标注的，不是文件当前序号；
> `REPRODUCE.md` 已就此加了说明。工具重跑即可刷新数值，但编号漂移需人工决定。

---

## 3. MISMATCH（2 条）

| ID | 位置 | 稿件 | 复现 | 原因 | 建议一行修复 |
|---|---|---|---|---|---|
| `m-supp-s43` | `main.tex:108` | `S1--S43` | 文件有 **46** 个编号 section | 补充材料在稿件定稿后被扩写（见上节） | 把正文改为 `S1--S46`，或把新增的 3 节移出编号序列（改用 `\section*`）；并用 `\ref` 替换所有 `Section~S\d+` |
| `s11-corr-cg` | 补充材料 Table S11 | `r(rank, CG) = -0.43` | `-0.4248` | 归档值第三位小数为 4，`-0.4248` 应舍入为 `-0.42`，稿件印成 `-0.43` | 把 S11 该格改为 `-0.42`（或在表注说明取整方式） |

---

## 4. UNSOURCED（45 条）分类与建议

### 4.1 稿件自己声明的缺口（1 条，无需处理）

| ID | 内容 | 说明 |
|---|---|---|
| `s28-steps` | S28 优化器步数 | 稿件原文即写 "the optimizer step count is not archived"，已核实 `cloud_vqa_full451_*` 确无该字段。**这是诚实声明，不是缺陷。** |

### 4.2 近似值 / 第三方数字（9 条，建议保留但确认措辞）

| ID | 内容 | 建议 |
|---|---|---|
| `s1-llava-min` | `~34 min/run` | 保留波浪号即可；LLaVA 逐 run 有 `elapsed_min`，但这是整批均值，无对应字段 |
| `s1-qwen-min` | `~1--2 min/run` | 云端 run 记录**无耗时字段**，保留 |
| `s1-cost` | `~$7.5 total` | 账单数字，保留 |
| `c-usd8` | `~$8 USD` | 同上 |
| `s1-qwen-stack` | `bitsandbytes 0.49.2` | 归档不存该版本号；建议改写成"the version recorded in the run logs"或补记字段 |
| `f2-mdi-llava` / `f2-mdi-qwen` | `10.23` / `33.10` | Wu et al. 第三方数字，已带引用，保留 |
| `c-five-seed-quote` | 结论里重复引述的五个 per-seed 值 | **已在 S12/S13/S22 逐条断言**，此处不重复列，避免同一错误报两次 |
| `c-zenodo-doi` / `m-github` | DOI 与仓库 URL | 外部标识，不可复现，已在台账显式记录 |

### 4.3 解析式陈述（非测量，7 条，建议在台账里保留 `analytic` 标记）

`t-c2`（指数分配 = KKT 结果）、`t-c3`（`r_c` 存在性 = 推论）、`t-ode-beta`（定义式关系）
——这些是推导不是测量；它们的**实测实例**已在 `f4-gamma-*`、`S18`、`S34` 逐条断言。

### 4.4 引述他文（5 条，Paper 1/2 的数字，超出 P3 归档范围）

`t-proj-var`（`Var(Gamma)/Var(H) > 20x`）、`t-proj-eps`（`eps_proj < 0.05`）、
`t-identifiability`（`theta_0: r = -0.27`）、`t-ers-k`（`k = 0.088`）、
`t-intro-r2`（`R^2 > 0.96`）、`t-textonly-5`（"5 architectures"）、`t-ers-plateau`。
**建议**：这些应在 Paper 1/2 的台账（`tools/_claim_ledger*.py`）里断言，P3 台账只登记"引用他文"。

### 4.5 归档里对不上的数字（23 条，**需要逐条处理**）

这一类是重点——稿件数字在 P3 归档里**找不到对应量**：

| ID | 稿件 | 归档实际值 | 建议一行修复 |
|---|---|---|---|
| `c-p6-instruction` | `+83.0 / -7.5`（instruction protocol） | 十seed家族：r6 `+71.2/+66.8`、r5 `-49.0/-1.33`；五seed：`+65.5/-23.0`；密集 sweep：`+87.3/-43.7` | 改为主文其他处已断言的 `+65.5 / -23.0`（五seed，S12 口径），或指明这组均值来自哪个归档 |
| `c-p6-caption` | `+66.5 / -39.5`（caption protocol） | `-39.5` 只作为 hessian 环境桶里的无关 per-seed 值出现 | 补 caption-protocol 的 ⟮rank⟯ 归档，或删去该对数字 |
| `f2-llava-surge` | LLaVA `46x` surge | `dE(r=16)/|dE(r=4)|` = **15.0**（合并批次）、**11.1**（密集 sweep） | 改为 `15x`，或说明 46x 的分母口径 |
| `c-diverge16` | r=16 时 3 seed 中 2 个发散 | 密集 sweep 里 r=16 三条轨迹**全程有限** | 指明发散证据来自 `p3_nan_diagnostics.json` 的日志扫描，并补 rank 索引；否则改写 |
| `c-diverge20` | r=20 时 3 个全发散 | 同上，三条均有限 | 同上 |
| `e-paired-diff` | 4 对配对 `+11.5`，CI `[+6.8, +16.2]` | 归档有两组 Gamma-vs-random 配对：by-seed `+1106.5`(3对)、by-plan `-1870.0`(10对)，**都不是这一组** | 补 4 对配对归档，或改用现有配对及其真实数值 |
| `e-power-hi` | `11 to 28 seeds` 的 28 | 归档 spread 代入得 12.6（within-plan σ）、27.9（pool σ=4771.2）；**28 需 σ≈4776，无对应字段** | 改为 `11 to 12`（用归档 σ），或补记 28 所用 σ |
| `e-reversed-p3` | 三seed 时 `p = 0.037` | 归档只有六seed 的 `p = 0.206` | 补三seed 归档，或删去该回溯数字 |
| `q-blank-cross` / `s8-real-eval` / `s6-real-range` / `s6-real54` | Qwen2-VL-2B held-out 评测的 `-135..-271`、`-260`、`+179`、`+194..+450`、`-519..-185`、`-554/-471` | 该 per-rank 表**不在 P3 归档树里**（只有 sweep 汇总与本地 blank 重跑） | 把该 held-out 重评表归档进 `outputs/analysis/`，否则从 S6/S8 与主文删除这些区间 |
| `s32-signed-de` | 签名 Gamma `+232.5` / `+264.0` | `p3_signed_gamma_beta.json` 只有 β 网格与分配，**无训练臂** | 补训练臂归档，或删去该列（分配本身已断言） |
| `s33-signflip-*`（3 条） | 配对符号翻转 `p = 0.061 / 0.039 / 0.014` | 归档 `conclusion` 只有计数与最小值，**无逐对字段** | 在 `_p1595` 输出里补 `paired_signflip_p`，或删去这三个 p |
| `s33-pair-cis` | 逐对 bootstrap CI `[-77.20,-0.25]`、`[-37.35,-7.75]` | `separation.pairs` 只有精确 p 与差值，**无区间** | 补区间字段，或删去这两个 CI |
| `c-runs-132` | "132 runs on the present protocol" | 实验树共 374 个归档、跨多个 run family 与命名约定，**无字段枚举"本协议 run 数"** | 定义并归档一个 `n_runs_present_protocol` 字段，或改写为可核的口径 |

### 4.6 表格行完整性占位（4 条，无需处理）

`s16-adalora-claim`、`s16-igu-claim`、`s16-signed-claim`、`s16-three-s28`：
这些是 S17 `tab:claims` 里指向别处数字的**行引用**，其数值已在 `e-adalora-*`、`s39-arm`、
`s32-*`、`s28-*` 逐条断言，此处仅登记行已入账。

### 4.7 豁免项（2 条，符合 AGENTS 的 provenance 规则）

`s9-qwen-mse`（Table `tab:comparison` 是纯文献方法对比表）、`s22-hardware`（声明的局限，
非数字）。按"纯文献表/示意图可豁免但须显式标注"的规则登记为 UNSOURCED 而非断言。

---

## 5. 顺带确认的两条口径（已写进 REPRODUCE.md）

这两条是我一开始搞错、被归档自身纠正的，**后续做同类台账必须按归档口径**：

1. **相位表印的是总体标准差（ddof=0），不是样本标准差。**
   Table II 的 7 个 LLaVA 行 + 7 个 Qwen 行、Table S23（`tab:env`）、S37（`tab:envvar`）、
   S31（`tab:robust`）**全部**匹配 `sd_population`。
   **例外**：Table S34（`tab:crossing10`）匹配的是**样本**标准差，台账按样本口径校验。
2. **整数是显示舍入**：Table S10 印一位小数（`-102.5`）而主文 Table I 印整数（`-102`）。
   台账按各自印刷位取半单位容差，所以差 1 个单位仍会失败。

---

## 6. 工具的设计约束（供复核者）

- **不做模糊匹配**。每个数字**人工指名**归档 + 精确字段路径 + 复现规则。
  理由见 `AGENTS.md`：`tools/_reproducibility_gate.py` 曾在 122,161 个归档值里以 0.5% 容差
  搜出 145/145 通过——**纯属假象**。
- **无 expected 值的条目不再静默通过**（本次修掉的缺陷）：原先 `expected=None` 会直接返回
  `OK`，现已改为 `UNCHECKED` 状态并单独列出，本次为 0。
- **输出确定性**：无时间戳；manifest 里唯一随运行变化的是 git commit，且不参与比对。
- **归档键含点时自动识别**：`comparisons["exp_beta_paper_0.137"]`、
  `["p3d_qwen_ranksweep.json_pairs"]`、`["cluster_3921.0"]`、
  `envs["torch 2.9/cu130"]` 这类键用贪心最长匹配 + `::` 字面量语法解析。

---

## 7. 建议的下一步（**未施行，需操作者决定**）

1. **先冻结稿件**再重跑本工具——当前每十来分钟文件就变一次，台账数值会被追着改。
2. 决定补充材料编号策略（`\ref` 化 or 重编号），并复核主文 6 处 `Section~S\d+`。
3. 按 §4.5 的 23 条逐条处理：**补归档**（Qwen held-out 重评表、签名 Gamma 训练臂、
   逐对符号翻转 p、逐对 CI、4 对配对、132-run 口径）或**改数字/删数字**。
4. 把 §4.4 的 Paper 1/2 数字移入对应稿件的台账，本台账只留"引用他文"标记。