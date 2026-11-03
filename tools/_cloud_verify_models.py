# -*- coding: utf-8 -*-
r"""云端：核对权重完整性 + 补缺（2026-10-09）。

    $env:CLOUD_PW='...'; python tools\_cloud_verify_models.py
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))
PY = "/root/miniconda3/bin/python"
WORK = "/root/autodl-tmp/work"

V = r'''
cd /root/autodl-tmp/work
echo "=== 权重文件 ==="
for d in models/clip-vit-base-patch32 models/clip-vit-base-patch16 models/openclip; do
  echo "--- $d"
  ls -la "$d" 2>/dev/null | awk 'NR>3{printf "  %12s  %s\n", $5, $9}'
done
echo
echo "=== 实际加载校验（含 patch size 断言）==="
/root/miniconda3/bin/python - <<'PY'
import os, sys
os.chdir("/root/autodl-tmp/work")
import torch
from transformers import CLIPModel
for dst, want in [("models/clip-vit-base-patch32", 32),
                  ("models/clip-vit-base-patch16", 16),
                  ("models/openclip", 32)]:
    if not os.path.isdir(dst):
        print(f"  {dst}: MISSING DIR"); continue
    big = [f for f in os.listdir(dst)
           if f.endswith((".bin", ".safetensors"))
           and os.path.getsize(os.path.join(dst, f)) > 100e6]
    if not big:
        print(f"  {dst}: NO WEIGHTS ({os.listdir(dst)[:6]})"); continue
    try:
        m = CLIPModel.from_pretrained(dst, local_files_only=True)
        got = m.config.vision_config.patch_size
        n = sum(p.numel() for p in m.parameters()) / 1e6
        print(f"  {dst}: {big[0]} {os.path.getsize(os.path.join(dst,big[0]))} B | "
              f"patch={got} (want {want}) | params={n:.1f}M | "
              f"{'OK' if got == want else 'MISMATCH'}")
    except Exception as e:
        print(f"  {dst}: LOAD FAIL {str(e)[:130]}")
PY
echo
echo "=== 磁盘 ==="
df -h / | tail -1
du -sh models .ms 2>/dev/null
'''


def main() -> int:
    from _cloud_ssh import client, run

    c = client()
    try:
        print("=== 权重核对 ===")
        run(c, V, timeout=420)
    finally:
        c.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
