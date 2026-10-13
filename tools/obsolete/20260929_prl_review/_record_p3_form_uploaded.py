# -*- coding: utf-8 -*-
r"""记录 P3 的 Authorship Confirmation 已由操作者上传（2026-09-29）。

状态来源：**操作者报告**（未提供上传后的确认稿文件，故文档中如实标注，不写成"已核"）。

    python tools/_record_p3_form_uploaded.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

HANDOFF = """> **✅ 待办 ① 已办——P3（`...-02378`）补表已由操作者上传完成（2026-09-29）**
> 上传文件：`paper3/paper_ieee/PRL_submission/Authorship Confirmation (P3, 2026-09-26).pdf`
> （单页；日期 `September 26, 2026` = P3 投稿日；签名 `Hongrui Wan`；两处 `None`）。
> **状态来源：操作者报告**（本次未提供上传后的确认稿，故不记作"已核实"）。
> 此前 P3 的投稿确认稿（`C:\\Users\\hongr\\Desktop\\PRLETTERS-D-26-02378.pdf`，22 页）曾核实其中
> 第 4 页含 09-26 版表；本次补交的是同一份文件。
>
> **🔴 待办 ②——综述（`...-02402`）表日期更正**：综述 09-28 晚投稿，**但投稿时用的表日期写的是 09-26**（差 2 天）。
> **正确版本已备好**：`paper_review_prl/Authorship Confirmation (review, 2026-09-28).pdf`
> （`September 28, 2026`；单页、姓名×2、`None`×2 均已校验）。
> **建议**：等编辑部来信时顺带交（P3 是投稿后 3 天收到补件要求的）；若 EM 仍可 Attach Files 也可主动交，
> 附一句"更正日期笔误"。**不要为此撤稿重投。**
> ⚠️ 若 EM 显示的投稿日为 09-29，改按 09-29 生成（`tools/_make_prl_authorship_form.py --date`）。
>
> **⚠️ 归属误记的完整留档（2026-09-29 两次反复，避免重犯）**：09-28 21:54 生成 P3 表时提交信息写明
> **"for P3"**（`3a1f6e4`）；但因该文件同时放在 `paper_review_prl/`（综述目录）下，09-29 早间一度被误判为
> "综述的表"并据此改了记录（`970d462`），其中还写错了 P3 的投稿时间。**操作者指出后已全部改回**：
> 表属 P3；文件名统一带**稿号+日期**；归属以 **git 提交信息+时间戳** 判定，**不按所在目录推断**。
> 依据见 `paper_review_prl/AUTHORSHIP_FORM_ATTRIBUTION.md`。"""

MAP = """> **✅ P3（`...-02378`）补表已交（2026-09-29，操作者报告）**：上传
> `paper3/paper_ieee/PRL_submission/Authorship Confirmation (P3, 2026-09-26).pdf`（单页，日期 09-26 = P3 投稿日）。
> **🔴 综述（`...-02402`）表日期更正待办**：综述 09-28 晚投稿，但用的表日期写的是 09-26（差 2 天）。
> 正确版已备好：`paper_review_prl/Authorship Confirmation (review, 2026-09-28).pdf`。
> 建议等编辑来信时顺带交，或 EM 仍可 Attach Files 时主动交；**不要撤稿重投**。
> ⚠️ 两表文件名均带稿号+日期；归属以 git 提交信息为准（见 `paper_review_prl/AUTHORSHIP_FORM_ATTRIBUTION.md`）。"""


def replace_block(path: Path, start_marker: str, end_marker: str | None, block: str) -> None:
    lines = io.open(path, encoding="utf-8").read().splitlines()
    s = next((i for i, l in enumerate(lines) if start_marker in l), None)
    if s is None:
        print(f"  ⚠ {path.name}: 未找到 {start_marker!r}")
        return
    if end_marker:
        e = next((i for i in range(s + 1, len(lines)) if end_marker in lines[i]), None)
        if e is None:
            print(f"  ⚠ {path.name}: 未找到终点 {end_marker!r}")
            return
    else:
        e = s + 1
        while e < len(lines) and lines[e].strip().startswith(">"):
            e += 1
    lines[s:e] = block.splitlines()
    io.open(path, "w", encoding="utf-8", newline="").write("\n".join(lines) + "\n")
    print(f"  ✅ {path.name}: 第 {s+1}–{e} 行已更新")


def main() -> int:
    apply = "--apply" in sys.argv
    if not apply:
        print("（预演，加 --apply 生效）")
        return 0
    replace_block(REPO / "HANDOFF.md", "待办 ①", "P3 投稿包核实", HANDOFF)
    replace_block(REPO / "文件地图.md", "P3（", None, MAP)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
