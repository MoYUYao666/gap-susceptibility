# -*- coding: utf-8 -*-
r"""记录 P1（`PR-D-26-10149`）状态日期更新为 2026-10-04（操作者报告，2026-10-04 晚）。

## 依据

操作者提供的 EM 列表行：

| Title | Submitted | Status 日期 | Status |
|---|---|---|---|
| Protect, Don't Perturb: Cross-Modal Alignment under PEFT of Vision-Language Models | Jul 24, 2026 | **Oct 04, 2026** | **Required Reviews Completed** |

**与既有记录的差别**：先前记录的状态日期是 **Sep 30, 2026**（2026-10-01 由操作者报告）。
现在显示 **Oct 04, 2026** → **状态日期被刷新**（很可能是新一轮审稿意见到齐，或编辑流程更新）。

## 诚实标注（必须写清）

- **"Required Reviews Completed" 是状态，不是决定** —— 它表示所需份数的审稿意见已收齐，
  稿件在**编辑手里等决定**；**尚未接受或拒稿**。
- **来源是操作者报告**（未见 EM 截图）→ 记为"操作者报告"，不写成"已核实"。
- 状态日期变化的原因**未知**（可能是追加审稿意见），**不推测**。

## 为什么这条重要

P1 的决定同时决定三条线的走向：

| 结果 | 对 `paper合`（本会话整改对象） | 对 ap3 |
|---|---|---|
| **接收** | 需重新定位（实证部分已另行发表） | 红线仍在，且 ap3 意义下降 |
| **修回** | 需与 P1 的修回内容协调 | 红线仍在 |
| **拒稿** | **`paper合` 成为该工作线主稿，可立即投 Neurocomputing** | **红线解除，ap3 可投** |

    python tools\_docs_p1_status_1004.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENTRY = r"""> **📮 2026-10-04 晚 —— P1（`PR-D-26-10149`）状态日期更新为 Oct 04, 2026**
>
> **来源：操作者报告**（EM 列表，未见截图 → **记为"操作者报告"，不写成"已核实"**）。
>
> | Title | Submitted | Status 日期 | Status |
> |---|---|---|---|
> | Protect, Don't Perturb: Cross-Modal Alignment under PEFT of Vision-Language Models | Jul 24, 2026 | **Oct 04, 2026** | **Required Reviews Completed** |
>
> **与既有记录的差别**：先前记录的状态日期为 **Sep 30, 2026**（2026-10-01 由操作者报告），
> 现显示 **Oct 04, 2026** → **状态日期被刷新**。
>
> ### ⚠️ 必须说清的三点
>
> 1. **这是状态，不是决定** —— "Required Reviews Completed" 表示所需份数的审稿意见**已收齐**，
>    稿件在**编辑手里等决定**；**尚未接受、修回或拒稿**。
> 2. **状态日期变化的原因未知**（可能是追加审稿意见或流程更新）——**不推测**。
> 3. **来源是操作者报告**，未见 EM 截图。
>
> ### 决策影响面（与 2026-10-01 条目一致，未变）
>
> | P1 结果 | 对 `paper/`（P1） | 对 `paper合/`（本会话整改对象） | 对 `ap3/` |
> |---|---|---|---|
> | **接收** | 需按意见修回 | **需重新定位**（实证部分已另行发表）；投稿时点需再议 | 红线仍在，意义下降 |
> | **修回** | 按意见修 | 需与 P1 的修回内容**协调**（避免重复发表） | 红线仍在（待 P1 最终定） |
> | **拒稿** | 该稿终止 | **成为该工作线主稿 → 可立即投 Neurocomputing**（投稿包已就绪） | **红线解除 → ap3 可投** |
>
> ### 当前 `paper合` 的就绪度（若 P1 被拒即可投）
>
> NC 版 **41 页**、Springer 版 **31 页**、0 错误 / 0 未定义引用、cites 41 / bib 41 全匹配、
> 摘要 **244 词**、`paper合/NC_submission/` 终检全绿（`tools/_pa_final_check_nc.py`）。
>
> ### 仍在跑
>
> SigLIP r4 的 `both` 臂（补齐三臂图谱）+ OpenCLIP r4；断点见本日 21:47 条目。

"""


def main() -> int:
    apply = "--apply" in sys.argv
    p = REPO / "HANDOFF.md"
    t = io.open(p, encoding="utf-8").read()
    if "P1（`PR-D-26-10149`）状态日期更新为 Oct 04" in t:
        print("  已记录，跳过")
        return 0
    anchor = "> **✏️ 2026-10-04 下午"
    i = t.find(anchor)
    if i < 0:
        print("  ⚠ 未找到锚点")
        return 1
    if apply:
        io.open(p, "w", encoding="utf-8", newline="").write(t[:i] + ENTRY + t[i:])
        t2 = io.open(p, encoding="utf-8").read()
        for k in ("Oct 04, 2026", "这是状态，不是决定", "状态日期被刷新", "操作者报告"):
            assert k in t2, f"断言失败：缺 {k}"
        print(f"  ✅ HANDOFF 已追加（{len(t2.splitlines())} 行）")
    else:
        print("  （预演）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
