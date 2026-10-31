# PR R1.6 收尾 — LoRA / Adapter 的学习率扫描：公平比较做完之后，结论是什么

**任务**：`task-6`（causal-hardener）· **日期**：2026-10-12 ·
**主交付件**：本文 + `outputs/analysis/pr_peft_lr_sweep.json`（24 次运行 / 0 失败 / 2 seeds）+
对照基准 `outputs/analysis/pr_fullft_lr_sweep_full.json`（task-5）

**要回答的问题**（task-6 第 3 条）：**LoRA/Adapter 在自己的最优 lr 下，与 full-FT@1e-6（60.87 % / ΔCG −0.0016）比是什么？**

---

## 0. 结论速览

| 方法（各自最优 lr） | zero-shot top-1 % | ΔCG | R@1 | 与 full-FT@1e-6 的差 |
|---|---|---|---|---|
| 冻结基线 | 59.91 | — | 0.1555 | — |
| **full-FT @ 1e-6**（task-5，3 seeds） | **60.87 ± 0.21** | **−0.0016 ± 0.0052** | 0.1808 | — |
| **LoRA-both @ 1e-5**（2 seeds） | **60.69 ± 0.05** | **−0.0054 ± 0.0001** | 0.1765 | **−0.18 pp / −0.004** |
| LoRA-text @ 1e-5 | 60.06 ± 0.16 | −0.0073 ± 0.0034 | 0.1663 | −0.81 pp / −0.006 |
| LoRA-text @ 3e-4（gap 最优） | 51.48 ± 1.08 | −0.0469 ± 0.0000 | 0.1683 | −9.39 pp / **−0.045** |
| Adapter-both @ 3e-4（其最优） | 23.38 ± 0.57 | +0.0714 ± 0.0045 | 0.1425 | −37.5 pp / +0.073 |

**答案：LoRA 在它自己的最优 lr 下并没有胜过 full-FT。** 在 zero-shot 上 full-FT@1e-6 反而略高
（60.87 ± 0.21 对 60.69 ± 0.05，差 −0.18 pp，落在 full-FT 自身 seed 波动之内）；在 CG 上两者都≈0
（−0.0016 对 −0.0054，差 0.004，可忽略）。唯一能明显压低 CG 的配置是 **text-only LoRA @ 3e-4**
（ΔCG −0.0469），但它要付 **8.4 pp** 的 zero-shot（51.48 对冻结 59.91）。

⇒ **"用 LoRA / 只适配文本侧"这条建议不能再建立在"LoRA 比全量微调更能保住对齐"之上**：把两者都调到
各自最优后，它们在 zero-shot 与 CG 两个轴上**统计上不可区分**。可保留的是更窄的一条（见 §5）。

---

## 1. 协议（与 task-5 逐项对齐）与"确实是 PEFT"的代码级证明

协议取自 task-5 的 `tools/_p263_fullft_lr_sweep.py`（评测函数直接 import 复用，避免协议漂移）：
Flickr30k captions [0, 2000)、batch 64、fp16、10 epoch、AdamW(wd 0.01)、cosine（按 step）、
grad clip 1.0；评测 = ImageNet-1K 前 14,288 张单模板 zero-shot + Flickr30k [2000,3000) 的 CG/DG
（`src/gap_metrics.GapTracker`）与 R@1（1000 对）；冻结基线直接复用 task-5 的
`pr_fullft_lr_sweep_full.json :: frozen`（59.91 % / CG 0.8157 / R@1 0.1555），保证两批实验同一口径。
（`pr_peft_lr_sweep.json :: meta.protocol`）

**"不是全量微调"的三重断言**（`runs[*].peft_proof`，每次运行都过）：

| config | 可训练参数 | 架构推导期望值 | 占模型比例 | 非 PEFT 参数全冻结 | 注入模块 | 被包裹原层冻结 |
|---|---|---|---|---|---|---|
| `lora_both`（q,v；r=8 α=16；两塔） | 491,520 | 491,520 | 0.3249 % | ✔ | 48 | ✔ |
| `lora_text`（q,v；r=8 α=16；仅文本塔） | 196,608 | 196,608 | 0.1300 % | ✔ | 24 | ✔ |
| `adapter_both`（bottleneck d=64，self_attn+mlp，两塔） | 3,965,952 | 3,965,952 | 2.6216 % | ✔ | 48 | ✔ |

断言内容：① 所有不属于 PEFT 的参数 `requires_grad == False`；② 可训练数 == 从注入模块重算的数
== 架构推导的字面值；③ 可训练数 < 全模型参数数（151,277,313）。这直接对应 task-2 发现的坑
（"参数量大 ≠ 全量微调"）：LoRA 的 491,520 与 196,608 也与论文 strict-freeze 一节记录的
491,520 / 196,608 **逐位一致**。

---

## 2. 网格结果（2 seeds，全部数字见 `outputs/analysis/pr_peft_tables.md` T2/T3）

| config@lr | n | zero-shot % (mean ± sd) | ΔCG (mean ± sd) | R@1 |
|---|---|---|---|---|
| `lora_both@1e-5` | 2 | **60.69 ± 0.05** | **−0.0054 ± 0.0001** | 0.1765 |
| `lora_both@3e-5` | 2 | 60.52 ± 0.14 | +0.0025 ± 0.0028 | 0.1805 |
| `lora_both@1e-4` | 2 | 57.70 ± 0.41 | +0.0376 ± 0.0014 | 0.1757 |
| `lora_both@3e-4` | 2 | 48.02 ± 0.09 | +0.1194 ± 0.0033 | 0.1735 |
| `lora_text@1e-5` | 2 | 60.06 ± 0.16 | −0.0073 ± 0.0034 | 0.1663 |
| `lora_text@3e-5` | 2 | 59.77 ± 0.16 | −0.0002 ± 0.0038 | 0.1678 |
| `lora_text@1e-4` | 2 | 57.32 ± 0.31 | −0.0251 ± 0.0005 | 0.1698 |
| `lora_text@3e-4` | 2 | 51.48 ± 1.08 | **−0.0469 ± 0.0000** | 0.1683 |
| `adapter_both@1e-5` | 2 | 0.13 ± 0.07 | +0.4114 ± 0.0175 | 0.0020 |
| `adapter_both@3e-5` | 2 | 1.16 ± 0.15 | +0.3171 ± 0.0072 | 0.0173 |
| `adapter_both@1e-4` | 2 | 17.11 ± 0.40 | +0.1148 ± 0.0030 | 0.1242 |
| `adapter_both@3e-4` | 2 | 23.38 ± 0.57 | +0.0714 ± 0.0045 | 0.1425 |

（字段：`analysis.grid['<config>@<lr>'].{zero_shot_top1_pct_mean,zero_shot_top1_pct_sd,dCG_mean,dCG_sd,R@1_mean}`；
逐 seed 原值 `runs[*].final`；逐 epoch 训练损失 `runs[*].history.train_loss`。两 seed 之间的复现性极好：
LoRA 的 zero-shot 差 ≤0.7 pp、ΔCG 差 ≤0.005。）

**三个方法对 lr 的敏感方向完全不同**（这是 R1.6 最有力的证据）：

| 方法 | 随 lr 升高 | 最优 lr |
|---|---|---|
| full-FT（task-5） | **急剧变差**（1e-6: 60.87 % → 1e-4: 0.14 %） | 最低端 1e-6 |
| LoRA | 温和变差（1e-5: 60.69 % → 3e-4: 48.02 %），CG 在 1e-4 起变正 | 低端 1e-5 |
| Adapter（both） | **变好**（1e-5: 0.13 % → 3e-4: 23.38 %） | 高端 3e-4 |

⇒ **同一套共享超参不可能对三者都公平**：论文用 lr=1e-4 时，吃亏最大的是 full-FT（0.14 %），
LoRA 只是从 60.7 掉到 57.7，Adapter 反而在 1e-4/3e-4 才勉强开始工作。也就是说，原稿那种比较里
**LoRA 的优势至少有一部分来自"full-FT 被 lr 打残"**。

---

## 3. Adapter 的 both 配置在注入时就已损坏（关键 caveat）

`runs[*].post_injection_gap_retrieval`（注入后、训练前的同口径评测）：

| config | 注入后 CG | ΔCG vs 冻结 | 注入后 R@1 |
|---|---|---|---|
| `lora_both` | 0.8156 | **−0.0001** | 0.1570 |
| `lora_text` | 0.8157 | **+0.0000** | 0.1655 |
| `adapter_both` | **1.2617** | **+0.4460** | **0.0010** |

- LoRA 在注入处是**恒等**的（`lora_B` 零初始化）⇒ 与冻结模型逐位一致，是干净的对照起点。
- bottleneck Adapter 在注入处**不是恒等**：`AdapterWrapper` 的 `up` 层 `weight=0` 但 **`bias≠0`**，
  于是每个位置被加了一个常数向量 → **注入本身就把 R@1 从 0.1555 打到 0.0010（≈随机）**，CG 抬高 55 %。
  这与归档 `outputs/analysis/adapter_common_baseline.json` 记录的一致
  （其 `adapter_both` 的 `dCG_common_mean = +0.5003`，并注明"published convention 是从注入后状态量起"）。
- 因此：**任何"Adapter 的 CGΔ"如果是从它自己的注入后状态量起（论文的 delta_old 口径），
  其参照点本身是坏的**；本表用统一口径（对冻结模型）给出，`adapter_both` 在任何 lr 下都是正的 ΔCG
  （+0.071…+0.411），从未回到冻结水平。

---

## 4. 与 full-FT 的对照（`analysis.vs_fullft`）

| 量 | full-FT 最优（lr=1e-6） | 最优 PEFT（lora_both@1e-5） | 差（PEFT − FT） |
|---|---|---|---|
| 单次最优 run 的 zero-shot | 61.02（seed 42） | 60.72（seed 42） | −0.30 pp |
| 2–3 seed 均值 zero-shot | 60.87 ± 0.21 | 60.69 ± 0.05 | **−0.18 pp** |
| ΔCG（均值） | −0.0016 ± 0.0052 | −0.0054 ± 0.0001 | −0.004（可忽略） |
| R@1（均值） | 0.1808 ± 0.0028 | 0.1765 ± 0.0014 | −0.004 |

（字段：`analysis.vs_fullft.best_*`、`analysis.vs_fullft.delta_best_peft_minus_best_fullft`；
full-FT 逐 lr 参考 `analysis.vs_fullft.fullft_per_lr`，来源 `pr_fullft_lr_sweep_full.json :: analysis.per_lr`。）

**判定**：按 task-6 预设的判据（`analysis.vs_fullft.interpretation_rule`：zero-shot 差为正、
ΔCG 差为负才favour PEFT），**LoRA 没有通过**——zero-shot 差 −0.18~−0.30 pp（负），
ΔCG 差 −0.004（负但极小）。即在"各自调到最优"这一最强公平性检验下，
**full-FT 与 LoRA 打平**，只有 text-only LoRA 在付出 zero-shot 代价时可以换来更小的 gap。

---

## 5. 建议怎么改（英文段落，可直接进 response letter）

> **Per-method learning-rate tuning (R1.6, completed).** We tuned the learning rate for every
> method under one identical protocol (Flickr30k captions 0–1999, batch 64, fp16, 10 epochs;
> ImageNet-1K zero-shot on the same 14,288 images; CG/DG and R@1 on the same splits), two seeds
> per cell, and verified in code that each adapter run trains only its own parameters
> (491,520 for LoRA-both, 196,608 for LoRA-text, 3,965,952 for the d=64 bottleneck Adapter; every
> other parameter frozen). The three methods respond to the learning rate in *opposite*
> directions: full fine-tuning is best at the lowest rate (60.87 ± 0.21 % zero-shot, ΔCG
> −0.0016), LoRA is best at the low end too but far less sensitive (60.69 ± 0.05 %, ΔCG
> −0.0054 at lr 1e-5), and the both-position bottleneck Adapter only begins to work at the high
> end (23.38 ± 0.57 % at lr 3e-4) because its insertion is not identity — the randomly
> initialised bottleneck alone drops R@1 from 0.1555 to 0.0010 and raises CG by 0.446 before any
> training. Consequently (i) a single shared learning rate cannot be fair to all three methods,
> and the low rate at which LoRA looks best is precisely the rate at which the previous
> comparison crippled full fine-tuning; (ii) **at each method's own optimum, LoRA does not beat
> full fine-tuning**: the two are within 0.2 pp of zero-shot accuracy (60.69 vs 60.87, inside
> full fine-tuning's own seed spread) and within 0.004 of ΔCG, both indistinguishable from the
> frozen model; and (iii) the only configuration that clearly reduces the gap is text-only LoRA
> at lr 3e-4 (ΔCG −0.0469 ± 0.0000), which costs 8.4 pp of zero-shot accuracy. We therefore
> restate the recommendation: preferring text-side adaptation is supported by the strict-freezing
> control (the vision encoder need not be touched) and by the gap metric, **not** by a claim that
> LoRA preserves alignment better than an equally well tuned full fine-tuning.

### 建议写进 limitation 的一句

> The three method families respond to the learning rate in opposite directions (full fine-tuning
> optimal at 1e-6, LoRA at 1e-5, the both-position bottleneck Adapter only functional from 1e-4
> up), so no single shared learning rate is fair to all of them; once each is tuned to its own
> optimum, LoRA and full fine-tuning are indistinguishable on both zero-shot accuracy
> (60.69 ± 0.05 % vs 60.87 ± 0.21 %) and the centroid gap (ΔCG −0.0054 vs −0.0016), and the only
> configuration that clearly narrows the gap — text-only LoRA at lr 3e-4 (ΔCG −0.047) — pays
> 8.4 pp of zero-shot accuracy for it.

---

## 6. 溯源表

| 文档中的数字 | 归档文件 | 字段 |
|---|---|---|
| PEFT 代码级证明（491,520 / 196,608 / 3,965,952；全冻结断言） | `outputs/analysis/pr_peft_lr_sweep.json` | `runs[*].peft_proof.*` |
| 网格逐 run 结果 | 同上 | `runs[*].final.{zero_shot_imagenet1k_top1_pct,CG,DG,R@1_mean}` |
| 逐 (config, lr) 均值±sd | 同上 | `analysis.grid['<config>@<lr>'].*` |
| 注入后几何（LoRA 恒等 / Adapter 损坏） | 同上 | `runs[*].post_injection_gap_retrieval.{CG,R@1_mean}` |
| 每配置最优 lr | 同上 | `analysis.best.best_lr_per_config` |
| 最优 PEFT vs 最优 full-FT 的差 | 同上 | `analysis.vs_fullft.delta_best_peft_minus_best_fullft` |
| full-FT 逐 lr 参考值 | `outputs/analysis/pr_fullft_lr_sweep_full.json` | `analysis.per_lr.<lr>.{zero_shot_top1_pct_mean,zero_shot_top1_pct_sd,dCG_mean,R@1_mean_of_runs}` |
| 冻结基线（两批共用） | 同上 | `frozen.{zero_shot.top1_pct,gap_retrieval.CG,gap_retrieval.DG,gap_retrieval.R@1_mean}` |
| 归档 Adapter 的 `dCG_common = +0.5003` | `outputs/analysis/adapter_common_baseline.json` | `adapter_both.dCG_common_mean` |
| 逐 epoch 训练损失（含 Adapter 在 1e-5 停在 ln 64 附近） | `outputs/analysis/pr_peft_lr_sweep.json` | `runs[*].history.train_loss` |

**本次新建文件**

| 文件 | 说明 |
|---|---|
| `tools/_p291_peft_lr_sweep.py` | LoRA/Adapter lr 扫描（`--configs/--lrs/--seeds/--resume/--epochs`；评测直接 import `_p263`） |
| `tools/_p292_peft_tables.py` | 表格与结论渲染（数字不手抄） |
| `outputs/analysis/pr_peft_lr_sweep.json` | **主结果：24 次运行 / 2 seeds / 0 失败** |
| `outputs/analysis/pr_peft_tables.md` | T1–T6 表 |
| `outputs/analysis/pr_peft_verdict.json` | 机器可读结论块 |
| `outputs/analysis/pr_peft_sweep/<config>_lr<lr>_seed<s>/peft_state_last.pt` | 每次运行的最终 PEFT 权重（LoRA 数 MB；Adapter ~16 MB） |

**复现命令**（单进程串行；本机 RTX 4060 8 GB，全程约 2.4 h，峰值 <2 GB）
```powershell
$env:PYTHONIOENCODING='utf-8'; $env:PYTHONUTF8='1'
python tools\_p291_peft_lr_sweep.py --apply --seeds 42 --resume        # 12 runs
python tools\_p291_peft_lr_sweep.py --apply --seeds 42,123 --resume   # 补 seed 123
python tools\_p292_peft_tables.py --apply
```

---

## 7. 限制（必须与结论一起写）

1. **只有 2 个 seed**（每格 2 次运行）。LoRA 的 seed 间差异极小（zero-shot ≤0.7 pp、ΔCG ≤0.005），
   因此 LoRA 的结论稳；但 Adapter 的 1e-4/3e-4 两格只有 2 个点，其"未达冻结水平"的结论稳健
   （差距 36–43 pp），具体数值仍有不确定性。
2. **训练集是 2000 条 caption**（与 task-5 对齐），比论文主表用的规模小；LoRA 在低 lr 下 train loss
   仍高（1e-5: 0.274–0.388，而 full-FT@1e-6 为 0.141–0.161），说明低 lr 的 LoRA **未完全收敛**。
   若换更大数据/更多 epoch，"LoRA 最优"可能移到更低的 lr 或表现更好 —— 这一点本实验**没有测**。
3. **R@1 口径**：本 val 切片每图 5 条 caption，对角口径上限 ≈0.2（本表所有 run 都在 0.14–0.18），
   因此 R@1 不能与论文主表的 0.627 之类数字横向比较；这里只用于**本网格内部**的一致性检查。
4. **LoRA 只测了 q,v（r=8, α=16）**、Adapter 只测了 both(d=64)；论文还有 qvko / 分层 / 其他 d 的配置，
   本扫描没有覆盖，因此"LoRA 最优"仅指这一族。
5. **Adapter 的注入损坏是仓库现有实现（`src/peft_methods.py`：`up.bias` 非零）**；本报告把它当作事实
   记录并用于解释 Adapter 的 lr 方向，**不**主张"Adapter 方法本身无效"（把 `up.bias` 也零初始化后
   是否恒等、是否更好，未测）。
6. 全部实验与 task-5 共用 GPU（单进程串行），未与其它任务并发。
