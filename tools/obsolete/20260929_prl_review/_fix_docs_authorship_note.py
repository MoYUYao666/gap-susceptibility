# -*- coding: utf-8 -*-
r"""更正两份交接文档里 Authorship Confirmation 表的归属记录。

背景（2026-09-29，以 git 提交信息为准）：
  09-26        P3（PRLETTERS-D-26-02378）投稿
  09-28 21:54  生成表，日期 September 26，提交信息写明 **for P3**（`3a1f6e4`）
  09-28 晚     综述（PRLETTERS-D-26-02402）投稿，**当时已带表**
  09-29        编辑部回信要求 **P3** 补表；早间曾误把该表判给综述（`970d462`），现改回

    python tools/_fix_docs_authorship_note.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

HANDOFF_BLOCK = """> **🔴 待办 —— P3（`...-02378`）补表（2026-09-29 编辑部回信要求）**：
> P3 于 **2026-09-26** 投稿；**2026-09-29 编辑部回信要求补 Authorship Confirmation**
> （PRL 技术检查常规流程；A1 当年同样在投稿后 2–4 天被要求补，见本文档 2026-08 条目）。
> **表已就绪**：`paper3/paper_ieee/PRL_submission/Authorship Confirmation (P3, 2026-09-26).pdf`
> （日期 = P3 投稿日 09-26；签名 `Hongrui Wan`；两处 `None`）。上传到 **`-02378`** 稿号下，
> item type 选 **Cover Letter**。
>
> **⚠️ 一次归属误记及其更正（2026-09-29，留档避免重犯）**：09-28 21:54 生成该表时，提交信息写明是
> **"for P3"**（`3a1f6e4`）；但因文件同时放在 `paper_review_prl/`（综述目录）下，2026-09-29 早间一度被
> 判为"综述的表"并据此改了记录（`970d462`）。**操作者指出实情后已改回**：该表属 **P3**。
> 现文件名统一为 `Authorship Confirmation (P3, 2026-09-26).pdf`，归属依据见
> `paper_review_prl/AUTHORSHIP_FORM_ATTRIBUTION.md`（以 git 提交信息+时间戳为准，不按目录推断）。
>
> **📌 综述（`...-02402`）投稿时（09-28 晚）已带上 Authorship Confirmation**（操作者确认）。
> **遗留待核（不影响 P3）**：综述用的那一份表日期是否为 09-28。若用的是 09-26 那份（目录里长期只有那一份），
> 建议按 09-28 重生成替换（改 `tools/_make_prl_authorship_form.py` 的 `NEW_DATE`，底稿与做法不变）。
> 判定方法：取 `-02402` 的投稿确认稿，看该页 `Date` 字段。
>"""

MAP_BLOCK = """> **🔴 P3（`...-02378`）补表（2026-09-29 编辑部回信要求）**：P3 于 09-26 投稿，09-29 被要求补
> Authorship Confirmation。**表已就绪**（日期 = P3 投稿日 09-26）：
> `paper3/paper_ieee/PRL_submission/Authorship Confirmation (P3, 2026-09-26).pdf`
> → 上传到 **`-02378`** 稿号，item type 选 **Cover Letter**。
> ⚠️ 该表曾在 09-29 早间被误记为"综述的表"（因文件放在 `paper_review_prl/` 下）；**已改回**，
> 依据见 `paper_review_prl/AUTHORSHIP_FORM_ATTRIBUTION.md`（以 git 提交信息为准，不按目录推断）。
> **综述（`...-02402`）投稿时（09-28 晚）已带表**（操作者确认）；**遗留待核**：那份表日期是否为 09-28，
> 取 `-02402` 确认稿看 `Date` 字段即可判定。"""


def patch(path: Path, start_marker: str, end_marker: str | None, block: str) -> bool:
    lines = io.open(path, encoding="utf-8").read().splitlines()
    s = next((i for i, l in enumerate(lines) if start_marker in l), None)
    if s is None:
        print(f"  ⚠ {path.name}: 未找到起点标记 {start_marker!r}")
        return False
    if end_marker:
        e = next((i for i in range(s + 1, len(lines)) if end_marker in lines[i]), None)
        if e is None:
            print(f"  ⚠ {path.name}: 未找到终点标记 {end_marker!r}")
            return False
    else:
        e = s + 1
        while e < len(lines) and lines[e].strip().startswith(">"):
            e += 1
    lines[s:e] = block.splitlines()
    io.open(path, "w", encoding="utf-8", newline="").write("\n".join(lines) + "\n")
    print(f"  ✅ {path.name}: 已替换第 {s+1}–{e} 行")
    return True


def main() -> int:
    apply = "--apply" in sys.argv
    if not apply:
        print("（预演；加 --apply 生效）")
        print(f"  HANDOFF.md   → 替换含 '待办 —— 综述' 的段落到 'P3 投稿包核实' 之前")
        print(f"  文件地图.md  → 替换含 '归属待确认' 的引用块")
        return 0
    patch(REPO / "HANDOFF.md", "待办 —— 综述", "P3 投稿包核实", HANDOFF_BLOCK)
    patch(REPO / "文件地图.md", "归属待确认", None, MAP_BLOCK)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
