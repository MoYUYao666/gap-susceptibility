# paper合 与 P1 的重合处理（2026-09-20 起）

> **⛔ 2026-09-24 状态：`paper合` 已被操作者弃用并归档到 `备选/06_归档稿件/paper合/`。
> 本文件保留作历史记录与"若日后重启"的操作要点，**其中的在办项已全部关闭**——详见 §4。**
> ap3 条线不受影响：ap3 ↔ P1 无实质重合。

## 1. 事实：重合在 `paper合/`，不在 ap3

`docs/P1_REVIEW_OVERLAP.md` 记的 **1,413 词重合**是 **`paper合/`（Paper A = P1+P2 Springer 合并稿）↔ P1**，
不是 ap3↔P1（ap3 只有 2 段 21/27 词的短残句，已在 P1 整改中一并处理）。

我写了可复跑的扫描器 `tools/_overlap_scan.py`（去标记 → 词化 → 找 ≥20 词的**最长公共词串**），本轮实测：

```
python tools/_overlap_scan.py paper paper合 20
A = paper (16 files, 11298 words)   B = paper合 (9 files, 6524 words)
common runs >= 20 words: 19, total shared words: 1053
```

**1,053 词**（低于报告里的 1,413——因为这轮 P1 整改改写了 supplementary 的若干段与图注，重合已自然下降）。
分布：`paper合/sections/supplement.tex` **593 词 / 8 段**、`related_work.tex` **370 词 / 8 段**、`empirical.tex` **90 词 / 3 段**。
最大单段 **245 词**（P1 `tab:full_experiments` 的目录表体），其后 139、82、63、52 词。

## 2. 重合的两种性质（决定改法不同）

| 类型 | 段数 / 词数 | 性质 | 改法 |
|---|---|---|---|
| **表格行体**（目录表、Route C/D/E 表、机制探针/SigLIP 表、footnote） | 8 段 / **593 词** | 同一批实验的同一批标签与数值（合并稿复现 P1 的目录表）。逐字相同是因为**数据本身相同** | **需要你定**：(a) Paper A 不再复制逐行目录，改为按节汇总（组 → n → 最佳配置）并指向已发布目录；或 (b) 保留全部数据但改列序/表头（数据无损，逐字重合消失）。(a) 是**编辑上正确的解法**（合并稿无需重印姊妹稿的逐行目录，且能减庞），(b) 只是绕开查重 |
| **文献综述与结果散文** | 11 段 / **460 词** | 句子级复用（如 "cai geometric developed measure-theoretic framework…"、"on flickr text-only reduces the gap by twice as much as both-position…"） | 逐段改写 `paper合` 一侧的措辞（实质不变、措辞不同），改完用扫描器复验 |

## 3. ⚠️ 顺带发现：`paper合` 仍带**已作废的 Adapter 旧口径**

`paper合/sections/supplement.tex:58–64` 的 Adapter 行仍是**自身注入后基线**的旧值
（`adapter_d64_text & $d$=64 & text_only & $-$0.217`、`$-$0.204`、`$-$0.069` …）。
这与 P1/ap3 已修正的口径冲突——统一到冻结基线后这些值全部转正
（`outputs/analysis/adapter_common_baseline.json`：−0.217 → **+0.064**，组均值 **+0.229**，n=7）。
`paper合` 若要走出版流程，这一处必须与 P1/ap3 同步，否则同一作者的三份稿子会给出互相矛盾的数。

## 4. 状态

### ⛔ 2026-09-24：随 `paper合` 弃用，本文件全部在办项**关闭**

操作者决定：**`paper合` 放在备选、目前弃用**（ap3 = P1+P2+P3 为唯一合并主线）。
该稿 65 个文件已在 `备选/06_归档稿件/paper合/`，根目录不存在该目录。因此 §2 的 (a)/(b) 选型、
§2 的 11 段散文改写、§3 的 Adapter 口径同步**均不再执行**——**弃用的稿子不需要改写重合**。

> 关键澄清（此前一度被记成"ap3 的在办项"）：**1,053–1,413 词重合是 `paper合` ↔ P1 的事，与 ap3 无关。**
> ap3 ↔ P1 只有两段 21/27 词的残句，已在 P1 整改中处理；ap3 封面信也已在 (b) 段主动披露
> "Section 4 的实证刻画与 P1 共享"。所以"重合改写"从不是 ap3 的投稿阻塞项。

### 若日后重启 `paper合`（本文件仍有用的部分）

1. 先把它从 `备选/06_归档稿件/paper合/` 移回仓库根（清单见 `备选/归档清单.txt`），
   否则 `tools/audit/` 下 5 个用**字面路径**打开 `paper合/` 的脚本会找不到文件
   （`audit_citations.py`、`check_paperA.py`、`find_bib_placeholders.py`、`fix_paperA_round3.py`，
   以及 `_bib_verify.py` 里的 bib 路径列表）。归档时**故意没改这些脚本**，移回即恢复。
2. 再执行 §2 的选型与改写、§3 的 Adapter 旧口径同步（`paper合/sections/supplement.tex:58–64` 仍是
   自身注入后基线的旧值，与 P1/ap3 的冻结基线口径冲突）。
3. 该稿另带旧的 116 篇目录、"Causal Evidence" 标题，且与**在审的 P1** 有实质重合——
   重启前先把 P1 的审稿状态（`PR-D-26-10149`）摘清楚。

### 本次改动前保留的原始状态记录

- ✅ 已建 `tools/_overlap_scan.py`（可复跑，支持 `--text` 打印重合原文），重合位置**精确到行号**已获取。
- ⏳ 待办（**已随弃用关闭**）：按 §2 表格的 (a)/(b) 选择执行；改写 §2 的 11 段散文；
  执行 §3 的 Adapter 口径同步；每次改动后复跑扫描器直到 ≥20 词的重合归零。
