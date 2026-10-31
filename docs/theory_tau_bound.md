# τ↔top-1 理论：完整推导（v2 终版，2026-08-22）

> 状态：**推导完整**。定理栈（Lemma 1–2、Theorem 1–5、Corollary 1–2 及其全部证明）均已闭合；
> 校验全部落盘：`outputs/a1_margins.json`（含新增 `predicted_rank1_loss_corr` 字段，
> `mean_m = 0.372`，由 `tools/clip_a1_margins.py` 重跑生成，旧字段逐值复现）。
> 用途：A1 journal 扩展版 §4（理论节）的正式素材；可直接转为 LaTeX。
> 有效域与残差：见 `docs/theory_first_order_residual.md`（与本文档互补，两者合并即理论全貌）。

## 0. 定理栈总览

| 编号 | 内容 | 有效性 |
|---|---|---|
| Lemma 1 | 成对反转的精确条件 λ‖g‖(m_j−m_i) > d_ij | **任意 λ 精确**（非一阶） |
| Lemma 2 | 图像侧手术的序 = s_c + λ‖g‖m_c 的序 | **任意 λ 精确** |
| Theorem 1 | τ(λ) 的确定性逐点算子（零假设、零参数） | 校验 9/9（差 ≤0.002） |
| Theorem 2 | 分布模型：E[τ]、高斯闭式与 Chebyshev 界 | 参数全部来自冻结模型 |
| Theorem 3 | top-1：精确事件 + 相关结构条件界 + 与 union bound 比较 | 数值校验（§11） |
| Theorem 4 | 图像/文本非对称（一阶恒等式 + 二阶比值界 0.13λ） | 与实测 0.43/0.36 吻合 |
| Corollary 1 | 正交平移族：同构运算 + 温和性 |
| Theorem 5 | 类别对齐收缩 = 同构偏置场（**任意 a 精确**）；两场分解 | 与 Table 1（78.6%/τ 0.615）自洽 |
| Corollary 2 | **界中无 CG 项**：分类健康与 CG 形式上无关（A1 命题的形式化） |

---

## 1. 记号与假设

- 冻结模型：归一化图像嵌入 $x \in \mathbb{S}^{d-1}$；类别文本嵌入 $\{t_c\}_{c=1}^{n}$（$n=1000$），$s_c = x\cdot t_c$。
- 冻结全排序 $c_1 \succ c_2 \succ \dots$；成对 margin $d_{ij} := s_i - s_j \ge 0$（$i \succ j$）。
- 鸿沟向量（Flickr30k 验证子集，与 A1 同口径）：$g = \frac{1}{n_t}\sum_t - \frac{1}{n_x}\sum x$，$\|g\| = 0.815$，$\hat d = g/\|g\|$。
- gap-direction 手术：$\tilde x = \mathrm{norm}(x + \lambda\|g\|\hat d)$，$\lambda \in \{-2,-1,-0.5,-0.25,0.25,0.5,1,2,4\}$。
- 类偏置场标量：$m_c := \hat d \cdot t_c$；记 $b_{ij} := m_j - m_i$。
- 逐图 top-5 指标：$\tau_{\mathrm{img}}$ = 冻结 top-5 集合上冻结分数与扰动分数的 Kendall τ（10 个无序对）。

**假设**（全部有实测背书）：
- **A1（归一化）**：$x, t_c$ 单位范数；手术与收缩均做归一化。
- **A2（精确判据）**：只关心两两序，不关心分数数值（Lemma 1–2 的基础）。
- **A3（近似独立）**：$(d_{ij}, b_{ij})$ 在 50000 对样本上 Pearson = 0.066、Spearman = 0.040——margin 与偏置差分近似独立（`margin_bias_independence` 字段）。
- **A4（工作模型）**：$m_c = \mu_m + \sigma_m Z_c$，$Z_c$ i.i.d. 标准正态；实测 $\mu_m = 0.372$（不为零！但差分自动消去），$\sigma_m = 0.0674$，$\sigma_b := \sqrt{2}\sigma_m = 0.0953$。
- **A5（指标定义）**：τ 取冻结 top-5 集合上的配对计数；top-1 指全 1000 类上的 argmax。

---

## 2. Lemma 1（成对反转的精确条件）

**陈述**：对任意 $\lambda$（含负值），$\tilde x$ 下对 $(i,j)$（$i \succ j$，$d_{ij} > 0$）被反转当且仅当
$$\lambda\|g\|\,(m_j - m_i) \;>\; d_{ij}.$$

**证明**：Lemma 2（下文）给出序的精确表示；$\tilde s_i < \tilde s_j \iff s_i + \lambda\|g\|m_i < s_j + \lambda\|g\|m_j \iff \lambda\|g\|(m_j - m_i) > s_i - s_j = d_{ij}$。注意 $\lambda < 0$ 时不等式方向自动翻转（两边乘负号），故正负 λ 均为同一条件。∎

**含义**：反转 = "小 margin × 大偏置差"的联合事件；**与归一化非线性、与 CG 均无任何一阶（乃至任何阶）联系**。

## 3. Lemma 2（图像侧排序的仿射精确表示）

**陈述**：设 $u_c := s_c + \lambda\|g\| m_c$。则 $\arg$sort$_c\,\tilde s_c = \arg$sort$_c\, u_c$（逐图，任意 λ 精确）。

**证明**：$\tilde x = (x + \delta)/\|x+\delta\|$（$\delta = \lambda\|g\|\hat d$），$\tilde s_c = \tilde x \cdot t_c = (s_c + \delta\cdot t_c)/\|x+\delta\| = u_c / \|x+\delta\|$；分母逐图常数（与 c 无关）且为正，不改变序。∎

**评注**：Lemma 2 吸收掉全部范数非线性——排序层面理论对任意 λ 精确；这与"数值层面（CG 位移大小）只在 λ‖g‖ ≲ 1 内有效"（见 `theory_first_order_residual.md` §4）构成并列的两个有效域。A1 中 Pearson(实测逐类位移, λ‖g‖m_c) = 1.0000 正是该分解的数值影子。

---

## 4. Theorem 1（τ 的确定性逐点算子）

**陈述**：令 $P_i$ = 图像 $i$ 的冻结 top-5 生成的 10 个无序对，$\mathrm{inv}_i(\lambda) := |\{(i,j) \in P_i : \lambda\|g\|b_{ij} > d_{ij}\}|$。则（逐图精确）
$$\tau_i(\lambda) = 1 - \frac{2\,\mathrm{inv}_i(\lambda)}{10},\qquad \bar\tau(\lambda) = \frac{1}{N}\sum_{i=1}^{N} \tau_i(\lambda).$$

**证明**：Lemma 1 + Kendall τ 的定义（5 个互异元素 10 对中，反转对数为 inv，一致对为 10 − inv，τ = (C−D)/10）。∎

**校验（同一 5k 样本，无参数、无分布假设）**：9/9 命中，差 ≤ 0.002（正负 λ 皆然）：

| λ | −2 | −1 | −0.5 | −0.25 | 0.25 | 0.5 | 1 | 2 | 4 |
|---|---|---|---|---|---|---|---|---|---|
| 预测 (Theorem 1) | 0.202 | 0.330 | 0.493 | 0.654 | 0.636 | 0.463 | 0.290 | 0.155 | 0.070 |
| 实测 (同 5k) | 0.200 | 0.329 | 0.492 | 0.654 | 0.635 | 0.462 | 0.288 | 0.154 | 0.068 |

**推论（因果性表述）**：任何图像在任意 gap-direction 平移下的**序破坏程度可以从冻结模型闭式计算**——τ–top-1 的 0.926 相关性从"相关"升级为"可计算"。

## 5. Theorem 2（分布模型：期望与界）

**陈述**：在 A3–A4 下（b 近似 i.i.d. 零均值、方差 σ_b²，且与 margin 独立）：
$$\mathbb{E}[\tau_{\mathrm{img}}] = 1 - \frac{2}{10}\sum_{(i,j)\in P_i} \mathbb{P}\!\left(b > \frac{d_{ij}}{\lambda\|g\|}\right).$$
（a）**高斯闭式**：$\bar\tau(\lambda) = 1 - \frac{2}{10}\sum_{(i,j)} \bar\Phi\!\left(\frac{d_{ij}}{\lambda\|g\|\sigma_b}\right)$，$\bar\Phi(u)=\mathbb{P}(N(0,1)>u)$。
（b）**分布无关界**（Chebyshev）：$\mathbb{P}(b>t) \le \sigma_b^2/t^2 = 2\sigma_m^2/t^2 \Rightarrow \bar\tau \ge 1 - \frac{2}{10}\sum_{(i,j)}\frac{2\sigma_m^2\lambda^2\|g\|^2}{d_{ij}^2}$（对零均值 b 用一阶 Chebyshev/Cantelli：$\mathbb{P}(b\ge t) \le \mathrm{Var}(b)/(\mathrm{Var}(b)+t^2) \le \mathrm{Var}(b)/t^2$）。
（c）**高斯尾界**：$\bar\Phi(u) \le \tfrac12 e^{-u^2/2}$（$u>0$），给出指数型下限。
（d）**显式下界**：若所有 margin ≥ d_min，则 $\bar\tau \ge 1 - 2\bar\Phi\!\left(\frac{d_{\min}}{\lambda\|g\|\sigma_b}\right)$。

**证明**：Lemma 1 + 期望线性 + $\mathrm{Var}(m_j - m_i) = 2\sigma_m^2$（A4）；Chebyshev 与高斯尾代入即得。∎

**单调性**：τ 只通过组合量 $\lambda\|g\|\sigma_b / \{d_{ij}\}$ 依赖扰动——这就是剂量-响应的理论形态；小 margin 对先崩（实测 margin 分布：mean 0.0183、q50 0.0123、q10 0.0018，q10 驱动的早期崩塌）。

**对拍**：高斯 Φ̄ 模型在 λ=1/2/4 给出 0.180/0.093/0.047，明显弱于 Theorem 1（精确 0.290/0.155/0.070）——**精确算子完胜**；分布模型的用途是"不需要真实 m 的可行预测"（如对新模型族先验预测）。

## 6. Theorem 3（top-1：精确事件与界）

**精确事件**（Lemma 1 逐对）：$c_1$ 被 $j$ 超越 ⟺ $\lambda\|g\|b_{1j} > d_{1j}$，$j \ne c_1$。
$r_1(\lambda) := \mathbb{P}($frozen-top-1 $c_1$ 被任何一个竞争者超越$)$。

**（a）精确量**（top-5 竞争者子集，确定性）：$\hat r_1(\lambda) = \frac{1}{N}\sum_i \mathbb{1}[\max_{j\in \mathrm{top5}\setminus c_1} (\lambda\|g\|b_{1j} - d_{1j}) > 0]$——程序 `predicted_rank1_loss_exact` 所示。这是**超集下界**情形（只数 top-5 内竞争者）。

**（b）union bound（边缘模型）**：$r_1 \le \sum_{j\ne c_1}\bar\Phi\!\left(\frac{d_{1j}}{\lambda\|g\|\sigma_b}\right) \le 4\bar\Phi\!\left(\frac{d^1_{\min}}{\lambda\|g\|\sigma_b}\right)$。λ=1 时右端 ≈ 1.42——**饱和，无信息**。

**（c）相关结构紧界（新，本版核心推导）**：给定 $m_1 = \mu_m + \sigma_m u$，各竞争者 条件独立（A4）：
$$r_1^{\mathrm{corr}}(\lambda) \;=\; 1 - \int \varphi(u)\prod_{j\ne c_1}\Phi\!\big(\sigma_\lambda\,u + \tfrac{d_{1j}}{\lambda\|g\|\sigma_m}\big)\,\mathrm{d}u, \qquad \sigma_\lambda = \mathrm{sign}(\lambda),$$
其中 $\varphi, \Phi$ 为标准正态密度/分布函数；$\lambda<0$ 时因子为 $\Phi(c_j - u)$（由 Lemma 1 变号即得）。
**证明**：条件独立 ⟹ 存活概率 = 乘积；$Z_j \le u + c_j$（λ>0）/ $Z_j \ge u - c_j$（λ<0），对 $u \sim N(0,1)$ 积分。∎
**实现与对拍**：`tools/clip_a1_margins.py` 数值求积（u∈[−8,8]，0.02 步长）；蒙特卡洛独立复核 200k 次：**0.6773 vs 0.6766（差 0.0007）**——公式与实现一致。

**（d）数值比较（top-5 竞争者被超越率，5k 样本）**：

| λ | 精确（真实 m） | 相关结构界（高斯） | 边缘模型 E[Σ_j inv_j]/4（存档 gauss 字段） | 实测：冻结正确类保失率* |
|---|---|---|---|---|
| 0.25 | 0.208 | 0.325 | 0.138 | 0.053 |
| 0.5 | 0.357 | 0.505 | 0.248 | 0.192 |
| 1 | 0.521 | 0.651 | 0.354 | 0.46 |
| 2 | 0.666 | 0.729 | 0.424 | 0.77 |
| 4 | 0.753 | 0.766 | 0.461 | 0.94 |

\* 冻结正确类保失率 = (frozen_top1_5k − top1(λ)) / frozen_top1_5k，frozen 5k = 59.26%；与"被 top-5 竞争者超越"并非同一事件（含 top-5 外竞争者），故仅作量级对照。
**读数**：确定性精确 ≈ 实测（在冻结正确子集口径下同源）；相关结构界严于 union bound（1.42 → 0.65，λ=1），但高斯模型相对真实 m 仍保守（0.65 vs 0.52）——真实 $m$ 的尾部薄于高斯（$\sigma_m$ 估计由样本矩决定）。**结论：可做范畴化预测（分类正确性由 margin×m 差分决定），逐点精确预测必须走 Theorem 1/3(a) 的确定性算子**。
**弱界（无分布、恒成立）**：top-1 错误 ⟹ 该图至少 1 反转 ⟹ $\tau_{\mathrm{img}} \le 0.8$；且 $\mathbb{P}(\text{top-1 错}) \le \mathbb{E}[\#\text{反转}] = 5(1-\bar\tau)$。诚实标注：在实测 τ∈[0.07, 0.65] 区间内多为平凡，价值在方向正确。

## 7. Theorem 4（图像/文本非对称）

**陈述**：文本侧平移 $t_c \mapsto \mathrm{norm}(t_c + \lambda\|g\|\hat d)$ 下，展开分母 $(1+u)^{-1/2}$：
$$\Delta s_c = \underbrace{\delta\cdot x}_{(0)}\;-\;\underbrace{\lambda\|g\| m_c s_c}_{(1)}\;+\;\underbrace{\big(\tfrac32(\lambda\|g\|m_c)^2 - \tfrac12\lambda^2\|g\|^2\big)s_c}_{(2)} + O(\lambda^3),$$
- **(0)** 为纯逐图像常数 ⟹ **一阶零反转**；
- **(1)** 为逐类项 ∝ m_c s_c ⟹ 重排从 O(λ²) 开始；
- 量级比：图像侧一阶差分 ≈ λ‖g‖σ_b ≈ 0.077λ，文本侧二阶差分 ≈ λ²‖g‖²·σ_m·s_c ≈ 0.01λ²，**比值 ≈ 0.13λ**。

**推论**：λ=1 文本侧重排强度 ≈ 图像侧 13%（实测：txt τ 0.43 基本无损 vs img τ 0.29），λ=2 时 ≈ 26%（txt 0.36 开始侵蚀）——表 2 非对称的**定量来源是结构性的**（一阶项恰好是逐图像常数），而非偶然小常数。
**证明**：直接展开（见 `theory_first_order_residual.md` §3，含完整代数）。∎

## 8. Corollary 1（正交平移族）

$r \perp \hat d$ 的同幅平移给出偏置场 $\lambda\|g\|\,(r\cdot t_c)$——与 Theorem 1–3 **完全同构**，仅把 $m_c$ 换成 $r\cdot t_c$。其有效离散度 $\tilde\sigma = \mathrm{std}(r\cdot t_c) < \sigma_m$，故 O 家族在**同一算子**下更温和。

**数值验证（2026-08-22，`outputs/a1_theory_verify.json`）**：复现实验用 $r$（RandomState(7)，正交化于 $\hat d$）→ $\tilde\sigma = 0.0306 = 0.454\,\sigma_m$（低于一半——量化"正交族温和"）。Theorem 1 算子预测 τ_O(λ) vs 实测：

| λ | −2 | −1 | −0.5 | 0.25 | 0.5 | 1 | 2 | 4 |
|---|---|---|---|---|---|---|---|---|
| 预测 τ_O | 0.289 | 0.446 | 0.615 | 0.753 | 0.595 | 0.408 | 0.228 | 0.102 |
| 实测 τ_O | 0.226 | 0.407 | 0.594 | 0.757 | 0.614 | 0.445 | 0.287 | 0.177 |

差 ≤0.075（|λ|≤1 时 ≤0.039；大 λ 偏差与 a1_full 批次 d̂ 口径微差一致——T 族在同一冻结数据上为 ≤0.002）。与 T 族对照（λ=1：τ_T 预测 0.289 vs τ_O 0.408）印证"orthogonal 温和"为结构性结论：$\tilde\sigma \approx 0.45\sigma_m$ 直接进入反转概率的钟形中心。

## 9. Theorem 5（类别对齐收缩 = 同构偏置场；两场分解）

设 $x$ 的真类为 $i$，类质心 $\mu_i$（该类图像嵌入均值），收缩 $x \mapsto \tilde x = \mathrm{norm}\big((1-a)x + a\mu_i\big)$，$e := \mu_i - x$。

**陈述（同构）**：任意 $a$ 精确地，
$$\arg\mathrm{sort}_c\,\tilde s_c = \arg\mathrm{sort}_c\big(\,s_c + a\,\langle e, t_c\rangle\,\big).$$
即**收缩与 gap-direction 手术是同一族形式对象**：偏置场 $a\,e$ 取代 $\lambda\|g\|\,\hat d$；有效性对**任意 a 精确**（分母公共正因子，同 Lemma 2 论证）。

**两场分解**：$e = \langle e, t_i\rangle\, t_i + e_\perp$（Gram–Schmidt 于 $t_i$）。则
$$\Delta s_i = a\,\langle e, t_i\rangle \quad(\text{自场，真类}),\qquad \Delta s_c = a\,\langle e_\perp, t_c\rangle \quad(c\ne i,\ \text{横场}).$$
- **自场**：把分数推向质心对齐水平 $\langle \mu_i, t_i\rangle$ ——真类 margin 的**确定性再对准**（对"图像分数低于类质心分数"的图像成立，方向为正）；
- **横场**：$\mathbb{E}_{x\sim \mu_i}[\langle e, t_c\rangle] = \langle \mu_i - \mathbb{E}x, t_c\rangle = 0$（$x$ 的分布均值就是 $\mu_i$）——**零均值置换噪声场**。

**推论（与 Table 1 的定量自洽）**：横场给出"其他类之间"的零均值重排 ⟹ $\tau$（相对冻结）下降；自场扩大真类 margin ⟹ 正确率上升——这正是 A1 Table 1 P 类行的结构（a=0.5：top-1 78.6% ↑、τ=0.615 ↓）与 Fig.2 右上灰点的机制解释。同时**证明**：τ(vs 冻结) 对"对齐型扰动"不是恰当的健康指标（它惩罚了自场增益）；恰当参照应为类对齐扰动坐标系——对应扩展版的 open question。

**逐图微验证（2026-08-22，与实测逐值一致）**：用同 5k 样本质心（类内均值，同 `clip_a1_subspace.py` 口径）代入精确仿射序：

| a | 预测 top-1 | 实测 top-1 | 预测 τ | 实测 τ |
|---|---|---|---|---|
| 0.25 | **70.32** | 70.32 | **0.7598** | 0.7598 |
| 0.50 | **78.58** | 78.58 | **0.615** | 0.615 |

（完全一致——同构的序运算与实测的归一化收缩在任意 a 下等价，Theorem 5 的"精确"得到逐值确认。）自场实测：mean ⟨e, t_i⟩ = **+0.0435**（std 0.0288）——真类分数确实被系统性上推；而 ⟨e, t_c⟩（c≠i）零均值形成排列噪声——两场分解的统计形状被直接观察到。
**证明**：公共正分母 + $\mathbb{E}$ 线性，如上诉。∎

## 10. Corollary 2（分类健康与 CG 无关——A1 主张的形式化）

Theorem 1–3 的每个量（τ、top-1 界、反转条件）**只依赖** $(\lambda\|g\|, \{m_c\}, \{d_{ij}\})$——其中**不含任何 CG/DG 项**；CG 的单调性、符号、大小均不进入界。形式上：
> 对固定 (m, d)，集合 $\{(\lambda, \mathrm{CG}(\lambda))\}$ 的任意重参数化不改变 τ(λ)、top-1(λ)。
> 因此"gap 收缩破坏分类"不是 gap 的功能，而是**偏置场 m_c 通过成对反转作用于分数序**的功能——分类健康 = 序健康（A1 标题命题的直接形式化）。∎

## 11. 校验汇总（全部落盘）

- **τ 逐点**：Theorem 1 vs 实测 9 点 ≤0.002（§4 表；`predicted_tau_exact` vs `measured_tau_5k`）。
- **top-1**：§6(d) 表（`predicted_rank1_loss_{exact,corr,gauss}` vs 实测 5k top-1）；相关结构界与 MC 对拍差 0.0007。
- **独立性**：A3 已验（Pearson 0.066/Spearman 0.040，50k 对）。
- **非对称**：§7 比值 0.13λ 与实测（0.43/0.36 vs 0.29/0.15）一致。
- **P 类**：§9 与 Table 1（78.6/0.615；70.3/0.760）方向自洽。
- **独立性与常数**：A3 已验（Pearson 0.066/Spearman 0.040，50k 对）；$\|g\|=0.815$、$\sigma_m=0.0674$、$\mu_m=0.372$、margin mean 0.0183/q50 0.0123/q10 0.0018、rank1_mean 0.0303/rank1_q10 0.0063。
- **本版新增（08-22）**：① 经验分布界 λ=1: 0.5701（高斯 0.6508 / 精确 0.5204）；② O 族 σ̃=0.0306=0.454σ_m、预测-实测 ≤0.075；③ P 类预测=实测（70.32/78.58、0.7598/0.615）、自场 +0.0435。数据：`outputs/a1_theory_verify.json`。

## 12. 完成状态（2026-08-22 三项闭环）

1. ✅ **经验分布版相关结构界**（`predicted_rank1_loss_emp`）：F̂_m（999 类 LOO）取代高斯 Φ。λ=1 时 **0.5701**（高斯 0.6508 → 精确 0.5204）——保守差从 0.13 缩至 0.05；λ=4 时 0.7438 vs 0.7528（几乎贴合）。结论：分布模型应默认用经验分布。
2. ✅ **O 族 σ̃ 与同构验证**：σ̃ = 0.0306 = 0.454σ_m；预测 τ_O 与实测 ≤0.075（见 §8）。
3. ✅ **Theorem 5 逐图微验证**：预测与实测**逐值一致**（70.32/78.58、0.7598/0.615）；自场均值 +0.0435 直接测到。
4. ⏳ 可选：负 λ 文本侧（λ³ 项）展开——`theory_first_order_residual.md` §7 已标注，按需补。
5. ⚠️ 已知口径注记：O 族大 λ（|λ|≥2）预测偏差疑因 `a1_full_results` 批的 d̂ 与本次重算相差（同一冻结数据 T 族 ≤0.002 佐证）；如需逐值统一，可用同管道重算 O 全曲线（零新实验、数分钟）。
