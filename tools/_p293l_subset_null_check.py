# -*- coding: utf-8 -*-
r"""Is a seed-subset match at 3 decimals evidence?  Quantify the null, independently.

The Lead's `tools/_p330_subset_overfit_check.py` reports that of 4581 three-seed subsets, 17-43
round to any given target (0.679 / 0.651 / 0.621), i.e. roughly 1%.  If true, a subset match
carries no provenance information at that precision and must not be reported as a source.  This
recomputes the null directly from the archive and also spells out the search space, so the number
in the report is checkable rather than quoted.

Outputs a JSON next to the other provenance artefacts.
"""
from __future__ import annotations

import glob
import itertools
import json
import statistics
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "dinov2_hetero" / "subset_null_check.json"

TARGETS = {"0.679": 0.679, "0.651": 0.651, "0.621": 0.621}


def main():
    groups = defaultdict(list)
    for f in glob.glob(str(REPO / "outputs" / "**" / "results.json"), recursive=True):
        try:
            r = json.loads(Path(f).read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            continue
        tm = r.get("final_task_metrics") or {}
        if tm.get("R@1") is None:
            continue
        rel = str(Path(f).relative_to(REPO)).replace("\\", "/")
        run_dir = rel.rsplit("/", 1)[0].rsplit("/seed", 1)[0]
        groups[(run_dir, r.get("n_trainable_params"))].append(tm["R@1"])

    # every subset of size 3..5 across every group with enough seeds
    means = []
    per_size = defaultdict(int)
    for runs in groups.values():
        for k in range(3, min(5, len(runs)) + 1):
            for sub in itertools.combinations(runs, k):
                means.append(sum(sub) / len(sub))
                per_size[k] += 1

    rounded = [round(m, 3) for m in means]
    distinct = sorted(set(rounded))
    hit_counts = {name: sum(1 for x in rounded if x == t) for name, t in TARGETS.items()}
    rate = {name: c / len(means) for name, c in hit_counts.items()}

    out = {
        "script": "tools/_p293l_subset_null_check.py",
        "question": ("does reproducing a published 3-decimal R@1 through a seed subset of size "
                     "3-5 constitute evidence of provenance?"),
        "n_groups": len(groups),
        "n_subsets": len(means),
        "subsets_by_size": dict(sorted(per_size.items())),
        "subset_mean_range": [round(min(means), 6), round(max(means), 6)],
        "distinct_3dp_values_covered": len(distinct),
        "targets": TARGETS,
        "subsets_matching_each_target": hit_counts,
        "hit_rate_per_target": {k: round(v, 5) for k, v in rate.items()},
        "expected_hit_rate_if_uniform_over_3dp_grid": None,
        "verdict": None,
    }
    # the direct null: if subset means were spread evenly over the 3dp grid they cover, the
    # chance of hitting any one value is 1 / (number of distinct 3dp values covered)
    out["expected_hit_rate_if_uniform_over_3dp_grid"] = round(1.0 / len(distinct), 5)
    out["verdict"] = (
        "A subset match is not evidence. %d subsets of size 3-5 exist; their means round to only "
        "%d distinct 3-decimal values, so a uniform spread over that grid would hit any chosen "
        "target about %.2f%% of the time. Observed hit rates for the three published values are "
        "%s. Reporting a subset match as the source of a published cell would therefore be a "
        "~1-in-%d coincidence, and these artefacts must be described as NOT reproducible from any "
        "group's complete seed set."
        % (len(means), len(distinct),
           100.0 / len(distinct),
           ", ".join("%s: %d subsets (%.2f%%)" % (k, v, 100 * rate[k])
                     for k, v in hit_counts.items()),
           len(distinct)))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, ensure_ascii=False)

    print(json.dumps({k: v for k, v in out.items() if k != "verdict"}, indent=2))
    print("\n" + out["verdict"])
    print("[ok] wrote", OUT)


if __name__ == "__main__":
    main()
