"""Collect the exact numbers the A23 revision cover letter may quote, with their field paths.

The letter must not invent anything: every value it prints has to come from
`outputs/analysis/a23_multiencoder_transfer.json` (with a field path), or from
`docs/a23_21unit_switch_notes.md` / `docs/a23_transfer_claim_rewrite_notes.md`. This script reads the
archive and prints each value next to the field path it came from, including the survivor breakdown
that the summary does not pre-group (recomputed by walking `transfer.pairs[*].by_statistic[*].bootstrap`).

Usage:
    python tools/_p1666_a23_letter_facts.py
"""

from __future__ import annotations

import collections
import io
import json
import sys

ARCHIVE = "outputs/analysis/a23_multiencoder_transfer.json"


def main() -> int:
    d = json.load(io.open(ARCHIVE, encoding="utf-8"))
    t, c, lim = d["transfer"], d["conclusion"], d["limits"]
    print("== headline counts ==")
    for path, val in [
        ("transfer.n_units", t["n_units"]),
        ("transfer.n_pairs", t["n_pairs"]),
        ("transfer.self_pairs", t["self_pairs"]),
        ("transfer.cross_unit_pairs", t["cross_unit_pairs"]),
        ("transfer.cross_corpus_pairs", t["cross_corpus_pairs"]),
        ("conclusion.n_encoders", c["n_encoders"]),
        ("conclusion.n_corpora", c["n_corpora"]),
        ("conclusion.n_statistics_per_pair", c["n_statistics_per_pair"]),
        ("conclusion.n_scored_entries_cross_unit", c["n_scored_entries_cross_unit"]),
        ("conclusion.n_entries_above_chance", c["n_entries_above_chance"]),
        ("conclusion.n_entries_surviving_bootstrap", c["n_entries_surviving_bootstrap"]),
    ]:
        print("  %-48s %s" % (path, val))

    print("\n== survivors, recomputed by walking transfer.pairs[*].by_statistic[*].bootstrap ==")
    print("   (self-pairs are excluded: the archive states they are reported but never counted as a")
    print("    transfer, and the claim is evaluated on the cross-unit entries -- see")
    print("    transfer.summary.self_pairs_excluded_from_the_claim)")
    surv = []
    for p in t["pairs"]:
        if p.get("self_pair"):
            continue
        for stat, ent in p["by_statistic"].items():
            b = ent.get("bootstrap") or {}
            if b.get("survives"):
                surv.append({"source": p["source"], "target": p["target"],
                             "target_encoder": p["target_encoder"],
                             "target_corpus": p["target_corpus"], "statistic": stat,
                             "target_BA": ent.get("target_BA"),
                             "source_fit_BA": ent.get("source_fit_BA"),
                             "p_delta_gt_zero": b.get("p_delta_gt_zero")})
    print("  n survivors (cross-unit)               :", len(surv),
          "| archive conclusion.n_entries_surviving_bootstrap =",
          c["n_entries_surviving_bootstrap"])
    print("  by target_encoder                      :", dict(collections.Counter(s["target_encoder"] for s in surv)))
    print("  by target_corpus                       :", dict(collections.Counter(s["target_corpus"] for s in surv)))
    print("  by statistic                           :", dict(collections.Counter(s["statistic"] for s in surv)))
    sigma = [s for s in surv if "sigma" in s["statistic"]]
    print("  survivors whose statistic is sigma-relative (name contains 'sigma'):", len(sigma))

    print("\n== best surviving pair (conclusion.best_surviving_pair) ==")
    for k in ("source", "target", "statistic", "target_BA", "source_fit_BA", "chance", "paired", "survives"):
        print("  conclusion.best_surviving_pair.%-16s %s" % (k, c["best_surviving_pair"].get(k)))

    print("\n== headline string (conclusion.headline) ==")
    print(" ", c.get("headline"))

    print("\n== encoder top-1 vs chance (encoders.<name>.corpora.<corpus>) ==")
    for enc in ("remoteclip", "siglip-base-patch16-224", "oceanclip", "clip-vit-large-patch14"):
        block = d["encoders"].get(enc, {}).get("corpora") or {}
        for corpus, v in block.items():
            top1 = None
            for key in ("top1_percent", "top_1_percent", "top1", "top_1"):
                if key in v:
                    top1 = v[key]
                    break
            if top1 is None:
                # look one level down: probe_stats / frozen_row / reproduction
                for sub in ("probe_stats", "frozen_row", "reproduction", "correlations"):
                    node = v.get(sub)
                    if isinstance(node, dict):
                        for k2, v2 in node.items():
                            if "top1" in k2.lower() or "top_1" in k2.lower():
                                top1 = (sub + "." + k2, v2)
                                break
                    if top1:
                        break
            print("  encoders.%s.corpora.%s  top1=%s  chance=%s"
                  % (enc, corpus, top1, v.get("chance_percent")))

    print("\n== limits.list (the manuscript's limitation list, 8 entries) ==")
    for i, item in enumerate(lim["list"], 1):
        print("  %d. %s" % (i, item))
    return 0


if __name__ == "__main__":
    sys.exit(main())
