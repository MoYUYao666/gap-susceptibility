# -*- coding: utf-8 -*-
r"""Upload the seven LoRA adapters to the new host and report the weight-download progress.

The adapters are the only input the recomputation needs besides the base weights, and they were pulled back to
the laptop on 2026-10-16 (773 MB), so they go up as-is. Sizes are verified after transfer.

    python tools/_p1104_upload_adapters.py [--apply]
"""
from __future__ import annotations

import argparse
import glob
import os
import sys

import paramiko

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOST = os.environ.get("P3SSH_HOST", "")
PORT = int(os.environ.get("P3SSH_PORT", "22"))
PASS = os.environ.get("P3SSH_PASS", "")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  (dry run)")
        return 0
    if not (HOST and PASS):
        print("  P3SSH_HOST / P3SSH_PASS are not set")
        return 2
    cli = paramiko.SSHClient()
    cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    cli.connect(HOST, port=PORT, username="root", password=PASS, timeout=30,
                allow_agent=False, look_for_keys=False)
    sftp = cli.open_sftp()
    files = sorted(glob.glob(os.path.join(REPO, "outputs", "llava_bf16_sites_cloud", "*.pt")))
    print(f"  {len(files)} adapters, {sum(os.path.getsize(f) for f in files)/1e6:.1f} MB")
    total = 0
    for f in files:
        base = os.path.basename(f)
        remote = f"/root/p3/adapters/{base}"
        sftp.put(f, remote)
        rs = sftp.stat(remote).st_size
        ls = os.path.getsize(f)
        ok = rs == ls
        print(f"  {'OK ' if ok else 'BAD'} {base:<28} {ls:>12,} -> {rs:>12,}")
        total += ok
    sftp.close()

    def sh(cmd: str, timeout: int = 120) -> str:
        _i, o, e = cli.exec_command(cmd, timeout=timeout)
        return (o.read().decode("utf-8", "replace") + e.read().decode("utf-8", "replace")).strip()

    print(f"  adapters verified: {total}/{len(files)}")
    print("=== weight download progress ===")
    print(sh("tail -4 /root/p3/mirror_mt.log 2>/dev/null | tr -d '\\r'; du -sh /root/autodl-tmp/hf 2>/dev/null"))
    cli.close()
    return 0 if total == len(files) else 1


if __name__ == "__main__":
    sys.exit(main())
