# -*- coding: utf-8 -*-
r"""Record the v2.1 GitHub release in the hand-off documents.

    python tools/_p1460_record_v21_release.py --apply
"""
from __future__ import annotations

import argparse
import io
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HANDOFF = os.path.join(REPO, "HANDOFF.md")
MAP = os.path.join(REPO, "文件地图.md")

ENTRY = """> **📦 2026-10-21 03:15 —— GitHub v2.1 release 已创建**
>
> | 字段 | 值 |
> |---|---|
> | Release | **v2.1**（Latest）|
> | URL | https://github.com/MoYUYao666/gap-susceptibility/releases/tag/v2.1 |
> | Tag | `v2.1`（annotated `86a3836` → 指向 **mirror** 提交 `c01cd0b`）|
> | 内容 | 仅代码与结果：`tools/` 分析脚本、`outputs/analysis/` 结果 JSON、`docs/provenance_manifest.json` + 清单、`docs/DEEPINFER_NOTES_2026-10-20.md`、`RELEASE_NOTES_v2.1.md`、五包 staged 检查脚本等 |
> | 不含 | 任何稿件源文件/PDF、cover letter、title page、highlights、投稿包（tag 树内 `.tex` 稿件 = 0，唯一 PDF 为 `outputs/` 下的分析图）|
> | 说明 | release 正文为**通用内容清单**，无论文题名/状态/结果细节 |
> | 镜像 | `publish_clean` main `24316ae..c01cd0b` 已推送 |
> | Zenodo | **版本 DOI 待核**：本机 zenodo.org DNS 不可用，无法确认自动抓取状态；概念 DOI 不变，若需要稿件引用请操作者稍后在 Zenodo 记录页核对新版本 DOI |
>
> 至此本轮全部目标闭环：Round 1–3 完成、provenance 硬规则落地且门禁 PASS、六稿终检 ALL PASS、五包 staged 1:1、mirror 推送、v2.1 发布。
>

"""

ROW = ("127. 📦 **GitHub v2.1 release（2026-10-21 03:15）** —— tag `v2.1`（annotated `86a3836` → mirror commit `c01cd0b`），"
       "release 正文为通用内容清单（无论文信息）；内容 = 分析脚本 + 结果 JSON + provenance manifest + DeepInfer notes + "
       "包检查工具；tag 树内稿件 .tex = 0；mirror `24316ae..c01cd0b` 已推；Zenodo 版本 DOI 待核（DNS 不可用）。\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  (dry run)")
        return 0
    h = io.open(HANDOFF, encoding="utf-8").read()
    if "GitHub v2.1 release 已创建" not in h:
        i = h.find("# 项目交接文档")
        j = h.find("\n", i)
        io.open(HANDOFF, "w", encoding="utf-8", newline="").write(h[: j + 1] + "\n" + ENTRY + h[j + 1:])
        print("  handoff updated")
    m = io.open(MAP, encoding="utf-8").read()
    if "GitHub v2.1 release（2026-10-21 03:15）" not in m:
        anchor = "126. 🧪 **Round 2 收口"
        idx = m.find(anchor)
        assert idx >= 0
        end = m.find("\n", idx)
        io.open(MAP, "w", encoding="utf-8", newline="").write(m[: end + 1] + ROW + m[end + 1:])
        print("  file map updated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
