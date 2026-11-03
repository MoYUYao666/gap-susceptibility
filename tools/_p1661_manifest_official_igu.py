#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""_p1661_manifest_official_igu.py -- register tab:igucompare in docs/provenance_manifest.json (P3).

Idempotent. The row names the generating script and every archive field path the table and the
subsection prose quote, so the provenance gate can check the paths exist.
"""
import json
import os
from pathlib import Path

ROOT = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MAN = ROOT / "docs/provenance_manifest.json"

ENTRY = {
    "label": "tab:igucompare",
    "kind": "table",
    "script": "tools/_p1639_p3_official_igu.py",
    "archive": "outputs/analysis/p3_official_vs_reimpl.json",
    "archives": [
        "outputs/analysis/p3_official_vs_reimpl.json",
        "outputs/analysis/p3_official_igu_run.json",
        "outputs/analysis/p3_official_igu_replicates.json",
    ],
    "status": "verified",
    "note": (
        "Official IGU-LoRA allocator versus the block-level integrated-gradient rule (S41 subsection "
        "app:igucompare, 2026-10-25). Fields: overall.mean_gap_delta_E, overall.ci95, overall.margin, "
        "meta.margin_fraction_of_E0, per_configuration.trained_arm_delta_E.{tost_p,"
        "min_equivalent_margin}, per_configuration.allocation.l1, allocation_sensitivity_to_the_block_"
        "mapping.{archived,corrected}.l1, same_stack_for_every_pair, stack_mix_warning, "
        "pairs[].{gap,official.env,reimpl.E}; six trained arms from runs[]; replicate dispersion from "
        "summary.{max_spread_across_arms,mean_spread_across_arms,archived_official_minus_reimpl_gap} "
        "and pinned_anchors_sha256_before/after. Scripts: tools/_p1639_p3_official_igu.py --compare "
        "(comparison) and tools/_p1646_p3_arm_replicates.py (replicate spread). Single-seed arm "
        "readings are deliberately not printed as the comparison."
    ),
}


def main():
    man = json.loads(MAN.read_text(encoding="utf-8"))
    floats = man["manuscripts"]["P3"]["floats"]
    labels = {f.get("label") for f in floats}
    if "tab:igucompare" in labels:
        print("tab:igucompare already present -- nothing to do")
        return 0
    idx = next((i for i, f in enumerate(floats) if f.get("label") == "tab:iguofficial"), None)
    if idx is None:
        floats.append(ENTRY)
    else:
        floats.insert(idx + 1, ENTRY)
    missing = [p for p in ENTRY["archives"] if not (ROOT / p).exists()]
    assert not missing, "manifest entry names missing archives: %s" % missing
    MAN.write_text(json.dumps(man, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print("inserted tab:igucompare after tab:iguofficial (index %s); %d P3 floats now"
          % (idx, len(floats)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
