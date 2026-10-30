# P3 任务 B 方案：第二个下游任务 POPE（2026-10-24 编制，仅准备，未开机、未训练）

> 交付件：`tools/_p1640_p3_second_downstream.py`（`--plan` / `--prepare` / `--eval` / `--aggregate` / `--self-test`）
> 本文件回答：**为什么现在只有一个下游任务 → 为什么选 POPE 而不是 ScienceQA → 数据集到底是哪个 → 32 GB 卡上要多久/多少显存 → 什么结果算强化、什么算削弱论文主张**。
> 所有数字给出可复核来源；未离线核实的假设集中在第 8 节。

---

## 1. 这条 caveat 现在是什么

补充材料 `paper3/paper_ieee/supplementary/supplementary.tex` 的 **"VQA-RAD downstream check"**（`\label{app:vqa}`）
是全稿**唯一**的下游任务：LLaVA 适配器在 VQA-RAD 的 **451** 个留出问题上评测（真实图像、normalised exact match + token F1、
三臂同一问题顺序、按问题配对 bootstrap + TOST）。

同一节里已经写明它自己的**分辨力上限**：

> "a single arm on 451 questions carries a binomial standard error of about 0.022 in accuracy, so differences
> below roughly two of those standard errors (about 0.045) are at the resolution limit of this evaluation set"

也就是说：**单任务 + 451 题 + 0.045 的分辨力极限**是这条 caveat 的两个组成部分。第二个任务只要满足
"多模态、公开可下载、7B LoRA 一小时内可评、五篇稿子都没用过"，就能把两部分一起补掉（第二个任务若有 3000 题，
二项标准误降到 **≈0.009**，比 0.045 的极限好一个量级）。

---

## 2. 候选与选择

| 判据 | **POPE（选中）** | ScienceQA（落选） |
|---|---|---|
| 多模态 | ✅ 每个问题都以图像为条件（图像内嵌在 parquet 里） | ⚠️ 仅部分：test 4241 题里只有带图的那一部分是多模态 |
| 公开可下载 | ✅ HF `lmms-lab-encoder/POPE`（**255 MB**，含图）+ ModelScope 镜像 `lmms-lab/POPE`（510 MB，Apache-2.0） | ✅ HF `derek-thomas/ScienceQA`（**7.94 GB** 仓库体积） |
| 7B LoRA 一小时内 | ✅ 3000 题、答案是 1 个 token（yes/no），按实测锚点 0.3–0.6 s/题 ≈ **15–30 分钟/臂** | ⚠️ 4241 题自由文本作答，更长、更慢 |
| 五篇稿子是否用过 | ✅ **从未测过**（见下方"重叠披露"） | ✅ 未用过 |
| **与 VQA-RAD 指标口径可否直接复用** | ✅ **label 空间就是 VQA-RAD 里已有的 yes/no 子集**：`norm()`、`token_f1()`、`yes_no_accuracy`、`n_yes_no` 全部原样迁移，不新增任何解析规则 | ❌ 多选题需要**新的"答案字母抽取"约定**，两个任务就不再是同一套度量 |

**选择：POPE，config `Full`，split `random`（3000 题）。**
理由归纳：唯一一个能在**不新增度量规则**的前提下补上第二个任务族的选择；同时体积最小（255 MB vs 7.94 GB）、
每题成本最低、题目数最多（3000 vs 2017 带图题）。落选的 ScienceQA 若要上，必须先在论文里把"答案字母抽取"
写成预声明规则，那会让两个任务的数字不再可比——所以本方案不用它。

**重叠披露（必须知道的一条）**：五篇稿子里，**Commentary**（`paper_review_prl/main_prl.tex` §3.1）**引用了** POPE 的
第三方数值（LLaVA-1.5 报告的 87.3 / 86.1 / 84.2 对应 rand/pop/adversarial；DoRA 报告的 85.9 / 86.4 / 87.2 未说明子集），
用来举例"基准子集没写清楚"。它**没有跑过 POPE**，全仓库也没有任何 POPE 测量。
处理方式：本任务把 config、split、revision、parquet sha256、prompt、解码方式**全部写进归档**，
正是 Commentary 那张"12 项报告清单"要求的东西 ⇒ 两篇稿子不冲突，而是**互相印证**（P3 遵守，Commentary 主张）。
⚠️ 但仍需操作者确认一点：Commentary 与 P3 **都投 PRL**，一篇主张"POPE 数字要写清子集"、另一篇给出自己的 POPE 数字，
不属于重复发表，但建议在 P3 的 cover letter 里一句话说明这是**我们自己的首次测量**（不同数据、不同主张）。

---

## 3. 数据集身份（已核实，2026-10-24）

| 项 | 值 | 来源 |
|---|---|---|
| dataset id | `lmms-lab-encoder/POPE` | HF API `?full=true`（`datasets-server` 对旧名 `lmms-lab/POPE` 回 "The dataset has been renamed"） |
| revision | `4db1276663dfa5eb8ad16a52d24c31a09e470896` | 同上 |
| config / split | `Full` / **`random`**（另有 `popular`、`adversarial`；config `default` 的 `test` 是三者拼接的 9000 行） | dataset card `dataset_info` |
| 每题数 | 每个 split **3000** 题 | 同上 |
| 文件 | `Full/random-00000-of-00001.parquet`（脚本按此路径找） | `siblings` 列表 |
| 字段 | `id, question_id, question, answer`(yes/no)`, image_source, image, category` | dataset card `features` |
| 体积 | 整仓 download_size **255,022,914 B**；单 split 是其中一部分；ModelScope 镜像 510,051,032 B（Apache-2.0） | HF card + ModelScope API |
| 出处 | POPE 的格式化发布版：Li et al., *Evaluating Object Hallucination in Large Vision-Language Models*, arXiv:2305.10355；原始代码 `RUCAIBox/POPE` | dataset card README |
| 关键便利 | **图像已内嵌在 parquet 里** ⇒ 不需要单独下载 COCO val2014（原始 POPE 发布版才需要） | dataset card `features: image` |

**取数命令（镜像优先；脚本自己绝不下载）**：

```bash
export HF_ENDPOINT=https://hf-mirror.com
export HF_HOME=/root/autodl-tmp/hf
python -c "from huggingface_hub import snapshot_download; \
  snapshot_download('lmms-lab-encoder/POPE', repo_type='dataset', \
  revision='4db1276663dfa5eb8ad16a52d24c31a09e470896', \
  allow_patterns=['Full/random-00000-of-00001.parquet'], local_dir='/root/autodl-tmp/pope')"
mkdir -p data/pope/raw/Full && cp /root/autodl-tmp/pope/Full/random-00000-of-00001.parquet data/pope/raw/Full/

# 兜底：ModelScope（仓库名先用 HubApi 核实，规矩照旧）
python -c "from modelscope.hub.api import HubApi; print(HubApi().get_dataset_files('lmms-lab/POPE'))"
modelscope download --dataset lmms-lab/POPE --include 'Full/random-00000-of-00001.parquet' --local_dir /root/autodl-tmp/pope
```

`--prepare` 找不到 parquet 时**就是把这套命令原样打印出来**并以 exit 2 停止（不会自己联网）。

---

## 4. 流程与产物

```bash
# 0) 只打印、不执行、不写盘（任意机器可跑）
python tools/_p1640_p3_second_downstream.py --plan
python tools/_p1640_p3_second_downstream.py --prepare --dry-run
python tools/_p1640_p3_second_downstream.py --eval --rank base --dry-run
python tools/_p1640_p3_second_downstream.py --aggregate --dry-run

# 1) 准备：校验原始 parquet（列、行数=dataset card、答案必须落在 yes/no 标签空间），
#    抽出内嵌图像，写 paper3/test-pope-random.parquet + data/pope/images/random/*.png
python tools/_p1640_p3_second_downstream.py --prepare

# 2) 三臂各一个进程（prompt "Answer briefly. <question>"，greedy，max_new_tokens=16 —— 与 S28 完全一致）
python tools/_p1640_p3_second_downstream.py --eval --rank base
python tools/_p1640_p3_second_downstream.py --eval --rank 5
python tools/_p1640_p3_second_downstream.py --eval --rank 6

# 3) 配对 bootstrap + TOST（确定性、可重跑）
python tools/_p1640_p3_second_downstream.py --aggregate --strict
```

**写盘边界**：`--plan`/`--self-test`/`--dry-run` 不写任何东西；`--prepare` 只写
`paper3/test-pope-<split>.parquet` 与 `data/pope/images/<split>/*.png`（已存在且合法则跳过，`--force` 才重写）；
`--eval` 每臂写 `outputs/analysis/p3_second_downstream_<base|5|6>.json`（合法则跳过）；`--aggregate` 只写
`outputs/analysis/p3_second_downstream.json`（无 wall-clock 字段 ⇒ 同输入重跑逐字节一致）。

**适配器纪律（不训练、不静默换模型）**：三臂用的是归档那一轮的
`outputs/p3_vqa_adapters/r{5,6}_step`（VQA-RAD 全训练集 1793 对、3 epoch、`--per-step`）。
脚本会读 `adapter_config.json` 校验 `r` = 5/6、`lora_alpha` = 2r、targets = qkvo，
并把 `adapter_model.safetensors` 的 sha256 与归档记录比对：

| 臂 | 归档 sha256（来源 `outputs/analysis/cloud_vqa_full451_{5,6}.json::meta.adapter_sha256`） |
|---|---|
| r5_step | `1615d21ecf2d6200effa9b1c180d1256934d22d3cbb16f6b8695ea902b64767b` |
| r6_step | `5f681f3f80ee0fa2db1626b98f64113554305fd133f41a3867ebf74c2affee42` |

⚠️ **本工作区里只有 `outputs/p3_vqa_adapters/r5`、`r6`（早期冒烟适配器），没有 `r5_step`/`r6_step`**
（`_p1613_p3_cloud_runner.py` 明确说这两个 plain 目录"deliberately NOT used"）。若实例上也已丢失，
只能按归档配方**重建**（`tools/_p1516_p3_vqa_downstream.py ensure_adapter()`：1793 对、3 epoch、per-step；
云端实测每臂 **约 64 分钟**含训练+300 题评测，见 `docs/p3_cloud_round_notes.md` §5）。
sha256 不匹配时脚本**拒绝评测**（exit 2），不会拿另一个适配器的数字冒充。

---

## 5. 32 GB 卡上的预期时间 / 显存 / 磁盘

**时间（实测锚点，非估算）**：归档的 451 题 VQA-RAD 三臂在同一天同一台云卡上分别用了
**3.47 / 3.63 / 4.40 分钟**（`outputs/analysis/cloud_vqa_full451_*.json::meta.elapsed_min`）
= **0.46–0.59 s/题**（最多生成 16 个 token）。POPE 答案是 1 个 token、会立刻 EOS 停下，所以
**3000 题 ≈ 15–30 分钟/臂**，三臂串行 **≈1–1.5 小时**（不含 prepare；prepare 抽 3000 张图约 1–3 分钟 CPU）。
若要把 `popular`/`adversarial` 也跑上（`--split all` 三个 split 共 9000 题），单臂升到 ~45–90 分钟，**但 `random` 一档已满足"一小时内"**。

**显存**：归档那一轮 4-bit LLaVA-1.5-7B 加载占 **4.1 GB**（`docs/p3_cloud_round_notes.md` §5），batch=1、576 个图像 token；
32 GB 卡上约占 13%，**建议至少 12 GB 空闲**即可，不存在 OOM 风险。三臂是三个独立进程，不同时驻留。

**磁盘**：原始 parquet ≤255 MB（单 split 更小）；抽出的 PNG 按 VQA-RAD 的实测尺度估算（`data/vqa_rad/images`
**662 MB / 2244 张** = 0.295 MB/张）⇒ 3000 张 **≈0.9 GB**；每个臂归档 <1 MB。
`HF_HOME`/`MODELSCOPE_CACHE` 指到 50 GB 数据盘（不放 30 GB 根盘）。

---

## 6. 验收标准（`--aggregate --strict` 逐条强制）

1. 三臂归档齐全，且**题数相同**（按问题配对的前提）；
2. 三臂 `refs` **逐字节一致**（sha256 相同），且与 `paper3/test-pope-random.parquet` 的行序一致；
3. 三臂的指标**等于从各自归档的 hypotheses 重算的值**（不引用汇总字段）；
4. 适配器来源 = 归档那一轮（`adapter_source=reused_from_archived_round` 且 sha256 匹配）；
5. 每对对比（base−5、base−6、5−6）× 每个指标（accuracy、token_f1、pope_f1）都给出
   **delta、95% CI、TOST p、最小等价边界**；
6. `--aggregate` **打印的每一个数字都在写出的 JSON 里被逐项断言**（`--self-test` 会先在合成 fixture 上
   跑同一套 ledger：53 个数字全过才通过）；
7. 同输入重跑 `--aggregate` **逐字节一致**（无 wall-clock 字段，RNG 固定 `20261024`）。

**预声明边界**：accuracy / token F1 / yes 类 F1 都用 **0.05**（从 S28 原样沿用，不因题数变多而重新拟合）；
每对对比都报 `min_equivalent_margin = max(−ci90_low, ci90_high)`。
3000 题下 accuracy 的二项标准误 ≈ **0.009**，所以 0.05 这个边界这次**不再贴着分辨力极限**。

**POPE 自己的指标**（脚本一并给出，便于与文献对齐）：`pope_precision` / `pope_recall` / `pope_f1`
（yes 为正类，`2TP/(2TP+FP+FN)`）、`yes_ratio`（预测 yes 的比例）、混淆矩阵 `tp/fp/fn/tn`。

---

## 7. 什么结果强化 / 削弱论文的下游主张

`--aggregate` 会把结论写成三个取值之一（`claim_verdict.second_task_verdict`）：

| 取值 | 触发条件 | 对论文的含义 |
|---|---|---|
| `supports_the_adapters` | 两个适配器相对 base 在 accuracy 上**都**做到"等价或更好"（TOST 等价，或 95% CI 下界 > 0） | **强化**：第二个任务族不再与 VQA-RAD 方向冲突，且 3000 题把 S28 的分辨力极限抹掉；可直接用第 8 节的 `two_tasks` 句 |
| `task_dependent_effect` | 任一适配器 accuracy 的 95% CI 上界 < −0.05 | **削弱**：下游收益是任务相关的（POPE 上变差），论文必须如实写"task-dependent"，并把 S28 的措辞从"small downstream gain"收紧 |
| `inconclusive` | 两者都不成立 | 中性：既不能声称第二个任务支持适配器，也不能说它反证；仍需如实报告 |

**先验提醒（第三方文献，不是我们的数字）**：Commentary 引用过 LLaVA-1.5 报告在 POPE 上的
87.3 / 86.1 / 84.2（rand/pop/adversarial）。base 模型本身在 POPE 上分数很高，而两个适配器是在
VQA-RAD（短答、医学图像）上微调的 ⇒ **"微调把 yes/no 偏置带偏、POPE 掉分"是完全可能的结果**。
因此本方案从一开始就把"削弱"场景写成可发布的结果（不删运行、不换 split），这也是这条 caveat 值得跑的原因。

---

## 8. 替换 caveat 的句子（英文）

**跑通且 `supports_the_adapters`（把"单一下游任务"这条 caveat 撤掉）**：

> The downstream check is repeated on a second, independent task: POPE (config \texttt{Full}, split
> \texttt{random}, 3000 held-out questions, revision 4db12766), with the same adapters, the same prompt and the
> same greedy decoding as the VQA-RAD evaluation. The adapters are equivalent to or better than the base model on
> POPE accuracy and yes-class F1 within the pre-declared 0.05 margin (paired by question, 20000 bootstrap
> replicates; smallest equivalent margin \emph{<m>}), so the downstream evidence rests on two task families
> rather than one, and the resolution limit of the 451-question VQA-RAD set no longer binds.

（对应归档字段：`meta.declared_margins`、`contrasts.<pair>.<metric>.min_equivalent_margin`、
`claim_verdict.second_task_verdict`；由 `--aggregate` 写入 `caveat_sentences.two_tasks`。）

**跑通但 `task_dependent_effect`（caveat 保留并改写为"任务相关"）**：

> A second downstream task (POPE, config \texttt{Full}/split \texttt{random}, 3000 questions) does not reproduce
> the VQA-RAD direction: the adapters lose accuracy by \emph{<d>} (95\% CI \emph{[lo, hi]}) beyond the
> pre-declared 0.05 margin, so the downstream effect is task-dependent and we make no claim that the
> alignment-energy ordering transfers to downstream accuracy.

**没跑成（如实标注，不冒充已做）**：`--aggregate` 的 `caveat_sentences.not_run` 就是这一句；
若最终没跑，S28 的"单一下游任务"措辞**必须保持原样**。

---

## 9. 未能离线核实 / 需要实例确认的假设

1. **POPE 的 `answer` 字段字面值**：预期是 `yes`/`no`（脚本在 `--prepare` 里断言 ≥99% 落在
   `{yes,no}`，否则 exit 2 并把观测到的取值分布打出来）。**未在本地打开过该 parquet**（本任务不允许下载）。
2. **单个 split 的 parquet 字节数**：只核实了整仓 download_size 255,022,914 B 与 ModelScope 镜像 510,051,032 B；
   单文件大小待 `--prepare` 实测记录。
3. **`r5_step`/`r6_step` 适配器在本机不存在**（只有 `r5`/`r6` 冒烟适配器）⇒ 实例/备份里必须能找到，
   否则要按归档配方重建（每臂约 64 分钟），脚本会打印配方并 exit 2。**这一点会直接影响这轮的实际耗时**。
4. **POPE 上的每题延迟**：由 VQA-RAD 的 0.46–0.59 s/题外推（POPE 只生成 1 个 token，理应更快），
   **没有 POPE 上的实测**（本任务不允许开机/评测）。
5. **base 模型在 POPE 上的实际分数**：未测；文献值 87.3/86.1/84.2 是**第三方报告**（Commentary 引用），
   只能作为"可能掉分"的先验，不能进 P3 的数字。
6. **ScienceQA 带图子集的确切题数**（常被引作 ~2017）：**未核实**，若日后改用 ScienceQA，必须由 `--prepare`
   类的步骤实测写出，不得直接引用该数。
7. **`--split all`（9000 题）在 32 GB 卡上的单臂耗时**：只有 `random`（3000 题）的估算，
   9000 题的 45–90 分钟是线性外推。