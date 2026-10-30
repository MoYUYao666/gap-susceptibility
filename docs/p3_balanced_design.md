# P3 均衡共同种子设计（S29 环境矩阵 / S37 方差分解）

生成脚本：`tools/_p1638_p3_balanced_env_design.py`（`--audit` / `--plan` / `--power`）
结果归档：`outputs/analysis/p3_balanced_design_plan.json`（确定性输出，整数 rng 种子 7，无墙钟字段）
本文件快照时间：2026-10-24（torch 2.6/cu124 补种子轮正在本机运行中）

---

## 1. 当前的不均衡（一张表）

**每个格子 = 一次训练**，协议是归档的 20 样本 / 3 epoch（`lr 5e-5`、`batch 1`、`uniform`、
`adamw`、`float16`、`grad_mask none`、`attn_targets qkvo`、`lora_alpha = 2*rank`）。
"共同种子"指设计目标集 `{42, 7, 123, 999}`。

| stack（torch/CUDA） | 机器 | rank 5：种子数（含共同种子） | rank 6：种子数（含共同种子） | 归档来源 |
|---|---|---|---|---|
| torch 2.9/cu130 | RTX 4060 Laptop（本地） | 5（3/4） | 5（3/4） | `outputs/analysis/p3_seeds_combined.json` 的 `values.r5` / `values.r6` |
| torch 2.12/cu130 | RTX 4080 SUPER（云） | 10（4/4） | 10（4/4） | `paper3/scripts/outputs/experiments/cloud_verify_r{5,6}_s*.json` 的 `delta_E`（排除 `partial`/`imgs`/`_e1_`） |
| torch 2.4/cu121 | RTX 4060 Laptop（本地） | 4（3/4） | **1（1/4）** | 文件名带 `_torch24` 后缀的行（种子 42）＋ rank 5 的 `_a10` 行（种子 123/999，即 `p3_env_variance.json` 里 torch 2.4/cu121 桶的 4 个值） |
| torch 2.6/cu124 | 4060（种子 42）＋ 云（7/123/999） | 3（3/4） | **1（1/4）** | 文件名带 `_torch26` 后缀的行 |

**不均衡的三个事实**（全部由归档字段数出来，`--audit` 可直接复现）：

1. 每个 (stack, rank) 的种子数从 **1 到 10**，极差 9；今天共 **39** 个格子。
2. **两个格子只有 1 个种子**：`torch24_cu121` 的 rank 6、`torch26_cu124` 的 rank 6（都只有种子 42）。
3. 四个 stack **真正共有的种子只有 `{42, 123}`**——只有 2 个观测/环境（df_within = 4）：
   这种设计下 `sigma_env` / `sigma_seed` 虽然能算（30.5 / 18.9，份额 0.594，
   见 `power_comparison.designs.anchor_seed_today`），但"环境差异"只是**这 2 个种子**上的差异，
   换个共同种子集结论可能就变——即**环境项被种子集绑住**，正是要消除的混淆。

> ⚠️ **不要再用 `tools/_p1570_env_variance_update.py`**：它用宽松 glob `verify_r5_s*_a10*.json`
> 选 torch 2.4/cu121 桶，今天这条 glob 也会命中 `_a10_torch26.json` 行，归档的
> sigma_env 31.1489 / sigma_seed 34.2950 / share 0.4520 已不可复现。本脚本与
> `tools/_p1613_p3_cloud_runner.py` 一样使用**显式注册表**，逐文件校验 payload 字段。

---

## 2. 最小均衡方案（补哪些格子、在哪里跑）

共同种子集 `{42, 7, 123, 999}`、rank 5+6、4 个 stack ⇒ 均衡设计共 **32** 格，
其中共同种子格今天已有 **22** 格（= 32 − 10）。缺 **10** 格，按位置分
**10 LOCAL / 0 CLOUD**（云 stack 一格都不缺），其中：

* **4 格正在跑**（本机 torch 2.6/cu124 轮，`tools/_p1613_p3_cloud_runner.py --job env-seeds`）；
  不要手工重跑，先看目标归档是否已出现；
* **6 格需要新跑**（全部本地）：

| stack | rank | seed | 用哪个解释器 | 跑完把未加后缀的输出另存为 |
|---|---|---|---|---|
| torch 2.4/cu121 | 5 | 7  | `D:\Anaconda\envs\torch24\python.exe` | `..._a10_torch24.json` |
| torch 2.4/cu121 | 6 | 7  | `D:\Anaconda\envs\torch24\python.exe` | `..._a12_torch24.json` |
| torch 2.4/cu121 | 6 | 123 | `D:\Anaconda\envs\torch24\python.exe` | `..._a12_torch24.json` |
| torch 2.4/cu121 | 6 | 999 | `D:\Anaconda\envs\torch24\python.exe` | `..._a12_torch24.json` |
| torch 2.9/cu130 | 5 | 7  | `D:\Anaconda\envs\pytorch\python.exe` | （`p3_seeds_combined.json` 加 `values.r5.7`） |
| torch 2.9/cu130 | 6 | 7  | `D:\Anaconda\envs\pytorch\python.exe` | （`p3_seeds_combined.json` 加 `values.r6.7`） |

**云 stack（torch 2.12/cu130）一格都不缺**——rank 5/6 都已含全部 4 个共同种子，
**这一轮不需要开云实例**。（若日后换共同种子集，`--plan --common-seeds ...` 会自己算出新的缺口。）

> ⚠️ **未加后缀的文件名属于别的 stack**：`run_training.py` 只会写
> `verify_r{rank}_s{seed}_lr5e-05_nw_float1_adamw_e3_bcuniform_a{10,12}.json` 这个名字，
> 而 rank 5 的种子 123/999 的**未加后缀**行是 **torch 2.4/cu121 的归档行**
> （`p3_env_variance.json` 的 torch 2.4/cu121 桶里 -2.5 与 +64.5 就是它们）。
> 跑 torch 2.4 的新格子前**先把这两个文件备份**；跑完立刻另存为 `_torch24` 名字再还原。
> torch 2.6/cu124 轮次里 `tools/_p1613_p3_cloud_runner.py` 已经用"跑前保存、跑后写回"的办法处理了同一问题。

---

## 3. 成本

* **每轮实测（本次协议在本地机器上的记录）**：`outputs/analysis/p3_rerun_{protocol,seeds,extra}.json`
  的 `elapsed_min` 共 10 次（rank 5/6）：21.3, 21.4, 21.4, 21.5, 22.9, 23.0, 25.9, 26.6, 43.7, 65.8 分钟，
  中位数 **23.0**；`outputs/run_*.log` 里同协议的 `Training time:` 另有 21 条（1265–5104 秒）。
  合并 31 条记录的中位数 **22.6 分钟**。
* **torch 2.4/cu121 与云 stack 的单轮耗时：归档里没有**——这两个 stack 的归档文件
  （`verify_*_torch24.json`、`cloud_verify_*.json`）都不带 elapsed 字段，
  `docs/p3_cloud_round_notes.md` 也没有它们的单轮实测。**如实记为未知**，
  不拿别的 stack 的数字冒充。
* **估算**（归档 `cost_estimate` 字段）：
  * 只按实测耗时的格子：**0.75 GPU 小时**（= torch 2.9 的 2 格 × 22.6 分钟）；
  * 把 8 个未知耗时的格子按实测中位数 22.6 分钟计价：**约 3.76 GPU 小时**。
* 补充：torch 2.6 轮的 6 格跑完后，`outputs/analysis/p3_env_seeds_runlog.json` 的
  `runs.*.elapsed_seconds` 会给出该 stack 的真实单轮耗时，可回填这个未知量。

**结论：把 4 个 stack 对齐到 `{42,7,123,999}` 只需 6 次新训练、约 3.8 GPU 小时（本地过夜即可）。**

---

## 4. 补完之后 S29 / S37 会怎么说

**方法完全沿用现有的那一套**（不是新方法）：环境层单因素随机效应 ANOVA，
`n0 = (n - Σn_i²/n)/(k-1)` 的不等样本量校正，`sigma_seed² = MS_within`，
`sigma_env² = max(0, (MS_between - MS_within)/n0)`——与
`outputs/analysis/p3_env_variance.json` 的 `meta.method`、
`tools/_p1613_p3_cloud_runner.py` 的 `decomposition()` 一致。
本期新增的只有 **bootstrap 的抽样单位**：按格子重采样（固定 rng 种子 7，10000 次），
归档里 `power_comparison` 同时给出"环境内重采样"（与归档 `bootstrap.share_ci95` 可比）
和"按格子配对重采样"（只有共同种子设计才可能）两套区间。

rank 5、共同种子 `{42,7,123,999}` 的对照（实测值，`power_comparison`）：

| 量 | 今天（不均衡，1–10 种子/环境） | 均衡设计（4 种子/环境） |
|---|---|---|
| `sigma_env` | 30.5 | **36.5** |
| `sigma_seed` | 34.5 | **28.2** |
| 环境份额 `env_variance_share` | 0.440 | **0.625** |
| 份额 CI95（环境内 bootstrap） | [0.249, 0.749]，宽 0.500 | [0.466, 0.932]，宽 0.465 |
| `sigma_env` CI95 宽 | 31.5 | 35.7 |
| 环境份额是否可识别 | 勉强（四个 stack 共有种子只有 `{42,123}`，df_within = 4） | **是**（今天已到 13/16 格，df_within = 9；补完 4 种子/环境后 df_within = 12） |

**怎么读**：均衡后份额区间宽度基本不变（0.500 → 0.465），但含义变了——
今天的区间是"stack 之间的差异＋每个 stack 恰好有哪些种子"混在一起
（四个 stack 共有的种子只有 `{42,123}` 两个，环境差异就是这两个种子上的差异），
均衡后的区间才是**配对同种子集（4 个）下的环境效应**；同时 `sigma_env` 的点估计变大
（30.5 → 36.5）、份额从 44% 升到 63%，说明今天的环境项被不均衡的种子集**低估**了。
`sigma_env` 的区间反而变宽（31.5 → 35.7）是诚实的代价：均衡设计只有 16 个观测，
但它是无偏的；今天多出来的 23 个观测落在不同种子上，并不增加环境项的信息。

**S29（表 `tab:envcloud`）**：机器列要写清 torch 2.6/cu124 组跨机器
（种子 42 在 RTX 4060 Laptop，种子 7/123/999 在云 GPU）；
rank 5/6 每行的 n 与 sd 改为四种子值，caption 不再用单个种子下结论。

**S37（表 `tab:envvar` + sigma 值）**：四个 stack 都写 4 个共同种子，
报 `sigma_env` / `sigma_seed` / 份额三件套，并显式说明"这是共同种子设计"；
并排给出"今天的不均衡设计"与"共同种子设计"两套数（本文件第 4 节表格），
不要只留一套。`outputs/analysis/p3_env_variance.json`（31.1 / 34.3 / 45%）**必须被取代而不是延续**，
内容门禁 `tools/_p1575_content_audit.py` 的检查源要同步改指
`p3_env_stack_seeds.json`（轮次跑完时由 runner 写出）或本例的
`p3_balanced_design_plan.json`。

---

## 5. 操作员命令（照抄即可）

### 5.1 torch 2.6/cu124 正在跑的 4 格——不要手工重跑

先看目标归档是否已出现；跑完用 runner 的 `--aggregate` 收口：

```powershell
Test-Path paper3\scripts\outputs\experiments\verify_r6_s999_lr5e-05_nw_float1_adamw_e3_bcuniform_a12_torch26.json
& 'D:\Anaconda\envs\torch26\python.exe' tools\_p1613_p3_cloud_runner.py --job env-seeds --aggregate
```

（`--job env-seeds` 本身可重入：输出已存在且校验通过就会跳过。）

### 5.2 需要新跑的 6 格（本地，约 2.3 小时，可过夜）

**先备份两个未加后缀的 torch 2.4 归档行**：

```powershell
Copy-Item paper3\scripts\outputs\experiments\verify_r5_s123_lr5e-05_nw_float1_adamw_e3_bcuniform_a10.json `
          paper3\scripts\outputs\experiments\_backup_r5_s123_a10.json
Copy-Item paper3\scripts\outputs\experiments\verify_r5_s999_lr5e-05_nw_float1_adamw_e3_bcuniform_a10.json `
          paper3\scripts\outputs\experiments\_backup_r5_s999_a10.json
```

**torch 2.4/cu121 的 4 格**（跑完立刻另存为 `_torch24`，再还原上面两个备份）：

```powershell
# r5 s7
& 'D:\Anaconda\envs\torch24\python.exe' paper3/scripts/run_training.py --rank 5 --seed 7 --epochs 3 --num-samples 20 --lr 5e-5 --batch-size 1 --block-config uniform --opt adamw --compute-dtype float16 --attn-targets qkvo --grad-mask none --lora-alpha 10
Copy-Item paper3\scripts\outputs\experiments\verify_r5_s7_lr5e-05_nw_float1_adamw_e3_bcuniform_a10.json `
          paper3\scripts\outputs\experiments\verify_r5_s7_lr5e-05_nw_float1_adamw_e3_bcuniform_a10_torch24.json

# r6 s7
& 'D:\Anaconda\envs\torch24\python.exe' paper3/scripts/run_training.py --rank 6 --seed 7 --epochs 3 --num-samples 20 --lr 5e-5 --batch-size 1 --block-config uniform --opt adamw --compute-dtype float16 --attn-targets qkvo --grad-mask none --lora-alpha 12
Copy-Item paper3\scripts\outputs\experiments\verify_r6_s7_lr5e-05_nw_float1_adamw_e3_bcuniform_a12.json `
          paper3\scripts\outputs\experiments\verify_r6_s7_lr5e-05_nw_float1_adamw_e3_bcuniform_a12_torch24.json

# r6 s123
& 'D:\Anaconda\envs\torch24\python.exe' paper3/scripts/run_training.py --rank 6 --seed 123 --epochs 3 --num-samples 20 --lr 5e-5 --batch-size 1 --block-config uniform --opt adamw --compute-dtype float16 --attn-targets qkvo --grad-mask none --lora-alpha 12
Copy-Item paper3\scripts\outputs\experiments\verify_r6_s123_lr5e-05_nw_float1_adamw_e3_bcuniform_a12.json `
          paper3\scripts\outputs\experiments\verify_r6_s123_lr5e-05_nw_float1_adamw_e3_bcuniform_a12_torch24.json

# r6 s999
& 'D:\Anaconda\envs\torch24\python.exe' paper3/scripts/run_training.py --rank 6 --seed 999 --epochs 3 --num-samples 20 --lr 5e-5 --batch-size 1 --block-config uniform --opt adamw --compute-dtype float16 --attn-targets qkvo --grad-mask none --lora-alpha 12
Copy-Item paper3\scripts\outputs\experiments\verify_r6_s999_lr5e-05_nw_float1_adamw_e3_bcuniform_a12.json `
          paper3\scripts\outputs\experiments\verify_r6_s999_lr5e-05_nw_float1_adamw_e3_bcuniform_a12_torch24.json

# 还原被 run_training.py 覆盖的 torch 2.4 rank-5 归档行
Copy-Item paper3\scripts\outputs\experiments\_backup_r5_s123_a10.json `
          paper3\scripts\outputs\experiments\verify_r5_s123_lr5e-05_nw_float1_adamw_e3_bcuniform_a10.json -Force
Copy-Item paper3\scripts\outputs\experiments\_backup_r5_s999_a10.json `
          paper3\scripts\outputs\experiments\verify_r5_s999_lr5e-05_nw_float1_adamw_e3_bcuniform_a10.json -Force
```

> torch 2.4 这 4 格在 `--plan` 里没有自动改名保护（那是 runner 对 torch 2.6 的机制），
> 所以上面 4 条 `Copy-Item` 与 2 条还原**必须手工执行**，否则 rank 5 的种子 123/999
> 归档行会被覆盖，`p3_env_variance.json` 的 torch 2.4/cu121 桶就对不上。

**torch 2.9/cu130 的 2 格**（跑完把 `values.r5.7` / `values.r6.7` 加进
`outputs/analysis/p3_seeds_combined.json`，并更新 `n_seeds`）：

```powershell
& 'D:\Anaconda\envs\pytorch\python.exe' paper3/scripts/run_training.py --rank 5 --seed 7 --epochs 3 --num-samples 20 --lr 5e-5 --batch-size 1 --block-config uniform --opt adamw --compute-dtype float16 --attn-targets qkvo --grad-mask none --lora-alpha 10
& 'D:\Anaconda\envs\pytorch\python.exe' paper3/scripts/run_training.py --rank 6 --seed 7 --epochs 3 --num-samples 20 --lr 5e-5 --batch-size 1 --block-config uniform --opt adamw --compute-dtype float16 --attn-targets qkvo --grad-mask none --lora-alpha 12
```

### 5.3 收口与复核

```powershell
& 'D:\Anaconda\envs\pytorch\python.exe' tools\_p1638_p3_balanced_env_design.py --audit
& 'D:\Anaconda\envs\pytorch\python.exe' tools\_p1638_p3_balanced_env_design.py --plan --power
& 'D:\Anaconda\envs\pytorch\python.exe' tools\_p1613_p3_cloud_runner.py --job env-seeds --aggregate --strict
```

`--audit` 应报出 4 个 stack × 2 rank 全部 **4/4 共同种子**、**0 个单种子格子**；
`--plan` 的 `missing_cells` 应为空；`--power` 的
`designs.balanced_common_seed.stacks_with_all_common_seeds` 应为 4 个 stack，
`ci_width_change` 里两套区间都有值。

**云主机**：本轮不需要开实例；若日后需要，按
`docs/p3_cloud_round_notes.md` 第 2、4 节（`cloud_next/p3_env_seeds.sh`）走，
并遵守仓库的"云端主机收尾规则"（跑完 → 校验 → 取回产物 → 关机 → 验证端口）。