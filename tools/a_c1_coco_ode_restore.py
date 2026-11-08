# -*- coding: utf-8 -*-
"""Paper A C1: analyse the restored COCO ODE trajectories (2026-11-08).

Scans `outputs/coco_restore/r<rank>/<tag>/seed42/dg_star_history.json` (new runs on the cloud), fits the same
ODE model used by `tools/_p1_ledger.py::grid_fit`, and compares overlapping cells with the archived trajectories in
`outputs/coco_sweep_dgstar/`.  Writes `outputs/analysis/a_c1_coco_ode_restore_2026-11-08.json`.
"""
import glob
import importlib.util
import io
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "outputs", "analysis", "a_c1_coco_ode_restore_2026-11-08.json")


def load_grid_fit():
    p = os.path.join(REPO, "tools", "_p1_ledger.py")
    spec = importlib.util.spec_from_file_location("p1_ledger", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.grid_fit


def summarize_series(d):
    if not d or "epochs" not in d or "dg_star" not in d:
        return None
    if len(d["epochs"]) < 5:
        return None
    grid_fit = load_grid_fit()
    A, B, R = grid_fit(d["epochs"], d["dg_star"])
    return {"n_epochs": len(d["epochs"]), "A": round(float(A), 6), "B": round(float(B), 6),
            "R2": round(float(R), 6), "dg_star_initial": round(float(d["dg_star"][0]), 6),
            "dg_star_final": round(float(d["dg_star"][-1]), 6)}


def scan(root, pattern="**/dg_star_history.json"):
    out = {}
    for p in sorted(glob.glob(os.path.join(root, pattern), recursive=True)):
        rel = os.path.relpath(p, root)
        parts = rel.split(os.sep)
        # expect r<rank>/<tag>/seed<N>/dg_star_history.json
        key = "/".join(parts[:-1])
        try:
            d = json.load(io.open(p, encoding="utf-8"))
        except Exception:
            continue
        s = summarize_series(d)
        if s:
            out[key] = s
    return out


def main():
    new = scan(os.path.join(REPO, "outputs", "coco_restore"))
    old = scan(os.path.join(REPO, "outputs", "coco_sweep_dgstar"))
    rows = []
    for key in sorted(new):
        rows.append({"config": key, **new[key]})
    overlapping = []
    for key in sorted(set(new) & set(old)):
        overlapping.append({"config": key, "new": new[key], "archived": old[key],
                             "delta_R2": round(new[key]["R2"] - old[key]["R2"], 6)})
    report = {
        "generated": "2026-11-08",
        "note": ("C1 restoration on the cloud instance: COCO training corpus is the val2014 image set (40,504 images, "
                 "25k+ caption pairs) because train2014 was too large for the instance disk; 5000 caption pairs are "
                 "sampled by the loader, batch 128, 10 epochs, matching the archived run configuration (batch 128, "
                 "5000 samples, 10 epochs). The grid fit is `_p1_ledger.py::grid_fit`."),
        "new_runs": rows,
        "overlapping_with_archive": overlapping,
    }
    io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(report, indent=1, ensure_ascii=False))
    print(json.dumps(report, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
