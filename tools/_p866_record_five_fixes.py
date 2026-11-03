# -*- coding: utf-8 -*-
r"""Record the five PR-letter fixes as a handoff entry and a map row.

Covers: the language repair (29 truncated words plus one markdown leak), the two rank claims that
contradicted the measurements, the full-scale MS-COCO result now written into the manuscript, the
stratified DG-R@1 figure with its within-group statistics, and the state of the LLaVA write-in (the
script exists and refuses to run until the twelve runs land).

    python tools/_p866_record_five_fixes.py [--apply]
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HANDOFF = REPO / "HANDOFF.md"
MAP = REPO / "文件地图.md"
BT = chr(96)
MARK = "PR 拒稿信剩 5 条已做 4 条"

ENT = """> **🛠️ 2026-10-15 13:25 —— PR 拒稿信剩 5 条已做 4 条；第 5 条（LLaVA）脚本就绪待数据**
>
> 操作者指令：**「剩 5 条全做」**（对象 = 上一条 13:20 审核条目的 5 项）。
>
> ### 一、✅ 语言编辑（第 1 项，三位审稿人一致点名）
>
> `tools/_p857_fix_truncated_words.py` —— 逐处改写被截断的词，**不碰任何数字/引用/label**：
>
> | 项 | 实测 |
> |---|---|
> | 源文件截断词 | **29 处**（`analyz` 12、`optimiz` 9、`minimiz` 4、`normaliz` 2、`characteriz` 1、`summariz` 1）|
> | 涉及文件 | `empirical` 9、`supplement` 5、`validation` 4、`discussion` 4、`main_nc` 3、`related_work` 2、`conclusion` 1、`theory` 1 |
> | 初版编译件（2026-10-14）实测 | **28 处**在 PDF 里可见（源文件此后被改过，故源=29）|
> | 同时修掉 | `empirical.tex` 里漏进 LaTeX 的 markdown `**not used**` → `\\emph{not used}` |
> | 规则 | 只匹配**独立成词**的截断形（`analysis`/`analyzer`/`normalization` 等完好形式不动）；逐句按上下文选正确词形 |
>
> ### 二、✅ 两条与实测相反的秩断言（第 2 项）
>
> `tools/_p859_rank_claims_clean.py`（替代首次失败、留下不一致状态的 `_p858`）：
>
> | 原断言 | 问题 | 改写为 |
> |---|---|---|
> | *"Increasing configured rank beyond the task's effective rank expands alignment-vulnerable parameters **without adding gradient capacity**"* | 与实测**相反** | 「gap 变化随配置秩**趋近于 0**，趋近方向由**语料**决定」＋给出 flickr/COCO 两组逐秩数 |
> | *"the text-only arm **improves monotonically with rank**"* | 只在 COCO 成立（Flickr30k 是反向单调）| 「秩效应的符号由语料决定」＋两组数据 |
> | *"higher rank now preserves the gap better **rather than reversing**"* | 趋势不是"反转"，是**收敛到不变** | 「从'扩大'一侧收敛到不变」 |
>
> **支撑数**（**全来自归档**）：`flickr_rank.json` dCG −0.0195(r1) / −0.0244(r4) / −0.0176(r8) / −0.0123(r16, r32) / −0.0019(r64)；`rank_rerun.json` dCG +0.0135(r2) → +0.0021(r64)。
> **两个副本都改**（工作副本 + `NC_submission/latex_source/`；后者用英式拼写，按其自身锚点匹配）。
>
> ### 三、✅ 全量 COCO 写进稿件（第 3 项，回应 R2-3「larger datasets」）
>
> `tools/_p863_coco_scale.py` —— 把 **40,504 图 / 202,654 caption 全 gallery** 的结果写入 `empirical.tex` 的检索协议段：
>
> * frozen **R@1 0.5655** → text-only **0.5823 ± 0.0002**（三 seed，rank 8，3 epoch，10,000 训练图）
> * 增益**单向**：t2i R@1 0.1316 → 0.1650，i2t 两臂都在天花板（0.9994 / 0.9997）
> * **如实标注三点**：只跑了 frozen + text-only 两臂（两适配位置的高低**未在本规模重测**）、3 epoch 比上面的 6 epoch 短、**两规模不可直接互读**
> * **NC 副本此前根本没有这段**（只有"COCO 全部近随机"），故同时把 3,000 图修复版补进去（值由 `coco_scaleup.json` 现算：0.579 / 0.607 / 0.623）
>
> ### 四、✅ 分层 DG–R@1 图（第 4 项，回应 R1-Q4 图 + R1-Q3「within-dataset/within-model」）
>
> `tools/_p860_fig_stratified.py` → `paper合/figures/fig15_stratified_dg_r1.pdf`（**图 15**），
> 由 `empirical.tex` 新增段落 + `\\label{fig:stratified}` 引用。**图与统计同源且当场断言**：
>
> | 量 | 值 | 归档 |
> |---|---|---|
> | within-dataset | **−0.751** | `pr_stats_within_group.json::pooled_within_dataset.r_within` |
> | within-model | **−0.707** | 同上 `pooled_within_model` |
> | within-design-cell | **−0.731** | 同上 `pooled_within_design_cell` |
> | within-family | **−0.551** | 同上 `pooled_within_family` |
> | SigLIP 反向 | **+0.808**（n=5）| 同上 `by_model.SigLIP.r` |
>
> **⇒ 这直接回答 R1 的怀疑**：组内相关（−0.71 ～ −0.75）与合并值 −0.714 **接近**，说明该关联**不是组间假象**；
> 例外是 SigLIP 反向（与适配位置控制的反向是同一处），且 n 小，文中写明只作**边界**读。
> **脚本先复算归档相关值再画图**（dataset/model 逐格断言一致），避免图与统计漂移。
>
> ### 五、⏳ 第 5 项（第二个 decoder VLM）—— 脚本就绪，等数据
>
> `tools/_p864_llava_supplement.py`：
>
> * **要求 12 个 run 全部齐备**（4 臂 × 3 seed）才写稿，缺一个就**拒绝执行**（已实测会拒绝：现在只有 3 个 frozen 记录）；
> * 读取时断言 `samples=400 / epochs=3 / rank=8` 且 `frozen` 三 seed 必须复现 **−0.7659953%** 的噪声地板；
> * 逐臂给"是否超过 **0.8%** 地板"的判定，并把 LLaVA 定位为**第二个 decoder 模型**（补 Qwen2-VL-2B 之外）；
> * 插入点 = `supplement.tex` E 节（`sec:vlm`）表前。
>
> ### 六、✅ 编译与台账（本轮复核）
>
> | 项 | 结果 |
> |---|---|
> | 编译（`main_nc.tex`，2 遍 pdflatex）| **59 页 / 0 错误**、无未定义引用、无 rerun 需求 |
> | 第一遍曾报错 | `Missing $ inserted`：`$0.5823 $\\pm$ $0.0002$` 留下**空数学组** ⇒ 已改为单一 `$0.5823 \\pm 0.0002$` 并**三段落拆分**（原为整块一页）；修后 0 错误 |
> | `_claim_ledger_paperA.py` | **PASS 52 ｜ GAP 0**（新增 §7 共 17 条：全量 COCO 4 条、3k 修复 3 条、组内相关 5 条、图 3 条等）|
> | `_claim_ledger.py` | **80/80** |
> | 遗留警告（**非本轮引入**）| `Float too large for page by 268.4pt`（`fig3`，`[h]` 放置）—— 早于本轮，待排版阶段处理 |
>
> ### 七、🆕 本轮修掉的两个我自己的失误
>
> 1. `_p858` 只改了一部分就断言失败，**把工作副本与 NC 副本改成不一致状态**（一处新旧文本并存）⇒ 已 `git checkout` 回到干净基线，重做并按**行号/上下文**核对；
> 2. 落账脚本的锚点写错（用了 NC 副本里不存在的句子）⇒ 改为**两个副本各自的锚点**，并让 NC 副本补上它本来就缺的 3,000 图段。
>

"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    hp = io.open(HANDOFF, encoding="utf-8").read()
    mp = io.open(MAP, encoding="utf-8").read()
    if MARK in hp:
        print("  already recorded")
        return 0
    if not a.apply:
        print("  (dry run)")
        print(f"  would prepend {len(ENT.splitlines())} lines to HANDOFF.md")
        return 0

    i = hp.find("# 项目交接文档")
    assert i >= 0
    j = hp.find("\n", i)
    hp = hp[: j + 1] + "\n" + ENT + hp[j + 1:]
    io.open(HANDOFF, "w", encoding="utf-8", newline="").write(hp)

    row = ("14. 🛠️ **PR 拒稿信剩 5 条已做 4 条（2026-10-15）** —— 语言 29 处截断词、两条与实测相反的秩断言、"
           "全量 COCO（40,504 图，frozen 0.5655 → text-only **0.5823 ± 0.0002**）、分层 DG–R@1 图"
           "（`figures/fig15_stratified_dg_r1.pdf`，组内 r −0.71～−0.75、SigLIP 反向 +0.808）**均已入稿**；"
           "第 5 条 LLaVA 写稿脚本 `tools/_p864_llava_supplement.py` **就绪但拒绝在 12 个 run 齐备前执行**。"
           "编译 59 页 / 0 错误；台账 **PASS 52 ｜ GAP 0**。详见 `HANDOFF.md` 顶部 2026-10-15 13:25 条目。\n")
    anchor = "13. ⚠️ **文档完整性规则（2026-10-15 立）**"
    idx = mp.find(anchor)
    assert idx >= 0, "map item 13 not found"
    end = mp.find("\n", idx)
    mp = mp[: end + 1] + row + mp[end + 1:]
    io.open(MAP, "w", encoding="utf-8", newline="").write(mp)

    h2 = io.open(HANDOFF, encoding="utf-8").read()
    m2 = io.open(MAP, encoding="utf-8").read()
    assert h2.split("\n")[2].startswith("> **🛠️ 2026-10-15 13:25"), "entry is not first"
    assert h2.count(MARK) == 1 and m2.count(MARK) == 1
    for k in ("PASS 52", "59 页", "fig15_stratified_dg_r1.pdf", "0.5823", "Missing $ inserted"):
        print(f"  {'OK ' if k in h2 else 'BAD'} handoff::{k}")
    print(f"  HANDOFF lines = {len(h2.splitlines())}  map lines = {len(m2.splitlines())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
