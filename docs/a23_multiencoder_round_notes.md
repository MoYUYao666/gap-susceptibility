# A23 多编码器阈值迁移 — 本轮改动记录（2026-10-24）

本轮只动三处：`paper_a2/ext_partII_domains.tex`（正文段落 + Source 行）、`docs/provenance_manifest.json`
（A23 条目 `tab:calib_lodo`），并重建 `paper_a2/main_ieee.pdf`。依据归档：
`outputs/analysis/a23_multiencoder_transfer.json`（脚本 `tools/_p1614_a23_multi_encoder_transfer.py`，
本地 5 单元运行：`clip-vit-base-patch32` x {marine_optical, acoustic_sonar, rare_species} +
`bioclip` x rare_species + `oceanclip` x rare_species）。

## 1. 文件与行号

| 文件 | 位置 | 改动 |
|---|---|---|
| `paper_a2/ext_partII_domains.tex` | 新增 第 121-133 行 | 在"$M$ 不给出可迁移阈值"一句之后扩写：负结论的证据基础扩到本地全部有序对（3 编码器 x 3 语料、5 单元、25 有序对、260 条跨单元条目、7 条名义高于 chance、0 条通过 bootstrap） |
| 同上 | 新增 第 137-138 行 | `Source:` 行补 `tools/_p1614_a23_multi_encoder_transfer.py` 与 `outputs/analysis/a23_multiencoder_transfer.json`；原有 `_p1472` / fine-eps 两条（第 134-136 行）保留 |
| `docs/provenance_manifest.json` | 第 1049-1058 行（A23 `tab:calib_lodo`） | `note` 记入该段主张的脚本/归档/字段路径与本地数值；`archives` 增加 `outputs/analysis/a23_multiencoder_transfer.json`；`status` 保持 `verified`（脚本与两个归档均存在，数字取自 JSON） |
| `paper_a2/main_ieee.pdf` | — | `pdflatex -interaction=nonstopmode main_ieee.tex` x2 重建 |

该主张落在正文散文、不是浮动体，故按指示挂到最接近的既有条目 `tab:calib_lodo`（留一域校准探针，同属
"跨域迁移/校准"）。`paper_a2/main_ieee.tex` 未改（Source 行在段落内，无需进附录）。

## 2. 页数

- 重建前 72 页，重建后 **72 页**（`main_ieee.log`：`Output written on main_ieee.pdf (72 pages, 1272927 bytes)`）。
- `paper_a2/verify_a23_fix.py` 的 `PAGES = 72` **无需修改**。
- 日志干净：0 error / 0 undefined reference / 0 undefined citation / 0 Overfull \hbox / 0 "Rerun to get"。

## 3. 门禁结果

| 命令 | 结果 |
|---|---|
| `python paper_a2/verify_a23_fix.py` | **ALL CHECKS PASSED**（29 项全 PASS；72 页；frozen archive 37/37 SHA-256 未变） |
| `python tools/_p1428_provenance_gate.py` | **gate: PASS**（A23 floats=34 manifest=34，missing=0 pending=0 broken=0；四稿合计同样为 0） |
| `python -m tools.paper_audit audit --profile a23_joe --fail-on NONE` | **BLOCKED, grade D**，`pass=57 fail=1 warn=0 manual=9 skip=19 error=0`；唯一 FAIL = `A-01`(P1) "Git working tree is clean for the manuscript paths"（`uncommitted changes under paper_a2`）——即本轮未提交的 `paper_a2/ext_partII_domains.tex`，属预期的 git-dirty 失败，其余全部 PASS。报告：`docs/audits/AUD-a23_joe-20261024T105710Z.md` / `.json` |

对照：改动前的同 profile 基线（输出到临时目录，未入库）为 READY/grade A、`pass=58 fail=0`；差值恰为 A-01 一项。

## 4. 放宽了什么、保留了什么限制

放宽（全部来自 `outputs/analysis/a23_multiencoder_transfer.json`）：

| 正文写法 | 归档字段 |
|---|---|
| 3 个冻结编码器（generic-CLIP 对照 + 两个适配编码器） | `conclusion.n_encoders` = 3；`registry.encoders.<enc>.group` / `notes` |
| 3 个语料、5 个 encoder-corpus 单元 | `conclusion.n_corpora` = 3、`conclusion.n_units` = 5（`transfer.n_units` = 5） |
| 全部 25 个有序对 | `conclusion.n_ordered_pairs` = 25（`transfer.n_pairs` = 25） |
| 每对 13 个阈值统计量 | `conclusion.n_statistics_per_pair` = 13（`meta.statistic_keys`，13 个键） |
| 260 条已评分跨单元（对, 统计量）条目 | `transfer.summary.n_scored_entries_cross_unit` = 260（自对 65 条不计入主张：`n_scored_entries_self_pairs`） |
| 7 条名义高于 chance 0.50 | `conclusion.n_entries_above_chance` = 7（chance = `transfer.protocol.chance` = 0.5） |
| 0 条通过图像 bootstrap 区间 | `conclusion.n_entries_surviving_bootstrap` = 0（区间字段 `transfer.pairs[].by_statistic.<key>.bootstrap.delta_vs_chance_ci95`） |
| 2,000 次图像重采样、源阈值每次重拟合、同语料配对否则独立 | `meta.selection.bootstrap_draws` = 2000、`n_boot` = 2000、`transfer.protocol.bootstrap`、`pairs[].bootstrap.paired` |
| 最强名义条目：OceanCLIP/marine 子集 -> generic CLIP/光学语料 @ eps=0.01，BA 1.000、源拟合 0.500、区间 [-0.150, +0.500] | `conclusion.best_pair_point_estimate.{source,target,statistic,target_BA,source_fit_BA,delta_ci95}` |
| 精确复现归档证书（max abs diff = 0，128 个比较值、4 个单元） | `encoders.<enc>.corpora.<corpus>.reproduction.{max_abs_diff, pairs_checked, reproduced}` |

保留的限制（正文明确写出）：① 这是部分选择 —— 5 / 21 个已注册单元（`7` 个注册编码器 x `3` 个语料，
`limits.encoder_count.n_registered` = 7）；② 适配编码器的提示词沿用先前协议
（`registry.corpora.rare_species.prompt_template` = "a photo of a {name}"，`meta.prompt_note`）；
③ 最强名义条目的区间含零（`delta_ci95` = [-0.150, +0.500]），故负结论按"本次选择所支持的范围"扩写，
未写成"所有已注册编码器 x 语料"（云上 21 单元网格尚未跑，`conclusion.effect_on_a23_text.action` 亦如此要求）。

## 5. 需要人工确认的数字

- **"3 个编码器 + 对照"**：任务书写的是"three encoders plus the control"（读作 4 个），但 JSON 的
  `conclusion.n_encoders` = 3，且 generic-CLIP 对照本身是这 3 个之一
  （`registry.encoders.clip-vit-base-patch32.notes`："the generic-CLIP control of the published negative claim"）。
  正文按 JSON 写成"3 个冻结编码器——generic-CLIP 对照与两个适配编码器"。
- **JSON 内部有一处措辞张力**：`conclusion.claim` 写的是"no-transfer claim can be widened to every registered
  encoder x corpus pair"，而同一文件的 `conclusion.effect_on_a23_text.action` 明确要求"只有在完整 21 单元网格
  分析之后才能扩写句子"。本轮按后者执行（正文把扩写范围限定为本次选择），并把 `conclusion.claim` 的强写法
  留给云上网格跑完后再用。
- **`21`**（= 7 注册编码器 x 3 语料）是 `limits.encoder_count.n_registered` 与 `conclusion.n_corpora` 的乘积，
  不是单一字段；**`128`** 是四个单元 `reproduction.pairs_checked`（28+28+36+36）之和，也不是单一字段。
  两者均由字段直接相乘/相加得到，未做任何估计。
