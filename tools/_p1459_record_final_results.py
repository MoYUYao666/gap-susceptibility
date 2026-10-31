# -*- coding: utf-8 -*-
r"""Record the final Round-2 results (P3 five seeds, P3 ablation, A1 both-tower) in the hand-off documents.

    python tools/_p1459_record_final_results.py --apply
"""
from __future__ import annotations

import argparse
import io
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HANDOFF = os.path.join(REPO, "HANDOFF.md")
MAP = os.path.join(REPO, "文件地图.md")
EVID = os.path.join(REPO, "docs", "EVIDENCE_MAP_2026-10-19.md")

ENTRY = """> **🧪 2026-10-21 03:10 —— Round 2 完成：P3 五 seed 统计达显著性 + 消融 + A1 双塔 LoRA**
>
> | 项 | 结果 |
> |---|---|
> | **P3 五 seed（r=5 vs r=6）** | r=5：−10.5/+8.0/−36.5/−27.0/−49.0，**−23.0 ± 22.3**（1/5 正）；r=6：+115.0/+25.5/+32.0/+62.0/+93.0，**+65.5 ± 38.5**（5/5 正）；差值 **+88.5**，精确双侧置换 **p=0.008**（5 seeds/rank 的最小可达值） |
> | **P3 入稿** | conclusion/experiments 的 seed 表述改为五 seed；"126 runs"→**132 runs**；补充材料新增 **S14**（per-seed 表）；正文仍 **10 页**、补充 **6 页**、0 错 0 overfull、`audit_check` 0/0 |
> | **P3 消融（num-samples 12/20/32/64）** | ΔE：**+40.5 / +115.0（默认 20）/ +44.5 / +30.0**（r=6, seed42）；幅度差 **3.8×**，符号不变；**已如实入稿 S15**（不声称临界点移动，只声称效应量依赖协议）|
> | **A1 双塔 LoRA 监控** | DTD/Food101 两域：最小 mass 规则**都选中 oracle epoch**（regret 0.0），末轮 regret 1.01、首轮 4.63；已入 A1 正文；A1 仍 **63 页** 0/0/0 |
> | **已跑时间** | 午夜后 GPU 恢复满速（21–27 min/run），2 个链式后台任务全部成功；**GPU 现已空闲** |
>
> 待办：五稿重编译（已完成）+ 五包重建 + staged 复核 + 终检 → mirror push → **v2.1 release（generic notes）**。
>

"""

ROW = ("126. 🧪 **Round 2 收口（2026-10-21 03:10）** —— P3 5-seed：r5 −23.0±22.3（1/5 正）vs r6 +65.5±38.5（5/5 正），"
       "差值 +88.5，精确置换 **p=0.008**（最小可达）；入稿 S14、正文仍 10 页；消融 12/20/32/64 = +40.5/+115.0/+44.5/+30.0"
       "（3.8×，如实入 S15）；A1 双塔 LoRA 两域均选中 oracle（regret 0.0），A1 仍 63 页。下一步：五包重建+终检+mirror+v2.1。\n")

EVID_ROWS = """| `p3_seeds_combined.json` | P3 5-seed 合并 + 精确置换（p=0.008） | `tools/_p1448_p3_seeds_analysis.py` |
| `p3_rerun_seeds.json` | P3 新增 seed 原始记录（r5/r6 × 789/999/1024） | `tools/_p1416_p3_seeds.py` |
| `p3_numsamples_ablation.json` | P3 num-samples 消融（12/32/64） | `tools/_p1417_p3_numsamples.py` |
| `a1_monitor_bothtower.json` | A1 双塔 LoRA 逐 epoch 监控 | `tools/_p1411_a1_bothtower.py` |
| `a1_monitor_bothtower_analysis.json` | A1 双塔 regret 分析（两域均 0.0） | `tools/_p1452_a1_bothtower_analysis.py` |
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  (dry run)")
        return 0
    h = io.open(HANDOFF, encoding="utf-8").read()
    if "Round 2 完成：P3 五 seed 统计" not in h:
        i = h.find("# 项目交接文档")
        j = h.find("\n", i)
        io.open(HANDOFF, "w", encoding="utf-8", newline="").write(h[: j + 1] + "\n" + ENTRY + h[j + 1:])
        print("  handoff updated")
    m = io.open(MAP, encoding="utf-8").read()
    if "Round 2 收口（2026-10-21 03:10）" not in m:
        anchor = "125. 🧪 **五稿升级轮"
        idx = m.find(anchor)
        assert idx >= 0
        end = m.find("\n", idx)
        io.open(MAP, "w", encoding="utf-8", newline="").write(m[: end + 1] + ROW + m[end + 1:])
        print("  file map updated")
    e = io.open(EVID, encoding="utf-8").read()
    if "p3_seeds_combined.json" not in e:
        io.open(EVID, "w", encoding="utf-8", newline="").write(e.rstrip() + "\n" + EVID_ROWS)
        print("  evidence map updated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
