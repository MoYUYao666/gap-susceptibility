# -*- coding: utf-8 -*-
r"""Delete the seven adapter files that hold no weights, locally and on the host.

Operator instruction 2026-10-17: "删". Safety: every file is opened and checked first -- the deletion only
proceeds for files whose `model` dict is empty, which is the defect signature. Any file that actually carries
tensors is kept and reported. The twelve run records beside them are untouched.

    python tools/_p1131_delete_empty_adapters.py [--apply]
"""
from __future__ import annotations

import argparse
import glob
import os
import sys

import paramiko

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCAL = os.path.join(REPO, "outputs", "llava_bf16_sites_cloud")
HOST = os.environ.get("P3SSH_HOST", "")
PORT = int(os.environ.get("P3SSH_PORT", "22"))
PASS = os.environ.get("P3SSH_PASS", "")

CHECK = r"""
import glob, json, torch
from pathlib import Path
out = []
for f in sorted(glob.glob("/root/p3/adapters/*.pt")):
    obj = torch.load(f, map_location="cpu")
    n = len(obj.get("model", {}) or {})
    out.append({"file": f, "tensors": n, "mb": round(Path(f).stat().st_size / 1e6, 1)})
print(json.dumps(out))
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    import torch  # local check needs torch
    print("=== local adapters ===")
    keep, drop, dropped_mb = [], [], 0.0
    for f in sorted(glob.glob(os.path.join(LOCAL, "*.pt"))):
        obj = torch.load(f, map_location="cpu")
        n = len((obj.get("model", {}) or {}) if isinstance(obj, dict) else {})
        mb = os.path.getsize(f) / 1e6
        print(f"  {os.path.basename(f):<28} {mb:>7.1f} MB  model tensors: {n}")
        if n == 0:
            drop.append(f)
            dropped_mb += mb
        else:
            keep.append(f)
    print(f"  -> empty: {len(drop)} ({dropped_mb:.0f} MB) | carrying tensors: {len(keep)}")
    if keep:
        print("  !! some files carry tensors and will be KEPT:", [os.path.basename(k) for k in keep])

    if not a.apply:
        print("\n  (dry run)")
        return 0

    for f in drop:
        os.remove(f)
    print(f"\n  deleted {len(drop)} local files, {dropped_mb:.0f} MB freed")

    if not (HOST and PASS):
        print("  (no host credentials; remote adapters left in place)")
        return 0

    cli = paramiko.SSHClient()
    cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    cli.connect(HOST, port=PORT, username="root", password=PASS, timeout=30,
                allow_agent=False, look_for_keys=False)

    def sh(cmd: str, timeout: int = 600) -> str:
        _i, o, e = cli.exec_command(cmd, timeout=timeout)
        return (o.read().decode("utf-8", "replace") + e.read().decode("utf-8", "replace")).strip()

    print("\n=== host adapters ===")
    import json as _json
    sftp = cli.open_sftp()
    with sftp.open("/root/p3/_check_adapters.py", "w") as fh:
        fh.write(CHECK)
    sftp.close()
    raw = sh("/root/miniconda3/bin/python /root/p3/_check_adapters.py 2>/dev/null | tail -1")
    try:
        info = _json.loads(raw)
    except Exception:
        print("  could not parse:", raw[:200])
        cli.close()
        return 1
    for it in info:
        print(f"  {os.path.basename(it['file']):<28} {it['mb']:>7.1f} MB  model tensors: {it['tensors']}")
    empty = [it["file"] for it in info if it["tensors"] == 0]
    print(f"  -> empty: {len(empty)} of {len(info)}")
    if empty:
        print("  " + sh("rm -f " + " ".join(empty) + " && ls /root/p3/adapters 2>/dev/null | wc -l"))
        print("  " + sh("du -sh /root/p3/adapters 2>/dev/null || echo 'adapters dir gone'"))
    print("\n  === retrain still running? ===")
    print(sh("ps -eo pid,etimes,cmd | grep _p820_llava_sites | grep -v grep | head -1 || echo none"))
    print(sh("cat /root/p3/outputs/llava_canonical/train_progress.json 2>/dev/null | head -7"))
    cli.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
