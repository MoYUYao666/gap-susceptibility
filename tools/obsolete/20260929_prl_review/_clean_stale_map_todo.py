# -*- coding: utf-8 -*-
r"""清理 `文件地图.md` 中今早那次错误更正留下的待办 3a 项（内容自相矛盾）。

第 241 行左右仍写着"那张表实为 P3 的表（P3 于 09-28 16:22 投稿…）"——
其中 **09-28 16:22 是错的**（P3 是 **09-26** 投稿；09-28 16:22 是当时对 P3 的错误记忆）。
该项整体被替换为正确的待办：P3 补表 + 综述表日期待核。

    python tools/_clean_stale_map_todo.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MAP = REPO / "文件地图.md"

BLOCK = """3a. 🔴 **P3（`PRLETTERS-D-26-02378`）补表**：P3 于 **2026-09-26** 投稿，**2026-09-29 编辑部回信要求补
    Authorship Confirmation**。**表已就绪**（日期 = P3 投稿日 09-26）：
    `paper3/paper_ieee/PRL_submission/Authorship Confirmation (P3, 2026-09-26).pdf`
    → 上传到 **`-02378`** 稿号，item type 选 **Cover Letter**。
    ⚠️ 该表曾在 09-29 早间被误记为"综述的表"（因文件放在 `paper_review_prl/` 下），**已改回**；
    归属依据见 `paper_review_prl/AUTHORSHIP_FORM_ATTRIBUTION.md`（以 git 提交信息为准，不按目录推断）。
3b. ⏳ **综述（`PRLETTERS-D-26-02402`）表日期待核（不影响 P3）**：综述 09-28 晚投稿时**已带表**（操作者确认）。
    若那份表用的是 09-26 版（目录里长期只有那一份），建议按 **09-28** 重生成替换
    （改 `tools/_make_prl_authorship_form.py` 的 `NEW_DATE`，底稿与做法不变）。
    判定方法：取 `-02402` 投稿确认稿，看 Authorship Confirmation 页的 `Date` 字段。"""


def main() -> int:
    apply = "--apply" in sys.argv
    lines = io.open(MAP, encoding="utf-8").read().splitlines()
    s = next((i for i, l in enumerate(lines) if l.startswith("3a.")), None)
    if s is None:
        print("  ⚠ 未找到 3a. 起始行")
        return 1
    e = s + 1
    while e < len(lines) and not lines[e].startswith("4."):
        e += 1
    print(f"  将替换第 {s+1}–{e} 行（{e-s} 行）为新待办 3a/3b")
    if apply:
        lines[s:e] = BLOCK.splitlines()
        io.open(MAP, "w", encoding="utf-8", newline="").write("\n".join(lines) + "\n")
        t = io.open(MAP, encoding="utf-8").read()
        print("  ✅ 已写入")
        print("  残留「尚未生成」:", "❌ 仍有" if "尚未生成" in t else "✅ 无")
        print("  残留错误的「09-28 16:22」:", "❌ 仍有" if "09-28 16:22" in t else "✅ 无")
    else:
        print("  （预演，加 --apply 生效）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
