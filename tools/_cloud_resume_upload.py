# -*- coding: utf-8 -*-
r"""云端：**可断点续传**的上传权重（2026-10-09）。

## 为什么要续传

前次上传在 **343 MB / 577 MB** 处中断（会话被切断）→ 需从中断处继续，
而不是重传 577 MB（每次 ~7.5 min）。

## 做法

1. 远端已有 `.uploading` 的大小 → 决定 `sftp.put` 的起始偏移（paramiko 支持 `fileobj` + seek）；
2. 传完比对总大小 → 才改名覆盖。

    $env:CLOUD_PW='...'; python tools\_cloud_resume_upload.py
"""
from __future__ import annotations

import io
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))
WORK = "/root/autodl-tmp/work"

JOBS = [
    ("models/clip-vit-base-patch32/pytorch_model.bin",
     f"{WORK}/models/clip-vit-base-patch32/pytorch_model.bin"),
    ("models/clip-vit-base-patch16/pytorch_model.bin",
     f"{WORK}/models/clip-vit-base-patch16/pytorch_model.bin"),
]


def main() -> int:
    from _cloud_ssh import client

    c = client()
    try:
        sftp = c.open_sftp()
        for local_rel, remote in JOBS:
            p = REPO / local_rel
            if not p.exists():
                print(f"  ❌ 本地缺 {local_rel}")
                continue
            total = p.stat().st_size
            tmp = remote + ".uploading"
            try:
                have = sftp.stat(tmp).st_size
            except IOError:
                have = 0
            if have >= total:
                print(f"  · {Path(remote).name} 已传完（{have} B），改名")
                try:
                    sftp.remove(remote)
                except IOError:
                    pass
                sftp.rename(tmp, remote)
                continue
            print(f"\n=== {Path(remote).name}：从 {have/2**20:.0f} MB 续传 "
                  f"（共 {total/2**20:.0f} MB）", flush=True)
            t0 = time.time()
            last = [0.0]

            def cb(done, tot, base=have):
                now = time.time()
                if now - last[0] < 10:
                    return
                last[0] = now
                el = now - t0
                done_abs = base + done
                rate = done / max(el, 1e-6) / 2**20
                eta = (tot - done) / max(done / max(el, 1e-6), 1e-6)
                print(f"    {100*done_abs/max(total,1):5.1f}%  "
                      f"{done_abs/2**20:6.1f}/{total/2**20:.0f} MB  "
                      f"{rate:.2f} MB/s  ETA {eta/60:.1f} min", flush=True)

            if have > 0:
                # 续传：先取回已有部分（paramiko 无远端 seek put，故用 prefetch）
                # 简化：用 sftp.open(tmp,'r+') 定位写（paramiko 支持 r+ 模式 + seek）
                with io.open(p, "rb") as lf:
                    lf.seek(have)
                    with sftp.open(tmp, "r+") as rf:
                        rf.seek(have)
                        rf.set_pipelined(True)
                        buf = 1024 * 1024
                        sent = have
                        while True:
                            chunk = lf.read(buf)
                            if not chunk:
                                break
                            rf.write(chunk)
                            sent += len(chunk)
                            if time.time() - last[0] > 10:
                                last[0] = time.time()
                                el = time.time() - t0
                                rate = (sent - have) / max(el, 1e-6) / 2**20
                                eta = (total - sent) / max(
                                    (sent - have) / max(el, 1e-6), 1e-6)
                                print(f"    {100*sent/total:5.1f}%  "
                                      f"{sent/2**20:6.1f}/{total/2**20:.0f} MB  "
                                      f"{rate:.2f} MB/s  ETA {eta/60:.1f} min",
                                      flush=True)
            else:
                sftp.put(str(p), tmp, callback=cb)

            sz = sftp.stat(tmp).st_size
            print(f"  远端 {sz} B ｜ 本地 {total} B")
            if sz == total:
                try:
                    sftp.remove(remote)
                except IOError:
                    pass
                sftp.rename(tmp, remote)
                print("  ✅ 校验一致，已改名覆盖")
            else:
                print("  ⚠️ 大小不符，保留 .uploading")
        sftp.close()
    finally:
        c.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
