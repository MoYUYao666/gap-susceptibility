# -*- coding: utf-8 -*-
r"""Create the workspace on the rented host and upload the fixture bundle.

Layout on the host:

    /root/p3/tools/_p820_llava_sites.py      the sweep (uploaded separately, it is small)
    /root/p3/cloud_fixture/...               700 images, annotations, MANIFEST.json
    /root/p3/parity_local.json                the local baseline losses, for the comparison
    /root/autodl-tmp/hf                        HF cache: the model goes on the 50 GB data disk, not on
                                               the 30 GB root filesystem

Credentials come from the environment only.

    python tools/_p963_cloud_setup.py [--apply]
"""
from __future__ import annotations

import argparse
import os
import posixpath
import sys
import time

import paramiko

HOST = os.environ.get("P3SSH_HOST", "")
PORT = int(os.environ.get("P3SSH_PORT", "22"))
USER = os.environ.get("P3SSH_USER", "root")
PASS = os.environ.get("P3SSH_PASS", "")
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUNDLE = os.path.join(REPO, "cloud_fixture", "p3_llava_cloud.zip")
SWEEP = os.path.join(REPO, "tools", "_p820_llava_sites.py")
REMOTE = "/root/p3"


def run(cli: paramiko.SSHClient, cmd: str, timeout: int = 300) -> str:
    _in, out, err = cli.exec_command(cmd, timeout=timeout)
    text = out.read().decode("utf-8", "replace") + err.read().decode("utf-8", "replace")
    return text.strip()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not (HOST and PASS):
        print("  P3SSH_HOST / P3SSH_PASS are not set")
        return 2
    if not (os.path.exists(BUNDLE) and os.path.exists(SWEEP)):
        print("  bundle or sweep missing locally")
        return 2
    print(f"  bundle {os.path.getsize(BUNDLE) / 1e6:.1f} MB, sweep {os.path.getsize(SWEEP)} bytes")
    if not a.apply:
        print("  (dry run)")
        return 0

    cli = paramiko.SSHClient()
    cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    cli.connect(HOST, port=PORT, username=USER, password=PASS, timeout=30,
                allow_agent=False, look_for_keys=False)
    print("  connected")

    print("  " + run(cli, f"mkdir -p {REMOTE}/tools /root/autodl-tmp/hf && echo dirs-ready"))

    t0 = time.time()
    sftp = cli.open_sftp()
    sftp.put(BUNDLE, f"{REMOTE}/p3_llava_cloud.zip")
    print(f"  uploaded bundle in {time.time() - t0:.0f} s")
    sftp.put(SWEEP, f"{REMOTE}/tools/_p820_llava_sites.py")
    print("  uploaded the sweep")

    # the local baseline, so the comparison does not need the laptop again
    base = {
        "command": "python tools/_p820_llava_sites.py --coco-root cloud_fixture "
                   "--samples 20 --eval-pairs 10 --epochs 1 --batch 2 --max-len 2048 "
                   "--seeds 1 --rank 8 --arms text_only --bench-steps 5 --report-every 5 --apply",
        "losses_at_step": {"5": 2.9466},
        "note": "second local run of the same command gave 2.9449 at step 5 (spread 1.7e-3); "
                "cloud tolerance is 5e-3",
    }
    with sftp.open(f"{REMOTE}/parity_local.json", "w") as fh:
        fh.write(__import__("json").dumps(base, indent=1))
    sftp.close()

    print("  " + run(cli, f"cd {REMOTE} && unzip -q -o p3_llava_cloud.zip && ls -la && "
                          f"ls cloud_fixture | head && du -sh cloud_fixture"))
    print("  " + run(cli, "cat /root/p3/cloud_fixture/MANIFEST.json | head -20"))
    cli.close()
    print("  workspace ready at /root/p3")
    return 0


if __name__ == "__main__":
    sys.exit(main())
