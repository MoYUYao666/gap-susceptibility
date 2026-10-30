# -*- coding: utf-8 -*-
r"""Record the weekly literature check of 2026-10-19 in HANDOFF and the file map.

    python tools/_p1325_record_weekly_lit.py [--apply]
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HANDOFF = REPO / "HANDOFF.md"
MAP = REPO / "文件地图.md"

ENT = """> **📚 2026-10-19 12:00 —— 每周文献检索（6 篇稿件）：A1 出现最接近的竞争工作，P3 的 rank 分配卖点被逼近**
>
> 17 条检索式 + arXiv API/Crossref 逐条核对；**已投稿件一律不动**，只记下轮修回动作。报告：
> `docs/reviews/WEEKLY_LIT_2026-10-19.md`。
>
> | 稿件 | 最重要发现 | 动作 |
> |---|---|---|
> | **A1** | **Sharma & Saxena 2026**（[arXiv:2609.36101](https://arxiv.org/abs/2609.36101)）"One Geometry, Different Outcomes"：秩一主方向 + readout 三角色解释 gap 修改的任务依赖性，与 A1"任务敏感谱"**高度重叠**；但无充分性定理/下界/证书。`"order preservation" AND "zero-shot"` 全库仅 1 条无关命中 → 保序叙事仍首创 | **修回必引 + 区分段**（几何解释 vs 统计充分性 + margin 证书）|
> | **Paper A** | Sharma、Yaras **已在 bib** ✅；Amblard 的 "Fill the Gap" 已有**期刊正式版**（IJMI，DOI `10.1007/s13735-026-00423-w`）| 修回把预印本条升级为期刊版；可选加 CLIP-CIL 两条背景 |
> | **P3** | rank allocation 新增多篇：**StatLoRA**（[2607.20205](https://arxiv.org/abs/2607.20205) 假设检验 + 优化器 CLT）、**IFCLoRA**（[2607.22251](https://arxiv.org/abs/2607.22251) 训练前零搜索分配）、LoRA-GA²（[2608.19800](https://arxiv.org/abs/2608.19800)）| **修回必引并区分**（P3：解析式 + 临界 rank，无搜索/校准）；deadline 2026-11-02 最紧急 |
> | **A23** | 未发现"声呐图像–文本对比对齐"竞争工作 | 仅记录 |
> | P1 / ap3 | 无新发现 | 无需动作 |
>
> 四句总评：竞争最激烈的是 **A1**；P3 的"训练前零搜索"被逼近；最紧急 **P3（11-02）**；A1 修回加 Sharma/Yaras，
> Paper A 修回升 Amblard 期刊版，其余记录。
>

"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    h = io.open(HANDOFF, encoding="utf-8").read()
    need = "每周文献检索（6 篇稿件）：A1 出现最接近的竞争工作" not in h
    print(f"  handoff entry needed: {need}")
    if a.apply and need:
        i = h.find("# 项目交接文档")
        j = h.find("\n", i)
        io.open(HANDOFF, "w", encoding="utf-8", newline="").write(h[: j + 1] + "\n" + ENT + h[j + 1:])
        print("  handoff entry added")
    m = io.open(MAP, encoding="utf-8").read()
    row = ("100. 📚 **每周文献检索（2026-10-19 12:00）** —— 报告 `docs/reviews/WEEKLY_LIT_2026-10-19.md`：**A1** 遇最接近竞争 "
           "[Sharma & Saxena 2026, arXiv:2609.36101](https://arxiv.org/abs/2609.36101)（秩一 + readout 三角色；无定理/下界/证书）→ 修回必引+区分；"
           "**P3** rank 分配竞争 StatLoRA/IFCLoRA/LoRA-GA² → 修回必引（deadline 11-02）；**Paper A** Amblard 已有 IJMI 期刊版可升级；"
           "A23/P1 无新竞争。已投稿件本轮未动。\\n")
    if "每周文献检索（2026-10-19 12:00）" not in m:
        anchor = "99. 🌐 **公开镜像推送"
        idx = m.find(anchor)
        assert idx >= 0
        end = m.find("\n", idx)
        if a.apply:
            io.open(MAP, "w", encoding="utf-8", newline="").write(m[: end + 1] + row + m[end + 1:])
            print("  map row added")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
