# -*- coding: utf-8 -*-
"""
Turnkey updater for the strict-freeze control table once the joint arm has been run.

Usage (after running the joint configuration and regenerating the summary):

    python experiments/strict_freeze_control.py --tags both                # ~52 min/seed
    python experiments/strict_freeze_control.py --tags vision_only         # similar
    python tools/p1_strict_control_summary.py
    python tools/_p1_add_joint_rows.py
    (then recompile paper/main_nn.tex)

What it does, idempotently:
  * inserts a row per available configuration into Table~\\ref{tab:strictcontrol};
  * rewrites the two sentences that currently flag the control as one-armed, so the text
    matches whatever arms exist;
  * refuses to run if the summary JSON has no joint data.

It is safe to run before the joint arm exists: it then reports what is missing and changes
nothing.
"""
import io
import json
import os
import sys

ROOT = r"D:\Realdesktop\Wan\Important\New"
SC = os.path.join(ROOT, "paper", "sections", "strict_control.tex")
SUM = os.path.join(ROOT, "outputs", "analysis", "strict_control_summary.json")

LABELS = {"both": "Both", "vision_only": "Vision-only"}


def main():
    if not os.path.exists(SUM):
        print("missing %s; run tools/p1_strict_control_summary.py first" % SUM)
        return 1
    with io.open(SUM, encoding="utf-8") as fh:
        S = json.load(fh)
    cfgs = S["configs"]
    have = [(k, cfgs[k]) for k in ("both", "vision_only")
            if cfgs.get(k) and cfgs[k]["n_seeds"] >= 1]
    if not have:
        print("no joint runs in the summary yet -- nothing to insert")
        return 0

    src = io.open(SC, encoding="utf-8").read()
    rows = ""
    for key, e in have:
        xs = e["vision_nonzero_tensors"]
        rows += ("%s & %d & %s & $%+.3f \\pm %.3f$ & %.3f & %d/%d \\\\\n"
                 % (LABELS[key], e["n_seeds"], f"{e['n_trainable_params']:,}",
                    e["cg_delta_mean"], e["cg_delta_std"], e["r1_mean"],
                    xs[0] if xs else -1, e["vision_tensors"]))
    anchor = "Text-only & 5 & 196,608 & $-0.047 \\pm 0.003$ & 0.624 & 0/199 \\\\\n"
    if rows.strip() and rows not in src:
        if src.count(anchor) != 1:
            print("anchor row not found exactly once; aborting")
            return 1
        src = src.replace(anchor, anchor + rows, 1)
        print("inserted %d joint row(s)" % len(have))

    # the one-armed wording must go once the joint arm exists
    old_a = ("Two limits on the reading: the control is one-armed---the joint configuration was\n"
             "not run under the same freeze---so we do not claim that vision-side perturbation is what\n"
             "makes joint adaptation costlier; and the effective-rank equality is a consistency check on\n"
             "the freeze rather than independent evidence, since a parameter set that never changes cannot\n"
             "change the geometry it computes.")
    new_a = ("The joint configuration, run under the same freeze, is reported in "
             "Table~\\ref{tab:strictcontrol}; it places trainable parameters inside the vision tower, so\n"
             "its vision tensors do change, which is what makes the comparison informative. The\n"
             "effective-rank equality for the text-only arm remains a consistency check on the freeze\n"
             "rather than independent evidence, since a parameter set that never changes cannot change\n"
             "the geometry it computes.")
    if old_a in src:
        src = src.replace(old_a, new_a, 1)
        print("rewrote the one-armed paragraph")
    io.open(SC, "w", encoding="utf-8", newline="").write(src)
    print("updated %s" % SC)
    print("now recompile:  cd paper && pdflatex main_nn.tex (twice)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
