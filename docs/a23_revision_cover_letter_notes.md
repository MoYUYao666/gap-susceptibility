# A23 修订投稿信（IEEE JOE 26-0663）—— 交付件与证据链

> 任务：shared **task-24**。为 `SUBMISSION/A23_JOE_next_revision/` 补上该包唯一缺失的部件：
> 英文修订投稿信 `CoverLetter.pdf`（无下划线），并同步包的 `README.md` 与 `SHA256SUMS.txt`，
> 证明冻结投稿件未被改动。
>
> 产出：`CoverLetter.pdf`（**2 页**，141,290 B）+ 源文件 `revision_cover_letter.tex`；
> 构建与清单脚本 `tools/_p1667_a23_coverletter_package.py`；取数脚本 `tools/_p1666_a23_letter_facts.py`。

---

## 一、先做的一项独立核验（决定信怎么写）

给编辑的信要做事实声明，因此我**没有**直接采信任务简报的措辞，而是用 pypdf 把冻结投稿版全文抽出来核对：

| 检索串（冻结投稿版 `SUBMISSION/A23_JOE/current/main_ieee.pdf`） | 命中 |
|---|---|
| 页数 | **64 页** |
| `multi-encoder` | **0** |
| `21 units` | **0** |
| `RemoteCLIP` | **0** |
| `survivors` | **0** |
| `no threshold` | **0** |
| 任何 `10.5281/zenodo.<id>` 形式的仓库版本 DOI | **0**（正文只写 GitHub URL；`zenodo` 的 2 处命中都是**数据集** UXO 在 Zenodo 上不可达的叙述） |

⇒ 两条结论：
1. **多编码器迁移段落确实在投稿版里完全不存在** ⇒ 信里可以（也必须）写成"**新增材料、不是对审稿人所读内容的收窄**"。
2. **⚠️ 与任务简报的一处偏差（已按事实写）**：简报说"冻结包保留它原来的 DOI"，但实测**冻结投稿版里根本没有仓库版本 DOI**，
   只有 GitHub URL。因此信里写的是：**当前稿新增了版本归档 DOI（v2.5）**，而不是"保留了原 DOI"。
   这一条已如实写进信的第 6 段，并在此记录。

另外核对：当前工作稿 `paper_a2/main_ieee.pdf` = **73 页**，正文 DOI = **`10.5281/zenodo.23632347`**（v2.5）✔ 与任务一致。

---

## 二、信的结构（共 2 页，逐段落写清"改了什么/为什么/什么没变"）

| # | 段落 | 主张 | 证据（归档字段 / 笔记） |
|---|---|---|---|
| 1 | 开头 | 这是 26-0663 的修订稿，保留原论证与五域评估，新增一项有界分析并记录其局限 | — |
| 2 | **新增材料（最重要）** | 多编码器迁移分析是**投稿后新增**；投稿版无迁移章节、无多编码器语料比较、无阈值迁移陈述；**不是**对审稿人所读内容的收窄，投稿版没有任何句子被撤回或削弱 | 独立核验见 §一（冻结 PDF 0 命中） |
| 3 | 新增内容与数字 | 7 个冻结编码器 × 3 语料 = **21** units；**441** 有序 source→target 对；每对 **13** 个统计量 ⇒ **4,940** 条 cross-unit 计分条目；**179** 条点估计优于 chance，其中 **29** 条 95% bootstrap 区间仍高于 chance；**29 条全部以声呐语料为目标**（SigLIP **12** + OceanCLIP **10** + RemoteCLIP **6** + CLIP ViT-L/14 **1**）；**27/29** 是尺度相对统计量 $M(\varepsilon/\sigma_D)$；最强幸存对 BioCLIP(sonar)→SigLIP(sonar) @ $\varepsilon=0.002$：目标 BA **0.900**、源拟合 **0.500**、(BA−chance) 区间 **[+0.100, +0.500]** | `conclusion.n_units`=21、`conclusion.n_ordered_pairs`=441、`conclusion.n_statistics_per_pair`=13、`conclusion.n_scored_entries_cross_unit`=4940、`conclusion.n_entries_above_chance`=179、`conclusion.n_entries_surviving_bootstrap`=29、`conclusion.best_surviving_pair.{target_BA, source_fit_BA, delta_ci95}`；幸存者按目标编码器的分布由 `transfer.pairs[*].by_statistic[*].bootstrap.survives` 重算（**排除 self-pair**，依据 `transfer.summary.self_pairs_excluded_from_the_claim`） |
| 4 | 主张的有界性 | **不**声称阈值跨编码器/跨语料可迁移；只声称：在这三个语料上、目标为声呐时，$M$ 的阈值在编码器对之间**方向**可迁移、且阈值固定在目标单元自身分数尺度；4940 条中 29 条 ⇒ 不延伸到海洋光学与稀有物种目标；"无阈值可迁移"这一无条件旧句不在投稿版中，修订也**不**恢复它 | 同上 + `docs/a23_transfer_claim_rewrite_notes.md`（改写口径） |
| 5 | **新增第五条限制** | 新增的 RemoteCLIP 是遥感微调编码器，top-1 在三个语料上都落在 chance 两倍以内（**12.83 / 11.27 / 2.43 %** vs chance **14.29 / 14.29 / 1.49 %**），29 条幸存者中 **6 条**的目标取自它 | `encoders.remoteclip.corpora.<corpus>.frozen_row.top1` 与 `.chance_percent`；正文该段限制：`paper_a2/ext_partII_domains.tex`（limitation 第 5 条）；四组复验见 `docs/a23_21unit_switch_notes.md` §2 |
| 6 | 页数与 DOI | 页数 **64 → 73**（新增迁移章节 + 逐数字的 Source/字段路径标注）；当前稿引用版本归档 DOI **10.5281/zenodo.23632347**（v2.5, 25 October 2026），**投稿版只写仓库 URL、无版本 DOI**，冻结提交件未改 | 独立核验 §一；`paper_a2/main_ieee.pdf` 73 页；`paper_a2/ext_partII_domains.tex` 的 Data availability 段 |
| 7 | **什么没变** | 诊断方法本身、order-preservation 结果、五域评估与协议、adaptation decision table、标题、作者、声明均**实质未变**；投稿版没有任何结果被撤回；迁移结论不外推到 7 编码器/3 语料之外的任何对象 | — |
| 8 | 数据/代码 | 见第 6 段（不放两个 DOI 以免自相矛盾） | — |
| 9 | 经费/利益冲突 | 未变：无经费、无利益冲突、AI 使用声明仍在稿中 | — |

**信里刻意避免的事**：没有写"应审稿人要求"之类的假因果（我没有审稿意见记录）；没有把 5 units 口径说成审稿人读到的版本；
没有把"29 survivors"夸大为普适可迁移；没有为凑页数删掉 DOI。

---

## 三、构建与核验

**构建命令**（工作目录 `SUBMISSION/A23_JOE_next_revision/`）：

```bash
pdflatex -interaction=nonstopmode -halt-on-error -jobname=CoverLetter revision_cover_letter.tex   # ×2
```

**结果**：`Output written on CoverLetter.pdf (2 pages, 141290 bytes)`；**0** errors、**0** undefined refs/cites、**0** overfull hbox、**0** overfull vbox。

**字体（`pdffonts CoverLetter.pdf`，全部 Type 1、embedded）**：

```
name                                 type              encoding         emb sub uni object ID
HKUVIZ+TeXGyreTermesX-Regular        Type 1            Custom           yes yes yes      8  0
MFBDIS+TeXGyreTermesX-Italic         Type 1            Custom           yes yes yes      9  0
ZFLGOX+TeXGyreTermesX-Bold           Type 1            Custom           yes yes yes     10  0
HKUVIZ+TeXGyreTermesX-Regular        Type 1            Custom           yes yes yes     11  0
FEVIEU+txsys                         Type 1            Builtin          yes yes yes     12  0
MKWCKV+NewTXMI                       Type 1            Builtin          yes yes yes     13  0
WOFTFE+NewTXMI7                      Type 1            Builtin          yes yes yes     14  0
OGYQFN+txmiaX                        Type 1            Builtin          yes yes yes     15  0
```

- 正文用 **TeXGyreTermesX**（TeX Gyre Termes = Times 克隆）⇒ Times 兼容 ✔
- 数学用 **newtxmath**（`txsys` / `NewTXMI` / `txmiaX`，专为 Times 兼容设计的数学字体组）✔
- **注意**：第一版用 `\usepackage{times}` 时，数学符号仍落到 **Computer Modern**（`CMR10`/`CMSY10`/`CMMI10`/`CMMI8`），
  不符合"Times 兼容"，已改为 `newtxtext` + `newtxmath` 重建，现存 PDF **不含任何 CM 字体**。

**包清单**（`python tools/_p1667_a23_coverletter_package.py --apply`）：

- `README.md` 两行由 "not supplied" 改为 `CoverLetter.pdf`（2 页 + 源文件）；
- 删除构建中间产物 `CoverLetter.aux/.log/.out`，包目录只留交付文件；
- 重算 `SHA256SUMS.txt`（**8 条**，覆盖除自身外全部文件）：

| 文件 | 字节 | sha256 |
|---|---|---|
| `CoverLetter.pdf` | 141,290 | `cdcb8cc8…` |
| `DeclarationOfInterest.docx` | 5,700 | `99bbb817…`（**未变**） |
| `Highlights.pdf` | 72,213 | `15ca97d1…`（**未变**） |
| `LaTeXSource.zip` | 964,664 | `e92b0a91…`（**未变**） |
| `Manuscript.pdf` | 1,275,901 | `f5a3725e…`（**未变**） |
| `README.md` | 3,014 | `c3477456…`（本轮更新） |
| `revision_cover_letter.tex` | 5,853 | `326b67d7…`（新） |
| `Supplementary.pdf` | 1,065,101 | `5a9c624e…`（**未变**） |

**上传文件名检查**：`CoverLetter.pdf`、`DeclarationOfInterest.docx`、`Highlights.pdf`、`LaTeXSource.zip`、
`Manuscript.pdf`、`Supplementary.pdf` —— **全部无下划线** ✔（`revision_cover_letter.tex` 是仓库内部源文件，
非上传件；`SHA256SUMS.txt`/`README.md` 亦非上传件）。

**清单自洽性核验**：8 条逐条重算哈希 **全部匹配**；`未列出的包内文件 = []`；`列出但缺失 = []`。

---

## 四、冻结件未被动用的证明

`python paper_a2/verify_a23_fix.py` → **`ALL CHECKS PASSED`**，其中关键一条：

```
PASS  frozen archive: all 37 SHA-256 hashes unchanged
```

即 `SUBMISSION/_frozen_submitted/`、`SUBMISSION/A23_JOE/` 与其它冻结输入**均未改动**；
包内 5 个"carried unchanged"文件的哈希与建包时（`SHA256SUMS.txt` 旧版）**逐条相同**，
两者互为独立佐证。

（说明：`SUBMISSION/` 整目录被 `.gitignore` 忽略，`git status` 看不到这些文件的增删，
**哈希门禁才是真正的冻结证据**——这一点在 `docs/a23_next_revision_package_notes.md` §3 已记录。）

---

## 五、无法溯源 / 刻意未做的事项（诚实清单）

1. **"投稿版是否曾有过某句 'no threshold on M transfers'"**：冻结 PDF 里该串 **0 命中**，所以信里只说
   "该无条件旧句不在这份投稿版中，修订也不恢复它"，**没有**说"我们删掉了它"——避免把草稿史说成投稿史。
2. **64 → 72 页那段增长的逐项归因**：只有最后一步 **72 → 73**（本次改写：新句约 +1,073 字符、Source 字段路径约 +600 字符）
   有笔记依据（`docs/a23_transfer_claim_rewrite_notes.md` §5）；因此信里只写"增长来自新增迁移章节与逐数字来源标注"，
   **没有**虚构 64→72 的分解。
3. **审稿意见**：手上没有 26-0663 的审稿报告，信里**不写**"应审稿人要求"，只写"本修订拟替代当前在审版本"。
4. **TitlePage / Abstract**：仍未提供（JOE 单盲、作者块在正文；`paper_a2/abstract.pdf` 1 页但不在包内）——
   不在本任务范围，保持 README 的 "not supplied" 与理由。
5. **未改动**：任何稿件源文件、`SUBMISSION/A23_JOE/`、`SUBMISSION/_frozen_submitted/`、其它包。

---

## 六、一句话状态

`CoverLetter.pdf`（2 页，Times 兼容字体，0 错误/0 overfull）已入包；README 与 SHA256SUMS 已同步且自洽；
**37 条冻结哈希全部未变**。包内现共 **9 个文件**（8 个交付/元数据文件 + `SHA256SUMS.txt`），
上传件 6 个且**全部无下划线**。
