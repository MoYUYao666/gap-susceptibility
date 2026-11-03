# -*- coding: utf-8 -*-
r"""Check what the new host already has, and whether its downloads are moving at all.

The host showed two stalls at once: `images.cocodataset.org` stopped growing at 3.8 MB of the 472 MB
annotation archive, and `pip install torch` (2.5 GB) had printed nothing in five minutes. Both could be the
same cause -- this instance's egress. This reports the preinstalled stack (earlier instances shipped a complete
environment, which would make the install unnecessary), and measures two independent downloads over 30 s.

    python tools/_p1064_env_and_network.py
"""
from __future__ import annotations

import os
import sys
import time

import paramiko

HOST = os.environ.get("P3SSH_HOST", "")
PORT = int(os.environ.get("P3SSH_PORT", "22"))
PASS = os.environ.get("P3SSH_PASS", "")

CHECK = r"""
echo "=== preinstalled packages (first 30) ==="
/root/miniconda3/bin/pip list 2>/dev/null | head -30
echo "=== key imports ==="
/root/miniconda3/bin/python - <<'PYEOF'
import importlib
for m in ("torch", "torchvision", "transformers", "peft", "accelerate", "numpy", "PIL"):
    try:
        mod = importlib.import_module(m)
        print("  %-14s %s" % (m, getattr(mod, "__version__", "?")))
    except Exception as exc:
        print("  %-14s MISSING (%s)" % (m, type(exc).__name__))
PYEOF
echo "=== running installs ==="
ps -eo pid,etimes,cmd | grep -E "pip|python" | grep -v grep | head -5 || echo none
echo "=== disk ==="
df -h / /root/autodl-tmp | tail -2
"""


def main() -> int:
    if not (HOST and PASS):
        print("  P3SSH_HOST / P3SSH_PASS are not set")
        return 2
    cli = paramiko.SSHClient()
    cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    cli.connect(HOST, port=PORT, username="root", password=PASS, timeout=30,
                allow_agent=False, look_for_keys=False)

    def sh(cmd: str, timeout: int = 300) -> str:
        _i, o, e = cli.exec_command(cmd, timeout=timeout)
        return (o.read().decode("utf-8", "replace") + e.read().decode("utf-8", "replace")).strip()

    print(sh(CHECK))

    print("\n=== 30 s download measurement ===")
    for label, cmd in (
        ("coco annotations zip",
         "stat -c %s /root/p3/coco_eval/_ann.zip 2>/dev/null || echo 0"),
        ("pip cache (torch wheel, partial)",
         "du -sb /root/autodl-tmp/pipcache 2>/dev/null | cut -f1 || echo 0"),
    ):
        a = sh(cmd)
        time.sleep(30)
        b = sh(cmd)
        try:
            d = (int(b) - int(a)) / 30
        except ValueError:
            d = -1
        print(f"  {label:<36} {a} -> {b}  ({d:,.0f} B/s)")

    print("\n=== can the host reach the pip mirror it was told to use? ===")
    print(sh("curl -sS -m 15 -o /dev/null -w 'pypi.tuna %{http_code} %{speed_download} B/s\\n' "
             "https://pypi.tuna.tsinghua.edu.cn/simple/torch/ || echo 'tuna unreachable'"))
    print(sh("curl -sS -m 15 -o /dev/null -w 'pypi.org %{http_code} %{speed_download} B/s\\n' "
             "https://pypi.org/simple/torch/ || echo 'pypi unreachable'"))
    cli.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
