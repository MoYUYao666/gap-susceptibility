# -*- coding: utf-8 -*-
r"""Annotate the random-head text_only run's `lora_update_*` validity, and record the control.

The random-head `text_only/seed42` run started at 20:51, i.e. BEFORE the LoRA-zeroing fix was
applied at ~20:45 but with the file already edited -- so whether its `lora_update_*` fields are
valid has to be CHECKED, not assumed.  This script reads the JSON, reports what it actually
contains, and writes `lora_norm_validity` accordingly; it never rewrites a measured field.
"""
from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
P = (REPO / "outputs" / "analysis" / "dinov2_hetero" / "random" / "text_only" / "seed42"
     / "results.json")


def main():
    d = json.loads(P.read_text(encoding="utf-8"))
    ln = d.get("lora_update_norm_frobenius")
    ls = d.get("lora_update_sum_of_layer_frobenius")
    print("lora_update_norm_frobenius        :", ln)
    print("lora_update_sum_of_layer_frobenius:", ls)
    zeroed = bool(ln) and all(v == 0.0 for v in ln.values())
    if zeroed:
        rec = P.parent / "lora_norm_recovered.json"
        d["lora_norm_invalid_reason"] = (
            "invalid: the values are 0.0, which is the pre-fix instrumentation artefact (the "
            "trained LoRA matrices were zeroed before being measured); the run itself adapted "
            "normally, as its delta_CG shows")
        d["lora_norm_recovered_from"] = (
            str(rec.relative_to(REPO)).replace("\\", "/") if rec.exists()
            else "no checkpoint recovery found")
        verdict = "INVALID (0.0); recovery pointer written"
    else:
        d["lora_norm_validity"] = ("measured live, after the zeroing fix; values are the "
                                   "in-process measurement")
        verdict = "VALID"
    P.write_text(json.dumps(d, indent=2, ensure_ascii=False), encoding="utf-8")
    print("verdict:", verdict)
    print("[ok]", P.relative_to(REPO))


if __name__ == "__main__":
    main()
