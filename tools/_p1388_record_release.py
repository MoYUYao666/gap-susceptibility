# -*- coding: utf-8 -*-
r"""Record the v2.0 release, verify the tag state, and note the pending Zenodo version DOI.

    python tools/_p1388_record_release.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import subprocess

HANDOFF = "HANDOFF.md"
MAP = "文件地图.md"
NOTES = "RELEASE_NOTES_v2.0.md"
MIRROR = "publish_clean"
URL = "https://github.com/MoYUYao666/gap-susceptibility/releases/tag/v2.0"

ENT = f"""> **🚀 2026-10-20 00:20 —— 全部本地升级完成，公开镜像发布 **v2.0**（不移动 v1.0）**
>
> | 项 | 状态 |
> |---|---|
> | 发布 | GitHub release **v2.0**：{URL} |
> | 镜像 | `publish_clean` 已推送（本次 25 文件；边界核对：稿件类 0、>100MB 0）|
> | **v1.0 冻结** | tag `v1.0-prl-revision`（`e320e75`）与版本 DOI `10.5281/zenodo.23341223` **未动** |
> | **Zenodo v2.0** | 集成异步处理中；新版本 DOI 出现在 Zenodo 记录页后，回填到本文件与 `文件地图.md`（**待补**）|
> | 升级内容 | A1 早停基线（min-$M$ 0.18 vs 置信度 2.80–4.18）+ checkpoint 钩子；A23 τ 阳性对照（+0.85/+0.81）、12 域臂迁移、UATD 第二声呐域（OOD 边界，如实记录）；P3 当前协议完整曲线（r=5 跨零、r=6 两 seed 为正、r=7/8/10/16 依次 +214.5/+262.0/+298.0/+1235.0；置换 p=0.33，如实说明功效）+ 本地 CLIP 控制；Commentary 合规段与六实例表（7 页）|
> | 审计 | P3/A23/Commentary/PaperA-Springer **READY/A**；A1 与 PaperA-NC 仅剩预期 I-02（冻结包 vs 本地升级稿）|
>
> **下一动作**：修回时按 `_venue_builds/` 的五个包提交；Zenodo 新 DOI 出现后回填。
>

"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    tags = subprocess.run(["git", "-C", MIRROR, "tag", "--list"], capture_output=True, text=True).stdout.split()
    log = subprocess.run(["git", "-C", MIRROR, "log", "--oneline", "-1"], capture_output=True, text=True).stdout.strip()
    print("  mirror tags:", sorted(tags), "| head:", log)
    print("  v1.0 present:", "v1.0-prl-revision" in tags, "| v2.0 present:", "v2.0" in tags)
    if not a.apply:
        print("  (dry run)")
        return 0
    h = io.open(HANDOFF, encoding="utf-8").read()
    if "公开镜像发布 **v2.0**" not in h:
        i = h.find("# 项目交接文档")
        j = h.find("\n", i)
        io.open(HANDOFF, "w", encoding="utf-8", newline="").write(h[: j + 1] + "\n" + ENT + h[j + 1:])
        print("  handoff entry added")
    m = io.open(MAP, encoding="utf-8").read()
    row = (f"119. 🚀 **Release v2.0（2026-10-20 00:20）** —— GitHub release {URL}；镜像推送 25 文件（稿件类 0、>100MB 0）；"
           f"v1.0 tag/DOI 未动；Zenodo 新版本 DOI **待补**（异步）；五个修回包已重建。\n")
    if "Release v2.0（2026-10-20 00:20）" not in m:
        anchor = "118. 🏁 **本地升级全部完成"
        idx = m.find(anchor)
        assert idx >= 0
        end = m.find("\n", idx)
        io.open(MAP, "w", encoding="utf-8", newline="").write(m[: end + 1] + row + m[end + 1:])
        print("  map row added")
    n = io.open(NOTES, encoding="utf-8").read()
    if "github.com/MoYUYao666/gap-susceptibility/releases/tag/v2.0" not in n:
        n = n.replace("Status: **prepared, not yet tagged**.",
                      "Status: **released** — https://github.com/MoYUYao666/gap-susceptibility/releases/tag/v2.0 . "
                      "The Zenodo version DOI for this release is minted asynchronously and is recorded in HANDOFF.md "
                      "when it appears.", 1)
        io.open(NOTES, "w", encoding="utf-8", newline="").write(n)
        print("  release notes updated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
