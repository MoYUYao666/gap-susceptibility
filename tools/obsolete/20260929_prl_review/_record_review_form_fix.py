# -*- coding: utf-8 -*-
r"""把"综述补一张日期正确的表"这一事实写入归属说明与两份交接文档。

事实（2026-09-29 操作者确认）：
  - P3（`PRLETTERS-D-26-02378`）09-26 投稿；09-29 编辑部回信要求补 Authorship Confirmation。
  - 综述（`PRLETTERS-D-26-02402`）09-28 晚投稿，**投稿时用的表日期写的是 09-26**（差 2 天）。
  - 已生成日期正确的综述表：`paper_review_prl/Authorship Confirmation (review, 2026-09-28).pdf`。

    python tools/_record_review_form_fix.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

NOTE_ADD = """
## 2026-09-29 追加：综述的表已按正确日期重生成

**已确认事实**（操作者）：综述 `...-02402` **09-28 晚投稿**，而它投稿时用的表**日期写的是 `September 26, 2026`**
（即与 P3 相同的日期），**相差 2 天**。

**已生成正确版本**：

| 文件 | 归属 | 日期 |
|---|---|---|
| `paper_review_prl/Authorship Confirmation (review, 2026-09-28).pdf` | **综述** `...-02402` | `September 28, 2026` ✅ |

生成命令（可复核）：

```powershell
python tools/_make_prl_authorship_form.py --date "September 28, 2026" --slug "review, 2026-09-28"
```

校验：单页 ✅ ｜ 含日期 ✅ ｜ 姓名×2 ✅ ｜ `None`×2 ✅

**处理建议（按稳妥度排序）**：
1. **等编辑部来信**——P3 就是投稿后 3 天收到补件要求的（09-26 投 → 09-29 要）。若综述也来信，
   顺手交这张日期正确的表，最自然。
2. 若 EM 里 `-02402` 仍可 Attach Files（技术检查阶段通常可以），也可主动上传该表（item type 选 **Cover Letter**），
   并在给编辑的短信里说明"更正日期笔误"。
3. **不要为此撤稿重投**——日期相差 2 天属笔误级瑕疵，撤稿重投的代价远大于收益。

⚠️ **日期依据**：`September 28` 取自"09-28 晚投稿"这一操作者陈述（该稿定稿于 09-28 22:30）。
**若 EM 显示的投稿日为 09-29，请改按 09-29 生成**（命令同上，仅换 `--date`）。
"""


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

    note = REPO / "paper_review_prl" / "AUTHORSHIP_FORM_ATTRIBUTION.md"
    t = io.open(note, encoding="utf-8").read()
    if "2026-09-29 追加" not in t:
        io.open(note, "w", encoding="utf-8", newline="").write(t.rstrip() + "\n" + NOTE_ADD)
        print(f"  ✅ {note.name}: 已追加综述表更正记录")

    handoff = """> **🔴 待办 ①——P3（`...-02378`）补表（编辑部 2026-09-29 回信要求）**：
> **表已就绪**：`paper3/paper_ieee/PRL_submission/Authorship Confirmation (P3, 2026-09-26).pdf`
> （日期 = P3 投稿日 09-26）→ 上传到 **`-02378`**，item type 选 **Cover Letter**，Approve。
>
> **🔴 待办 ②——综述（`...-02402`）表日期更正**：综述 09-28 晚投稿，**但投稿时用的表日期写的是 09-26**（差 2 天）。
> **正确版本已生成**：`paper_review_prl/Authorship Confirmation (review, 2026-09-28).pdf`
> （`September 28, 2026`，单页，姓名/None 校验通过）。
> **建议**：等编辑部来信时顺手上传（P3 就是投稿后 3 天收到要求的）；或若 EM 仍可 Attach Files 就主动上传，
> 附一句"更正日期笔误"。**不要为此撤稿重投。**
> ⚠️ 若 EM 显示的投稿日为 09-29，改按 09-29 生成（`--date` 换一下即可）。
>
> **⚠️ 归属误记的完整留档（2026-09-29 两次反复，避免重犯）**：09-28 21:54 生成 P3 表时提交信息写明
> **"for P3"**（`3a1f6e4`）；但因该文件同时放在 `paper_review_prl/`（综述目录）下，09-29 早间一度被误判为
> "综述的表"并据此改了记录（`970d462`），其中还写错了 P3 的投稿时间。**操作者指出后已全部改回**：
> 表属 P3；文件名统一带**稿号+日期**；归属以 **git 提交信息+时间戳** 判定，**不按所在目录推断**。
> 依据见 `paper_review_prl/AUTHORSHIP_FORM_ATTRIBUTION.md`。"""

    map_block = """> **🔴 P3（`...-02378`）补表（编辑部 2026-09-29 回信要求）**：表已就绪（日期 = P3 投稿日 09-26）：
> `paper3/paper_ieee/PRL_submission/Authorship Confirmation (P3, 2026-09-26).pdf` → 上传到 **`-02378`**，item type **Cover Letter**。
> **🔴 综述（`...-02402`）表日期更正**：综述 09-28 晚投稿，但用的表日期写的是 09-26（差 2 天）。
> 正确版已生成：`paper_review_prl/Authorship Confirmation (review, 2026-09-28).pdf`。
> 建议等编辑来信时顺带交，或 EM 仍可 Attach Files 时主动交；**不要撤稿重投**。
> ⚠️ 两表文件名均带稿号+日期；归属以 git 提交信息为准（见 `paper_review_prl/AUTHORSHIP_FORM_ATTRIBUTION.md`）。"""

    replace_block(REPO / "HANDOFF.md", "待办 —— P3", "P3 投稿包核实", handoff)
    replace_block(REPO / "文件地图.md", "P3（", None, map_block)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
