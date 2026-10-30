# -*- coding: utf-8 -*-
r"""清光旧备份（操作者 2026-09-30 指示："清理所有旧备份"）。

## 背景与一次自我纠正

我先前的做法偏离了指示：删了旧快照 zip，却把旧备份的 `.sha256` / `.manifest.txt`
**留在** `tools/obsolete/_backups_legacy_20260924/`。操作者说的是"**所有**旧备份"，故一并删除。

## 先记录，再删除

删除前把旧备份的可核指纹写入本目录 README，避免凭证彻底消失：
- 原名 `snapshot_20260924_1421.zip`（后由操作者改名为 `snapshot_FULL_20260924.zip`）
- SHA256 `ccf1dbf14d807c4a1cc38f20bfeef3dd14646e30fc36bcf1568501dc2d47a0d8`
- 13882 条目 / 14.80 GB 原始体积 / zip 13.74 GB / 校验通过（2026-09-24）

保留的**非备份**文件（属项目历史，不是备份凭证）：
- `_push_run_20260924.log`（2026-09-24 GitHub 推送全过程 597 行）
- `_deleted_old_backups_20260924.txt`（上一轮旧备份删除台账）

    python tools/_purge_old_backup_credentials.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
LEG = REPO / "tools" / "obsolete" / "_backups_legacy_20260924"

DELETE = [
    "snapshot_FULL_20260924.zip.sha256",
    "snapshot_FULL_20260924.zip.manifest.txt",
]

README = """# 2026-09-24 那一代备份的遗留记录

> 更新：2026-09-30

## 已删除的旧备份（操作者指示"清理所有旧备份"）

| 项 | 值 |
|---|---|
| 文件名（原始） | `snapshot_20260924_1421.zip`（后由操作者改名为 `snapshot_FULL_20260924.zip`） |
| **SHA256** | `ccf1dbf14d807c4a1cc38f20bfeef3dd14646e30fc36bcf1568501dc2d47a0d8` |
| 条目数 | **13882** |
| 原始体积 / zip 体积 | 14.80 GB / **13.74 GB** |
| 校验 | 2026-09-24 建时通过（sha256 一致、条目数与 manifest 一致、`testzip` 无损坏） |
| **删除时间** | **2026-09-30**（新快照校验通过之后） |

**删除顺序（安全闸门）**：先建新快照 → 四步校验通过（SHA256／条目数三方一致／`testzip`／关键内容 8 项）
→ **才**删除旧 zip。校验脚本 `tools/_verify_and_cleanup_backups.py`，任一步失败即拒绝删除。

**同时删除的凭证文件**（本目录内，避免"旧备份"残留）：
`snapshot_FULL_20260924.zip.sha256`、`snapshot_FULL_20260924.zip.manifest.txt`
（内容即上表；删除前已把指纹摘录到本文件）。

## 保留下来的两项（**不是备份凭证**，属项目历史）

| 文件 | 内容 | 为何保留 |
|---|---|---|
| `_push_run_20260924.log` | 2026-09-24 GitHub 推送全过程，597 行 | 含"保留 1384 / 移出权重 20 / 移出稿件 403"等**发布边界决策依据** |
| `_deleted_old_backups_20260924.txt` | 2026-09-24 那轮旧备份删除台账 | 记录被删的 `cloud_upload.zip`、`cloud_upload`、`备选/03_检查与备份产物` |

> 这两项从 `backups/` 移出的原因：`tools/_make_backup_snapshot.py` 把 `backups/` 整体排除（防套娃），
> 留在那里就**不会进入任何快照**。移到这里即可被归档。

## 当前唯一有效备份

`backups/snapshot_FULL_20260930.zip` —— 14050 条目 / 13.74 GB /
SHA256 `b84a701b49cb02e9e05d15bbadf1caeef9b353e909caeae567b0a2cb09d2db32`（2026-09-30 校验通过）。
"""


def main() -> int:
    apply = "--apply" in sys.argv
    if not LEG.exists():
        raise SystemExit(f"❌ 目录不存在：{LEG}")
    n = 0
    for name in DELETE:
        p = LEG / name
        if p.exists():
            print(f"  🗑 {name}  ({p.stat().st_size:,} B)")
            if apply:
                # 目标校验
                assert p.parent.resolve() == LEG.resolve(), "待删文件不在预期目录下"
                assert p.name == name, "文件名与预期不符"
                p.unlink()
            n += 1
        else:
            print(f"  跳过（不存在）：{name}")
    if apply:
        (LEG / "README.md").write_text(README, encoding="utf-8")
        left = sorted(p.name for p in LEG.iterdir())
        print(f"\n✅ 已删 {n} 个旧备份凭证文件；README 已更新（含旧备份 SHA256 摘录）")
        print(f"   本目录现有：{left}")
    else:
        print(f"\n（预演：将删 {n} 个；加 --apply 生效）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
