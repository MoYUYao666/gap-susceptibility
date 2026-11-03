# -*- coding: utf-8 -*-
r"""Restart the two still-needed downloads and launch the LLaVA clean re-measurement.

The data disk turned out to be persistent across instances: `/root/autodl-tmp/hf` already held the complete
LLaVA-1.5-7B weights (14 GB, timestamps from the morning host) and `/root/p3/outputs/llava_canonical/` still held
the nine adapters and twelve records. A blanket `pkill -f _p1101_parallel_fetch_any` intended to stop a redundant
LLaVA re-download also stopped the Flickr30k and Qwen2-VL-2B fetches; both resume from their `.parts` directories,
so nothing is lost.

Meanwhile the GPU is idle and the LLaVA adapters are local, so the clean gap measurement
(`tools/_p1145_clean_gap_measure.py`) can start immediately.

    python tools/_p1151_restart_and_launch.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import os
import sys
import time

import paramiko

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOST = os.environ.get("P3SSH_HOST", "")
PORT = int(os.environ.get("P3SSH_PORT", "22"))
PASS = os.environ.get("P3SSH_PASS", "")

FETCH = "/root/p3/tools/_p1101_parallel_fetch_any.py"
JOBS = [
    # (label, base url template, files, sizes, dest, log)
    ("qwen2b",
     "https://hf-mirror.com/Qwen/Qwen2-VL-2B-Instruct/resolve/main/{f}",
     "model-00001-of-00002.safetensors,model-00002-of-00002.safetensors",
     "0,0",
     "/root/autodl-tmp/hf/hub/models--Qwen--Qwen2-VL-2B-Instruct/snapshots/main",
     "/root/p3/qwen2b_dl.log"),
    ("flickr",
     "https://hf-mirror.com/datasets/nlphuji/flickr30k/resolve/main/{f}",
     "flickr30k-images.zip", "4390240817", "/root/p3/data/flickr", "/root/p3/flickr_dl.log"),
]


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

    def sh(cmd: str, timeout: int = 200) -> str:
        """Run a command; a launched background job can hold the channel open, so a read timeout is not an error."""
        _i, o, e = cli.exec_command(cmd, timeout=timeout)
        try:
            return (o.read() + e.read()).decode("utf-8", "replace").strip()
        except Exception:
            return "(channel stayed open -- the background job is running)"

    sftp = cli.open_sftp()
    local = os.path.join(REPO, "tools", "_p1145_clean_gap_measure.py")
    sftp.put(local, "/root/p3/tools/_p1145_clean_gap_measure.py")
    sftp.close()
    print("  uploaded _p1145_clean_gap_measure.py")

    # resume the two downloads, one at a time so they share the link rather than starving each other
    for label, base, files, sizes, dest, log in JOBS:
        done = sh(f"grep -c 'OK' {log} 2>/dev/null || echo 0")
        print(f"  {label}: completed files so far = {done}")
        if done.strip() != "0" and label == "qwen2b":
            print(f"  {label}: already assembled, skipping")
            continue
        cmd = (f"cd /root/p3 && ( setsid /root/miniconda3/bin/python {FETCH} "
               f"--base '{base}' --files '{files}' --sizes '{sizes}' --dest '{dest}' "
               f"> {log} 2>&1 < /dev/null & ) ; sleep 2; echo relaunched")
        print("  " + sh(cmd))
    time.sleep(5)

    print("  === launching the LLaVA clean measurement ===")
    launch = ("cd /root/p3 && export HF_HOME=/root/autodl-tmp/hf HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 "
              "PYTORCH_ALLOC_CONF=expandable_segments:True PYTHONIOENCODING=utf-8 && "
              "( setsid /root/miniconda3/bin/python -u -X utf8 tools/_p1145_clean_gap_measure.py "
              "--out /root/p3/outputs/canonical_caption_metric.json > /root/p3/clean_measure.log 2>&1 "
              "< /dev/null & ) ; sleep 3; echo launched")
    print("  " + sh(launch))

    print("\n  === status after launch ===")
    for name, cmd in (("qwen2b", "tail -1 /root/p3/qwen2b_dl.log | tr -d '\\r'"),
                      ("flickr", "tail -1 /root/p3/flickr_dl.log | tr -d '\\r'"),
                      ("measure", "grep -avE 'Loading weights' /root/p3/clean_measure.log 2>/dev/null | tail -3"),
                      ("gpu", "nvidia-smi --query-gpu=memory.used --format=csv,noheader")):
        print(f"  {name:<9} {sh(cmd)}")
    cli.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
