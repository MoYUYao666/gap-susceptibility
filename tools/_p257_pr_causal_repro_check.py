# -*- coding: utf-8 -*-
r"""Reproducibility cross-check for the parameter-matched perturbation experiment.

Compares the 5-seed pass (`outputs/analysis/_p255_run1_5seed_superseded.json`, produced by
`tools/_p255_relative_perturbation.py` before the seed/level grid was extended) against the final
10-seed pass (`outputs/analysis/pr_relative_perturbation.json`) on every condition present in
both. Each condition is seeded independently, so the overlapping conditions must reproduce
BIT-FOR-BIT; anything else means the pipeline is not deterministic and the archived numbers
cannot be trusted.

Ground truth for the comparison: `rows[*].R1.*`, `rows[*].CG`, `rows[*].DG`,
`rows[*].drop_pct_i2t`, `rows[*].rel_injected`, `rows[*].dW_frob_total`.

Output: outputs/analysis/pr_relative_perturbation_repro_check.json
Exit code: 0 if every overlapping condition matches to <= 1e-9, else 2.

    python tools\_p257_pr_causal_repro_check.py [--tol 1e-9]
"""
from __future__ import annotations

import argparse
import io
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RUN1 = REPO / "outputs" / "analysis" / "_p255_run1_5seed_superseded.json"
RUN2 = REPO / "outputs" / "analysis" / "pr_relative_perturbation.json"
OUT = REPO / "outputs" / "analysis" / "pr_relative_perturbation_repro_check.json"

FIELDS = ["CG", "DG", "drop_pct_i2t", "rel_injected", "dW_frob_total",
          "R1.R@1_i2t", "R1.R@1_t2i", "R1.R@5_i2t", "R1.R@10_i2t"]


def get(row, path):
    cur = row
    for p in path.split("."):
        cur = cur[p]
    return cur


def key(row):
    """(protocol, tower, seed, level) -- level rounded to kill float-noise mismatches."""
    return (row["protocol"], row["tower"], row["seed"], round(float(row["level"]), 12))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tol", type=float, default=1e-9)
    args = ap.parse_args()

    a = json.load(io.open(RUN1, encoding="utf-8"))
    b = json.load(io.open(RUN2, encoding="utf-8"))
    assert b["meta"]["status"] == "complete", "run 2 is not complete yet"
    ra = [r for r in a["rows"] if "error" not in r]
    rb = {key(r): r for r in b["rows"] if "error" not in r}
    assert len(rb) == len([r for r in b["rows"] if "error" not in r]), \
        "duplicate condition keys in run 2 -- the comparison would be incomplete"

    compared, missing, diffs = 0, [], {f: 0.0 for f in FIELDS}
    worst = {f: None for f in FIELDS}
    for row in ra:
        new = rb.get(key(row))
        if new is None:
            missing.append({"protocol": row["protocol"], "tower": row["tower"],
                            "level": row["level"], "seed": row["seed"]})
            continue
        compared += 1
        for f in FIELDS:
            d = abs(float(get(row, f)) - float(get(new, f)))
            if d > diffs[f]:
                diffs[f] = d
                worst[f] = {"protocol": row["protocol"], "tower": row["tower"],
                            "level": row["level"], "seed": row["seed"],
                            "run1": float(get(row, f)), "run2": float(get(new, f))}

    bad = {f: d for f, d in diffs.items() if d > args.tol}
    payload = {
        "script": "tools/_p257_pr_causal_repro_check.py",
        "purpose": "each condition is seeded independently, so conditions present in both passes "
                   "must reproduce bit-for-bit; this checks the pipeline is deterministic",
        "run1": str(RUN1.relative_to(REPO)), "run1_status": a["meta"]["status"],
        "run1_seeds": a["meta"]["seeds"], "run1_script_sha1": a["meta"]["script_sha1"],
        "run2": str(RUN2.relative_to(REPO)), "run2_status": b["meta"]["status"],
        "run2_seeds": b["meta"]["seeds"], "run2_script_sha1": b["meta"]["script_sha1"],
        "script_sha1_identical": a["meta"]["script_sha1"] == b["meta"]["script_sha1"],
        "n_run1_rows": len(ra), "n_compared": compared, "n_not_rerun_in_run2": len(missing),
        "not_rerun": missing,
        "max_abs_diff_per_field": diffs,
        "worst_case_per_field": worst,
        "tolerance": args.tol,
        "verdict": "PASS: every overlapping condition reproduced exactly" if not bad
                   else "FAIL: fields exceed tolerance: %s" % list(bad),
        "fields_exceeding_tolerance": bad,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    io.open(OUT, "w", encoding="utf-8", newline="").write(
        json.dumps(payload, ensure_ascii=False, indent=1))
    print("compared %d conditions; %d present only in run 1: %s"
          % (compared, len(missing), [(m["protocol"], m["level"]) for m in missing[:8]]))
    for f in FIELDS:
        print("  max |diff| %-14s = %.3e%s" % (f, diffs[f], worst[f] or ""))
    print(payload["verdict"])
    print("wrote", OUT.relative_to(REPO))
    return 0 if not bad else 2


if __name__ == "__main__":
    raise SystemExit(main())
