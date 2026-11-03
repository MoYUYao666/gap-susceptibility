# -*- coding: utf-8 -*-
r"""Wait for the LLaVA sweep to reach twelve records, then freeze, verify and report in one pass.

Called with a wait budget so a single invocation covers the remaining runs instead of repeated status polls.
Nothing is written to the host except a snapshot directory and a summary file.

    python tools/_p1024_await_and_finalize.py --wait 3300
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

import paramiko

HOST = os.environ.get("P3SSH_HOST", "")
PORT = int(os.environ.get("P3SSH_PORT", "22"))
PASS = os.environ.get("P3SSH_PASS", "")
OUT = "/root/p3/outputs/llava_bf16_sites"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--wait", type=int, default=3300)
    ap.add_argument("--poll", type=int, default=300)
    a = ap.parse_args()
    if not (HOST and PASS):
        print("  P3SSH_HOST / P3SSH_PASS are not set")
        return 2

    cli = paramiko.SSHClient()
    cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    cli.connect(HOST, port=PORT, username="root", password=PASS, timeout=30,
                allow_agent=False, look_for_keys=False)

    def sh(cmd: str, timeout: int = 120) -> str:
        _i, o, e = cli.exec_command(cmd, timeout=timeout)
        return (o.read().decode("utf-8", "replace") + e.read().decode("utf-8", "replace")).strip()

    deadline = time.time() + a.wait
    seen = 0
    while time.time() < deadline:
        state = sh(f"ls {OUT}/*.json 2>/dev/null | grep -v train_progress | wc -l; "
                   f"cat {OUT}/train_progress.json 2>/dev/null | head -6")
        lines = state.splitlines()
        n = int(lines[0]) if lines and lines[0].strip().isdigit() else 0
        run = next((ln for ln in lines if '"run"' in ln), "?")
        step = next((ln for ln in lines if '"step"' in ln), "?")
        if n != seen:
            print(f"  [{time.strftime('%H:%M')}] records={n} | {run.strip()} {step.strip()}")
            seen = n
        if n >= 12:
            print("  twelve records reached")
            break
        time.sleep(a.poll)

    print()
    print("=== final state ===")
    print(sh(f"ls -la {OUT}/ | tail -20"))
    print("=== per-record metrics ===")
    print(sh("/root/miniconda3/bin/python - <<'PYEOF'\n"
             "import json, glob\n"
             "rows = []\n"
             "for f in sorted(glob.glob('" + OUT + "/*.json')):\n"
             "    if 'train_progress' in f: continue\n"
             "    d = json.load(open(f))\n"
             "    rows.append((d.get('arm'), d.get('seed'), d.get('dg_before'), d.get('dg_after'),\n"
             "                 d.get('cg_before'), d.get('cg_after'), d.get('dg_rel_change'),\n"
             "                 d.get('train_seconds'), d.get('samples'), d.get('epochs')))\n"
             "print('  %-11s %-5s %9s %9s %9s %9s %9s %8s %6s' % ('arm','seed','dg_before',\n"
             "      'dg_after','cg_before','cg_after','rel%','train_s','n'))\n"
             "for r in rows:\n"
             "    rel = ('%+.3f' % (100 * r[6])) if r[6] is not None else '-'\n"
             "    print('  %-11s %-5s %9.4f %9.4f %9.4f %9.4f %9s %8s %6s' % (\n"
             "        r[0], r[1], r[2] or -1, r[3] or -1, r[4] or -1, r[5] or -1, rel, r[7], r[8]))\n"
             "print('  records:', len(rows))\n"
             "PYEOF", timeout=180))
    print("=== artefacts ===")
    print(sh(f"ls {OUT}/*.pt 2>/dev/null | wc -l; du -sh {OUT}; df -h / | tail -1"))
    print("=== failures ===")
    print(sh(f"cat {OUT}/ARM_FAILURES.txt 2>/dev/null | tail -5 || echo none"))
    cli.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
