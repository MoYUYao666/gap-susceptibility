# -*- coding: utf-8 -*-
r"""Compare the 2-epoch main grid with the 6-epoch ablation, per dataset and provenance arm.

Answers the reviewer objection that the provenance ordering is an artefact of short training: if the ordering is the
same after three times as much training, the ordering is not a training-length artefact.

Outputs
  analysis/epoch_ablation.json
  analysis/epoch_ablation.md
"""
import glob
import io
import json
import os
import statistics as st

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARMS = ["human", "templated", "metadata"]


def load(runs_dir, budget="10000", site="both"):
    out = {}
    for p in glob.glob(os.path.join(ROOT, "runs", runs_dir, "*.json")):
        rec = json.loads(io.open(p, encoding="utf-8").read())
        name = os.path.basename(p)[:-5]
        parts = name.split("_")
        seed = int(parts[-1][1:])
        if site != parts[-2] or budget != parts[-3]:
            continue
        arm = parts[-4]
        ds = "_".join(parts[:-4])
        out.setdefault((ds, arm), []).append(rec)
    return out


def summarise(cells):
    return {k: {"R@1_i2t": round(st.mean([r["metrics"]["R@1_i2t"] for r in v]), 4),
                "R@1_t2i": round(st.mean([r["metrics"]["R@1_t2i"] for r in v]), 4),
                "n": len(v)}
            for k, v in cells.items()}


def main():
    main2 = summarise(load("full_10k"))
    ablate6 = summarise(load("epoch_ablation"))
    rows = []
    for key in sorted(set(main2) & set(ablate6), key=lambda k: (k[0], ARMS.index(k[1]) if k[1] in ARMS else 9)):
        rows.append({"dataset": key[0], "arm": key[1],
                     "epochs2": main2[key], "epochs6": ablate6[key]})
    # ordering check within each dataset
    ordering = {}
    for ds in {r["dataset"] for r in rows}:
        d = {r["arm"]: r for r in rows if r["dataset"] == ds}
        if len(d) < 3:
            continue
        order2 = sorted(d, key=lambda a: -d[a]["epochs2"]["R@1_i2t"])
        order6 = sorted(d, key=lambda a: -d[a]["epochs6"]["R@1_i2t"])
        ordering[ds] = {"epochs2": order2, "epochs6": order6, "same_ordering": order2 == order6}
    out = {"note": "same grid, 2 versus 6 epochs; site = both; budget = 10k pairs", "rows": rows,
           "ordering": ordering}
    os.makedirs(os.path.join(ROOT, "analysis"), exist_ok=True)
    io.open(os.path.join(ROOT, "analysis", "epoch_ablation.json"), "w", encoding="utf-8",
            newline="").write(json.dumps(out, indent=1))
    md = ["# Training-length ablation (2 versus 6 epochs)", "",
          "If the provenance ordering survives three times the training, it is not a training-length artefact.", "",
          "| dataset | arm | R@1 2ep | R@1 6ep | change |", "|---|---|---|---|---|"]
    for r in rows:
        a, b = r["epochs2"]["R@1_i2t"], r["epochs6"]["R@1_i2t"]
        md.append("| %s | %s | %.4f | %.4f | %+.4f |" % (r["dataset"], r["arm"], a, b, b - a))
    md += ["", "Ordering:", ""]
    for ds, v in ordering.items():
        md.append("- %s: 2ep %s / 6ep %s -> %s" % (ds, " > ".join(v["epochs2"]), " > ".join(v["epochs6"]),
                                                  "unchanged" if v["same_ordering"] else "CHANGED"))
    io.open(os.path.join(ROOT, "analysis", "epoch_ablation.md"), "w", encoding="utf-8", newline="").write("\n".join(md) + "\n")
    print("wrote analysis/epoch_ablation.{json,md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
