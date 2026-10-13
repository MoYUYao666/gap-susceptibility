# -*- coding: utf-8 -*-
r"""改回 Authorship Confirmation 表的正确归属（撤销 2026-09-29 的错误"更正"）。

## 时间线（以 git 提交信息为准，非推测）

| 时间 | 事件 | 证据 |
|---|---|---|
| 2026-09-26 | **P3**（`PRLETTERS-D-26-02378`）投稿 | 操作者确认；确认稿写 September 26 |
| 2026-09-28 21:54 | 生成表，日期 `September 26, 2026`，**为 P3** | 提交 `3a1f6e4` 信息：*"prepare the authorship confirmation form for **P3**, dated for its submission"* |
| 2026-09-28 晚 | **综述**（`PRLETTERS-D-26-02402`）投稿，**当时已带上 Authorship Confirmation** | 操作者 2026-09-29 确认 |
| 2026-09-29 | **P3 收到编辑部回信，要求补 Authorship Confirmation** | 操作者 2026-09-29 确认；P3 清单里原本无此表 |

**结论**：09-28 生成的那张表**属 P3**（日期 = P3 投稿日 09-26）。2026-09-29 的提交 `970d462`
把它判给"研究论文"、并称"那张表属于 P3"——**判断方向正确但把它当成错误来改，实际是把对的改错了**；
本次撤销该更正的错误部分，恢复"该表为 P3 的表"。

    python tools/_restore_authorship_attribution.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
NOTE = REPO / "paper_review_prl" / "AUTHORSHIP_FORM_ATTRIBUTION.md"

TEXT = """# Authorship Confirmation 表 —— 归属说明

> 建立 2026-09-29（同日两次更正后定稿）｜ 依据：git 提交信息 + 操作者确认，**不含推测**

## 时间线（可核）

| 时间 | 事件 | 证据 |
|---|---|---|
| 2026-09-26 | **P3**（`PRLETTERS-D-26-02378`）投稿 | 操作者确认 |
| 2026-09-28 21:54 | 生成表，日期 `September 26, 2026`，**为 P3** | 提交 `3a1f6e4` 信息写明 *"prepare the authorship confirmation form for **P3**, dated for its submission"* |
| 2026-09-28 晚 | **综述**（`PRLETTERS-D-26-02402`）投稿，**当时已带上 Authorship Confirmation** | 操作者 2026-09-29 确认 |
| 2026-09-29 | **P3 收到编辑部回信，要求补表** | 操作者确认；P3 原投稿清单中无此表 |

## 归属

| 文件 | 归属 | 日期 | 备注 |
|---|---|---|---|
| `paper_review_prl/Authorship Confirmation submit.pdf` | **P3** `...-02378` | `September 26, 2026` | 生成于 09-28 21:54；**与 P3 投稿日一致** ✅ |
| `paper_review_prl/UPLOAD/Authorship Confirmation.pdf` | 同一文件副本 | 同上 | 目录位置有误导性，见下 |
| `paper3/paper_ieee/PRL_submission/Authorship Confirmation (P3, 2026-09-26).pdf` | 同上 | 同上 | 已另存到 P3 目录，便于查找 |
| `paper_a1/_archive_prl/Authorship Confirmation submit.pdf` | A1 `...-01941` | `August 16, 2026` | A1 投稿日 |

## ⚠️ 遗留待核（不影响 P3）

该表**同时存在于 `paper_review_prl/`（综述目录）下**，是历史放置位置造成的。
**综述 `...-02402` 投稿时用的是哪一份表，尚未核实**——若它用的就是这份（日期 09-26 而非 09-28），
表日期与投稿日差 2 天，**建议按 09-28 重新生成一张替换**（改 `tools/_make_prl_authorship_form.py` 的 `NEW_DATE`，
底稿与做法不变）。

**判定方法**：取 `...-02402` 的投稿确认稿（EM 内 Build PDF for my Approval 生成的那种），
看 Authorship Confirmation 页 `Date` 字段。

## 教训（写下来避免重犯）

- 生成"以日期为唯一差异"的表时，**文件名必须带稿号与日期**（如 `Authorship Confirmation (P3, 2026-09-26).pdf`），
  否则同一目录下极易张冠李戴。
- 判断归属时**以 git 提交信息与文件时间戳为准**，不要凭"文件放在哪个目录"推断。
"""


def main() -> int:
    apply = "--apply" in sys.argv
    print(f"将写入: {NOTE.relative_to(REPO)}")
    print("内容要点：表属 P3（日期 09-26，与 P3 投稿日一致）；综述的表待核。")
    if apply:
        NOTE.write_text(TEXT, encoding="utf-8")
        print("\n✅ 已写入")
    else:
        print("\n（预演，加 --apply 生效）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
