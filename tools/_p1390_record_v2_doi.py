# -*- coding: utf-8 -*-
r"""Record the v2.0 version DOI provided by the operator: 10.5281/zenodo.23479164.

    python tools/_p1390_record_v2_doi.py [--apply]
"""
from __future__ import annotations

import argparse
import io

HANDOFF = "HANDOFF.md"
MAP = "文件地图.md"
NOTES = "RELEASE_NOTES_v2.0.md"
DOI = "10.5281/zenodo.23479164"

ENT = f"""> **🔖 2026-10-20 08:00 —— v2.0 的 Zenodo 版本 DOI 已落账：`{DOI}`**
>
> 操作者提供：Zenodo 记录 **`v2.0`（MoYUYao666/gap-susceptibility: v2.0）**，版本 DOI **`{DOI}`**；记录标题已为 `v2.0`（不含论文细节）。
>
> | 记录 | DOI |
> |---|---|
> | v1.0-prl-revision（冻结，`e320e75`）| `10.5281/zenodo.23341223` |
> | **v2.0（当前最新）** | **`{DOI}`** |
>
> **引用规则**：已投出的稿件继续引用 **v1.0 版本 DOI**；修回版可在 Data availability 中引用 **v2.0 版本 DOI**（`{DOI}`），
> 或在同时指向两版时说明"v2.0 为更新版本"。概念 DOI（始终指向最新版）由 Zenodo 记录页自动维护，不手填。
>

"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  (dry run)")
        return 0
    changed = 0
    h = io.open(HANDOFF, encoding="utf-8").read()
    old = ("> | **Zenodo v2.0** | 集成异步处理中；新版本 DOI 出现在 Zenodo 记录页后，回填到本文件与 `文件地图.md`（**待补**）|")
    new = (f"> | **Zenodo v2.0** | 版本 DOI **`{DOI}`**（2026-10-20 操作者提供）；记录标题 `v2.0`；v1.0 记录不动 |")
    if old in h:
        h = h.replace(old, new, 1)
        changed += 1
        print("  release entry updated")
    old2 = ("> | 待补 | v2.0 的 Zenodo 版本 DOI（异步生成）与修改后的标题；出现后回填本文件与 `文件地图.md` |")
    new2 = f"> | Zenodo DOI | 已回填：**`{DOI}`**（版本 DOI）；记录标题 `v2.0` |"
    if old2 in h:
        h = h.replace(old2, new2, 1)
        changed += 1
        print("  choice-A entry updated")
    if "v2.0 的 Zenodo 版本 DOI 已落账" not in h:
        i = h.find("# 项目交接文档")
        j = h.find("\n", i)
        h = h[: j + 1] + "\n" + ENT + h[j + 1:]
        changed += 1
        print("  handoff entry added")
    io.open(HANDOFF, "w", encoding="utf-8", newline="").write(h)

    m = io.open(MAP, encoding="utf-8").read()
    old3 = "v1.0 tag/DOI 未动；Zenodo 新版本 DOI **待补**（异步）；五个修回包已重建。"
    new3 = f"v1.0 tag/DOI 未动；**Zenodo v2.0 版本 DOI `{DOI}`**；五个修回包已重建。"
    if old3 in m:
        m = m.replace(old3, new3, 1)
        changed += 1
        print("  map row updated")
    row = (f"121. 🔖 **v2.0 版本 DOI 落账（2026-10-20 08:00）** —— Zenodo 记录 `v2.0` 版本 DOI **`{DOI}`**（操作者提供）；"
           f"v1.0 版本 DOI `10.5281/zenodo.23341223` 不变；已投稿件引 v1.0、修回可引 v2.0。\n")
    if "v2.0 版本 DOI 落账（2026-10-20 08:00）" not in m:
        anchor = "120. ⏳ **P3 Decision in Process"
        idx = m.find(anchor)
        assert idx >= 0
        end = m.find("\n", idx)
        m = m[: end + 1] + row + m[end + 1:]
        changed += 1
        print("  map row added")
    io.open(MAP, "w", encoding="utf-8", newline="").write(m)

    n = io.open(NOTES, encoding="utf-8").read()
    if DOI not in n:
        n = n.rstrip("\n") + f"\n\nVersion DOI: `{DOI}`\n"
        io.open(NOTES, "w", encoding="utf-8", newline="").write(n)
        changed += 1
        print("  release notes file updated")
    print("  changed:", changed)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
