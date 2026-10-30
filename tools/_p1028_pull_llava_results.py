# -*- coding: utf-8 -*-
r"""Pull the finished LLaVA run back to the laptop: records, trained adapters, log and script.

Operator instruction 2026-10-16: "注意先保存所有结果包括pt模型". The adapters on the host are ~774 MB in total,
and the run that produced them is frozen there as well; this copies them into `outputs/llava_bf16_sites_cloud/`
so the results survive the host being released, and verifies every file arrived with the same size.

    python tools/_p1028_pull_llava_results.py [--apply]
"""
from __future__ import annotations

import argparse
import os
import sys

import paramiko

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCAL = os.path.join(REPO, "outputs", "llava_bf16_sites_cloud")
HOST = os.environ.get("P3SSH_HOST", "")
PORT = int(os.environ.get("P3SSH_PORT", "22"))
PASS = os.environ.get("P3SSH_PASS", "")
REMOTE = "/root/p3/outputs/llava_bf16_sites"
EXTRA = [("/root/p3/sweep_run.log", "sweep_run.log"),
         ("/root/p3/outputs/analysis/llava_sites.json", "llava_sites.json")]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not (HOST and PASS):
        print("  P3SSH_HOST / P3SSH_PASS are not set")
        return 2
    if not a.apply:
        print(f"  would pull {REMOTE} -> {LOCAL}")
        return 0

    os.makedirs(LOCAL, exist_ok=True)
    cli = paramiko.SSHClient()
    cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    cli.connect(HOST, port=PORT, username="root", password=PASS, timeout=30,
                allow_agent=False, look_for_keys=False)
    sftp = cli.open_sftp()

    names = sftp.listdir(REMOTE)
    ok = bad = 0
    for name in sorted(names):
        if not name.endswith((".json", ".pt")):
            continue
        rpath = f"{REMOTE}/{name}"
        lpath = os.path.join(LOCAL, name)
        rsize = sftp.stat(rpath).st_size
        sftp.get(rpath, lpath)
        lsize = os.path.getsize(lpath)
        same = rsize == lsize
        ok += same
        bad += not same
        print(f"  {'OK ' if same else 'BAD'} {name:<28} {rsize:>12,} -> {lsize:>12,}")

    for rpath, lname in EXTRA:
        lpath = os.path.join(LOCAL, lname)
        try:
            sftp.get(rpath, lpath)
            print(f"  OK  {lname:<28} {os.path.getsize(lpath):>12,}")
            ok += 1
        except IOError as exc:
            print(f"  --  {lname} not fetched: {exc}")
    sftp.close()
    cli.close()

    print(f"\n  files verified identical: {ok}, mismatched: {bad}")
    print(f"  local directory: {LOCAL}")
    total = sum(os.path.getsize(os.path.join(LOCAL, f)) for f in os.listdir(LOCAL))
    print(f"  local total: {total / 1e6:.1f} MB")
    pt = [f for f in os.listdir(LOCAL) if f.endswith(".pt")]
    print(f"  adapters kept: {len(pt)} -> {sorted(pt)}")
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
