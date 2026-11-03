# -*- coding: utf-8 -*-
r"""Restore the exact sweep that produced the LLaVA results, from the frozen copy on the host.

Why: the model-selection and prompt patches (`_p1019`) changed LLaVA's behaviour. A five-step deterministic
run of the patched script gave loss **4.3099** where the frozen record for the identical configuration
(`samples 20`, `epochs 1`, `batch 2`, `n_eval 10`, seed 42, text_only) gives **2.9496**. The cause is that
transformers 5.16.1 ships a chat template for the LLaVA processor, so building prompts through
`apply_chat_template` produced a different prompt string from the one the published numbers came from.

The correct response is to restore the validated script rather than patch it further, and to give Qwen its own
runner. The host holds a byte-exact copy of the pre-patch script inside the freeze directory, which is copied
back here and verified by parsing it and checking that the patch markers are absent.

    python tools/_p1031_restore_sweep.py [--apply]
"""
from __future__ import annotations

import argparse
import os
import shutil
import sys

import paramiko

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCAL = os.path.join(REPO, "tools", "_p820_llava_sites.py")
BACKUP = os.path.join(REPO, "tools", "_p820_llava_sites.patched.bak")
HOST = os.environ.get("P3SSH_HOST", "")
PORT = int(os.environ.get("P3SSH_PORT", "22"))
PASS = os.environ.get("P3SSH_PASS", "")
STAMP = "frozen_llava_1016"


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
    # find the freeze directory (the timestamp suffix is not known here)
    dirs = [d for d in sftp.listdir("/root/p3") if d.startswith("frozen_llava_")]
    print(f"  freeze directories on the host: {dirs}")
    assert dirs, "no frozen copy found on the host"
    remote = f"/root/p3/{sorted(dirs)[-1]}/_p820_llava_sites.py"
    tmp = LOCAL + ".fromcloud"
    sftp.get(remote, tmp)
    sftp.close()
    cli.close()

    text = open(tmp, encoding="utf-8").read()
    print(f"  fetched {remote} ({len(text)} bytes)")
    # prove it is the pre-patch version
    for marker in ("--model", "apply_chat_template", "_load_vlm", "_arm_guard"):
        print(f"    contains {marker!r}: {marker in text}")
    assert "--model" not in text and "apply_chat_template" not in text, \
        "the fetched copy is not the pre-patch script"

    shutil.copy2(LOCAL, BACKUP)
    print(f"  kept the patched version at {os.path.basename(BACKUP)}")
    shutil.move(tmp, LOCAL)
    import ast
    ast.parse(open(LOCAL, encoding="utf-8").read())
    print("  restored script parses")
    for flag in ("--precision", "--eval-batch", "--alloc-warmup-gb", "--tf32", "--no-grad-ckpt",
                 "release_between_runs", "ARM_FAILURES"):
        print(f"    {flag:<22} {flag in text}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
