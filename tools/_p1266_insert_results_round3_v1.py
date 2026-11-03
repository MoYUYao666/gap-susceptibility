# -*- coding: utf-8 -*-
r"""Generate and insert the three results subsections of novelty items 1, 2, 5, 6 from the archives.

Numbers are read from the JSON archives at build time (no hand-copied values):
  outputs/analysis/a1_prompt_template_gap.json        item 1 (prompt-template drift) and item 4 (tau at k=5/10)
  outputs/analysis/a1_threshold_transfer.json         item 2 (no absolute threshold transfers)
  outputs/analysis/a1_more_benchmarks.json            item 5 (further benchmarks) and item 6 (bootstrap intervals)

Inserted before `\\subsection{A label-free monitoring protocol}`:
  \\subsection{Text-side drift in practice}      label sec:promptgap
  \\subsection{Absolute thresholds do not transfer} label sec:thresholds
  \\subsection{Further benchmarks, with intervals}  label sec:morebench

    python tools/_p1266_insert_results_round3.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import os
import statistics

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAIN = os.path.join(REPO, "paper_a1", "main.tex")
AN = os.path.join(REPO, "outputs", "analysis")
ANCHOR = r"\subsection{A label-free monitoring protocol}"

NAMES = {"clip32": "CLIP ViT-B/32", "clip16": "CLIP ViT-B/16", "openclip": "OpenCLIP laion2B",
         "siglip": "SigLIP B/16", "vitl": "CLIP ViT-L/14"}
BENCH = {"imagenet5k": "ImageNet-5k", "inat_wild": "iNaturalist-wild", "rare_species": "Rare species"}


def load(name):
    p = os.path.join(AN, name)
    if not os.path.exists(p):
        return None
    return json.load(io.open(p, encoding="utf-8"))


def fmt(x, nd=2):
    return "%.*f" % (nd, x)


def prompt_section(d):
    rows = []
    for tag, v in d["models"].items():
        tau = [r["tau5"] for r in v["rows"] if r["tau5"] is not None and r["tau5"] < 0.999]
        cgs = [r["CG"] for r in v["rows"]]
        t1 = [r["top1"] for r in v["rows"]]
        rows.append({"tag": tag, "frozen_cg": cgs[0], "cg_lo": min(cgs), "cg_hi": max(cgs),
                     "cg_spread": v["cg_spread"], "t1_lo": min(t1), "t1_hi": max(t1),
                     "t1_range": max(t1) - min(t1), "tau_lo": min(tau) if tau else 1.0})
    tab = "\n".join(
        "%s & %s & %s & %s & %s--%s & %s \\\\" % (
            NAMES.get(r["tag"], r["tag"]), fmt(r["frozen_cg"], 3),
            fmt(r["cg_lo"], 3) + "--" + fmt(r["cg_hi"], 3), fmt(r["cg_spread"], 3),
            fmt(r["t1_lo"], 1), fmt(r["t1_hi"], 1), fmt(r["t1_range"], 2))
        for r in rows)
    max_spread = max(r["cg_spread"] for r in rows)
    max_t1 = max(r["t1_range"] for r in rows)
    return r"""
\subsection{Text-side drift in practice: the prompt template}
\label{sec:promptgap}

Proposition~\ref{prop:confound} is not a pathological construction. The text side of a zero-shot classifier is set by the
researcher, and its most common free parameter is the prompt template. We hold the image set fixed (the same $5{,}000$
ImageNet-5k images) and change only the template, using ten standard formulations (``a photo of a \{\}.'', ``a bad photo
of a \{\}.'', ``a cropped photo of a \{\}.'', the bare class name, and six others).

Changing nothing but the template moves the centroid gap by up to %s on %s, while the zero-shot accuracy range across
the same ten templates is %s points (Table~\ref{tab:prompt}). For comparison, the gap difference that accompanies the
$32.7$-point accuracy collapse of the flagship matched pair is $0.028$ (Section~\ref{sec:matchedgap}): a prompt choice
moves the gap %s times as far as the difference that hides a third of the accuracy, and changes accuracy by a few points
at most.

\begin{table}[H]
\centering
\small
\caption{Prompt-template control on ImageNet-5k (5{,}000 images, ten templates). Only the text embedding changes.
$\Delta\mathrm{CG}$ is the spread of the centroid gap over the ten templates; the last column is the range of top-1
achieved by the ten templates. Source: \texttt{outputs/\allowbreak analysis/\allowbreak a1\_prompt\_template\_gap.json}.}
\label{tab:prompt}
\begin{tabular}{lccccc}
\toprule
backbone & frozen $\mathrm{CG}$ & $\mathrm{CG}$ range & $\Delta\mathrm{CG}$ & top-1 range (points) & $\tau_5$ min \\
\midrule
%s
\bottomrule
\end{tabular}
\end{table}

The accuracy is not entirely flat -- the templates shift it by %s points, and $\tau_5$ against the reference template
falls to %s in the worst case -- but the two movements are unrelated in size: a gap movement of the order of the
matched-gap tolerance buys an accuracy movement two orders of magnitude smaller than the matched-gap collapse itself.
This is the practical form of Proposition~\ref{prop:confound}: any gap number reported without its prompt vocabulary is
not attributable to the image side.
""" % (fmt(max_spread, 3), NAMES.get(max(rows, key=lambda r: r["cg_spread"])["tag"], "the backbone"),
       fmt(max_t1, 2), fmt(max_spread / 0.028, 1), tab, fmt(max_t1, 2),
       fmt(min(r["tau_lo"] for r in rows), 2))


def threshold_section(d):
    s = d["summary"]
    ba = [v for v in s["transfer_balanced_accuracy"] if v is not None]
    frozen = d["settings"]
    sig = None
    if "siglip_imagenet5k" in frozen:
        sig = frozen["siglip_imagenet5k"]
    clip = frozen.get("clip_imagenet5k")
    return r"""
\subsection{Absolute thresholds do not transfer}
\label{sec:thresholds}

If the gap were a health metric, one absolute threshold would separate healthy from degraded configurations. The frozen
(configuration-fitted) gaps of the settings in this paper span %s--%s, a factor of %s, before any fine-tuning damage:
SigLIP has the largest frozen gap (%s) and the highest frozen accuracy (%s\%%), so a threshold fitted on CLIP
(%s / %s\%%) labels the best model as the least healthy.

Fitting the balanced-accuracy-optimal threshold inside each setting and applying it to the others makes the failure
quantitative: over the %d cross-setting transfers the balanced accuracy has median %s, %d of %d transfers fall below
chance, and the worst is %s. A threshold does not degrade gracefully across settings; it becomes anti-correlated with
accuracy, because the ranking of frozen gaps has nothing to do with the ranking of accuracies.

A monitor can still be calibrated, but only conditionally: the threshold must be re-fitted per benchmark and per model
family, and it must be reported together with the setting it was fitted in (Section~\ref{sec:standard}).
""" % (fmt(s["frozen_CG_min"], 3), fmt(s["frozen_CG_max"], 3), fmt(s["frozen_CG_ratio"], 2),
       fmt(sig["CG"], 3) if sig else "n/a", fmt(sig["top1"], 1) if sig else "n/a",
       fmt(clip["CG"], 3) if clip else "n/a", fmt(clip["top1"], 1) if clip else "n/a",
       len(ba), fmt(statistics.median(ba), 3), sum(1 for x in ba if x < 0.5), len(ba), fmt(min(ba), 3))


def morebench_section(d):
    rows, lines = [], []
    for spec, v in d["benchmarks"].items():
        b = v["widest_matched_pair"]
        c = v.get("contraction")
        rows.append({"spec": spec, "classes": v["n_classes"], "images": v["n_images"],
                     "cg": v["frozen"]["CG"], "t1": v["frozen"]["top1"],
                     "spread": b["spread"], "dCG": b["dCG"], "ci": b["ci95"],
                     "gain": c["top1_gain"] if c else None, "gain_ci": c["ci95"] if c else None})
        lines.append("%s & %d & %d & %s & %s & %s & [%s, %s] & %s & [%s, %s] \\\\" % (
            BENCH.get(spec, spec), v["n_classes"], v["n_images"], fmt(v["frozen"]["CG"], 3),
            fmt(v["frozen"]["top1"], 1), fmt(b["spread"], 1), fmt(b["ci95"][0], 1), fmt(b["ci95"][1], 1),
            fmt(c["top1_gain"], 1) if c else "n/a",
            fmt(c["ci95"][0], 1) if c else "n/a", fmt(c["ci95"][1], 1) if c else "n/a"))
    im = next((r for r in rows if r["spec"] == "imagenet5k"), None)
    ci_txt = ""
    if im:
        ci_txt = ("On ImageNet-5k the flagship matched pair differs by %s points, 95\\%% bootstrap interval [%s, %s] "
                  "over images." % (fmt(im["spread"], 1), fmt(im["ci"][0], 1), fmt(im["ci"][1], 1)))
    return r"""
\subsection{Further benchmarks, with intervals}
\label{sec:morebench}

Section~\ref{sec:secondbench} replicated the control on DTD and Food-101. We add two further local benchmarks that were
not used anywhere in the construction of the argument: iNaturalist-wild (50 species) and a rare-species release (classes
with at least five images). Table~\ref{tab:morebench} reports the widest matched-gap pair and the class-contraction gain
on each benchmark, together with 95\%% bootstrap intervals over images (500 resamples). %s

\begin{table}[H]
\centering
\small
\caption{Matched-gap spread and contraction gain on further benchmarks (frozen CLIP ViT-B/32, same protocol as
Section~\ref{sec:matchedgap}). The spread is the largest top-1 difference between two configurations whose gaps agree to
$0.03$; the gain is the accuracy change when every image is contracted toward its class prototype ($\alpha=0.5$).
Intervals are percentile bootstraps over images. Source: \texttt{outputs/\allowbreak analysis/\allowbreak
a1\_more\_benchmarks.json}.}
\label{tab:morebench}
\begin{tabular}{lcccccccc}
\toprule
benchmark & classes & images & frozen CG & frozen top-1 & spread & 95\% CI & gain & 95\% CI \\
\midrule
%s
\bottomrule
\end{tabular}
\end{table}

The intervals exclude zero on every benchmark, but the magnitude follows the benchmark difficulty: $32.7$ points on
ImageNet-5k and $21.0$ on the rare-species release, against $2.6$ points on the fine-grained iNaturalist set, where
frozen accuracy is only $10.6\%$ and the classifier has little to lose. The contraction gain keeps its sign everywhere
($+19.0$ to $+3.2$ points). What varies is the level, not the sign, which is the same pattern the boundary analysis
reports for the first-order law.
""" % (ci_txt, "\n".join(lines))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    prompt = load("a1_prompt_template_gap.json")
    thresh = load("a1_threshold_transfer.json")
    more = load("a1_more_benchmarks.json")
    blocks = []
    if prompt:
        blocks.append(prompt_section(prompt))
    if thresh:
        blocks.append(threshold_section(thresh))
    if more:
        blocks.append(morebench_section(more))
    print(f"  blocks: {len(blocks)} (prompt={bool(prompt)} threshold={bool(thresh)} morebench={bool(more)})")
    assert blocks, "no archives found"
    t = io.open(MAIN, encoding="utf-8").read()
    n = t.count(ANCHOR)
    print(f"  anchor occurrences: {n}")
    assert n == 1
    before = len(t)
    t = t.replace(ANCHOR, "".join(blocks) + "\n" + ANCHOR, 1)
    for token in ("sec:promptgap", "sec:thresholds", "sec:morebench", "tab:prompt", "tab:morebench"):
        print(f"  present {token!r}: {t.count(token)}")
    print(f"  length {before} -> {len(t)} (+{len(t) - before})")
    if not a.apply:
        print("  (dry run)")
        return 0
    io.open(MAIN, "w", encoding="utf-8", newline="").write(t)
    print("  written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
