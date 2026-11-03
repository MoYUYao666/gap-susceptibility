# -*- coding: utf-8 -*-
r"""A23: insert the second acoustic corpus (UATD detection crops) into the domain-matrix paragraph.

Reads outputs/analysis/a23_uatd_domain.json and appends one sentence after the order-preservation sentence. The wording
depends on the measured correlations (it reports the same relation only when the numbers support it).

    python tools/_p1384_a23_uatd_insert.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import os

TEX = os.path.join("paper_a2", "ext_partII_domains.tex")
JSON = os.path.join("outputs", "analysis", "a23_uatd_domain.json")
ANCHOR = "diagnostic the framework actually uses."


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    d = json.load(io.open(JSON, encoding="utf-8"))
    m = d["models"]
    r_tau = [m[k]["r_tau"] for k in ("bioclip", "oceanclip")]
    r_cg = [m[k]["r_CG"] for k in ("bioclip", "oceanclip")]
    same = all(x > 0.5 for x in r_tau)
    tops = [m[k]["top1_range"][1] for k in ("bioclip", "oceanclip")]
    chance = 100.0 / len(d["classes"])
    near_chance = max(tops) < 2 * chance
    if near_chance:
        sentence = (f" A second acoustic corpus built from UATD detection crops ({len(d['classes'])} classes, "
                    f"{d['n_test']} held-out crops) is class-wise out of distribution for both encoders: top-1 stays at "
                    f"{min(m[k]['top1_range'][0] for k in m)}--{max(tops):.1f}\\% against a {chance:.1f}\\% chance level, so "
                    f"neither $\\tau$ ($r={r_tau[0]:+.2f}$ and ${r_tau[1]:+.2f}$) nor the centroid gap "
                    f"($r={r_cg[0]:+.2f}$ and ${r_cg[1]:+.2f}$) can be read as an ordering relation. We treat the second "
                    f"corpus as the boundary of the diagnostic's domain rather than as a replication.")
    elif same:
        sentence = (f" Beyond the five-domain matrix, a second acoustic corpus built from UATD detection crops "
                    f"({len(d['classes'])} classes, {d['n_test']} held-out crops) shows the same ordering relation: $\\tau$ "
                    f"tracks accuracy at $r={r_tau[0]:+.2f}$ and ${r_tau[1]:+.2f}$ while the centroid gap gives "
                    f"$r={r_cg[0]:+.2f}$ and ${r_cg[1]:+.2f}$. The diagnostic is therefore not specific to one acoustic "
                    f"dataset, although the two corpora differ in sensor, class set and crop statistics.")
    else:
        sentence = (f" A second acoustic corpus built from UATD detection crops ({len(d['classes'])} classes, "
                    f"{d['n_test']} held-out crops) gives a weaker but consistent picture: $\\tau$ tracks accuracy at "
                    f"$r={r_tau[0]:+.2f}$ and ${r_tau[1]:+.2f}$ against $r={r_cg[0]:+.2f}$ and ${r_cg[1]:+.2f}$ for the "
                    f"centroid gap, so the ordering relation survives the change of corpus only partially and we treat "
                    f"the second corpus as an extension rather than a replication.")
    t = io.open(TEX, encoding="utf-8").read()
    if "UATD detection crops" in t:
        print("  already inserted")
        return 0
    assert t.count(ANCHOR) == 1, t.count(ANCHOR)
    t = t.replace(ANCHOR, ANCHOR + sentence, 1)
    print("  sentence:", sentence.strip()[:170], "...")
    if not a.apply:
        print("  (dry run)")
        return 0
    io.open(TEX, "w", encoding="utf-8", newline="").write(t)
    print("  written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
