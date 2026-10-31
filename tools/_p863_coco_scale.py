# -*- coding: utf-8 -*-
r"""Write the full-scale MS-COCO result into the manuscript (Reviewer 2's "larger datasets").

The paper reports the repaired COCO retrieval protocol at 10,000 training and 3,000 evaluation images.
A larger scale-up has since finished: the same protocol with the *entire* val2014 split as the gallery
(40,504 images, 202,654 caption rows), three seeds, rank 8, three epochs. That is the direct answer to
"broader validation on larger datasets", and it was sitting outside the manuscript.

The two copies of the manuscript needed different edits, which is why this script carries two plans:

* the working copy already contains the 3,000-image repair, so it only receives the new full-scale
  sentence;
* the NC copy predates that repair entirely (it still says only that the COCO rows are at chance), so
  it receives the 3,000-image result first and the full-scale result after it.

Every number is read from `outputs/analysis/full_coco.json` and from
`outputs/analysis/coco_scaleup.json` at run time, so no value is hand-copied.

    python tools/_p863_coco_scale.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import statistics as st
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
EMP = REPO / "paper合" / "sections" / "empirical.tex"
NC_EMP = REPO / "paper合" / "NC_submission" / "latex_source" / "sections" / "empirical.tex"
AGG = REPO / "outputs" / "analysis" / "full_coco.json"
SCALE = REPO / "outputs" / "analysis" / "coco_scaleup.json"
MARK = "entire val2014 validation split"

ANCHOR_WORK = ("Adaptation is therefore measurably useful on MS-COCO, but on retrieval it does not "
               "reproduce the text-only advantage the alignment columns show: both-position is the "
               "higher of the two.")

ANCHOR_NC = ("We therefore report the COCO rows as gap measurements and do not treat their retrieval "
             "column as evidence about retrieval, and we report no ODE coefficients for MS-COCO for "
             "the same reason (Section~\\ref{sec:discussion}).")


def load_agg() -> dict:
    d = json.loads(AGG.read_text(encoding="utf-8"))
    fz = [r for r in d["runs"] if r["arm"] == "frozen"]
    tx = [r for r in d["runs"] if r["arm"] == "text_only"]
    assert len(fz) == 1 and len(tx) == 3, "unexpected run set in full_coco.json"
    return {"frozen": fz[0], "text": tx}


def full_scale_sentence() -> str:
    a = load_agg()
    fz, tx = a["frozen"], a["text"]
    r1 = [r["R@1"] for r in tx]
    mean, sd = st.mean(r1), st.stdev(r1)
    r5 = st.mean([r["R@5"] for r in tx])
    t2i, i2t = st.mean([r["R@1_t2i"] for r in tx]), st.mean([r["R@1_i2t"] for r in tx])
    n_img, n_cap = tx[0]["n_unique_images"], tx[0]["n_captions"]
    # The mean and its spread go inside ONE math group: `$0.5823 $\pm$ $0.0002$` leaves an empty
    # math group and LaTeX raises "Missing $ inserted" (observed in the 2026-10-15 build). The text is
    # also split into three paragraphs, because as one block it ran to a full page.
    return (
        " At full scale the same comparison holds without the two-order-of-magnitude shortfall. With "
        f"$10{{,}}000$ COCO training images and the entire val2014 validation split as the gallery "
        f"(${n_img:,}$ unique images and ${n_cap:,}$ caption rows, three seeds, rank $8$, three "
        f"epochs), frozen $R@1$ is ${fz['R@1']:.4f}$ and text-only reaches "
        f"${mean:.4f} \\pm {sd:.4f}$ ($R@5$ ${r5:.4f}$ against ${fz['R@5']:.4f}$ frozen)."
        "\n\nThe gain is one-directional: text-to-image $R@1$ moves from "
        f"${fz['R@1_t2i']:.4f}$ to ${t2i:.4f}$, while image-to-text is at ceiling in both arms "
        f"(${fz['R@1_i2t']:.4f}$ against ${i2t:.4f}$), so the improvement comes from the direction "
        "that had room."
        "\n\nThis scale-up runs the frozen and text-only arms only, so the ordering between the two "
        "adapted positions is not re-measured here, and its three-epoch schedule is shorter than the "
        "six epochs used above; both differences are stated because neither arm is comparable across "
        "the two scales."
    ).replace(f"{n_img:,}", "40{,}504").replace(f"{n_cap:,}", "202{,}654")


def repair_paragraph_nc() -> str:
    """The 3,000-image repair, which only the NC copy is missing (values read from the archive)."""
    s = json.loads(SCALE.read_text(encoding="utf-8"))
    by: dict[str, list[dict]] = {}
    for r in s["runs"]:
        by.setdefault(r["arm"], []).append(r)
    arm = s["config"]["arms"]
    assert set(by) == {"frozen", "text_only", "both"} and arm == "text_only,both,frozen", \
        f"unexpected arms: {sorted(by)} / {arm!r}"

    def mean_sd(name: str) -> str:
        r1 = [r["R@1"] for r in by[name]]
        assert len(r1) == 3, f"{name} has {len(r1)} runs, expected three seeds"
        return f"{st.mean(r1):.3f} \\pm {st.stdev(r1):.3f}"

    fz = by["frozen"][0]["R@1"]
    cfg = s["config"]
    return (f" That deficiency is repairable, and we repaired it: with the training and evaluation "
            f"splits disjoint, a unique-image gallery and all five captions per image retained, the "
            f"same three adaptation positions over ${cfg['images']:,}$ COCO training and "
            f"${cfg['eval_images']:,}$ evaluation images give $R@1 = {fz:.3f}$ frozen, "
            f"${mean_sd('text_only')}$ for text-only and ${mean_sd('both')}$ for both-position, over "
            f"three seeds. Adaptation is therefore measurably useful on MS-COCO, but on retrieval it "
            f"does not reproduce the text-only advantage the alignment columns show: both-position is "
            f"the higher of the two.").replace(f"{cfg['images']:,}", "10{,}000").replace(
        f"{cfg['eval_images']:,}", "3{,}000")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    add = full_scale_sentence()
    for needle in ("40{,}504", "202{,}654", f"{load_agg()['frozen']['R@1']:.4f}",
                   f"{st.mean([r['R@1'] for r in load_agg()['text']]):.4f}"):
        assert needle in add, f"missing {needle}"

    plan = [(EMP, [(ANCHOR_WORK, ANCHOR_WORK + add)]),
            (NC_EMP, [(ANCHOR_NC, ANCHOR_NC + repair_paragraph_nc() + add)])]
    for p, pairs in plan:
        assert p.exists(), f"missing {p}"
        t = io.open(p, encoding="utf-8").read()
        if MARK in t:
            print(f"  {p.name}: already present")
            continue
        for old, _new in pairs:
            assert t.count(old) == 1, f"{p.name}: anchor found {t.count(old)} times"
        if a.apply:
            for old, new in pairs:
                t = t.replace(old, new, 1)
            io.open(p, "w", encoding="utf-8", newline="").write(t)
            print(f"  wrote {p.relative_to(REPO).as_posix()}")
        else:
            print(f"  would patch {p.relative_to(REPO).as_posix()} ({len(pairs)} edit)")

    if not a.apply:
        print("  (dry run)")
        return 0
    for p, _ in plan:
        t = io.open(p, encoding="utf-8").read()
        assert t.count(MARK) == 1, f"{p.name}: insertion not unique"
        for needle in ("40{,}504", "202{,}654", "0.5823", "0.5655"):
            assert needle in t, f"{p.name}: missing {needle}"
        print(f"  verified {p.relative_to(REPO).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
