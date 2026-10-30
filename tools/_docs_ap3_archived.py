# -*- coding: utf-8 -*-
r"""ap3 归档后重建根目录索引，并修正 A1 的记录（2026-10-06）。

## 两件事

### ① ap3 已移出根目录 → 索引从 9 个 `paper*` 变 **8 个**

### ② **修正 A1 的记录——我之前写错了**

我原先把 A1 写成"**不在推进队列**"。**错**。操作者提供的投稿记录显示：

| 项 | 事实 |
|---|---|
| 标题 | **The Modality Gap Is Not a Universal Health Metric: Order Preservation Governs Zero-Shot Robustness** |
| 期刊 | **Neurocomputing** |
| 稿号 | **`NEUCOM-D-26-20952`** |
| 时间 | 提交 **2026-09-16** ｜ 状态更新 **2026-09-17** |
| 状态 | **With Editor** |
| 前身 | `PRLETTERS-D-26-01941`（2026-09-14 被 PRL 拒） |

### ③ **并且这暴露一个我必须提请你注意的冲突**

**A1 已在 Neurocomputing 在审（With Editor）**，而 `paper合/` 的目标期刊**也是 Neurocomputing**。

**同一作者向同一期刊投两篇相关稿**（都做 PEFT 下的 modality gap、都测零样本），
编辑可能视为**重复发表或自我竞争**。

**两篇的区别**（实测）：

| | A1（`paper_a1/`） | `paper合/` |
|---|---|---|
| 核心主张 | 间隙**不是**普适健康指标；**阶序保持**决定零样本鲁棒性 | Gap Susceptibility + 一阶 ODE |
| 独有构件 | Order Preservation、gap surgery（精确全局平移） | Gap Susceptibility、Distribution Gap |
| 共有构件 | — | — |

→ **理论构件不重叠**，但**主题（PEFT 下的 modality gap）与实验场景（零样本）重叠**。
**这需要你决定**：是否换刊、是否在投稿信里说明区别、或等 A1 决定。

    python tools\_docs_ap3_archived.py [--apply]
"""
from __future__ import annotations

import io
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENTRY = r"""> **🗄️ 2026-10-06 —— ap3 归档进 `备选/`；**并修正 A1 的记录（我先前写错）+ 提请注意一个投稿冲突****
>
> 操作者指示："**不可投放进备选**"，并给出三条投稿记录纠正我的记录。
>
> ### ① ap3 已归档
>
> `paper_ap3/` → **`备选/06_归档稿件/paper_ap3/`**（113 项，7 MB）。
> **21 个 ap3 专用脚本一并归档**（`备选/06_归档稿件/ap3_工具/`）——它们是审计/打补丁工具，
> **ap3 归档后已无对象**，留着只会变成"指向不存在目录"的脚本。
> 归档说明：`备选/06_归档稿件/AP3_归档说明.md`。
>
> **修正的引用（8 处）**：
>
> | 类型 | 脚本 | 处置 |
> |---|---|---|
> | 发布工具（**会因目录不存在出错**） | `_publish_new_files.py`、`_sync_publish_round10.py`、`_publish_live_drift.py` | **从目录列表移除** |
> | 硬编码路径 | `_fix_op_dates_20260924.py` | 改指归档路径 |
> | 文档串 | `_pa_to_elsarticle.py`、`_pa_build_nc_package.py`、`_pa_add_declarations.py`、`_pa_fix_m1_evidence.py`、`_p1_log_append7.py` | 改指归档路径 |
> | 通用 bib 工具 | `_bib_verify.py`、`_p1_bib_fix.py` | `paper_ap3/refs.bib` → **`paper合/references.bib`**（等价后继） |
>
> **保留**：`_a1_cover_letter_fix.py`、`_fix_round2.py`、`audit_submission_pdfs.py` 等里的 `'paper_ap3'`
> 是**禁用词表**（确保投稿件不提及它）——字符串，非路径，仍正确。
>
> **根目录 `paper*` 由 9 个减为 8 个**；索引 `哪篇是哪篇.md` 已重建。
>
> ### ② ⚠️ 修正：我先前把 A1 写成"不在推进队列"——**错**
>
> 操作者提供的记录：
>
> | 项 | 事实 |
> |---|---|
> | 标题 | **The Modality Gap Is Not a Universal Health Metric: Order Preservation Governs Zero-Shot Robustness** |
> | 期刊 | **Neurocomputing** |
> | 稿号 | **`NEUCOM-D-26-20952`** |
> | 时间 | 提交 **2026-09-16** ｜ 状态更新 **2026-09-17** |
> | **状态** | **With Editor** |
> | 前身 | `PRLETTERS-D-26-01941`（2026-09-14 PRL 拒稿后转投） |
>
> （我的文档里记的还是旧的 *Submitted to Journal*，且我把 A1 归为"不在推进队列"——两处均更正。）
>
> ### ③ ⚠️⚠️ 由此暴露的**投稿冲突**（之前完全没联系起来）
>
> **A1 已在 Neurocomputing 在审（With Editor），而 `paper合/` 的目标期刊也是 Neurocomputing。**
>
> 同一作者向同一期刊投两篇**相关**稿件（都做 PEFT 下的 modality gap、都测零样本），
> 编辑可能视为**重复发表或自我竞争**。
>
> **两篇的理论构件不重叠**（实测）：
>
> | | A1（`paper_a1/`） | `paper合/` |
> |---|---|---|
> | 核心主张 | 间隙**不是**普适健康指标；**阶序保持**决定零样本鲁棒性 | Gap Susceptibility + 一阶 ODE |
> | 独有构件 | Order Preservation、gap surgery（精确全局平移） | Gap Susceptibility、Distribution Gap |
>
> **但主题与实验场景重叠。这需要操作者决定**：换刊 ／ 投稿信中说明区别 ／ 等 A1 决定。
>
> ### ④ 三条在审稿号（按操作者记录更新）
>
> | 稿号 | 期刊 | 是哪篇 | 状态 |
> |---|---|---|---|
> | `PR-D-26-10149` | Pattern Recognition | **P1**（`paper/`） | Required Reviews Completed |
> | **`NEUCOM-D-26-20952`** | **Neurocomputing** | **A1（`paper_a1/`）** | **With Editor** |
> | `PRLETTERS-D-26-02378` | Pattern Recognition Letters | **P3**（`paper3/`） | Under Review |
> | `PRLETTERS-D-26-02402` | Pattern Recognition Letters | **Commentary**（`paper_review/`） | Under Review |
> | `26-0663` | IEEE JOE | **A2/A23**（`paper_a2/`） | 已投 |

"""

# A1 的索引条目修正
A1_FIX = [
    ("paper_a1", "**A1**", "main.tex",
     "**Neurocomputing** ｜ 稿号 **`NEUCOM-D-26-20952`** ｜ **With Editor**（2026-09-16 投，"
     "前身 `PRLETTERS-D-26-01941` 于 09-14 被 PRL 拒）｜⚠️ **与 `paper合/` 同刊，见下方冲突提示**"),
]


def main() -> int:
    apply = "--apply" in sys.argv
    # ① 从索引脚本中移除 ap3
    iw = REPO / "tools" / "_write_paper_index.py"
    s = io.open(iw, encoding="utf-8").read()
    if '"paper_ap3"' in s:
        # 删掉 ap3 的元组行
        import re
        s2 = re.sub(r'\n    \("paper_ap3",[\s\S]*?\),(?=\n    \("paper_review")', "", s, count=1)
        if s2 != s:
            print("  ✅ 索引脚本：已移除 ap3 条目")
            if apply:
                io.open(iw, "w", encoding="utf-8", newline="").write(s2)
        else:
            print("  ⚠ 索引脚本：ap3 条目未匹配删除")

    # ② 修正索引脚本里的 A1 描述
    if apply:
        s = io.open(iw, encoding="utf-8").read()
        old_a1 = ('    ("paper_a1", "**A1**", "main.tex", "main.pdf",\n'
                  '     "Neurocomputing 方向 ｜ **不在推进队列**", "`main_zh.pdf`(22页) 中文版"),')
        new_a1 = ('    ("paper_a1", "**A1** — The Modality Gap Is Not a Universal Health Metric",\n'
                  '     "main.tex", "main.pdf",\n'
                  '     "**Neurocomputing** ｜ 稿号 **`NEUCOM-D-26-20952`** ｜ **With Editor**"\n'
                  '     "（2026-09-16 投；前身 `PRLETTERS-D-26-01941` 于 09-14 被 PRL 拒）"\n'
                  '     "｜⚠️ **与 `paper合/` 同刊（Neurocomputing），见索引末尾的冲突提示**",\n'
                  '     "`main_zh.pdf`(22页) 中文版"),')
        if old_a1 in s:
            s = s.replace(old_a1, new_a1, 1)
            io.open(iw, "w", encoding="utf-8", newline="").write(s)
            print("  ✅ 索引脚本：A1 描述已更正")
        else:
            print("  ⚠ 索引脚本：A1 条目未匹配（可能格式不同），打印实际：")
            i = s.find('"paper_a1"')
            print("     " + repr(s[i:i + 220]))

    if not apply:
        print("\n  （预演）")
        return 0

    # ③ 索引正文加冲突提示
    s = io.open(iw, encoding="utf-8").read()
    marker = '"## 二、⭐ 三句话记住"'
    note = ('"## 二、⚠️ 一个需要你决定的冲突", "",\n'
            '          "**A1（`paper_a1/`）已在 Neurocomputing 在审（With Editor），'
            '而 `paper合/` 的目标期刊也是 Neurocomputing。**", "",\n'
            '          "同一作者向同一期刊投两篇相关稿（都做 PEFT 下的 modality gap、都测零样本），'
            '编辑可能视为重复发表或自我竞争。", "",\n'
            '          "**两篇的理论构件不重叠**（A1 用 Order Preservation / gap surgery；'
            '`paper合` 用 Gap Susceptibility / ODE），但主题与实验场景重叠。", "",\n'
            '          "→ **需要决定**：换刊 ／ 在投稿信中说明区别 ｜ 等 A1 决定。", "",\n'
            '          "## 三、⭐ 三句话记住", "",')
    if "一个需要你决定的冲突" not in s and marker in s:
        io.open(iw, "w", encoding="utf-8", newline="").write(s.replace(marker, note, 1))
        print("  ✅ 索引脚本：已加冲突提示段")

    # ④ 重建索引
    r = subprocess.run([sys.executable, str(iw), "--apply"], capture_output=True, cwd=REPO)
    print("  " + r.stdout.decode("utf-8", "ignore").strip().replace("\n", "\n  "))

    # ⑤ HANDOFF
    hp = REPO / "HANDOFF.md"
    h = io.open(hp, encoding="utf-8").read()
    if "ap3 归档进 `备选/`" not in h:
        anchor = "> **📐 2026-10-06 —— patch 尺寸分组写入正文"
        i = h.find(anchor)
        if i > 0:
            io.open(hp, "w", encoding="utf-8", newline="").write(h[:i] + ENTRY + h[i:])
            h2 = io.open(hp, encoding="utf-8").read()
            for k in ("NEUCOM-D-26-20952", "With Editor", "投稿冲突", "ap3_工具"):
                assert k in h2, f"HANDOFF 断言失败：缺 {k}"
            print(f"  ✅ HANDOFF 已追加（{len(h2.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
