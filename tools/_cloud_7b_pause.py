# -*- coding: utf-8 -*-
r"""云端：暂停/恢复 7B 下载（让 seed 独占带宽）（2026-10-09）。

    $env:CLOUD_PW='...'; python tools\_cloud_7b_pause.py --pause
    $env:CLOUD_PW='...'; python tools\_cloud_7b_pause.py --resume
    $env:CLOUD_PW='...'; python tools\_cloud_7b_pause.py --status
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))
PY = "/root/miniconda3/bin/python"
WORK = "/root/autodl-tmp/work"

PAUSE = r'''
import subprocess, os
subprocess.run(["pkill", "-f", "_7bp.py"])
subprocess.run(["pkill", "curl"])
import time; time.sleep(3)
n = subprocess.run(["pgrep", "-c", "curl"], capture_output=True, text=True).stdout.strip()
d = "models/qwen2vl7b"
size = sum(os.path.getsize(os.path.join(d,f)) for f in os.listdir(d)
           if os.path.isfile(os.path.join(d,f)))
parts = len([f for f in os.listdir(d) if ".tmp.p" in f])
print("  已暂停 ｜ curl 剩余 %s ｜ 7B 已下 %.2f GB ｜ 保留分段 %d 个"
      % (n or "0", size/1e9, parts))
'''

STATUS = r'''
import os, subprocess
d = "models/qwen2vl7b"
size = sum(os.path.getsize(os.path.join(d,f)) for f in os.listdir(d)
           if os.path.isfile(os.path.join(d,f)))
print("  7B: %.2f GB ｜ 分段 %d ｜ curl %s"
      % (size/1e9, len([f for f in os.listdir(d) if ".tmp.p" in f]),
         subprocess.run(["pgrep","-c","curl"],capture_output=True,text=True).stdout.strip() or "0"))
r = subprocess.run("tail -3 outputs_cloud_driver.log", shell=True,
                   capture_output=True, text=True)
print("  seed: " + (r.stdout or "").strip().replace("\n", " | ")[:180])
n = subprocess.run("find outputs -name results.json | wc -l", shell=True,
                   capture_output=True, text=True).stdout.strip()
print("  results.json:", n)
'''


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pause", action="store_true")
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--status", action="store_true")
    a = ap.parse_args()

    from _cloud_ssh import bg, client, run

    c = client()
    try:
        if a.pause:
            io.open(REPO / "outputs" / "_remote_p.py", "w", encoding="utf-8",
                    newline="\n").write(PAUSE)
            sftp = c.open_sftp()
            sftp.put(str(REPO / "outputs" / "_remote_p.py"), f"{WORK}/_p7b.py")
            sftp.close()
            run(c, f"{PY} {WORK}/_p7b.py", timeout=180)
        if a.resume:
            print("=== 恢复 7B 下载（续用已有分段）===")
            bg(c, f"{PY} _7bp.py", "outputs_7b.log")
        if a.status or not (a.pause or a.resume):
            io.open(REPO / "outputs" / "_remote_s.py", "w", encoding="utf-8",
                    newline="\n").write(STATUS)
            sftp = c.open_sftp()
            sftp.put(str(REPO / "outputs" / "_remote_s.py"), f"{WORK}/_s7b.py")
            sftp.close()
            run(c, f"cd {WORK} && {PY} _s7b.py", timeout=180)
    finally:
        c.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
