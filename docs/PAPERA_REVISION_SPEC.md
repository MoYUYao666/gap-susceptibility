# Paper A（P1+P2 合并版）整改规格

> **建立**：2026-10-01 ｜ **触发**：操作者判断 P1 大概率被拒，指示"准备 paper12 合并版的修正，在备选里"
> **对象**：`paper合/`（Paper A = **P1+P2**，Springer `sn-jnl`，28 页，8 个 section，65 文件）
> **状态**：已于 2026-10-01 从 `备选/06_归档稿件/paper合/` **移回仓库根目录**（`tools/_restore_paperhe.py`）
> —— 因为 14 个脚本用**字面相对路径**打开它，移回即恢复（依据 `备选/归档清单.txt:111–123`）。

---

## 一、范围界定（重要，先说清）

| 稿 | 内容 | 与本次整改的关系 |
|---|---|---|
| **Paper A** = `paper合/` | **P1 + P2** | ✅ **本次整改对象**。已核实**完全不含 P3 内容**（`Representation Theorem`／`Generalized Flow`／`Γ`／`counterfactual` 在 8 个 section 中均 **0 处**） |
| ap3 = `paper_ap3/` | P1 + P2 + **P3** | ⛔ **不在本次范围**。它已完成 10 轮整改、86 页就绪，但**含 P3 内容**，而 **P3 已投 PRL 在审** → 动它会引入重叠 |
| P1 = `paper/` | P1 独立版 | 在 PR 审稿中，**不动** |

**⚠️ 与既定文档的差异（需操作者确认）**：`docs/PA_P3_MERGE_PLAN.md` 记的 2026-09-04 决策是
"P1 被拒 → **Paper A 与 P3 合并**"（即目标是 ap3）。操作者本次指示为"**paper12** 合并版"（P1+P2），
**不含 P3**。本规格按**操作者本次指示**（P1+P2）编写，但**第 4 节的整改项对两者都适用**。

---

## 二、已核实的缺陷清单（Paper A 内实测命中数）

检索命令：`Select-String -Path paper合\sections\*.tex -Pattern <模式> -Encoding UTF8`

| 来源 | 缺陷 | Paper A 命中 | 修法 |
|---|---|---|---|
| `P1_ADVERSARIAL_REVIEW` [M1] | `zero vision-side updates` 这一**被存档自证为假**的图注 | **3 处** | **移植 ap3 的写法**（见 §3） |
| [M2] | 有效秩主张与自身数据相反 | **14 处** | 移植 ap3 §"Effective rank" 段 |
| [M11] | **n=81 相关性无法重建**（选样规则丢失）——却是头号数字 | **14 处** | 换 ap3 的可复现替代（见 §3） |
| [M13] | 摘要 "24%" 用单次运行口径 | **2 处** | 改 5-seed 均值 ± std（23.4% ± 0.9%） |
| [M14] | "116 experiments" 实为 **117** | **6 处** | 全篇改 117（已备脚本 `tools/_p1_count_experiments.py` 思路） |
| [M24] | 姊妹稿披露（`companion`／`wan2026`）——**状态需逐处核对** | 3 处 | 核对是否指向仍在审的稿件 |
| [M21] | `yi2025` 用**被 ICML 2026 正式版取代的预印本**（A1/A23 已修，Paper A 未同步） | 1 处 | 换 ICML 2026 正式版 |
| `PAPERHE_OVERLAP_RESOLUTION` §3 | **Adapter 行仍是"自身注入后基线"旧值**，与 P1/ap3 的冻结基线口径冲突（`$-$0.217 → +0.064`，组均值 **+0.229**，n=7） | `supplement.tex:58–64` | 统一到冻结基线（依据 `outputs/analysis/adapter_common_baseline.json`） |
| 同上 §1 | 与 P1 的 **1,053 词逐字重合**（supplement 593 / related_work 370 / empirical 90） | 19 段 | 见 §5 选型 |
| 标题 | 旧标题含 **"Causal Evidence"**，与 [M1] 的因果失效冲突 | **2 处** | 去因果化（ap3 已不用该措辞） |
| `PA_P3_MERGE_PLAN` 待办 | 旧的 116 篇目录、篇幅 28 页 vs 目标刊要求 | — | 见 §4 |

---

## 三、可直接移植的修复（ap3 已写好，有源码行号）

**这是本次整改最省力的部分**——ap3 经 10 轮整改，已把 P1 的主要缺陷处理完：

| Paper A 缺陷 | ap3 的现成写法 | 位置 |
|---|---|---|
| [M1] 冻结失效 | 「**Strict control.** The archived text-only runs trained $145{,}170{,}177$ parameters, **the vision encoder included**, so they cannot …」 | `paper_ap3/sections/04_mechanism.tex:111` |
| 噪声敏感性（同源，已撤） | 「**Noise sensitivity (withdrawn).** An earlier single evaluation … suggested …」 | 同上 `:105` |
| [M8] Adapter 基线 | 「LoRA ablations, **all measured against the frozen model** (CG$\Delta$; lower is better)」 | 同上 `:59`、`:64` |
| [M2] 有效秩 | 「**Effective rank of the embeddings.** We track the effective rank $\exp(-\sum_i p_i\log p_i)$ of the per-layer image embeddings, …」 | 同上 `:109` |
| [M11] 相关性替代 | ap3 第九轮用 `outputs/clustered_bootstrap_dg_r1.json`：**r = −0.847, 95% CI [−0.936, −0.709], 98 实验/14 簇**（可复现） | `docs/PA_P3_MERGE_PLAN.md:42` |
| LoRA 作用域披露 | 「实际运行 LoRA 注入 LLM q/k/v/o **+ vision 塔 self-attn q/k/v**（r6: 6.29M+0.88M=7.2M）；"vision frozen" 仅指基座冻结」 | `docs/PA_P3_MERGE_PLAN.md:41 ⑧` |

> **注意**：移植的是**结论与措辞**，数值与出处必须回到 `outputs/**` 复核（Paper A 的 n 与协议可能与 ap3 不同）。

---

## 四、需要新决策的事项（不能照抄）

| # | 事项 | 为什么不能照抄 |
|---|---|---|
| 1 | ~~**[M1] 两条路**~~ → ✅ **已定：走"救回因果主张"**（见 §4.1） | 严格冻结实验**已跑完且结果支持原论点** |
| 2 | **篇幅与目标刊** | Paper A 现 28 页（Springer）。若改投 Neurocomputing（Elsevier, 单盲），需换 `elsarticle` 模板；`PA_P3_MERGE_PLAN` 建议 ~40–48p |
| 3 | **§5 重合选型 (a)/(b)** | (a) 不再复制 P1 的逐行目录、改为按节汇总并指向已发表目录（**编辑上正确**）；(b) 保留数据但改列序/表头（仅绕开查重） |
| 4 | **是否并入 P3** | 见 §一：本次按**不含 P3** 执行 |

### 4.1 ✅ [M1]/[M2] 已解决：严格冻结实验支持原论点（2026-10-01 实测）

**数据源**：`outputs/analysis/strict_control_summary.json`（5 seeds/配置；实验 `experiments/strict_freeze_control.py`）

| 配置 | 可训参数 | 视觉侧非零张量 | CGΔ | R@1 |
|---|---|---|---|---|
| frozen（参照） | — | 0（199 张量） | — | — |
| **text_only** | **196,608** | **0** ✅ | **−0.0465** ± 0.0027 | 0.6238 |
| **both** | **491,520** | **0** ✅ | **−0.0258** ± 0.0031 | **0.6932** |
| vision_only | 294,912 | **0** ✅ | **+0.0106** ± 0.0039 | 0.6800 |
| ~~legacy text-only~~ | ~~145,170,177~~ | 失效 | −0.0635 | 0.6270 |
| ~~legacy both~~ | ~~131,290,881~~ | 失效 | −0.0324 | 0.7000 |

**结论（可写进论文，5 seeds 全可复现）**：
1. **严格冻结下原论点成立**：text-only 比 both 更好地降低模态间隙（−0.0465 vs −0.0258）；
2. **[M2] 同步解决**：text_only 的 `vision_rank_delta_mean = 0.0`（旧数据"压低 25–35%"是冻结失效造成的假象）；
   严格冻结后 text-only **确实保持**视觉几何 → "protect the visual encoder" **因果主张可保留**；
3. **额外诚实发现（应写进论文）**：**both 的检索更强**（R@1 0.6932 vs 0.6238）→
   **降低间隙 ≠ 提升检索能力**，两者是不同的目标。

> 📌 **这意味着 Paper A 的整改不是"撤回主张"，而是"换成受控实验"**——比最坏情况好得多。
> ⚠️ 但要注意：legacy 与 strict 的**可训参数差 700 倍**（145M vs 19.7 万），
> **两套结果不可混用于同一张表**；正文必须明确区分"legacy 未受控"与"strict 受控"两个协议。


---

## 四点五、逐项核实记录（"改对"的凭据）

### ✅ 4.5.1 实验计数：**117 正确，正文 116 是笔误**（2026-10-01 实测）

方法：解析 `paper合/sections/supplement.tex` 的 `tab:full_experiments` 表体，逐节加总并与表内 Total 行对照。

```
I. LoRA Core 30 ｜ II. Adapter 7 ｜ III. COCO Cross-Dataset 8 ｜ IV. BLIP-1 7 ｜ V. ViT-L 3
VI. Route C/D/E 16 ｜ VII. 5-Seed 20 ｜ VIII. ImageNet ZS 4 ｜ IX. ViT-B Layered 5 ｜ X. ViT-L Layered 4
XI. Adapter Layered 2 ｜ XII. Mechanism Probes 3 ｜ XIII. ZS+SigLIP 8
→ 13 节加总 = 117   ｜   表内 Total 行声明 = 117   ｜   正文 6 处写 116
```

**判定**：`117` 有**两处独立一致**（逐节加总、表内 Total），`116` 无来源 → **改 116→117**。

### ⚠️ 4.5.2 `yi2025decipher`：**"ICML 2026 正式版"无据，保留现状待核**

| 来源 | 内容 |
|---|---|
| **arXiv:2510.03268**（权威） | `citation_title` = **Decipher** the Modality Gap…: From Convergent Representations to **Pairwise** Alignment；作者 Yi, Lingjie／Douady, Raphael／Chen, Chao；`citation_date` 2025/09/27 |
| **OpenReview** | 同作者有一条 "**Decrypt** Modality Gap…: From Convergent Representation to **Pair** Alignment"，状态 **ICLR 2026 Conference Withdrawn Submission** |
| **全仓库 7 处 bib** | 均为预印本记录（`arXiv preprint arXiv:2510.03268`，year 2025） |

**发现**：`paper合/references.bib` 的 note 写 "(ICML 2026 version)"，但**查不到任何支持 ICML 2026 的权威来源**；
OpenReview 显示的是 **ICLR 2026 撤稿投稿**。`P1_REMEDIATION_LOG.md:43` 称"已增加 ICML 2026 正式版题名注"，
实际**只加了 note、未改题名与出处**，且该 note 本身无据。

**处置**：**不修改**（改成另一个无法核实的出处，是以错误替代错误）。
`116→117` 等**有据项照改**；本条**保持现状并标注待核**，需操作者或可访问出版方数据库时确认。
⚠️ 论文正文有 4 处以该文的"dimension collapse 是根因"承载论证，**该主张本身也标注为未独立核实**
（见 `P1_REMEDIATION_LOG.md:33` 对措辞的降级处理）。

---

## 五、与 P1 的 1,053 词重合处理（19 段）

分布（`tools/_overlap_scan.py paper paper合 20` 实测）：

| 位置 | 词数 / 段数 | 性质 | 改法 |
|---|---|---|---|
| `paper合/sections/supplement.tex` | **593 / 8** | 表格行体（同一批实验的同一批标签与数值） | §5 选型 (a) 或 (b) |
| `paper合/sections/related_work.tex` | **370 / 8** | 句子级复用 | 逐段改写合并稿一侧（实质不变、措辞不同） |
| `paper合/sections/empirical.tex` | **90 / 3** | 同上 | 同上 |

最大单段 **245 词**（P1 `tab:full_experiments` 的目录表体）。

**验收**：改完复跑 `python tools/_overlap_scan.py paper paper合 20`，**≥20 词重合归零**。

---

## 六、执行顺序（建议）

1. **先定 §4-1（[M1] 两条路）** —— 它决定叙事骨架，后做会返工；
2. 移植 §3 的现成写法（移植后**逐值回 `outputs/**` 复核**）；
3. 修 §2 的机械项（116→117、24%→5-seed、yi2025 正式版、Adapter 冻结基线、去 "Causal Evidence"）；
4. 处理 §5 重合（选型 + 改写 + 扫描器归零）；
5. 全量复核：`tools/audit/check_paperA.py`、`tools/audit/audit_citations.py`、
   `tools/audit/find_bib_placeholders.py`、`tools/_overlap_scan.py`、重编译 0 错误。

---

## 七、状态

- [x] **2026-10-01**：`paper合/` 移回根目录（65 文件计数一致），14 个脚本路径恢复；
- [x] **2026-10-01**：缺陷盘点完成（§二 命中数为实测）；
- [x] **2026-10-01**：确认 Paper A **不含 P3 内容**（0 处）；
- [x] **第 1 项 实验计数 116 → 117**（6 处）——三处独立证据支持 117；顺带统一 `runs`→`experiments`；
- [x] **第 2 项 零样本 `−53.3%` → `56.7 pp`**——源 JSON 实测；`CG +24%` 经核为正确，未改；
- [x] **第 3 项 Adapter 旧基线**——Paper A 无旧数值表；`validation.tex:111` 的 `−0.217` 已改 `+0.064`（见第 7 项）；
- [x] **第 4 项 去 "Causal Evidence" 标题**——实测**已不存在**（旧记录不适用当前稿）；
- [x] **第 5 项 [M1]/[M2] 因果证据线**（9 处改写）：
      · **噪声敏感性撤回**（修正探针 5 seeds 无稳定排序，ratio 0.76，paired p=0.77，σ=0 对照完美复现基线）
      · **GSNR `1.5×` → 实测 `1.41×`** + 单次测量的诚实披露
      · **有效秩**改为**严格冻结实测**（text-only 视觉侧 0 更新 / 秩变化 0.000；both −0.042；vision_only −0.059）
      · 两条**补充图已重建**（fig8、fig9，全部从归档 JSON 出图，可复现）
      · `theory.tex:98` 补漏（同句含两个旧值）
- [x] **第 6 项 [M11] 相关性**（操作者选"两套都报"）：
      · 主结果 **n=204**（`dg_r1_reproducible.json`，rule 明确）｜ DG −0.714 / CG −0.594 / partial −0.581
      · 稳健性 **n=98 / 14 簇** cluster bootstrap（r=−0.847, CI[−0.936,−0.709]）+ n=204 的 12 簇（r=−0.738）
      · **CGΔ 由 n.s. 变为显著**（r=+0.190, p=0.007）→ 如实改写
      · **fig2 重新生成**（n=204，与正文一致）
- [x] **第 7 项 [M8]+[M24]**：`validation.tex:111` 一句三病——Adapter 旧口径（−0.217→+0.064，**方向翻转，已如实改写**）、
      循环引用改为稿内交叉引用（3 处）、删除 `wan2026protect` 未使用条目（cites 42→41）；
- [x] **第 8 项 [M7] 重合改写**：**1,053 → 227 词**（`_overlap_scan.py paper paper合 20`）。

### 7.1 ⚠️ 剩余项与无法清除的部分（如实记录）

| 项 | 状态 |
|---|---|
| **重合 227 词 / 7 段** | **这是该扫描口径下的地板**。经逐段核查，剩余命中的主体是**引用键**（`\cite{liang2022mind}` 归一化后留下 "liang mind"、"schiappa robust"）与 **LaTeX 脚手架**（`\includegraphics{figures/...}`、表注、`tab:full_experiments`）。两稿引用同一批文献、使用同一批图，这些 token 序列必然相同，**继续改写散文不会降低该数**。真正的散文重合已降至约 50–80 词。 |
| **SigLIP CGΔ（+0.067 / +0.058）** | `outputs/theory/siglip/*.json` **只含梯度统计**（Γ_t=0.362、Γ_v=4.23 已核实），**不含 CGΔ**。已保留数值但**去掉"优势成立"的结论**，**待核**。 |
| **`empirical.tex:28` 的 −0.064 vs −0.032** | legacy 协议的数（与严格冻结的 −0.0465/−0.0258 不同协议）。**本轮未动**——它不在缺陷清单内，且改动会波及多处数字，需单独任务。**已在 `tab:position` 表注与 §empirical 开头披露协议性质。** |
| **`k = 0.043`（`fig:falsification` / `fig:ers` 的 \|g_v\| 对 rank 斜率）** | **无法从归档独立复算**：`norm_g_v` 只存在于 LLaVA/adapter 的 `outputs/theory/**`，CLIP 的 rank sweep 结果里没有该字段；`outputs/c3_log_dynamics.json` 的 `g_vis_slope_mean` 是 LLaVA 的负值，非此量。全稿数字审计（§7.3）未把 0.043 判为"无源"，但**本轮无法重建其计算**。**记为待核**。 |
| **图注一致性复核（2026-10-01）** | 逐条核对 17 个 caption：修掉 2 处与已改正文**矛盾**的 Adapter 图注（`fig:crossmethod`、`fig:adapter_layered`——原文称"both benefit from text-only"，而正确口径下 Adapter 无此优势）；`fig:overview` 经数据核实（Full FT +0.1994、text-only −0.0635、both −0.0324、5-seed 带 −0.0426…−0.0478）**主张成立**。 |
| **yi2025decipher 的 ICML 2026 出处** | 见 §4.5.2：无权威来源支持，**保留现状待核**。 |
| **目标刊与篇幅** | 现 28 页（Springer sn-jnl）。若投 Neurocomputing 需换 `elsarticle`；`PA_P3_MERGE_PLAN` 建议 ~40–48p。 |
| **是否并入 P3** | 按操作者本次指示**不含 P3**。 |

### 7.3 数字全量审计（2026-10-01，脚本 `tools/_pa_check_beta_claim.py`）

对全稿 **204 个唯一小数** 与 `outputs/**/*.json` 中 125,432 个数值形式做交叉比对：

> **只有 2 个数值在 outputs 中找不到对应**，且**两者都不是缺陷**：
> ① `92.8\% / 12.4\%` 是**引用文献**（`\cite{xu2026vlreasoning}`）自报的数字，本就不该出现在我们的 outputs；
> ② 补充材料的 `\beta_{\text{theor}} \approx 0.0035` 是**理论量级说明**——已核其算术**自洽**
> （"40×" 对应 fitted 0.14–0.16 的比值区间 **40×–46×**；0.14–0.16 落在 `tab:coco_ode` 的 0.093–0.284 之内），
> 且该句**已承认**"fully predictive theory … requires additional modeling"。

**结论：本稿数字溯源干净。**

### 7.4 ⏸ 可选后续实验：SigLIP 严格冻结对照（已准备，未启动）

**为什么值得做**：正文当前对 SigLIP 的处理是"保留数值但不作主张"（见 §7.1）。跑一次严格冻结对照，
可把该项从**已收窄**升级为**已验证**，并让"跨架构"主张真正站住。

**可行性已核实**：
- SigLIP 权重在本地（`models/siglip-base-patch16-224`，1.5 GB）；
- `experiments/siglip_experiments.py` 的包装类**已暴露 `vision_model` / `text_model`**——正是
  `apply_lora_to_model` 需要的接口；
- `strict_freeze()` 仅 8 行（全冻结 → 只放开 `lora_A/lora_B`）；
- 环境：`D:\Anaconda\envs\pytorch`（torch 2.9.1+cu130、CUDA 可用、`peft`/`transformers` 齐备）。

**已完成的准备**（提交 `f4281c1`）：给 `siglip_experiments.py` 加 `--strict-freeze`，
在适配器注入后、优化器建立前冻结基座，并断言可训参数 < 2e6 且视觉侧为 0；
同时修掉一处我自己的作用域错误（模块级 `run_one_siglip` 看不到 `main` 的局部变量，已改为参数传递）。

**启动前还需两项**：
1. `D:\Anaconda\envs\pytorch\python.exe -m pip install sentencepiece`（SigLIP tokenizer 依赖，当前缺失）；
2. 给 `SIGLIP_EXPERIMENTS` 加 **5-seed 支持**（该序列目前**无种子参数**，原 run 是单次；
   而要与 CLIP 严格冻结对照可比，需 5 seeds）。

**成本**：15 次全量训练（3 配置 × 5 seeds），SigLIP 比 CLIP 大，**约数小时**。

**命令（准备就绪后）**：
```powershell
& 'D:\Anaconda\envs\pytorch\python.exe' experiments\siglip_experiments.py `
    --strict-freeze --max_samples 5000 --epochs 10 --batch_size 64 --skip_full_ft
```

### 7.2 复核入口（全部可重跑）

```powershell
python tools\_pa_fix_count_117.py --apply      # 第 1 项
python tools\_pa_fix_zeroshot.py --apply        # 第 2 项
python tools\_pa_fix_correlation.py --apply     # 第 6 项
python tools\_pa_fix_m1_evidence.py --apply     # 第 5 项
python tools\_pa_fix_theory_stale.py --apply    # 第 5 项补漏
python tools\_pa_fix_validation_111.py --apply  # 第 7 项
python tools\_pa_fig8_rebuild.py                # 图重建
python tools\_pa_fig9_noise_rebuild.py          # 图重建
python tools\_pa_fig2_corr.py                   # 图重建
python tools\_pa_rewrite_overlap.py / _overlap2.py   # 第 8 项
python tools\audit\check_paperA.py             # 引用审计
python tools\_overlap_scan.py paper paper合 20  # 重合扫描
```

**终态**：28 页 ｜ 0 编译错误 ｜ 0 未定义引用 ｜ cites=41/bib=41 全匹配、无未使用。

### 7.5 2026-10-02 追加：换模板 + 两处证据错误 + 新实验

**① 两处证据错误（已修，提交 `1b59f20`）**

| # | 错误 | 证据 | 修法 |
|---|---|---|---|
| 1 | 称 SigLIP 的 pairwise sigmoid 目标不同于 CLIP 的 InfoNCE | `src/trainer.py:418-428`：**所有模型微调都用同一 InfoNCE**（`logit_scale * image @ text.T` + `cross_entropy`） | 改为"差在编码器与预训练，**微调损失相同**"；`tools/_pa_fix_loss_claim.py` |
| 2 | ODE "mean $R^2 > 0.96$" | **我的验证脚本查错了来源**：按 `R2/r2/R^2` 全仓搜到的 13 处**全来自 `outputs/llava_*`（解码器）**；CLIP 侧拟合在 `outputs/theory/**/beta_results.json` 的 **`exponential_fit.r_squared`** | 用正确来源重算：**仅 LoRA n=6，mean 0.9855（range 0.9777–0.9965）**；full_ft 组 0.9223、最低 0.8629。全文 6 处统一为"LoRA 子集 0.986"，并把 full_ft 与 OpenCLIP BitFit(0.943) **明确标为低于该区间** |

**② SigLIP 严格冻结对照（新，产物 `outputs/siglip_strict/`）**

- 协议：5000 样本 / 10 epochs / batch 64 / rank8+α16 / seeds 42,123,456,789,1024
- 严格冻结已验证：text_only 可训 **294,912**（**视觉侧 0**）；both 可训 **589,824**
- **text_only +0.0664 ± 0.0060**（R@1 0.432）vs **both −0.0114 ± 0.0059**（R@1 **0.619**）
- **配对差 −0.0778（sd 0.0033），t = −52.7，5/5 seeds 方向一致**
- CLIP 同协议对照：text_only −0.0465 vs both −0.0258，配对差 +0.0207，t = +10.0
- → **两架构方向相反**；且两者**同预算、同 seeds、同 rank、同一微调损失**
- 统计脚本：`tools/_siglip_strict_stats.py`、`tools/_crossarch_strict_stats.py`

**③ 已据此改写的正文位置**

| 文件 | 改动 |
|---|---|
| `empirical.tex:124` | 设计模式①去掉"across architectures"普适声称 |
| `validation.tex:111` | 写入 SigLIP 反例及两点后果（含"ODE 不预测分配方向"的范围声明） |
| `conclusion.tex:11` | "central message"去掉"and why it must" |
| `introduction.tex:25` | 同一处方加架构限定 |
| 四处 "text-only superiority" | 改为 "text-only position" + 范围声明 |
| 摘要 | **367 → 244 词**，去循环引用与旧值，写入架构依赖 |

**④ 模板与投稿包（提交 `03497e3`）**

- Elsevier `elsarticle`：`paper合/main_nc.tex`（`tools/_pa_to_elsarticle.py` 生成；**正文 8 个 `\input` 未改**）
- **无损性已核**（`tools/_pa_compare_versions.py`）：labels 31/31、refs 22/22、cites 39/39、引用 key 集合完全一致、无重复 input
- 编译：**39 页、0 错误、0 未定义引用、41 条参考文献**
- 新增：Highlights（5 条，最长 59 字符）、Cover Letter（2 页）、5 节声明（CRediT 9 项 + 生成式 AI，**位置在参考文献之前**）
- 投稿包：`paper合/NC_submission/`（Manuscript / Highlights.pdf+.txt / Cover Letter / latex_source.zip / README）
- 终检：`tools/_pa_final_check_nc.py`（**从 PDF 实测**）全绿；摘要 **244 词** ≤250
- ⚠️ 终检抓到：初次实测 252 词，其中 **8 词是 `pdftotext` 把首页页脚拼进摘要正文流**；剔除后合规，脚本已固化该逻辑

**⑤ 补充实验**

| 实验 | 目的 | 脚本 | 状态 |
|---|---|---|---|
| OpenCLIP B/32 (LAION-2B) 严格冻结 | 与 CLIP **同架构（patch32/768/151M）不同预训练** → 分离"骨干 vs 预训练" | `strict_freeze_control.py --model models/openclip --name oclip_` | 🏃 进行中 |
| SigLIP vision_only | 补全 SigLIP 三臂（CLIP 已有三臂） | `siglip_experiments.py --only s6_siglip_lora_vision_only`（**新增配置**） | ⏳ 排队 |
| 严格冻结 rank sweep（rank 4/16/32） | 设计模式②"更低 rank 更保对齐"此前**只在 rank 8 验证过** | `strict_freeze_control.py --rank N`（**新增参数**） | ⏳ 排队 |

排队执行：`tools/_run_extra_experiments.py --apply`（串行，避免 GPU 争用）

**脚本改动（默认值不变，既有产物语义不受影响）**：
`strict_freeze_control.py` 新增 `--model/--out-dir/--name/--rank/--alpha-mult`；
`siglip_experiments.py` 新增 `s6_siglip_lora_vision_only` 配置。

### 7.6 2026-10-03 追加：补充实验 38/38 完成，两条设计模式改写

**① 三骨干三臂图谱**（	ools/_pa_three_arm_stats.py；同协议：5000 样本/10 epochs/rank8+α16/5 seeds/同一 InfoNCE）

| 骨干 | text_only | both | vision_only | ΔCG排序 vs 检索排序 |
|---|---|---|---|---|
| CLIP B/32 (WIT) | **−0.0465** / 0.624 | −0.0258 / **0.693** | +0.0106 / 0.680 | **完全反转** |
| OpenCLIP B/32 (LAION) | **+0.0694** / 0.643 | +0.0881 / **0.680** | +0.0925 / 0.672 | **完全反转** |
| SigLIP B/16 | +0.0664 / 0.432 | **−0.0114** / **0.619** | +0.0522 / 0.341 | **一致** |

→ 两个 B/32 骨干排序逐项相同且与检索排序完全反转；SigLIP 两者都不同。**无位置优势可跨骨干迁移。**

**② 设计模式②被反证**（	ools/_pa_rank_sweep_stats.py、_pa_rank_legacy_vs_strict.py）

| rank | legacy | 严格冻结 text_only | 严格冻结 both |
|---|---|---|---|
| 4 | −0.0272 | −0.0285 | −0.0184 |
| 8 | −0.0304 | −0.0465 | −0.0258 |
| 16 | −0.0199 | −0.0598 | −0.0149 |
| 32 | **+0.0010** | **−0.0754** | −0.0032 |
| 64 | **+0.0121** | 未跑 | 未跑 |

→ 严格冻结下 text_only **单调递减**（rank 越高越降间隙），rank32 处两约定符号相反。**该规则是基座也在训练的产物。**

**③ 正文改动位置**

empirical.tex:124（设计模式①②）｜:59（rank 段落）｜:17（小节标题加约定限定）｜新增 	ab:position_strict｜alidation.tex SigLIP 段补 vision_only

**④ 复核**：NC **41 页** / Springer **30 页**、0 错误、0 未定义引用、cites 41/bib 41、摘要 244 词、终检全绿、投稿包已重建。

**⑤ 本阶段修的坑（均已加断言）**：--model 未传入 TrainConfig.clip_model（致整批白跑）｜rank sweep 共用 out-dir（致静默污染）。

### 7.7 2026-10-04 ~ 10-05 追加：`k` 修正、跨骨干实验、计数更正、图重绘、投稿前审核

**全部改动均由 `tools/` 下带断言的幂等脚本完成，可重跑复核。**

#### 7.7.1 `k = 0.043` 从全稿清除（5 处）

重测（both 臂，严格冻结，3 seeds/rank，$r\in[1,64]$）：$\|g_v\|$ 极差 **10%**（12.75–14.09），
而 $\sqrt r$ 预测应变化 **8 倍**。**线性拟合给 0.257，且相邻区间局部斜率正负交替**
（−0.20/+0.89/−0.35/+1.39/−0.40）→ **无可辨趋势，斜率不应报**。
改为"**区间 10% vs $\sqrt r$ 预测 8 倍**"。详见 `docs/K043_INVESTIGATION.md`。

- 脚本：`tools/_pa_fix_k_slope.py`、`tools/_pa_fix_k_slope2.py`
- 数据：`outputs/analysis/k_remeasured_both.json`（`tools/_pa_remeasure_k.py`）

#### 7.7.2 跨骨干严格冻结实验完成（95 个 run）

three backbones × 双 rank × 各臂。**权威分析** `tools/_pa_rank_analysis.py`（配对检验）：

| 骨干 | 臂 | r8−r4 | t | 方向 |
|---|---|---|---|---|
| CLIP | text_only | −0.0192 | −7.96 | r8 更小 |
| CLIP | both | −0.0065 | −2.88 | r8 更小 |
| OpenCLIP | text_only | −0.0112 | −5.86 | r8 更小 |
| **OpenCLIP** | **both** | **+0.0042** | **+1.09** | 例外（**不显著**） |
| SigLIP | text_only | −0.0166 | −3.79 | r8 更小 |
| SigLIP | both | −0.0204 | −2.57 | r8 更小 |

→ **5/6 同向且显著**。**位置排序按骨干分组**：CLIP 6/6、OpenCLIP 2/2 为 `text_only` 更小，
**SigLIP 2/2 相反** → 8/10。

#### 7.7.3 实验计数更正（**两轮**）

| 口径 | 值 |
|---|---|
| 附录目录（13 类机理 + XIV 类严格冻结） | **212** |
| ODE 拟合 | 162 |
| **全文合计** | **374** |

- **第一轮**：补上先前**完全未计入**的 95 个严格冻结对照 —— 而那正是位置效应结论的**唯一可靠依据**
  （legacy 约定下 text-only 臂实际训练约 1.45 亿参数）。
- **第二轮（最终确认时发现）**：目录表 `Total` 一度被改成全文字口径 **374**，**与表内求和 212 不符**；
  且附录说明把严格冻结**既算进目录又单列（重复计数）**。**已修正为 212**，说明改为
  "212 catalogued here + 162 in Section~\ref{sec:validation} = 374 in total"。
- **另修**：两版 `main*.tex` **摘要**里残留的旧计数 **278**（第一轮只改了 `sections/*.tex`，漏了主文件）。
- 核算脚本：`tools/_check_catalog_sum.py`（**断言"求和 = Total"**）、`tools/_verify_experiment_counts.py`

#### 7.7.4 图来源重绘（9 张，**12/12 现全部可溯源**）

先前审计：12 张里仅 3 张可溯源，其余 9 张由 **2026-08-22 已不存在的脚本**产出。
现已全部重绘，每张有仓库内脚本 + 明确源 JSON。详见 `docs/PAPERA_FIGURE_PROVENANCE.md`。

**重绘捕获 2 处主张与数据不符**（这才是重绘的价值）：

| 图 | 原主张 | 数据 | 处置 |
|---|---|---|---|
| `fig12` | "all fine-tuned variants within **0.8 pp**" | Food101/both **0.87 pp** | 改为分变体（text-only ≤0.1、both ≤0.9） |
| `fig14` | "**reaches frozen-level CG**"；图题"Text-only Also Preserves Alignment" | Adapter text-only CG **+0.250**、R@1 **0.06**；both +0.503、0.005 | 图注与图题改为如实陈述；**保留**原图注中正确的两点披露 |

**工作方式**：每个重绘脚本**先断言正文主张、再画图**——数据不符即报错。

#### 7.7.5 投稿前审核（`docs/PAPERA_PREFLIGHT_AUDIT.md`）

- 修 **1 项实质缺陷**：`introduction.tex` 残留无条件声称"text-only **overwhelmingly preserves** …
  **117 experiments on five architectures**"（正文已记录 SigLIP 反转；且那 117 个多在 legacy 约定下）。
  改为"holds where the comparison isolates the adaptation site, **but not universally**"。
  **发现方式**：新增的**范围词扫描** `tools/_extract_claims.py`（288 句命中 76 条）。
- 修 **4 项审计工具自身缺陷**：终检脚本引用计数只认数字制（在 44 条文献上报"0 处"）、
  preflight 把 `(fig|tab)` 一起数、漏数 `longtable`、以及**我自己的三次快速断言**。

#### 7.7.6 本阶段我自己的错误（如实记录，供复查）

| # | 错误 | 发现方式 |
|---|---|---|
| 1 | 把 CLIP 的"更负"与 SigLIP 的"更小"当成**相反方向** | 配对检验 |
| 2 | 仅凭 2 个骨干断言"rank 效应**跨骨干成立**"（**曾写入正文**） | OpenCLIP 跑完后推翻 |
| 3 | 断言"OpenCLIP 两臂都与另两个骨干相反" | 其中一臂 **t=+1.09 不显著** |
| 4 | 给 `fig10` 设断言时**臆想了正文没有的主张** | 断言失败，回读正文 |
| 5 | 把 `Overfull \hbox` 误判为"重绘的图太宽" | 目视 page 10 + `pdftotext -bbox` 实测：**无越界** |

**共同根因**：数据未齐/未读原文就下结论。**对策**：分析固化脚本 + 配对检验 + 先读正文再设断言。

#### 7.7.7 最终确认（全绿）

| 项 | 结果 |
|---|---|
| 编译（从零，两版） | NC **49 页** / Springer **33 页**，**0 错误、0 未定义引用** |
| 引用 | cites **44** = bib **44**，缺失 0、未使用 0；PDF 中作者-年份引用 **51 处** |
| 结构 | 悬空 `\ref` **0**、重复 label **0**、占位符 **0**、图文件缺 **0**、图 12/12、表 8/8 |
| 摘要 | **244 词** ≤250，两版一致 |
| 声明 | 5 节齐备且位于参考文献之前 ｜ Highlights 5 条、最长 59 字符 |
| 核心主张复算 | 严格冻结 5-seed 方向+排序 ✅；`R² > 0.96` ✅ |
| 图来源 | **12/12** ✅ ｜ `k=0.043` 残留 **0** ✅ |
| 投稿包 | 已重建，`tools/_pa_final_check_nc.py` **全绿** |

#### 7.7.8 复核入口（本阶段新增）

```powershell
python tools\_check_catalog_sum.py           # 目录表求和 = Total（带断言）
python tools\_verify_experiment_counts.py    # 三段口径核算
python tools\_count_strictfreeze_runs.py     # 严格冻结 run 盘点
python tools\_pa_rank_analysis.py            # 三骨干 rank 配对检验
python tools\_pa_rank_matrix.py              # 骨干 × rank 矩阵
python tools\_extract_claims.py --apply      # 主张提取（措辞审核）
python tools\_audit_paperA_preflight.py      # 新面审计
python tools\_pa_rebuild_figs_rest.py --dry  # 图主张核对（不写图）
python tools\_write_figure_provenance.py --apply
```
