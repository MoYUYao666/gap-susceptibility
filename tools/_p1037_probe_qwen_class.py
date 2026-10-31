# -*- coding: utf-8 -*-
r"""Report the Qwen runner's import lines locally and the Qwen classes available on the host.

The generated runner failed with `NameError: name 'Qwen2_5_VLForConditionalGeneration' is not defined`,
which means the import statement was never rewritten (the replacement pattern did not match the real import
line) and/or the class does not exist under that name in transformers 5.16.1. Both possibilities are checked
here in one pass.

    python tools/_p1037_probe_qwen_class.py
"""
from __future__ import annotations

import io
import os
import sys
from pathlib import Path

import paramiko

REPO = Path(__file__).resolve().parents[1]
RUNNER = REPO / "tools" / "_p1035_qwen_sites.py"
HOST = os.environ.get("P3SSH_HOST", "")
PORT = int(os.environ.get("P3SSH_PORT", "22"))
PASS = os.environ.get("P3SSH_PASS", "")

REMOTE = r"""
/root/miniconda3/bin/python - <<'PYEOF'
import transformers as t
names = [n for n in dir(t) if "Qwen" in n]
print("  Qwen classes:", sorted(n for n in names if "VL" in n or "Conditional" in n))
print("  AutoModelForVision2Seq:", hasattr(t, "AutoModelForVision2Seq"))
print("  AutoModelForImageTextToText:", hasattr(t, "AutoModelForImageTextToText"))
from transformers import AutoConfig
cfg = AutoConfig.from_pretrained("Qwen/Qwen2.5-VL-7B-Instruct")
print("  model_type:", getattr(cfg, "model_type", None))
print("  image_token_id:", getattr(cfg, "image_token_id", None))
print("  architectures:", getattr(cfg, "architectures", None))
PYEOF
"""


def main() -> int:
    print("=== local runner import lines ===")
    for i, line in enumerate(io.open(RUNNER, encoding="utf-8").read().splitlines(), 1):
        if line.lstrip().startswith(("from transformers", "import transformers")) or "Llava" in line:
            print(f"  {i:>4} {line[:110]}")

    if not (HOST and PASS):
        print("  P3SSH_HOST / P3SSH_PASS are not set; remote side skipped")
        return 0
    cli = paramiko.SSHClient()
    cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    cli.connect(HOST, port=PORT, username="root", password=PASS, timeout=30,
                allow_agent=False, look_for_keys=False)
    _i, o, e = cli.exec_command("export HF_HOME=/root/autodl-tmp/hf HF_HUB_OFFLINE=1; " + REMOTE, timeout=300)
    print("=== host: transformers classes and the Qwen config ===")
    print((o.read().decode("utf-8", "replace") + e.read().decode("utf-8", "replace")).strip())
    cli.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
