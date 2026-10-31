# -*- coding: utf-8 -*-
r"""Record the SUBMISSION reorganisation and the final all-READY audit state.

    python tools/_p1245_record_submission_reorg.py [--apply]
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HANDOFF = REPO / "HANDOFF.md"
MAP = REPO / "文件地图.md"
README = REPO / "SUBMISSION" / "README.md"

ENT = """> **🗂️ 2026-10-18 15:55 —— `SUBMISSION/` 整理完成：当前包在根、旧的进 `_archive/`，全部移动哈希校验，6 个审计全 READY/A**
>
> 操作者要求："全部整理进 SUBMISSION 文件夹里，旧的归档"。**未删除任何文件**。
>
> ### 一、新结构
>
> | 位置 | 内容 |
> |---|---|
> | `SUBMISSION/PaperA_Neurocomputing/` | **当前** Paper A 包（70 页 + 揭示函 3 页 + Highlights + 源码 45 文件 + `PORTAL_TEXT.md`）；原 `paper合/NC_submission/` |
> | `SUBMISSION/A1_PatternAnalysisApplications/` | **当前** A1 包（45 页 + 1 页 title page + 揭示函 + 源码 14 文件）；原 `paper_a1/PAA_submission/` |
> | `SUBMISSION/P3_PRL_revision/`、`A23_JOE/`、`Review_PRL/` | **在审冻结包，原位未动**（P3 的 `CORRECTED/UPLOAD_2026-10-15` 等冻结件保持原路径，freeze 校验通过）|
> | `SUBMISSION/_archive/` | `A1_NeuralNetworks_rejected_2026-10-18/`（16 文件，NN 桌面拒）、`PaperA_Neurocomputing_2026-10-12_60pp/`（55 文件，被 70 页版取代）、`_superseded_P3_PRL_revision/`、`_superseded_P3_PRL_submitted_2026-09-26/`、`_old/`（77 文件）、`scripts/`、`duplicates/PaperA_Neurocomputing_2026-10-18/`（3 个与门户名重复的副本）|
> | `SUBMISSION/_archive/MOVED_2026-10-18.tsv` | 9 条 old→new 映射 |
> | `SUBMISSION/README.md` | 重写为索引（当前包 / 归档 / 冻结纪律）|
>
> ### 二、移动安全
>
> 9 项移动**逐树 SHA-256 前后比对，全部 OK**；`_archive` 现 180 文件 / 18.2 MB。
> 同时清理 Paper A 包里的同名重复（`cover_letter_nc.pdf` 等 3 个），并让构建脚本 `_p1169` 只写门户名。
>
> ### 三、工具与 profile 同步
>
> `_p1169`（Paper A 包输出）、`_p1236`（A1 包输出）、`paperA_nc`/`a1_paa`/`a1_nn` 的 package 与 freeze 路径全部改为新位置；
> `a1_nn` 标记为**历史 profile**（NN 投稿已于 2026-10-18 桌面拒，当前目标 PAA 用 `a1_paa`）；
> 重建 `a1_nn`、`a1_paa` freeze 基线（16 文件，内容哈希未变，仅路径变）。
>
> ### 四、终检（6 个 profile 全部 READY / grade A）
>
> | profile | 结果 |
> |---|---|
> | `paperA_nc` | **READY A** pass=65 fail=0 warn=2 |
> | `a1_paa` | **READY A** pass=61 fail=0 warn=0 |
> | `a1_nn`（历史）| **READY A** pass=55 fail=0 warn=0 |
> | `p3_prl` | **READY A** pass=47 fail=0 warn=3 |
> | `a23_joe` | **READY A** pass=55 fail=0 warn=3 |
> | `prl_commentary` | **READY A** pass=53 fail=0 warn=3 |
>

"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  (dry run)")
        return 0
    # README: add the duplicates row to the archive table
    r = io.open(README, encoding="utf-8").read()
    if "duplicates/" not in r:
        anchor = "| `scripts/` | 原先散落在 `SUBMISSION/` 根的两个辅助脚本 | 2026-10-18 |"
        assert anchor in r
        r = r.replace(anchor, anchor + "\n| `duplicates/PaperA_Neurocomputing_2026-10-18/` | Paper A 包中与门户名重复的 3 个副本（同一内容两个文件名） | 2026-10-18 |", 1)
        io.open(README, "w", encoding="utf-8", newline="").write(r)
        print("  README archive table updated")
    h = io.open(HANDOFF, encoding="utf-8").read()
    if "SUBMISSION/` 整理完成" not in h:
        i = h.find("# 项目交接文档")
        j = h.find("\n", i)
        io.open(HANDOFF, "w", encoding="utf-8", newline="").write(h[: j + 1] + "\n" + ENT + h[j + 1:])
        print("  handoff added")
    m = io.open(MAP, encoding="utf-8").read()
    row = ("78. 🗂️ **`SUBMISSION/` 整理完成（2026-10-18 15:55）** —— 当前包入根（Paper A 70 页、A1 PAA 45 页+title page），"
           "旧的/已拒的入 `_archive/`（A1_NN 拒稿包、PaperA 旧 60 页、3 个 superseded、_old、scripts、duplicates）；"
           "9 项移动逐树 SHA-256 校验 OK；工具与 profile 路径同步、freeze 基线重建；**6 个 profile 全 READY/A**。\n")
    if "`SUBMISSION/` 整理完成" not in m:
        anchor = "77. ✅ **A1 PAA 投稿包建成"
        idx = m.find(anchor)
        if idx >= 0:
            end = m.find("\n", idx)
            io.open(MAP, "w", encoding="utf-8", newline="").write(m[: end + 1] + row + m[end + 1:])
            print("  map row added")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
