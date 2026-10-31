# -*- coding: utf-8 -*-
r"""Record the 2026-10-17 workspace cleanup in the handover documents.

    python tools/_p1162_record_cleanup.py [--apply]
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HANDOFF = REPO / "HANDOFF.md"
MAP = REPO / "文件地图.md"
MARK = "工作区清理"

ENT = """> **🧹 2026-10-17 19:15 —— 工作区清理（操作者：保留 data 和 models）**
>
> ### 一、结果
>
> | 指标 | 清理前 | 清理后 |
> |---|---|---|
> | 工作区总量（不含 `.git`）| **119 GB** | **85.2 GB** |
> | D 盘可用 | 112.9 GB | **144.3 GB（+31.4 GB）** |
>
> ### 二、删了什么（全部 git-ignored，仓库未受影响）
>
> | 项 | 大小 | 说明 |
> |---|---|---|
> | `outputs/**/*.pt` 历史检查点 | **21.83 GB**（1423 个）| 论文数字均在 JSON 中，账本只引 JSON |
> | `_removed_from_publish/` | 19 MB | 已从发布库移出文件的暂存 |
> | `.codegraph/` | 83 MB | 可再生的代码图谱缓存 |
> | 旧快照 `snapshot_FULL_20260930.zip` | **13.74 GB** | 已由新快照取代 |
> | 新建快照 `snapshot_FULL_20261017_after_cleanup` | **+4.25 GB** | 14,369 条目，**含 9 个适配器** |
>
> **净释放 ≈ 31.4 GB。**
>
> ### 三、⚠️ 明确保留（有理由，不是遗漏）
>
> | 项 | 大小 | 理由 |
> |---|---|---|
> | **`outputs/llava_canonical_cloud/*.pt`**（9 个 LoRA 适配器）| **1.58 GB** | **今天重训的唯一副本**；云机按新规则即将关机，G 节的干净数值只能由这些文件复现。脚本用**路径白名单**排除，不靠大小启发 |
> | `data/` | 51.3 GB | 操作者指定保留 |
> | `models/` | 27.6 GB | 操作者指定保留 |
> | `envs/tf457/` | 102 MB | 本地 Python 环境，脚本可能引用 |
>
> ### 四、备份校验（按备份纪律，先校验再删旧的）
>
> 新快照 `snapshot_FULL_20261017_after_cleanup`：
> - **sha256 重算一致**：`07f8e3f8208ba6dca71814f0bfc8582bb2308c1361f69e003a6784969519d26b`
> - `zipfile.testzip()` → **OK**；条目 **14,369**；manifest 与 `.sha256` 齐备；
> - **9 个 LLaVA 适配器在包内**（双重保险）。
>
> ### 五、脚本
>
> - `tools/_p1159_workspace_survey.py`（只测量、不删除，分级 SAFE/LIKELY/ASK/KEEP）
> - `tools/_p1160_cleanup_safe.py`（只删 `__pycache__` 与根目录 stray log，带保护目录断言）
> - `tools/_p1161_cleanup_artifacts.py`（删检查点，**排除 `outputs/llava_canonical_cloud/`**）
> - `tools/_p1162_record_cleanup.py`（本条）
>

"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  (dry run)")
        return 0
    hp = io.open(HANDOFF, encoding="utf-8").read()
    if MARK not in hp:
        i = hp.find("# 项目交接文档")
        j = hp.find("\n", i)
        hp = hp[: j + 1] + "\n" + ENT + hp[j + 1:]
        io.open(HANDOFF, "w", encoding="utf-8", newline="").write(hp)
        print("  handoff entry added")
    else:
        print("  handoff already has this entry")
    mp = io.open(MAP, encoding="utf-8").read()
    row = ("54. 🧹 **工作区清理（2026-10-17 19:15，操作者：保留 data 和 models）** —— 工作区 **119 GB → 85.2 GB**，"
           "D 盘可用 **+31.4 GB（→144.3 GB）**。删：历史 `.pt` 检查点 **21.83 GB/1423 个**、`_removed_from_publish/`、`.codegraph/`、"
           "旧快照 **13.74 GB**；新建快照 **4.25 GB**（sha256 重算一致、zip 完整、14,369 条目、**含 9 个适配器**）。"
           "**明确保留**：`outputs/llava_canonical_cloud/` 9 个适配器（**唯一副本**，路径白名单排除）、`data/`、`models/`、`envs/`。"
           "删的均为 git-ignored，仓库未受影响。脚本 `_p1159`/`_p1160`/`_p1161`。详见 `HANDOFF.md` 19:15 条目。\n")
    if "工作区清理（2026-10-17 19:15" not in mp:
        anchor = "53. 🕐 **进行中：E 节干净重跑"
        idx = mp.find(anchor)
        if idx >= 0:
            end = mp.find("\n", idx)
            mp = mp[: end + 1] + row + mp[end + 1:]
            io.open(MAP, "w", encoding="utf-8", newline="").write(mp)
            print("  map item added")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
