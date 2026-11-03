# -*- coding: utf-8 -*-
r"""Record round 3: A1 interior-optimum monitoring validation, A1/PaperA audit state, mirror staging.

    python tools/_p1356_record_round3.py [--apply]
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HANDOFF = REPO / "HANDOFF.md"
MAP = REPO / "文件地图.md"
EVID = REPO / "docs" / "EVIDENCE_MAP_2026-10-19.md"
PLAN = REPO / "docs" / "UPGRADE_PLAN_2026-10-19.md"

ENT = """> **🎯 2026-10-19 19:40 —— A1 补上最后一块：内部最优点下的监控验证（重跑，本地 6 分钟）**
>
> 之前"A1 监控声明只能当诊断、不能当早停"的缺口，本轮用**同域留出评测**补上了：CLIP B/32 文本塔 LoRA，DTD（47 类）
> 与 Food-101（101 类）各 40 张/类训练、留出 12–15 张/类，8 个 epoch × 2 seed = **4 条轨迹 / 32 个 checkpoint**。
>
> | 指标 | 结果 |
> |---|---|
> | 准确率轨迹 | 非单调：Food-101 最优在第 6 epoch，DTD 在第 7–8；首轮平均落后最优 **4.03** 点 |
> | **min-$M(0.01)$ 选 epoch** | 平均 regret **0.19**（最差 0.74）——无标签、几乎不输 oracle |
> | min-CG 选 epoch | 平均 regret **2.19**（最差 3.40）|
> | 训练到末轮 | 平均 regret **0.76** |
> | 池化 32 点相关 | $r(M,\\text{top-1})=-0.983$；$r(\\text{CG},\\text{top-1})=+0.32$（符号再次翻转）|
>
> 已写入 `paper_a1/main.tex` 监控小节（60 页 0/0/0）；归档 `outputs/analysis/a1_monitor_interior.json`；
> A1 ledger **187/187 PASS**（新增 9 条主张）。
>
> **审计**：A1 仅剩预期 I-02（冻结包 vs 本地）；Paper A Springer **READY/A**（重建后 A-04 消除）；Paper A NC 仅剩预期 I-02。
> **镜像**：新归档与分析脚本已加入 `_p1284` 暂存清单（尚未推送，等操作者确认）。
>

"""

EVID_ROW = """
| A1 interior-optimum monitoring (n=32 checkpoints, min-M regret 0.19, r(M)=-0.983) | `outputs/analysis/a1_monitor_interior.json` | `tools/_p1354_monitor_interior.py` |
"""

PLAN_ADD = """

## Round 3 (2026-10-19 19:40): A1 monitoring validation completed

The earlier plan item "monitoring claim scoped as a diagnostic, early stopping left open" is now closed by a re-run in a
regime with an interior optimum (same-domain held-out evaluation, DTD + Food-101, 4 trajectories / 32 checkpoints):
minimum-margin-mass epoch selection reaches mean regret 0.19 (worst 0.74) without labels, against 2.19 for the gap rule,
0.76 for training to the end and 4.03 for the first epoch; pooled r(M, top-1) = -0.983 while r(CG, top-1) = +0.32.
`paper_a1/main.tex` 60 pages, A1 ledger 187/187.
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  (dry run)")
        return 0
    h = io.open(HANDOFF, encoding="utf-8").read()
    if "A1 补上最后一块" not in h:
        i = h.find("# 项目交接文档")
        j = h.find("\n", i)
        io.open(HANDOFF, "w", encoding="utf-8", newline="").write(h[: j + 1] + "\n" + ENT + h[j + 1:])
        print("  handoff entry added")
    mp = io.open(MAP, encoding="utf-8").read()
    row = ("113. 🎯 **A1 监控验证补齐（2026-10-19 19:40）** —— 同域留出评测重跑（DTD+Food-101，4 轨迹/32 checkpoint）："
           "min-M 选 epoch 平均 regret **0.19**（首轮 4.03、末轮 0.76、min-CG 2.19）；池化 $r(M,top1)=-0.983$、"
           "$r(CG)=+0.32$；写入 `paper_a1/main.tex`；A1 ledger **187/187**；A1 仅剩预期 I-02；Paper A Springer READY/A。\n")
    if "A1 监控验证补齐（2026-10-19 19:40）" not in mp:
        anchor = "112. 🔁 **升级继续（2026-10-19 18:50）"
        idx = mp.find(anchor)
        assert idx >= 0
        end = mp.find("\n", idx)
        io.open(MAP, "w", encoding="utf-8", newline="").write(mp[: end + 1] + row + mp[end + 1:])
        print("  map row added")
    ev = io.open(EVID, encoding="utf-8").read()
    if "A1 interior-optimum monitoring" not in ev:
        io.open(EVID, "w", encoding="utf-8", newline="").write(ev.rstrip() + EVID_ROW)
        print("  evidence map extended")
    pl = io.open(PLAN, encoding="utf-8").read()
    if "A1 monitoring validation completed" not in pl:
        io.open(PLAN, "w", encoding="utf-8", newline="").write(pl.rstrip() + PLAN_ADD)
        print("  plan updated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
