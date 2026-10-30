# -*- coding: utf-8 -*-
r"""Bring the handover documents up to date with the live state, marking superseded numbers explicitly.

The audit (`tools/_p1097_status_audit.py`) found the file map still quoting Paper A at NC 60 / Springer 44
(line 45), NC 60 (line 46), NC 56 / Springer 40 (line 173) and NC 52 / Springer 38 (line 457), while the PDFs
on disk are **NC 67 / Springer 49** after supplement Section F was added. Stale numbers left unmarked have
misled this project before, so each old value is marked as superseded rather than silently replaced, and the
current figures are stated with their source.

    python tools/_p1098_sync_handover.py [--apply]
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MAP = REPO / "文件地图.md"
HANDOFF = REPO / "HANDOFF.md"

REPLACEMENTS = [
    ("> - **`paper合` 当前就绪度**：NC **60 页** / Springer **44 页**，0 错误 / 0 未定义 / 0 Overfull；",
     "> - **`paper合` 当前就绪度（⚠️ 此行为 2026-10-12 记录，页数已过期）**：当时 NC **60 页** / Springer **44 页**；"
     "**现行值见下方 2026-10-16 条目：NC 67 页 / Springer 49 页**（新增补充 F 节后），0 错误 / 0 未定义 / 0 Overfull；"),
    ("> 摘要 **250 词**；投稿包 `NC_submission/Manuscript.pdf` **60 页**已同步；",
     "> 摘要 **250 词**；⚠️ 投稿包 `NC_submission/Manuscript.pdf` 的页数**已过期**——该包**尚未同步** 2026-10-16 的"
     "补充 F 节改动（现行 `paper合/main_nc.pdf` 为 **67 页**）；"),
    ("> **🔄 2026-10-10 页数更新（`paper合`）**：**Springer 版 40 页｜NC 版 56 页**（2026-10-10 晚更新），0 错误、0 未定义引用、0 Overfull。",
     "> **🔄 2026-10-10 页数更新（`paper合`）**：**Springer 版 40 页｜NC 版 56 页**（2026-10-10 晚更新），0 错误、0 未定义引用、0 Overfull。\n"
     "> ⚠️ **已于 2026-10-16 再次更新**：新增补充 F 节后为 **NC 67 页 / Springer 49 页**，0 错误 / 0 未定义引用 / **0 Overfull**，"
     "bib **48 条目 / 48 被引 / 0 缺失**。"),
    ("- **编译**：NC **52 页** / Springer **38 页**，0 错误 0 未定义 0 Overfull。",
     "- **编译（⚠️ 已过期，2026-10-16 现值见下）**：当时 NC **52 页** / Springer **38 页**，0 错误 0 未定义 0 Overfull；"
     "**现值 NC 67 / Springer 49**。"),
]

STATUS = """## 🔴 当前总状态（2026-10-16 22:45 更新）

> 本节由 `tools/_p1098_sync_handover.py` 生成，live 数字均当场实测（脚本 `tools/_p1097_status_audit.py`）。
> **与下方任何旧条目冲突时，以本节为准**（旧条目保留、不重写，仅标注过期）。

### 一、论文状态

| 稿件 | 位置 | 页数（实测）| 编译 | 状态 |
|---|---|---|---|---|
| **Paper A**（P1+P2）| `paper合/` | **NC 67｜Springer 49** | 0 错误 / 0 未定义 / 0 Overfull；bib 48/48 | ✅ 就绪；**2026-10-16 新增补充 F 节**（LLaVA 负结果）；⚠️ `NC_submission/` 投稿包**尚未同步** |
| **P3** | `paper3/paper_ieee/` | 正文 **10 页** | ✅ | **Under Review**（PRL `PRLETTERS-D-26-02378R1`）；替换件已备、**等编辑部回复** |
| A1 | `paper_a1/` | — | — | `NEUNET-D-26-09426` |
| A23 | `paper_a2/` | — | — | IEEE JOE `26-0663` |
| P1 | `paper/` | — | — | `PR-D-26-10149`，**已拒** |

### 二、实验状态（LLaVA 批次）

| 项 | 值 |
|---|---|
| 全量 run | **EXIT=0**、**12 条记录**、**零 arm 失败** |
| 精度 / 规模 | **bf16**、1500 训练 / 500 评测、3 epochs、3 seeds、rank 8 |
| 结果 | frozen **+0.297%±0.000%**、text_only **+0.297%±0.000%**（与 frozen 逐位相同）、vision_only **+13.333%±4.737%**、both **+6.068%±6.547%** |
| **适配器** | **7 个 `.pt`（773 MB）已取回本地** `outputs/llava_bf16_sites_cloud/` |
| 门禁 | `_p984` **all checks passed**；账本 **96/96**（含 16 条 LLaVA 条目 + 与汇总文件逐位交叉校验） |
| **待办** | ⏭️ **规范度量重算**（`docs/resume_2026-10-17_llava_metric.md`）：归档用的是自写 gap 定义，论文/ODE 用 `src/dg_star_tracker.py:compute` ⇒ **不是同一量**；**不需重训**（适配器已存，只做前向），**先只算 frozen 验证分辨率** |

### 三、Qwen 状态

| 项 | 值 |
|---|---|
| 运行器 | `tools/_p1035_qwen_sites.py` **已就绪**（七项架构差异全部适配并验证）|
| 阻塞 | **bf16 下 32 GB 装不下 7B**：31.09/31.48 GiB 已分配，把 batch/max-len/eval-batch 压到最小（1/512/1）**失败点不移动** ⇒ 是权重+优化器底噪，非激活 |
| 结论 | **需 >32 GB 卡**（或 4-bit，与"不要 4bit"口径冲突，未做）|

### 四、规则（2026-10-16 立）

**下载源优先级**：⭐ **`hf-mirror.com` 首选**（主机 3：15 GB/6–8 分钟）→ tuna（pip）→ ModelScope 兜底；
**每台新机先探速**（同一天两台机镜像速度差 60 倍）；**单连慢先测多连接**（ModelScope 单连 ~1 MB/s → 32 路 **13–18 MB/s**）；
`download.pytorch.org` 与直连 `huggingface.co` 不可用。

"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(MAP, encoding="utf-8").read()
    changed = 0
    for old, new in REPLACEMENTS:
        if old in t:
            t = t.replace(old, new, 1)
            changed += 1
        else:
            print(f"  not found (already handled?): {old[:60]}...")
    print(f"  {changed}/{len(REPLACEMENTS)} stale page-count claims marked as superseded")
    if not a.apply:
        print("  (dry run)")
        return 0
    marker = "## 🔴 当前总状态（2026-10-16 22:45 更新）"
    if marker not in t:
        # insert after the top-level heading block so it is the first thing a reader sees
        lines = t.splitlines(keepends=True)
        insert_at = 1
        for i, l in enumerate(lines[:40]):
            if l.startswith("# "):
                insert_at = i + 1
                break
        t = "".join(lines[:insert_at]) + "\n" + STATUS + "\n" + "".join(lines[insert_at:])
        print("  status section inserted at the top of 文件地图.md")
    io.open(MAP, "w", encoding="utf-8", newline="").write(t)

    # a matching pointer in HANDOFF so the two agree
    h = io.open(HANDOFF, encoding="utf-8").read()
    line = ("\n> **📊 2026-10-16 22:45 —— 状态总览**：Paper A **NC 67 / Springer 49 页**（补充 F 节后，0 错/0 未定义/0 Overfull）；"
            "LLaVA 批次 **12 条记录 + 7 个适配器（773 MB）**已归档本地、门禁 **96/96**；Qwen 运行器就绪但**32 GB 装不下 7B**；"
            "规范度量重算**待明天**（`docs/resume_2026-10-17_llava_metric.md`）。详见 `文件地图.md` 顶部「当前总状态」。\n")
    if "状态总览**：Paper A **NC 67" not in h:
        i = h.find("# 项目交接文档")
        j = h.find("\n", i)
        h = h[: j + 1] + line + h[j + 1:]
        io.open(HANDOFF, "w", encoding="utf-8", newline="").write(h)
        print("  HANDOFF pointer added")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
