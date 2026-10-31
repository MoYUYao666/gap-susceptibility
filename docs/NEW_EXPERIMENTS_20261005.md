# 补充实验报告：理论根基与机制的**直接**验证

> 日期：**2026-10-05** ｜ 依据：`tools/_exp1_gradflow_identity.py`、
> `tools/_exp2b_mechanism_gradient_interference.py`、`tools/_exp2c_encoder_side_gradients.py`
> 产物：`outputs/theory/gradflow_identity/`、`outputs/theory/grad_interference/`、
> `outputs/theory/encoder_side/`、`outputs/theory/gap_direction/`

## 为什么做这两项

论文的两大支柱此前都是**间接**验证：

| 支柱 | 此前的验证 | 缺口 |
|---|---|---|
| ODE 从**梯度流恒等式**推出 | 轨迹拟合 $R^2 = 0.986$ | **拟合好 ≠ 推导对** |
| "视觉侧干预有害" | 框架**预测** | **机制从未直接测量** |

## 实验一：梯度流恒等式**直接**验证 ✅

$$\Delta DG^* \;\overset{?}{=}\; -\eta\,\langle \nabla_\theta DG^*,\ \nabla_\theta \mathcal{L}\rangle$$

**做法**：同一次构造下取两套梯度，再做**一个真实 SGD 步**，比较预测与实测。
（关键：$DG^*$ 在**含 L2 归一化的计算图内**求导，不 detach。）

| 位置 | seed | 预测 | 实测 | 比值 |
|---|---|---|---|---|
| text_only | 42 / 123 / 456 | −1.98e−4 / −8.55e−4 / −2.85e−4 | −1.87e−4 / −8.64e−4 / −2.53e−4 | 0.95 / 1.01 / 0.89 |
| both | 42 / 123 / 456 | −6.56e−4 / −6.02e−4 / −3.23e−4 | −6.65e−4 / −5.79e−4 / −3.28e−4 | 1.01 / 0.96 / 1.02 |
| vision_only | 42 / 123 / 456 | −2.34e−4 / −3.39e−4 / −4.53e−4 | −2.45e−4 / −3.30e−4 / −4.64e−4 | 1.05 / 0.97 / 1.02 |

**$\cos(\text{预测},\text{实测}) = 0.9977$ ｜ 中位相对误差 $= 2.70\%$**

**判据（事先写明：$\cos>0.9$ 且相对误差 $<20\%$）→ 远超通过。**

**意义**：ODE 的推导前提**不再只是"拟合得像"，而是被直接验证**。

## 实验二：按编码器侧分解梯度 ✅ **理论预测全部成立**

| 位置 | $\|\nabla_{\theta_v} DG^*\|$ | $\|\nabla_{\theta_t} DG^*\|$ | $\|g_v\|$ | $\|g_t\|$ |
|---|---|---|---|---|
| **text_only** | **0.0000** | 1.5162 | **0.0000** | 13.5077 |
| both | 1.7613 | 1.6025 | 12.9289 | 11.0456 |
| **vision_only** | 1.8599 | **0.0000** | 15.4371 | **0.0000** |

**理论预测（逐位置）**：

| 预测 | 结果 |
|---|---|
| `text_only` → $g_v = 0$ | ✅ **精确成立**（0.0000） |
| `vision_only` → $g_t = 0$ | ✅ **精确成立**（0.0000） |
| `both` → 两侧非零 | ✅ 成立 |

**→ 论文最核心的理论断言（"文本侧适配消除视觉梯度项"）得到直接验证。**

### 机制图景（数据支持）

| 位置 | 视觉侧扰动压力 |
|---|---|
| vision_only | $g_v = 15.44$，**仅视觉侧** → 最大 |
| both | $g_v = 12.93$ 且 $g_t = 11.05$ → 中等 |
| text_only | $g_v = 0$ → **无视觉侧扰动** |

**与三臂实测排序一致**：$\Delta$CG 为 text_only **−0.0465** < both −0.0258 < vision_only **+0.0106**。

## 实验三（附加）：间隙方向的秩 1 程度

| 量 | 值 |
|---|---|
| $\|\overline{z^I - z^T}\|$ | 0.8076 |
| $\text{mean}\|z_i^I - z_i^T\|^2$ | 1.3677 |
| **沿 $\hat d$ 的解释方差占比** | **0.4820** |
| 中心化后第一奇异值占总能量 | 0.2691 |

**判据（>0.5）→ 0.4820，未达** → **CLIP ViT-B/32 上间隙不完全是单一方向**。

**与 `sharma2026readout`（CLIP/SigLIP 上 94.4–99.9%）的关系**：他们的量是
"**图像-文本均值分离**的平方范数被单一方向解释的比例"，
本文此处是"**逐对差向量**沿均值方向的能量占比"——**两者口径不同，不可直接比较**。
**已如实标注口径差异**，不作"矛盾"表述。

## 对稿件的意义（**待操作者决定是否写入**）

| 发现 | 可加强的主张 | 建议位置 |
|---|---|---|
| 恒等式直接验证（cos 0.998） | **ODE 的理论根基** | §Theory 末 或 §Validation 首 |
| $g_v = 0$ 逐位置精确成立 | **核心理论断言** | §Theory "The text-only position" |
| 编码器侧梯度表 | **机制解释**（不只现象） | §Validation 新小段 + 可选小表 |
| 间隙方向非严格秩 1 | **如实边界** | §Discussion 局限 |

## 复核入口

```powershell
python tools\_exp1_gradflow_identity.py --apply
python tools\_exp2b_mechanism_gradient_interference.py --apply
python tools\_exp2c_encoder_side_gradients.py --apply
python tools\_exp2_mechanism_gap_direction.py --apply
```

---

## ✅ 已写入正文（2026-10-05，操作者确认）

| 插入位置 | 内容 |
|---|---|
| `theory.tex`（式 `eq:gradflow` 之后、Lemma 之前） | **恒等式直接验证**：9 个配置，cos = **0.998**，中位相对误差 **2.7%** |
| `theory.tex`（"The text-only position"） | `g_v = 0` 的措辞**补上实测支撑**（0.0000） |
| `validation.tex`（新小节 **Measured Gradient Asymmetry**） | 按编码器侧的 `‖g_v‖`/`‖g_t‖` 实测 + **表 `tab:grad_side`** |

**插入脚本**：`tools/_pa_add_verified_theory.py`（带断言，可重跑——理论锚点为
`\begin{lemma}[Modality Decomposition]`，验证锚点为 `\subsection{Closing the Empirical--Theory Loop}`）

**编译结果**：NC **43 页** / Springer **33 页**（+1，因新小节与小表）、0 错误、0 未定义引用、
cites 44 = bib 44、表 **9/9** label 一致、悬空 ref 0、摘要仍 **244 词**、终检全绿。

**已核验新内容进入 PDF**：`Measured Gradient Asymmetry`、`13.51`、`15.44`、`12.93`、
`0.998`、`2.7%`、`0.0000` 全部检出。
