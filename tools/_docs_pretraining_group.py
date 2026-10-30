# -*- coding: utf-8 -*-
r"""落账：按预训练目标改写规律（操作者选①，2026-10-08 12:00）。

    python tools\_docs_pretraining_group.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **✅ 2026-10-08 12:00 —— 论文已按①改写：规律改为**按预训练目标分组****
>
> 操作者选①（按预训练分组）。改写脚本 `tools/_pa_group_by_pretraining3.py`。
>
> ### 改了三处
>
> | 处 | 原文 | 改为 |
> |---|---|---|
> | **表 caption** | "The patch column is what the ordering tracks: every patch-32 backbone puts text-only smallest and **every patch-16 backbone puts both there**" | "**Rows are grouped by pre-training objective**, which is what the ordering tracks: every contrastive image--text backbone puts text-only smallest, and the two backbones trained with other objectives put both there. **Patch size does not separate the groups**, and the two rows marked $\\dagger$ show this directly…" |
> | **表体** | 5 行 | **6 行 + 分组小标题**（新增 `CLIP B/32† @ r4`、`CLIP B/16† @ r4`） |
> | **规律句（L165）** | "…every patch-32 backbone has the text-only arm at the smallest gap change and **every patch-16 backbone has the both-position arm there, without exception**" | 明说"**early reading attributed the ordering to patch size** … **That reading does not survive the matched comparison** … **What separates the two orderings is the pre-training objective.**" |
>
> ### 改后的表（`tab:position_strict`）
>
> | 分组 | 骨干 | Pat. | Text-only | Both | Vision-only |
> |---|---|---|---|---|---|
> | **Contrastive image–text pre-training** | CLIP B/32 (WIT) | 32 | **−0.0465** / 0.624 | −0.0258 / **0.693** | +0.0106 / 0.680 |
> | | OpenCLIP B/32 (LAION) | 32 | **+0.0694** / 0.643 | +0.0881 / **0.680** | +0.0925 / 0.672 |
> | | **CLIP B/32† @ r4** | 32 | **−0.0297** / 0.625 | −0.0186 / **0.680** | +0.0124 / 0.668 |
> | | **CLIP B/16† @ r4** | **16** | **−0.0190** / 0.642 | +0.0150 / **0.696** | +0.0433 / 0.677 |
> | **Other objectives** | SigLIP B/16 (WebLI) | 16 | +0.0664 / 0.432 | **−0.0114** / **0.619** | +0.0522 / 0.341 |
> | | BioCLIP B/16 (bio.) | 16 | −0.3671 / — | **−0.4515** / — | −0.2927 / — |
>
> ### 保留的诚实标注（写进 caption）
>
> - **$\\dagger$ 行为单 seed**，而归档行为 5 seed 均值；**CLIP B/32 的逐 seed sd = 0.003**，
>   故单 run 分出的差距是该离散度的数倍；
> - **OpenCLIP 相邻臂差距是所有骨干中最小的**（约 2 倍 sd）→ **其排序应据此理解**；
> - **BioCLIP 只有汇总归档、无逐 run** → 保留原注。
>
> ### 编译与门禁
>
> | 项 | 结果 |
> |---|---|
> | NC | **51 页**（+1，表格新增两行）｜ 0 错误 ｜ 0 未定义引用 ｜ **0 Overfull** |
> | Springer | **38 页**｜ 0 错误 ｜ 0 未定义引用 ｜ **0 Overfull** |
> | 引用 | **47 = bib 47** |
> | **门禁** `tools/_claim_ledger.py` | **36/36 通过**（新增 12 条：两行 × 三臂 × CGΔ+R@1） |
>
> ### 🐛 改稿过程踩的两个坑（已记录）
>
> | 版 | 失败 | 教训 |
> |---|---|---|
> | 1 | 手打 caption 字符串跨行 → **命中 0** | 长字符串跨行匹配易错 |
> | 2 | 找**第一个** `\\caption{` → 改到了 **`fig:overview` 的 caption**（图的，不是表的） | **必须按 label 定位**；断言把旧措辞仍在抓了出来 |
>
> 第 3 版改为**先找 `\\label{tab:position_strict}`，再向上找该表自己的 caption**，
> 且**断言 `fig:overview` 的 caption 未被误改**。用 `git checkout` 恢复了第 2 版的损坏。
"""


def main() -> int:
    apply = "--apply" in sys.argv
    if not apply:
        print("  （预演）")
        return 0
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "论文已按①改写" in t:
        print("  已记录，跳过")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("论文已按①改写", "Patch size does not separate the groups", "36/36 通过",
              "51 页", "必须按 label 定位"):
        assert k in t2, f"断言失败：缺 {k}"
    print(f"  ✅ HANDOFF 已追加（{len(t2.splitlines())} 行）")

    mp = REPO / "文件地图.md"
    m = io.open(mp, encoding="utf-8").read()
    if "0J." not in m:
        add = """
**0J. ✅ 规律已按①改写为「按预训练目标分组」（2026-10-08 12:00）**

- `empirical.tex` 的 `tab:position_strict` **新增两行**（`CLIP B/32† @ r4`、`CLIP B/16† @ r4`，同秩对照）+ **分组小标题**；
  caption 与 L165 规律句均改为「**对比式图文预训练 → text_only 最保护；其它目标 → both**」。
- 旧措辞（"every patch-16 backbone puts both there, without exception"）**已全清**。
- **编译**：NC **51 页**、Springer **38 页**，均 0 错误、0 未定义引用、**0 Overfull**；引用 47 = bib 47。
- **门禁** `tools/_claim_ledger.py` → **36/36 通过**。
- 脚本 `tools/_pa_group_by_pretraining3.py`（**按 label 定位**；前两版因手打跨行串与"找第一个 caption"而失败）。

"""
        anchor = "## 七、当前真正待办（按优先级）\n"
        m2 = m.replace(anchor, anchor + add, 1)
        io.open(mp, "w", encoding="utf-8", newline="").write(m2)
        print(f"  ✅ 文件地图.md 已更新（{len(m2.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
