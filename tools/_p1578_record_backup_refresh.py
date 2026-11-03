# -*- coding: utf-8 -*-
"""Record the 2026-10-24 backup refresh (new snapshot created, old snapshot deleted)."""
import io
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(REPO)

entry = """> **💾 2026-10-24 14:10 —— 新全量备份已出，旧备份已删**
>
> - **新快照**：`backups/snapshot_FULL_20261024_after_v23`，**4.71 GB**（原始 5.10 GB / 20,191 文件，压缩比 92.2%），
>   用时 288 s；sha256 `a402ab2e56b442269d04c41b44d8424a11e031d021d61f89f83a22fffe855c72`；
>   复核：`.sha256` 一致、manifest `files=20191` = zip 条目 **20191**、`zipfile.testzip()` 无损坏；
> - **删除的旧快照**：`snapshot_FULL_20261017_after_cleanup`（4.35 GB，sha256 `07f8e3f8208ba6dca71814f0bfc8582bb2308c1361f69e003a6784969519d26b`）
>   及其 `.manifest.txt`、`.sha256`（删除前已核对绝对路径均在 `backups/` 内且名称匹配）；
> - 备份范围：含 `outputs/`、`SUBMISSION/`、`.git/`，排除 `data`/`models`/`coco`/`flickr30k`/`backups/` 与既有 zip；
> - 当前 `backups/` 只保留这一份最新快照（约 4.72 GB）。
>
"""

h = io.open("HANDOFF.md", encoding="utf-8").read()
if "新全量备份已出，旧备份已删" not in h:
    i = h.find("# 项目交接文档")
    j = h.find("\n", i)
    h = h[:j + 1] + "\n" + entry + h[j + 1:]
    io.open("HANDOFF.md", "w", encoding="utf-8", newline="").write(h)
    print("handoff updated")

m = io.open("文件地图.md", encoding="utf-8").read()
old = "| `backups/` | 最新全量快照 `snapshot_FULL_20261017_after_cleanup`（4.25 GB，校验通过）| 旧快照已由新快照取代 |"
new = ("| `backups/` | 最新全量快照 `snapshot_FULL_20261024_after_v23`（4.71 GB，20,191 文件，sha256 校验通过）| "
       "**当前只保留这一份**（2026-10-24 操作者要求删除旧快照 `snapshot_FULL_20261017_after_cleanup`）|")
if old in m:
    m = m.replace(old, new, 1)
    io.open("文件地图.md", "w", encoding="utf-8", newline="").write(m)
    print("map backups row updated")
else:
    print("note: backups row pattern not found")

row = ("157. 💾 **2026-10-24 14:10 —— 备份刷新**：新快照 `snapshot_FULL_20261024_after_v23`（4.71 GB / 20,191 文件 / "
       "sha256 a402ab2e…）；旧快照 `snapshot_FULL_20261017_after_cleanup` 已删。\n")
if "备份刷新" not in m:
    i = m.find("156. 🔧 **2026-10-24 14:05")
    e = m.find("\n", i)
    m = io.open("文件地图.md", encoding="utf-8").read()
    m = m[:e + 1] + row + m[e + 1:]
    io.open("文件地图.md", "w", encoding="utf-8", newline="").write(m)
    print("map entry added")
print("done")