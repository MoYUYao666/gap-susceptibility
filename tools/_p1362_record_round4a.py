# -*- coding: utf-8 -*-
r"""Record round 4a: P3 supplementary rank control, commentary six-instance table.

    python tools/_p1362_record_round4a.py [--apply]
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HANDOFF = REPO / "HANDOFF.md"
MAP = REPO / "文件地图.md"
EVID = REPO / "docs" / "EVIDENCE_MAP_2026-10-19.md"
COMM = REPO / "docs" / "COMMENTARY_REVIEWER_OBJECTIONS.md"
P3MEMO = REPO / "docs" / "P3_UPGRADE_MEMO_2026-10-19.md"

ENT = """> **📚 2026-10-19 19:25 —— 两项暂缓全部落地：P3 补充材料本地秩控制 + Commentary 六实例表**
>
> | 项 | 结果 |
> |---|---|
> | **P3-P2-7 本地秩控制** | CLIP ViT-B/32、文本塔 LoRA、DTD 47 类（40 训练/15 留出）、rank 4–64、6 epoch × 2 seed：gap 全程 0.744–0.792（单次最大变化 0.031）、无发散/坍缩；池化 $r(\\text{rank},\\text{CG})=-0.43$、$r(\\text{rank},\\text{top-1})=-0.10$。作为**补充材料 S7** 写入 `supplementary/supplementary.tex`（6 页 0/0/0），并在主文结论加一句指向补充材料；**不**当作 LLaVA 证据 |
> | **Commentary 六实例表** | 紧凑 2 列表格（6 行）加入 §3 末，配合 4 处压缩与表格字号，**仍守 7 页**、builder 检查全过、0 overfull |
>
> 审计：P3 主文 10 页 0/0/0（结论新增一句指向 supplement），Commentary gate `全部通过`。
>

"""

COMM_ROW = """
## Update (2026-10-19 19:25): six-instance table restored

The compact two-column table (instance -> item that makes it comparable) is now in §3, and the page limit still holds at
seven pages; three sections were tightened (§2.3, §3.3, §4 intro) and the table is set in the builder's footnotesize
float. The earlier note that the table had to be removed is superseded.
"""

P3_ROW = """
## Round 4 (2026-10-19 19:25): local rank-sensitivity control added to the supplement

Deferred item P2-7 is now executed as a *supplementary* control, not as main-text evidence: CLIP ViT-B/32, text-tower
LoRA, ranks 4-64, DTD with a per-class held-out split, six epochs and two seeds. The centroid gap stays in [0.744, 0.792]
with no divergence or collapse, pooled r(rank, CG) = -0.43 and r(rank, top-1) = -0.10, i.e. the LLaVA critical-rank
phenomenon does not reproduce in this cheaper local setting - consistent with the main text's system/protocol-specific
reading. Archive `outputs/analysis/p3_rank_local_control.json`, script `tools/_p1358_p3_rank_control.py`, supplement
section `sec:supp-rank-control`.
"""

EVID_ROW = """
| P3 local rank control (CLIP, ranks 4-64: CG 0.744-0.792, r(rank,CG) -0.43) | `outputs/analysis/p3_rank_local_control.json` | `tools/_p1358_p3_rank_control.py` |
| A1 interior-optimum v2 (2 backbones, 3 seeds, 10 epochs, sequential rules) | `outputs/analysis/a1_monitor_interior_v2.json` | `tools/_p1357_monitor_interior_v2.py` |
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  (dry run)")
        return 0
    h = io.open(HANDOFF, encoding="utf-8").read()
    if "两项暂缓全部落地" not in h:
        i = h.find("# 项目交接文档")
        j = h.find("\n", i)
        io.open(HANDOFF, "w", encoding="utf-8", newline="").write(h[: j + 1] + "\n" + ENT + h[j + 1:])
        print("  handoff added")
    mp = io.open(MAP, encoding="utf-8").read()
    row = ("115. 📚 **暂缓项落地（2026-10-19 19:25）** —— P3 本地秩控制进补充材料 S7（6 页 0/0/0；rank 4–64 gap 0.744–0.792、"
           "无发散；主文结论加一句指向）；Commentary 六实例表以紧凑两列版回到 §3，仍守 7 页；审计 P3 10 页 0/0/0。\n")
    if "暂缓项落地（2026-10-19 19:25）" not in mp:
        anchor = "114. 📦 **镜像推送 + 修回包就绪"
        idx = mp.find(anchor)
        assert idx >= 0
        end = mp.find("\n", idx)
        io.open(MAP, "w", encoding="utf-8", newline="").write(mp[: end + 1] + row + mp[end + 1:])
        print("  map row added")
    ev = io.open(EVID, encoding="utf-8").read()
    if "P3 local rank control" not in ev:
        io.open(EVID, "w", encoding="utf-8", newline="").write(ev.rstrip() + EVID_ROW)
        print("  evidence map extended")
    cm = io.open(COMM, encoding="utf-8").read()
    if "six-instance table restored" not in cm:
        io.open(COMM, "w", encoding="utf-8", newline="").write(cm.rstrip() + COMM_ROW)
        print("  commentary objections updated")
    pm = io.open(P3MEMO, encoding="utf-8").read()
    if "local rank-sensitivity control added to the supplement" not in pm:
        io.open(P3MEMO, "w", encoding="utf-8", newline="").write(pm.rstrip() + P3_ROW)
        print("  p3 memo updated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
