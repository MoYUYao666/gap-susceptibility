# -*- coding: utf-8 -*-
r"""Write the full-scale MS-COCO result into the manuscript (Reviewer 2's "larger datasets").

The paper currently reports the repaired COCO retrieval protocol at 10,000 training and 3,000
evaluation images. A larger scale-up has since finished: the same three adaptation positions over
10,000 COCO training images with the *entire* val2014 split as the gallery (40,504 images, 202,654
caption rows), three seeds, rank 8, three epochs. It is the direct answer to "broader validation on
larger datasets", and it was sitting outside the manuscript.

Every number is read from `outputs/analysis/full_coco.json` at run time, so the sentence follows the
archive rather than a hand-copied value:

* frozen  R@1 0.5655 / R@5 0.6410
* text-only R@1 0.5823 +/- 0.0002 (three seeds) / R@5 0.6689
* text-to-image R@1 0.1316 frozen against 0.1650 for text-only; image-to-text R@1 0.9994 against 0.9997

The scale-up has no both-position arm, so the sentence says so rather than implying the 3,000-image
ordering was reproduced at this scale.

    python tools/_p862_add_full_coco.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import statistics as st
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
AGG = REPO / "outputs" / "analysis" / "full_coco.json"
EMP = REPO / "paper合" / "sections" / "empirical.tex"
NC_EMP = REPO / "paper合" / "NC_submission" / "latex_source" / "sections" / "empirical.tex"

ANCHOR = ("Adaptation is therefore measurably useful on MS-COCO, but on retrieval it does not "
          "reproduce the text-only advantage the alignment columns show: both-position is the higher "
          "of the two.")
MARK = "entire val2014 validation split"


def sentence() -> str:
    d = json.loads(AGG.read_text(encoding="utf-8"))
    fz = [r for r in d["runs"] if r["arm"] == "frozen"]
    tx = [r for r in d["runs"] if r["arm"] == "text_only"]
    assert len(fz) == 1 and len(tx) == 3, "unexpected run set in full_coco.json"
    fz, r1 = fz[0], [r["R@1"] for r in tx]
    mean, sd = st.mean(r1), st.stdev(r1)
    n_img = tx[0]["n_unique_images"]
    n_cap = tx[0]["n_captions"]
    t2i_m = st.mean([r["R@1_t2i"] for r in tx])
    i2t_m = st.mean([r["R@1_i2t"] for r in tx])
    return (
        " At full scale the same comparison holds without the two-order-of-magnitude shortfall: with "
        f"$10{{,}}000$ COCO training images and the entire val2014 validation split as the gallery "
        f"(${n_img:,}$ unique images, ${n_cap:,}$ caption rows, three seeds, rank $8$, three epochs), "
        f"frozen $R@1$ is ${fz['R@1']:.4f}$ and text-only reaches ${mean:.4f} \\pm {sd:.4f}$ "
        f"($R@5$ ${st.mean([r['R@5'] for r in tx]):.4f}$ against ${fz['R@5']:.4f}$ frozen). The gain "
        "is one-directional: text-to-image $R@1$ moves from "
        f"${fz['R@1_t2i']:.4f}$ to ${t2i_m:.4f}$, while image-to-text is at ceiling in both arms "
        f"(${fz['R@1_i2t']:.4f}$ against ${i2t_m:.4f}$), so the improvement comes from the direction "
        "that had room. This scale-up runs the frozen and text-only arms only, so the 3{,}000-image "
        "ordering between the two adapted positions is not re-measured here, and the three-epoch "
        "schedule is shorter than the six epochs used above; both differences are stated because "
        f"neither arm can be read across the two scales.").replace(",}", "}").replace("$,", "$,")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    add = sentence()
    # the thousands separators were inserted for readability; keep them (no LaTeX math commas)
    add = add.replace(f"{40504:,}", "40{,}504").replace(f"{202654:,}", "202{,}654")
    assert "\n" not in add and len(add) < 1400, "sentence looks wrong"
    for needle in ("40{,}504", "202{,}654", "0.5655", "0.5823"):
        assert needle in add, f"missing {needle}"

    for p in (EMP, NC_EMP):
        assert p.exists(), f"missing {p}"
        t = io.open(p, encoding="utf-8").read()
        if MARK in t:
            print(f"  {p.name}: already present")
            continue
        c = t.count(ANCHOR)
        assert c == 1, f"{p.name}: anchor found {c} times"
        if a.apply:
            io.open(p, "w", encoding="utf-8", newline="").write(t.replace(ANCHOR, ANCHOR + add, 1))
            print(f"  appended to {p.relative_to(REPO).as_posix()}")
        else:
            print(f"  would append {len(add)} chars to {p.relative_to(REPO).as_posix()}")

    if not a.apply:
        print("  (dry run)")
        return 0
    for p in (EMP, NC_EMP):
        t = io.open(p, encoding="utf-8").read()
        assert t.count(MARK) == 1, f"{p.name}: insertion not unique"
        for needle in ("40{,}504", "202{,}654", "0.5823", "0.1650"):
            assert needle in t, f"{p.name}: missing {needle}"
        print(f"  verified {p.relative_to(REPO).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
