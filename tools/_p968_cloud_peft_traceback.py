# -*- coding: utf-8 -*-
r"""Get the real traceback for the cloud's `import peft` failure.

The cloud has peft 0.20.0 and transformers 5.16.1, the same pair as the machine that produced the local
baseline, yet `import peft` fails with "Could not import module 'BloomPreTrainedModel'". Version numbers
agreeing is not the same as the import working, so this prints the full traceback.

    python tools/_p968_cloud_peft_traceback.py
"""
from __future__ import annotations

import os
import sys

import paramiko

HOST = os.environ.get("P3SSH_HOST", "")
PORT = int(os.environ.get("P3SSH_PORT", "22"))
PASS = os.environ.get("P3SSH_PASS", "")

PROBE = r""" /root/miniconda3/bin/python - <<'EOF'
import traceback, sys
print("python", sys.version.split()[0])
print("executable", sys.executable)
try:
    import peft
    print("peft OK", peft.__version__, peft.__file__)
except Exception:
    traceback.print_exc()
print("---- transformers probe ----")
try:
    import transformers
    print("transformers", transformers.__version__, transformers.__file__)
    from transformers import BloomPreTrainedModel
    print("BloomPreTrainedModel OK")
except Exception:
    traceback.print_exc()
print("---- peft metadata ----")
try:
    import importlib.metadata as md
    for r in md.requires("peft") or []:
        print("  requires:", r)
except Exception:
    traceback.print_exc()
EOF"""


def main() -> int:
    if not (HOST and PASS):
        print("  P3SSH_HOST / P3SSH_PASS are not set")
        return 2
    cli = paramiko.SSHClient()
    cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    cli.connect(HOST, port=PORT, username="root", password=PASS, timeout=30,
                allow_agent=False, look_for_keys=False)
    _i, o, e = cli.exec_command(PROBE, timeout=180)
    text = (o.read().decode("utf-8", "replace") + e.read().decode("utf-8", "replace")).strip()
    print(text)
    cli.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
