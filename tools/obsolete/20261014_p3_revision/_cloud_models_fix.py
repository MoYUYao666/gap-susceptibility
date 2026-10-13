# -*- coding: utf-8 -*-
r"""云端：核对已下模型文件 + 补下缺失（含 openclip 的非常规文件名）（2026-10-09）。

    $env:CLOUD_PW='...'; python tools\_cloud_models_fix.py
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))
PY = "/root/miniconda3/bin/python"
WORK = "/root/autodl-tmp/work"

CHECK = r'''
cd /root/autodl-tmp/work
echo "=== 各模型目录内容 ==="
for d in models/*/; do
  echo "--- $d"
  ls -la "$d" 2>/dev/null | awk 'NR>1{printf "  %10s  %s\n", $5, $9}' | head -14
done
echo
echo "=== 权重文件大小 ==="
find models -name "*.safetensors" -o -name "pytorch_model.bin" | while read f; do
  printf "  %10s  %s\n" "$(stat -c%s "$f")" "$f"
done
'''


def main() -> int:
    from _cloud_ssh import client, run

    c = client()
    try:
        print("=== ① 核对现状 ===")
        run(c, CHECK, timeout=180)
    finally:
        c.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
