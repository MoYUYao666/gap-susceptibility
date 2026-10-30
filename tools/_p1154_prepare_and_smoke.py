# -*- coding: utf-8 -*-
r"""Prepare the host for the corrected Qwen2-VL-2B sweep and run a one-seed smoke test.

Three things:

1. `/root/p3/src/` is not present on this host (the persistent disk holds outputs and models, not the repo), while
   `tools/_p1150_qwen_clean_sweep.py` imports `src.dataset.create_dataloaders`. Upload the minimal source it needs.
2. The second Qwen2-VL-2B shard stalled at 0.0 MB/s; restart its fetch (resumes from `.parts`).
3. Run the sweep with `--arms text_only --seed 42 --maxsamples 16 --epochs 1` first, so a bad caption-span mask or
   a hook failure is caught in two minutes rather than after an hour of the full run.

    python tools/_p1154_prepare_and_smoke.py [--apply]
"""
from __future__ import annotations

import argparse
import os
import sys

import paramiko

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOST = os.environ.get("P3SSH_HOST", "")
PORT = int(os.environ.get("P3SSH_PORT", "22"))
PASS = os.environ.get("P3SSH_PASS", "")

UPLOADS = [
    ("src/dataset.py", "/root/p3/src/dataset.py"),
    ("src/__init__.py", "/root/p3/src/__init__.py"),
    ("tools/_p1150_qwen_clean_sweep.py", "/root/p3/tools/_p1150_qwen_clean_sweep.py"),
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

    def sh(cmd: str, timeout: int = 300) -> str:
        _i, o, e = cli.exec_command(cmd, timeout=timeout)
        try:
            return (o.read() + e.read()).decode("utf-8", "replace").strip()
        except Exception:
            return "(channel stayed open)"

    sh("mkdir -p /root/p3/src")
    sftp = cli.open_sftp()
    for local, remote in UPLOADS:
        lp = os.path.join(REPO, local)
        if not os.path.exists(lp):
            print(f"  !! missing local file {local}")
            continue
        sftp.put(lp, remote)
        print(f"  uploaded {local} -> {remote} ({os.path.getsize(lp)} bytes)")
    sftp.close()

    print("  === restart the stalled shard 2 fetch ===")
    print("  " + sh("pkill -9 -f _p1101_parallel_fetch_any || true; sleep 1; "
                    "cd /root/p3 && ( setsid /root/miniconda3/bin/python tools/_p1101_parallel_fetch_any.py "
                    "--base https://hf-mirror.com/Qwen/Qwen2-VL-2B-Instruct/resolve/main/{f} "
                    "--files model-00002-of-00002.safetensors --sizes 0 "
                    "--dest /root/autodl-tmp/hf/hub/models--Qwen--Qwen2-VL-2B-Instruct/snapshots/main "
                    "> /root/p3/qwen2b_shard2.log 2>&1 < /dev/null & ) ; sleep 2; echo relaunched"))
    import time
    time.sleep(50)
    print("  " + sh("tail -2 /root/p3/qwen2b_shard2.log | tr -d '\\r'"))

    print("\n  === smoke: text_only, seed 42, 16 samples, 1 epoch ===")
    smoke = ("cd /root/p3 && export HF_HOME=/root/autodl-tmp/hf HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 "
             "PYTORCH_ALLOC_CONF=expandable_segments:True PYTHONIOENCODING=utf-8 && "
             "timeout 900 /root/miniconda3/bin/python -u -X utf8 tools/_p1150_qwen_clean_sweep.py --apply "
             "--arms text_only --seed 42 --maxsamples 16 --epochs 1 --batch 2 "
             "--outdir outputs/vlm_clean_smoke 2>&1 | grep -avE 'Loading weights' | tail -20")
    print(sh(smoke, timeout=1000))
    cli.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
