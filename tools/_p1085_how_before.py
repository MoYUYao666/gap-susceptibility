# -*- coding: utf-8 -*-
r"""Report how the earlier hosts obtained the weights, and what the current host is doing.

The operator asked "之前怎么弄的" -- how was this done before. The answer has to come from the surviving record
rather than memory: the earlier hosts' setup scripts and logs are in this repository, and the current host's
state is one probe away.

    python tools/_p1085_how_before.py
"""
from __future__ import annotations

import io
import os
import re
import sys
from pathlib import Path

import paramiko

REPO = Path(__file__).resolve().parents[1]
HOST = os.environ.get("P3SSH_HOST", "")
PORT = int(os.environ.get("P3SSH_PORT", "22"))
PASS = os.environ.get("P3SSH_PASS", "")


def main() -> int:
    print("=== how the surviving scripts fetched the weights ===")
    pats = [REPO / "SUBMISSION" / "cloud_p3_setup.sh"] + sorted(REPO.glob("tools/_p106*.sh")) + \
           sorted(REPO.glob("tools/_p96*.py")) + sorted(REPO.glob("tools/_p97*.py")) + \
           sorted(REPO.glob("tools/_p98*.py")) + sorted(REPO.glob("tools/_p99*.py"))
    for f in pats:
        if not f.exists():
            continue
        try:
            text = io.open(f, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        hits = [l.strip() for l in text.splitlines()
                if re.search(r"snapshot_download|HF_ENDPOINT|huggingface|modelscope|HF_HOME", l)]
        if hits:
            print(f"  {f.relative_to(REPO)}:")
            for l in hits[:5]:
                print(f"     {l[:120]}")

    print("\n=== what the earlier hosts actually cached (from the session record) ===")
    print("  host 2 (bjb2) and host 3 (bjb3): /root/autodl-tmp/hf/hub/models--llava-hf--llava-1.5-7b-hf")
    print("  i.e. the weights came through the HuggingFace client with HF_ENDPOINT=https://hf-mirror.com")
    print("  host 3's setup note: '15 GB model, about 6-8 minutes' on that host's link")
    print("  host 3 also carried /root/.cache/modelscope/hub (6.62 GB) -- used for other models")

    if not (HOST and PASS):
        print("\n  (no host credentials; live state skipped)")
        return 0

    cli = paramiko.SSHClient()
    cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    cli.connect(HOST, port=PORT, username="root", password=PASS, timeout=30,
                allow_agent=False, look_for_keys=False)

    def sh(cmd: str, timeout: int = 120) -> str:
        _i, o, e = cli.exec_command(cmd, timeout=timeout)
        return (o.read().decode("utf-8", "replace") + e.read().decode("utf-8", "replace")).strip()

    print("\n=== live state of the current host ===")
    print(sh("ps -eo pid,etimes,cmd | grep -E '_p1082|_p1083|snapshot_download|curl' | grep -v grep | head -6 || echo 'nothing running'"))
    print(sh("tail -6 /root/p3/mtdl.log 2>/dev/null | tr -d '\\r' || echo 'no mtdl.log'"))
    print(sh("du -sh /root/autodl-tmp/modelscope 2>/dev/null; ls /root/autodl-tmp/modelscope/hub/llava-hf/llava-1.5-7b-hf 2>/dev/null | head"))
    print(sh("df -h /root/autodl-tmp | tail -1"))
    cli.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
