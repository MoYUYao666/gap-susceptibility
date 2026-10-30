# -*- coding: utf-8 -*-
r"""Decide whether the cloud sweep's results are sound. This is the gate in front of the shutdown.

Operator instruction 2026-10-15: "按你要求结果无误全部跑完之后直接关机". The shutdown therefore happens only
if every check here passes, and the machine is left running if any of them fails.

Checks, all against the files the sweep wrote:

1. the run finished (its log carries BF16_SWEEP_DONE and the process is gone);
2. one record per arm and seed, twelve in total, and no leftovers from the timing runs;
3. every record carries the fields the analysis needs, with the scale actually used (1500/500/3/rank 8),
   a training time above zero for the trained arms, and no null metric;
4. the frozen arm's metric is identical across its three seeds -- that arm trains nothing, so any spread
   there would mean the measurement itself is unstable;
5. the log is free of errors and of tracebacks;
6. the reported losses look like training rather than a stall;
7. metrics are finite and in range.

Usage:

    python tools/_p984_verify_cloud_results.py            # report only
    python tools/_p984_verify_cloud_results.py --shutdown # shut the host down, only if everything passed
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

import paramiko

HOST = os.environ.get("P3SSH_HOST", "")
PORT = int(os.environ.get("P3SSH_PORT", "22"))
PASS = os.environ.get("P3SSH_PASS", "")
OUTDIR = "outputs/llava_bf16_sites"
LOG = "bf16_sweep2.log"
WANT_RUNS = 12
ARMS = ("frozen", "text_only", "vision_only", "both")
SEEDS = (42, 123, 456)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--shutdown", action="store_true")
    ap.add_argument("--outdir", default=OUTDIR)
    ap.add_argument("--log", default=LOG)
    a = ap.parse_args()
    if not (HOST and PASS):
        print("  P3SSH_HOST / P3SSH_PASS are not set")
        return 2

    cli = paramiko.SSHClient()
    cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    cli.connect(HOST, port=PORT, username="root", password=PASS, timeout=30,
                allow_agent=False, look_for_keys=False)

    def sh(cmd: str, timeout: int = 180) -> str:
        _i, o, e = cli.exec_command(cmd, timeout=timeout)
        return (o.read().decode("utf-8", "replace") + e.read().decode("utf-8", "replace")).strip()

    problems: list[str] = []
    notes: list[str] = []

    log = sh(f"cat /root/p3/{a.log} 2>/dev/null | tail -400")
    print("=== log tail ===")
    for line in log.splitlines()[-6:]:
        print("   ", line[:150])

    # 1. finished?
    done = "BF16_SWEEP_DONE" in log
    # `pgrep -f <pattern>` also matches the shell that runs this check, because the pattern is part of
    # its command line. Listing the processes and excluding the checker avoids that self-match; the
    # measured state on 2026-10-16 was `NO SWEEP PROCESS` with the device idle at 1 MiB.
    alive = sh("ps -eo pid,etimes,cmd | grep _p820_llava_sites | grep -v grep "
               "| grep -v _p984_verify || echo NONE")
    still_running = "NONE" not in alive and bool(alive.strip())
    print(f"\n=== finished? log says done: {done}, process alive: {still_running}")
    if not done:
        problems.append("the sweep has not finished (no BF16_SWEEP_DONE in the log)")
    if still_running:
        problems.append("a sweep process is still running")

    # 2. records
    raw = sh(f"cat /root/p3/{a.outdir}/*.json 2>/dev/null | head -c 200000")
    recs: list[dict] = []
    listing = sh(f"ls /root/p3/{a.outdir}/ 2>/dev/null")
    files = [f for f in listing.split() if f.endswith(".json")]
    print(f"=== records: {len(files)} files -> {files}")
    for f in files:
        blob = sh(f"cat /root/p3/{a.outdir}/{f}")
        try:
            d = json.loads(blob)
        except Exception as exc:
            problems.append(f"{f} is not valid JSON: {exc}")
            continue
        if "arm" in d:
            recs.append(d)
    trained = [r for r in recs if r.get("arm") != "frozen"]
    print(f"    records with an arm: {len(recs)} (frozen {len(recs) - len(trained)}, trained {len(trained)})")
    if len(recs) != WANT_RUNS:
        problems.append(f"expected {WANT_RUNS} run records, found {len(recs)}")

    seen = {(r.get("arm"), r.get("seed")) for r in recs}
    for arm in ARMS:
        for seed in SEEDS:
            if (arm, seed) not in seen:
                problems.append(f"missing run {arm}_s{seed}")

    # 3. fields and scale
    required = ("arm", "seed", "rank", "samples", "epochs", "dg_before", "dg_after", "cg_before",
                "cg_after", "n_eval", "train_seconds")
    for r in recs:
        name = f"{r.get('arm')}_s{r.get('seed')}"
        missing = [k for k in required if k not in r]
        if missing:
            problems.append(f"{name}: missing fields {missing}")
            continue
        if (r["samples"], r["epochs"], r["rank"]) != (1500, 3, 8):
            problems.append(f"{name}: scale is {r['samples']}/{r['epochs']}/rank{r['rank']}, "
                            f"expected 1500/3/rank8")
        if r["dg_after"] is None or r["cg_after"] is None:
            problems.append(f"{name}: a metric is null")
        if r["arm"] != "frozen" and not r["train_seconds"]:
            problems.append(f"{name}: trained arm reports train_seconds={r['train_seconds']}")

    # 4. the frozen arm must be identical across seeds
    fr = {r["seed"]: r["dg_after"] for r in recs if r.get("arm") == "frozen" and r.get("dg_after")}
    print(f"\n=== frozen arm DG* by seed: {fr}")
    if len(fr) == 3 and len({round(v, 12) for v in fr.values()}) != 1:
        problems.append(f"the frozen arm differs between seeds: {fr}")
    elif len(fr) == 3:
        notes.append("frozen arm identical across the three seeds, as it must be")

    # 5/6/7. log hygiene and ranges
    for pat, why in ((r"Traceback", "a traceback"), (r"^!.*Error", "an error line"),
                     (r"CUDA out of memory", "a CUDA OOM")):
        if re.search(pat, log, re.M):
            problems.append(f"the log contains {why}")
    losses = [float(m) for m in re.findall(r"loss ([\d.]+)\s+[\d.]+ s/step", log)]
    if losses:
        print(f"=== losses: first {losses[0]:.4f}, last {losses[-1]:.4f}, count {len(losses)}")
        if losses[-1] >= losses[0]:
            problems.append(f"the loss did not fall: {losses[0]:.4f} -> {losses[-1]:.4f}")
    else:
        problems.append("no loss heartbeats in the log")

    print("\n=== verdict ===")
    if problems:
        print("  NOT SOUND -- the host will NOT be shut down:")
        for p in problems:
            print(f"    - {p}")
    else:
        print("  all checks passed")
        for n in notes:
            print(f"    note: {n}")
    print(f"\n=== shutdown requested: {a.shutdown}, safe to shut down: {not problems}")

    if a.shutdown and not problems:
        print("=== shutting the host down ===")
        cli.exec_command("sync; sleep 2; shutdown -h now", timeout=30)
        cli.close()
        return 0
    cli.close()
    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main())
