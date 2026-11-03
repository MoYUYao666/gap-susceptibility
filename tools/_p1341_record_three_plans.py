# -*- coding: utf-8 -*-
r"""Record the P3 / A23 / Commentary upgrade plans.

    python tools/_p1341_record_three_plans.py [--apply]
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HANDOFF = REPO / "HANDOFF.md"
MAP = REPO / "文件地图.md"

ENT = """> **🗺️ 2026-10-19 15:10 —— 三稿升级包方案：P3 / A23 / Commentary（本地算力，规则同 A1+Paper A）**
>
> 新增 `docs/UPGRADE_PLAN_P3_A23_COMMENTARY_2026-10-19.md`：三张表，共 **23 项**（P3 8 / A23 8 / Commentary 7），
> 全部本地执行、峰值内存 ≤8 GB、预计总耗时 **~12 h**、GPU ≤75 min：
>
> | 稿 | 核心升级（P0）| 关键资源 |
> |---|---|---|
> | **P3**（PRL 在审，11-02）| 配对 bootstrap 补"分配 vs uniform 不可区分"的区间；**族内重拟合临界 rank**；AdaLoRA 对照表；修订版重编译+回复骨架 | 181 个本地实验 JSON，纯分析 |
> | **A23**（JOE 在审，64–66 页）| **接入 margin 质量证书**（用已有 `ocean_margins*`/`sonar_*`）；跨域阈值迁移；对称手术+逐域 CI；意见包 | 30+ 个本地归档，纯分析为主 |
> | **Commentary**（PRL 在审，7 页）| 与 Sharma 2026 / Role-Ambard 期刊版**划界**；12 条报告项逐条挂自有实证数字；POPE/MMBench 说法复核 | 无实验，写作+核对 |
>
> 三稿审计均 **0 FAIL**（只余 P2：死标签、未用 bib、PDF 无 title、A23 字体警告），已作为 P1/P2 清账项列入。
> 冻结包与 `_frozen_submitted/` 不动；每项完成即更新 HANDOFF、文件地图与各稿 FIXES/RELEASE_NOTES。
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
    if "三稿升级包方案：P3 / A23 / Commentary" not in h:
        i = h.find("# 项目交接文档")
        j = h.find("\n", i)
        io.open(HANDOFF, "w", encoding="utf-8", newline="").write(h[: j + 1] + "\n" + ENT + h[j + 1:])
        print("  handoff entry added")
    m = io.open(MAP, encoding="utf-8").read()
    row = ("107. 🗺️ **P3/A23/Commentary 升级包方案（2026-10-19 15:10）** —— `docs/UPGRADE_PLAN_P3_A23_COMMENTARY_2026-10-19.md`："
           "23 项（8/8/7），本地、峰值 ≤8 GB、总 ~12 h、GPU ≤75 min；P3 补配对区间/族内 r_c/AdaLoRA 表，A23 接入 margin 证书+阈值迁移，"
           "Commentary 划界+12 条报告项挂实证；三稿审计 0 FAIL。\n")
    if "P3/A23/Commentary 升级包方案（2026-10-19 15:10）" not in m:
        anchor = "106. 📮 **投稿后续跟踪"
        idx = m.find(anchor)
        assert idx >= 0
        end = m.find("\n", idx)
        io.open(MAP, "w", encoding="utf-8", newline="").write(m[: end + 1] + row + m[end + 1:])
        print("  map row added")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
