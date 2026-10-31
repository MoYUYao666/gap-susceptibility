# A23 多编码器迁移网格 — 重跑记录（2026-10-25）

本轮修复 `tools/_p1614_a23_multi_encoder_transfer.py` 的编码器加载/取特征 API，
按 6 编码器 x 3 语料重跑整张网格，并重写 `outputs/analysis/a23_multiencoder_transfer.json`。
**结论翻转为"有迁移"：19 条 (对, 统计量) 通过 bootstrap。** 因此**未改稿件**（`paper_a2/` 由另一路负责），
第 6 节给出建议替换句。

## 1. 本轮写范围

| 文件 | 动作 |
|---|---|
| `tools/_p1614_a23_multi_encoder_transfer.py` | 修复 4 类编码器的取特征路径 + dry-run 断言补全 |
| `outputs/analysis/a23_multiencoder_transfer.json` | 重跑覆盖（18 单元 / 324 有序对） |
| `docs/a23_multiencoder_rerun_notes.md` | 本文件 |
| `outputs/analysis/_cache/a23_multiencoder/*.npz` | 脚本自身缓存（13 个新建，5 个复用，共 18 个） |

## 2. 每条编码器的 API Bug 与修法

原写法把**所有** `transformers` 编码器都当成 CLIP 走
`vision_model -> pooler_output -> visual_projection`；实际安装 `transformers 5.16.1`
（`D:\Anaconda\envs\pytorch\python.exe`，torch 2.9.1+cu130，open_clip 3.3.0）下只有 `CLIPModel` 有这条链。
现在**每条编码器在注册表里显式声明**取特征路径（`kind` / `image_path` / `text_path` / `probe`），
并在首批上断言维度（`ImageTextEncoder.assert_dim`），不再"猜"。

### 2.1 `siglip-base-patch16-224`（原报错点）

- **症状**：`AttributeError: 'SiglipModel' object has no attribute 'visual_projection'`。
- **实况**（`SiglipModel` 压根没有 `visual_projection` / `text_projection`）：
  - 图像嵌入 = **`vision_model.head(last_hidden_state)`**，即 `SiglipMultiheadAttentionPoolingHead`
    对**整段 patch 序列**做注意力池化；实测 `vision_model(pixel_values).pooler_output` **正好等于**
    `head(last_hidden_state)`（maxdiff `0.0`），但语义上它是 patch 均值而非官方嵌入，故显式走 head。
  - 文本嵌入 = **`text_model.head(text_model.pooler_output)`**；`text_model.head` 是 `Linear(768,768)`。
- **记账字段**：`registry.encoders.siglip-base-patch16-224.loader|image_path|text_path`；
  缓存内 `model.extraction.declared_image_path|declared_text_path|detected.vision_head_class`。

### 2.2 `dinov2-base`（纯视觉塔 + 线性探针）

- **症状**：路径本身选错。`Dinov2Model` **没有 `vision_model` 属性**（`has_vision_model=false`），
  原代码会把 `self.model.vision_model` 直接抛 `AttributeError`；而且它没有文本塔。
- **修法**：`image_path="model"` —— 模型自身就是视觉编码器，取
  `pooler_output`（= `layernorm(last_hidden_state[:,0])`，实测与 CLS 位 `maxdiff 0.0`）。
  `probe=True` 生效：top-1 走注册表声明的线性探针（30% 留出集，`probe_protocol`），
  **不调用 `text()`**（缓存里 `tfeat` 就是探针的 L2 归一化余弦头 `W`）。
- **顺带修的一个真 bug**：原先没有"配置里的特征宽度"校验。`SiglipConfig` **没有顶层 `projection_dim`**，
  只有嵌套的 `vision_config/text_config.hidden_size`；现在 `_feature_dim()` 递归三层取维度，
  再与 `embed_dim` 断言一致（SigLIP 768、DINOv2 768 实测通过）。

### 2.3 `clip-vit-base-patch32` / `clip-vit-large-patch14`

- 原路径**本来就是对的**，保留 `vision_model -> pooler_output -> visual_projection` / `text_projection`。
- **回归证据**：新旧两条路径在同一批真实图像上给出**逐位相同**的嵌入
  （`max|new-old| = 0.000e+00`，`np.array_equal=True`，图/文两侧都是）。
- 归档层面的证据：`encoders.<enc>.corpora.<corpus>.reproduction.max_abs_diff = 0.0`（见第 5 节）。

### 2.4 `bioclip` / `oceanclip` / `remoteclip`（open_clip 路径）

- 未改（`encode_image` / `encode_text`）。加载器的 `missing_keys` 断言仍在：
  本轮两个适配编码器的 302 个 state-dict 键**全部命中**（`missing_keys=0`）。
- `WARNING:root:No pretrained weights loaded for model 'ViT-B-16'` 是
  `create_model_and_transforms(pretrained=None)` 的正常提示，权重随后由 `load_state_dict` 注入
  （`load_report.weights.missing_keys=0`），不是随机模型。

## 3. 运行时间与命令

| 步骤 | 命令 | 结果 |
|---|---|---|
| 修正后单批校验 | 内联脚本：6 编码器 x 14 张真实图，断言 shape / dtype / L2 范数 | 全部 `(n, embed_dim)`，行范数 1.000000 |
| 最小单元 `--encode` | `--encode --analyze --corpora marine_optical --include-adapted --allow-missing-models` | 新出 5 个 `.npz`；`clip-vit-base-patch32` 缓存 `reusing`（幂等成立） |
| **最终网格** | `--encode --analyze --include-adapted --allow-missing-models --encoders clip-vit-base-patch32,siglip-base-patch16-224,clip-vit-large-patch14,dinov2-base,bioclip,oceanclip` | 18 单元全部 `reusing`，82.4 s（`meta.duration_seconds`，2026-10-25T07:29:41+0800 收尾） |
| 稳定性 | 同一 `--analyze` 连跑两次（run1 / run2） | 分析内容哈希一致（见 §4） |
| 断言门禁 | 同一选择的 `--dry-run` | **160 asserted OK, 0 unasserted, 0 FAILED** |

> 注：`--encode` 本身会连带跑一遍 analyze 并**覆盖 JSON**（`main()` 里 `if a.analyze or a.encode:`），
> 所以单测一个单元时不要带 `--encode`——本 agent 中途用
> `--encode --units siglip-base-patch16-224__rare_species` 试幂等性，把 JSON 覆盖成了 1 单元版，
> 随后用上面的完整命令重建；最终归档已复核为 18 单元（见 §4 末的指纹）。

**真实编码耗时**（逐单元，取自 `encoders.<enc>.corpora.<corpus>.cache_creation.encode_seconds`，单位秒；
前 5 个单元是 2026-10-24 既有缓存，其余为本轮 07:07–07:16 新编码）：

| 编码器 | marine_optical (343) | acoustic_sonar (1783) | rare_species (1608) |
|---|---|---|---|
| clip-vit-base-patch32 | 8.01 *(旧)* | 18.14 *(旧)* | 415.11 *(旧)* |
| siglip-base-patch16-224 | 7.17 | 13.33 | 34.93 |
| clip-vit-large-patch14 | 14.47 | 58.73 | 79.81 |
| dinov2-base | 8.01 | 23.51 | 45.51 |
| bioclip | 12.97 | 22.08 | 287.12 *(旧)* |
| oceanclip | 14.22 | 22.38 | 415.83 *(旧)* |

18 个单元编码秒数合计 **1501.3 s ≈ 25.0 min**（含 GPU 争用，属上界）；DINOv2 的探针拟合另计在内。
缓存总体积 **49.1 MB**。全部 18 单元的分析阶段（324 对 x 13 统计量 + 2000 次重采样）**21.6 s**
（§4 稳定性那两次 `--analyze`：`meta.duration_seconds` = 21.57 / 21.66 s）；
端到端 `--encode --analyze`（缓存全部命中、含图像载入与 18 次缓存校验）**82.4 s**。

## 4. 新计数与结论（全部来自 `outputs/analysis/a23_multiencoder_transfer.json`）

| 量 | 值 | 归档字段 |
|---|---|---|
| 编码器 / 语料 | 6 x 3 | `conclusion.n_encoders` / `n_corpora`；`meta.selection.encoders` |
| 单元 | **18** | `transfer.n_units`；`meta.n_units_analyzed=18`，`complete_for_selection=true` |
| 有序对 | **324** | `transfer.n_pairs`（=18²） |
| 每单元手术族行数 | **9** | `encoders.<enc>.corpora.<corpus>.n_family_rows`，18/18 均为 9 |
| 每对统计量 | 13 | `conclusion.n_statistics_per_pair`；`meta.statistic_keys` |
| (对, 统计量) 条目合计 | 4212 | `transfer.summary.n_pair_statistic_entries`（=13x324） |
| 已评分跨单元条目 | **3536** | `transfer.summary.n_scored_entries_cross_unit`（自对 221 条另计，不计入主张） |
| 退化条目（中位切分单类） | 455 | `transfer.summary.n_degenerate_entries` |
| **名义高于 chance(0.50)** | **124** | `conclusion.n_entries_above_chance` |
| **通过图像 bootstrap** | **19** | `conclusion.n_entries_surviving_bootstrap` |
| 判定 | **`yes for at least one pair`** | `conclusion.answer` |

- 通过规则（`transfer.protocol.survives_rule`）：(目标 BA - 0.50) 的 2.5 百分位 > 0，2000 次图像重采样，
  每次**重拟合源阈值**；同语料配对（paired=true）、跨语料独立（paired=false）。
- 19 条幸存集中在 **9 个有序对**、**2 个目标单元**（`siglip-base-patch16-224__acoustic_sonar` 11 条、
  `oceanclip__acoustic_sonar` 8 条），源单元来自 `acoustic_sonar`(10) 与 `rare_species`(9)；
  统计量以固定相对分辨率的 `mass_sigmarel_0p005`(9) / `_0p01`(7) 为主，另 `mass_0p002`(1)、`mass_sigmarel_0p02`(2)。
- 最强条目（`transfer.summary.best_entry_surviving_bootstrap`）：
  `bioclip__acoustic_sonar -> siglip-base-patch16-224__acoustic_sonar`，`mass_0p002`，
  目标 BA **0.900**、源拟合 BA 0.500、阈值 0.96859，delta CI95 **[0.100, 0.500]**、`p_delta_gt_zero=0.992`，
  2000/2000 次抽样可用（paired=true）。
- **它不是"水平标定"，而是"方向"迁移**（本轮新发现，写进正文要谨慎）：
  源拟合 BA = 0.500 是九点族上的**下确界**（阈值取在源第 5 低的 M 上）；
  真正迁移的是"**M 低 = 健康**"这一方向——目标族按 M 排序后，最低 5 个配置全部 `top1 <= 中位`、
  最高 4 个全部 `top1 > 中位`，唯一错分在 λ=-1.0（M 最小但 top1 高）。混淆阵 tp=4 fp=0 tn=4 fn=1 -> BA 0.900。
- 仍是名义最强、但**未通过**的条目（`transfer.summary.best_entry_overall`）：
  `oceanclip__rare_species -> clip-vit-base-patch32__marine_optical`，`mass_0p01`，BA 1.000、
  CI95 [-0.167, +0.500]、`p_delta_gt_zero=0.499`（与 2026-10-24 五单元版的 [-0.150,+0.500] 同量级）。

**幂等与稳定性证据**：

- 最终网格的 `meta.encode_log` 18 条**全部** `reused=true`（`--encode` 只复用有效缓存，指纹未变则不重编码）；
  18 个 `.npz` 与 `meta.selection.units` 一一对应。
- 两次 `--analyze` 的差异**只有** `meta.started_at/finished_at/duration_seconds` 与
  `meta.git.status_porcelain*`（工作区快照），其余全部字节相同：
  去除这几项后 `sha256 = 420365c6e62cbbf336f5738bbcfeb3d43700bc315052ab6baa5121a25f88761c`（两次一致）。
- 最终归档指纹：`sha256 = e7710ee1062ba616f4c7c6eb2330321be7999c151fc41bdfd9b93fcc97294603`（4,984,242 B），
  `meta.script_sha1 = ee174963df00583822b4d70f30f8da450dda3fbb`（与磁盘脚本一致）。
- `--dry-run` 现同时断言 `--analyze` 末行打印的四个数（单元数、已评分跨单元条目、名义高于 chance、幸存数）
  与判定字符串：160 项全 OK、0 FAIL。

## 5. 归档复现门禁（未变）

四个与既有证书重叠的单元仍逐值相同，`reproduction.max_abs_diff = 0.0`，
共比较 **128** 个值（28+28+36+36）：

| 单元 | 参考归档 | 比较值数 | max abs diff | reproduced |
|---|---|---|---|---|
| `clip-vit-base-patch32__marine_optical` | `a23_certificate_control.json` | 28 | 0.0 | true |
| `clip-vit-base-patch32__acoustic_sonar` | `a23_certificate_control.json` | 28 | 0.0 | true |
| `bioclip__rare_species` | `a23_certificate_adapted.json` | 36 | 0.0 | true |
| `oceanclip__rare_species` | `a23_certificate_adapted.json` | 36 | 0.0 | true |

字段路径：`encoders.<enc>.corpora.<corpus>.reproduction.{reference,pairs_checked,max_abs_diff,reproduced}`。
**修复没有改动任何归档值**，因此本次可以交付。

## 6. 稿件措辞（**本 agent 未改稿件**，留给负责 `paper_a2/` 的一路）

现句（`paper_a2/ext_partII_domains.tex` 第 121–133 行）写的是"3 编码器 x 3 语料、5 单元、25 有序对、260 条、
7 条名义、0 条通过"，且结论句是"no threshold transfers"。**三个数字与判定全部已过期**，并给出替换句：

英文（可直接替换第 121–133 行那一段的对应分句；数字逐项对应上面的归档字段）：

> Widening the same test to every ordered pair of encoder--corpus units available locally ($6$ frozen
> encoders---the generic-CLIP control, the two adapted encoders, and three further frozen backbones---over
> $3$ corpora, i.e.\ $18$ units and all $324$ ordered pairs, each scored on $13$ threshold statistics)
> **does** produce transfer, and only on one axis: of the $3536$ scored cross-unit (pair, statistic) entries
> $124$ beat chance at the point estimate (chance $0.50$) and $19$ keep their $95\,\%$ interval above chance
> under an image-level bootstrap ($2{,}000$ draws, the source threshold refitted on each source resample;
> paired when source and target share a corpus, independent otherwise). Every survivor targets an
> acoustic-sonar unit, and the strongest
> (BioCLIP on the sonar corpus $\to$ SigLIP on the sonar corpus at $\varepsilon=0.002$) reaches balanced
> accuracy $0.900$ with a ($-$chance) interval of $[+0.100,+0.500]$; its source fit itself is at chance
> ($0.500$), because what transfers is the \emph{direction} (lower $M$ = healthier) rather than a calibrated
> level. The unqualified "no threshold on $M$ transfers" is therefore not supported and is replaced by this
> bounded statement; the new encodings still reproduce every archived certificate value they share with the
> two certificates ($\max|\Delta|{=}0$ over $128$ compared values on four units).

中文要点（给操作者）：旧句说"没有任何阈值可迁移"，新证据是**有 19 条通过**，
但全部落在**声呐语料**上、且最强那条靠的是**方向而非水平**，所以句子应改成
"只在一根轴上迁移（声呐域内 / 朝向声呐的目标），并点名该对"。

## 7. 本地编不了 / 需要说明的

1. **RemoteCLIP 本轮排除，但"403"这条理由已不成立。**
   任务书写的是 "hf-mirror returns 403 from this laptop and ModelScope has no such repository"。
   实测（2026-10-25，本机）：`https://hf-mirror.com/chendelong/RemoteCLIP/resolve/main/RemoteCLIP-ViT-B-32.pt`
   **HTTP 200**，605,208,421 B 全程 53 MB/s 下完，`zipfile.is_zipfile=True`、`testzip()=None`，
   `sha256 = 60014e395d930a3f2963d1d89c8522bf4ad56775571e4356e866864789af85c4`。
   ModelScope 侧仍为 404（`HubApi().get_model_files`：`chendelong/RemoteCLIP`、`AI-ModelScope/RemoteCLIP`、
   `RemoteCLIP` 三个名字都是 `NotExistError [E3020] [404] record not found`）。
   ⇒ 镜像侧现在能取，**"取不到"不再是排除理由**；本轮仍按任务指定的 6 编码器 / 18 单元交付。
   权重已存到 `backups/models_stash_RemoteCLIP_2026-10-25/RemoteCLIP/RemoteCLIP-ViT-B-32.pt`
   （未放进 `models/`，因为 `models/` 在 `.gitignore` 里且会直接把该编码器加进选择，改变网格规模）。
   若要扩到 7 编码器 / 21 单元：把权重放回 `models/RemoteCLIP/`，删掉 3 个 `remoteclip__*.npz`，再跑
   不带 `--encoders` 的 `--encode --analyze --include-adapted --allow-missing-models`。
   （本轮误跑过一次 21 单元：21 单元 / 441 对 / 4940 条跨单元 / 29 条幸存，日志见
   `outputs/_serial_logs/a23_multiencoder_fullgrid_2026-10-25.log`；该结果**不在**本归档里。）
2. **DINOv2 的 marine_optical 单元在迁移测试里完全退化**：455 条退化条目中，以它为源或目标的共 468 次
   （占绝大多数；其余单元各 26 次）。其九配置 `top1` 有 8 个**完全相同**（90.57%），中位切分后健康标签
   **9/9 全为真**（`encoders.dinov2-base.corpora.marine_optical.rows[].top1`），源/目标两侧都无法构成二分类。
   这是**饱和探针**的真实性质（留出集 top-1 90.57%），不是脚本错误；跨这份归档引用该单元时必须说明。
3. **探针单种子**：DINOv2 三个单元都是 seed 0 单次切分（`limits.probes.single_seed`）；
   换切分会动该单元的 top-1 与整个族，故其结论的稳健性未测。
4. **族只有 9 个配置**：目标 BA 的粒度是 1/4~1/5（`limits.family_size.note`）。
   `transfer.summary.survivors` 只存**前 10 条**（按目标 BA 排序），其中 9 条的
   `target_value_n_distinct <= 7`（最小 4、最大 9），即目标族在该统计量上取值很粗；
   `transfer.summary.survivor_caveat` 已把它标成"结构切分而非标定操作点"的风险——引用时请一并引用该免责字段。
   （完整 19 条只在 `transfer.pairs[].by_statistic.*.bootstrap.survives` 里，逐条统计需要自己汇总。）
5. **语料口径**：marine / sonar 是原始数据树（7 类 / 343 / 1783，声呐第 8 类 `tire` 834 个根目录文件按构造排除，
   `meta.corpus_size_checks.*.root_level_files_ignored`），不是稿件的规范协议；67 类子集是 24 张/类的平衡子集。

## 8. 复核命令（可重跑）

```powershell
$env:HF_HUB_OFFLINE='1'; $env:TRANSFORMERS_OFFLINE='1'
D:\Anaconda\envs\pytorch\python.exe tools\_p1614_a23_multi_encoder_transfer.py --encode --analyze `
    --include-adapted --allow-missing-models `
    --encoders clip-vit-base-patch32,siglip-base-patch16-224,clip-vit-large-patch14,dinov2-base,bioclip,oceanclip
# 断言门禁（160 项，须 0 FAILED）
D:\Anaconda\envs\pytorch\python.exe tools\_p1614_a23_multi_encoder_transfer.py --dry-run `
    --include-adapted --allow-missing-models `
    --encoders clip-vit-base-patch32,siglip-base-patch16-224,clip-vit-large-patch14,dinov2-base,bioclip,oceanclip
```

本次运行的完整控制台日志：`outputs/_serial_logs/a23_multiencoder_18unit_2026-10-25.log`。
归档自述的脚本指纹 `meta.script_sha1 = ee174963df00583822b4d70f30f8da450dda3fbb`（与磁盘一致）；
运行提交 `meta.git.commit = 75eab7acb9992d6f57f2854a93b2433606758885`（工作区当时 dirty，条目见 `meta.git.status_porcelain`）。

## 9. 稿件整合记录（另一路 agent，2026-10-25）

**已改稿件**（`paper_a2/` 一路负责）：`paper_a2/ext_partII_domains.tex` 第 122--145 行的迁移句按本文件 §4 的
19 条幸存重写为"有界迁移"陈述（旧句 1,387 字符 → 新句 2,460 字符），并把 Source 行补上
`outputs/analysis/a23_multiencoder_transfer.json` 的字段路径；同段三处配套限定一并改掉
（第 87 行小标题的无条件断言、第 118--119 行 "portable" → "portable absolute"、Source 行末句的
"rather than a portable scalar"）。**没有照抄 §6 的建议英文句**：新句更短，且按任务要求写进了
"每个幸存者的目标语料都是声呐（11 条 SigLIP / 8 条 OceanCLIP）、光学与 67 类稀有物种目标为 0 条"这一边界，
以及四条限制（九配置中位切分 / 类别不平衡 / 探针单种子 / 声明式取特征路径 vs 官方参考实现）。

**页数与门禁**（可复核，详见 `docs/a23_transfer_claim_rewrite_notes.md`）：

- `pdflatex` ×2 in `paper_a2/`：exit 0，**72 → 73 页**，0 error / 0 undefined ref / 0 undefined cite / 0 overfull；
- `python paper_a2/verify_a23_fix.py`：**ALL CHECKS PASSED**（页数常量 72 → 73，只改常量与注释；
  37 个冻结归档哈希未变）；
- `python -m tools.paper_audit audit --profile a23_joe --fail-on NONE`：退出码 0，`BLOCKED`（grade D，
  pass=57 / fail=1 / warn=0 / manual=9 / skip=19 / error=0），唯一 FAIL 是 `A-01` git-dirty（即本轮未提交的
  `paper_a2/ext_partII_domains.tex`、`paper_a2/verify_a23_fix.py`），提交后消失；
- `python tools/_p1428_provenance_gate.py`：**gate: PASS**（A23 floats=34 manifest=34，missing/pending/broken 全 0）。

**归档版本说明（重要）**：本轮 `outputs/analysis/a23_multiencoder_transfer.json` 被重写过三次
（07:23:41 的 18 单元版、**07:28:12 的 1 单元中间态**、07:29:41 的 18 单元版）。我已逐字段比较确认
07:23:41 与 07:29:41 两版**内容完全一致**（含 `conclusion` 的 3536 / 124 / 19 与 19 条幸存明细）；
磁盘当前版本 sha256 = `E7710EE1062BA616F4C7C6EB2330321BE7999C151FC41BDFD9B93FCC97294603`，
已随提交 `ec27c94b` 入库。引用时请以该 18 单元版为准，勿引中间态。

**本文件 §6 的替换建议已被采纳其数字、未采纳其措辞**；如需回退，旧句可从
`git show 75eab7ac:paper_a2/ext_partII_domains.tex` 取回。
