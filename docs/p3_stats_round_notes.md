# P3 扩展秩分离统计 —— 入稿记录（2026-10-24）

本轮把机器可验证的秩分离统计（证据文档 `docs/p3_rank_separation_text.md`，归档
`outputs/analysis/p3_rank_separation_extended.json`，脚本 `tools/_p1595_p3_rank_separation.py`）
写入 P3 工作稿补充材料 `paper3/paper_ieee/supplementary/supplementary.tex`，并把两个审计脚本
`paper3/paper_ieee/audit_check.py`、`paper3/paper_ieee/audit_pdf.py` 的期望值重新播种到新版本。

**写入范围**：仅 `paper3/paper_ieee/`（补充材料源文件 + 两个审计脚本）与本文件。
未触碰 `SUBMISSION/**`、`HANDOFF.md`、`文件地图.md`、`docs/provenance_manifest.json` 及其它论文。

## 1. 改动清单（行号 = 改后的 supplementary.tex，全文 1729 行）

| # | 位置（行） | 章节 | 改动 | 依据 |
|---|---|---|---|---|
| 1 | 1206–1213 | S28 正文 | "1434 training pairs per epoch, 4302 optimizer steps" → **1793 training pairs, three epochs**，并写明 `meta.train_samples = 1793`、`meta.epochs = 3`、**步数未归档**；追加 TOST 边际预先声明的理由（单臂 300 题准确率二项标准误 ≈0.027–0.028，故 ±0.05 为分辨率下限）与三臂按题配对说明 | 三份归档 `outputs/analysis/cloud_vqa1793_{base,5,6}.json` 的 `meta.train_samples=1793`；`paper3/train-vqarad.parquet` 1793 行；失败的旧值 1434/4302 仅见于 `HANDOFF.md:153` 与生成脚本 `tools/_p1562_integrate_round3.py:41-42` |
| 2 | 1226–1238 | S28 表 `tab:vqa` 标题 | 重写为：token F1 两秩均优于 base（+0.0713 / +0.0647，95% CI [+0.0204,+0.1235] / [+0.0194,+0.1103]）；准确率仅 r=5 显著（+0.0633，[+0.0133,+0.1167]），r=6 未达显著（+0.0200，[-0.0233,+0.0633]）；**r5−r6 token F1 在预先声明 ±0.05 边际下等效（TOST p=0.0074）**；**r5−r6 准确率反转 +0.0433（[+0.0033,+0.0833]），在 ±0.05 下未达等效（TOST p=0.351，最小可等效边际 0.0767）**；原句"no rank ordering"已重写为"token F1 上不构成排序、准确率方向与能量图景相反"；补 Source 行 | `vqa_equivalence.contrasts`、`vqa_equivalence.claim_verdict`、`vqa_equivalence.arms` |
| 3 | 1264–1270 | S29 表 `tab:envcloud` 标题 | 归档 glob `verify_r5_s42_*_a10_torch26.json` 之外**显式列出 r6 那一行**：`verify_r6_s42_lr5e-05_nw_float1_adamw_e3_bcuniform_a12_torch26.json`（+42.0）；r5 路径也由 glob 改为全名并加 `\allowbreak` 以避免溢出（标志 F9） | 两份 JSON 实测 `delta_E`：r5 = −35.5、r6 = +42.0，与 S29 表格印刷值一致 |
| 4 | 870–871 | S17 主张表 `tab:claims` | ①r5-vs-r6 的近似值 `p≈1.1e-5` 改为精确值 `p=2/C(20,10)=1.08e-5` 并写明"15 对中 14 对在 5% 水平分离、Holm–Bonferroni 后同样 14 对"；②"complete separation"改为"complete sign split at r=5/r=6；除 r=7 vs r=8（p=0.071）外相邻对均分辨" | `separation.pairs`、`separation.n_separating_holm_p05`、`conclusion.sign_split` |
| 5 | 879 | S17 主张表 | VQA 行：`1434 training pairs` → `1793 training pairs`，并写明 token F1 等效（TOST p=0.0074 @ ±0.05）与准确率反转 +0.0433 | 同 #1、#2 |
| 6 | 1437–1449 | S33 表 `tab:crossing10` 标题 | 明确符号划分（r=3,4,5 全 10 个为负；r=6,7,8 全 10 个为正）；**15 对全测**：14/15 在 5% 水平分离，其中 **10 对取到最小可达 p=2/184756=1.08e-5**（含此前无归档的 r5-vs-r6）；唯一不分离的是相邻对 **r7 vs r8（差值 +40.0，精确 p=0.071）**，其 bootstrap CI [-77.20,-0.25] 仅以 0.25 越过零，**两者不一致时以精确置换检验为准**；补 Source 行（新 JSON + 15 对字段路径） | `separation.pairs`、`separation.n_separating_holm_p05`、`conclusion.*` |
| 7 | 1453–1467 | S33 新正文段 | 15 对精确置换（枚举 C(20,10)=184756 个划分）、Holm 校正、四个相邻对数值（r3r4 −23.05 p=0.0100；r4r5 −53.95 p=0.00235；r5r6 −131.0 与 r6r7 −107.7 均 1.08e-5）、配对符号翻转检验（2^10=1024，最小 p=0.0020，12 对取到；r7r8 p=0.061；r3r4/r4r5 较不敏感） | `separation.pairs[i].p_exact/p_holm/ci95_diff/p_paired_signflip`、`separation.paired_minimum_p` |
| 8 | 1469–1475 | S33 新正文段（TOST 限定） | **十种子 r=5 组不是零**：它是幅度最小的负秩（−43.7 vs r=4 的 −97.7、r=3 的 −120.7），TOST 边际 = 该组一个种子 sd = 38.77 → **TOST p=0.652**；只有边际放宽到 ±66.17（1.71 sd）才能声明等效；90% 区间 [-66.17,-21.23]、95% 区间 [-71.43,-15.97] **整体位于零以下** | `rank5_equivalence.tost_p/.margin/.min_equivalent_margin/.ci90_t/.ci95_t` |

**关于"十种子 r=5 被称为 zero / near zero"的检查结果**：逐条检索补充材料后确认，**没有任何句子**
把该十种子组称作 zero 或 near zero。文中三处 "near zero"（`supplementary.tex:543` S9 ShareGPT、
`:1265` S29 四环境栈、`:1555` S30 加性残差）与 `:486` 的 r=5 单种子区间均指**其它数据集合**，按任务要求
**未改动**；S17 主张表也未出现该表述。因此第 8 项的限定句以新增段落形式落在 S33 该组首次出现处。

## 2. 页数 / 章节数

| 量 | 改动前 | 改动后 | 备注 |
|---|---|---|---|
| `supplementary.pdf` 页数 | 17 | **18** | 新增 2 段正文导致 +1 页；`audit_pdf.py` 的 `SUPP_PAGES` 已由 17 改为 18 |
| 补充材料 `\section` 数 | 43 | **43** | 本轮不新增章节，`audit_check.py` 的"forty-three S-sections"检查不变 |
| `main.pdf` 页数 | 10 | 10 | 主稿未改动（`1.1\times10^{-5}` 不在主稿） |
| 编译 | — | pdflatex ×2，0 error，1 个 Overfull hbox（1533–1556，S35 既有段落，**非本轮引入**） | 两次编译输出同为 18 页 / 396285 bytes |

## 3. 审计结果（三条命令，全部 0 失败）

| 命令 | 结果 |
|---|---|
| `python -m tools.paper_audit audit --profile p3_prl --fail-on NONE` | **READY, grade A — pass=50 fail=0 warn=0 manual=9 skip=27 error=0**（报告 `docs/audits/AUD-p3_prl-20261024T084356Z.{md,json}`）|
| `python paper3/paper_ieee/audit_check.py` | **0 hard failure(s), 0 warning(s)** |
| `python paper3/paper_ieee/audit_pdf.py` | **0 hard failure(s), 0 warning(s)**（实测 supplementary 18 页 / main 10 页）|

审计脚本本轮同步更新：

* `audit_pdf.py`：`SUPP_PAGES` 17→18；`SUPP_CHECKS` 新增 9 条守门（十种子符号划分、`1.08e-5` 最小可达 p、
  r7r8 `p=0.071`、r=5 `TOST p=0.652`、"not statistically indistinguishable from zero"、S28 的
  `1793 training pairs` / `TOST p=0.0074` / `+0.0433`、S29 两份 torch2.6 归档全名）；新增
  `collapse_letterspacing()` / `letter_spaced()` 两个辅助函数，用于还原被排版成字距展开（small caps）后
  pdftotext 逐字分开的路径串（否则 `verify_r6_..._a12_torch26.json` 这类全名无法匹配）。
* `audit_check.py`：新增 `SUPP_NEW_NUMBERS`（8 条：S28/S33 的关键归档值）与 `SUPP_STALE_TOKENS`
  （`1434 training pairs`、`4302 optimizer steps` 不得再出现）两组检查；文档字符串注明本轮重新核验
  "43 个 S 章节"。**未改动** 章节数期望（仍为 43）。

## 4. 建议的 provenance manifest 增补（本轮未改 manifest，按写入范围交主控决定）

在 `docs/PROVENANCE_MANIFEST_2026-10-20.md` 的 `## P3 (paper3/paper_ieee)` 表内追加两行：

| item | script | archive | status |
|---|---|---|---|
| `tab:crossing10`（含 15 对分离矩阵、r=5 TOST） | `tools/_p1595_p3_rank_separation.py` | `outputs/analysis/p3_rank_separation_extended.json`（`ranks`、`separation.pairs`、`separation.n_separating_holm_p05`、`conclusion`、`rank5_equivalence`） | 待 manifest 登记 |
| `tab:vqa`（含 TOST 等效 / 反转） | `tools/_p1595_p3_rank_separation.py` | `outputs/analysis/p3_rank_separation_extended.json`（`vqa_equivalence.arms/.contrasts/.claim_verdict`）；原始臂 `outputs/analysis/cloud_vqa1793_{base,5,6}.json` | 待 manifest 登记 |
| `tab:envcloud`（S29 归档补齐） | 归档来源 `paper3/scripts/run_training.py` | `paper3/scripts/outputs/experiments/verify_r5_s42_..._a10_torch26.json`、`verify_r6_s42_..._a12_torch26.json`（字段 `delta_E`） | 待 manifest 登记 |

注意：`outputs/analysis/p3_rank_separation_extended.json` 被根 `.gitignore` 的 `outputs/` 规则忽略
（与 `p3_robust_stats_10seed.json` 等同），发布时需显式 add/copy。

## 5. 未决 / 遗留

1. **F6（优化器步数）——仍未解决，未编造。** 三份归档只给 `train_samples=1793`、`epochs=3`；
   `paper3/scripts/run_training.py` 不把 `--num-samples` 写入实验 JSON（只写 `num_samples` 到
   `paper3/scripts/outputs/experiments/verify_*.json`，VQA 臂不在其中），训练日志亦未检索到该臂。
   因此正文改写为"1793 training pairs, three epochs …（步数未归档）"，**未给任何步数**。
   若日后取回训练日志，`E(0)` 之后的 step 打印（`step k/len(loader)`、`batch_size` 默认 1、
   `train_data = processed[4:]` 留 4 条作 eval）可反推，但当前归档不足，未反推。
2. **S17 主张表第 891 行**引用 "(S44)"，而补充材料只有 43 个章节（S43 = SmolVLM-500M）。属既有陈旧引用，
   超出本轮任务范围，**未改动**，建议下一轮修正。
3. **F3 的表述选择**：S33 明确写出"bootstrap 与精确检验在 r7r8 上不一致、以精确检验为准"，与证据文档 F3
   一致；若审稿人要求只印一种区间，可删 bootstrap CI，但需同步 `audit_pdf.py` 的守门条目。
4. **本轮 git 提交**：`c07c54b`（由并行会话提交，含补充材料主体改动）、`f22fa50`（两个审计脚本）、
   `506912f`（S29 `\allowbreak`）。`paper3/paper_ieee` 工作树已干净，`p3_prl` 审计的 A-01 因此通过。