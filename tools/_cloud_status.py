# -*- coding: utf-8 -*-
r"""云端状态一览（无需 PowerShell 转义）（2026-10-09）。

    $env:CLOUD_PW='...'; python tools\_cloud_status.py
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))
WORK = "/root/autodl-tmp/work"

STATUS = r"""cd /root/autodl-tmp/work
echo "=== 模型下载日志 ==="
grep -aE "OK |FAIL|===|ALLDONE" outputs_bin.log 2>/dev/null | tail -14
echo
echo "=== models 体积 ==="
du -sh models 2>/dev/null
echo
echo "=== 权重文件（>1MB）==="
find models -type f \( -name "*.bin" -o -name "*.safetensors" \) 2>/dev/null | while read f; do
  sz=$(stat -c%s "$f")
  if [ "$sz" -gt 1000000 ]; then printf "  %12s  %s\n" "$sz" "$f"; fi
done
echo
echo "=== 数据 ==="
du -sh flickr30k 2>/dev/null; ls flickr30k 2>/dev/null | head -4
echo
echo "=== 进程 ==="
pgrep -fa "_cloud_bin|_cloud_models|_p56_add|strict_freeze" 2>/dev/null | head -4
echo
echo "=== 磁盘 ==="
df -h / | tail -1
"""


def main() -> int:
    from _cloud_ssh import client, run

    c = client()
    try:
        print("=== 云端状态 ===")
        run(c, STATUS, timeout=300)
    finally:
        c.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
