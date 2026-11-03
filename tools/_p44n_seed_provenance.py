#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""_p44n_seed_provenance.py -- R3.17 follow-up demanded by the Lead:

Were seeds 42/123/999 (the paper's three seeds at r=5/r=6) the FIRST runs, or were
they selected out of the ten? And is the E0=3930.5 cluster an artefact of *when*
a run was made?

Evidence used (no speculation):
  * file mtime / ctime of every verify_r{5,6}_s*.json
  * the E0 recorded inside each file
  * the `note` field (the tf457 run left an explicit note)
  * the paper's own sweep driver (run_full_sweep.py / run_e4_counterfactual.py)
    which fixes SEEDS = [42, 123, 999]

Output: outputs/analysis/p3_seed_provenance.json
"""
import json
import os
import re
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXP = os.path.join(ROOT, "paper3", "scripts", "outputs", "experiments")
OUTDIR = os.path.join(ROOT, "outputs", "analysis")

files = []
for fn in sorted(os.listdir(EXP)):
    if not re.match(r"^verify_r[56]_s\d+\.json$", fn):
        continue
    p = os.path.join(EXP, fn)
    st = os.stat(p)
    with open(p, encoding="utf-8") as f:
        d = json.load(f)
    E = d.get("E", [])
    files.append({
        "file": fn,
        "rank": int(d["rank"]),
        "seed": int(d["seed"]),
        "E0": E[0] if E else None,
        "dE": (E[-1] - E[0]) if len(E) >= 2 else None,
        "epochs": d.get("epochs"),
        "mtime": datetime.fromtimestamp(st.st_mtime).isoformat(timespec="seconds"),
        "ctime": datetime.fromtimestamp(st.st_ctime).isoformat(timespec="seconds"),
        "mtime_ts": st.st_mtime,
        "note": d.get("note"),
    })

files.sort(key=lambda x: x["mtime_ts"])

print("=" * 100)
print("verify_r{5,6}_s*.json IN FILE-MODIFICATION ORDER (MTIME)")
print("=" * 100)
print("%-26s %-5s %-6s %-9s %-21s %s" % ("file", "rank", "seed", "E0", "mtime", "note?"))
for f in files:
    print("%-26s %-5s %-6s %-9s %-21s %s"
          % (f["file"], f["rank"], f["seed"], f["E0"], f["mtime"],
             "YES" if f["note"] else ""))

PAPER_SEEDS = [42, 123, 999]
TEN_SEEDS = [7, 17, 27, 37, 42, 47, 57, 67, 123, 999]

by_r5 = [f for f in files if f["rank"] == 5]
by_r6 = [f for f in files if f["rank"] == 6]

print("\n" + "=" * 100)
print("WERE THE PAPER'S 3 SEEDS THE EARLIEST-RUN?")
print("=" * 100)
for tag, group in (("r=5", by_r5), ("r=6", by_r6)):
    ordered = sorted(group, key=lambda x: x["mtime_ts"])
    earliest = [f["seed"] for f in ordered[:3]]
    print("  %s mtime order of seeds : %s" % (tag, [f["seed"] for f in ordered]))
    print("  %s earliest-3 seeds     : %s" % (tag, earliest))
    print("  %s earliest-3 == paper's: %s" % (tag, set(earliest) == set(PAPER_SEEDS)))
    # ctime order too
    oc = sorted(group, key=lambda x: x["ctime"])
    print("  %s ctime order of seeds : %s" % (tag, [f["seed"] for f in oc]))

print("\n" + "=" * 100)
print("E0 CLUSTER vs MTIME")
print("=" * 100)
for tag, group in (("r=5", by_r5), ("r=6", by_r6)):
    print("  %s:" % tag)
    for f in sorted(group, key=lambda x: x["mtime_ts"]):
        print("     %-21s E0=%-9s seed=%-5s" % (f["mtime"], f["E0"], f["seed"]))

# is E0 contiguous in time?
print("\n  Within each rank, is E0 a contiguous block in mtime order?")
contig = {}
for tag, group in (("r5", by_r5), ("r6", by_r6)):
    seq = [f["E0"] for f in sorted(group, key=lambda x: x["mtime_ts"])]
    flips = sum(1 for a, b in zip(seq, seq[1:]) if a != b)
    contig[tag] = {"E0_sequence_in_mtime_order": seq, "n_transitions": flips,
                   "contiguous_block": flips <= 1}
    print("    %s: %s  transitions=%d  contiguous=%s"
          % (tag, seq, flips, flips <= 1))

# the paper's own drivers hard-code the seeds -> evidence about *intent*
drivers = {}
for rel in ("paper3/scripts/run_full_sweep.py", "paper3/scripts/run_e4_counterfactual.py"):
    p = os.path.join(ROOT, rel)
    if os.path.exists(p):
        txt = open(p, encoding="utf-8", errors="replace").read()
        m = re.search(r"SEEDS\s*=\s*\[([^\]]*)\]", txt)
        m2 = re.search(r"for s in \[([^\]]*)\]", txt)
        drivers[rel] = {
            "SEEDS_literal": m.group(1).strip() if m else None,
            "loop_seeds": m2.group(1).strip() if m2 else None,
        }

out = {
    "meta": {
        "script": "tools/_p44n_seed_provenance.py",
        "purpose": ("R3.17 follow-up: was the paper's 3-seed set the first run or a "
                    "selection out of ten?  Decide from mtime/ctime + E0 + note fields."),
        "caveat": ("file mtime/ctime are filesystem metadata; a re-run OVERWRITES the "
                   "same filename, so mtime reflects the LAST write.  verify_r5_s42.json "
                   "explicitly says it was 'restored 2026-09-09 after a transformers-4.57 "
                   "reproducibility run temporarily overwrote this file'."),
    },
    "files_in_mtime_order": files,
    "paper_seeds": PAPER_SEEDS,
    "ten_seeds": TEN_SEEDS,
    "earliest_three": {
        "r5": [f["seed"] for f in sorted(by_r5, key=lambda x: x["mtime_ts"])[:3]],
        "r6": [f["seed"] for f in sorted(by_r6, key=lambda x: x["mtime_ts"])[:3]],
    },
    "earliest_three_equals_paper_seeds": {
        "r5": set(f["seed"] for f in sorted(by_r5, key=lambda x: x["mtime_ts"])[:3]) == set(PAPER_SEEDS),
        "r6": set(f["seed"] for f in sorted(by_r6, key=lambda x: x["mtime_ts"])[:3]) == set(PAPER_SEEDS),
    },
    "E0_contiguity_in_time": contig,
    "driver_seed_literals": drivers,
}
dst = os.path.join(OUTDIR, "p3_seed_provenance.json")
with open(dst, "w", encoding="utf-8") as f:
    json.dump(out, f, indent=1, ensure_ascii=False)

print("\n" + "=" * 100)
print("PAPER'S OWN DRIVERS: hard-coded seed lists")
print("=" * 100)
print(json.dumps(drivers, indent=1))
print("\nwrote", dst)
