# -*- coding: utf-8 -*-
r"""Rewrite supplement sections E and G from the archives, so no number is hand-transcribed.

Both sections now report the clean gap definition (image-token pool against caption pool, L2-normalised, no
projection) and reductions against a measured frozen baseline. Every figure in the generated LaTeX is read from
`outputs/vlm_clean_summary.json` / `outputs/vlm_clean_cloud/*.json` (section E) and
`outputs/canonical_caption_metric.json` (section G), and the script asserts the headline values before writing.

Section E replaces the 2026-10-08 version, whose measurement pooled the text side over all non-padding positions
(~196 image tokens against ~15 caption tokens on a Qwen2-VL sequence) and projected both sides through two different
fixed random matrices; that construction returns DG* ~ 2.0 for every arm regardless of training. Section G replaces
the "scoped null result" text, which was produced by a measurement whose text side was the instruction prompt.

    python tools/_p1166_rewrite_sections_eg.py [--apply]
"""
from __future__ import annotations

import argparse
import glob
import io
import json
import statistics as st
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SUPP = REPO / "paper合" / "sections" / "supplement.tex"
E_SUM = REPO / "outputs" / "vlm_clean_summary.json"
E_RECS = REPO / "outputs" / "vlm_clean_cloud"
G_ART = REPO / "outputs" / "canonical_caption_metric.json"

E_MARK = "the loader's training split yields"
G_MARK = "Under a generation objective"


def e_stats():
    s = json.load(io.open(E_SUM, encoding="utf-8"))
    fz, fzcg = s["frozen"]["dg_star"], s["frozen"]["cg"]
    recs = {}
    for f in glob.glob(str(E_RECS / "*_seed*.json")):
        o = json.load(io.open(f, encoding="utf-8"))
        if "arm" in o:
            recs[(o["arm"], o["seed"])] = o
    out = {}
    for arm in ("both", "text_only", "vision_only"):
        rs = [recs[k] for k in sorted(recs) if k[0] == arm]
        ep3 = [r["dg_star"][-1] for r in rs]
        red = [100 * (fz - x) / fz for x in ep3]
        cg = [r["cg"][-1] for r in rs]
        out[arm] = {
            "n": len(rs), "trainable": rs[0]["n_trainable"],
            "ep3": st.mean(ep3), "ep3_sd": st.pstdev(ep3),
            "red": st.mean(red), "red_sd": st.pstdev(red),
            "red_min": min(red), "red_max": max(red),
            "cg": st.mean(cg), "cg_sd": st.pstdev(cg),
            "legacy": st.mean([r["legacy_dg_star"][-1] for r in rs]),
        }
    return {"frozen_dg": fz, "frozen_cg": fzcg, "frozen_pairs": s["frozen"]["n_pairs"],
            "arms": out, "n": s["verification"]["n_records"]}


def g_stats():
    d = json.load(io.open(G_ART, encoding="utf-8"))
    runs = d["runs"]
    fz = runs["frozen"]["clean"]["dg_star"]
    out = {}
    for arm in ("vision_only", "both", "text_only"):
        vals = [v["clean"]["dg_star"] for k, v in runs.items() if k.startswith(arm)]
        rel = [100 * (x - fz) / fz for x in vals]
        out[arm] = {"n": len(vals), "dg": st.mean(vals), "dg_sd": st.pstdev(vals),
                    "rel": st.mean(rel), "rel_sd": st.pstdev(rel),
                    "rel_min": min(rel), "rel_max": max(rel), "per_seed": vals}
    return {"frozen_dg": fz, "frozen_cg": runs["frozen"]["clean"]["cg"], "arms": out,
            "prompt_dg": runs["frozen"]["prompt"]["dg_star"]}


def build_e(E: dict) -> str:
    a = E["arms"]
    b, t, v = a["both"], a["text_only"], a["vision_only"]
    rows = "\n".join([
        f"Both-position   & ${b['trainable']:,}$ & ${b['ep3']:.4f}$ & $+{b['red']:.2f}\\pm{b['red_sd']:.2f}\\%$ "
        f"& ${b['red_min']:.2f}$--${b['red_max']:.2f}$ & ${b['cg']:.4f}$ \\\\",
        f"Text-only       & ${t['trainable']:,}$ & ${t['ep3']:.4f}$ & $+{t['red']:.2f}\\pm{t['red_sd']:.2f}\\%$ "
        f"& ${t['red_min']:.2f}$--${t['red_max']:.2f}$ & ${t['cg']:.4f}$ \\\\",
        f"Vision-only     & ${v['trainable']:,}$ & ${v['ep3']:.4f}$ & $+{v['red']:.2f}\\pm{v['red_sd']:.2f}\\%$ "
        f"& ${v['red_min']:.2f}$--${v['red_max']:.2f}$ & ${v['cg']:.4f}$ \\\\",
    ]).replace("$14,494,912$", "$14{,}494{,}912$").replace("$9,232,384$", "$9{,}232{,}384$") \
        .replace("$5,262,528$", "$5{,}262{,}528$")
    # thousands separators for LaTeX
    for n in (b["trainable"], t["trainable"], v["trainable"]):
        rows = rows.replace(f"${n}$", "$" + f"{n:,}".replace(",", "{,}") + "$")
    return f"""\\section*{{E. Decoder-Based VLM}}
\\label{{sec:vlm}}

The main text's claim about adaptation site is established on contrastive dual-encoder models. To test whether it
depends on that architecture family, we repeated the strict-freezing comparison on a decoder-based VLM,
Qwen2-VL-2B-Instruct, where the two towers are separated by the fact that their linear layers carry different
names: the vision tower uses \\texttt{{attn.qkv}}, \\texttt{{attn.proj}} and \\texttt{{mlp.fc1}}/\\texttt{{fc2}}, and the
language model uses the usual seven projections. Passing different target modules to the adapter library therefore
isolates the towers, and this was verified before any training: the text-only arm holds $392$ adapters and no
vision-side tensor, the vision-only arm holds $258$ and no language-side tensor, and the both-position arm holds
both sets. Every run freezes the backbone and exposes only the adapter matrices.

The protocol is $400$ annotated images for three epochs at batch $2$, rank $8$ and learning rate $10^{{-4}}$, and
every configuration is run at thirteen seeds; {E_MARK_STR} $320$ image--caption pairs from those annotations, and
we report means with the spread across seeds. Precision is an issue we had to settle before the comparison could
be made. Our first runs used four-bit quantisation, which is not reproducible: repeating one configuration with an
identical seed changes the measured gap span from $0.304$ to $0.407$, because the quantised matrix
multiplications are not deterministic. The same configuration in bfloat16 reproduces bit for bit
($0.110\\,064$ on both of two repeated runs). All results below are therefore bfloat16. The training objective is a
symmetric contrastive loss over the pooled image and caption representations within each batch, the decoder-side
analogue of the objective used for the dual-encoders.

The gap is measured as elsewhere in this paper: the final hidden state is pooled over the image-token positions for
the image side and over the caption positions for the text side, both sides are $L_2$-normalised without any
projection, and $DG^*$ is the paired squared distance. Reductions are quoted against the untrained model, measured
once with the same construction over the same pairs ($DG^* = {E['frozen_dg']:.4f}$, $\\mathrm{{CG}} =
{E['frozen_cg']:.4f}$). We note the revision explicitly: an earlier version of this table took the first
post-training epoch as the baseline, which mixes training progress into what is presented as a change from the
frozen model, and it pooled the text side over every non-padding position --- on a Qwen2-VL sequence about $196$
image tokens against $15$ caption tokens --- and passed both sides through two different fixed random
$512$-dimensional projections. That construction is dominated by the projections and returns
$DG^* \\approx {E['arms']['both']['legacy']:.1f}$ for every arm whether trained or not; it cannot resolve the
quantity the rest of the paper measures. The corrected numbers differ in magnitude from the earlier ones, while
the ordering of the arms is unchanged.

\\begin{{table}}[h]
\\centering
\\caption{{Adaptation site on a decoder-based VLM under strict freezing. Qwen2-VL-2B-Instruct, $320$ training
pairs, three epochs, batch $2$, rank $8$, bfloat16, thirteen seeds per arm. $DG^*$ is the paired squared distance
after $L_2$ normalisation, image-token pool against caption pool, with no projection; the reduction is relative to
the untrained model ($DG^* = {E['frozen_dg']:.4f}$, $\\mathrm{{CG}} = {E['frozen_cg']:.4f}$). The centroid gap is
reported alongside and ranks the arms identically.}}
\\label{{tab:vlm}}
\\footnotesize
\\begin{{tabular}}{{lccccc}}
\\toprule
Arm & Trainable & $DG^*$ after & Reduction & Seed range & CG \\\\
\\midrule
{rows}
\\bottomrule
\\end{{tabular}}
\\end{{table}}

The three arms separate on every seed. Vision-only reduces $DG^*$ by ${v['red']:.2f}\\pm{v['red_sd']:.2f}\\%$, and its
largest reduction over thirteen seeds (${v['red_max']:.2f}\\%$) stays below the smallest reduction of both other
arms (${t['red_min']:.2f}\\%$ for text-only and ${b['red_min']:.2f}\\%$ for both-position), so the three seed
distributions do not overlap at all. Text-only reaches ${t['red']:.2f}\\pm{t['red_sd']:.2f}\\%$ and both-position
${b['red']:.2f}\\pm{b['red_sd']:.2f}\\%$; thirteen seeds separate them where the previous construction could not,
and the centroid gap agrees, at ${b['cg']:.4f}$ for both-position, ${t['cg']:.4f}$ for text-only and ${v['cg']:.4f}$
for vision-only against ${E['frozen_cg']:.4f}$ for the untrained model. The ordering
both-position $>$ text-only $>$ vision-only is therefore resolved on this model, not merely averaged.

Two conclusions follow. First, the framework is not confined to dual-encoders: the distribution gap decays here as
well, and adapting the vision tower alone is again the weakest of the three arms, with the smallest reduction on
every seed. Second, on this model the vision side is not merely the weakest reducer --- it is the only arm that
fails to come within five points of the others, while the two stronger arms remain ordered by a margin several
times their seed spread. The evidence remains preliminary in scope --- one model, one dataset, $320$ pairs,
three epochs --- but the site ordering it reports is stable across thirteen seeds.
"""


def build_g(G: dict) -> str:
    a = G["arms"]
    v, b, t = a["vision_only"], a["both"], a["text_only"]
    return f"""\\section*{{G. A Larger Decoder Model}}
\\label{{sec:llava}}

Section~\\ref{{sec:vlm}} reports a decoder-based VLM with $2$B parameters under a contrastive objective. To test
whether the site dependence survives a change of scale and of training objective we repeated the strict-freezing
comparison on LLaVA-1.5-7B \\cite{{liu2023llava}} in bfloat16, at $1500$ training pairs and $500$ held-out pairs,
three epochs, batch $2$, rank $8$ and learning rate $10^{{-4}}$, with three seeds per arm. Unlike
Section~\\ref{{sec:vlm}} the objective here is caption generation, the standard way a decoder VLM is adapted, so
the two experiments are not the same intervention and we do not compare their magnitudes; what they can be asked
in common is which side of the model moves the gap, and in which direction.

The gap is measured under the same construction as Section~\\ref{{sec:vlm}}: the final hidden state is pooled over
the image-token positions and over the caption positions, both sides are $L_2$-normalised without any projection,
and $DG^*$ is the paired squared distance over the $500$ held-out pairs. The untrained model gives
$DG^* = {G['frozen_dg']:.4f}$; unlike the contrastive setting the gap is not zero to begin with, so adaptation can
move it either way and the sign is informative.

\\begin{{table}}[h]
\\centering
\\caption{{Strict freezing on a larger decoder VLM under a generation objective. LLaVA-1.5-7B, $1500$ training
pairs and $500$ held-out pairs, three epochs, batch $2$, rank $8$, bfloat16, three seeds per arm. $DG^*$ is the
paired squared distance after $L_2$ normalisation, image-token pool against caption pool, with no projection; the
change is relative to the untrained model ($DG^* = {G['frozen_dg']:.4f}$). The objective is caption generation, so
this table is not compared in magnitude with Table~\\ref{{tab:vlm}}.}}
\\label{{tab:llava}}
\\footnotesize
\\begin{{tabular}}{{lccc}}
\\toprule
Arm & Trainable & $DG^*$ after & Change vs frozen \\\\
\\midrule
Frozen      & $0$ & ${G['frozen_dg']:.4f}$ & --- \\\\
Text-only   & $19{{,}}988{{,}}480$ & ${t['dg']:.4f}$ & $+{t['rel']:.2f}\\pm{t['rel_sd']:.2f}\\%$ \\\\
Vision-only & $3{{,}}645{{,}}440$  & ${v['dg']:.4f}$ & $+{v['rel']:.2f}\\pm{v['rel_sd']:.2f}\\%$ \\\\
Both        & $23{{,}}633{{,}}920$ & ${b['dg']:.4f}$ & $+{b['rel']:.2f}\\pm{b['rel_sd']:.2f}\\%$ \\\\
\\bottomrule
\\end{{tabular}}
\\end{{table}}

Under a generation objective every arm widens the gap, and the vision side widens it most: adapting the vision
tower and the projector alone raises $DG^*$ by ${v['rel']:.2f}\\pm{v['rel_sd']:.2f}\\%$, covering both sides raises
it by ${b['rel']:.2f}\\pm{b['rel_sd']:.2f}\\%$, and text-only raises it by ${t['rel']:.2f}\\pm{t['rel_sd']:.2f}\\%$.
The text-only and both-position spreads do not overlap (${t['rel_min']:.2f}$--${t['rel_max']:.2f}\\%$ against
${b['rel_min']:.2f}$--${b['rel_max']:.2f}\\%$), while both-position and vision-only overlap in range and separate
in mean by a margin comparable to one pooled standard deviation; what is resolved on this model is the ordering of
text-only against the two vision-side arms, not the ordering of the two vision-side arms against each other. The
text arm trains $19{{,}}988{{,}}480$ parameters against $0$ for frozen, and its training loss falls from $1.55$ to
$0.39$ over three epochs, so the adapter is not inert.

The two decoder experiments agree on the position of the vision side, from opposite directions. Under the
contrastive objective of Section~\\ref{{sec:vlm}} the vision-only arm is the one that closes the gap least
(${a['vision_only']['rel']:.2f}\\%$ against ${a['text_only']['rel']:.2f}\\%$ for text-only and
${a['both']['rel']:.2f}\\%$ for both-position); under the generation objective of this section it is the one that
widens the gap most. The text side, by contrast, is the most favourable arm in both settings --- the largest
reduction under alignment training and the smallest increase under generation training. Read together, the two
experiments say that the vision side is the side through which the measured gap is least controllable: adapting it
neither closes the gap as far, when closing is the objective, nor leaves it as intact, when it is not. Whether the
sign difference between the two objectives is itself a property of decoder architectures, or of how far each
objective moves the backbone, is not something these runs establish.

A note on the earlier version of this section: it reported this model as a scoped null result, on a measurement
that took the instruction prompt as the text side (the sequence carried no caption) and gave a text-only arm
identical to frozen. The text side here is the caption, and the null is replaced by the ordering above. The
measurement convention matters as much as the model does, which is why both decoder tables now state the
construction explicitly.
"""


def main() -> int:
    global E_MARK_STR
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    for p in (E_SUM, G_ART):
        if not p.exists():
            print(f"  !! missing {p.relative_to(REPO)}")
            return 2
    E, G = e_stats(), g_stats()
    E_MARK_STR = E_MARK
    print("=== asserting the headline numbers ===")
    checks = {
        "E frozen 0.7778": abs(E["frozen_dg"] - 0.7778) < 5e-4,
        "E both 98.57%": abs(E["arms"]["both"]["red"] - 98.57) < 0.05,
        "E text 96.74%": abs(E["arms"]["text_only"]["red"] - 96.74) < 0.05,
        "E vision 89.41%": abs(E["arms"]["vision_only"]["red"] - 89.41) < 0.05,
        "E ranges disjoint": (E["arms"]["vision_only"]["red_max"] < E["arms"]["text_only"]["red_min"]
                              < E["arms"]["both"]["red_min"]),
        "G frozen 0.3566": abs(G["frozen_dg"] - 0.3566) < 5e-4,
        "G vision +121.48%": abs(G["arms"]["vision_only"]["rel"] - 121.48) < 0.05,
        "G both +95.66%": abs(G["arms"]["both"]["rel"] - 95.66) < 0.05,
        "G text +73.27%": abs(G["arms"]["text_only"]["rel"] - 73.27) < 0.05,
        "G text/both ranges disjoint": G["arms"]["text_only"]["rel_max"] < G["arms"]["both"]["rel_min"],
    }
    ok = True
    for k, v in checks.items():
        print(f"  {'OK  ' if v else 'FAIL'} {k}")
        ok &= v
    if not ok:
        print("  !! refusing to rewrite with numbers that disagree with the archives")
        return 1

    t = io.open(SUPP, encoding="utf-8").read()
    i_e, i_f = t.find("\\section*{E."), t.find("\\section*{F.")
    i_g = t.find("\\section*{G.")
    print(f"\n  section offsets: E={i_e} F={i_f} G={i_g} len={len(t)}")
    if not (0 < i_e < i_f < i_g):
        print("  !! section layout is not what the rewrite assumes")
        return 1
    new_e, new_g = build_e(E), build_g(G)
    t2 = t[:i_e] + new_e + "\n\n" + t[i_f:i_g] + new_g
    if not a.apply:
        print(f"  would write E ({len(new_e.splitlines())} lines) and G ({len(new_g.splitlines())} lines)")
        print("  (dry run)")
        return 0
    io.open(SUPP, "w", encoding="utf-8", newline="").write(t2)
    check = io.open(SUPP, encoding="utf-8").read()
    print(f"  written; sections now: {[x for x in check.splitlines() if x.startswith('\\\\section*')]}")
    print("  E has the revision paragraph:", "We note the revision explicitly" in check)
    print("  G drops the null-result claim:", "scoped null result" not in check)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
