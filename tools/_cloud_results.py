# -*- coding: utf-8 -*-
r"""云端：核对 seed 结果 + 查 `Γ_m` 的 rc=1（2026-10-09）。

    $env:CLOUD_PW='...'; python tools\_cloud_results.py
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))

REMOTE = r'''
import os, json, glob, subprocess
W = "/root/autodl-tmp/work"
os.chdir(W)

print("=== 全部 results.json ===")
files = sorted(glob.glob("outputs/**/results.json", recursive=True))
print("  共 %d 个" % len(files))
for f in files:
    try:
        d = json.load(open(f))
        cg0 = d.get("initial_gap", {}).get("centroid_gap")
        cg1 = d.get("final_gap", {}).get("centroid_gap")
        dlt = (cg1 - cg0) if (cg0 is not None and cg1 is not None) else None
        print("  %-56s CGΔ=%s" % (f[:56], ("%+.4f" % dlt) if dlt is not None else "?"))
    except Exception as e:
        print("  %-56s ERR %s" % (f[:56], str(e)[:60]))

print("\n=== Γ_m 日志（最后 20 行）===")
p = "outputs_cloud_driver.log"
if os.path.exists(p):
    lines = open(p).read().splitlines()
    i = next((k for k, l in enumerate(lines) if "Γ_m" in l or "gamma" in l.lower()), max(0, len(lines)-25))
    for ln in lines[max(0, i-25):]:
        print("  " + ln[:150])

print("\n=== gamma_clip.json 是否存在 ===")
print("  ", os.path.exists("outputs/analysis/gamma_clip.json"))
'''


def main() -> int:
    from _cloud_ssh import client, run

    c = client()
    try:
        io.open(REPO / "outputs" / "_remote_r.py", "w", encoding="utf-8",
                newline="\n").write(REMOTE)
        sftp = c.open_sftp()
        sftp.put(str(REPO / "outputs" / "_remote_r.py"), "/root/autodl-tmp/work/_r.py")
        sftp.close()
        run(c, "/root/miniconda3/bin/python /root/autodl-tmp/work/_r.py", timeout=600)
    finally:
        c.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
