# -*- coding: utf-8 -*-
r"""Mirror additions for the cloud round (2026-10-24 evening): decoder ladder + 451-question VQA + cloud bundle.

    python tools/_p1619_prepare_v25.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(REPO)

FILES = [
    "tools/_p1612_objective_control_multimodel.py",
    "tools/_p1613_p3_cloud_runner.py",
    "tools/_p1614_a23_multi_encoder_transfer.py",
    "tools/_p1615_cloud_exec.py",
    "cloud_next/README.md",
    "cloud_next/env_setup.sh",
    "cloud_next/run_all.sh",
    "cloud_next/p1_driver.sh",
    "cloud_next/p3_env_seeds.sh",
    "cloud_next/a23_encoders.sh",
    "cloud_next/verify_cloud_artifacts.py",
    "cloud_next/expected_outputs.json",
    "outputs/analysis/decoder_attribution_qwen2vl-2b_contrastive_seed42.json",
    "outputs/analysis/decoder_attribution_qwen2vl-2b_generative_seed42.json",
    "outputs/analysis/decoder_attribution_llava15-7b_contrastive_seed42.json",
    "outputs/analysis/decoder_attribution_llava15-7b_generative_seed42.json",
    "outputs/analysis/decoder_attribution_qwen25vl-7b_generative_seed42.json",
    "outputs/analysis/cloud_vqa_full451_base.json",
    "outputs/analysis/cloud_vqa_full451_5.json",
    "outputs/analysis/cloud_vqa_full451_6.json",
    "outputs/analysis/p3_vqa_full_equivalence.json",
    "outputs/analysis/a23_multiencoder_transfer.json",
    "docs/CLOUD_RUNBOOK_2026-10-24.md",
    "docs/decoder_attribution_cloud_notes.md",
    "docs/p3_cloud_round_notes.md",
    "docs/p3_vqa451_round_notes.md",
    "docs/a23_multiencoder_cloud_notes.md",
    "docs/DECODER_CONTROL_CAP_CORRECTION_2026-10-24.md",
]

NOTES_ADDENDUM = """
## v2.5 (unreleased) - cloud round of 24 October 2026

Not yet tagged; these files are on `main` and would form the next version.

- `tools/_p1612_objective_control_multimodel.py` - matched decoder ladder (four model registries, two objectives,
  two protocols, tower isolation, non-finite-step guard, A/B frozen check).
- `tools/_p1613_p3_cloud_runner.py` - environment-stack seeds and 451-question VQA evaluation with paired
  bootstrap and TOST equivalence.
- `tools/_p1614_a23_multi_encoder_transfer.py` - multi-encoder threshold-transfer grid (7 encoders x 3 corpora).
- `tools/_p1615_cloud_exec.py` - the SSH/SFTP helper used to drive the instance (password from the environment).
- `cloud_next/` - the prepared, resumable cloud bundle: mirror-first setup, phase driver, per-phase entry points,
  expected-output manifest and the pre-shutdown gate.
- Result archives: the five `decoder_attribution_*` ladder runs, the three `cloud_vqa_full451_*` arms plus their
  equivalence archive, and the multi-encoder transfer archive.
- Notes: the cloud runbook, the three preparation notes, and the correction note for the earlier local control's
  image-token budget.
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
    print("to add: %d | not on disk: %s" % (len(need), missing or "none"))
    if a.apply and need:
        assert t.count(anchor) == 1, "mirror list anchor not unique"
        io.open(p, "w", encoding="utf-8", newline="").write(
            t.replace(anchor, anchor + "".join('    "%s",\n' % x for x in need), 1))
        print("mirror list extended")
    rn = "publish_clean/RELEASE_NOTES_v2.5.md"
    if a.apply and not os.path.exists(rn):
        io.open(rn, "w", encoding="utf-8", newline="").write(
            "# Release notes - v2.5 (unreleased)\n" + NOTES_ADDENDUM)
        print("wrote", rn)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())