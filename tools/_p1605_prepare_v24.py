# -*- coding: utf-8 -*-
r"""Mirror additions and release notes for v2.4 (run only after every gate is green).

    python tools/_p1605_prepare_v24.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(REPO)

FILES = [
    "tools/_p1472_a23_fine_eps.py",
    "tools/_p1500_commentary_compression_probe.py",
    "tools/_p1580_paperA_decoder_confound.py",
    "tools/_p1585_a23_margin_negative_control.py",
    "tools/_p1595_bootstrap_ci_round.py",
    "tools/_p1595_p3_rank_separation.py",
    "tools/_p1595_qwen_objective_control.py",
    "tools/_p1600_commentary_round.py",
    "outputs/analysis/p3_rank_separation_extended.json",
    "outputs/analysis/a23_fine_eps_certificate.json",
    "outputs/analysis/a1_monitoring_bootstrap.json",
    "outputs/analysis/paperA_strict_bootstrap.json",
    "outputs/analysis/qwen_objective_control_contrastive_both_seed42.json",
    "outputs/analysis/qwen_objective_control_generative_both_seed42.json",
    "docs/p3_rank_separation_text.md",
    "docs/a23_fine_eps_text.md",
    "docs/a1_paperA_bootstrap_text.md",
    "docs/commentary_compression_and_table.md",
]

NOTES = """# Release notes - v2.4

This release refreshes the analysis layer, the result archives and the auditing tooling. It contains code,
result archives and provenance metadata only.

## Included

- **Analysis scripts** (`tools/`)
  - exact permutation matrix over all rank pairs, with Holm correction and TOST equivalence tests;
  - run-level and seed-level bootstrap confidence intervals for the monitoring and strict-freeze arms;
  - a fine-resolution re-evaluation of the margin-quality certificate (one decade below the previous grid)
    with uncached embeddings and a corrected archive-key reproduction check;
  - an objective-isolation control for a decoder vision-language model (contrastive vs generation loss at a
    fixed model, data, budget and adaptation site);
  - reproduction-check repair and manifest corrections for the affected tables;
  - Commentary compression probe and the two-decisions placement table generator.

- **Result archives** (`outputs/analysis/`)
  - rank-separation matrix, TOST and VQA equivalence archives;
  - bootstrap archives for the monitoring and strict-freeze analyses;
  - fine-epsilon certificate archive with embedding caches;
  - decoder objective-control archives;
  - updated margin-control and decoder-confound evidence.

- **Tooling and metadata**
  - provenance metadata updated for the affected tables;
  - audit expectations updated for the new page and section counts;
  - release-notes and packaging housekeeping.

- **Verification**
  - all repository gates pass: frozen-archive hashes, provenance gate, claim ledgers, per-project audits and
    the final verification report.

## Excluded (by repository policy)

- Model weights and datasets.
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    p = "tools/_p1284_prepare_public_mirror.py"
    t = io.open(p, encoding="utf-8").read()
    anchor = '    "cloud_p3/run_cloud_final.sh",\n'
    need = [x for x in FILES if x not in t]
    missing = [x for x in need if not os.path.exists(x)]
    print("to add: %d | not yet on disk: %s" % (len(need), missing or "none"))
    if a.apply and need and t.count(anchor) == 1:
        io.open(p, "w", encoding="utf-8", newline="").write(
            t.replace(anchor, anchor + "".join('    "%s",\n' % x for x in need), 1))
        print("mirror list extended")
    rn = "publish_clean/RELEASE_NOTES_v2.4.md"
    if a.apply and not os.path.exists(rn):
        io.open(rn, "w", encoding="utf-8", newline="").write(NOTES)
        print("wrote", rn)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())