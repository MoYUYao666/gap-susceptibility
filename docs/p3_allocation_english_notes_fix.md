# P3 分配配对归档：两条中文 note 英文化并重新暂存 v2.5（2026-10-25）

**状态：已完成（附证据）。** 归档已重生成、门禁已复跑、`publish_clean/` 已产生**新提交**（未 amend、未 push、未 tag）。

本轮处理的是 `docs/V25_RELEASE_PREP_2026-10-25.md` 第六节"待决定项"里的方案 B：`p3_allocation_paired_stats.json`
含 2 条**本轮新产物**的中文散文叶子（属"新建产出物一律英文"的违例）。该文档当时因写权限限制未擅自处理。

---

## 一、两条字符串及其来源（实测，非推测）

| 归档字段 | 中文原文 | 谁写的 |
|---|---|---|
| `controls.random_pool.archived_tests.levene_note` | 方差判据用 within_resid（Γ-guided vs 组内残差池）；mixed_pool 版本含组间差异，不应直接比 | `tools/_p458_random_pool_test.py` 第 276–277 行 → 落到 `outputs/analysis/p3_alloc_random_pool.json::tests.levene_note`（该文件第 203 行） |
| `controls.random_pool.archived_power_diagnosis.rule` | 同分配内 seed 极差 ≥ 方案间均值差 ⇒ 判为功效不足 | `tools/_p458_random_pool_test.py` 第 297 行 → 落到 `outputs/analysis/p3_alloc_random_pool.json::power_diagnosis.rule`（该文件第 233 行） |

**继承路径**：`tools/_p1634_p3_allocation_paired.py` 把这两个块**整体拷贝**出去
（原第 789 行 `"archived_tests": tests`、第 792 行 `"archived_power_diagnosis": pool_doc["power_diagnosis"]`），
所以中文是**继承**来的，不是本轮脚本写的。溯源命令：

```powershell
git grep -n "levene_note" -- tools outputs
git grep -n "同分配内 seed 极差" -- tools outputs
```

**裁决**：源归档 `p3_alloc_random_pool.json` **保持中文不动**——它是既有存量产出物（语言规则"只管今后，存量不动"），
改它会让它与自己的生成脚本 `_p458` 脱钩；要改的是**新**归档，所以改在 `_p1634` 的拷贝点。

## 二、英文替换（字段名 / 嵌套 / 数值全部照旧）

新增助手函数 `inherited_note(block, field, english)`（`_p1634_p3_allocation_paired.py`），
做浅拷贝后只替换一条散文叶子，统一加前缀点名来源：

```
inherited from outputs/analysis/p3_alloc_random_pool.json :: <field>, translated from the Chinese
original for repository language compliance; <英文释义>
```

| 字段 | 英文替换文本（`<前缀>` 之后的释义部分） |
|---|---|
| `archived_tests.levene_note` | the variance criterion uses within_resid (the Gamma-guided arm against the within-group residual pool); the mixed_pool version mixes between-plan differences and must not be compared directly |
| `archived_power_diagnosis.rule` | if the within-plan seed range is at least the between-plan mean difference, the comparison is called underpowered |

脚本内 `inherited_note` 的 docstring 与模块 docstring 都写明了"**为什么这里是英文而源归档保留中文**"
（源归档是既有产出物、被语言规则豁免；本脚本写的是新产出物，必须英文）。
顺带修正了 `load_json_readable` docstring 里"note 字段不被本分析使用"的旧说法——该说法与拷贝行为不符。

## 三、重生成与证据

命令：`python tools/_p1634_p3_allocation_paired.py`（默认 20000 resamples，退出码 0，41 个 print-to-JSON 断言 0 失败、51 个 addendum 复现检查 0 失败）。

| 证据 | 结果 |
|---|---|
| 两次运行**逐字节一致** | 运行 1 与运行 2 的文件 sha256 均为 `c5965d83089495497b32aa9d62dc8de7391bd5d4e232c70d5887c5760f48fbae` → **True**（92158 B） |
| `meta.result_sha256` 稳定 | 两次均为 `249d805f66c106108ab3b4a39ddaeec400023652ab27f0594f1ada77395631ea`（旧值 `e5a802c3…`）；脚本自报 on-disk 与本次一致 |
| **零 CJK** | 新归档 CJK 字符 **0**；更强：全文件**非 ASCII 字符 0**（旧文件 44 个 CJK，含 `Γ`、`⇒`、全角括号） |
| 数值叶子 diff | 叶子总数 1929 → 1929（路径集合完全相同），其中数值/布尔/null 叶子 **1316 个，变化 0 处**；数值指纹 sha256 两者同为 `0bc40333…` |
| 变化仅 4 个字符串叶子 | 2 条 note，加 `meta.git_commit`（`5b865a94…` → `7bed09ee…`，记录生成时的 live HEAD）与 `meta.result_sha256` |
| 两个拷贝块 | 键集合一致；`archived_tests` 8 个数值键、`archived_power_diagnosis` 4 个数值键，逐一相同（嵌套 `within_plan_seed_ranges` 亦含在全局 1316 个数值叶子之内，0 变化） |

## 四、门禁复跑

| 门禁 | 命令 | 结果 |
|---|---|---|
| 溯源门禁 | `python tools/_p1428_provenance_gate.py` | **PASS**（A1 浮点 35/35、paperA 32/32、P3 4/4、A23 34/34，missing 0 / pending 0 / broken_paths 0） |
| P3 复现账本 | `python tools/_p1637_p3_reproduce_all.py --check --quiet` | **OK 902 / MISMATCH 0 / UNSOURCED 0**（TOTAL 940，其余为 ANALYTIC/THIRD_PARTY 等非重算类别） |
| 指向本归档的账本条目仍可解析 | `… --check --only MAIN-IV-E` | **OK**：`e-power-lo` 打印 11 → 重算 11.15927951；`e-sep-value` 打印 3570 → 重算 3570.098307（二者都读 `p3_allocation_paired_stats.json::paired.capacity_matched_by_seed.mean_difference`） |
| 稿件审计 | `python -m tools.paper_audit audit --profile p3_prl --fail-on NONE` | **READY / grade A / pass=50 fail=0 warn=0 manual=9 skip=27 error=0**（退出码 0） |

关于"git-dirty 失败"：本 profile 的清洁度检查 **A-01 只覆盖稿件目录**（`paper3/paper_ieee`），
本轮只改了 `tools/` 与 `outputs/`，故 **A-01 仍 PASS、没有出现 dirty 失败**；审计报告头部如实记为
`7bed09ee1804 on master (dirty tree)`。审计报告按工具惯例归档到 `docs/audits/AUD-p3_prl-20261025T011259Z.{md,json}`。

## 五、v2.5 重新暂存

```powershell
python tools/_p1641_sync_publish_v25.py            # 干跑：确认只多出 2 个变更文件
python tools/_p1641_sync_publish_v25.py --apply    # 复制进 publish_clean/（不提交）
git -C publish_clean add -A
git -C publish_clean commit -m "<英文提交信息>"
python tools/_p1641_sync_publish_v25.py --preflight --rev HEAD
```

| 项 | 值 |
|---|---|
| **新提交** | **`5ad772488fdea93d881a66ab8aca137983644c8a`**（短 `5ad7724`） |
| 父提交 | `e202db8c93e175a4591df38dc5328b0bbb71fbe8`（原 v2.5 暂存提交，未改动） |
| 变更 | **2 个路径，均为修改（0 新增 / 0 删除）**：`outputs/analysis/p3_allocation_paired_stats.json`、`tools/_p1634_p3_allocation_paired.py`；`39 insertions(+), 8 deletions(-)`，载荷 0.178 MB |
| 提交身份 | `Repository Maintainer <noreply@example.com>`（与 `e202db8` 一致） |
| 未做 | **未 amend**（reflog HEAD@{0} 为 `commit:`）、**未 push**、**未 tag**（`git -C publish_clean tag` 仍只到 `v2.4`） |
| 落库字节 | 提交后的 blob 与 live 文件**逐字节相同**（归档 sha256 `c5965d83…`、脚本 `aad72801…`；两者均为纯 LF） |

**pre-flight 五项（对 `5ad7724` 实测，verdict = PASS）**：

| 项 | 结果 | 数字 |
|---|---|---|
| (a) 稿件类 | **PASS** | 投稿页文件名 0、稿件目录路径 0 |
| (b) 大文件 | **PASS** | ≥100 MB 0 个；最大仍为 `outputs/a1_h_templates.json` 7.810 MB |
| (c) 权重/缓存 | **PASS** | 全库已跟踪权重类仅 1 个（`a1_campaign_correct.npz`，75,755 B，`e202db8` 之前既有），本轮新增 0 |
| (d) 中文 | **PASS**（原为 REVIEW 1 项） | 本轮 2 个文件**含中文散文 0**；`RELEASE_NOTES_v2.5.md` CJK 0；仅"豁免目录名"计数也为 0 |
| (e) 暂存差异 | **PASS** | 2 路径（0 新增 / 2 修改 / 0 删除），0.178 MB < 200 MB |

**结论**：v2.5 待发布内容重新回到"干净"状态——`docs/V25_RELEASE_PREP_2026-10-25.md` 第六节的
"方案 B（修）"已执行完毕，(d) 项由 REVIEW 升为 PASS。打 tag / 推送仍留给操作者，命令见该文档第三节，
但**目标提交应从 `e202db8` 改为 `5ad7724`**。

## 六、如何复核

```powershell
python tools/_p1634_p3_allocation_paired.py                 # 重生成（应与 c5965d83… 一致）
python tools/_p1428_provenance_gate.py
python tools/_p1637_p3_reproduce_all.py --check --quiet
python tools/_p1641_sync_publish_v25.py --preflight --rev HEAD
git -C publish_clean show --stat 5ad7724
```