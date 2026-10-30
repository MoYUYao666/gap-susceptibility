# PR R1.3 / R2.4 / R3.3 — 参数匹配扰动实验：Visual Fragility 是否成立

**任务**：`task-2`（causal-hardener）· **日期**：2026-10-12 · **交付件**：本文 + `outputs/analysis/pr_relative_perturbation.json`（唯一数字来源）

**审稿人原话（Pattern Recognition，三位审稿人一致质疑"因果证据"）**：

> *"applying the same absolute noise to both encoders does not imply the same relative
> perturbation, because their weight scales, parameter distributions, layer architectures, and
> numbers of parameters may differ"*

要求：**① 层级归一化扰动（控制 ‖ΔW‖_F/‖W‖_F）② 多个噪声级 ③ 两塔匹配相对扰动预算 ④ 多种子**。

---

## 0. 结论速览（先给答案）

| 问题 | 答案 | 数字（mean ± sd） |
|---|---|---|
| **匹配相对扰动下，vision 塔是否仍更脆弱？** | **否（不可分辨）**。点估计反而偏向"text 塔更易受损"，但 sd 大于均值 | drop 比 `0.610 ± 2.283`（n=30；中位数 0.697；10/30 > 1）<br>同损伤相对预算比 `0.912 ± 0.452`(5%) / `0.989 ± 0.449`(10%) / `1.061 ± 0.435`(20%) |
| **"倍率是多少（带 sd）"** | 匹配相对口径：**≈1，不可分辨**（预算比 5–20% 损伤时 0.91–1.06，sd ≈0.44） | 见上 |
| **现论文"等绝对噪声"口径的倍率** | `1.293 ± 1.424`（drop 比）；同损伤 σ 比 `1.104 ± 0.110`(10%) / `1.455 ± 0.165`(20%) — 即 vision 需要多 10–46% 的 σ，**不是 2.6×** | 归档协议 `abs_std` |
| **"同一 σ"是否等于"同一相对扰动"？** | **不等**：塔级 V/T = **1.141**（等 σ·std 协议）/ **1.237**（真·等绝对 σ）；塔内逐张量相对扰动相差最多 **18×**（LayerNorm 权重 ≈0.098σ vs 注意力/MLP 权重 ≈1.00σ） | T2/T3 |
| **Visual Fragility 能否作为"因果证据"？** | **不能**。匹配相对预算后没有任何一个方案给出稳定、跨噪声级的"vision 更脆弱"排序；该结论必须保持为**与证据一致的假设**，不能写成因果 | — |

---

## 1. 这个实验到底测了什么

模型 `openai/clip-vit-base-patch32`（冻结，纯评测、无训练），同一批**固定 1000 张图 × 1000 条文本**
（`flickr30k/flickr30k.json` 第 400–1399 张图的 caption#0，图像张量只预处理一次并被所有条件逐字节复用，
**实验过程中没有任何随机数据增强**），测 R@1(i→t)、R@1(t→i)、R@5、R@10、CG、DG
（CG/DG 用仓库自身的 `src/gap_metrics.py::GapTracker`）。基线（`baseline`）：
R@1(i2t)=0.6950、R@1(t2i)=0.6710、CG=0.7742、DG=0.8308。

四种扰动协议，注入张量集合完全相同（192 个/塔，与归档脚本一致）：

| key | 每张量扰动 | 跨塔相对预算 |
|---|---|---|
| `rel_layer` | `‖ΔW_i‖_F = r·‖W_i‖_F`（方向各向同性） | **逐张量、逐 block、塔级全部恰好 = r**（脚本内断言 <1e-4，实测偏差 1.4e-8） |
| `rel_uniform` | `‖ΔW_i‖_F = r·‖W_inj‖_F/√n`（塔预算均摊） | 塔级 = r，但层级分配不同 |
| `abs_std` | **归档协议**：`ΔW_i = σ·std(W_i)·randn`，由 `paper/scripts/noise_sensitivity.py::inject_noise_to_encoder` **原样 import 执行** | 否（实测 V/T = 1.1408） |
| `abs_raw` | 字面"同一绝对噪声"：`ΔW_i = σ·randn`，两塔共用同一 σ | 否（实测 V/T = 1.2374） |

- 噪声级：`rel_layer` 7 级 `{0.01,0.03,0.06,0.1,0.2,0.3,1.0}`；`abs_std` 6 级 `{0.01,…,0.3}`；
  `abs_raw` 4 级 `σ = r·rms(W_vision,inj)`，`r ∈ {0.03,0.06,0.1,0.3}`；`rel_uniform` 4 级 `{0.01,…,0.05}`。
- 种子：**10 个** `[42,123,456,789,1024,2048,4096,8192,16384,32768]`（前 5 个与归档
  `outputs/noise_fixed_aug.json` 相同）。每个条件用 `torch.manual_seed(seed)` 在扰动抽样前重置，
  且所有协议对同一 seed 抽取**同一组张量方向**（只有缩放不同）⇒ 级间/协议间比较是按方向配对的。
- 控制条件：每个协议的 `level = 0` 必须**逐位复现 baseline**（脚本内断言，全部通过）。
- 权重每条件前后 bit-exact 还原（`torch.equal` 全量断言），无跨条件污染。
- 全部 426 条件、**0 失败**、GPU 单进程串行 20.5 min。
- **跨运行复现**：`tools/_p257_pr_causal_repro_check.py` 对 5-seed 版与 10-seed 版重叠的 **136 个条件**
  逐字段比较，`R@1`/`R@5`/`R@10`/`CG`/`DG`/`drop%`/`rel_injected` 的最大绝对差 **全部 0.000e+00**。

---

## 2. 结果 A：同一 σ ≠ 同一相对扰动（审稿人质疑的定量核心）

`weight_geometry.<tower>`（T1/T2 表全文见 `outputs/analysis/pr_relative_perturbation_tables.md`）：

| 量 | vision | text | V/T |
|---|---|---|---|
| 注入张量 | 192 | 192 | 1.000 |
| 注入参数 | 85,054,464 | 37,828,608 | **2.248** |
| 注入参数/该塔总参数 | 0.973 | 0.599 | — |
| `‖W_inj‖_F` | 333.043 | 274.830 | 1.212 |
| 注入权重 RMS | 0.03611 | 0.04468 | **0.808** |
| 等 σ·std 协议下塔级相对扰动/单位 σ | 0.48303 | 0.42366 | **1.1401** |

**逐张量期望相对扰动**（`by_kind[*].expected_rel_at_unit_sigma`，×σ 即得）：

| 张量类别 | vision | text |
|---|---|---|
| `layer_norm2.weight` | 0.0983 | 0.0757 |
| `layer_norm1.weight` | 0.1049 | 0.0766 |
| `fc1.bias` | 0.4910 | 0.4066 |
| `q/k/v/out_proj.weight`、`fc1/fc2.weight` | 1.0000 | 1.0000 |
| 各类 bias | 0.99–1.00 | 0.99–1.00 |

**这就是审稿人说的那件事，实测数字**：

1. **同一 σ 在塔内就不是同一相对扰动**：LayerNorm 权重只拿到 ≈0.10σ，注意力/MLP 权重拿到 ≈1.00σ — 相差 **≈10×**；
   逐张量实现的相对扰动在 vision 塔内从 0.018 到 0.318（σ=0.3 时）**跨 18×**。
2. **同一 σ 在两塔之间也不是同一相对扰动**：塔级 V/T = **1.1408**（等 σ·std）/ **1.2374**（等绝对 σ），
   且这一比值与 σ 无关（`rows[*].rel_injected` 在每个 σ 上都是 0.00483/0.00424 … 0.14495/0.12705）。
   即：**等绝对噪声实际上多给了 vision 塔 14%–24% 的相对扰动预算**。
3. **层级也不齐**：归档协议 σ=0.3 时，逐 block（12 个 block、按范数加权）相对扰动
   vision 0.0945–0.2161（max/min = 2.29），text 0.1076–0.1442（max/min = 1.34）。

> **顺带一个必须写进方法描述的更正**：归档注入器的注释写"跳过 LayerNorm/embedding"，
> 但判据是 `'layernorm' in name.lower()`，而 HF 的实际命名是 `layer_norm1.weight`（**带下划线**），
> 因此 **LayerNorm 参数实际被注入了**（`n_injected=192` = 12 层 × 16 张量，含每层 2 个 LN 权重 + 2 个 LN 偏置）；
> 另外噪声是 `σ·std(W_i)`（**逐张量尺度**），不是"各向同性/同一绝对 σ"。
> 本实验用 `archive_injector.function_verified_to_touch_exactly_the_expected_set = true`
> 逐张量核对了被改动的集合。**现稿"isotropic Gaussian noise in the encoder parameters"的描述与代码不符**，
> 建议改成"per-tensor scale-relative Gaussian noise on `encoder.layers` tensors (LayerNorm included)"。

---

## 3. 结果 B：匹配相对扰动下 R@1 的下降（主结果）

`analysis.per_level.rel_layer[*]`（10 seeds；T4/T7 含逐 seed 原值）：

| r（逐张量=逐 block=塔级相对扰动） | vision drop% | text drop% | 均值比 | 逐 seed 配对比 | 逐 seed V>T | V>50% | T>50% |
|---|---|---|---|---|---|---|---|
| 0.01 | 0.45 ± 0.68 | 0.45 ± 0.63 | 1.00 | 0.62 ± 2.03 | 4/10 | 0 | 0 |
| 0.03 | 1.14 ± 0.66 | 3.93 ± 7.56 | 0.29 | −0.93 ± 2.71 | 3/10 | 0 | 0 |
| 0.06 | 3.28 ± 1.36 | 13.60 ± 26.17 | 0.24 | 1.03 ± 1.14 | 3/10 | 0 | 1 |
| 0.10 | 14.73 ± 6.52 | 24.37 ± 30.95 | 0.60 | 1.73 ± 1.98 | 7/10 | 0 | 2 |
| 0.20 | 98.35 ± 1.83 | 55.34 ± 21.82 | **1.78** | 2.01 ± 0.70 | 10/10 | 10 | 5 |
| 0.30 | 99.78 ± 0.10 | 94.86 ± 2.69 | 1.05 | 1.05 ± 0.03 | 10/10 | 10 | 10 |
| 1.00 | 99.86 ± 0.12 | 99.76 ± 0.15 | 1.00 | 1.00 ± 0.00 | 7/10 | 10 | 10 |

读法（**关键**）：

- **在尚未饱和的区间（r ≤ 0.1）没有"vision 更脆弱"**：均值比 0.24–0.60，逐 seed 中位数 0.70（30 个配对里只有 10 个 > 1）。
  文本塔的均值被**重尾**拉高：r=0.1 时 10 个种子中 2 个崩到 69.5%/93.5%（R@1 掉到近随机），其余 8 个只有 4.5%–17.4%；
  vision 塔则很集中（8.4%–30.9%）。
- **唯一"vision 明显更差"的区间是 r=0.2**（98.35% vs 55.34%），但那时 vision 的 10 个种子**全部崩到
  93.4%–99.6%**（R@1 均值 0.0115，最低 0.0030 ≈ 随机水平），而文本塔有 8/10 个种子仍在 30.7%–64.2%。
  这反映的是**崩溃阈值/曲线陡度不同**，不是"任何噪声级下 vision 都更脆弱"。
- CG/DG 与 R@1 同向（T5）：r=0.1 时 text 塔把 CG 推到 0.878（vision 0.798，基线 0.774）、DG 推到 0.943（vision 0.850）。

**同损伤所需相对预算比（`analysis.headline.*.matched_drop_budget_ratio`，text/vision，>1 表示 vision 更脆弱）**：

| 协议 | @5% 下降 | @10% 下降 | @20% 下降 |
|---|---|---|---|
| `rel_layer`（匹配相对） | 0.912 ± 0.452 | 0.989 ± 0.449 | 1.061 ± 0.435 |
| `rel_uniform` | 0.686 ± 0.184 | 0.679 ± 0.137 | 0.761 ± 0.060 |
| `abs_std`（归档等 σ·std） | 0.955 ± 0.281 | 1.104 ± 0.110 | 1.455 ± 0.165 |
| `abs_raw`（等绝对 σ） | 1.013 ± 0.203 | 1.058 ± 0.192 | 1.176 ± 0.098 |

---

## 4. 结果 C：等绝对 vs 匹配相对——结论会不会翻转？会

同一份数据、同一批方向，只换协议（T5/T6/T8）：

| 口径 | vision/text 下降比 | 读作 |
|---|---|---|
| `rel_layer` r=0.1（相对预算完全匹配） | **0.60** | text 更受损 |
| `abs_raw` σ=0.003611（vision 塔级相对预算 = 0.10，与上一行同预算；但分配不同） | **2.47** | vision 更受损 |
| `abs_std` σ=0.3（归档协议，vision 塔级相对 0.1450 / text 0.1271） | **1.60** | vision 更受损 |
| 归档一次抽样的旧值（`outputs/noise_fixed_aug.json`，σ=0.1） | 0.77（p=0.77，非显著） | 无排序 |

**同一 seed 的配对比较（T8）**：把 vision 塔的**塔级**相对预算固定成 r，只换"这些预算怎么摊到 192 个张量上"：

| r（vision 塔级相对预算） | vision: `rel_layer` vs `abs_raw` | text 同 σ |
|---|---|---|
| 0.06 | 3.28 ± 1.36 vs 11.64 ± 2.21（配对差 −8.36 ± 1.81） | 13.60 ± 26.17 vs 10.53 ± 2.19 |
| 0.10 | 14.73 ± 6.52 vs 84.01 ± 2.73（配对差 −69.28 ± 7.07） | 24.37 ± 30.95 vs 34.03 ± 5.80 |

**结论**：`abs_raw` 下那个"vision 2.47× 更差"的观感，一半来自相对预算没配平（vision 多拿 1.237×），
一半来自分配方式；一旦按审稿人要求做**逐层归一化**，观感消失甚至反向。

原因在范数构成：**LayerNorm 参数占了 vision 塔注入集 Frobenius 范数的 73.89%**
（仅 LN 权重 71.98%；注意力/MLP 权重合计只有 15.83%），text 塔同口径更高（79.66% / 76.66%）。
`rel_layer` 要求这些 LN 权重也拿到 r=0.10 的相对扰动，而 `abs_raw`/`abs_std` 下它们几乎没被动。

---

## 5. 给 Lead 的可直接引用段落（英文，回应信/正文用）

> **Matched relative perturbation (R1.3 / R2.4 / R3.3).** We repeated the weight-perturbation probe
> with the relative budget controlled. For each transformer block and for the tower as a whole,
> the perturbation now satisfies ‖ΔW‖_F/‖W‖_F = r exactly in both encoders (verified to 1.4e-8),
> over seven levels r ∈ {0.01,…,1.0} and ten seeds, on a fixed 1000-pair Flickr30k slice with no
> stochastic augmentation. Under this control the vision tower is **not** the more fragile one:
> the per-seed ratio of R@1 degradation (vision/text) pooled over the non-saturated levels is
> **0.61 ± 2.28** (median 0.70; 10/30 above 1), and the relative budget each tower needs for the
> same degradation is **0.91 ± 0.45**, **0.99 ± 0.45** and **1.06 ± 0.44** at 5%, 10% and 20% R@1
> loss — i.e. indistinguishable from parity. The single regime in which the vision tower is clearly
> worse (r = 0.2, 98.4% against 55.3%) is the regime in which it has already collapsed to chance
> in all ten seeds, so it reflects a steeper collapse curve rather than a level-independent
> fragility ordering. We also confirm the reviewer's premise quantitatively: at the same σ the
> archived protocol delivers a **1.141× larger** tower-level relative perturbation to the vision
> encoder (0.483σ against 0.424σ), and within a tower the per-tensor relative perturbation spans
> ~18× because the code scales the noise by each tensor's own standard deviation
> (LayerNorm parameters, which carry 73.9% of the injected Frobenius norm in the vision tower,
> receive only ≈0.10σ while attention/MLP matrices receive ≈1.00σ). The same
> σ therefore does not mean the same relative perturbation, and the resulting ordering is
> protocol-dependent: the identical comparison gives 0.60 under matched relative budgets and 2.47
> under equal absolute noise (where the vision tower also receives 1.237× the relative budget).
> **We therefore do not present the noise probe as causal evidence for Visual Fragility.** The
> interpretation remains a hypothesis about where the adapters are placed, supported by the
> strict-freezing control rather than by perturbation sensitivity.

---

## 6. 每个数字的溯源

| 文档中的数字 | 归档文件 | 字段 |
|---|---|---|
| 基线 R@1/CG/DG | `outputs/analysis/pr_relative_perturbation.json` | `baseline.*` |
| 参数量、范数、RMS、单位 σ 相对扰动 | 同上 | `weight_geometry.<tower>.{n_injected_params,n_total_params,frob_injected,rms_injected,expected_rel_at_unit_sigma_injected}` |
| 逐类别相对扰动（0.0983σ vs 1.0000σ 等） | 同上 | `weight_geometry.<tower>.by_kind[*].expected_rel_at_unit_sigma` |
| 逐 block 相对扰动（0.0945–0.2161 等） | 同上 | `rows[*].rel_realized_by_block`（`protocol=abs_std, level=0.3`） |
| LayerNorm 参数占注入范数 73.89% / 79.66% | 同上 → 渲染表 | `weight_geometry.<tower>.by_kind[*].frob`；渲染见 `pr_relative_perturbation_tables.md` T2 末表 |
| r=0.2 时 vision R@1 均值 0.0115（0.0030–0.0460） | 同上 | `rows[*].R1.R@1_i2t`（`protocol=rel_layer, tower=vision, level=0.2`） |
| 各协议实际相对预算（1.1408 / 1.2374） | 同上 | `rows[*].rel_injected`（均值），表见 `pr_relative_perturbation_tables.md` T3 |
| 各 r 下 drop%、配对比、种子计数 | 同上 | `analysis.per_level.rel_layer[*].{vision_drop_i2t,text_drop_i2t,ratio_of_means,paired_ratio_mean,paired_ratio_sd,n_seeds_vision_gt_text,n_seeds_*_drop_gt_50pct}` |
| 池化 drop 比 0.610 ± 2.283（n=30，中位数 0.697） | 同上 | `analysis.headline.rel_layer.matched_relative_fragility.levels_nonsaturated` |
| 同损伤预算比 0.912/0.989/1.061 ± 0.44 | 同上 | `analysis.headline.rel_layer.matched_drop_budget_ratio.drop_{5,10,20}_pct` |
| abs_std 1.293 ± 1.424、预算 1.104/1.455 | 同上 | `analysis.headline.abs_std.*` |
| abs_raw 1.507 ± 0.958、1.2374、2.47 | 同上 | `analysis.headline.abs_raw.*`、`analysis.per_level.abs_raw['0.0036112000248814027']` |
| T8 配对差 −69.28 ± 7.07 | 同上 | `rows`（`protocol ∈ {rel_layer, abs_raw}`，同 seed 配对），表见 T8 |
| 136 个条件逐位复现 | `outputs/analysis/pr_relative_perturbation_repro_check.json` | `max_abs_diff_per_field.*`、`verdict` |
| 归档协议 1.90 ± 1.83 vs 2.48 ± 3.25（σ=0.1，旧口径） | `outputs/noise_fixed_aug.json` | `paired['0.1000']` |
| 注入器实际行为（192 张量、含 LayerNorm、σ·std 缩放） | `outputs/analysis/pr_relative_perturbation.json` | `meta.archive_injector.*` |

**产生脚本**：`tools/_p255_relative_perturbation.py`（sha1 见 `meta.script_sha1`）→
`tools/_p256_pr_causal_tables.py`（渲染表）→ `tools/_p257_pr_causal_repro_check.py`（复现核对）。

**本次新建文件**：
- `tools/_p255_relative_perturbation.py` — 主实验（含 `--apply/--resume/--pilot`）
- `tools/_p256_pr_causal_tables.py` — 表渲染（数字不手抄）
- `tools/_p257_pr_causal_repro_check.py` — 跨运行逐位复现核对
- `outputs/analysis/pr_relative_perturbation.json` — **主结果（426 条件 / 0 失败 / status=complete）**
- `outputs/analysis/pr_relative_perturbation_tables.md` — T1–T8 表格（本文引用其数字）
- `outputs/analysis/pr_relative_perturbation_verdict.json` — 机器可读结论块（含逐 seed 原值）
- `outputs/analysis/pr_relative_perturbation_repro_check.json` — 复现核对结果
- `outputs/analysis/_p255_run1_5seed_superseded.json` — 5-seed 中间版（**已被 10-seed 取代**，仅用于复现核对）
- `outputs/analysis/_smoketest_pr_relative_perturbation.json` — 256 图冒烟测试（非结论来源）

**复现命令**（单进程串行，约 21 分钟，GPU 峰值 <2 GB）：
```powershell
$env:PYTHONIOENCODING='utf-8'; $env:PYTHONUTF8='1'
python tools\_p255_relative_perturbation.py --apply          # 崩溃后加 --resume 续跑
python tools\_p256_pr_causal_tables.py --apply
python tools\_p257_pr_causal_repro_check.py
```

---

## 7. 限制（必须与结论一起写）

1. **单模型、单数据集切片**（CLIP ViT-B/32，1000 对 Flickr30K 固定切片）。结论是"在本协议下无法支持
   vision 更脆弱"，不是"所有 VLM 上都对称"。
2. **文本塔的响应是重尾的**：10 个方向里有 2 个让文本塔崩到近随机，其余 8 个几乎无损。因此
   均值比与中位数比会给出不同印象（0.604 vs 中位数 0.697；池化 0.610 vs 0.697）。本文两个都给。
3. **`rel_layer` 的匹配包含 LayerNorm 权重**，而它们占 vision 注入集 Frobenius 范数约 75%。
   这是"逐张量相对"定义的直接后果，也是 T8 里两种协议差 69 个百分点的原因；
   若把 LayerNorm 排除在注入集外，结论是否变化**本实验未测**（属未验证，不猜）。
4. **注入张量集合沿用归档脚本**（含 LayerNorm，因命名判据失效），因此两塔被注入的**参数占比不同**
   （vision 97.3% vs text 59.9%；Frobenius 口径 99.15% vs 97.09%），这是审稿人说的
   "numbers of parameters may differ"的直接体现，无法靠归一化消除。
5. 一次 CUDA 驱动瞬时故障（`cublasLtMatmul EXECUTION_FAILED` → `cudaErrorUnknown`）中断了第一遍扩展运行；
   脚本已加 `--resume`，续跑后 0 失败，且与 5-seed 版重叠的 136 个条件逐位一致 ⇒ 该故障未影响数据。
