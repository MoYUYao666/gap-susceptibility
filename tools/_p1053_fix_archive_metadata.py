# -*- coding: utf-8 -*-
r"""Correct the precision label inside the archived summary, and record the correction.

`outputs/llava_bf16_sites_cloud/llava_sites.json` is an archived result of the bfloat16 run, but the sweep
wrote it with the hard-coded 4-bit label. The archive is not regenerated (regenerating would need the host,
which is switched off), so exactly the two wrong fields are corrected, the original values are kept beside
them under `_label_correction`, and the edit is logged. Nothing else in the file is touched, and the change is
verified afterwards by re-reading and comparing every other key.

    python tools/_p1053_fix_archive_metadata.py            # report only
    python tools/_p1053_fix_archive_metadata.py --apply
"""
from __future__ import annotations

import argparse
import io
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ARCHIVE = REPO / "outputs" / "llava_bf16_sites_cloud" / "llava_sites.json"
LOG = REPO / "docs" / "archive_metadata_fix_2026-10-16.md"

CORRECT_QUANT = "bfloat16 (no quantisation)"
CORRECT_CAVEAT = ("bfloat16 throughout, which the supplement reports as reproducible; the model needs "
                  "about 30 GB of device memory at this precision")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not ARCHIVE.exists():
        print(f"  {ARCHIVE} is missing")
        return 2
    before = json.loads(io.open(ARCHIVE, encoding="utf-8").read())
    print("  current fields:")
    for k in ("model", "quantisation", "caveat", "precision"):
        print(f"    {k}: {str(before.get(k))[:96]}")

    needs = (before.get("quantisation") != CORRECT_QUANT
             or before.get("caveat") != CORRECT_CAVEAT
             or before.get("precision") != "bf16")
    if not needs:
        print("  already correct")
        return 0

    after = json.loads(json.dumps(before))  # deep copy
    after["quantisation"] = CORRECT_QUANT
    after["caveat"] = CORRECT_CAVEAT
    after["precision"] = "bf16"
    after["_label_correction"] = {
        "date": "2026-10-16",
        "reason": ("The run used --precision bf16, but the script wrote a hard-coded '4-bit nf4' label and a "
                   "4-bit caveat. Corrected so that anyone citing this file states the real configuration."),
        "original_quantisation": before.get("quantisation"),
        "original_caveat": before.get("caveat"),
        "script_fix": "tools/_p1052_fix_quant_label.py",
    }

    changed = [k for k in after if before.get(k) != after.get(k)]
    print(f"  fields corrected: {changed}")
    untouched = [k for k in before if k not in changed]
    print(f"  fields untouched: {len(untouched)} ({', '.join(sorted(untouched))})")

    if not a.apply:
        print("  (dry run)")
        return 0

    ARCHIVE.write_text(json.dumps(after, ensure_ascii=False, indent=1), encoding="utf-8", newline="")
    # verify: everything except the corrected keys and the added note is identical
    check = json.loads(io.open(ARCHIVE, encoding="utf-8").read())
    same = all(check[k] == before[k] for k in untouched)
    print(f"  written; untouched fields still equal: {same}")
    if not same:
        return 1

    LOG.parent.mkdir(parents=True, exist_ok=True)
    with io.open(LOG, "w", encoding="utf-8", newline="") as fh:
        fh.write("# Archive metadata correction, 2026-10-16\n\n")
        fh.write(f"File: `{ARCHIVE.relative_to(REPO)}`\n\n")
        fh.write("The twelve records came from a bfloat16 run; the summary carried a hard-coded '4-bit nf4' "
                 "label written for the earlier development runs.\n\n")
        fh.write(f"- `quantisation`: `{before.get('quantisation')}` -> `{CORRECT_QUANT}`\n")
        fh.write(f"- `caveat`: replaced with the bfloat16 wording\n")
        fh.write(f"- `precision`: added, `bf16`\n")
        fh.write(f"- `_label_correction`: added, keeping the original values\n\n")
        fh.write("All 12 runs and every metric are unchanged.\n")
    print(f"  wrote {LOG.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
