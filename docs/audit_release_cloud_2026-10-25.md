# 独立审计 B —— 发布状态、公开边界、云端产物、脚本谱系（2026-10-25）

- **审计对象**：shared task-20。发布 `publish_clean/`（远端 `ssh-origin`）、`cloud_retrieved/round2_2026-10-25/`、
  本轮归档、以及 `tools/_p1639_p3_official_igu.py` 的谱系。
- **审计者**：`p3-downstream`（本轮云端轮次的执行者，**因此本审计不是完全独立**——见 §8 局限）。
- **方式**：只读复核。所有结论都带命令与原始输出；**未修改任何被审文件**（本文件是唯一写入）。
- **总判定**：**通过（no blocking finding）**。核心主张全部在产物上成立：
  `v2.5 → e66094c`、远端 `main = e66094c`、7 个 tag 原位未动、公开树无稿件/权重/parquet/≥100 MB、
  云产物 47/48 校验、六个臂与两个锚点哈希吻合、复现性 132.0/76.08 可从归档直接重算、
  两个缺陷修复均在位且 `--self-test` 37/37。
  另有 **3 项非阻塞发现**（1 项 should-fix、2 项 cosmetic/记录性），见 §6。

---

## 1. 发布状态（RELEASE STATE）

### 1.1 远端 tag 清单（`git -C publish_clean ls-remote --tags ssh-origin`）

| tag | 注解 tag 对象 | 指向 commit | tagger 时间（+0800） |
|---|---|---|---|
| `v1.0-prl-revision` | `e320e7538a89…` | `8b03800ccdba…` | 2026-10-13 20:13:51 |
| `v2.0` | `8d9d8454730d…` | `464fd7d9c8b9…` | 2026-10-20 00:08:02 |
| `v2.1` | `86a38367f0e9…` | `c01cd0b96634…` | 2026-10-21 03:07:59 |
| `v2.2` | `0630332f79ce…` | `92b34ef7eb94…` | 2026-10-21 10:20:48 |
| `v2.3` | `c557fa8639d1…` | `81e23d4a1a36…` | 2026-10-24 12:12:07 |
| `v2.4` | `8caec6ab595f…` | `7eef37f6ab81…` | 2026-10-24 17:24:46 |
| **`v2.5`** | **`03e6cebfe09c…`** | **`e66094c23dc2…`** | **2026-10-25 11:13:10** |

- **`v2.5` 指向 `e66094c`** ✅（`e66094c23dc2907d6b6902ab1bb88a9566b9201d`）。
- `git ls-remote ssh-origin HEAD main` → 两者都是 **`e66094c23dc2907d6b6902ab1bb88a9566b9201d`** ✅
- 7 个 tag **全部是 annotated tag**（都存在 `^{}` 解引用行），因此 tag 对象哈希覆盖 tagger/时间/说明/目标提交。

### 1.2 "没有 tag 被移动或重建"的证据

git **没有 tag reflog**（`reflog` 只覆盖 refs/heads 与 HEAD），所以不能用 reflog 证明。改用两条更强的字节级证据：

1. **本地 ↔ 远端 注解 tag 对象的 SHA-1 逐一相等**：
   `git for-each-ref refs/tags --format='%(refname:short) %(objectname)'` 得到的 7 个对象哈希与
   `ls-remote --tags` 的 7 个 `refs/tags/*` 哈希**完全一致**（见上表）。
   ⇒ tag 内容（含 tagger、时间戳、说明、目标）未被改写；**重建 tag 会改变 tag 对象哈希**。
2. **每个 tag 解引用的 commit 都是 `main` 的祖先**（`git merge-base --is-ancestor` 逐个返回 0）：
   `8b03800`、`464fd7d`、`c01cd0b`、`92b34ef`、`81e23d4`、`7eef37f`、`e66094c` —— 全部为 True。
   ⇒ 没有 tag 被重指到无关提交。

**tagger 时间戳严格单调**（10-13 → 10-20 → 10-21 ×2 → 10-24 ×2 → 10-25），`v2.5` 的 11:13:10 晚于
`e66094c` 的提交时间 11:12:44（28 秒），符合"先提交、后打 tag"的正常顺序。
与 AGENTS.md 记录的冻结值一致：`v1.0-prl-revision` = `e320e75`（Zenodo `23341223`）**未动** ✅

### 1.3 我的第三提交是否原样进入远端

`git log --oneline 9976333..main` → **只有一条** `e66094c`（"v2.5 round 4: POPE verdict wording,
acceptance honesty fix, final verification snapshot"）。
⇒ 远端树 = 我的 `9976333` + lead 的一次收尾提交；**我的提交未被 amend 或丢弃** ✅
`e66094c` 相对 `9976333` 改了 6 个文件（`final_verification.json`、`p3_pope_latex_values.json`、
`p3_pope_tex_insert.json`、`_p1649_pope_supplement_insert.py`，以及**收入**我在主仓未提交的
`_p1650_fix_pope_acceptance_bool.py`(+81) 与 `_p1651_update_phase_close_docs.py`(+285)）。

### 1.4 GitHub Release（AGENTS.md 2026-10-25 新增铁律的判据）

AGENTS.md 于 2026-10-25 追加铁律：**打 tag 之后必须再建 GitHub Release**（Zenodo 摄取的是 Release，不是裸 tag），
判据是"`gh release list` 里必须出现新 tag 且标为 `Latest`"。实测：

`gh release list --repo MoYUYao666/gap-susceptibility --json tagName,name,isLatest,isDraft,publishedAt`

| tag | Release 名称 | isLatest | isDraft | publishedAt (Z) |
|---|---|---|---|---|
| **v2.5** | v2.5 - cloud round 2 and the Paper 3 improvement round | **true** | false | **2026-10-25T03:19:51Z** |
| v2.4 | v2.4 - analysis layer update | false | false | 2026-10-24T09:24:54Z |
| v2.3 | v2.3 - analysis layer update | false | false | 2026-10-24T04:12:50Z |
| v2.2 | v2.2 | false | false | 2026-10-21T02:20:58Z |
| v2.1 | v2.1 | false | false | 2026-10-20T19:08:09Z |
| v2.0 | v2.0 | false | false | 2026-10-19T16:08:09Z |
| v1.0-prl-revision | v1.0 - Code and results for PRLETTERS-D-26-02378 (Paper 3 revision) | false | false | 2026-10-13T12:14:05Z |

- **7 个 Release 与 7 个 tag 一一对应**，无遗漏、无重复、无 draft ✅
- `v2.5` 标为 **`Latest`**，发布时间 03:19:51Z（= 11:19:51 +0800），晚于 tag 时间 11:13:10 **6 分 41 秒**，
  符合"先 tag、后 Release"的正确顺序 ✅ ⇒ **新铁律的判据满足**。

### 1.5 Zenodo DOI（Release → Zenodo 摄取结果）

| 项 | 值 |
|---|---|
| **v2.5 版本 DOI** | **`10.5281/zenodo.23632347`** |
| 概念 DOI（始终指向最新版） | `10.5281/zenodo.23341082` |
| `metadata.version` | `v2.5` |
| `metadata.title` | MoYUYao666/gap-susceptibility: v2.5 - cloud round 2 and the Paper 3 improvement round |
| 发布日 | 2026-10-25 |
| `related_identifiers` | `https://github.com/MoYUYao666/gap-susceptibility/tree/v2.5` ← **指向 v2.5 tag 本身** |
| 旧 v1.0 记录 | `10.5281/zenodo.23341223`（`version = v1.0-prl-revision`，同一 concept `23341082`） |

⇒ **发布链条完整：`main`(e66094c) → annotated tag `v2.5` → GitHub Release(v2.5, Latest) → Zenodo DOI `23632347`** ✅

**一处观察（非缺陷）**：`zenodo.org/api/records?q=conceptdoi:"10.5281/zenodo.23341082"` 只返回 **1 条**（v2.5），
而旧的 `23341223` 单独按 record id 仍可正常解析且 conceptdoi 相同。这是 Zenodo 检索对"已被新版本取代"记录的
默认过滤行为，不是本项目的版本缺失；引用时应按官方建议**引具体版本 DOI**（v2.5 用 `23632347`）。

---

## 2. 公开边界（PUBLICATION BOUNDARY）

审计对象：**推送后的树** `e66094c`（`git ls-tree -r -l e66094c`），不是工作区。

- **跟踪文件 2,786 个，合计 61.1 MB**。
- **最大五个文件**：

| 字节 | 路径 |
|---|---|
| 7,326,030 | `outputs/a1_h_templates.json` |
| 6,679,520 | `outputs/analysis/a23_multiencoder_transfer.json` |
| 5,917,904 | `tools/_tmp_a23_index.json` |
| 4,523,829 | `outputs/a1_h_baseline_metrics.json` |
| 2,996,398 | `outputs/analysis/lit_pool.json` |

### 边界检查表

| 检查项 | 结果 | 证据 |
|---|---|---|
| `paper*/`、`SUBMISSION/` 下的路径 | **0** | 正则 `^(paper[^/]*|SUBMISSION)/` 无命中 |
| `.tex` 文件 | **0** | — |
| `.pdf` 文件 | **2**，均为**结果图** | `outputs/analysis/fig15_stratified_dg_r1.pdf`、`outputs/paper_figures/fig7.pdf` |
| cover letter / title page / declaration / highlights | **1**，是**结果记录**非投稿件 | `outputs/analysis/paperhe_highlights.json`（258 B，内容为标题 + `r2_probes` 统计，非 Highlights 投稿页） |
| LaTeXSource / `.zip` 归档 | **0** | — |
| 权重 `.pt/.pth/.safetensors/.ckpt/.bin` | **0** | — |
| `.parquet` | **0** | 本次的 `paper3/test-pope-random.parquet` 未进公开库（`EXCLUDE_EXT` 含 `.parquet`，且 `paper3/` 不在 `TREES`） |
| ≥ 100 MB | **0** | 最大 7.33 MB |
| 二进制文件 | **1 个 `.npz`** | `outputs/analysis/a1_campaign_correct.npz` **75,755 B** ——**仍然是唯一的二进制**，即既有的、经操作者默许的例外（bootstrap 区间需要它） |

⇒ **公开边界成立：无稿件、无权重、无 parquet、无 ≥100 MB 文件**；`a1_campaign_correct.npz` 仍是唯一二进制 ✅

---

## 3. 云端证据（CLOUD EVIDENCE）

1. **取回校验**：`python tools/_p1641_verify_retrieval.py --manifest cloud_retrieved/round2_2026-10-25/SHA256SUMS.txt --dir cloud_retrieved/round2_2026-10-25`
   → **`== 47/48 verified ==`**。
   唯一未通过项是 `logs/plan_recheck_20261025.log`（下载被 SSH 中断截断为 **0 B**，实例上 11,010 B）——
   该情形已在本轮记录中如实标注，并以本地重跑件 `logs/plan_recheck_LOCAL_RERUN.log` 替代（文件名自带 `LOCAL_RERUN` 注明）。
   另注：`RETRIEVAL_MANIFEST.md`、`verify_round2c.json` 是校验器自身产物、不在清单内（非失败项）。
2. **POPE parquet**：`cloud_retrieved/round2_2026-10-25/parquet/test-pope-random.parquet`
   → **61,909 B**，sha256 **`66faa5e6de3be2374be68b8794a14cf660ff14670575ea47b9b77da8b43a71d4`** ✅（与要求值逐字节一致）
3. **实例已关闭**：`Test-NetConnection connect.westb.seetacloud.com -Port 10137 -InformationLevel Quiet` → **False** ✅

---

## 4. 归档完整性（ARCHIVE INTEGRITY）

### 4.1 四个归档的哈希与内部计数

| 归档 | 字节 | sha256 | 内部计数 | 主张值 |
|---|---|---|---|---|
| `outputs/analysis/p3_official_igu_run.json` | 15,278 | `8f4546edff677b46182f6482c4b9a30c9b1d700b0346f662c777c037508ee35f` | `runs[] = 6` | 六个 run ✅ |
| `outputs/analysis/p3_official_vs_reimpl.json` | 16,214 | **`4698a6e7da4e9c61da2b95590dada1e216bd2acdd861df347fd0b7867b6955c6`** | `overall.verdict = small` | `4698a6e7…` ✅ |
| `outputs/analysis/p3_official_igu_replicates.json` | 4,322 | `e38f65ab00a4b24801e098520c31339f346a465839ce108fd917e8278160c718` | 6 臂 / 2 趟 | 见 §4.3 ✅ |
| `outputs/analysis/p3_second_downstream.json` | 15,406 | **`41723dc2f1be53cf0eba0adb132c0381cf64f3524893b8fe25ab643b9dfe9e97`** | acceptance 9 项 | `41723dc2…` ✅ |

### 4.2 `p3_official_igu_run.json` 的六臂与自洽性

- `runs[]` 长度 **6**；`runs_sha256` 记录值 `a2cd1c16b03dc813aab27860227d34701bdc1ee95848f12f7687355df852576e`
  用工具自身的序列化（`json.dumps(runs, ensure_ascii=True, separators=(",",":"))`）**精确重算一致** ✅
- 六条记录 `delta_E` = **+182.5 / +178.0 / +242.0（official_corrected_map）、+333.0 / +186.0 / +262.0（reimpl_igu_style）**。
- **六个臂归档逐一比对 `runs[*].sha256`：6/6 全部命中**（在 `cloud_retrieved/round2_2026-10-25/arms/` 中）。

  ⚠️ **方法学记录（差点误报）**：若以**主仓工作区** `paper3/scripts/outputs/experiments/` 比对，会看到
  **5 个 ABSENT** 而误判"哈希不符"。实际原因是这些云上产出的臂归档**本地主仓从来不存**（只有已发表的
  S27 锚点 `verify_r1_s42_bcexplicit_v11_s1_m3_d1.json` 在本地）。正确比对对象是取回副本。
  ⇒ 结论是 **6/6 通过**；但这说明"`runs[*].sha256` 只能对取回副本验证"这件事应写进交接文档，
  否则后来的审计者会重复误判（见 §6 F2）。

### 4.3 复现性 spread 直接从归档重算

`p3_official_igu_replicates.json` 中 `arms[].max_minus_min`：
`118.0, 108.0, 55.5, 132.0, 7.5, 35.5`（对应 official 42/123/789、reimpl 42/123/789）

- **重算 max = 132.00**，与 `summary.max_spread_across_arms = 132.0` **一致** ✅
- **重算 mean = 76.0833**，与 `summary.mean_spread_across_arms = 76.083333…` **一致** ✅
- `passes_completed = 2`，`n_arms = 6` ✅
- 归档另存两锚点还原后的哈希（`pinned_anchors_sha256_after`），与 §4.4 实测一致。

### 4.4 两个 pinned 锚点

| 锚点 | 实测字节 | 实测 sha256 | 要求 |
|---|---|---|---|
| `paper3/scripts/outputs/experiments/verify_r1_s42_bcexplicit_v11_s1_m3_d1.json` | **937** | **`212e9c75e7fcad2e2f4b6e544ad394014771ed20f814ba48677b7a38b61f248a`** | 937 B / `212e9c75…` ✅ |
| `paper3/scripts/outputs/experiments/verify_r1_s42_bcexplicit_v12_s1_m2_d1.json` | **946** | **`a060e2a880a638cb81c54ca8b444936c0d6612e3eccee98231ad79cc00338e7f`** | 946 B / `a060e2a8…` ✅ |

### 4.5 POPE 聚合的验收状态

`p3_second_downstream.json :: acceptance`：

```
three_arms_present true | records_per_arm {base 3000, 5 3000, 6 3000} | equal_question_counts true
refs_byte_identical_across_arms true | refs_match_prepared_parquet_order true
prepared_parquet_order_check true | adapters_reused_not_trained true | contrasts_computed true
every_contrast_reports_a_minimum_equivalent_margin true
```

`claim_verdict.second_task_verdict = supports_the_adapters` ✅
→ 行序检查现在是**真实比对**结果（`prepared_parquet_order_check` 与布尔值同源），不再是哨兵字符串被 `bool()` 吞掉。

### 4.6 公开树里的副本 == 工作区文件

用 git blob 身份比对（避免 PowerShell 重编码干扰）：
`p3_official_igu_run.json`、`p3_official_vs_reimpl.json`、`p3_official_igu_replicates.json`、
`p3_second_downstream.json`、`tools/_p1640_p3_second_downstream.py`、`tools/_p1641_verify_retrieval.py`
在 `e66094c` 中的 blob 与工作区**全部 identical=True** ✅

---

## 5. 脚本谱系（SCRIPT LINEAGE）

被审文件：`tools/_p1639_p3_official_igu.py`，本地 sha256 `2065ebbb3463b8c654fd77220e8d4193f22dd3b3be701cceab5b83a76bf4c728`。

**字节级身份**：`git hash-object tools/_p1639_p3_official_igu.py` = `001fb9961ceda28771ad1db69c8e97e64d07ac37`
= `git -C publish_clean rev-parse e66094c:tools/_p1639_p3_official_igu.py` = `9976333:…`
⇒ **工作区 = 我的第三提交 = 推送树，三者逐字节相同** ✅
（首次比对曾因 PowerShell `Out-File` 重编码得出不同哈希，属于工具误差，已用 git blob 复核纠正。）

### 5.1 两个缺陷的修复是否在位

| 缺陷 | 要求 | 实测 | 结论 |
|---|---|---|---|
| #1 训练后删掉自己的产物 | 不得对整个 `expected` 列表做 `restore_owned` | `:870` `for path in expected[1:]:`（在 `restore_side_effects()` 内）；`:915` 只调用 `restore_side_effects(expected, saved)` | ✅ |
| #2 `block_maps` 被清零覆盖 | `merge_block_maps` 绝不用零覆盖 | `:937` `def merge_block_maps`；`:945` 注释"never overwrite with zeros"；`:957` `if ranks:` 才重算；`:961` 否则保留 payload 原值 | ✅ |
| 可移植性 | `mkdtemp(..., dir=REPO)` | `:1491` `tmp = tempfile.mkdtemp(prefix="p1639_selftest_", dir=REPO)` | ✅ |

**关于 `:906` 的 `for path in expected:`（未加 `[1:]`）——不是缺陷**：
它是训练前的**快照保存**循环（`saved[path] = fh.read()`，`:905-910`），目的是 `run_training.py`
改写文件前先存字节；恢复只走 `restore_side_effects()`（`:915`）。逐行读过，语义正确。

### 5.2 `--self-test`

`python tools/_p1639_p3_official_igu.py --self-test` → **`assertion ledger: 37 checks, 0 failed`** ✅
（含 `[C]` 恢复逻辑双向回归、`[D]` `block_maps` 合并回归；在实例 Linux 与本地 Windows 均通过。）

### 5.3 `--workers` fork 的隔离

| 对象 | 事实 | 结论 |
|---|---|---|
| `cloud_next/par_arms/_p1639_with_workers_94a48285.py` | 存在，89,899 B，sha256 `a329042fe96ffe60d21bbca8f42734f56d97fa5df6802502cfd2fe10a80b950c`；全仓 grep 只在 `docs/p3_cloud_round2_notes.md:500` 被**文字提及** | **仅冻结参考，未被 import、未被执行** ✅ |
| 公开树 | `_p1639_with_workers_94a48285` / `_p1639_parallel_variant` 在 `e66094c` 中**均不存在** | 未进入公开库 ✅ |
| ⚠️ 兄弟 fork `cloud_next/_p1639_parallel_variant.py` | 被 `cloud_next/_jobB_train.sh:16` **实际执行**（`--workers 2`），并被 `cloud_next/_confirm_standdown.sh` 以 `grep` 探测 | 见 F3：它是另一 agent 的并行尝试驱动脚本，**未产出任何被报告的数字**（该次运行 exit=1、两臂 OOM）；两个脚本都**未进公开树** |

---

## 6. 发现（按严重度排序）

### 阻塞级（blocking）：**无**

没有 tag 被移动/重建、没有稿件泄漏进公开树、没有归档内部计数与其哈希校验副本冲突。

### F1（should-fix，非本轮引入）公开树里有 **8.02 MB 的 `.err` 编译错误日志**

- 证据：`git ls-tree -r -l e66094c` 中
  `outputs/analysis/_p805.err` 1,943,184 B、`_scaleup.err` 1,940,708 B、
  `_scaleup2.err` 1,811,239 B、`_scaleup3.err` 2,328,725 B —— 合计 **8,023,856 B ≈ 8.02 MB**，
  占公开树 61.1 MB 的 **13%**。
- 来源：`git log --diff-filter=A -- outputs/analysis/_p805.err` → 提交 **`43b733c`（2026-10-14）**，
  **并非本轮（2026-10-25）新增**；`_p1641_sync_publish_v25.py` 的 `EXCLUDE_EXT` 排除了 `.log` 但**没有排除 `.err`**，
  所以它们从 10-14 那次发布起一直留在镜像里。
- 影响：不违反本次列明的边界（非稿件/权重/parquet，且远小于 100 MB），但把**报错日志**当发布内容不合适，
  且占体积。**建议**（不在本审计职责内执行）：后续发布给 `EXCLUDE_EXT` 加 `.err`，并在下一次发布时**删除**这 4 个文件。

### F2（cosmetic / 文档性）`runs[*].sha256` 只能对取回副本验证，主仓不存 5 个臂归档

- 事实：`paper3/scripts/outputs/experiments/` 在主仓只有 `verify_r1_s42_bcexplicit_v11_s1_m3_d1.json`
  （S27 锚点）与 `verify_r1_s42_bcexplicit_v12_s1_m2_d1.json`（S39 锚点）；
  本轮 6 臂中 **5 个只在 `cloud_retrieved/round2_2026-10-25/arms/`**。
- 风险：审计者若在主仓比对 `runs[*].sha256` 会把"文件不存在"误读成"归档被篡改"（本审计第一遍就撞上）。
- 建议：交接文档或 `_p1641_verify_retrieval.py` 的说明里写明**验证路径是取回副本**。

### F3（informational）`cloud_next/` 有 9 个文件在公开树里；并行 fork 的驱动脚本存在但未发布

- 公开树含 `cloud_next/` 下 9 个**早期轮次**文件（`README.md`、`env_setup.sh`、`p1_driver.sh`、`run_all.sh`、
  `verify_cloud_artifacts.py` 等），来自更早的发布，**与本轮 fork 无关**。
- `cloud_next/_p1639_parallel_variant.py`（另一 agent 的 `--workers` fork）**未被发布**，
  但被 `cloud_next/_jobB_train.sh` 实际调用（该次运行 OOM、exit=1，未产出任何被报告数字）。
  任务要求核对的 `_p1639_with_workers_94a48285.py`（我保存的冻结副本）**确实只有文档引用** ✅。

---

## 7. 复现命令（全部只读）

```powershell
cd <repo>\publish_clean
git ls-remote --tags ssh-origin                      # 7 tags
git ls-remote ssh-origin HEAD main                   # e66094c…
git for-each-ref refs/tags --format='%(refname:short) %(objectname)'   # == remote tag objects
git cat-file -p refs/tags/v2.5                       # object = e66094c…, tagger 2026-10-25 11:13:10
git merge-base --is-ancestor <peeled> main           # 7/7 true
git log --oneline 9976333..main                       # exactly e66094c
git ls-tree -r -l e66094c                            # boundary inventory
git hash-object ..\tools\_p1639_p3_official_igu.py
git rev-parse e66094c:tools/_p1639_p3_official_igu.py # must equal the hash-object above

cd <repo>
python tools\_p1641_verify_retrieval.py --manifest cloud_retrieved/round2_2026-10-25/SHA256SUMS.txt --dir cloud_retrieved/round2_2026-10-25
python -c "import hashlib;print(hashlib.sha256(open('cloud_retrieved/round2_2026-10-25/parquet/test-pope-random.parquet','rb').read()).hexdigest())"
Test-NetConnection connect.westb.seetacloud.com -Port 10137 -InformationLevel Quiet   # False
python tools\_p1639_p3_official_igu.py --self-test                                    # 37/37
```

---

## 8. 本审计的局限（诚实标注）

1. **审计者不是第三方**：我是本轮云端轮次的执行者，被审的归档、取回清单、脚本补丁都是我自己产出的。
   本审计能验证"主张是否与产物一致"，但**不能替代真正的第三方复核**（例如 `_p1640` 的 POPE 修正已由
   observer agent 从原始记录独立重算，那一次才算第三方）。
2. **远端只读核对**：用 `ls-remote` 取远端引用，没有 `fetch`（避免改动本地 refs）；
   因此"远端树内容"是通过本地 `e66094c` 不可变对象核对的——这依赖"该commit哈希在两处相同"，
   而 `main = e66094c` 已由 `ls-remote` 直接确认。
3. **tag 移动的证明是间接的**：git 无 tag reflog；本报告用"注解 tag 对象哈希本地↔远端相等"+"解引用 commit
   全部是 main 祖先"两条证据，未保留历史快照对照。
4. **未审**：稿件正文、各 paper_audit profile、SUBMISSION 冻结包（属 task-19 / task-21 范围）。
5. **一处观察**：主仓仍有未提交改动（含本轮文档与 `_p1650`/`_p1651`）；`e66094c` 已把其中
   `_p1650`/`_p1651` 收入公开树，但主仓的提交状态需 lead 自行收尾。

---

## 9. 现状复检（2026-10-25 11:37–11:45，`main` 已推进到 `b743651` 之后）

> 本节是**对当前状态的重跑**，不是对 §1–§8 的改写。§1.3/§1.4 记录的 `main = e66094c` 当时为真；
> 之后 **DOI 回填提交 `b743651`** 把 `main` 推进了一格，**tag `v2.5` 未被移动**（仍指 `e66094c`），
> 这正是"元数据改动不铸新 DOI、不动 tag"的正确行为。冲突时**以本节为准**。

### 9.1 逐项结果

| # | 检查项 | 结果 | 实测值 / 命令 |
|---|---|---|---|
| 1a | 远端 tag 清单 | ✅ | `git ls-remote --tags ssh-origin` → **7 个**：`v1.0-prl-revision`、`v2.0`、`v2.1`、`v2.2`、`v2.3`、`v2.4`、`v2.5`（全部 annotated，均有 `^{}` 解引用行） |
| 1b | `v2.5` 指向 | ✅ **未移动** | tag 对象 `03e6cebfe09c…` → target **`e66094c23dc2…`**；tagger `1792897990 +0800` = 2026-10-25 11:13:10 |
| 1c | 本地 ↔ 远端 tag 对象 | ✅ 逐一相等 | 本地：`e320e75 / 8d9d845 / 86a3836 / 0630332 / c557fa8 / 8caec6a / 03e6ceb`，与 `ls-remote` 完全一致 ⇒ 无 tag 被重建 |
| 1d | 远端 `main` / `HEAD` | ✅ | 两者均 **`b74365103a6467262380ce69d25960b1b1ac66f9`**（= 本地 `main`） |
| 1e | GitHub Release | ✅ **Latest** | `gh release list --repo MoYUYao666/gap-susceptibility --json tagName,isLatest,isDraft,publishedAt` → `v2.5`：`isLatest=true`、`isDraft=false`、`publishedAt=2026-10-25T03:19:51Z` |
| 1f | Zenodo DOI | ✅（注册与解析） | `https://doi.org/api/handles/10.5281/zenodo.23632347` → `responseCode=1`，URL `https://zenodo.org/doi/10.5281/zenodo.23632347`；concept `10.5281/zenodo.23341082` 同样 `responseCode=1`。元数据（`version=v2.5`、`related=…/tree/v2.5`）于 11:20 由 Zenodo API 取得，见 §1.5 |
| 2 | 公开边界（当前 `b743651`） | ✅ | **2,787** 文件 / **61.1 MB**；`paper*/`+`SUBMISSION/` **0**；`.tex` **0**；权重 **0**；`.parquet` **0**；≥100 MB **0**；`.npz` **1**（`outputs/analysis/a1_campaign_correct.npz` 75,755 B，仍是唯一二进制） |
| 2b | 最大五个文件 | ✅ | 7,326,030 `outputs/a1_h_templates.json`；6,679,520 `outputs/analysis/a23_multiencoder_transfer.json`；5,917,904 `tools/_tmp_a23_index.json`；4,523,829 `outputs/a1_h_baseline_metrics.json`；2,996,398 `outputs/analysis/lit_pool.json` |
| 2c | 两个 `.pdf` 的性质 | ✅ 非稿件 | `outputs/analysis/fig15_stratified_dg_r1.pdf`、`outputs/paper_figures/fig7.pdf`，均为**结果图** |
| 3a | 取回校验 | ✅ 47/48 | `python tools\_p1641_verify_retrieval.py --manifest cloud_retrieved/round2_2026-10-25/SHA256SUMS.txt --dir cloud_retrieved/round2_2026-10-25` → `== 47/48 verified ==`（唯一未过为已记录的 0 B 截断日志 `plan_recheck_20261025.log`） |
| 3b | POPE parquet | ✅ | **61,909 B**，sha256 **`66faa5e6de3be2374be68b8794a14cf660ff14670575ea47b9b77da8b43a71d4`** |
| 3c | 实例端口 | ✅ **False** | `Test-NetConnection connect.westb.seetacloud.com -Port 10137 -InformationLevel Quiet` → `False` |
| 4a | `p3_official_igu_run.json` | ✅ | 15,278 B、sha256 `8f4546ed…`；`runs[] = 6`；`runs_sha256` 用工具序列化**精确复现** |
| 4b | `p3_official_vs_reimpl.json` | ✅ | 16,214 B、sha256 **`4698a6e7…`**；内部：`verdict=small`、**`mean_gap_delta_E=-59.5`**、`ci95=[-150.5, -8.0]`、**`margin=196.05`**、`allocation_l1=2`、`within_tolerance=True` |
| 4c | `p3_official_igu_replicates.json` | ✅ | 4,322 B、sha256 `e38f65ab…`；6 臂；**重算 max = 132.00、mean = 76.0833**，与归档 `132.0 / 76.083333…` 一致；`passes_completed=2` |
| 4d | `p3_second_downstream.json` | ✅ | 15,406 B、sha256 **`41723dc2…`**；`refs_match_prepared_parquet_order=true`、`prepared_parquet_order_check=true`、`second_task_verdict=supports_the_adapters` |
| 4e | 锚点 1 | ✅ | `verify_r1_s42_bcexplicit_v11_s1_m3_d1.json` **937 B**、`212e9c75…` |
| 4f | 锚点 2 | ✅ | `verify_r1_s42_bcexplicit_v12_s1_m2_d1.json` **946 B**、`a060e2a8…` |
| 5a | 采纳脚本身份 | ✅ 三处一致 | `git hash-object tools/_p1639_p3_official_igu.py` = `001fb9961ceda28771ad1db69c8e97e64d07ac37` = `git -C publish_clean rev-parse b743651:tools/_p1639_p3_official_igu.py` ⇒ 工作区 = 公开树 |
| 5b | 缺陷 #1 修复 | ✅ | `:870 for path in expected[1:]` 在 `restore_side_effects()` 内；唯一一处 `restore_owned("training by-product", …)` 调用在 `:871`，**只作用于 `expected[1:]`** |
| 5c | 缺陷 #2 修复 | ✅ | `:937 def merge_block_maps`；`:961` 注释与逻辑"无权威来源时**保留** payload 原值，绝不用零和覆盖" |
| 5d | 可移植性 | ✅ | `:1491 tempfile.mkdtemp(prefix="p1639_selftest_", dir=REPO)` |
| 5e | `--self-test` | ✅ **37/37** | `assertion ledger: 37 checks, 0 failed`（含 [C] 恢复逻辑、[D] `block_maps` 合并两组回归） |
| 5f | `--workers` fork 隔离 | ✅ | `cloud_next/par_arms/_p1639_with_workers_94a48285.py` 在全仓仅被**文档**引用（`docs/p3_cloud_round2_notes.md`、本文件），**无 import、无执行**；且**不在公开树**（`git ls-tree b743651` 无此文件） |

### 9.2 复现命令（全部只读，base 解释器）

```powershell
cd <repo>\publish_clean
git ls-remote --tags ssh-origin; git ls-remote ssh-origin HEAD main
git for-each-ref refs/tags --format='%(refname:short) %(objectname) %(objecttype)'
git cat-file -p refs/tags/v2.5
gh release list --repo MoYUYao666/gap-susceptibility --limit 3 --json tagName,isLatest,isDraft,publishedAt
git ls-tree -r -l b743651        # 边界清点

cd <repo>
python tools\_p1641_verify_retrieval.py --manifest cloud_retrieved/round2_2026-10-25/SHA256SUMS.txt --dir cloud_retrieved/round2_2026-10-25
Test-NetConnection connect.westb.seetacloud.com -Port 10137 -InformationLevel Quiet
git hash-object tools/_p1639_p3_official_igu.py
git -C publish_clean rev-parse b743651:tools/_p1639_p3_official_igu.py
python tools\_p1639_p3_official_igu.py --self-test
```

（DOI 的注册/解析用 `Invoke-RestMethod https://doi.org/api/handles/10.5281/zenodo.23632347`，见 §9.3 的说明。）

### 9.3 本次**未能验证**的两项（如实标注）

1. **`zenodo.org` 的 API 在本次复检时不可达**：11:20 那次查询成功（记录 `23632347`、`version=v2.5`、
   `conceptdoi=23341082`、`related=…/tree/v2.5`，已记入 §1.5），但 11:40 前后连续 3 次
   `Invoke-RestMethod https://zenodo.org/api/records/23632347` 均报 DNS 解析失败
   （`请求的名称有效，但是找不到请求的类型的数据 (zenodo.org:443)`）。
   ⇒ 因此我改用**独立于 zenodo.org 的 DOI 解析**：`doi.org` handle API 返回 `responseCode=1`
   （即 handle 已注册）并指向 `https://zenodo.org/doi/10.5281/zenodo.23632347`，concept DOI 同样可解析。
   **"DOI 已注册且可解析"已证明；"Zenodo 记录页元数据在 11:45 时点仍如 11:20 所读"未能重新证明**（网络所限，非项目缺陷）。
2. **取回集 47/48 中的那 1 个失败项**仍为 `logs/plan_recheck_20261025.log`（0 B，实例上 11,010 B，下载被 SSH 中断截断），
   已用本地重跑件 `logs/plan_recheck_LOCAL_RERUN.log` 替代并在清单中注明。**该项无法"修好"——实例已关机，原始字节不可再取。**

### 9.4 结论

**无阻塞级发现。** 发布链条 `main(b743651) → tag v2.5(03e6cebf→e66094c，未移动) → Release(Latest) → Zenodo DOI 23632347`
完整且自洽；公开边界干净；云产物取回与校验通过；四个归档与两个锚点的哈希/内部计数全部吻合；脚本谱系与 `--self-test`（37/37）通过，
`--workers` fork 仍为未使用的冻结参考。§6 的 F1/F2/F3 三项非阻塞发现维持原判（其中 F1 的 `.err` 文件为 2026-10-14 `43b733c` 遗留，非本轮引入）。
