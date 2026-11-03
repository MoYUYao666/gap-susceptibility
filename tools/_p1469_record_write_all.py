# -*- coding: utf-8 -*-
r"""Record the 'write everything into the papers' round.

    python tools/_p1469_record_write_all.py --apply
"""
from __future__ import annotations

import argparse
import io
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HANDOFF = os.path.join(REPO, "HANDOFF.md")
MAP = os.path.join(REPO, "文件地图.md")
EVID = os.path.join(REPO, "docs", "EVIDENCE_MAP_2026-10-19.md")

ENTRY = """> **📝 2026-10-21 07:50 —— 全部复核并"写进论文"：新增 4 个附录/引用，六稿终检全绿**
>
> | 稿 | 本轮写入的内容 | 页数 |
> |---|---|---|
> | **A1** | 新附录 **Monitoring rule variants**（三类任务 × 四条规则的 regret 表，`tab:monitor_variants`，`app:monitor_variants`）+ 正文指针 | 63→**64** |
> | **A23** | 新附录 **Protocol-sensitivity probes**：water-tank96 重预处理探测（top-1 8.9–18.5/4.3–17.5、r(τ) −0.75/−0.76）+ evaluation-size sweep（32/64/128/256/全量，`tab:watertank96`、`tab:neval`、`app:probes`）+ 正文边界句 | 68→**69** |
> | **Paper A** | 新附录 **ODE fit diagnostics**（按 family/site 的 R² 结构表 `tab:odefit`，`app:odefit`）+ 正文指针 | NC **74** / Springer **53** |
> | **P3** | 5-seed 统计与消融已在正文/补充 S14/S15；本轮复核无新增 | 正文 **10** + 补充 **6** |
> | **Commentary** | 新增 2026 证据引用（Sun et al., arXiv:2603.09095，评测伪影）并压缩两处文字保持 **7 页** | **7** |
>
> 复核：C-07 两个新附录死标签修复（正文补 `\ref{app:...}`）；Commentary 引用库同步（`refs_all.json`）；
> A23 verify 69 页；六稿审计 = Springer/A23/P3/Commentary **READY 0 warn**，A1/PaperA-NC 仅预期 I-02+I-06；
> provenance gate **PASS**（A1 34、A23 33、PaperA 31、P3 6 floats）；五包重建 + staged **1:1**（64/69/7/10/74）；
> 顺手修复 staged 检查器"选错 main.tex"的问题（按 shipped 页数选择候选）。
>

"""

ROW = ("128. 📝 **全部复核并写进论文（2026-10-21 07:50）** —— A1 新增 Monitoring-rule-variants 附录（64 页）；"
       "A23 新增 Protocol-sensitivity-probes 附录（watertank96 OOD + n_eval，69 页）；Paper A 新增 ODE-fit-diagnostics "
       "附录（74/53 页）；Commentary 补 2026 评测伪影引用（仍 7 页）；C-07 清零；provenance gate PASS（A1 34/A23 33/"
       "PaperA 31/P3 6）；五包 staged 1:1（64/69/7/10/74）。\n")

EVID_ROWS = """| `tab:monitor_variants` | A1 附录：三类任务 × 四条选择规则 regret | `tools/_p1463_a1_monitoring_appendix.py` |
| `tab:watertank96` / `tab:neval` | A23 附录：water-tank96 OOD 探测 + 评测集大小 sweep | `tools/_p1461_a23_probes_appendix.py` |
| `tab:odefit` | Paper A 附录：按 family/site 的 ODE 拟合质量 | `tools/_p1462_paperA_ode_appendix.py` |
| Commentary ref `sun2026reading` | Commentary §3.2 评测伪影引用（arXiv:2603.09095）| `tools/_p1464_commentary_freshness.py` |
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  (dry run)")
        return 0
    h = io.open(HANDOFF, encoding="utf-8").read()
    if "全部复核并“写进论文”" not in h:
        i = h.find("# 项目交接文档")
        j = h.find("\n", i)
        io.open(HANDOFF, "w", encoding="utf-8", newline="").write(h[: j + 1] + "\n" + ENTRY + h[j + 1:])
        print("  handoff updated")
    m = io.open(MAP, encoding="utf-8").read()
    if "全部复核并写进论文（2026-10-21 07:50）" not in m:
        anchor = "127. 📦 **GitHub v2.1 release"
        idx = m.find(anchor)
        assert idx >= 0
        end = m.find("\n", idx)
        io.open(MAP, "w", encoding="utf-8", newline="").write(m[: end + 1] + ROW + m[end + 1:])
        print("  file map updated")
    e = io.open(EVID, encoding="utf-8").read()
    if "tab:monitor_variants" not in e:
        io.open(EVID, "w", encoding="utf-8", newline="").write(e.rstrip() + "\n" + EVID_ROWS)
        print("  evidence map updated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
