# -*- coding: utf-8 -*-
"""Within-dataset real-checkpoint matched pairs (same training corpus, different seed/epoch)."""
import io
import json

d = json.load(io.open("outputs/a1_epoch_sweep.json", encoding="utf-8"))
ck = [c for c in d["checkpoints"] if c.get("CG_flickr_val") is not None and c.get("top1_5k") is not None]
by_ds = {}
for c in ck:
    by_ds.setdefault(c["dataset"], []).append(c)
for ds, rows in sorted(by_ds.items()):
    best = None
    for i in range(len(rows)):
        for j in range(i + 1, len(rows)):
            dcg = abs(rows[i]["CG_flickr_val"] - rows[j]["CG_flickr_val"])
            dtop = abs(rows[i]["top1_5k"] - rows[j]["top1_5k"])
            if dcg <= 0.01 and (best is None or dtop > best[0]):
                best = (dtop, dcg, rows[i], rows[j])
    print(f"{ds}: n={len(rows)}", end="")
    if best:
        t, g, a, b = best
        print(f" | widest within-dataset pair at |dCG|<=0.01: {t:.2f} pts (dCG={g:.4f}) "
              f"[{a['seed']}/ep{a['epoch']} vs {b['seed']}/ep{b['epoch']}]")
    else:
        print(" | no pair within 0.01")
