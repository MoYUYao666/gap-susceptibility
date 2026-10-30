# -*- coding: utf-8 -*-
r"""Map each point of the Pattern Recognition report (PR-D-26-10149) to evidence in Paper A.

Read-only: for every reviewer concern, search the current Paper A sources for the construct that would answer it, and
print where (file + short snippet) so the passage can be read in context. Absence is as informative as presence.

    python tools/_p1182_audit_against_pr_review.py
"""
from __future__ import annotations

import io
import os
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PA = REPO / "paper合"
FILES = [PA / "main_nc.tex"] + sorted((PA / "sections").glob("*.tex"))

CHECKS = [
    ("R1-Q1/R2-1 narrow claims of generality",
     [r"universal", r"any contrastive", r"across architectures", r"generaliz", r"scope"]),
    ("R1-2 config differences across groups (target modules/seeds/splits)",
     [r"target modules?", r"data split", r"same seed", r"configuration comparison", r"sanity"]),
    ("R1-3/R1-W2/R3-2 pseudo-replication: clustered / mixed / within-group",
     [r"clustered", r"mixed[- ]effects?", r"within-dataset", r"within-model", r"pseudo-replicat",
      r"non-?independent", r"cluster-robust"]),
    ("R1-3/R3-2 held-out or leave-one-out validation of the DG-R\@1 association",
     [r"held-?out", r"leave-one-(configuration|config|out)", r"leave-one-dataset", r"predictive"]),
    ("R1-4 / R1-2 configuration comparison table",
     [r"configuration comparison", r"Table~\\ref\{tab:config", r"tab:full_experiments", r"catalog"]),
    ("R1-4 stratified DG-R\@1 plots",
     [r"stratified", r"by model", r"per-dataset", r"figure.*strat"]),
    ("R1-5 repetitive Visual Fragility discussion",
     [r"Visual Fragility"]),
    ("R1-W1/R3-1 numerical inconsistencies reconciled (provenance of the disputed cells)",
     [r"provenance", r"Route D", r"0\.079", r"-0\.081", r"0\.427", r"0\.627", r"reconcil"]),
    ("R1-W3/R3-3 causal overclaim: is 'direct causal evidence' gone?",
     [r"direct causal", r"causal evidence", r"causally", r"consistent with"],),
    ("R1-W3 parameter-matched / normalised perturbations, several noise levels, seeds",
     [r"\\\\|\\\\Delta W\\\\|_F", r"Frobenius", r"relative perturb", r"noise level", r"sigma.*0\.0[123]",
      r"matched.*budget"]),
    ("R1-W4/R3-4 COCO near-zero protocol + BLIP-1 selective unfreezing + SigLIP weak",
     [r"near-random", r"test set", r"BLIP-1", r"selective unfreez", r"SigLIP"]),
    ("R1-W5/R2-5 DG-ES repositioned as preliminary, overhead reported",
     [r"early stopping", r"overhead", r"zero[- ]overhead", r"preliminary", r"proof-of-concept"]),
    ("R1-W6 fairness: same lr across full-FT and PEFT",
     [r"learning rate", r"lr sweep", r"sweep", r"hyperparameter", r"recipe"]),
    ("R2-2 novelty sharpened vs prior modality-specific PEFT work",
     [r"novel", r"contribution", r"unlike", r"differences? from"]),
    ("R2-3 scale/diversity: larger datasets, modern VLMs",
     [r"LLaVA", r"Qwen", r"decoder", r"large(r)? dataset"]),
    ("R2-4 alternative explanations (regularisation, optimisation)",
     [r"alternative", r"regulariz", r"optimization effect", r"cannot rule out"]),
    ("language editing",
     [r"\\bthe the\\b", r"\\ba a\\b"]),
]


def main() -> None:
    texts = {}
    for f in FILES:
        if f.exists():
            texts[f.name] = io.open(f, encoding="utf-8", errors="ignore").read()
    print(f"  scanning {len(texts)} files in paper合/\n")
    for label, pats in CHECKS:
        print(f"=== {label}")
        found = 0
        for pat in pats:
            hits = []
            for name, txt in texts.items():
                for m in re.finditer(pat, txt, re.I):
                    snippet = txt[max(0, m.start() - 55): m.start() + 75].replace("\n", " ")
                    hits.append((name, snippet))
            if hits:
                found += 1
                name, snip = hits[0]
                print(f"   hit[{pat}] {len(hits)}x  {name}: ...{snip[:150]}")
            else:
                print(f"   MISS[{pat}]")
        print(f"   -> {found}/{len(pats)} constructs present\n")


if __name__ == "__main__":
    main()
