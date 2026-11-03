# -*- coding: utf-8 -*-
"""Does a pair of REAL fine-tuned checkpoints exist with matched gap but different accuracy?

The synthetic perturbation families are the paper's most attackable point ("not real fine-tuning"). The archived
per-epoch checkpoints carry both a gap (CG_flickr_val) and a measured top-1, so we can ask directly whether real
checkpoints reproduce the dissociation.
"""
import io
import json
import statistics

d = json.load(io.open("outputs/a1_epoch_sweep.json", encoding="utf-8"))
ck = [c for c in d["checkpoints"] if c.get("CG_flickr_val") is not None and c.get("top1_5k") is not None]
print(f"real checkpoints with (CG, top-1): {len(ck)}")
rows = [(c["CG_flickr_val"], c["top1_5k"], c["dataset"], c["seed"], c["epoch"]) for c in ck]
print(f"  CG range {min(r[0] for r in rows):.4f}..{max(r[0] for r in rows):.4f}")
print(f"  top-1 range {min(r[1] for r in rows):.2f}..{max(r[1] for r in rows):.2f}")

best = None
for i in range(len(rows)):
    for j in range(i + 1, len(rows)):
        dcg = abs(rows[i][0] - rows[j][0])
        dtop = abs(rows[i][1] - rows[j][1])
        if dcg <= 0.03 and (best is None or dtop > best[0]):
            best = (dtop, dcg, rows[i], rows[j])
if best:
    dtop, dcg, a, b = best
    print(f"\nwidest real-checkpoint pair at |dCG|<=0.03: {dtop:.2f} points (dCG={dcg:.4f})")
    print(f"  A: {a[2]}/seed{a[3]}/ep{a[4]} CG={a[0]:.4f} top1={a[1]:.2f}")
    print(f"  B: {b[2]}/seed{b[3]}/ep{b[4]} CG={b[0]:.4f} top1={b[1]:.2f}")
else:
    print("no matched-gap pair among real checkpoints")
# how many pairs within tighter tolerance
for tol in (0.01, 0.02, 0.03, 0.05):
    pairs = [(abs(rows[i][1] - rows[j][1])) for i in range(len(rows)) for j in range(i + 1, len(rows))
             if abs(rows[i][0] - rows[j][0]) <= tol]
    print(f"  tol {tol}: {len(pairs)} pairs, max top-1 difference {max(pairs):.2f}" if pairs else f"  tol {tol}: no pairs")
