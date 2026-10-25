"""Measure the run-to-run spread of every official-IGU arm (2026-10-25 cloud round).

Motivation (measured, not assumed): the SAME arm with byte-identical argv produced delta_E of
+250.5, +181.0 and +182.5 in three executions. `paper3/scripts/run_training.py` seeds torch but does
not enable `use_deterministic_algorithms` / `cudnn.deterministic`, and 4-bit bitsandbytes
dequantisation plus cuBLAS reductions are not bit-reproducible. The spread is the same order as both
the pre-declared equivalence margin (196.05 = 5% of E(0)) and the archived
official-minus-reimplementation gap (92.5), so a single-seed delta_E must not be presented as a
reproducible reading. This script produces the evidence for that statement.

Method
------
1. Snapshot the PRIMARY archive `outputs/analysis/p3_official_igu_run.json` and the six primary arm
   archives (`paper3/scripts/outputs/experiments/verify_r1_s<seed>_bcexplicit_*.json`).
2. For each replicate pass: **restore the primary archives first** (so the pinned anchors are intact
   and `verify_inputs()` cannot refuse), then run
   `_p1639 --run-official --stage train --force`, which retrains all six arms and rewrites `runs[]`
   with six fresh delta_E values; snapshot them; **restore the primaries again immediately**.
3. Write `outputs/analysis/p3_official_igu_replicates.json`: per arm the primary delta_E, the
   replicate values, max-min, mean and sample sd.

Anchor protection (2026-10-25): `reimpl_igu_style` seed 42 writes the PINNED S27 anchor
`verify_r1_s42_bcexplicit_v11_s1_m3_d1.json` (delta_E 333.0) and `verify_inputs()` asserts it, so a
forced retrain transiently drifts it. That is why the primaries are restored after *every* pass; a
failed restore aborts the run. The first version restored only at the very end and the second pass
aborted with `archived reimplementation arm delta_E +265.5 FAIL / refusing to run` - the guard in the
tool worked, but a pass of measurements was lost.

Usage (on the instance, from /root/autodl-tmp/p3work):
    python tools/_p1646_p3_arm_replicates.py --passes 2 [--apply]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARCHIVE = os.path.join(REPO, "outputs", "analysis", "p3_official_igu_run.json")
OUT = os.path.join(REPO, "outputs", "analysis", "p3_official_igu_replicates.json")
TOOL = os.path.join(REPO, "tools", "_p1639_p3_official_igu.py")
# The two archives verify_inputs() pins; they must never be left drifted.
PINNED_ANCHORS = {
    "verify_r1_s42_bcexplicit_v11_s1_m3_d1.json": 333.0,
    "verify_r1_s42_bcexplicit_v12_s1_m2_d1.json": 240.5,
}


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def key(rec):
    return "%s|%s" % (rec.get("config"), rec.get("seed"))


def read_runs():
    with open(ARCHIVE, encoding="utf-8") as fh:
        return json.load(fh).get("runs") or []


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--passes", type=int, default=2)
    ap.add_argument("--python", default=sys.executable)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    runs = read_runs()
    if len(runs) != 6:
        raise SystemExit("primary archive has %d arms, expected 6 -- consolidate first" % len(runs))
    arm_paths = {}
    for r in runs:
        p = r["path"] if os.path.isabs(r["path"]) else os.path.join(REPO, r["path"])
        if not os.path.isfile(p):
            raise SystemExit("primary arm archive missing: %s" % r["path"])
        arm_paths[key(r)] = p

    # ---- snapshot the primary bytes ----
    archive_bak = ARCHIVE + ".primary.bak"
    shutil.copy2(ARCHIVE, archive_bak)
    arm_bak = {}
    for k, p in arm_paths.items():
        b = p + ".primary.bak"
        shutil.copy2(p, b)
        arm_bak[k] = b
    before = {k: sha256_of(p) for k, p in arm_paths.items()}
    anchor_dir = os.path.dirname(next(iter(arm_paths.values())))
    anchor_hashes = {}
    for name in PINNED_ANCHORS:
        ap_ = os.path.join(anchor_dir, name)
        if not os.path.isfile(ap_):
            raise SystemExit("pinned anchor missing: %s" % name)
        anchor_hashes[name] = sha256_of(ap_)
        shutil.copy2(ap_, ap_ + ".anchor.bak")
    print("== snapshot taken: %d arms, %d pinned anchors ==" % (len(arm_paths), len(anchor_hashes)))
    for name, h in anchor_hashes.items():
        print("  anchor %-46s %s" % (name, h))

    def restore_primary(label):
        shutil.copy2(archive_bak, ARCHIVE)
        for k, b in arm_bak.items():
            shutil.copy2(b, arm_paths[k])
        for name in PINNED_ANCHORS:
            p = os.path.join(anchor_dir, name)
            shutil.copy2(p + ".anchor.bak", p)
        bad = [k for k in before if sha256_of(arm_paths[k]) != before[k]]
        bad_anchor = [n for n, h in anchor_hashes.items()
                      if sha256_of(os.path.join(anchor_dir, n)) != h]
        if bad or bad_anchor:
            raise SystemExit("%s: restore mismatch arms=%s anchors=%s" % (label, bad, bad_anchor))
        print("  %s: primary arms + anchors restored byte-identically" % label)

    replicates = {}
    passes_completed = 0
    try:
        for i in range(args.passes):
            restore_primary("pre-pass %d" % (i + 1))
            print("\n== replicate pass %d/%d (--force retrains all six; anchors re-restored after) =="
                  % (i + 1, args.passes), flush=True)
            cmd = [args.python, TOOL, "--run-official", "--stage", "train", "--force"]
            print("  $ %s" % " ".join(cmd), flush=True)
            rc = subprocess.run(cmd, cwd=REPO).returncode
            if rc != 0:
                print("  !! pass %d exited %d; keeping the measurements already taken" % (i + 1, rc))
                break
            vals = {key(r): float(r["delta_E"]) for r in read_runs()}
            if len(vals) != 6:
                print("  !! pass %d produced %d records; discarding it" % (i + 1, len(vals)))
                break
            for k, v in vals.items():
                replicates.setdefault(k, []).append(v)
            passes_completed += 1
            print("  pass delta_E: %s" % json.dumps(vals, sort_keys=True), flush=True)
    finally:
        restore_primary("final")

    rows = []
    for r in runs:
        k = key(r)
        prim = float(r["delta_E"])
        reps = replicates.get(k, [])
        vals = [prim] + reps
        sd = (sum((v - sum(vals) / len(vals)) ** 2 for v in vals) / (len(vals) - 1)) ** 0.5 \
            if len(vals) > 1 else None
        rows.append({"config": r["config"], "seed": r["seed"],
                     "primary_delta_E": prim, "replicate_delta_E": reps,
                     "all_values": vals, "n_runs": len(vals),
                     "max_minus_min": (max(vals) - min(vals)) if len(vals) > 1 else None,
                     "mean": sum(vals) / len(vals), "sd": sd,
                     "arm_archive": r["path"], "arm_sha256": r.get("sha256")})

    spreads = [x["max_minus_min"] for x in rows if x["max_minus_min"] is not None]
    payload = {
        "experiment": "p3_official_igu_replicates",
        "script": "tools/_p1646_p3_arm_replicates.py",
        "purpose": ("quantify run-to-run spread of delta_E for the six arms; 4-bit training is not "
                    "bit-reproducible, so a single-seed delta_E is not a reproducible reading"),
        "cache_defeat_method": ("--force (retrains despite an existing archive and ignores runs[] "
                                "entries); the primaries and both pinned anchors are restored "
                                "byte-identically before and after every pass"),
        "primary_preserved": True,
        "passes_requested": args.passes, "passes_completed": passes_completed,
        "pinned_anchors_sha256_before": anchor_hashes,
        "pinned_anchors_sha256_after": {n: sha256_of(os.path.join(anchor_dir, n))
                                       for n in PINNED_ANCHORS},
        "arms": rows,
        "summary": {"n_arms": len(rows), "n_replicate_passes": passes_completed,
                    "max_spread_across_arms": max(spreads) if spreads else None,
                    "mean_spread_across_arms": (sum(spreads) / len(spreads)) if spreads else None,
                    "declared_equivalence_margin": 196.05,
                    "archived_official_minus_reimpl_gap": 92.5},
        "how_to_reproduce": ("python tools/_p1646_p3_arm_replicates.py --passes 2 --apply  "
                             "(on the instance, after the six-arm consolidation)"),
    }
    print("\n== per-arm spread ==")
    for x in rows:
        print("  %-24s seed %-4s primary %+7.1f  replicates %s  spread %s  sd %s"
              % (x["config"], x["seed"], x["primary_delta_E"],
                 ["%+.1f" % v for v in x["replicate_delta_E"]],
                 ("%.1f" % x["max_minus_min"]) if x["max_minus_min"] is not None else "n/a",
                 ("%.1f" % x["sd"]) if x["sd"] is not None else "n/a"))
    print("  passes completed: %d/%d  |  max spread across arms: %s"
          % (passes_completed, args.passes, payload["summary"]["max_spread_across_arms"]))
    print("  anchors after: %s" % json.dumps(payload["pinned_anchors_sha256_after"]))

    if not args.apply:
        print("\n(preview; pass --apply to write %s)" % OUT)
        return 0
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=1)
        fh.write("\n")
    print("\n  wrote %s" % OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
