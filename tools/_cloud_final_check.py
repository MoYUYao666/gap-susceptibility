# -*- coding: utf-8 -*-
r"""云端：三模型最终校验 + 若通过则启动实验（2026-10-09）。

    $env:CLOUD_PW='...'; python tools\_cloud_final_check.py [--launch]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))
PY = "/root/miniconda3/bin/python"
WORK = "/root/autodl-tmp/work"

REMOTE = r'''
import os, sys
os.chdir("/root/autodl-tmp/work")
sys.path.insert(0, ".")
print("=== 三模型加载校验 ===")
from transformers import CLIPModel
ok_all = True
for d, want in (("models/clip-vit-base-patch32", 32),
                ("models/clip-vit-base-patch16", 16),
                ("models/openclip", 32)):
    big = []
    if os.path.isdir(d):
        for f in os.listdir(d):
            p = os.path.join(d, f)
            if f.endswith((".bin", ".safetensors")) and os.path.getsize(p) > 100e6:
                big.append((f, os.path.getsize(p)))
    if not big:
        print("  %-32s ❌ 无大权重" % d); ok_all = False; continue
    try:
        m = CLIPModel.from_pretrained(d, local_files_only=True)
        got = m.config.vision_config.patch_size
        n = sum(x.numel() for x in m.parameters()) / 1e6
        good = (got == want)
        ok_all &= good
        print("  %-32s ✅ %s %.0fMB patch=%d(want %d) params=%.1fM %s"
              % (d, big[0][0], big[0][1]/1e6, got, want, n, "OK" if good else "MISMATCH"))
    except Exception as e:
        ok_all = False
        print("  %-32s ❌ %s" % (d, str(e)[:110]))
print("READY" if ok_all else "NOTREADY")
'''


def main() -> int:
    from _cloud_ssh import bg, client, run

    c = client()
    try:
        io.open(REPO / "outputs" / "_remote_fc.py", "w", encoding="utf-8",
                newline="\n").write(REMOTE)
        sftp = c.open_sftp()
        sftp.put(str(REPO / "outputs" / "_remote_fc.py"), f"{WORK}/_fc.py")
        sftp.close()
        out, _ = run(c, f"{PY} {WORK}/_fc.py", timeout=600)
        if "--launch" in sys.argv:
            if "READY" in out and "NOTREADY" not in out:
                print("\n=== 校验通过 → 启动云端驱动 ===")
                bg(c, f"{PY} _cloud_driver.py", "outputs_cloud_driver.log")
            else:
                print("\n  ❌ 校验未过，不启动")
    finally:
        c.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
