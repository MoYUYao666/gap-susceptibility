# A23 迁移主张：18 单元 → 21 单元切换记录（2026-10-25）

本文件是**短记录**，面向操作者：把 `paper_a2/ext_partII_domains.tex` 里那句迁移主张从 18 单元口径切到
21 单元口径，并留下本轮的全部实测数字与门禁结果。唯一的数字来源是
`outputs/analysis/a23_multiencoder_transfer.json`（`tools/_p1614_a23_multi_encoder_transfer.py` 产出，
script sha1 `ee174963df00583822b4d70f30f8da450dda3fbb`，`meta.finished_at = 2026-10-25T07:39:56+0800`，
`meta.git = a834c33e…` 且 `dirty = false`）。

**本轮写范围内的文件**：`paper_a2/ext_partII_domains.tex`、`docs/provenance_manifest.json`（仅
`tab:calib_lodo` 一条 note）、`docs/a23_multiencoder_cloud_notes.md`（§3 loader 表 + RemoteCLIP 更正
+ 顶部状态行）、`docs/a23_transfer_claim_rewrite_notes.md`（追加 §9）、本文件。
`paper_a2/verify_a23_fix.py` **未改**（页数未变，无需改常量）。

## 1. 旧 vs 新（一行 + 可复核表）

一行：**18 单元 / 324 对 / 3536 条已评分跨单元条目 / 124 名义 / 19 幸存（SigLIP 11 + OceanCLIP 8）**
→ **21 单元 / 441 对 / 4940 条 / 179 名义 / 29 幸存（SigLIP 12 + OceanCLIP 10 + RemoteCLIP 6 + CLIP-L/14 1）**。

| 量 | 旧（18 单元） | 新（21 单元） | 归档字段 |
|---|---|---|---|
| 编码器 / 语料 / 单元 | 6 / 3 / 18 | 7 / 3 / 21 | `conclusion.n_encoders`, `n_corpora`, `n_units` |
| 有序对 | 324 | 441 | `conclusion.n_ordered_pairs`, `transfer.n_pairs` |
| 自对（排除） | 18 对 / 221 条 | 21 对 / 260 条 | `transfer.self_pairs`, `transfer.summary.n_scored_entries_self_pairs` |
| 跨单元对 | 306 | 420 | `transfer.cross_unit_pairs` |
| 已评分跨单元条目 | 3536 | 4940 | `conclusion.n_scored_entries_cross_unit` |
| 名义高于 chance | 124 | 179 | `conclusion.n_entries_above_chance` |
| bootstrap 幸存 | 19 | 29 | `conclusion.n_entries_surviving_bootstrap` |
| 退化条目 | 455（跨单元 442） | 533（跨单元 520 + 自对 13） | `transfer.summary.n_degenerate_entries` |
| 幸存者目标语料 | 全 sonar | 全 sonar（29/29） | `transfer.pairs[]` 聚合 |
| 幸存者统计量族 | σ 相对 18 + 绝对 1 | σ 相对 27（12/10/5）+ 绝对 2 | `transfer.pairs[]` 聚合 |
| 最强幸存者 | BioCLIP(sonar) → SigLIP(sonar), `mass_0p002`, BA 0.900, fit 0.500, ΔCI95 [+0.100,+0.500] | **同一条（不变）** | `conclusion.best_surviving_pair` |
| 判定 | yes for at least one pair | yes for at least one pair（不变） | `conclusion.answer` |

自对排除算术：441 × 13 = 5733；5733 − 533 = 5200 = 4940（跨单元）+ 260（自对）；另 420 × 13 = 5460，
5460 − 520 = 4940。旧 18 单元数字现在只存在于 `git show HEAD:outputs/analysis/a23_multiencoder_transfer.json`。

## 2. RemoteCLIP 健康检查（触发 STOP 条件，但"未加载"被证伪）

| 语料 | RemoteCLIP top-1 | chance | 复现行 |
|---|---|---|---|
| marine_optical（343 图 / 7 类） | 12.828 % | 14.2857 % | 无（`reproduction.reference = null`） |
| acoustic_sonar（1,783 图 / 7 类） | 11.273 % | 14.2857 % | 无 |
| rare_species（1,608 图 / 67 类） | 2.425 % | 1.4925 % | 无 |

字段：`encoders.remoteclip.corpora.<corpus>.frozen_row.top1` 与 `chance_percent`；三个语料**都没有任何历史
归档可交叉验证**（`_p1344` / `_p1352` / `_p1472` 都不含 RemoteCLIP）。

"看起来像未训练模型"成立（三个语料都在 chance 的 2 倍以内），但"权重没加载 ⇒ 21 单元 run 无效"不成立：

1. **权重身份**：`models/RemoteCLIP/RemoteCLIP-ViT-B-32.pt`（605,208,421 B）sha256 =
   `60014e395d930a3f2963d1d89c8522bf4ad56775571e4356e866864789af85c4`，与 HF 镜像 API 的官方 LFS oid
   （`https://hf-mirror.com/api/models/chendelong/RemoteCLIP/tree/main?recursive=true`，2026-10-25 查询）逐位一致。
2. **加载完整性**：归档 `model_source.load_report` = 302 keys，missing 0 / unexpected 0。
3. **不是随机权重**：与 `models/clip-vit-base-patch32/pytorch_model.bin` 逐张量 cos 0.9955–1.000
   （token/class embedding 1.0000、attn q/k/v 0.997、mlp 0.997–0.999、text/visual projection 转置后
   0.9989 / 0.9987），`logit_scale = 4.6037 ≈ ln 100`；随机初始化对照 cos ≈ 0.000。
4. **harness 对照**（marine_optical，同一预处理与 prompt）：OpenAI CLIP ViT-B/32 权重按 open_clip 布局转换
   （302/302 keys）得 **26.53 %**（GELU）/ **20.70 %**（QuickGELU）；RemoteCLIP 得 **12.83 %**（GELU，与归档
   小数点后两位一致）/ **14.29 %**（QuickGELU）。

补充（**未归档**，只用于本轮裁决、不入稿）：ImageNet-1k val shard 0（3,572 图，chance 0.10 %）上
OpenAI CLIP 60.13 %、RemoteCLIP 18.76 %（QuickGELU）⇒ RemoteCLIP 是 188× chance 的可用零样本分类器，
遥感微调把自然图像能力压到 18.76 %，故在这三个非遥感语料上落到 chance 上下。

**裁决**：21 单元 run 有效（加载意义上）⇒ 正文按 21 单元写，并把该编码器写成**第五条 limits**
（"top-1 on these corpora sits within a factor of two of chance（12.83 / 11.27 / 2.43 % 对
14.29 / 14.29 / 1.49 % chance）"，及"6 of the 29 survivors take their target from it"）。

## 3. 正文改动与页数

- `paper_a2/ext_partII_domains.tex`：122–147 行换数字 + 新增第五条 limits；Source 行（148–165 行）补
  21 单元字段路径（`conclusion.{n_encoders,n_units,n_ordered_pairs,n_scored_entries_cross_unit,
  n_entries_above_chance,n_entries_surviving_bootstrap,best_surviving_pair.{target_BA,source_fit_BA,delta_ci95}}`、
  `transfer.{self_pairs,cross_unit_pairs,summary.n_scored_entries_self_pairs}`、
  `limits.{probes.single_seed,class_imbalance.corpus_class_counts}`、
  `encoders.<encoder>.corpora.<corpus>.{frozen_row.top1,chance_percent,reproduction.max_abs_diff}`）。
- 幸存者阵营描述已按新格子改写：目标编码器从"11 SigLIP + 8 OceanCLIP"变为
  "12 SigLIP + 10 OceanCLIP + 6 RemoteCLIP + 1 CLIP-L/14"，σ 相对族从 18/19 变为 27/29（12/10/5）。
- **页数 73，与切换前相同**（`Output written on main_ieee.pdf (73 pages, 1275901 bytes)`）⇒
  `verify_a23_fix.py` 的 `PAGES = 73` **不需要改**，本轮未动该文件。

## 4. 门禁结果（本轮实测）

| 门禁 / 命令 | 结果 |
|---|---|
| `pdflatex -interaction=nonstopmode main_ieee.tex` ×2（`paper_a2/`） | 两次 exit 0；**73 页** |
| LaTeX log 逐项 | 0 error / 0 undefined reference / 0 undefined citation / **0 overfull hbox** / 0 overfull vbox / 0 rerun 请求；42 条 underfull，其中 **13 条落在本段**（"paragraph at lines 88--176"，即换过数字的那段 + Source 行字段列表；上一轮的 §5 记录同样报过该段 underfull，属 Source 行 `\texttt` 列表的固有松散断行）；门禁只查 overfull |
| `python paper_a2/verify_a23_fix.py` | **ALL CHECKS PASSED**（29 项 PASS：73 页、US letter、行号 1..73 连续、12 pt 正文、单栏、DOI、37 个冻结归档 SHA-256 全绿） |
| `python -m tools.paper_audit audit --profile a23_joe --fail-on NONE` | 退出码 0；`BLOCKED` grade D；**pass=57 / fail=1 / warn=0 / manual=9 / skip=19 / error=0**；唯一 FAIL = `A-01`（`M paper_a2/ext_partII_domains.tex`，预期的"未提交前 git-dirty"，待 lead 提交后消失）；报告 `docs/audits/AUD-a23_joe-20261025T001344Z.{json,md}` |
| `python tools/_p1428_provenance_gate.py` | **gate: PASS**（A23 floats=34 manifest=34 missing=0 pending=0 broken_paths=0；paperA/A1/P3 同样 0/0/0） |

## 5. 未溯源 / 诚实标注

1. **分项计数是聚合值**：12/10/6/1、12/10/5、源语料 16/13、成对 16 条，都不是归档里的标量字段，而是按
   `transfer.pairs[].{target_encoder,source_corpus,self_pair} × by_statistic.*.bootstrap.survives`（仅非自对）
   聚合得到；脚本只把前 10 条幸存者写进 `transfer.summary.survivors`（`survivors[:10]`），29 条必须自行聚合。
   聚合规则已同时写进 `docs/provenance_manifest.json` 的 `tab:calib_lodo` note。
2. **RemoteCLIP 的 ImageNet 数字（60.13 % / 18.76 %）未归档**：一次性 inline 复验（`data/imagenet_hf`
   `validation-00000-of-00014.parquet`，3,572 图），只用于判断、**不入稿、不进 manifest**。
3. **RemoteCLIP 无复现行**：它进格子后唯一无法与历史归档交叉验证的单元；可交叉验证的四个单元仍是
   `max|Δ| = 0.0`（`clip-vit-base-patch32` × marine/sonar 对 `a23_certificate_control.json`，
   `bioclip`/`oceanclip` × rare_species 对 `a23_certificate_adapted.json`，共 128 个比较值）。
4. **未做的事**：未改 `paper_a2/verify_a23_fix.py`、`paper_a2/main_ieee.tex`、`SUBMISSION/**`（37 个冻结哈希
   全绿，投稿包仍是 2026-10-24 冻结态，本轮改动**尚未进入投稿包**）、中文镜像 `zh_ext_partII_domains.tex`；
   未重跑单种子 DINOv2 探针（`limits.probes.single_seed` 如实标注）；未做任何机制解释（正文只写边界）。
5. `paper_audit` 运行时会自行归档报告（`docs/audits/AUD-a23_joe-20261025T001344Z.{json,md}`，2 个新文件），
   这是该门禁的固有产物，不在本轮写范围内但属于任务要求的门禁输出。