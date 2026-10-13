# Paper A 图来源清单（Figure Provenance）

> 更新：**2026-10-05** ｜ 复核：`python tools\_write_figure_provenance.py --apply` 会重写本文件；
> 图本身用下面各行的脚本重跑即可复现。

## 结论

**12 张图全部来源明确、可重跑。** 每张都有仓库内的生成脚本与源 JSON。
脚本在**写图前先断言正文主张**——数据不符即报错，不会画出与正文不一致的图。

## 清单

| 图 | 生成脚本 | 源数据 |
|---|---|---|
| `fig1.png` | `tools/_pa_rebuild_figs_rest.py`（`fig_overview`） | `outputs/flickr30k/{baseline_full_ft,rq2_text_only,rq2_both}/gap_history.json` + `outputs/flickr30k_seeds/rq2_text_only/seed*/gap_history.json` |
| `fig1_ode_fits.png` | `tools/_pa_rebuild_figs_rest.py`（`fig_ode_fits`） | `outputs/theory/beta_pilot/*/seed*/dg_star_history.json` |
| `fig2.png` | （本阶段前已重绘） | 归档 JSON |
| `fig2_v5_falsification.png` | `tools/_pa_rebuild_figs_rest.py`（`fig_k`） | `outputs/analysis/k_remeasured_both.json` |
| `fig3.png` | `tools/_pa_rebuild_figs_rest.py`（`fig_alpha`） | `outputs/flickr30k/alpha_*/gap_history.json` |
| `fig4.png` | `tools/_pa_rebuild_figs_rest.py`（`fig_crossmethod`） | `outputs/theory/adapter/adapter_all_results.json` |
| `fig4_effective_rank.png` | `tools/_pa_rebuild_figs_rest.py`（`fig_k`） | `outputs/analysis/k_remeasured_both.json` |
| `fig8_weight_svd.png` | （本阶段前已重绘） | 归档 JSON |
| `fig9_noise_sensitivity.png` | （本阶段前已重绘） | 归档 JSON |
| `fig10_layered_ft.png` | `tools/_pa_rebuild_fig10.py` | `outputs/layered_ft_results.json` |
| `fig12_zeroshot_more.png` | `tools/_pa_rebuild_fig12.py` | `outputs/zeroshot_extra.json` |
| `fig14_adapter_layered.png` | `tools/_pa_fix_fig14_title.py` | `outputs/adapter_layered_results.json` |

## 重绘时发现并修正的主张—数据不符（2 处）

### ① `fig12` 零样本：`0.8 pp` → 分变体

原正文与图注称"**all fine-tuned variants stay within 0.8 percentage points** of the frozen baseline"。

| 数据集 | 变体 | 值 | Frozen | 偏差 |
|---|---|---|---|---|
| DTD | Text-only | 43.33 | 43.27 | +0.06 |
| DTD | Both | 42.53 | 43.27 | +0.74 |
| Food101 | Text-only | 80.67 | 80.60 | +0.07 |
| **Food101** | **Both** | **79.73** | 80.60 | **+0.87** ← **超 0.8** |

**已改为**：text-only ≤ 0.1 pp、both-position ≤ 0.9 pp。（`tools/_pa_fix_zeroshot_claim.py`）

### ② `fig14` Adapter 分层：`frozen-level CG` → 如实陈述

原图注称"Training an Adapter on the text side only **reaches frozen-level CG**"，
图题称"**Text-only Also Preserves Alignment**"。

| 配置 | CG | R@1 | CG 升幅 |
|---|---|---|---|
| Frozen | 0.8143 | 0.6850 | — |
| Adapter Text-only | 1.0644 | **0.0600** | **+0.250** |
| Adapter Text+Vis | 1.3168 | 0.0050 | +0.503 |

**数据：两者 CG 都高于 frozen、R@1 都塌陷**——谈不上"frozen-level"或"preserves alignment"。
**已改为**：如实报告两者升幅（+0.25 vs +0.50，比值 2.01×）与 R@1 塌陷；
**并保留**原图注中**正确**的两点披露（"layered-configuration comparison"、
"the aggregate cross-dimension comparison does not reproduce a text-only advantage for Adapter"）。
（`tools/_pa_fix_fig14_caption.py`、`tools/_pa_fix_fig14_title.py`）

## 复现

```powershell
# 只核对主张、不写图
python tools\_pa_rebuild_figs_rest.py --dry
python tools\_pa_rebuild_fig10.py
python tools\_pa_rebuild_fig12.py

# 写图
python tools\_pa_rebuild_figs_rest.py --apply
python tools\_pa_rebuild_fig10.py --apply
python tools\_pa_rebuild_fig12.py --apply
python tools\_pa_fix_fig14_title.py --apply
```

> 注：绘图用 `D:\Anaconda\envs\pytorch\python.exe`（装有 matplotlib）。

## 教训

**重绘不是"把旧图画一遍"，而是"用归档数据重新核对正文主张"。**
本轮 9 张里有 **2 张**的主张经不起核对——若只把旧图原样重画（或干脆不重绘），
这两处会一直留在稿子里。**先断言、后画图**是本轮得到的最有价值的工作方式。

---

## 2026-10-06 追加：图例遮挡、配色统一、以及一处**真实表格溢出**

> 操作者指出："**表格溢出的部分**"、"**图片有的图例会挡住图片**"、"**图片的配色不高级**"。

### A. 表格溢出（**真越界**，已修）

我先前曾判断 `Overfull \hbox` 是"度量噪声"——**那次判断是错的**。
改用**像素法**（`tools/_measure_textblock.py`：把页面渲染成位图，量非白像素范围），
证明**确有三处真越界**：

| 表 | 原超出 | 修法 |
|---|---|---|
| `tab:position_strict` | **+97.9 pt** | 标签缩短（`CLIP B/32`）、`\footnotesize`、`\tabcolsep 4pt`、`@{}` 去边距 |
| `tab:phase2` | +20.9 pt | 同上 |
| `tab:generalization` | +20.9 pt | 同上 |

**修后实测**：右界范围 **476.6 ~ 478.1 pt**（版心右界 476.6）→ **无页越界**。
脚本：`tools/_fix_wide_tables.py`、`tools/_measure_textblock.py`。

### B. `fig4.png` 曾是**坏图**（已重做）

| 项 | 原图 | 现图 |
|---|---|---|
| 内容 | Adapter **β vs dim** | **跨方法比较**（图注声称的） |
| **图例** | **`False` / `True`**（布尔值直接当标签） | `LoRA` / `Adapter` |
| y 轴 | 到 **68** | ΔCG（−0.05 ~ +0.23） |
| 数据 | β 中位数 **0.50**、最大 **337** → **拟合失败值** | `outputs/analysis/adapter_common_baseline.json` + `outputs/strict_freeze` |

**新图**（`tools/_pa_rebuild_fig4_crossmethod.py`）：横向柱，LoRA 三臂
（−0.047 / −0.026 / +0.011）vs Adapter 两臂（+0.185 / +0.229），零线标出，图例置于轴外。
**这正是图注声称的模式**：LoRA 保对齐、Adapter 无一致的 text-only 优势。

### C. 配色统一为 **Okabe-Ito**（色盲友好国际标准）

定义在 **`tools/figure_style.py`**（含语义映射，保证同一概念跨图同色）：

| 语义 | 色值 |
|---|---|
| text-only / LoRA / 实测 | `#0072B2` 蓝 |
| both / Adapter / 预测对照 | `#D55E00` 朱红 |
| vision-only | `#009E73` 绿 |
| Frozen / 基准 | `#666666` 灰 |

**并加冗余编码**（线型 / 斜纹）——灰度打印或色觉异常读者仍可区分。
脚本：`tools/_pa_unify_figure_style.py`、`tools/_pa_apply_palette_to_overflow.py`、
`tools/_pa_fig1_semantic_colors.py`。

### D. 图例遮挡整改（逐张目视复核）

| 图 | 改动 |
|---|---|
| `fig4` | `lower right`（**压在柱上**）→ **轴外上方** |
| `fig12` | 轴内 → **轴下方**（数据柱从 0 起，轴内无空白） |
| `fig14` | `center right` → **左上** |
| `fig1` | 图例在空白区；**加线型冗余编码**（Full FT 点线 / text-only 实线 / both 虚线） |
| `fig10` / `fig2_v5_falsification` / `fig4_effective_rank` | 图例均在空白区，复核通过 |

---

## 2026-10-06 追加：字体统一为 Times New Roman，尺寸精确对齐

> 操作者："**图片啥的文字也要 times new roman，然后大小你要调整好**"

### 问题（实测）

| 项 | 现状 | 应为 |
|---|---|---|
| **字体** | matplotlib 默认 **DejaVu Sans**（`pdffonts` 实测） | **Times New Roman**（与正文一致） |
| **尺寸** | 各图在**任意画布**画出、LaTeX 再缩放，且**倍率各不相同**（`fig8` ×0.28、`fig10` ×0.48、`fig1` ×0.75） | **按最终尺寸出图，1.00×** |

**→ 同一张稿子里图的字号相差 3 倍**——这正是"大小没调整好"的表现。

### 修法

1. **`tools/figure_style.py`** 统一配置：
   - `font.family = serif` + Times 系列；`mathtext.fontset = stix`（与 Times 同源）；
   - 字号按**最终尺寸**定：刻度/轴标签 **9 pt**、图例 **8 pt**（均 ≥6 pt）；
   - `savefig.bbox = None` + `constrained_layout`——**避免 tight bbox 按内容外扩**
     （实测 `fig8` 曾因此偏大 1.46×，反而要 LaTeX 再缩 0.68×）。
2. **按 LaTeX 里的实际宽度出图**（`\textwidth = 342.7 pt = 4.760 in`，像素法实测）：
   `0.88\textwidth → 4.189 in`、`0.78\textwidth → 3.713 in`；
3. **同时导出 PDF 矢量版**（供后续把 LaTeX 从 PNG 切到矢量）。

### 结果（实测）

**尺寸**：12/12 图**缩放全部 1.00×**（目标与实际差 ≤0.003 in）

**字体**：`pdffonts` 实测全部为 **TimesNewRomanPSMT**
（数学符号为 STIXGeneral，与 Times 同源）

### 踩坑记录（同一类作用域错误连犯三次）

| # | 错误 | 原因 |
|---|---|---|
| ① | `NameError: figsize_full` | 共享样式在 `main()` 内 import，但绘图在**模块级函数**里 |
| ② | `NameError: sys` | 把 `sys.path.insert` 插到了 `import sys` **之前** |
| ③ | 图仍是 DejaVu | `apply_style()` 在重写 import 块时**被删掉**（4 个脚本从未调用） |

**对策**：
- import 全部提到**模块层**并**固定顺序**；
- 加 **import 冒烟测试**（`_pa_fix_import_order.py`）；
- 字体用 **`pdffonts` 实测**验证——**不靠"我设了就应该生效"**。

---

## 2026-10-06 追加：附录 B 的 1×3 面板图**拆为单面板**（操作者建议）

> 操作者："**可以分成三个图片啊，没必要挤在一起**" —— **对**。

### 背景

`fig8` 与 `fig9` 是 **1×3 面板**，却挤在 **3.713 in 宽**的画布里 → **每面板仅 1.24 in 宽**，
标题/轴标签/图例必然重叠。这两张图因此一度**完全不可读**。

### 拆分结果

| 原图 | 拆成 | 内容 |
|---|---|---|
| `fig8_weight_svd` | **`fig8a_rank_delta`** | 严格冻结下视觉/文本侧**有效秩变化** |
| | **`fig8b_budget`** | **可训参数预算**（严格 vs 旧协议，log 轴） |
| | **`fig8c_vision_untouched`** | **收到更新的视觉张量数**（对照冻结总数） |
| `fig9_noise_sensitivity` | **`fig9a_noise_sweep`** | 修正探针：按 σ 分组的 R@1 变化 |
| | **`fig9b_sigma0_control`** | **σ=0 对照**（必须精确为 0） |
| | **`fig9c_ratio`** | 测得比值 **0.76×** vs 旧文声称的 **2.6×** |

每张 **3.710 × 2.670 in**，占版心宽 `0.78\textwidth`，**单张仅占版心高 31%** → 一页绰绰有余。

### 同时修正 `fig8` 原图注的**两处错误**

| 错误 | 实际 |
|---|---|
| 写 "**(A) … (B--D) …**"（**四个**面板） | 只有 **A/B/C 三个** |
| 描述为 "Mean $\|\Delta W\|_F$ per encoder … **SVD of weight updates**" | 实际画的是**有效秩变化、可训预算、视觉张量数**——**完全不符** |

拆开后各图注**逐张如实描述**，不再有面板字母错配。

### 旧的合并图

`fig8_weight_svd.*` 与 `fig9_noise_sensitivity.*` **已移入 `paper合/figures/_superseded/`**
（不删，保留可回溯），因为 LaTeX 不再引用、留着会误导。

---

## 2026-10-06 追加：切矢量 PDF + 清理目录（B-3 / B-4）

### B-4：`\includegraphics` 由 `.png` 改为 `.pdf`（**矢量**）

16 张图全部已有 PDF 矢量版 → LaTeX 改用 `.pdf`，**任意缩放不糊**，期刊排版也偏好矢量。

**关键前提**：`fig1` / `fig3` 当时**缺 PDF**——因为它们的保存语句是
`fig.savefig(...)` 而非共享的 `save()`（后者才同时写 PNG+PDF）。已改为 `save()`。

**验证**：
- 编译 **0 错误**；
- `pdffonts` 确认图内字体仍嵌入；
- `pdfimages` 显示稿件 PDF 内仅剩 **4 个极小的 1-bit 位图对象**（299 ppi、约 1 KB），
  **线条 / 文字 / 坐标轴均为矢量**。

### B-3：下线图归档

| 类别 | 数量 | 处置 |
|---|---|---|
| 正文未引用的 PNG | **15** | → `figures/_superseded/` |
| 从未被引用的 SVG（8 月遗留） | **7** | → `figures/_superseded/` |

**`figures/` 现在是精确的「16 张图 × (PDF + PNG)」**，无多余文件。

### 顺带修掉打包脚本的**两个累积型缺陷**

| # | 缺陷 | 后果 |
|---|---|---|
| ① | `copytree(dirs_exist_ok=True)` **把 `_superseded/` 也打进投稿包** | 包里混入下线图 |
| ② | `srcdir` **未先清空**，而 `copytree` **只增不删** → 历次构建的旧图**累积** | zip 里多出 **33 个已下线 PNG**，虚增约 2 MB |

**修后**：`latex_source.zip` **5.4 MB → 1.1 MB**，包内 `figures/` 恰为 **32 个文件**
（16 张图的 PDF + PNG），**不含 `_superseded/`**。

> **教训**：这两个缺陷都是「**只增不删**」造成的——与正文里反复出现的
> 「只追加不核对」是同一类。**凡有累积的目录，构建前必须清空。**
