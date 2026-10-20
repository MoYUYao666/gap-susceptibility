# -*- coding: utf-8 -*-
r"""Record the Tier A + Tier B upgrade round and rebuild the affected revision packages.

    python tools/_p1409_record_tier_ab.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import subprocess
import sys

HANDOFF = "HANDOFF.md"
MAP = "文件地图.md"
MIRROR = "tools/_p1284_prepare_public_mirror.py"
REPO = "."

ENT = """> **🧹 2026-10-20 12:15 —— Tier A+B 升级：3 个真实告警清零，修回件全部备好**
>
> | 项 | 结果 |
> |---|---|
> | **Paper A 死标签/未引用图表（C-05/C-07）** | 7 个图/表标签补正文引用（fig:budget、fig:ode、fig:sigma0_control、tab:beta_pilot、tab:corr、tab:grad_side、tab:llava），4 个定义/公式标签补引用（def:dgstar、def:gamma、eq:dynamics、eq:solution）→ **NC 与 Springer 两条告警清零** |
> | **A23 字体告警（B-09）** | 显式声明 `\\DeclareFontShape{OT1}{ptm}{m}{scit}` → 9 条警告清零，审计 **0 warn** |
> | **Commentary 数据声明（H-02）** | Data availability 加 v1.0 版本 DOI `10.5281/zenodo.23341223` → 告警清零，仍 7 页 0 overfull |
> | **修回预备（Tier B）** | 三份逐点回复骨架（P3/A1/Paper A，英文，含"不可声明清单"）+ 三封修回 cover letter（各 1 页 0 错误 0 overfull：P3 10+6 页、A1 61 页、Paper A 72 页）|
> | **A1 补充表** | 新表 `tab:monitor_regret`（大/小留出集 × 5 条规则的 regret），仍 61 页 0/0/0 |
>
> 审计终态：P3 / A23 / Commentary / PaperA-Springer **READY/A（A23 与 Commentary 均 0 warn）**；A1 与 PaperA-NC 仅剩预期 I-02。
> 修回包：A1、PaperA-NC、A23、Commentary 已重建。
>

"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  (dry run)")
        return 0
    h = io.open(HANDOFF, encoding="utf-8").read()
    if "Tier A+B 升级" not in h:
        i = h.find("# 项目交接文档")
        j = h.find("\n", i)
        io.open(HANDOFF, "w", encoding="utf-8", newline="").write(h[: j + 1] + "\n" + ENT + h[j + 1:])
        print("  handoff added")
    m = io.open(MAP, encoding="utf-8").read()
    row = ("124. 🧹 **Tier A+B 升级（2026-10-20 12:15）** —— Paper A C-05/C-07 清零（7 图/表 + 4 定义/公式补引用）、"
           "A23 B-09 清零（scit 声明）、Commentary H-02 清零（数据声明加 DOI）；三份逐点回复骨架 + 三封修回 cover letter"
           "（各 1 页 0/0）；A1 新增 regret 表；审计 4 READY/A（A23/Commentary 0 warn）、两篇仅预期 I-02；四个修回包已重建。\n")
    if "Tier A+B 升级（2026-10-20 12:15）" not in m:
        anchor = "123. 🔬 **A1 反转根因诊断"
        idx = m.find(anchor)
        assert idx >= 0
        end = m.find("\n", idx)
        io.open(MAP, "w", encoding="utf-8", newline="").write(m[: end + 1] + row + m[end + 1:])
        print("  map row added")
    t = io.open(MIRROR, encoding="utf-8").read()
    new = ["tools/_p1407_tier_a_fixes.py", "tools/_p1408_a1_table.py", "tools/_p1409_record_tier_ab.py"]
    missing = [x for x in new if x not in t]
    if missing:
        anchor = '    "tools/_p1406_record_diagnosis.py",'
        assert t.count(anchor) == 1
        t = t.replace(anchor, anchor + "\n" + "\n".join('    "%s",' % x for x in missing), 1)
        io.open(MIRROR, "w", encoding="utf-8", newline="").write(t)
        print("  mirror list extended")
    pkgs = [
        ["--manuscript", "paper_a1/main.pdf", "--title-page", "paper_a1/title_page.pdf", "--cover-letter",
         "paper_a1/cover_letter.pdf", "--source", "paper_a1", "--figures", "paper_a1/figures", "--venue",
         "Pattern Analysis and Applications (A1)", "--out", "SUBMISSION/_venue_builds/A1_PAA_next"],
        ["--manuscript", "paper_a2/main_ieee.pdf", "--abstract", "paper_a2/abstract.pdf", "--cover-letter",
         "paper_a2/cover_letter.pdf", "--highlights", "paper_a2/highlights.pdf", "--source", "paper_a2", "--figures",
         "paper_a2/figures", "--venue", "IEEE JOE (A23)", "--out", "SUBMISSION/_venue_builds/A23_JOE_next"],
        ["--manuscript", "paper_review_prl/main_prl.pdf", "--cover-letter", "paper_review_prl/cover_letter.pdf",
         "--highlights", "paper_review_prl/highlights.pdf", "--source", "paper_review_prl", "--figures",
         "paper_review_prl/figures", "--venue", "Pattern Recognition Letters (Commentary)", "--out",
         "SUBMISSION/_venue_builds/Commentary_PRL_next"],
        ["--manuscript", "paper合/main_nc.pdf", "--abstract", "paper合/abstract_nc.pdf", "--cover-letter",
         "paper合/cover_letter_nc.pdf", "--highlights", "paper合/highlights_nc.pdf", "--source", "paper合",
         "--figures", "paper合/figures", "--venue", "Neurocomputing (Paper A)", "--out",
         "SUBMISSION/_venue_builds/PaperA_Neurocomputing_next"],
    ]
    for p in pkgs:
        r = subprocess.run([sys.executable, "tools/_p1336_build_venue_package.py"] + p + ["--apply"],
                           capture_output=True, text=True)
        print("  package:", p[p.index("--out") + 1], "exit", r.returncode)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
