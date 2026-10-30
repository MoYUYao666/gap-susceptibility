"""Update the three operator-facing documents for the 2026-10-25 phase close.

Scope (append-only; no historical entry is edited):

1. `docs/p3_pope_integration_notes.md` - append the section that closes the prepared-parquet
   acceptance item (the parquet is now local), records the new aggregate sha256 and the honesty fix,
   and records the independent third-party recomputation of the POPE contrasts.
2. `HANDOFF.md` - insert a dated block immediately under the document title (the file's convention is
   newest-first).
3. `文件地图.md` - insert a dated status/todo block under its title.

Every number written here is traceable, and the trace is quoted next to it:

* P3 supplement 26 pages / 50 tables / 46 sections
  -> `paper3/paper_ieee/supplementary/supplementary.log` ("Output written on supplementary.pdf
     (26 pages, 433931 bytes)"), `\\begin{table*?}` count = 50, `\\section{` count = 46 in
     `paper3/paper_ieee/supplementary/supplementary.tex`.
* A23 73 pages -> `paper_a2/main_ieee.log` ("Output written on main_ieee.pdf (73 pages, ...)").
* POPE aggregate sha256 before/after -> `outputs/analysis/p3_second_downstream.json` and the
  pre-re-run copy `cloud_retrieved/round2_2026-10-25/pope/aggregate_before_rerun.json`.
* Cloud-round figures -> `outputs/analysis/p3_official_igu_run.json`,
  `outputs/analysis/p3_official_vs_reimpl.json`, `outputs/analysis/p3_official_igu_replicates.json`,
  `cloud_retrieved/round2_2026-10-25/`.

Idempotent: each block carries a marker and is skipped when already present.

Usage:
    python tools/_p1651_update_phase_close_docs.py [--apply]
"""

from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

POPE_MARKER = "POPE 验收闭环（2026-10-25 收尾）"
POPE_APPEND = """
---

## 9. `POPE 验收闭环（2026-10-25 收尾）`

> 本节由 `p3-downstream` 追加；前 8 节是 task-18 的原始记录，未改动。

### 9.1 关闭 `acceptance.refs_match_prepared_parquet_order`

- 评估所用 prepared parquet 已本地化：`paper3/test-pope-random.parquet`
  **61,909 B**，sha256 **`66faa5e6de3be2374be68b8794a14cf660ff14670575ea47b9b77da8b43a71d4`**
  （与实例上同名文件哈希一致；来源 `cloud_retrieved/round2_2026-10-25/parquet/test-pope-random.parquet`）。
- 重跑命令（纯 CPU）：`python tools/_p1640_p3_second_downstream.py --aggregate --strict`
  → 输出末行 **`[5] strict acceptance: satisfied`**。
- `acceptance.refs_match_prepared_parquet_order` 现在由 `refs_match_parquet()` **真实逐行比对**
  parquet 的 `output` 列得到，而不是"预存 parquet 缺失时的替代不变量"。
- 聚合归档 sha256：
  - 重跑前（parquet 不在本机）：`52e4e7bd377d85cdf9cc1343a5dfe5bcb04c0b513864acb0bd3d2941e3f8f2fe`（15,379 B，
    副本 `cloud_retrieved/round2_2026-10-25/pope/aggregate_before_rerun.json`）
  - 重跑后（含诚实性修复，见 9.2）：**`41723dc2f1be53cf0eba0adb132c0381cf64f3524893b8fe25ab643b9dfe9e97`**（15,366 B）
- **数值零变化**：新旧 JSON 深度比对只有 **2 处差异，且都不是数值**——
  `meta.dataset.prepared_parquet`（`"not retrieved locally (see the per-arm meta)"` →
  `"paper3/test-pope-random.parquet"`）与新增字段 `acceptance.prepared_parquet_order_check: true`。
  所有 contrast 的 `delta` / `ci95` / `tost_p` / `min_equivalent_margin`、以及
  `claim_verdict.second_task_verdict = supports_the_adapters` **逐位不变**（token-F1 修正与判定修正都保住了）。

### 9.2 顺带修掉一处"把未验证写成已验证"的诚实性缺陷

- **缺陷**：`_p1640` 在 parquet 缺失（`--allow-missing-prepared`）时把行序检查写成**字符串**
  `"NOT_VERIFIED_LOCALLY (prepared parquet absent on this machine)"`，但 `aggregate_core()` 用
  `bool(match_parquet)` 存盘，而 **`bool(<非空字符串>) == True`** ⇒ 归档里出现
  `refs_match_prepared_parquet_order: true`，**而该检查从未执行**，且该字符串本身没有落盘、事后无从察觉。
  证据：重跑前归档里 `refs_match_prepared_parquet_order: true` 与
  `prepared_parquet: "not retrieved locally (see the per-arm meta)"` **同时存在**，全文无 `NOT_VERIFIED` 字样。
- **修复**：`tools/_p1650_fix_pope_acceptance_bool.py`（幂等，带断言）把该字段改为
  「`match_parquet` 是 bool 就照抄，否则记 `False`」，并新增
  `acceptance.prepared_parquet_order_check` **原样保存**哨兵字符串。布尔键类型与语义不变
  （= 行序到底有没有被真实验证），下游消费者不受影响。
- 修复后重跑仍是 `[5] strict acceptance: satisfied`，`prepared_parquet_order_check: true`。

### 9.3 第三方独立复算（另一 agent，2026-10-25）

该 agent 从**各臂原始逐题记录**重算，用归档的 `norm()`/`token_f1()`、20,000 次配对 bootstrap、RNG 20261024：

| 对比 | 指标 | 点估计 | 95% CI |
|---|---|---|---|
| base−r5 | accuracy | **−0.246000** | [−0.262667, −0.229658] |
| base−r5 | token F1 | **−0.189065** | [−0.203349, −0.174709] |
| base−r6 | accuracy | **−0.214000** | — |
| base−r6 | token F1 | **−0.158350** | — |
| r5−r6 | accuracy | **+0.032000** | — |
| r5−r6 | token F1 | **+0.030715** | — |

点估计与修正后聚合（`52e4e7bd…`）**完全一致**，CI 在 bootstrap 噪声内，判定 `supports_the_adapters`
与修正版一致、与被取代的旧版（`1c389125…`）相反 ⇒ **该修正得到独立第三方验证**。

**口径提醒（必须保持的边界）**：base 的 yes-class F1 仍**更高**（0.8849 vs 0.8593/0.8237），
因为适配器预测 "yes" 更少（0.4327 → 0.4123/0.3733）；`claim_verdict.metric_directions` 已分开记录。
⇒ **判定标签不得被扩大**为"全面更好"，正确表述只有：
**accuracy 与 token F1 提升、yes-class F1 下降**（指标依赖的第二下游结果）。
"""

HANDOFF_MARKER = "2026-10-25 11:00 —— 云端第 2 轮收尾"
HANDOFF_BLOCK = """## ☁️ 2026-10-25 11:00 —— 云端第 2 轮收尾：POPE 第二下游 + 官方 IGU 六臂 + 发布再暂存

**做了什么 → 结果 → 还差什么**

### 1. 科学结果

- **POPE 第二下游任务（task-18 交付，本轮闭环验收）**：指标依赖结果 —— **accuracy 与 token F1 提升、
  yes-class F1 下降**（base 的 yes-class F1 更高：0.8849 vs 0.8593/0.8237，因为适配器预测 "yes" 更少：
  0.4327 → 0.4123/0.3733；`outputs/analysis/p3_second_downstream.json :: claim_verdict.metric_directions`）。
  判定 `claim_verdict.second_task_verdict = supports_the_adapters`（**仅**就 accuracy 而言）。
  验收项 `acceptance.refs_match_prepared_parquet_order` 本轮**真实闭环**：prepared parquet 已本地化
  `paper3/test-pope-random.parquet`（61,909 B，sha256 `66faa5e6…`），`--aggregate --strict` 输出
  `[5] strict acceptance: satisfied`；聚合归档 sha256 `52e4e7bd…` → **`41723dc2…`**，
  **数值零变化**（只差 1 个 meta 路径字符串 + 1 个新增验收字段）。详见 `docs/p3_pope_integration_notes.md` §9。
- **官方 IGU 实现对比（task-17）**：六臂齐（`official_corrected_map`、`reimpl_igu_style` × seed 42/123/789），
  `outputs/analysis/p3_official_igu_run.json :: runs[]` 共 **6** 条；`--compare` 判定 **`small`**
  —— 配对均值差 **−59.5**、95% CI **[−150.5, −8.0]**、预声明 margin **196.05**（5%×E(0)）、
  块级 rank **L1 = 2/16**（容差 2）、`arm_verdict = equivalent`
  （`outputs/analysis/p3_official_vs_reimpl.json`，sha256 `4698a6e7…`；另一会话独立取回同一哈希）。
- **复现性实测（必须与判定同报）**：每臂再跑 2 次（`--force` 破缓存），
  `outputs/analysis/p3_official_igu_replicates.json`：**极差最大 132.0、均值 76.1**
  ⇒ 与被判定的差距 59.5、归档差距 92.5 **同量级** ⇒ **两个分配规则的差异小于 run-to-run 噪声**；
  定量框架用 margin 196.05 + L1=2，**不得**把单 seed 的 ΔE 当可复现读数。
  根因：`paper3/scripts/run_training.py:75` 设了 `manual_seed` 但未启用
  `use_deterministic_algorithms`/`cudnn.deterministic`，4-bit 反量化与 cuBLAS 归约非位可复现。

### 2. 两个工具缺陷与修复（都在 `tools/_p1639_p3_official_igu.py`）

- **缺陷 #1**：`run_one_arm` 训练后对 `predict_side_effects()` 的**整个列表**调 `restore_owned()`，
  而新文件名目标臂的 `prev is None` ⇒ **训练成功后把自己的产物删掉**，报
  `RuntimeError: no usable archive … after training`。原始 `:885-886`。6 臂里 **5 臂**受影响。
  修复：`for path in expected[1:]`（只回滚副产物）+ 训练后断言 target 存在且可解析 +
  `--self-test` [C] 回归（旧逻辑会 FAIL、新逻辑通过，双向验证）。
- **缺陷 #2**：`--stage train` 收尾重建 `block_maps` 时读 `run["module_ranks"]`，但分配阶段存在
  `allocation_stage.module_ranks` ⇒ 读到空 ⇒ 全零求和 ⇒ 把正确 `[11,1,2,2]` **覆盖成 `[4,4,4,4]`**，
  下一次 train 以 `corrected allocation … differs from the pinned` exit 2。修复：抽出
  `merge_block_maps()`（优先级 显式映射 > `module_ranks` 两处任一 > **保留原值，绝不零覆盖**）+
  `--self-test` [D]；归档用 `tools/_p1645_repair_run_archive_block_maps.py` **确定性重建**
  （`9f10aec7…` → `969875fd…`，`runs[]` 逐字节不变）。
- **关键教训**：`--plan` 25/25、`--self-test` 30/30、`--dry-run` exit 0 **三者全绿也抓不到缺陷 #1**，
  因为都不执行训练步；**按并行规则第 1 步做的"单臂冒烟"一步就抓到**。⇒ "先确认没有 bug"这一步必须真跑。
- 版本谱系：`16f38e47`（原始）→ `2d2d7057`（缺陷#1）→ `f2b53f85`（缺陷#2+自检，**产出六臂**）→
  `2065ebbb`（Windows 可移植性，最终）。`--self-test` 在实例 Linux 与本地 Windows 均 **37/37 通过**。
  `f2b53f85` 精确字节随实例丢失，**未伪造**，谱系与差异见
  `cloud_retrieved/round2_2026-10-25/script/_p1639_patch_lineage.md`。

### 3. 单写者事故（"禁止重复作业"实证）

- 10:18:35 发现**同一实例上另有一个 one-shot agent 的 JOB B 在跑**（PID 7823/7824/7826/**7829**，
  7829 是 `_p1639 --run-official --stage train --config official_corrected_map --seeds 42`）；
  按 lead 指示终止竞争进程（拆分字面量 `pkill`，避免误杀自己），之后 `ps`=NONE、GPU 12,923 MiB→0。
- 孤儿效应：被杀父进程的 `run_training.py` 子进程仍跑完并写出 ΔE 181.0 的臂归档，**移走留档、不复用**；
  official/s42 用补丁版重训为 182.5（`from_cache=False`）。副产物
  `verify_r1_s42_b1_partial.json` 停留在孤儿 transient 版（`4985ab20…`），实例非 git 仓库无法从 VCS 还原；
  该文件不承载发表数字，其哈希被用作回归基线（我的全部运行都不改它）。
- 另一 agent 曾在本机 `tools/_p1639_p3_official_igu.py` 上加 `--workers`（`94a48285…`），
  **存档备查、未采用**；其并行 fork `cloud_next/_p1639_parallel_variant.py`（`46061981…`）**仅作冻结参考**。
- **结论**：两个独立 agent 驱动同一实例，**唯一的发现机制是一份状态汇报**；最终靠"指定单写者 + 终止竞争进程"收敛。

### 4. 成本模型更正（readiness 文档未改，由 lead 改）

- 实测 **55 s/臂（其中训练 36 s）**，**只有 5 个臂需要训练** ⇒ 本阶段约 **5 分钟**；
  原 readiness 文档写「~25 min/臂、6 臂 = 2.5–3.5 GPU 小时」⇒ **高估约 30×**。
- **GPU 利用率**：训练期间 **79–100%**（"只用 7%"是 GPU 空闲时的读数）。
- 并发：实测单臂峰值 **12,923 MiB** ⇒ 上限 **2**（2×12.9=25.8 GiB < 31.47 GiB×85%=26.75 GiB；3 路 38.7 GiB 超限）；
  实测 OOM（并行尝试 3 进程）与吞吐（并发存活臂 54 s vs 串行训练 36 s ≈1.5× 慢）⇒ **本阶段串行**，
  理由是整文件 read-modify-write 会互相丢 `runs[]`，风险大于省下的 ~2 分钟。详见
  `docs/p3_cloud_round2_notes.md` 末尾中文节 §A.7。

### 5. 实例终止与取回

- **实例端口已关闭**（`Test-NetConnection connect.westb.seetacloud.com -Port 10137` 多次返回 **False**；
  裸 TCP `ConnectionRefusedError`；`ssh -p 10137` 拒连；同主机名端口 22 仍应答 = AutoDL 宿主而非容器）。
- **这次关机不是本 agent 发出的**：由**本轮的另一个 agent**（我继承其 POPE 链的那个 one-shot agent）
  执行 `sync; (shutdown -h now || poweroff || ...)` 并三方验证 —— 这也解释了我在取回途中 SFTP 被切断
  （39 文件只到 33 个）。**如实记录，不冒领**。
- 取回：`cloud_retrieved/round2_2026-10-25/` —— 校验 **47/48**；唯一未通过是
  `logs/plan_recheck_20261025.log` **被中断截断为 0 B**（实例上 11,010 B），已用**本地重跑件**
  `logs/plan_recheck_LOCAL_RERUN.log` 代替并在清单里注明；缺失的 6 个文件全部从本地既有副本补齐、
  逐文件标注来源（`tools/_p1647_assemble_retrieval.py`）。科学产物的完整性另有强证据：
  六条 `runs[*].sha256` 与本地臂文件 **6/6 逐位一致**，归档 `runs_sha256` 可精确复现，
  parquet 与实例哈希一致。

### 6. 发布状态

- `publish_clean` 现为 **`5ad7724`**（v2.5 两提交之上再叠加本轮第三提交，见下）。
  本轮把云轮归档、修正后的 POPE 聚合、新工具、以及 notes 之外的发布件同步进去；
  **未 push、未 tag**。推送与 `v2.5` tag、Zenodo DOI 由 lead 执行。
- **边界**：不含稿件、不含权重、无 ≥100 MB 文件；`docs/**` 按操作者指示不入公开仓库。

**待办**：① lead 执行 push `main` + tag `v2.5` + 取 Zenodo DOI；② `HANDOFF.md` 的
`tools/` 行号引用本轮未受影响（新脚本一律新增，不改旧文件）；③ 云端侧**已无待办**
（实例已停、产物已取回、验收已闭环）。

"""

MAP_MARKER = "2026-10-25 11:00 状态更新"
MAP_BLOCK = """> **🛰️ 2026-10-25 11:00 状态更新：云端第 2 轮跑完并收尾，发布件再暂存（第三提交）**
>
> **本轮改变的事实**（每条都能指名文件）：
>
> | 项 | 状态 | 依据 |
> |---|---|---|
> | **Paper 3 补充材料** | **26 页 / 50 表 / 46 节**，内含 POPE 小节（S29 新增 `\\subsection`） | `paper3/paper_ieee/supplementary/supplementary.log`（"Output written on supplementary.pdf (26 pages, 433931 bytes)"）；`\\begin{table*?}`=50、`\\section{`=46 于 `supplementary.tex` |
> | **A23** | **73 页**，声呐域迁移主张已**限定边界**，下一版修订包已暂存 | `paper_a2/main_ieee.log`（"Output written on main_ieee.pdf (73 pages, 1275901 bytes)"） |
> | **POPE 第二下游** | 已整合为**指标依赖**结果：accuracy 与 token F1 升、yes-class F1 降；验收 `refs_match_prepared_parquet_order` 本轮**真实闭环** | `outputs/analysis/p3_second_downstream.json`（sha256 `41723dc2…`）；`docs/p3_pope_integration_notes.md` §9 |
> | **官方 IGU 对比** | 判定 **`small`**：配对 −59.5、CI [−150.5, −8.0]、margin 196.05、L1=2 | `outputs/analysis/p3_official_vs_reimpl.json`（`4698a6e7…`） |
> | **复现性** | 同臂三次运行极差 **最大 132.0 / 均值 76.1** ⇒ 差异小于噪声 | `outputs/analysis/p3_official_igu_replicates.json` |
> | **两个云端作业** | **均已执行完毕**（IGU 六臂 + POPE），实例已停、产物已取回 | `cloud_retrieved/round2_2026-10-25/`（47/48 校验） |
> | **发布** | `publish_clean` 第三提交已建（基线 `5ad7724`），**未 push / 未 tag** | `git -C publish_clean log --oneline -1` |
>
> **还剩什么（仅两件，均在 lead 手上）**：
> ① **v2.5 的 push + tag + Zenodo DOI**（按 DOI/tag 冻结纪律：新版本用新 tag，**不得**重打已冻结的 tag）；
> ② **A23 下一版修订的 cover letter**。
> **云端侧已无待办**：实例已关机、产物已取回并校验、POPE 验收已闭环、IGU 对比与复现性已归档。
>
> **诚实标注**：本轮实例的 `shutdown` 由**本轮另一个 agent** 发出（非本 agent），端口已确认关闭；
> 取回有 1 个日志被中断截断为 0 B，已用本地重跑件替代并注明（详见 `docs/p3_cloud_round2_notes.md` §A.9）。
"""


def insert_after_title(path: Path, block: str, marker: str, apply: bool) -> str:
    text = io.open(path, encoding="utf-8").read()
    if marker in text:
        return "%s: already present, skipped" % path.name
    lines = text.splitlines(keepends=True)
    if not lines or not lines[0].startswith("#"):
        return "%s: ERROR no title line" % path.name
    head = lines[0]
    rest = "".join(lines[1:])
    # keep exactly one blank line between the new block and the old content
    merged = head + "\n" + block + ("\n" if not block.endswith("\n") else "") + rest
    if not apply:
        return "%s: would insert %d bytes" % (path.name, len(block.encode("utf-8")))
    with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(merged)
    return "%s: inserted %d bytes (now %d lines)" % (path.name, len(block.encode("utf-8")),
                                                     len(merged.splitlines()))


def append_section(path: Path, block: str, marker: str, apply: bool) -> str:
    text = io.open(path, encoding="utf-8").read()
    if marker in text:
        return "%s: already present, skipped" % path.name
    merged = text.rstrip("\n") + "\n" + block
    if not apply:
        return "%s: would append %d bytes" % (path.name, len(block.encode("utf-8")))
    with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(merged)
    return "%s: appended %d bytes (now %d lines)" % (path.name, len(block.encode("utf-8")),
                                                     len(merged.splitlines()))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    jobs = [
        ("append", REPO / "docs" / "p3_pope_integration_notes.md", POPE_APPEND, POPE_MARKER),
        ("insert", REPO / "HANDOFF.md", HANDOFF_BLOCK, HANDOFF_MARKER),
        ("insert", REPO / "文件地图.md", MAP_BLOCK, MAP_MARKER),
    ]
    rc = 0
    for kind, path, block, marker in jobs:
        if not path.is_file():
            print("ERROR: missing %s" % path)
            rc = 2
            continue
        fn = append_section if kind == "append" else insert_after_title
        print("  " + fn(path, block, marker, args.apply))
    if args.apply:
        for _, path, _, marker in jobs:
            text = io.open(path, encoding="utf-8").read()
            path.read_bytes().decode("utf-8")          # strict decode: no mixed encoding
            assert marker in text, "marker missing in %s" % path.name
            assert "#" in text.splitlines()[0], "title line lost in %s" % path.name
            print("  verified %s (strict UTF-8, marker present, title intact)" % path.name)
    return rc


if __name__ == "__main__":
    sys.exit(main())
