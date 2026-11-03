# -*- coding: utf-8 -*-
r"""云端：**终止全部实验与下载**（2026-10-09，操作者要求"跑完终止"）。

先保存关键产物（结果 JSON 清单 + Γ_m 数值），再杀进程。

    $env:CLOUD_PW='...'; python tools\_cloud_stop.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))

SAVE = r'''
import os, glob, json, subprocess, time
W = "/root/autodl-tmp/work"
os.chdir(W)

print("=== 终止前保存产物清单 ===")
files = sorted(glob.glob("outputs/**/*.json", recursive=True))
print("  JSON 产物 %d 个" % len(files))
inv = []
for f in files:
    inv.append({"path": f, "bytes": os.path.getsize(f)})
json.dump(inv, open("_cloud_inventory.json", "w"), indent=1)
for f in files[:30]:
    print("   ", f)
print("  ..." if len(files) > 30 else "")

print("\n=== Γ_m 数值（从驱动日志提取）===")
p = "outputs_cloud_driver.log"
if os.path.exists(p):
    for ln in open(p).read().splitlines():
        if "Γ_" in ln or "∇" in ln:
            print("  " + ln.strip()[:140])
'''


def main() -> int:
    apply = "--apply" in sys.argv
    from _cloud_ssh import client, run

    c = client()
    try:
        if apply:
            io.open(REPO / "outputs" / "_remote_save.py", "w", encoding="utf-8",
                    newline="\n").write(SAVE)
            sftp = c.open_sftp()
            sftp.put(str(REPO / "outputs" / "_remote_save.py"), "/root/autodl-tmp/work/_save.py")
            sftp.close()
            run(c, "/root/miniconda3/bin/python /root/autodl-tmp/work/_save.py", timeout=300)

        print("\n=== 终止全部 python / curl / bash 下载 ===")
        for pat in ("_7bp.py", "_cloud_driver", "strict_freeze", "curl", "wget",
                    "_probe", "_bp.py", "_tok.py", "_big.py", "_cloud_ms"):
            run(c, f"pkill -f '{pat}' 2>/dev/null; true", timeout=60, quiet=True)
        run(c, "sleep 3; echo '--- 剩余进程 ---'; "
               "pgrep -fa 'python|curl|wget' | head -10; echo '(空=已全部终止)'",
            timeout=120)
        run(c, "nvidia-smi --query-gpu=memory.used,utilization.gpu --format=csv,noheader",
            timeout=60)
    finally:
        c.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
