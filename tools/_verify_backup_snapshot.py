# -*- coding: utf-8 -*-
"""校验备份快照完整性（只读）。

    python tools/_verify_backup_snapshot.py [zip 路径]
"""
import sys
import zipfile
import collections
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
zp = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO / "backups" / "snapshot_FULL_20260924.zip"

z = zipfile.ZipFile(zp)
ns = z.namelist()
print("快照:", zp.name)
print("大小: %.2f GB" % (zp.stat().st_size / 1024**3))
print("条目数:", len(ns))
print("CRC 全量校验:", "PASS（无损坏）" if z.testzip() is None else "FAIL（有损坏条目）")
print("含 .git/:", any(n.startswith(".git/") for n in ns))
try:
    print("git master ref:", z.read(".git/refs/heads/master").decode().strip())
except KeyError:
    print("git master ref: 未找到")
c = collections.Counter(n.split("/")[0] for n in ns)
print("目录分布（前 10）:")
for k, v in c.most_common(10):
    print("  %6d  %s" % (v, k))
for d in ("data", "models", "coco", "flickr30k", "backups"):
    n = sum(1 for x in ns if x.split("/")[0] == d)
    flag = "OK（应为 0）" if n == 0 else "⚠ 非预期"
    print("  %-12s 条目 %5d  %s" % (d + "/", n, flag))
