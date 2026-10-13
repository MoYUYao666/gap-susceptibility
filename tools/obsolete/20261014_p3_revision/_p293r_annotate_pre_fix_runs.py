# -*- coding: utf-8 -*-
r"""Annotate the two pre-fix DINOv2 runs with the provenance of their `lora_update_*` fields.

Both `fitted/text_only/seed42` and `fitted/both/seed42` were started before a review caught that
the instrumentation zeroed the trained LoRA matrices before measuring them, so their
`lora_update_norm_frobenius` / `lora_update_sum_of_layer_frobenius` fields read 0.0 even though
both arms did adapt.  The trained matrices survive in each run's checkpoints.

This script does NOT rewrite the measured numbers -- that would destroy the record of what the
run actually wrote.  It adds, next to them, an explanation field and a pointer to the separate
recovery artefact, so a reader of the JSON cannot mistake 0.0 for a measurement.

OUTPUT: edits outputs/analysis/dinov2_hetero/fitted/<arm>/seed42/results.json in place, adding
        `lora_norm_invalid_reason` and `lora_norm_recovered_from`.

USAGE
    python tools/_p293r_annotate_pre_fix_runs.py
"""
from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RUNS = [REPO / "outputs" / "analysis" / "dinov2_hetero" / "fitted" / arm / "seed42"
        for arm in ("text_only", "both")]

REASON = ("invalid: this run loaded pre-fix code that zeroed the trained LoRA matrices before "
          "measuring them, so the 0.0 values above are an artefact of the instrumentation bug and "
          "are not a finding; the trained matrices were recovered separately from the run's "
          "checkpoints")


def main():
    for rd in RUNS:
        res = rd / "results.json"
        rec = rd / "lora_norm_recovered.json"
        if not res.exists():
            print("[skip] no results.json in", rd)
            continue
        d = json.loads(res.read_text(encoding="utf-8"))
        before = {k: d.get(k) for k in ("lora_update_norm_frobenius",
                                       "lora_update_sum_of_layer_frobenius")}
        d["lora_norm_invalid_reason"] = REASON
        d["lora_norm_recovered_from"] = (
            str(rec.relative_to(REPO)).replace("\\", "/") if rec.exists()
            else "no checkpoint recovery found")
        if rec.exists():
            rj = json.loads(rec.read_text(encoding="utf-8"))
            d["lora_update_recovered"] = {
                "frobenius_of_scaled_update": rj["best"]["frobenius_of_scaled_update"],
                "sum_of_per_layer_frobenius": rj["best"]["sum_of_per_layer_frobenius"],
                "note": rj.get("note"),
            }
        res.write_text(json.dumps(d, indent=2, ensure_ascii=False), encoding="utf-8")
        print("[ok] %s" % res.relative_to(REPO))
        print("     measured (left untouched): %s" % before)
        print("     recovery pointer        : %s" % d["lora_norm_recovered_from"])


if __name__ == "__main__":
    main()
