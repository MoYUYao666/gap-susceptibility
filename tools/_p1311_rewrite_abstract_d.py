# -*- coding: utf-8 -*-
r"""D: rewrite the abstract and the contribution paragraph so the theorem and the certificate lead.

The abstract is replaced wholesale and its length is checked with the audit counter (<= 250). The introduction's
"three model families" sentence becomes five backbones and gains a sentence about the theorem and the head-to-head
comparison.

    python tools/_p1311_rewrite_abstract_d.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import os
import re

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAIN = os.path.join(REPO, "paper_a1", "main.tex")

ABSTRACT = r"""Classification fine-tuning of a contrastive vision--language model moves the modality gap and erodes
class-relative rank order together; we establish which can be monitored. The decision rule depends only on row orderings,
whereas the gap is a function of the two embedding means: translating the text side leaves every prediction unchanged and
moves the gap arbitrarily. We state this as a characterization theorem: a first-moment summary is a valid health metric
exactly on interventions that are class-neutral, and for general interventions the error it can hide is bounded below by
the margin mass---the fraction of predictions whose margin is small enough for the intervention to flip. The bound is
attained by a zero-mean, gap-preserving perturbation and by matched-gap configurations that differ by $33$ accuracy points
at $|\Delta\mathrm{CG}|=0.03$ ($52$ at $0.05$), replicated by dense sweeps on five backbones (up to $62$ points) and by
real fine-tuned checkpoints $6.6$ points apart at $|\Delta\mathrm{CG}|=0.002$. Head to head, the gap correlates with
accuracy at $r=-0.15$ (classification) and $-0.22$ (retrieval), the Kendall order statistic reaches $+0.83$ but falls to
$-0.14$ on retrieval, and the margin mass reaches $-0.996$ and $-0.970$: the certificate, not the moment, transfers.
Changing only the prompt template moves the gap $3.4$ times as far as the difference hiding $33$ points while accuracy
barely moves, no absolute threshold transfers across settings, and a first-order bias field reproduces the shape of the
measured curve but not its level across four benchmarks ($r=0.93$--$0.99$, required scale $0.36$--$0.98$)."""

INTRO_OLD_1 = ("We resolve this decoupling with four controlled experiments, replicated across three model families "
               "(CLIP ViT-B/32, OpenCLIP laion2B, SigLIP).")
INTRO_NEW_1 = ("We resolve this decoupling with four controlled experiments, replicated across five backbones "
               "(CLIP ViT-B/32, ViT-B/16 and ViT-L/14, OpenCLIP laion2B, SigLIP), and we state the result as a theorem "
               "rather than as a collection of counterexamples: Theorem~\\ref{thm:characterization} characterises when a "
               "first-moment summary can be a health metric at all, bounds the error it can hide by the margin mass, and "
               "shows that the bound is attained. Section~\\ref{sec:showdown} then compares the candidate monitors head to "
               "head across classification and retrieval, and the appendix reports robustness checks.")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(MAIN, encoding="utf-8").read()
    m = re.search(r"(\\begin\{abstract\})(.*?)(\\end\{abstract\})", t, re.S)
    assert m
    t = t[:m.start(2)] + "\n" + ABSTRACT + "\n" + t[m.end(2):]
    print(f"  intro sentence: {t.count(INTRO_OLD_1)}")
    assert t.count(INTRO_OLD_1) == 1
    t = t.replace(INTRO_OLD_1, INTRO_NEW_1, 1)

    import sys
    sys.path.insert(0, REPO)
    from tools.paper_audit.texutil import count_words
    m2 = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", t, re.S)
    words = count_words(m2.group(1))
    print(f"  abstract words (audit counter): {words} (limit 250)")
    assert words <= 250, "abstract too long"
    if not a.apply:
        print("  (dry run)")
        return 0
    io.open(MAIN, "w", encoding="utf-8", newline="").write(t)
    print("  written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
