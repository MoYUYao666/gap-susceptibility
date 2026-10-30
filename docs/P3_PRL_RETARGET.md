# P3 → Pattern Recognition Letters：改投包（2026-09-26 完成）

> 背景与选刊依据见 **`docs/FAST_PUBLICATION_PLAN.md`**（§6 候选表、§8.2 首投链）。
> 目标：**6 个月内见刊、APC £0**。P3 是唯一无在投冲突的稿件（TNNLS 已拒，明确"不要再投修改版"）。
> ✅ **结果：已于 2026-09-26 16:22 投出 —— `PRLETTERS-D-26-02378`（Pattern Recognition Letters，Regular Article）**。

---

## 一、产物清单

| 文件 | 内容 | 状态 |
|---|---|---|
| `paper3/paper_ieee/main.tex` | 稿件源（作者信息已恢复 + 四项声明已补） | ✅ 编译通过 |
| `paper3/paper_ieee/main.pdf` | **11 页**，0 error / 0 undefined / Overfull>10pt = 0 | ✅ |
| `paper3/paper_ieee/cover_letter_prl.tex` / `.pdf` | 投 PRL 的封面信（**2 页**，含拒稿史披露） | ✅ |
| `paper3/paper_ieee/title_page_prl.tex` / `.pdf` | 可选标题页（**1 页**，含 ORCID 与全部声明） | ✅ |

**保留未动**（TNNLS 时期的材料，作历史留档）：`title_page.docx`、`cover_letter.docx`、`conflict.docx`、
`main_submission.zip`、`main_submission_old.zip`。

---

## 二、本次改动的三处（及依据）

### 1. 恢复作者信息（原为双盲匿名块）
- **改动**：`main.tex:24-30` 的 `Author Name Suppressed for Double-Anonymous Review` → 真实署名与单位
  （Hongrui Wan，School of Electronics and Computer Science, University of Southampton，`hw4c24@soton.ac.uk`）。
- **依据**：**PRL 是 single anonymized**（对照 Neurocomputing Guide 明文 "single anonymized review process"；
  IEEE TNNLS 才要求双盲）。双盲块照搬会把作者藏起来，属**格式错误**。
- **验证**：编译产物中 `Hongrui Wan` ×1、`Southampton` ×2、`Suppressed` ×0。

### 2. 补入 PRL 要求的四项声明（原稿没有——TNNLS 时期放在单独 title page）
- **依据**：PRL Guide 明确要求 **Declaration of competing interests**、**Funding sources**、
  **Declaration of generative AI use**、**Data statement**（本地官方 Guide 存档）。
- **位置**：`main.tex` 中 `\appendix` 之后、`\bibliographystyle` 之前。
- **验证**（`pdftotext -raw`）：四项声明标题依次位于 L1068/1072/1075/1082，**全部在 `REFERENCES`（L1096）之前** ✅。
  ⚠️ **验证注意**：IEEEtran 把 `\section*` 渲染为**全大写**，用原大小写检索会假报"缺失"——本次就踩过。
  可靠做法是 `pdftotext -raw` 或检索正文特征句。

### 3. 封面信（新建 `cover_letter_prl.tex`）
- 结构：投稿声明 → 论文做了什么 → **为什么投 PRL**（引其 Guide 原话 "rapid publication of concise articles"）
  → 证据 → **拒稿史披露** → 声明 → 落款。
- **拒稿史如实披露**：写明曾投 `IEEE TNNLS`（`TNNLS-2026-P-50569`）、**2026-09-03 被拒**。
  ⚠️ **依据与限度**：**PRL 的 Guide 并不要求披露拒稿史**（只有三条常规声明），但**主动披露更稳**——
  对照 JOE 那次是**强制**披露 + 附决定信（`docs/A23_JOE_MIGRATION.md`）。本信自愿披露，不附决定信。

---

## 三、封面信中的数字已逐条回核（项目铁律）

| 封面信断言 | 稿件对应 | 结果 |
|---|---|---|
| 190 runs = 181 sweep + 9 block-level | `conclusion.tex:7` 同表述 | ✅ |
| critical rank $r_c \in [5,6]$ | `discussion.tex:11`、`experiments.tex` 多处 | ✅ |
| "in LLaVA **but not** Qwen-VL" | `experiments.tex:131` 原文 "in LLaVA but not Qwen-VL: architectural differences…" | ✅（按原文措辞改写） |
| $30\times$ | `experiments.tex:270/279`："Random allocation suffers $30\times$ larger **standard deviation** ($808$ vs.\ $27$)" | ✅（原写"reduction"语义不准，已改为原文口径） |
| sample sizes 16–256 | 摘要与正文 | ✅ |

> 初稿曾写 "…reduction in allocation uncertainty" 与 "absent on Qwen2-VL-7B"，**两处都与原文字面不符**，已按稿件原文改正。
> 这正是"封面信数字必须回稿核对"的价值。

---

## 四、标题页的改动（**已按操作者指示定稿**）

| 项 | 旧 `title_page.docx` | 新 `title_page_prl.tex` | 说明 |
|---|---|---|---|
| 算力致谢 | "cloud GPU resources (**NVIDIA A800**)" | ✅ **保持 A800**：改为 "cloud GPU resources (**NVIDIA A800**) and a local workstation GPU (**NVIDIA RTX 4060**)" | **操作者 2026-09-26 确认：A800 确实使用过**；并按指示"**只写 A800 和 4060**"（不写 RTX 4080，即使云端实测记录为 4080 SUPER 32 GB） |
| AI 披露依据 | "Per IEEE policy… (**Section K of the TNNLS Information for Authors**)" | 改为期刊中性表述（PRL Guide 的 *Declaration of generative AI use*） | 改投后引用 TNNLS 的作者须知不合规 |

> 📌 **一次自我更正留档（避免以后再"自作聪明"）**：我最初**误判**此处为事实性错误——依据是 `HANDOFF.md:425` 的
> 云端实测记录（"autodl 实例实际是 RTX 4080 SUPER 32760 MiB"），据此把致谢改成了 4060 + 32GB RTX 4080。
> **该判断是错的**：操作者确认 **A800 确实使用过**（很可能用于更早的一批云端实验，其记录未进 HANDOFF）。
> 已按操作者指示改回 **A800 + 4060**。
> **教训**：仓库里的"实测更正"记录**只覆盖它记录的那一批实验**，不能据此推断**整个项目**没用过某硬件——
> 把局部记录当成全局事实，是这次误判的根因。

---

## 四之二、仍未处理的一处不一致（**留待操作者决定，未擅自改**）

仓库里另有 **11 处**把云端 GPU 写成 A800 或把云端写成 4080 的文件，彼此并不完全一致：

| 文件 | 现写法 | 与"只写 A800 和 4060"的关系 |
|---|---|---|
| `paper3/paper_ieee/sections/experiments.tex:10` | "Qwen-VL on a cloud **A800** (80GB), ~1–2 min/run (~\$7.5 total)" | ✅ 与 A800 一致（**已投稿件，本次未改动**） |
| `paper_ap3/sections/06_crossarch.tex:22` | "cloud **A800** (80GB) … ~\$8 total" | ✅ 一致（未投，未改动） |
| `paper3/{paper,paper_ICLR_backup}/sections/experiments.tex` | "cloud NVIDIA **A800** (80GB)" | ✅ 一致（历史版本） |
| `docs/CLOUD_RUNBOOK.md:44,57` | "**A800/A100 80GB** 单卡"、"吞吐低于整卡 A800" | ⚠️ 规划文档，非实测 |
| `HANDOFF.md:701`（环境节） | "RTX 4060 8GB (本地) / **A800 80GB** / RTX 5090 (云端)" | ⚠️ **"RTX 5090" 无实测依据**；且此处把 A800 与 5090 并列，含义不清 |
| `HANDOFF.md:425/457`（云端实测节） | "**RTX 4080 SUPER，32760 MiB**" | 与 A800 的说法**并存**——很可能对应**不同批次**的实验 |
| `exp/README.md:69`、`exp/qwen_gap_surgery.py:21`、`paper2/TODO_EXPERIMENTS.md:3,85`、`paper3/FOR_ADVISOR.md:85`、`paper3/PAPER3_EXPLAIN.md:104` | A800 / A100 作为**推荐或规划**硬件 | ⚠️ 规划性质 |

> **建议（需你点头才动）**：把 A800 与 4080 并存的关系**明确成"不同批次的实验用不同实例"**，
> 例如在 `HANDOFF.md` 环境节写成 "云端：A800 80GB（部分批次）/ RTX 4080 SUPER 32GB（2026-09-13 实测批次）"，
> 并删掉无依据的 "RTX 5090"。**在你说之前我不改**——因为你已经纠正过我一次，这里同样以你的事实为准。
> ✅ 唯一无需等待的：**论文里统一写 A800**（P3 正文本来就是 A800，无需改动）。

---

## 五、投稿时仍需注意（操作者侧）

1. **许可证必须选 CC BY** —— Southampton 协议批准免费 OA 的硬条件（`docs/OA_FUNDING_ROUTES.md` §三.4）。
2. **文章类型选 research report** —— PRL 只收 research reports 与 commentaries（其 Guide "Article types"）。
3. **不需单独 title page**（PRL 不要求），四项声明已在稿件内；`title_page_prl.pdf` 仅备必要时上传。
4. **篇幅**：11 页 IEEEtran。PRL 无硬性页数上限，但其定位是 "concise articles"；这版已比 TNNLS 版短，
   若编辑要求压缩，可再精简（附录与部分消融可移入补充材料）。

---

## 六、未完成 / 待定

- ⏳ **PRL 官方首轮时效无公开数字**（Elsevier 不公布，ScienceDirect 抓取被 captcha 拦）→ 规划仍按 2–3 个月保守估算。
- ⏳ **是否把附录移入补充材料以进一步压缩**（若你希望更贴"concise"）——待你定。
- ✅ 稿件与各节**无 TNNLS / 匿名残留**（已逐文件扫描：`main.tex` + `sections/*.tex` 零命中）。
