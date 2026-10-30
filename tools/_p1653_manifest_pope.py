#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""_p1653_manifest_pope.py -- register tab:pope in docs/provenance_manifest.json (P3) with its
generating script and archive field paths, then leave the gate in tools/_p1428 to verify it.

Idempotent: if the P3 float list already holds tab:pope it makes no change.
"""
import json
import os
from pathlib import Path

ROOT = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MAN = ROOT / "docs/provenance_manifest.json"

ENTRY = {
    "label": "tab:pope",
    "kind": "table",
    "script": "tools/_p1640_p3_second_downstream.py",
    "archive": "outputs/analysis/p3_second_downstream.json",
    "archives": [
        "outputs/analysis/p3_second_downstream.json",
        "outputs/analysis/p3_second_downstream_base.json",
        "outputs/analysis/p3_second_downstream_5.json",
        "outputs/analysis/p3_second_downstream_6.json",
        "outputs/analysis/p3_pope_corrected_metrics.json",
    ],
    "status": "verified",
    "note": (
        "POPE second downstream task (S29 subsection, 2026-10-25). Fields: arms.*.{accuracy,"
        "token_f1,pope_f1,yes_ratio}, contrasts.*.{accuracy,token_f1,pope_f1}.{delta,ci95}, "
        "meta.dataset.n_questions, meta.declared_margins, claim_verdict.metric_directions; "
        "confusion counts from the three per-arm archives. The aggregate was regenerated locally "
        "by the corrected script after defects D1 (arms.*.token_f1 held relaxed_accuracy) and D2 "
        "(verdict rule sign inverted); see docs/p3_pope_integration_notes.md and the independent "
        "recomputation p3_pope_corrected_metrics.json. The pre-correction cloud aggregate "
        "(sha256 1c389125f0c3ce55...) is superseded (p3_second_downstream_pre_correction.json)."
    ),
}


def main():
    man = json.loads(MAN.read_text(encoding="utf-8"))
    floats = man["manuscripts"]["P3"]["floats"]
    labels = {f.get("label") for f in floats}
    if "tab:pope" in labels:
        print("tab:pope already present in the manifest -- nothing to do")
        return 0
    # insert immediately after the VQA-RAD table it sits beside
    idx = next((i for i, f in enumerate(floats) if f.get("label") == "tab:vqa"), None)
    if idx is None:
        floats.append(ENTRY)
    else:
        floats.insert(idx + 1, ENTRY)
    # every named archive must exist before the entry is written
    missing = [p for p in ENTRY["archives"] if not (ROOT / p).exists()]
    assert not missing, "manifest entry names missing archives: %s" % missing
    MAN.write_text(json.dumps(man, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print("inserted tab:pope after tab:vqa (index %s); %d P3 floats now"
          % (idx, len(floats)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
