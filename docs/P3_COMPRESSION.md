# P3 七页合规版：四节压缩记录（theory / introduction / discussion / conclusion）

**任务**：`task-12` ｜ **对象**：`paper3/paper_ieee/`（PRL，`PRLETTERS-D-26-02378`，Revise，截止 2026-11-02）
**硬约束**：PRL *Mandatory Submission Requirements* 第 1 条 —— 双栏、**≤7 页（含全部材料）**
**日期**：2026-10-13 ｜ **写者边界**：只改 `sections/{theory,introduction,discussion,conclusion}.tex` + `tools/_p51*.py` + 本文件

---

## 1. 一句话结论

**四节已压 27.4%（29,038 → 21,155 字符），编译 10 页 / 0 错 / 0 未定义 / `_p497` 需处理 0 处。**
但**任务给的四个目标值（12,600）在不删结论的前提下达不到**，而且更重要的发现是：
**约束不在我这四节** —— `experiments.tex` 一节就有 27,847 字符（≈4.89 页），即使把我这四节**整节删光**，
全稿也只能到 35,859 字符 ≈ 6.3 页。详见 §6。

---

## 2. 压缩结果（逐节）

| 节 | 改前 | 任务目标 | 实际改后 | 实际压缩 | 与目标差 |
|---|---|---|---|---|---|
| theory | 15,191 | ≈6,500 | **9,805** | −5,386（−35.5%） | +3,305 |
| introduction | 5,054 | ≈2,400 | **4,057** | −997（−19.7%） | +1,657 |
| discussion | 5,746 | ≈2,500 | **4,542** | −1,204（−21.0%） | +2,042 |
| conclusion | 3,047 | ≈1,200 | **2,751** | −296（−9.7%） | +1,551 |
| **合计** | **29,038** | **≈12,600** | **21,155** | **−7,883（−27.1%）** | **+8,555** |

> 说明：`theory` 的"改前"含 `tools/_p512` 修复断头命令时补回的 `\`（+48 字符，见 §4）。
> `introduction` 的字符数在最后一轮 +57：把"does not reappear under real image--text pairs"
> 这条**协议归属的证据**加了回去（宁可多 57 字符，也不让"协议而非模型"变成无证据断言）。

---

## 3. 验证报告（全部实测）

### 3.1 编译（`cd paper3/paper_ieee` → `pdflatex` ×2 + `bibtex` + `pdflatex` ×2）

```
errors(!): 0
undefined refs: 0
Output written on main.pdf (10 pages, 414823 bytes).
```

**页数 11 → 10**（压缩前 11 页 / 64,835 字符；压缩后 10 页 / 56,957 字符）。

⚠️ **本次编译包含 Lead 正在改的 `experiments.tex`（当前 27,847 字符）**，因此页数会随 Lead
的改动而变；上表是我改完四节后的即时快照。

### 3.2 三项扫描

| 工具 | 结果 |
|---|---|
| `python tools\_p497_scan_contradictions.py` | **需处理 0 处**（✅ 无；命中 12 处全在允许的撤回/否定语境） |
| `python tools\_p503_fix_literal_n_correct.py` | **全稿字面 `\n` = 0**（合法 `\n` 命令 52，不可触碰） |
| `python tools\_p512_repair_severed_commands.py` | 四个文件**待修 0 处**（本次已修 31 处，见 §4） |

### 3.3 目标 vs 实际的换算（`tools/_p509` 口径）

```
现 56,957 字符 ｜ 10 页 ｜ ≈5,696 字符/页 ｜ ≤7 页预算 ≈39,870 字符
⇒ 还需再删 17,087 字符（现量的 30%）
```

---

## 4. 🔴 顺带查出的**既有事故**：58 处"断头命令"（不是本次压缩造成的）

### 4.1 病因（与 `_p501` 不同源，但同型）

某个脚本用**非 raw** 的 Python 字符串拼 LaTeX：`"\nabla"` 里 `\n` 是换行
⇒ 写进 `.tex` 后变成 `（真换行）abla`。同型受害者：

| 原命令 | 切断后 | 说明 |
|---|---|---|
| `\nabla` | `abla` | 数学模式里 `abla E` 只是四个变量字母 ⇒ **不报错**，但 PDF 印的是 `ablaE` 而不是 `∇E` |
| `\noindent` | `oindent` | 文本模式里就是一串字母 ⇒ 段首缩进与"Keywords"字样都错 |
| `\neq` | `eq` | 同上，`≠` 变成 `eq` |

**关键：这类损伤不产生编译错误。** `_p503`（只数字面 `\n`）报 0、`main.log` 报 0 errors，
**但 PDF 里是错的** —— 静默错误比报错更危险。

### 4.2 已修（我的 4 个文件，31 处）

`tools/_p512_repair_severed_commands.py`（幂等、带三重断言）：

```
theory.tex          修 24 处；断言 3 项全过
introduction.tex    修  3 处；断言 3 项全过
discussion.tex      修  2 处；断言 3 项全过
conclusion.tex      修  2 处；断言 3 项全过
```

判据刻意做窄：① 行首 token 白名单（`abla`→`\nabla`、`oindent`→`\noindent`、`eq`→`\neq`）；
② **前一行必须是"仍写了一半的表达式"**（`$` 未闭合，或以 `( [ | = , \langle \perp \cos( \Gamma` 结尾），
否则**报错退出、不写盘**；③ 写盘后逐行 diff，**只允许被锁定的那几行变化**，字符增量必须恰好
`2 × 修复数`。 —— 这是对 `_p501` 那次"宽泛正则把 `\newtheorem` 吃成 `ewtheorem`"的直接纠正。

### 4.3 🔴 **仍在主编译链上、需 Lead 处理（超出我的写范围）**

`python tools\_p512_repair_severed_commands.py --scan` 全树仍报 **58 处**，其中
**4 处在 `main.tex` 正文编译链上 ⇒ 当前 main.pdf 的摘要里印的是 `abla` 而不是 `∇`**：

| 文件 | 行 | 现状 | 应为 |
|---|---|---|---|
| `main.tex` | **40** | `abla_{M_k}E,u_{M_k}\rangle$. We ask what an` | `\nabla_{M_k}E,u_{M_k}\rangle$` |
| `main.tex` | **44** | `abla E\|^2$. Given` | `\nabla E\|^2$` |
| `main.tex` | **63** | `oindent\textbf{Keywords:}` | `\noindent\textbf{Keywords:}` |
| `sections/related_work.tex` | **14** | `abla E, u \rangle$---is the unique admissible` | `\nabla E, u \rangle$` |

**建议的二选一**（4 处、每处只差一个 `\`）：
- **A（推荐）**：授权我跑
  `python tools/_p512_repair_severed_commands.py --apply --files paper3/paper_ieee/main.tex paper3/paper_ieee/sections/related_work.tex`
  —— 同一条锚点判据、同一套断言，脚本会拒绝任何锚点不符的改动；
- **B**：Lead 自己按上表逐处补 `\`。

其余 54 处**不在主编译链上**（`appendix.tex` 17、`supplementary/supplementary.tex` 27、
`main_body_full.tex` 3、`title_page_prl.tex` 7）：`main.tex` 只 `\input` 六个 section，
`appendix`/`supplementary`/`*_full`/`title_page` 各自独立成文。**投稿前若这些也要编译，需一并修**。

---

## 5. 待 Lead 并入 supplementary（移出正文的内容，**未删除**）

以下段落是**从正文移出**的展开性文字（按 task-12 允许的三类：证明的逐步推导 / 各 Corollary 的展开讨论 /
与其他工作的逐条对比细节）。**逐字保留原文**，供并入 `supplementary/supplementary.tex`。

### 5.1 来自 `theory.tex`

**（T1）R1–R5 的逐条必要性论证**（现正文只留一句概括）：

> These are not ``axioms we chose.'' Each is a necessary condition for $S$ to serve as a PEFT allocation
> statistic: without (R1), allocation cannot be computed pre-training; without (R2), LoRA and Adapter give
> different allocations for the same update; without (R3), blocks cannot be individually compared; without
> (R4), beneficial and harmful training are conflated; without (R5), expensive Hessian computation is needed
> for negligible correction.

**（T2）R2 的展开陈述**（现压成一行）：

> Different PEFT methods (LoRA, Adapter, BitFit) reparameterize the same effective update. $S$ must give
> consistent answers regardless of parameterization --- requiring invariance under block-wise
> reparameterization. We restrict to the orthogonal subgroup of transformations, which is the natural
> invariance group for Euclidean gradient descent; the non-orthogonal case (including the LoRA $A/B$
> decomposition and Adapter bottleneck embeddings) is discussed in Corollary~4 and Section~V.

**（T3）Corollary 1 的"PEFT regime reduction"段**（现正文压成从句）：

> \textbf{PEFT regime reduction.} Under LoRA, $\|\Delta\theta\| \ll \|\theta_0\|$ ($<1\%$ parameters).
> Therefore $H_k$ is negligible and $\mathbb{E}[D_k]=0$, making $\Gamma_k$ the \emph{dominant first-order
> term}.

**（T4）Corollary 2 的指数唯一性论证尾句与 (A1) 失败的处置**：

> $1/\Gamma$ is unnormalized; sigmoid cannot satisfy $\sum = C$; piecewise introduces arbitrary cutoffs.
> The exponential emerges directly from KKT. If (A1) fails, the KKT framework remains valid with
> re-estimated $f(\mathrm{rank})$; only the closed form changes.

**（T5）Corollary 2 的 $\beta$ 展开讨论**（现正文保留结论：$\beta$ 不在源架构上拟合、无需跨架构标定、
`$|\Gamma|\sim10^3$–$10^4$` 的原始量级无配置含义、迁移的是序）：

> The allocation (Equation~\ref{eq:allocation}) depends on the products $\beta|\Gamma_k|$ alone and is
> invariant under the joint rescaling $(\beta, |\Gamma_k|) \to (\beta/s, s|\Gamma_k|)$ for any $s>0$.
> Because $\beta$ is the entropy-regularization temperature---a design parameter indexing the family from
> uniform ($\beta \to 0$) to the greedy corner solution ($\beta \to \infty$)---it is not fitted on the source
> architecture, and no cross-architecture calibration is required: if the target's $\Gamma$ magnitudes differ
> by a factor $s$, the identical allocation is recovered with temperature $\beta/s$. The raw magnitudes in
> Appendix~D ($|\Gamma| \sim 10^3$--$10^4$) therefore carry no allocative meaning by themselves; what
> transfers is the \emph{ordering} of $|\Gamma_k|$ (Corollary~4), and for well-separated magnitudes any
> temperature below the separation scale drives the linear surrogate to the same corner---negligible capacity
> on the alignment-sensitive blocks.

**（T6）Corollary 4 的"非正交重参数化"两条缓解论证**（现正文压成一句）：

> \textbf{Non-orthogonal reparameterizations.} The invariance holds within the orthogonal subgroup (R2);
> non-orthogonal reparameterizations (LoRA $A/B$, Adapter bottlenecks) do not preserve the inner product
> exactly. Two remarks mitigate this. First, $\Gamma$ is computed in the native parameter space of each
> method, so within-method block comparisons are unaffected. Second, the assumption's empirical validity is
> directly tested by our cross-method results: the ODE framework and exponential allocation hold
> quantitatively under LoRA, Adapter, and BitFit in Paper~2, and the phase transition reproduces under LoRA
> on LLaVA---the orthogonal restriction, while a formal limitation, does not break the practical
> predictions. A fully general treatment is left to future work.

**（T7）Corollary 5 的展开**（现压成一句）：

> Paper~2 is recovered as the retrieval-manifold specialization of the general framework: setting
> $K = \{\text{vision}, \text{text}\}$, $E = DG^*$, $u = \nabla L_{\mathrm{InfoNCE}}$ yields the ODE
> $d(DG^*)/dt = \alpha - \beta(DG^* - DG_0)$ as a natural special case.

### 5.2 来自 `discussion.tex`

**（D1）Future Directions 被压掉的两条**（task-12 允许压到 2 句，故正文只留 2 条）：

> (2) \textbf{Continual learning}: comparing $\Gamma$ across tasks could predict which orders minimize
> alignment degradation. (4) \textbf{$\Gamma$-guided PEFT design}: configuring LoRA placement and rank
> automatically before training would realize the zero-shot design promise.

**（D2）Rank Scaling 的收尾句**：

> A direct measurement of $\|g_v\|$ across ranks on LLaVA would determine whether gradient saturation holds
> in the decoder-based setting; we leave this to future work.

### 5.3 来自 `conclusion.tex`

无段落被移出（只做措辞压缩）；`Reproducibility` 声明**完整保留**。

---

## 6. 🔴 结构性结论：**7 页约束不在我这四节**

### 6.1 实测的边际关系

| 状态 | 全稿字符（7 个 tex） | 页数 |
|---|---|---|
| 压缩前 | 64,835 | 11 |
| 压缩后 | 56,957 | 10 |

⇒ 本轮删掉 **7,878 字符只换来 1 页**（边际 ≈7,900 字符/页）。按 `_p509` 的平均口径
（≈5,696 字符/页）估算，**再删 3 页还需 ≈17,000 字符**，两个口径互相印证（17,087）。

### 6.2 为什么这 17,000 字符不该从我这四节出

现全稿 56,957 字符的分布：

| 文件 | 字符 | 折合页 | 归属 |
|---|---|---|---|
| `main.tex`（题目/摘要/声明） | 4,652 | 0.82 | 不可压（声明类） |
| `sections/experiments.tex` | **27,847** | **4.89** | **Lead 正在改** |
| `sections/theory.tex` | 9,805 | 1.72 | 本任务 |
| `sections/discussion.tex` | 4,542 | 0.80 | 本任务 |
| `sections/introduction.tex` | 4,057 | 0.71 | 本任务 |
| `sections/related_work.tex` | 3,360 | 0.59 | 不在本任务 |
| `sections/conclusion.tex` | 2,751 | 0.48 | 本任务 |

**两次反证**：

1. **把我这四节整节删光**（−21,155）⇒ 35,802 字符 ≈ 6.3 页。也就是说，**即使 Theory、Introduction、
   Discussion、Conclusion 一个字都不剩，也才刚刚够 7 页** —— 这显然不是可投的稿子。
2. 反过来，**要保我这四节在 21,155**，则 `main + related_work + experiments` 必须从 35,859 降到
   **18,715**（−48%）。其中 `experiments.tex` 需从 27,847 降到约 12,000–15,000。

⇒ **结论：7 页的真正空间在 `experiments.tex`（4.89 页）。** 请 Lead 据此调整分工。

### 6.3 我这四节的"硬下限"在哪

四节从 29,038 压到 21,155 已是**只压措辞、未删任何结论/数字**的结果。剩余 21,155 字符里，
task-12 列为"必须保留"的部分占绝大多数：

- 4 个定理/引理环境 + 定义 + 4 个行间公式（含 markup）；
- R1–R5 **六条**逐条（R3$'$ 是第 4 条）；
- R3$'$ 的显式假设 + 反例 $\|\nabla E\|^2$、Lemma~\ref{lem:r3-not-r3p} 的反例 $S=\|x\|^2$；
- Corollary 2 的**两种预算口径** + $c_k$ 定义 + $655{,}360$ / $247{,}296$ / $2.65\times$；
- $\mathrm{Var}(\Gamma)/\mathrm{Var}(H)>20\times$、$\varepsilon_{\mathrm{proj}}<0.05$、$r=-0.27$、$k=0.088$；
- $+3607\pm514$ vs $+2241\pm1291$、$10^3$–$10^4$、$|\Gamma_v|$、$<1\%$；
- `bracketed` + CI 跨零 + $p=0.100$ + $r_c$ 属协议；
- 12 项 limitation 的**每一条结论**（正文现有 6 条，见 §7）；
- conclusion 的四处已修口径 + "negative and we state them as such" + "without searching" + 126 runs；
- `Reproducibility` 声明（约 350 字符，不可压）。

**若 Lead 仍要求四节 ≤12,600**，则必须从上面这份清单里砍 —— 那等于删结论，与 task-12 的纪律冲突。
**我按纪律停手并如实报告**（task-12："若某节压不到目标量而不删结论，如实报告（不要为达标而删结论）"）。

### 6.4 可选方案（供 Lead 决策，均给出数字）

| 方案 | 做法 | 结果 |
|---|---|---|
| **A（推荐）** | `experiments.tex` 压到 ≈12,000（−15,847）；`related_work` 压到 ≈2,400（−960）；我四节再压 ≈1,000 | ≈40,000 字符 ≈ **7.0 页** ✅ |
| B | `experiments.tex` 压到 ≈15,000；`main.tex` 压到 4,000；我四节再压 ≈1,500 | ≈42,500 ≈ 7.4 页 ⚠️ |
| C | 把 `experiments.tex` 的**一整节**（如逐块 Γ/rank 表或消融）移入 supplementary | 每移出 5,700 字符 ≈ 省 1 页 |
| D | 保持四节 21,155，接受 **10 页**投稿 | 与 PRL ≤7 页硬约束冲突，不可行 |

---

## 7. 与任务描述的差异（如实记录）

1. **"12 条 limitation" 与文件不符**：`sections/discussion.tex` 现有 **6 条**（First–Sixth，编号已改为 (1)–(6)）；
   `sections_full/discussion.tex`（完整版冻结件）同样 6 条。**6 条结论全部保留**。
   若 Lead 的"12 条"包含 `experiments.tex` 里的 limitation，那部分不在我的写范围。
2. **任务给的目标值**：见 §2 与 §6.3，未达标项已逐项说明原因，未删任何结论。
3. **`\beta` 出处**：`runs[90]` / $R^2=0.951$ / median $0.072$ over 96 fits 位于
   `experiments.tex:182–185`（Lead 的文件），**theory 未写回 `CLIP-derived β=0.137`**（§3.2 已验证为 0）。
4. **本次未触碰**：`experiments.tex`、`main.tex`、`related_work.tex`、`supplementary/`、
   `sections_full/`、`main_full.tex`、`outputs/`（`git status` 可核）。

---

## 8. 复现命令

```powershell
# 1) 修复断头命令（幂等；已修完则报 0）
python tools\_p512_repair_severed_commands.py            # 预演
python tools\_p512_repair_severed_commands.py --apply    # 写入（白名单 4 文件）
python tools\_p512_repair_severed_commands.py --scan     # 只读：全树剩余（含 main/related_work）

# 2) 四节压缩（幂等：已就位则 +0）
python tools\_p513_compress_p3_sections.py               # 预演 + 逐节量测 + 断言
python tools\_p513_compress_p3_sections.py --apply       # 写入
python tools\_p513b_diag_sections.py                     # 逐小节字符分布（只读）

# 3) 验证
python tools\_p497_scan_contradictions.py                # 需处理 0 处
python tools\_p503_fix_literal_n_correct.py              # 全稿字面 \n = 0
python tools\_p509_calibrate_pages.py                    # 页数 / 字符预算

# 4) 编译
cd paper3\paper_ieee
pdflatex -interaction=nonstopmode main.tex ; pdflatex -interaction=nonstopmode main.tex
bibtex main
pdflatex -interaction=nonstopmode main.tex ; pdflatex -interaction=nonstopmode main.tex
```
