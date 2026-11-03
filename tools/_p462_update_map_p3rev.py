# -*- coding: utf-8 -*-
r"""更新 `文件地图.md`：加入 P3 修订包条目（2026-10-13）。

    python tools\_p462_update_map_p3rev.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ADD = """
### P3 修订包（PRL Revise，2026-10-13 建）

- **路径**：`SUBMISSION/P3_PRL_revision/` —— **修订阶段**的包（投稿版在 `SUBMISSION/P3_PRL/`）
- **内容**：
  - `reviews/` —— 编辑决定邮件 + 审稿意见 PDF + 提取文本（33 条）
  - `response/P3_REVIEW_RESPONSE.md` + `.txt` —— **33 条逐条应答**（工作文档，含建议动作与空回复块）
  - `evidence/` —— 三组补实验报告（E / F+G / I）+ 意见解析与分类 JSON
  - `manuscript/main_REVISING.pdf` —— 当前稿件（**14 页，修订中，非投稿版**）
- **截止**：**2026-11-02**（逾期视为撤稿）；**必须在 Editorial Manager 逐条 reply to reviews**
- **备份脚本**：`tools/_p461_backup_prl_response.py`（幂等，可重跑）
- ⚠️ **备份 ≠ 定稿**：修订提交前须重新生成
- **待办**：P1 随机池未跑满（"未胜随机"仍 provisional）｜页数 14 需压缩｜33 条正式回复文本未撰写
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    fm = REPO / "文件地图.md"
    t = io.open(fm, encoding="utf-8").read()
    if "P3_PRL_revision" in t:
        print("  文件地图已有该条目")
        return 0
    if not a.apply:
        print("  （预演）")
        return 0
    io.open(fm, "w", encoding="utf-8", newline="").write(t.rstrip() + "\n" + ADD)
    t2 = io.open(fm, encoding="utf-8").read()
    for k in ("P3_PRL_revision", "main_REVISING.pdf", "_p461_backup_prl_response"):
        print(f"  {'✅' if k in t2 else '🔴'} {k}")
    print(f"  文件地图行数 = {len(t2.splitlines())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
