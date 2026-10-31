# -*- coding: utf-8 -*-
r"""One-shot health check for the running sweep, so supervision is systematic rather than ad hoc.

Answers, in one pass:
  * is the process alive, and is it consuming the GPU?
  * how many steps have been done and at what rate -- and is the rate consistent with the previous check?
  * did any arm fail (ARM_FAILURES.txt)?
  * how many records exist, and what do the canonical numbers look like so far?
  * is the disk about to fill (this killed a run on 2026-10-16)?
  * when will it finish?

A step count that has not advanced since the previous invocation is reported as STALLED, which is the failure mode
that cost a run before (a silent death with no traceback at 11:44 on 2026-10-16).

    python tools/_p1141_supervise.py [--json]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time

import paramiko

HOST = os.environ.get("P3SSH_HOST", "")
PORT = int(os.environ.get("P3SSH_PORT", "22"))
PASS = os.environ.get("P3SSH_PASS", "")
OUT_DIR = "/root/p3/outputs/llava_canonical"
LOG = "/root/p3/retrain_canonical.log"
STATE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                     "outputs", "_supervise_state.json")

REMOTE = r"""
echo "### process"
ps -eo pid,etimes,stat,pcpu,cmd | grep _p820_llava_sites | grep -v grep | head -1
echo "### gpu"
nvidia-smi --query-gpu=memory.used,utilization.gpu --format=csv,noheader
echo "### disk"
df -h / /root/autodl-tmp | tail -2
echo "### progress"
cat /root/p3/outputs/llava_canonical/train_progress.json 2>/dev/null
echo "### records"
ls /root/p3/outputs/llava_canonical/*.json 2>/dev/null | grep -v progress | xargs -n1 basename 2>/dev/null | tr '\n' ' '
echo
echo "### failures"
if [ -s /root/p3/outputs/llava_canonical/ARM_FAILURES.txt ]; then wc -l < /root/p3/outputs/llava_canonical/ARM_FAILURES.txt; else echo 0; fi
echo "### canonical"
grep -a "canonical DG" /root/p3/retrain_canonical.log 2>/dev/null | tail -14
echo "### tail"
tail -2 /root/p3/retrain_canonical.log 2>/dev/null | tr -d '\r'
echo "### date"
date +%s
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    if not (HOST and PASS):
        print("  P3SSH_HOST / P3SSH_PASS are not set")
        return 2
    cli = paramiko.SSHClient()
    cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    cli.connect(HOST, port=PORT, username="root", password=PASS, timeout=30,
                allow_agent=False, look_for_keys=False)
    _i, o, e = cli.exec_command(REMOTE, timeout=120)
    raw = (o.read() + e.read()).decode("utf-8", "replace")
    cli.close()

    def sect(name: str) -> str:
        m = re.search(rf"### {name}\n(.*?)(?=\n### |\Z)", raw, re.S)
        return m.group(1).strip() if m else ""

    proc = sect("process")
    gpu = sect("gpu")
    disk = sect("disk")
    prog_raw = sect("progress")
    records = sect("records").split()
    fails = sect("failures")
    canon = [ln for ln in sect("canonical").splitlines() if "canonical DG" in ln]
    tail = sect("tail")
    now = int(sect("date") or time.time())

    alive = bool(proc) and "_p820_llava_sites" in proc
    # the progress file is pretty-printed JSON; take the outermost braces rather than assuming the section
    # starts exactly at "{", which failed on the first run and left `run`/`step` unread
    prog = {}
    if "{" in prog_raw and "}" in prog_raw:
        try:
            prog = json.loads(prog_raw[prog_raw.find("{"): prog_raw.rfind("}") + 1])
        except Exception:
            prog = {}
    run = prog.get("run", "?")
    step = prog.get("step")
    total = prog.get("steps_total")
    sps = prog.get("sec_per_step")

    # compare against the previous run of this checker to catch a stall
    prev = {}
    if os.path.exists(STATE):
        try:
            prev = json.load(open(STATE, encoding="utf-8"))
        except Exception:
            prev = {}
    prev_step = prev.get("step")
    prev_run = prev.get("run")
    prev_t = prev.get("t")
    advanced = None
    rate = None
    if step is not None and prev_step is not None and prev_run == run and prev_t:
        advanced = step > prev_step
        if now > prev_t:
            rate = (step - prev_step) / (now - prev_t)

    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    json.dump({"run": run, "step": step, "t": now}, open(STATE, "w", encoding="utf-8"))

    # per-run canonical summary so far
    by_arm: dict[str, list[float]] = {}
    for ln in canon:
        m = re.search(r"canonical DG\* [\d.]+ -> ([\d.]+)\s+\(rel ([+\-\d.]+)%\)", ln)
        if m:
            rel = float(m.group(2))
            arm = "frozen" if abs(rel) < 1.0 else None
    # arm names are not in the log line, so report the raw list instead
    rels = []
    for ln in canon:
        m = re.search(r"\(rel ([+\-\d.]+)%\)", ln)
        if m:
            rels.append(float(m.group(1)))

    report = {
        "alive": alive,
        "gpu": gpu.replace("\n", " | "),
        "disk": " | ".join(disk.splitlines()),
        "run": run,
        "step": step,
        "total": total,
        "sec_per_step": sps,
        "advanced_since_last": advanced,
        "steps_per_sec_observed": round(rate, 4) if rate is not None else None,
        "records": len(records),
        "arm_failures_lines": int(fails) if fails.isdigit() else fails,
        "canonical_rels": rels,
        "tail": tail.replace("\n", " / "),
    }
    if not a.json:
        print("=== sweep health ===")
        print(f"  alive          : {alive}")
        print(f"  gpu            : {report['gpu']}")
        print(f"  disk           : {report['disk']}")
        print(f"  run            : {run}   step {step}/{total}   {sps} s/step")
        if advanced is not None:
            print(f"  advanced       : {advanced}   observed {report['steps_per_sec_observed']} steps/s")
        else:
            print("  advanced       : (first check, baseline recorded)")
        print(f"  records        : {len(records)}  {records}")
        print(f"  arm failures   : {report['arm_failures_lines']}")
        if rels:
            print(f"  canonical rel% : {rels}")
        print(f"  log tail       : {report['tail']}")
        print()
        problems = []
        if not alive:
            problems.append("the sweep process is NOT running")
        if advanced is False:
            problems.append(f"step did not advance since the last check (still {step})")
        if report["arm_failures_lines"] not in (0, "0"):
            problems.append(f"{report['arm_failures_lines']} lines in ARM_FAILURES.txt")
        m = re.search(r"(\d+)%\s+(\S+)\s+(\S+)\s+(\d+)", report["disk"].splitlines()[0] if report["disk"] else "")
        print("  VERDICT:", "OK" if not problems else "ATTENTION")
        for p in problems:
            print("    -", p)
    else:
        print(json.dumps(report, ensure_ascii=False))
    return 0 if report["alive"] or len(records) >= 12 else 1


if __name__ == "__main__":
    sys.exit(main())
