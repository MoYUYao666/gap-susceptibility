# -*- coding: utf-8 -*-
r"""Record the cleanup: what was removed, what was kept, what has to be re-downloaded.

    python tools/_p1049_record_cleanup.py [--apply]
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HANDOFF = REPO / "HANDOFF.md"
MAP = REPO / "文件地图.md"
MARK = "磁盘清理"

ENT = """> **🧹 2026-10-16 19:20 —— 磁盘清理：**共释放约 83 GB**（C 盘 52.4 → **93.8 GB**、D 盘 82.7 → **125.7 GB**）**
>
> 操作者指令：**「qwen开跑之后将本地workspace和C盘不需要的垃圾文件清理一下，注意辨别并询问我清理哪些」**
> —— 因此**先只读盘点 → 分类列出 → 由操作者圈定范围（A–E、H–I）→ 才逐项执行**，并保留完整记录。
> （Qwen 因 32 GB 装不下 7B 尚未开跑，清理提前完成。）
>
> ### 一、✅ 操作者批准的清理（实际执行）
>
> | 类 | 内容 | 释放 |
> |---|---|---|
> | **A** | `%TEMP%` 非 DSH 临时项（**跳过** `dsh-workspace-changes-*`：被占用、WinError 5）| 0.73 GB |
> | **B** | `coco/`（18.84 GB）、`flickr30k/`（8.27 GB）—— **公开数据集，可重下** | 27.11 GB |
> | **D** | `outputs/*.pt` —— **11 个微调权重**（文档未引用：HANDOFF/文件地图/docs 全查无）| 6.33 GB |
> | **E** | `cloud_fixture/`、`outputs/_cloud_data.zip`、`outputs/_cloud_layout`、`outputs/llava_parity_localdet`（4.48 GB）、`.worktrees`（经 `git worktree prune` 后删）、UATD 三个 zip（解压副本 18,400 文件仍在）| 9.6 GB |
> | **H** | `~/.cache/huggingface/datasets`（可重下）| 33.35 GB |
> | **I** | `~/.cache/modelscope/hub`（可重下）| 6.62 GB |
>
> ### 二、🚫 **按守卫保留 / 按指令不动**
>
> | 项 | 原因 |
> |---|---|
> | `backups/snapshot_FULL_20260930.zip`（**13.75 GB**）| ⚠️ **守卫拦下**：它是**唯一一份全量快照**，删了项目就**没有任何备份** ⇒ 我**没有删**（宁可少释放 13.7 GB）|
> | `~/.cache/huggingface/hub`（**15.09 GB**）| 操作者明确 **F 不删**（含本地 LLaVA 权重）|
> | `models/`（**40.76 GB**）| 本地跑实验所必需 |
> | `outputs/analysis/`（**15.78 GB，434 个 JSON**）| **所有论文数字的来源，绝不能删** |
> | `outputs/llava_bf16_sites_cloud/`（773 MB）| 今天成果 + **7 个 `.pt` 适配器** |
> | `UATD_OpenSLT.zip`（76 MB）| 在 `UATD/data/` 下**无对应解压目录** ⇒ 可能是唯一副本，**未删** |
> | `~/.cache/codex-runtimes`、`huggingface/modules` | DSH 运行时，不动 |
>
> ### 三、✅ 清理后完整性核对（实测）
>
> | 检查 | 结果 |
> |---|---|
> | **git 被跟踪且被删** | **0**（coco/flickr30k 本就被 `.gitignore` 排除，属未跟踪）|
> | `outputs/analysis` JSON | **434 个完好** |
> | LLaVA 适配器 | **7 个完好**（773 MB 目录）|
> | `models/`、`tools/`、`SUBMISSION/`、`paper合/`、`paper3/`、`docs/`、`.git/` | 全部在位 |
> | `tools/_claim_ledger.py` | 在位 |
>
> ### 四、⚠️ 需要重下的东西（如日后要本地重跑）
>
> `coco/`（18.8 GB）、`flickr30k/`（8.3 GB）、HF 数据集缓存、ModelScope 缓存；
> `exp/` 的实验本就在云端跑，`SUBMISSION/cloud_p3_setup.sh` 会**在服务器端**重新下载数据与依赖。
>
> **脚本**：`tools/_p1047_cleanup.py`（A–E，含三处守卫）｜`tools/_p1048_cleanup_caches.py`（H–I）｜
> **记录**：`docs/cleanup_2026-10-16.md`、`docs/cleanup_2026-10-16_caches.md`｜`tools/_p1049`（本条）。
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
    mp = io.open(REPO / "文件地图.md", encoding="utf-8").read()
    row = ("43. 🧹 **磁盘清理（2026-10-16 19:20）** —— 先只读盘点 → 操作者圈定 A–E/H–I → 逐项执行，**共释放约 83 GB**"
           "（**C 52.4 → 93.8 GB**、**D 82.7 → 125.7 GB**）。删：coco/flickr30k（27.1 GB，可重下）、`outputs/*.pt` 11 个微调权重（6.3 GB，"
           "文档全查无）、HF datasets 缓存（33.35 GB）+ ModelScope 缓存（6.6 GB）、cloud_fixture/_cloud_data/_cloud_layout/llava_parity_localdet/.worktrees、"
           "UATD 三个 zip（解压副本 18,400 文件仍在）、%TEMP% 非 DSH 项。**守卫保留**：`backups/snapshot_FULL_20260930.zip`（**唯一全量快照，13.75 GB，未删**）、"
           "`~/.cache/huggingface/hub`（F 不删）、`models/`、**`outputs/analysis`（434 JSON，论文数字来源）**、7 个 LLaVA 适配器、`UATD_OpenSLT.zip`（无解压副本）。"
           "**核对**：git 被跟踪且被删 = **0**。记录 `docs/cleanup_2026-10-16*.md`。详见 `HANDOFF.md` 顶部 19:20 条目。\n")
    anchor = "42. 🔌 **校验通过后已关机（2026-10-16 18:45）**"
    idx = mp.find(anchor)
    if idx >= 0:
        end = mp.find("\n", idx)
        mp = mp[: end + 1] + row + mp[end + 1:]
        io.open(REPO / "文件地图.md", "w", encoding="utf-8", newline="").write(mp)
        print("  map item added")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
