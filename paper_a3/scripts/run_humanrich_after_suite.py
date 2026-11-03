# -*- coding: utf-8 -*-
r"""Wait for the main strengthening suite to finish, then run the human-rich arm grid.

Kept as a separate waiter so the suite that is already running does not need to be restarted.
"""
import io
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = sys.executable
SUITE_PID = os.path.join(ROOT, "runs", "suite.pid")
LOG = os.path.join(ROOT, "runs", "humanrich_log.txt")


def log(msg):
    with io.open(LOG, "a", encoding="utf-8", newline="") as f:
        f.write("[%s] %s\n" % (time.strftime("%H:%M:%S"), msg))
    print(msg, flush=True)


def suite_alive():
    if not os.path.exists(SUITE_PID):
        return False
    pid = io.open(SUITE_PID).read().strip()
    out = subprocess.run(["tasklist", "/FI", "PID eq %s" % pid], capture_output=True, text=True).stdout
    return pid in out


def main():
    log("waiter started; waiting for the main suite")
    while suite_alive():
        time.sleep(60)
    log("main suite finished; starting the human-rich arm grid")
    proc = subprocess.run([PY, "-u", os.path.join(ROOT, "scripts", "run_humanrich_grid.py"), "--run"],
                          cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    with io.open(LOG, "a", encoding="utf-8", newline="") as f:
        f.write(proc.stdout.decode("utf-8", "replace")[-3000:] + "\n")
    log("human-rich grid finished with code %d" % proc.returncode)
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
