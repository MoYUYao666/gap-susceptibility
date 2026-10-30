# v2.5 发布准备（2026-10-25）

> **参见**：`docs/V25_READINESS_2026-10-24.md`（v2.5 就绪评估，2026-10-24）与 **本文件**
> （发布准备 + DOI 回填，2026-10-25，最新）。**冲突时以本文件为准**。

**状态：已在 `publish_clean/` 暂存并核验完毕，未打 tag、未推送。** 打 tag 是一步命令，留给操作者。

本文件是本次发布的交接记录。发布库（GitHub 公开库）只放代码与结果，本文件只在本仓库（`docs/`，不进公开库）。

---

## 一、暂存了什么

| 项 | 值 |
|---|---|
| 提交 | `5ad7724`（`5ad772488fdea93d881a66ab8aca137983644c8a`） |
| 父提交 | `b19d4a6`（远端 `main` 当前所在） |
| 变更 | **25 个路径：17 新增 + 8 修改**，载荷 **8.622 MB** |
| 推送性质 | **fast-forward**（`b19d4a6..HEAD` 只有这 1 个提交） |
| 提交身份 | `Repository Maintainer <noreply@example.com>`（与历史提交一致，中性） |

内容分两轮（`v2.4(7eef37f)..HEAD` 的全量差异）：

1. **云轮**（2026-10-24，其中大部分已在 `b19d4a6` 之前入库）：匹配解码器阶梯 `_p1612`、环境栈种子与
   451 题 VQA `_p1613`、多编码器阈值迁移 `_p1614`、SSH/SFTP 助手 `_p1615`、可续跑云包 `cloud_next/`。
2. **P3 改进轮**（本次新增，2026-10-24 晚—10-25）：`_p1634` 分配配对统计、`_p1635` R_c 家族与 AdaLoRA
   边界、`_p1636` Γ 稳健性、`_p1637` 一键复现账本、`_p1638` 均衡环境设计、`_p1639` 官方实现对比、
   `_p1640` 第二个下游任务；`_p1629` 已投稿件一致性核对、`_p1631` A23 下一版构建器；四栈环境分解
   （`p3_env_stack_seeds.json`，环境方差占比 **45.20% → 49.59%**）；21 单元迁移归档
   （`a23_multiencoder_transfer.json`，7 编码器 × 3 语料 = 21 单元）；以及刷新后的
   claim ledger 与 final verification。

**同步方式**：新增工具 `tools/_p1641_sync_publish_v25.py`（幂等、可重跑）。它按
`git log f3815f8f..HEAD --name-status` 取本轮触达的路径（`f3815f8f` = 与 `b19d4a6` 对应的 live 提交），
再做发布边界过滤后复制进 `publish_clean/`。刻意不收录 `046c6201`（live 的 `.gitignore` 修复）所追溯的
1,598 个旧归档（mtime 2026-08-03 — 10-24 19:01，早于镜像点），那是 live 的历史卫生，不是本轮内容；
其中 8 个 mtime 在镜像点之后的（含 `p3_allocation_paired_stats.json`）已单独识别并收录。

## 二、pre-flight 五项（对 `5ad7724` 实测）

复核命令：`python tools\_p1641_sync_publish_v25.py --preflight --rev HEAD`

| 项 | 结果 | 数字 |
|---|---|---|
| (a) 稿件类 | **PASS** | 投稿页文件名 **0**、稿件目录路径 **0**。注意：`outputs/paper_figures/`（15 个图文件）名字以 `paper` 开头，但它是**结果图目录**、不在本仓库的稿件目录清单内，自早期版本起就在库中 |
| (b) 大文件 | **PASS** | ≥100 MB **0 个** |
| (c) 权重/缓存 | **PASS（本轮）** | 全库已跟踪 `.pt/.safetensors/.ckpt/.npz/.bin` 共 **1 个**，其中**本轮新增 0 个**；唯一的 `outputs/analysis/a1_campaign_correct.npz`（75,755 B）是早期版本经 `.gitignore` 反选规则**有意保留**的逐图正确性数组（bootstrap 区间需要），非本轮引入 |
| (d) 中文 | **REVIEW（1 项）** | 发布说明 `RELEASE_NOTES_v2.5.md` 中文 **0**；助手脚本内仅 `paper合` 这一**真实目录名**（按语言规则属功能性数据，必须保留）。另有 2 个**归档**含中文散文，见下节待决定项 |
| (e) 暂存差异 | **PASS** | 25 路径（17 新增 / 8 修改 / 0 删除），载荷 **8.622 MB < 200 MB** |

**最大五个文件**（全库已跟踪）：

| 大小 | 路径 |
|---|---|
| 7.810 MB | `outputs/a1_h_templates.json` |
| 6.680 MB | `outputs/analysis/a23_multiencoder_transfer.json` |
| 5.918 MB | `tools/_tmp_a23_index.json` |
| 4.790 MB | `outputs/a1_h_baseline_metrics.json` |
| 2.996 MB | `outputs/analysis/lit_pool.json` |

**远端未被触碰（实测 `ls-remote`，只读）**：`refs/heads/main = b19d4a6`；标签
`v1.0-prl-revision`(e320e75)、`v2.0`、`v2.1`、`v2.2`、`v2.3`(c557fa8)、`v2.4`(8caec6a) **全部原样**，
**无 `v2.5`**。本次未执行任何 `tag` / `push` / Release 操作。

## 三、待执行命令（留给操作者）

```bash
# 1) 推送 main（fast-forward，无 force）
git -C publish_clean push ssh-origin main

# 2) 打新标签并推送（新 tag ⇒ Zenodo 在同一概念 DOI 下新增一个版本 DOI，DOI 不会漂移）
git -C publish_clean tag -a v2.5 5ad7724 -m "v2.5: cloud round and the Paper 3 improvement round"
git -C publish_clean push ssh-origin v2.5
```

- **铁律遵守**：新版本用**新 tag**；未 `tag -d`、未移动任何既有 tag、未删除重建任何 Release。
- **副作用提示**：推送 `v2.5` 会触发 Zenodo 铸出**新的版本 DOI**；这是新版本的正常行为。铸出后建议把
  `publish_clean/README.md` 里的 “Latest version DOI” 由 `10.5281/zenodo.23614290`（v2.4）改为新 DOI——
  **本次刻意未改 README**，因为 tag 之前不存在该 DOI，写了就是编造。
- **✅ 2026-10-25 回填（本文件的计划已执行完毕）**：Zenodo 已铸出 **v2.5 版本 DOI
  `10.5281/zenodo.23632347`**（concept DOI `10.5281/zenodo.23341082`）；GitHub Release `v2.5` 已建并标为 `Latest`，
  tag `v2.5` **未移动**（仍指 `e66094c`）。`publish_clean/README.md` 的徽章与 “Latest version DOI”
  已由 `10.5281/zenodo.23614290`（v2.4）改为 `10.5281/zenodo.23632347`（v2.5），v2.4/v2.3/v1.0 仍在 “Earlier snapshots” 列出；
  `publish_clean/RELEASE_NOTES_v2.5.md` 的 “尚未打 tag / 无版本 DOI”与 `_p1639`/`_p1640`
  “尚未执行”三处陈述已按事实改写。核验见 `docs/audit_release_cloud_2026-10-25.md` §1.4–§1.5。

## 四、发布说明现在声称什么

`publish_clean/RELEASE_NOTES_v2.5.md` 已重写（英文，5,271 字符，中文 0），风格对齐 v2.4：分
「云轮工具 / P3 改进轮 / 结果归档 / 验证」四组，明确写出：

- 云轮的 4 个工具 + `cloud_next/` 云包；
- P3 改进轮 7 个工具各自做什么，其中 `_p1634` 的结论是**不能声称 Γ 引导分配优于均匀分配**（capacity-matched
  设计下属有界结论）；`_p1635` 的家族**不一致**、不支持单一 R_c；
- ~~**`_p1639` 官方实现对比与 `_p1640` POPE 第二下游任务：已写好但尚未执行，需要云实例**~~ →
  **✅ 已过期（2026-10-25）**：两者都在 2026-10-25 云端轮执行完毕，产物已取回并入库：
  `p3_official_igu_run.json`（六臂）、`p3_official_vs_reimpl.json`（判定 `small`）、
  `p3_official_igu_replicates.json`（复现性 132.0/76.1）、`p3_second_downstream.json`（POPE）；
  故本轮**可以也应当发布结果**，`RELEASE_NOTES_v2.5.md` 已同步改写；
- 四栈环境分解的 45.20% → 49.59%；21 单元迁移归档；A23 下一版构建器 `_p1631`；
- 验证口径：frozen 归档 12 个无坏、provenance gate、A1 ledger 216/216、六个审计 profile 全 `READY`（A 级、
  0 fail / 0 warn）、staged package、六个页数——来源 `outputs/analysis/final_verification.json`；
- **明示“尚未打 tag，尚无版本 DOI”**。

## 五、刻意排除

1. **`docs/`（含本轮方法笔记）**——操作者 2026-10-14 明确“不要放 docs”；该目录含审稿意见、回复计划与
   期刊决策，且多篇仍在审理中。`publish_clean/.gitignore` 已整体忽略 `docs/`，云轮草稿里“附方法笔记”的
   说法与实际不符（那些笔记只在工作区、未进库），**本次已在发布说明中改正**。
2. **稿件类**：`main*.tex` / `main*.pdf` / 封面信 / title_page / declaration / highlights / `SUBMISSION/`。
3. **权重与数据集**（发布边界）。
4. **live `.gitignore` 修复所追溯的 1,598 个旧归档**（2026-08-03 — 10-24 19:01）：属 live 历史卫生，非本轮内容；
   若日后要让公开库承载完整 `outputs/` 记录，应作为一次**独立的、明示的范围扩张**来做。
5. **`outputs/_*` 内部/已知缺陷归档**（`_LOORA_NOT_FROZEN`、`_full_coco_CAPPED_EVAL_BUG`、
   `_llava_sites_wrong_scale`、`_serial_logs`、`_supervise_state.json` 等）：沿用 `tools/_p807_sync_publish.py`
   既有的发布过滤清单排除。
6. **仓库根 `README.md`**：公开库的 README 单独维护（历史上曾被根版本覆盖过一次），本次不动。

## 六、待决定项（打 tag 之前）

**(d) 的两个归档含中文散文**，均已按“归档必须与其脚本产物逐字节一致”原则**原样入库**：

| 文件 | 中文字数 | 位置 | 性质 |
|---|---|---|---|
| `outputs/analysis/claim_ledger.json` | 404（镜像原有 268，现 404） | `claims[].claim` / `claims[].source` 共 86 处叶子 | **既有已跟踪文件**（历史豁免）；这些是账本人读标签，且被 `_claim_ledger*.py` 读取，翻译会与 live 脱钩 |
| `outputs/analysis/p3_allocation_paired_stats.json` | 44（**本轮新增**） | 仅 2 个叶子：`controls.random_pool.archived_tests.levene_note`、`controls.random_pool.archived_power_diagnosis.rule` | **本轮新产物**，属“新建产出物一律英文”规则的违例 |

**建议**（二选一，均不影响打 tag 的正确性）：

- **A. 接受**：两者都是归档内部说明字段，不面向外部文档；与既有已跟踪的中文账本同类。
- **B. 修**：另起一轮把 `_p1634_p3_allocation_paired.py` 里这两条 note 文案改为英文并重生成归档。
  注意这要改 live 的 `tools/` 与 `outputs/`，**超出本次写权限**（本次只允许写 `publish_clean/**`、
  本文件、以及新增 `tools/_p16xx_*.py`），故未擅自处理；也**未**手改归档（那会让公开副本与脚本产物不一致）。

另有一项**非阻塞**观察：`p3_balanced_design_plan.json`、`p3_env_seeds_runlog.json` 与
`a23_multiencoder_transfer.json` 内含 `D:\Realdesktop\...` 本地绝对路径（运行日志的命令行记录；该迁移归档
**入库前就已有 29 处**，现 86 处）。属既有做法、非本轮引入，未做脱敏（脱敏会破坏“运行日志记录原命令”的溯源价值）。

## 七、如何复核

```bash
# 发布边界五项（对本次提交）
python tools\_p1641_sync_publish_v25.py --preflight --rev HEAD

# 本次提交改了什么
git -C publish_clean show --stat HEAD

# 远端仍未被本会话触碰（只读）
git -C publish_clean ls-remote --heads ssh-origin
git -C publish_clean ls-remote --tags  ssh-origin
```

## Update (2026-10-25 09:20)

The tag target moved from `e202db8` to **`5ad7724`** because the allocation-paired archive carried two Chinese prose leaves inherited from an older archive; `tools/_p1634_*.py` now writes English notes and the archive was regenerated with identical numbers (zero non-ASCII, 1316 numeric leaves unchanged, byte-stable re-run). The staged commits are therefore `e202db8` (the release itself) followed by `5ad7724` (the language fix), and the tag must point at the latter. A third staged commit will follow once the cloud round (POPE second downstream task and the official-implementation comparison) has produced its archives.
