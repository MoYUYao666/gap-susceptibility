# -*- coding: utf-8 -*-
r"""云端环境探测：把远端命令写成文件，避免 PowerShell 转义地狱（2026-10-09）。

    $env:CLOUD_PW='...'; python tools\_cloud_probe.py
"""
from __future__ import annotations

import io
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))

PY = "/root/miniconda3/bin/python"

CMDS = [
    ("python 与依赖", f"{PY} -c \"import torch,transformers,peft,PIL,numpy,tqdm;"
                      "print('torch',torch.__version__);"
                      "print('transformers',transformers.__version__);"
                      "print('peft',peft.__version__);"
                      "print('cuda',torch.cuda.is_available())\" 2>&1 | tail -6"),
    ("网络: modelscope", "curl -s -o /dev/null -w 'modelscope:%{http_code}\\n' "
                        "--max-time 15 https://www.modelscope.cn"),
    ("网络: hf-mirror", "curl -s -o /dev/null -w 'hf-mirror:%{http_code}\\n' "
                       "--max-time 15 https://hf-mirror.com"),
    ("网络: huggingface", "curl -s -o /dev/null -w 'huggingface:%{http_code}\\n' "
                         "--max-time 15 https://huggingface.co"),
    ("pip 版本", f"{PY} -m pip --version 2>&1 | tail -1"),
    ("/ 可用空间", "df -h / | tail -1"),
]


def main() -> int:
    from _cloud_ssh import client, run

    c = client()
    try:
        print("=== 云端环境探测（RTX 4080 SUPER 32 GB）===")
        for label, cmd in CMDS:
            print(f"\n  ── {label} ──")
            run(c, cmd, timeout=120)
    finally:
        c.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
