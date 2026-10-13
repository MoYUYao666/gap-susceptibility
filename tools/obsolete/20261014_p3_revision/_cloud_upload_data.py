# -*- coding: utf-8 -*-
r"""云端：上传数据包（138 MB，1000 张图 + results.csv）（2026-10-09）。

**显示进度**（paramiko 的 `put` 有 callback）。

    $env:CLOUD_PW='...'; python tools\_cloud_upload_data.py
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))
WORK = "/root/autodl-tmp/work"


def main() -> int:
    from _cloud_ssh import client

    pkg = REPO / "outputs" / "_cloud_data.zip"
    if not pkg.exists():
        print(f"  ❌ 缺 {pkg}")
        return 1
    total = pkg.stat().st_size
    print(f"=== 上传 {pkg.name} ｜ {total/2**20:.0f} MB ===")

    c = client()
    try:
        sftp = c.open_sftp()
        remote = f"{WORK}/_cloud_data.zip"
        t0 = time.time()
        last = [0.0]

        def cb(done, tot):
            now = time.time()
            if now - last[0] < 5:
                return
            last[0] = now
            pct = 100.0 * done / max(tot, 1)
            el = now - t0
            rate = done / max(el, 1e-6) / 2**20
            eta = (tot - done) / max(done / max(el, 1e-6), 1e-6)
            print(f"  {pct:5.1f}%  {done/2**20:6.1f}/{tot/2**20:.0f} MB  "
                  f"{rate:.2f} MB/s  ETA {eta/60:.1f} min", flush=True)

        sftp.put(str(pkg), remote, callback=cb)
        dt = time.time() - t0
        sz = sftp.stat(remote).st_size
        sftp.close()
        print(f"\n  ✅ 上传完成 {sz/2**20:.0f} MB ｜ {dt:.0f}s ｜ "
              f"{sz/2**20/dt:.2f} MB/s ｜ {'大小一致' if sz == total else '⚠️ 大小不符'}")
    finally:
        c.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
