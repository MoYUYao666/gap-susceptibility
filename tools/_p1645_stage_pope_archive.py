#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""_p1645_stage_pope_archive.py -- task-18: verify the retrieved POPE files against the
instance-side sha256 list, then (only if every hash matches) stage them into
outputs/analysis/ so the rest of the pipeline sees them at the path the producing
script declares.

Why a script: the project rules require batch file operations to be reproducible and
asserted.  This one refuses to copy anything if a hash is off, and it is idempotent:
if outputs/analysis already holds a byte-identical file it is left untouched.

Source: cloud_retrieved/round2_2026-10-25/pope/<name> + POPE_SHA256.txt
Dest:   outputs/analysis/<name>

Output: outputs/analysis/p3_pope_staging.json
"""
import hashlib
import json
import os
import shutil
from pathlib import Path

ROOT = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = ROOT / "cloud_retrieved/round2_2026-10-25/pope"
SHAFILE = ROOT / "cloud_retrieved/round2_2026-10-25/POPE_SHA256.txt"
DST = ROOT / "outputs/analysis"
OUT = DST / "p3_pope_staging.json"

WANT = ["p3_second_downstream.json",
        "p3_second_downstream_base.json",
        "p3_second_downstream_5.json",
        "p3_second_downstream_6.json",
        "p3_second_downstream_prepare.log",
        "p3_second_downstream_eval.log"]


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    expected = {}
    for line in SHAFILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        h, name = line.split()
        expected[name] = h

    rows, bad = [], []
    for name in WANT:
        s = SRC / name
        if not s.exists():
            rows.append({"name": name, "status": "MISSING_AT_SOURCE"})
            bad.append(name + " (missing at source)")
            continue
        got = sha(s)
        exp = expected.get(name)
        ok = (exp == got)
        if not ok:
            bad.append("%s (sha mismatch: expected %s got %s)" % (name, exp, got))
        d = DST / name
        existed = d.exists()
        dsha = sha(d) if existed else None
        action = "none"
        if ok:
            if not existed:
                shutil.copy2(s, d)
                action = "copied"
            elif dsha != got:
                shutil.copy2(s, d)
                action = "replaced (destination differed)"
            else:
                action = "already identical"
        rows.append({"name": name, "source": str(s.relative_to(ROOT)),
                     "dest": str(d.relative_to(ROOT)),
                     "size": s.stat().st_size, "sha256": got,
                     "expected_sha256": exp, "sha_ok": ok,
                     "dest_existed": existed, "dest_sha256_before": dsha,
                     "action": action})

    rep = {"source_dir": str(SRC.relative_to(ROOT)),
           "sha256_list": str(SHAFILE.relative_to(ROOT)),
           "files": rows, "all_hashes_ok": not bad, "problems": bad}
    OUT.write_text(json.dumps(rep, indent=1, ensure_ascii=False), encoding="utf-8")

    print("=" * 78)
    print("POPE ARCHIVE STAGING")
    print("=" * 78)
    for r in rows:
        print("  %-42s %-22s %s" % (r["name"], r["action"], "sha OK" if r.get("sha_ok") else "SHA BAD"))
        if r.get("size"):
            print("      %d B  sha256=%s..." % (r["size"], r["sha256"][:16]))
    if bad:
        print("\nREFUSING / PROBLEMS:")
        for b in bad:
            print("   -", b)
        return 1
    print("\nall %d files verified against the instance sha256 list" % len(WANT))
    print("wrote", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
