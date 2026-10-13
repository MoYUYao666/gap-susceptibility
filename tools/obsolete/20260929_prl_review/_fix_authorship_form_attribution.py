# -*- coding: utf-8 -*-
r"""修正"两张 Authorship Confirmation 表"的归属错误。

## 错误经过（2026-09-28/29 记录更正）

- 2026-09-28 **16:22**：P3（`PRLETTERS-D-26-02378`）投稿。
- 2026-09-28 **21:54**：为 **P3** 生成 Authorship Confirmation 表，日期填 **September 26, 2026**（= P3 投稿日）。
- 但该文件被放在 `paper_review_prl/`（**综述**目录）下，命名为 `Authorship Confirmation submit.pdf`，
  并被当成"综述的表"记入 `HANDOFF.md` / `文件地图.md` / `SUBMISSION_README.md`——**归属错误**。
- 2026-09-28 **22:30** 综述才定稿（`main_prl.pdf` 最后修改），**不可能在 21:54 就有它的表**。

## 本脚本做什么

把该表**明确标注为 P3 专属**（原地留一份，另存一份到 P3 目录），并输出一份归属说明，
避免日后又把它当综述的表用。**不删除任何文件**（操作者可能已用它投过稿）。

    python tools/_fix_authorship_form_attribution.py [--apply]
"""
from __future__ import annotations

import io
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "paper_review_prl" / "Authorship Confirmation submit.pdf"
P3_DST = REPO / "paper3" / "paper_ieee" / "PRL_submission" / "Authorship Confirmation (P3, 2026-09-26).pdf"
NOTE = REPO / "paper_review_prl" / "AUTHORSHIP_FORM_ATTRIBUTION.md"

TEXT = """# Authorship Confirmation 表 —— 归属说明（重要）

> 建立：2026-09-29 ｜ 起因：曾把两张表搞混

## 已确认归属

| 文件 | 归属稿号 | 表内日期 | 依据 |
|---|---|---|---|
| `paper_review_prl/Authorship Confirmation submit.pdf` | **P3 `PRLETTERS-D-26-02378`** | **September 26, 2026** | 生成于 2026-09-28 21:54，而 P3 投稿时间为同日 16:22；综述到 22:30 才定稿，不可能在 21:54 有表 |
| `paper_review_prl/UPLOAD/Authorship Confirmation.pdf` | 同上（同一文件的副本） | 同上 | 文件哈希一致 |
| `paper3/paper_ieee/PRL_submission/Authorship Confirmation (P3, 2026-09-26).pdf` | 同上（另存副本） | 同上 | 本目录下便于查找 |
| `paper_a1/_archive_prl/Authorship Confirmation submit.pdf` | A1 `PRLETTERS-D-26-01941` | August 16, 2026 | A1 投稿日 |

**核实**：P3 投稿确认稿（`C:\\Users\\hongr\\Desktop\\PRLETTERS-D-26-02378.pdf`）第 4 页
显示 `Signature Hongrui Wan` / `Date September 26, 2026` → **P3 的表已交且日期正确** ✅

## 综述（`PRLETTERS-D-26-02402`）的表 —— ⏳ 待操作者确认

综述于 **2026-09-28** 投稿（晚于 22:30 定稿）。可能性有二：

- **A.** 若上传的是上述日期 **September 26** 的表 → **表日期与投稿日差 2 天**，
  应重新生成日期为 **September 28** 的表替换（做法见 `tools/_make_prl_authorship_form.py`，改 `NEW_DATE` 即可）。
- **B.** 若上传的是 EM 内另行生成/其他来源的表 → 需核对日期是否正确。

**判定方法**：取 `...-02402` 的投稿确认稿（同 P3 那种 22 页 PDF），
看其 Authorship Confirmation 页的 `Date` 字段。

**⚠️ 绝不可把两张表互换稿号上传**——两稿表日期不同，编辑部对得上。
"""


def main() -> int:
    apply = "--apply" in sys.argv
    if not SRC.exists():
        raise SystemExit(f"❌ 源文件不存在：{SRC}")
    print(f"源文件: {SRC.relative_to(REPO)}（{SRC.stat().st_size} B）")
    print(f"目标:   {P3_DST.relative_to(REPO)}")
    print(f"说明:   {NOTE.relative_to(REPO)}")
    if apply:
        P3_DST.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(SRC, P3_DST)
        NOTE.write_text(TEXT, encoding="utf-8")
        print("\n✅ 已另存 P3 专属副本 + 写出归属说明（未删除任何文件）")
    else:
        print("\n（预演，加 --apply 生效）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
