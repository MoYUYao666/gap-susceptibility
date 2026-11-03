# -*- coding: utf-8 -*-
r"""把 backups/ 里的历史记录移出，使它们能进入新快照；并清理旧快照的元数据。

## 为什么必须先移出

`tools/_make_backup_snapshot.py` 第 43 行把 **`backups/` 整体排除**（防止备份套娃）。
因此 **`backups/` 里的任何东西都不会进入新 zip**。若直接跑新备份再删旧备份，
下列两项历史记录会**从归档中静默消失**：

| 文件 | 价值 |
|---|---|
| `_push_run_20260924.log` | 2026-09-24 GitHub 推送全过程（597 行），含"移出权重类 20 个 / 稿件类 403 个"等决策依据 |
| `_deleted_old_backups_20260924.txt` | 2026-09-24 旧备份删除台账（cloud_upload.zip、cloud_upload、备选/03_检查与备份产物） |

→ 移入 `tools/obsolete/_backups_legacy_20260924/`，**新快照即可包含它们**。

## 另处理

旧快照的 `.sha256` / `.manifest.txt`（小文本，记录上次备份的指纹与 13882 条目清单）
在旧 zip 删除后失去对照对象，但**体积极小且能证明"上次备份曾存在且校验通过"**，
一并移入同一目录留档。

    python tools/_relocate_backup_legacy.py [--apply]
"""
from __future__ import annotations

import io
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
BAK = REPO / "backups"
DEST = REPO / "tools" / "obsolete" / "_backups_legacy_20260924"

MOVE = [
    "_push_run_20260924.log",
    "_deleted_old_backups_20260924.txt",
    "snapshot_FULL_20260924.zip.sha256",
    "snapshot_FULL_20260924.zip.manifest.txt",
]

README = """# backups/ 历史记录（2026-09-24 那一代）

从 `backups/` 移出，**原因**：`tools/_make_backup_snapshot.py` 把 `backups/` 整体排除
（防备份套娃），所以留在那里的文件**不会进入任何新快照**。移到这里即可被归档。

| 文件 | 内容 | 为何留档 |
|---|---|---|
| `_push_run_20260924.log` | 2026-09-24 GitHub 推送全过程，597 行 | 含"保留 1384 / 移出权重 20 / 移出稿件 403"等发布边界决策依据 |
| `_deleted_old_backups_20260924.txt` | 2026-09-24 旧备份删除台账 | 记录被删的 `cloud_upload.zip`、`cloud_upload`、`备选/03_检查与备份产物` |
| `snapshot_FULL_20260924.zip.sha256` | 上一代快照的 SHA256 | 旧 zip 于 2026-09-30 删除后仍可证明"曾存在且校验通过" |
| `snapshot_FULL_20260924.zip.manifest.txt` | 上一代快照的 13882 条目清单（1 MB） | 同上；也是当时"备份里到底有什么"的唯一凭据 |

> 说明：2026-09-24 快照 zip 本体（14.07 GB）已于 **2026-09-30** 按操作者指示删除，
> 删除前新快照 `snapshot_FULL_20260930.zip` 已通过校验（见 `HANDOFF.md` 2026-09-30 条目）。
"""


def main() -> int:
    apply = "--apply" in sys.argv
    if not BAK.exists():
        raise SystemExit("❌ backups/ 不存在")
    moved = []
    for name in MOVE:
        src = BAK / name
        if src.exists():
            print(f"  {name}  ({src.stat().st_size:,} B)  →  {DEST.relative_to(REPO)}/")
            moved.append(name)
            if apply:
                DEST.mkdir(parents=True, exist_ok=True)
                shutil.move(str(src), str(DEST / name))
        else:
            print(f"  跳过（不存在）：{name}")
    if apply:
        (DEST / "README.md").write_text(README, encoding="utf-8")
        print(f"\n✅ 已移动 {len(moved)} 项 + 写入 README")
    else:
        print(f"\n（预演：将移动 {len(moved)} 项；加 --apply 生效）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
