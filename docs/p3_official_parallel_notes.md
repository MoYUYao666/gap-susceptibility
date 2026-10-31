# P3 official-IGU 并行化核查笔记（2026-10-25）

> 本文件是"能否并行"这一问题的**可复核留痕**：命令、实测数字、判定依据。
> 硬结论一句话：**本阶段不并行（并发度 = 1），真正的阻塞不是 GPU 排队，而是 `_p1639` 训练阶段的产物自删 bug。**
> 并行化的技术前提（脚本能否选臂、命名会不会撞、显存够几路）我全部验证过，结论与依据见第 2–5 节。

## English summary (measured facts)

| item | value | source |
|---|---|---|
| arm wall clock (whole `_p1639` process, one arm) | **55 s** (training itself **36 s**) | `logs/p3_official_igu_train_s42.log` |
| peak VRAM, one 4-bit 7B LoRA arm | **12 923 MiB**, 1 compute app | `logs/par_arms_watch.log` (mine) **and** `logs/gpu_mem_smoke.csv` (owner's) |
| baseline VRAM when idle | 0 MiB (4 773 MiB while the POPE eval held the card) | `nvidia-smi` |
| max safe concurrency on this 32 GB card | **2** (2 × 12.9 GiB ≈ 25.8 GiB ≈ 79 %); 3 ≈ 38.7 GiB ⇒ impossible | derived from the measurement above |
| real arms still to train | **5** (`reimpl_igu_style` seed 42 is served from the archived anchor) | `_p1639.predict_side_effects` + `outputs/analysis/p3_official_igu_run.json` |
| serial cost of the whole train stage | **≈ 5 min** (documented estimate was 25 min/arm, 2.5–3.5 GPU h ⇒ high by ~30×) | measured |
| naming collision axis | only `verify_r1_s<seed>_b1_partial.json` (seed-only); per-config tags never collide | source, §2 |
| run-archive write model | read at start, **whole-file rewrite at the end** ⇒ concurrent batches silently lose records | source, §5 |
| decision | **concurrency = 1 (serial)**; 2-way was actually attempted by the owner (`--workers 2`) and died with CUDA OOM (3 arms in flight, 3 × 12.61 GiB > 31.47 GiB usable) | §4.1, §9 |

## 1. 时间线（UTC = 本机 −8；全部来自实例日志/`ps`，可逐条复核）

| UTC | 本机 | 事件 | 证据 |
|---|---|---|---|
| 02:08:53 | 10:08 | 首次勘查：只有对方 agent 的 `_p1640 --eval --rank 6`（PID 5365，09:55 起），GPU 4 773 MiB；**无 `_p1639`** | `ps`、`nvidia-smi` |
| 02:09:12 | 10:09 | 对方写 `logs/jobB_archive_snapshot_pre_jobB.txt`（`_p1639` 五个锚定归档的 sha256 快照）⇒ JOB B 已上膛 | 文件时间戳 |
| 02:12:38 | 10:12 | JOB A 链完成：aggregate `exit=0`、`strict acceptance: satisfied`；`outputs/analysis/p3_second_downstream.json` 落盘（10:12:37） | `logs/p3_second_downstream_eval.log` |
| 02:14:57 | 10:14 | 对方启动 JOB B：PID 6941 `_p1639 --run-official --stage train --seeds 42` | `ps`、我的 `logs/par_arms_watch.log` |
| 02:15:52 | 10:15 | **该进程崩溃**：`RuntimeError: no usable archive at .../verify_r1_s42_bcexplicit_v11_s1_m2_d2.json after training`；日志自证 `removed the transient training by-product ...v11_s1_m2_d2.json` | `logs/p3_official_igu_train_s42.log` |
| 02:16:01 | 10:16 | 我的守望记录：臂进程消失，GPU 回 0 MiB；**单臂峰值 12 923 MiB / 1 个 compute app** | `logs/par_arms_watch.log` |
| 02:17:52–02:18:45 | 10:17–10:18 | 对方自测冒烟：直跑 `run_training.py`（绕开 `_p1639` 的 restore），峰值同为 12 923 MiB；外层被 `timeout` SIGTERM（`exit=143`），python 仍跑完 3 epoch 并存档（ΔE=+181.0） | `logs/p3_official_igu_train_smoke.log`、`gpu_mem_smoke.csv` |
| 02:18:15 | 10:18 | **对方自行修复** `tools/_p1639_p3_official_igu.py`（+70/−3）：新增 `restore_side_effects()`，只回滚 `expected[1:]`，永不碰 `target` | 本地 `git diff`、`LastWriteTime` |
| 02:19:41 | 10:19 | 修复版上传实例（84 670 B，sha256 `2d2d7057…`）；02:19:43 跑 `--self-test` | `ls`/`sha256sum`、`logs/selftest_postpatch.log` |
| 02:19:51 | 10:19 | 修复后**重跑臂**：PID 8725 `--stage train --config official_corrected_map --seeds 42`（PID 8790 训练中） | `ps` |
| 02:20:12 | 10:20 | 我复查：smoke 残留归档已被 owner 清理（不存在），`p3_official_igu_run.json` `runs=0` | `ls`、`json.load` |
| 02:19:51–02:21 | 10:19–10:21 | 修复后的臂跑完并**入档**：`official_corrected_map / seed 42 / delta_E=182.5 / from_cache=False`（E 轨迹 3926.0→3831.0→3844.5→4108.5） | `logs/smoke_fixed_s42.log`、`p3_official_igu_run.json` |
| 02:22:21 | 10:22 | 我复查：**无臂进程、GPU 0 MiB**、run archive `runs = 1`（6 个里第 1 个）；owner 仍按种子逐批推进 | `ps`、`nvidia-smi`、`json.load` |
| 02:25:16–02:27:03 | 10:25–10:27 | **并行实测尝试失败**：owner 的 `cloud_next/_p1639_parallel_variant.py` 以 `[train --workers 2]` 启动，exit=1；两个臂 `torch.OutOfMemoryError`（`31.47 GiB 容量只剩 49.94/67.94 MiB`，另有进程各持 12.61 GiB）；唯一跑完的臂 Training time **54 s**、ΔE=+262.0 | `logs/p3_official_igu_train_parallel.log`、`logs/p3_official_igu_arms/*.log` |
| 02:27:12 | 10:27 | owner 串行 consolidation 补齐缺的臂（`Training time: 53s`，ΔE=+186.0） | `logs/consolidate_six_final.log` |
| 02:27:36 | 10:27 | **run archive 收齐 6/6 条记录**（我逐条抄录，见 §4.1） | `p3_official_igu_run.json` |
| 02:27:48– | 10:27– | owner 启动 `--stage train --force` **复现轮**（`replicates.log`：`replicate pass 1/2 (--force, retrains all six)`）⇒ 臂值将再次变化；锚点覆盖风险见 §6.3 | `logs/replicates.log`、`ps` |

## 2. 命名冲突检查（新规则"第一步第 4 条"要求）

`tools/_p1639_p3_official_igu.py::predict_side_effects()`（第 820–830 行）给出一个臂写的两个文件：

1. 主归档 `paper3/scripts/outputs/experiments/verify_r1_s<seed>_bcexplicit_v<V>_s<S>_m<M>_d<D>.json`
   —— tag 由**分配**决定，与 `paper3/scripts/run_training.py:466-468` 的落盘逻辑逐字一致（已核）。
2. by-product `paper3/scripts/outputs/experiments/verify_r1_s<seed>_b1_partial.json`
   —— **只带 seed，不带分配**。

三个配方的 tag 互不相同，因此**不同配置永不重名**：

| config | allocation (v/s/m/d) | 主归档 tag |
|---|---|---|
| `official_archived_map` | 12/1/2/1 | `v12_s1_m2_d1` |
| `official_corrected_map` | 11/1/2/2 | `v11_s1_m2_d2` |
| `reimpl_igu_style` | 11/1/3/1 | `v11_s1_m3_d1` |

⇒ **唯一会撞的是 `_b1_partial.json`：并发集合内种子必须两两不同。**
⇒ 唯一安全的拆分轴是 **seed**（对方当前分批方式 `--seeds 42` / `123` / `789` 正是这个轴）。

## 3. 显存实测（新规则"第二步"要求的口径）

- **两次独立测量一致：12 923 MiB / 臂**（我的只读守望采样；对方的 `gpu_mem_smoke.csv`）。
- 曲线（owner 的 CSV）：空闲 0 → 加载模型 4 097 → 训练平台 12 897–12 923 MiB；训练期 GPU 利用率 **79–100 %**。
  ⇒ 操作者看到的"7 %"是**空闲时刻**的读数；真训起来这张卡是打满的（利用率层面），"单卡只用了 7 %"不能推出"还能塞 10 路"。
- 判据（32 GB × 85 % ≈ 27–28 GB）：**并发度上限 = 2**（25.8 GiB）；3 路 ≈ 38.7 GiB **超限**。

## 4. 并行 vs 串行实测耗时

- 单臂串行实测：`_p1639` 进程 02:14:57 → 02:15:52 = **55 s**；`run_training.py` 自报 `Training time: 36s`。
- 需要真跑的臂 = **5 个**（`reimpl_igu_style` seed 42 命中已归档锚点 `verify_r1_s42_bcexplicit_v11_s1_m3_d1.json`，走 `from_cache`，秒级）。
- ⇒ 串行 ≈ **5 分钟**；2 路并行理论 ≈ **3 分钟**（省 ~2 分钟）。
- ⇒ 与 `docs/V25_READINESS_2026-10-24.md` 里"6 arms / 2.5–3.5 GPU 小时 / ~25 min per arm"相比，**高估约 30 倍**；该行数字应以下载后的实测为准（建议更新该文档，勿据此排整轮时间预算）。

### 4.1 并行"实测尝试"的结果（这是本题最有价值的一条：不用再猜了）

owner 自己写了并行变体并在实例上真跑了一次（我只读记录，未参与）：

| 观测 | 数值 | 来源 |
|---|---|---|
| 并行驱动 | `[train --workers 2]`，02:25:16 启动 → 02:27:03 **exit=1** | `logs/p3_official_igu_train_parallel.log` |
| 死因 | `torch.OutOfMemoryError: CUDA out of memory. Tried to allocate 86.00 MiB. GPU 0 has a total capacity of 31.47 GiB of which 49.94 MiB is free.` | `logs/p3_official_igu_arms/arm_official_corrected_map_seed789.log` |
| 同一批第二个 OOM | `... of which 67.94 MiB is free. Process 10572 has 12.61 GiB ... Process 11084 ha[s] ...` | `arm_reimpl_igu_style_seed123.log` |
| 同时在飞的臂进程数 | 02:24:35 = **2** 个 → 02:26:05 = **3** 个（我的轮询） | `logs/par_arms_watch.log` 同期轮询输出 |
| 唯一跑完的臂 | Training time **54 s**（串行基线 36 s ⇒ 1.5× 慢），ΔE=+262.0 | `arm_reimpl_igu_style_seed789.log` |
| 并行收益 vs 代价 | 2 臂 54 s vs 串行 2 臂 72 s ⇒ 理论 ~1.3× 吞吐；实际代价 = **整批 exit=1** | 同上 |

⇒ **结论（有实测依据）**：本卡安全并发度 = **2**、**3 路必炸**（3 × 12.61 GiB ≈ 37.8 GiB > 31.47 GiB 可用）；
而且"workers=2"这种**按 worker 数限流**的写法守不住显存——只要投放节奏让第 3 个臂起来就 OOM
（要么加"上一个臂退出再放下一个"的闸门，要么直接串行）。按新规则第三步第 2 条，
**显存超限 + 进程异常退出 ⇒ 回退串行**，这正是最终采用的口径。

### 4.2 run archive 6/6 快照（02:27:36Z，只读抄录；owner 的 `--force` 复现轮会让它再变）

| config | seed | delta_E | from_cache | E |
|---|---|---|---|---|
| official_corrected_map | 42 | 182.5 | False | [3926.0, 3831.0, 3844.5, 4108.5] |
| official_corrected_map | 123 | 178.0 | False | [3926.0, 3835.5, 3783.0, 4104.0] |
| official_corrected_map | 789 | 242.0 | False | [3926.0, 3831.0, 3869.5, 4168.0] |
| reimpl_igu_style | 42 | 333.0 | True | [3921.0, 3814.5, 3904.5, 4254.0] |
| reimpl_igu_style | 123 | 186.0 | False | [3926.0, 3813.5, 3776.5, 4112.0] |
| reimpl_igu_style | 789 | 262.0 | True | [3926.0, 3827.0, 3824.0, 4188.0] |

配对差（official − reimpl）：seed 42 = **−150.5**、seed 123 = **−8.0**、seed 789 = **−20.0**
⇒ 三个种子的差离散极大（与 §6.1 的同臂运行间摆幅同源）；另有两点值得 owner 留意：
① `from_cache=True` 的两条来自旧归档，其 **E(0)=3921.0**，而本轮新训的臂 **E(0)=3926.0** ⇒ 归档里混了**两种环境**的臂；
② `delta_E = E(3) − E(0)`，E(0) 差 5 会直接进入 ΔE，配对差因此含环境漂移成分。**这不是我能改的判定规则**，只作事实摆出。

## 5. 为什么不并行：两条硬 blocker

1. **`p3_official_igu_run.json` 后写覆盖**：`stage_train()`（第 901、957–985 行）**开头读**归档、**结尾整份重写** `runs`。
   两个并发 `--stage train` ⇒ 后结束者的 `runs` 只含自己那批记录，另一批**静默丢失**（`--compare` 会缺种子）。
   若一定要并行，必须**所有批次结束后**再串行补一次
   `--stage train --config official_corrected_map,reimpl_igu_style --seeds 42,123,789`
   （全部命中磁盘归档 ⇒ `from_cache`、秒级、不重训），让它成为 run archive 的**最后写者**。
2. **与另一会话并存 = 重复作业 + 互删**（新规则第三步第 3 条明令禁止）：
   对方 02:14:57 起就在跑 `--run-official`，且 JOB B 的 train 阶段**不知道**我这边未归档的臂 ⇒ 会重训同名臂；
   `run_one_arm()` 的 `restore_owned()` 会删掉"非本进程写入"的文件 ⇒ 双方都可能 `read_arm()` 取空而崩。
   ⇒ 我按硬规则停手（未启动任何训练）。

## 6. 观测到的两个科学侧疑点（**只报不动**；判定规则与 pin 的 sha256 一律没碰）

### 6.1 同一臂两次运行 ΔE 不一致（运行间非确定性）

`official_corrected_map` / seed 42，两次运行、同一 argv（rank 1、vision 11、shallow 1、mid 2、deep 2、seed 42、epochs 3、num-samples 20、lora-alpha 16、同一 parquet）：

| run | 日志 | E 轨迹 | ΔE | 训练时间 |
|---|---|---|---|---|
| A（经**未修复**的 `_p1639`） | `logs/p3_official_igu_train_s42.log` | 3926.0 → 3829.0 → 3825.0 → 4176.5 | **+250.5** | 36 s |
| B（直跑 `run_training.py` 冒烟） | `logs/p3_official_igu_train_smoke.log` | 3926.0 → 3832.5 → 3849.0 → 4107.0 | **+181.0** | 35 s |
| C（**修复后**的 `_p1639`，即正式臂） | `logs/smoke_fixed_s42.log` | 3926.0 → 3831.0 → 3844.5 → 4108.5 | **+182.5** | （见日志） |

- 两次 **E(0) 完全相同（3926.0）**、第 1 epoch 的 step loss 到小数点后 4 位相同（11.5921 / 11.6717 / 8.8691 / 10.9111 / 11.2304），
  但 E(1..3) 不同 ⇒ 差异来自**训练本身**而非评测数据：`run_training.py:75` 只设 `torch.manual_seed`，
  未设 `torch.use_deterministic_algorithms(True)` / `cudnn.deterministic`，4-bit（bitsandbytes）反量化 matmul 与 cuBLAS 归约本身非确定。
- **三次运行的 ΔE = 181.0 / 182.5 / 250.5（极差 69.5）**：B 与 C 差 1.5，A 是离群点（高 68）。
  即同一臂的 ΔE 可复现性 ≈ ±35（以中位数 182.5 计），最坏差 69.5。
- 量级对照：ΔE 运行间极差 ≈ **70**；预声明等价 margin = **196.05**（5 % × 3921）；归档 official−reimpl 差 = **92.5**（333.0 − 240.5）。
  ⇒ 摆幅与"要判的差"同量级。**我没有改任何判定规则**（rule 6），但建议 owner 在报告里给出这一摆幅，或对关键臂做重复运行。
- 进入正式归档的是 Run C：`outputs/analysis/p3_official_igu_run.json` 记 `official_corrected_map / seed 42 / delta_E = 182.5 / from_cache = False`（02:21 前后写入）。
- ⚠️ 诚实 caveat：Run B 的外层被 smoke 的 `timeout` 发过 SIGTERM（日志 `exit=143`），但 python 仍完成 3 epoch 并写出完整归档；
  A/C 无此情况，而 B(181.0) 与 C(182.5) 彼此吻合 ⇒ 该 caveat 不影响"运行间存在摆幅"的结论（离群的是 A，不是 B）。

### 6.2 smoke 残留会被当成真臂（owner 已正确处理）

`run_one_arm()` 第 864–874 行：只要磁盘上存在满足协议的归档就**直接 `from_cache` 复用**（含 `ok/epochs/num_samples/lora_alpha/delta_E` 校验）。
10:18:45 曾落盘 `verify_r1_s42_bcexplicit_v11_s1_m2_d2.json`（897 B，ΔE=+181.0，来自被 SIGTERM 的冒烟进程）；
**10:20:12 我复查时已被 owner 清理**（不存在）⇒ 处理正确；否则冒烟数字会被当作正式臂。
（本笔记只记录该风险与处置，不评价 owner 的其它决定。）

### 6.3 owner 的 `--force` 复现轮会覆盖 pin 住的锚点（副作用，**可恢复**；只报不动）

- 事实：02:27:48 起 owner 跑 `_p1639 --run-official --stage train --force`（**无 `--config`/`--seeds`** ⇒ 默认 6 个臂），
  `logs/replicates.log` 自述 `replicate pass 1/2 (--force, retrains all six)` ⇒ 目的是测重复性（方向正确，与 §6.1 同源）。
- 但修复后的语义变了：`restore_side_effects()` 只回滚 `expected[1:]` ⇒ **已存在的 target 归档不再被保全**
  （修复前 `restore_owned` 会把预存 target 恢复成原字节，`archive_preserved` 字段就是为这个"保全"语义准备的）。
  因此当强制轮走到 `reimpl_igu_style / seed 42`（默认顺序第 5 个）时，
  **S27 锚点 `verify_r1_s42_bcexplicit_v11_s1_m3_d1.json`（ΔE=333.0）会被新值覆盖**；
  `official_archived_map` 不在默认 configs 内，所以 S39 锚点 `verify_r1_s42_bcexplicit_v12_s1_m2_d1.json`（ΔE=240.5）暂时不受影响。
- 后果：① `verify_inputs()` 断言这两个文件的 delta_E = 240.5 / 333.0（日志逐行可见 "the published number this
  comparison is anchored to"）⇒ 覆盖后**后续 `--run-official` 会 refuse to run**；
  ② `logs/jobB_archive_snapshot_pre_jobB.txt` 是 **sha256 快照、不是内容备份**，届时会显示漂移，
  需在轮次文档里注明"漂移 = 复现轮的**有意**重训"，否则会被读成归档污染。
- 可恢复性（我核过本机与实例快照）：原始字节仍完整存在，sha256 逐位一致 ——
  `v11_s1_m3_d1` = `212e9c75e7fcad2e…`（937 B）、`v12_s1_m2_d1` = `a060e2a880a638cb…`（946 B）
  ⇒ 需要时从本机重传即可复原（或让 owner 依快照回滚）。
- 建议（留给 owner 决定，我不越权）：复现轮结束后按上面的 sha256 复原锚点，或把复现值另存为不同文件名
  并声明"锚点仍以归档值为准"。

### 6.4 owner 的重复性复现轮：摆幅实测 + §6.3 的风险"确实发生、并被自家安全网修好"

- owner 先跑了一轮自建复现（`logs/replicates.log` 当时内容，我逐字抄录）：
  `pass delta_E: {official_corrected_map|123: 155.0, official_corrected_map|42: 186.0, official_corrected_map|789: 220.0, reimpl_igu_style|123: 88.5, reimpl_igu_style|42: 265.5, reimpl_igu_style|789: <截断>}`
  与首轮（§4.2）对比，**同环境重跑的同臂差**：

  | 臂 | 首轮 | 复现轮 | 差 |
  |---|---|---|---|
  | official_corrected_map 42 | 182.5 | 186.0 | +3.5 |
  | official_corrected_map 123 | 178.0 | 155.0 | −23.0 |
  | official_corrected_map 789 | 242.0 | 220.0 | −22.0 |
  | reimpl_igu_style 123 | 186.0 | 88.5 | **−97.5** |
  | reimpl_igu_style 42 | 333.0（旧环境归档，E0=3921.0） | 265.5 | −67.5（含环境漂移） |

  ⇒ 同协议重跑的 ΔE 摆幅：典型 **±25**、最坏 **~100**；配对差因此**会翻号** —— seed 123 的
  official−reimpl 差首轮 −8.0，复现轮变 **+66.5**。
- **§6.3 的风险确实发生了**（不是我猜的）：复现轮把 `reimpl_igu_style / seed 42`（S27 锚点）`--force` 覆盖成 **+265.5**，
  于是紧接着的下一轮 `verify_inputs()` 断言失败并拒绝运行：
  `archived reimplementation arm delta_E +265.5 FAIL the published number this comparison is anchored to`
  → `refusing to run: fix the inputs above first` → `replicate pass failed: exit 2`。
- 但 owner 的驱动脚本自带 `== restored primary archives ==`（`arm sha256 restored: all identical`）⇒ **已自动复原**；
  我 02:34 复核：两个锚点 sha256 与 pre-jobB 快照**逐位一致**（`212e9c75…` / `a060e2a8…`），run archive 也回到 `8f4546ed…`。
  ⇒ 事故是**瞬态且已闭环**（这也说明那两个 pin 的断言正是绊线，值得写进轮次文档）。
- owner 随后把它升级为专用工具 `tools/_p1646_p3_arm_replicates.py --passes 2 --apply`（02:34:31 起运行，自带 snapshot 与
  `anchors re-restored after` 语义）⇒ "重复性"这件事**已由 owner 接管并有正式工具**，我不再介入。
- 我另做的防患（不侵入 owner 流程）：`cloud_retrieved/par_arms_backup/anchors/` 存了锚点的**原始字节**
  （sha256 `212e9c75…` / `a060e2a8…`，与实例 pre-jobB 快照一致），即使实例与本机都被扰动也可复原。

## 7. 我做了什么 / 没做什么（可复核）

- 做：只读守望 `cloud_next/par_arms/_watch_launch.sh` → 实例 `logs/par_arms_watch.log`
  （记录 `--run-official` 启动时刻、显存峰值；模式串刻意不含 `_p1639`/`_p1640` 字样，避免在别人的 `ps | grep` 里造成假阳性）。
- 做：`cloud_next/par_arms/make_restore_fix_patch.py` —— 生成最小补丁的脚本（含断言）。
  **它主动拒发**：owner 先修了，原语句已不在 ⇒ exit 3、不产出过期补丁。这正是我想要的失败模式。
- 没做：未启动任何训练/臂进程；未修改 `tools/**`（`tools/` 不在我的写范围，且该脚本是对方交付件）；
  未写 `outputs/analysis/**`（除官方 runner 自己写的）；未碰 `--compare`、未碰 `publish_clean/`、未碰稿件。

## 8. 复现命令（逐条可重跑）

```bash
# 现场（实例，注意非交互 ssh 的 PATH 为空）
export PATH=/root/miniconda3/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
cd /root/autodl-tmp/p3work
ps aux | grep -E "_p1639|_p1640" | grep -v grep          # 有没有别的会话在跑同一作业
nvidia-smi --query-compute-apps=pid,used_memory --format=csv,noheader   # 单进程显存
ls -la --time-style=+%H:%M:%S outputs/analysis/ | tail   # p3_official_igu_run.json 的 runs
python -c "import json;d=json.load(open('outputs/analysis/p3_official_igu_run.json'));print(len(d['runs']))"
bash cloud_next/par_arms/_watch_launch.sh 30 60 15       # 只读守望（记录启动时刻 + 显存峰值）
```
```powershell
# 本机（凭据只走环境变量）
$env:CLOUD_PW='<password>'
python tools/_p1615_cloud_exec.py --host connect.westb.seetacloud.com --port 10137 --cmd '<remote command>'
python cloud_next\par_arms\make_restore_fix_patch.py --check   # 断言原语句仍在（否则说明已被修）
```

## 9. 并发度结论行（新规则第三步第 5 条要求）

**并发度 = 1（串行）。** 依据：
① 峰值显存 **12 923 MiB/臂**（两次独立实测）⇒ 32 GB 卡上限 **2**，3 路超限；
② 单臂墙钟 **55 s** ⇒ 全阶段串行 ≈ **5 min**，2 路并行仅省 ~2 min，收益小于风险；
③ 命名冲突检查：并发集合内**种子必须互斥**（`verify_r1_s<seed>_b1_partial.json` 是唯一重名点），
   且 `p3_official_igu_run.json` 是"结尾整份重写"⇒ 并发会造成 `runs` 记录静默丢失。
④ **实测反证**（不是推断）：owner 的 `--workers 2` 并行批因为 **3 个臂进程同时在飞**而 CUDA OOM、整批 `exit=1`；
   唯一跑完的并行臂 54 s vs 串行 36 s ⇒ 并行在本卡上**收益小且守不住**（详见 §4.1）。
**并行 vs 串行实测耗时**：串行 **36 s 训练/臂**（整进程 55 s）；并行**已由 owner 实测尝试**（`--workers 2`）
⇒ 2 个臂 `CUDA out of memory`、整批 `exit=1`，唯一跑完的臂 **54 s**（1.5× 慢）
⇒ 按降级条款回退串行（依据：`logs/p3_official_igu_arms/*.log` 的 OOM 堆栈）。

若**今后**真的需要并行（例如换成更重的下游评测），安全配方是：
2 个 detached 进程、**种子互斥**、每进程内配置串行，跑完后串行补一次 consolidation
（`--stage train --config official_corrected_map,reimpl_igu_style --seeds 42,123,789`，from_cache）作为 run archive 的最后写者；
启动前必须 `ps aux` 确认没有别的会话在跑同一作业（本次的 blocker 2 就是这个）。