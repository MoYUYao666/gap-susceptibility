# -*- coding: utf-8 -*-
r"""Record the normal-named upload folder and the title check.

Operator instruction (2026-10-15): the replacement files should carry their ordinary names, not a
"corrected" suffix. `SUBMISSION/P3_PRL_revision/UPLOAD_2026-10-15/` now holds both namings,
byte-identical: plain (`main.pdf`, `supplementary.pdf`) and manuscript-numbered
(`P3_PRLETTERS-D-26-02378_Manuscript.pdf`, `..._Supplementary.pdf`), the latter matching the slots the
13 October upload used.

Also recorded, because it was worth checking before any upload: the submitted manuscript's title is
already the short one used by the memo row, so a replacement does not change it. The longer "Gradient
Structure Laws as Predictors of PEFT Design: ..." appears in the submission package's title page, not in
the manuscript body.

    python tools/_p901_record_upload_folder.py [--apply]
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HANDOFF = REPO / "HANDOFF.md"
MAP = REPO / "文件地图.md"
MARK = "P3 替换件已按正常文件名备好"

ENT = """> **🗂️ 2026-10-15 14:15 —— P3 替换件已按「正常文件名」备好；并核实标题一致**
>
> 操作者指令：**「不用 main_corrected.pdf 加 corrected，正常即可」**。
>
> ### 一、✅ 待上传目录（两种命名并存，**逐字节相同**）
>
> `SUBMISSION/P3_PRL_revision/UPLOAD_2026-10-15/`
>
> | 文件 | 大小 | 说明 |
> |---|---|---|
> | `main.pdf` | 415,088 | 普通名 |
> | `supplementary.pdf` | 270,572 | 普通名 |
> | `P3_PRLETTERS-D-26-02378_Manuscript.pdf` | 415,088 | **与 10-13 上传所用槽位同名**（与 `main.pdf` SHA-256 相同）|
> | `P3_PRLETTERS-D-26-02378_Supplementary.pdf` | 270,572 | 同上 |
> | `README.md` | — | 两版差别 + 复核命令 + 两种命名说明 |
>
> **两处目录都加了指引**，避免开错：`UPLOAD/README_UPLOAD.txt` 注明「本目录是 **10-13 已提交版**，替换件见
> `../UPLOAD_2026-10-15/`」；`UPLOAD_2026-10-15/README.md` 注明「本目录是**今天的替换件**，已提交版在 `../UPLOAD/`」。
>
> **零删除**：`CORRECTED_2026-10-15/` 里的两个带 `_corrected` 名的文件**保留**（作对照），
> 只把 `README.md` 的措辞改成正常名；`UPLOAD/`（已提交版）与**任何文件都未删**。
>
> ### 二、✅ 上传前核实：**标题无需改动**
>
> | 检查 | 结果 |
> |---|---|
> | 已提交正文（`UPLOAD/P3_PRLETTERS-D-26-02378_Manuscript.pdf`，10 页）第 1 页标题 | **`Zero-Shot Cross-Architecture Rank Allocation from Gradient Geometry`** |
> | 替换件 `main.pdf` 第 1 页标题 | **完全相同** |
> | 长标题 `Gradient Structure Laws as Predictors of PEFT Design: …` | 出现在**投稿包的 title page**（`PRLETTERS-D-26-02378_R1.pdf` 第 5 页），**不在正文里** |
>
> ⇒ **替换不会改变正文标题**（与 EM 行的 Title 字段一致）。
>
> ### 三、⚠️ 顺带记录：桌面上的两份原件已不在原位
>
> 我先前读取的 `C:\\Users\\hongr\\Desktop\\PRLETTERS-D-26-02378_R1.pdf` 与
> `P3_PRLETTERS-D-26-02378_Supplementary.pdf` **现在已不存在于桌面**（可能被操作者移动或已上传）。
> **不影响核对结论**：工作区内有**逐字节副本**——已提交正文与补充分别在
> `SUBMISSION/P3_PRL_revision/UPLOAD/P3_PRLETTERS-D-26-02378_{Manuscript,Supplementary}.pdf`
> （414,938 / 266,021 字节），此前核对所依据的就是它们与桌面件的同源关系。
>
> ### 四、⏳ 下一步
>
> **等编辑部回复**；同意后上传 `UPLOAD_2026-10-15/` 中**带稿号的那两个**（与文件槽位同名，无需改名）。
> 若只允许换补充 ⇒ 只传 `P3_PRLETTERS-D-26-02378_Supplementary.pdf`，正文按信中承诺只改 5 个数字。
>
> **工具**：`tools/_p898_stage_upload.py`（按正常名建目录）｜`_p899_clarify_upload_folders.py`（两目录互相指引）｜
> `_p900_numbered_names.py`（加稿号命名并校验同一性）｜`_p901_record_upload_folder.py`（本条落账）。
>

"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    hp = io.open(HANDOFF, encoding="utf-8").read()
    if MARK in hp:
        print("  already recorded")
        return 0
    if not a.apply:
        print("  (dry run)")
        return 0

    i = hp.find("# 项目交接文档")
    j = hp.find("\n", i)
    hp = hp[: j + 1] + "\n" + ENT + hp[j + 1:]
    io.open(HANDOFF, "w", encoding="utf-8", newline="").write(hp)

    mp = io.open(MAP, encoding="utf-8").read()
    row = ("21. 🗂️ **P3 替换件已按正常文件名备好（2026-10-15 14:15）** —— "
           "`SUBMISSION/P3_PRL_revision/UPLOAD_2026-10-15/`：`main.pdf`(415,088) / `supplementary.pdf`(270,572) "
           "**默认名**，另附**与槽位同名**的 `P3_PRLETTERS-D-26-02378_Manuscript.pdf` / `..._Supplementary.pdf`"
           "（逐字节相同）。`UPLOAD/`（10-13 已提交版）未动，两目录互加指引避免开错。"
           "**上传前核实**：正文标题与已提交版**相同**（短标题），长标题只在投稿包 title page。"
           "⚠️ 桌面原件已不在原位，但工作区有逐字节副本。详见 `HANDOFF.md` 顶部 2026-10-15 14:15 条目。\n")
    anchor = "20. 📤 **P3 替换件申请已发 EM（2026-10-15 14:10）**"
    idx = mp.find(anchor)
    if idx >= 0:
        end = mp.find("\n", idx)
        mp = mp[: end + 1] + row + mp[end + 1:]
        io.open(MAP, "w", encoding="utf-8", newline="").write(mp)
    else:
        print("  WARN: map item 20 not found")

    h2 = io.open(HANDOFF, encoding="utf-8").read()
    for k in ("正常文件名", "UPLOAD_2026-10-15", "标题无需改动", "已不在原位"):
        print(f"  {'OK ' if k in h2 else 'BAD'} handoff::{k}")
    print(f"  HANDOFF lines = {len(h2.splitlines())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
