# -*- coding: utf-8 -*-
r"""Verify the canonical retrain and pull its results back to the laptop.

Run once the sweep writes its twelve records. It checks the things that would invalidate the numbers, then copies
the records and the (now real) adapters down and verifies every file's size.

Checks:
  1. twelve records, all four arms x three seeds, none missing;
  2. every record carries both metric definitions (the canonical `dg_star_*` and the legacy `dg_*`);
  3. every record has `n_eval == 500`;
  4. the frozen arm's three seeds agree -- it trains nothing, so any spread is measurement noise;
  5. the adapters are NON-EMPTY this time (the defect of 2026-10-16);
  6. no arm failed (ARM_FAILURES.txt absent or empty).

    python tools/_p1138_verify_and_pull.py [--apply]
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import paramiko

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOST = os.environ.get("P3SSH_HOST", "")
PORT = int(os.environ.get("P3SSH_PORT", "22"))
PASS = os.environ.get("P3SSH_PASS", "")
REMOTE = "/root/p3/outputs/llava_canonical"
LOCAL = os.path.join(REPO, "outputs", "llava_canonical_cloud")
ARMS = ("frozen", "text_only", "vision_only", "both")
SEEDS = (42, 123, 456)

VERIFY = r"""
import glob, json, os
from pathlib import Path
d = Path("/root/p3/outputs/llava_canonical")
recs = {}
for f in sorted(d.glob("*.json")):
    if "progress" in f.name or f.name.endswith("sites.json"):
        continue
    o = json.loads(f.read_text(encoding="utf-8"))
    if "arm" in o:
        recs[(o["arm"], o["seed"])] = o
fails = []
for arm in ("frozen", "text_only", "vision_only", "both"):
    for seed in (42, 123, 456):
        if (arm, seed) not in recs:
            fails.append(f"missing {arm}_s{seed}")
have_canon = all(("dg_star_before" in o and "dg_star_after" in o and "dg_empirical_after" in o)
                 for o in recs.values())
n_eval_ok = all(o.get("n_eval") == 500 for o in recs.values())
frozen = {s: recs.get(("frozen", s), {}).get("dg_star_after") for s in (42, 123, 456)}
frozen_same = len({round(v, 9) for v in frozen.values() if v is not None}) == 1
adapters = {}
for f in sorted(d.glob("*.pt")):
    adapters[f.name] = (round(f.stat().st_size / 1e6, 1),)
af = d / "ARM_FAILURES.txt"
arm_fail = af.read_text(encoding="utf-8") if af.exists() else ""
print(json.dumps({
    "records": len(recs), "fails": fails, "canonical_fields": have_canon, "n_eval_500": n_eval_ok,
    "frozen_by_seed": frozen, "frozen_identical": frozen_same,
    "adapters": adapters, "arm_failures_lines": len(arm_fail.splitlines()),
    "summary": {f"{a}": [round(100 * (o["dg_star_after"] - o["dg_star_before"]) / o["dg_star_before"], 3)
                         for s in (42, 123, 456) if (o := recs.get((a, s)))]
                for a in ("frozen", "text_only", "vision_only", "both")},
}, indent=1, ensure_ascii=False))
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  (dry run)")
        return 0
    if not (HOST and PASS):
        print("  P3SSH_HOST / P3SSH_PASS are not set")
        return 2
    cli = paramiko.SSHClient()
    cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    cli.connect(HOST, port=PORT, username="root", password=PASS, timeout=30,
                allow_agent=False, look_for_keys=False)

    def sh(cmd: str, timeout: int = 900) -> str:
        _i, o, e = cli.exec_command(cmd, timeout=timeout)
        return (o.read().decode("utf-8", "replace") + e.read().decode("utf-8", "replace")).strip()

    sftp = cli.open_sftp()
    with sftp.open("/root/p3/_verify_canonical.py", "w") as fh:
        fh.write(VERIFY)
    sftp.close()
    raw = sh("/root/miniconda3/bin/python /root/p3/_verify_canonical.py 2>&1 | tail -80")
    print("=== verification ===")
    print(raw)
    try:
        info = json.loads(raw[raw.index("{"):])
    except Exception as exc:
        print("  !! could not parse the verification output:", exc)
        cli.close()
        return 1

    problems = list(info.get("fails") or [])
    if info["records"] != 12:
        problems.append(f"expected 12 records, found {info['records']}")
    if not info["canonical_fields"]:
        problems.append("some records lack the canonical fields")
    if not info["n_eval_500"]:
        problems.append("some records were not measured on 500 pairs")
    if not info["frozen_identical"]:
        problems.append(f"frozen seeds differ: {info['frozen_by_seed']}")
    empty = [k for k, v in info["adapters"].items()]
    if not empty:
        problems.append("no adapters written")
    if info["arm_failures_lines"]:
        print(f"  note: ARM_FAILURES.txt has {info['arm_failures_lines']} lines")

    print("\n=== canonical DG* relative change by arm (%, per seed) ===")
    for arm, vals in info["summary"].items():
        print(f"  {arm:<12} {vals}")

    if problems:
        print("\n  NOT SOUND:")
        for p in problems:
            print(f"    - {p}")
        cli.close()
        return 1
    print("\n  all checks passed")

    print("\n=== pulling results back ===")
    os.makedirs(LOCAL, exist_ok=True)
    sftp = cli.open_sftp()
    ok = bad = 0
    for name in sorted(sftp.listdir(REMOTE)):
        if not name.endswith((".json", ".pt")):
            continue
        rp, lp = f"{REMOTE}/{name}", os.path.join(LOCAL, name)
        rs = sftp.stat(rp).st_size
        sftp.get(rp, lp)
        ls = os.path.getsize(lp)
        good = rs == ls
        ok += good
        bad += not good
        print(f"  {'OK ' if good else 'BAD'} {name:<32} {rs:>12,}")
    sftp.close()
    cli.close()
    total = sum(os.path.getsize(os.path.join(LOCAL, f)) for f in os.listdir(LOCAL))
    print(f"\n  files verified: {ok}, mismatched: {bad}")
    print(f"  local: {LOCAL}  ({total / 1e6:.1f} MB)")
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
