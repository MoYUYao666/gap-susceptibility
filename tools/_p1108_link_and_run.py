# -*- coding: utf-8 -*-
r"""Link the downloaded blobs into the snapshot directory the loader expects, then run the recomputation.

The mirror fetch wrote the three shards into `blobs/` (14 GB, verified sizes) while the small config files went
into `snapshots/main/`. `from_pretrained` resolves the index file's names inside the snapshot directory, so it
looked for `snapshots/main/model-00001-of-00003.safetensors` and found nothing:

    FileNotFoundError: .../snapshots/main/model-00001-of-00003.safetensors

Symlinks are what the hub cache uses anyway, so this creates them and re-runs the frozen arm.

    python tools/_p1108_link_and_run.py --arms frozen [--apply]
"""
from __future__ import annotations

import argparse
import os
import sys

import paramiko

HOST = os.environ.get("P3SSH_HOST", "")
PORT = int(os.environ.get("P3SSH_PORT", "22"))
PASS = os.environ.get("P3SSH_PASS", "")

LINK = r"""
cd /root/autodl-tmp/hf/hub/models--llava-hf--llava-1.5-7b-hf
SNAP=snapshots/main
for f in blobs/*.safetensors; do
  b=$(basename "$f")
  [ -e "$SNAP/$b" ] || ln -s "../../blobs/$b" "$SNAP/$b"
done
echo "=== snapshot contents ==="
ls -la "$SNAP" | head -16
echo "=== sizes match the registry? ==="
for b in model-00001-of-00003.safetensors model-00002-of-00003.safetensors model-00003-of-00003.safetensors; do
  printf '  %-34s blob=%s link=%s\n' "$b" "$(stat -c %s blobs/$b)" "$(stat -Lc %s $SNAP/$b 2>/dev/null || echo MISSING)"
done
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arms", default="frozen")
    ap.add_argument("--eval-pairs", type=int, default=500)
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

    def sh(cmd: str, timeout: int = 2400) -> str:
        _i, o, e = cli.exec_command(cmd, timeout=timeout)
        return (o.read().decode("utf-8", "replace") + e.read().decode("utf-8", "replace")).strip()

    print(sh(LINK))
    print(f"\n=== canonical recomputation: arms={a.arms} ===")
    cmd = (f"cd /root/p3 && ARMS={a.arms} EVAL_PAIRS={a.eval_pairs} bash _p1107_canonical.sh 2>&1 | tail -26")
    print(sh(cmd))
    cli.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
