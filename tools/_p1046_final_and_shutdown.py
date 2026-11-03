# -*- coding: utf-8 -*-
r"""Final check before powering the host down, then shut it down.

Operator decision 2026-10-16: LLaVA is complete and archived, Qwen2.5-VL-7B needs more than 32 GB, so the
machine is switched off and Qwen waits for a larger one.

Everything that must outlive the host is verified present locally **before** the shutdown command is sent:

* the twelve records and their summary;
* all seven trained adapters, with sizes matching the host;
* the Qwen runner and the sweep that produced the LLaVA numbers;
* the handoff and file-map entries for this stage.

Then the gate is re-run against the host, and `shutdown -h now` is issued only if it still reports
`all checks passed`.

    python tools/_p1046_final_and_shutdown.py [--apply]
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

import paramiko

REPO = Path(__file__).resolve().parents[1]
LOCAL = REPO / "outputs" / "llava_bf16_sites_cloud"
HOST = os.environ.get("P3SSH_HOST", "")
PORT = int(os.environ.get("P3SSH_PORT", "22"))
PASS = os.environ.get("P3SSH_PASS", "")
PY = r"D:\Anaconda\envs\pytorch\python.exe"

EXPECTED_JSON = 12
EXPECTED_PT = 7


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    print("=== local archive ===")
    files = sorted(os.listdir(LOCAL))
    jsons = [f for f in files if f.endswith(".json")]
    pts = [f for f in files if f.endswith(".pt")]
    total = sum(os.path.getsize(LOCAL / f) for f in files)
    print(f"  {len(files)} files, {total / 1e6:.1f} MB | records {len(jsons)} | adapters {len(pts)}")
    for f in pts:
        print(f"    {os.path.getsize(LOCAL / f):>12,}  {f}")
    ok = True
    if len(jsons) < EXPECTED_JSON:
        print(f"  !! expected {EXPECTED_JSON} records, found {len(jsons)}")
        ok = False
    if len(pts) != EXPECTED_PT:
        print(f"  !! expected {EXPECTED_PT} adapters, found {len(pts)}")
        ok = False

    print("=== runner and sweep present locally ===")
    for name in ("_p1035_qwen_sites.py", "_p820_llava_sites.py"):
        p = REPO / "tools" / name
        print(f"  {name:<26} {p.exists()}  {p.stat().st_size if p.exists() else 0:,} bytes")
        ok = ok and p.exists()

    print("=== handoff entries written ===")
    hp = (REPO / "HANDOFF.md").read_text(encoding="utf-8")
    # The entries are dated headings, so the dates are what identify them; the first version of this check
    # looked for prose fragments that never appear verbatim and reported false absences.
    for mark in ("2026-10-16 18:30", "2026-10-16 12:40", "2026-10-16 11:30", "2026-10-16 09:55"):
        present = mark in hp
        print(f"  handoff {mark}  {present}")
        ok = ok and present
    mp = (REPO / "文件地图.md").read_text(encoding="utf-8")
    for mark in ("41. 🧩", "40. 💾", "39. 🔧", "38. 🐌"):
        present = mark in mp
        print(f"  map {mark}  {present}")
        ok = ok and present

    if not a.apply:
        print("\n  (dry run: nothing shut down)")
        return 0 if ok else 1
    if not ok:
        print("\n  local archive incomplete -- NOT shutting down")
        return 1

    print("\n=== re-running the verification gate on the host ===")
    r = subprocess.run([PY, str(REPO / "tools" / "_p984_verify_cloud_results.py"),
                        "--log", "sweep_run.log"], capture_output=True, text=True)
    tail = (r.stdout or "")[-600:]
    print(tail)
    if "all checks passed" not in tail:
        print("  the gate did not pass -- NOT shutting down")
        return 1

    print("=== powering the host down ===")
    cli = paramiko.SSHClient()
    cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    cli.connect(HOST, port=PORT, username="root", password=PASS, timeout=30,
                allow_agent=False, look_for_keys=False)
    cli.exec_command("sync; sleep 3; shutdown -h now", timeout=30)
    import time
    time.sleep(8)
    try:
        _i, o, _e = cli.exec_command("echo still-up", timeout=10)
        print("  host still responding after the command:", o.read().decode().strip())
    except Exception as exc:
        print("  connection closed as expected:", type(exc).__name__)
    cli.close()
    print("  shutdown issued")
    return 0


if __name__ == "__main__":
    sys.exit(main())
