# -*- coding: utf-8 -*-
r"""Verify that every number in the new README traces to an archived source record.

Standing project principle: every number must name the script that produced it and the
archive file and field that holds it. The README quotes several statistics, so each one is
checked against the archive before the README is committed.

    python tools/_p618_verify_readme_numbers.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PC = REPO / "publish_clean"
OUT = REPO / "outputs" / "analysis" / "readme_numbers_verify.json"

# (label, list of acceptable literal representations, expected value for context)
CLAIMS = [
    ("uniform baseline at 5e-5", ["+5048", "5048"], None),
    ("experimental arm at 5e-5", ["+1478", "1478"], None),
    ("std of experimental arm", ["1563"], None),
    ("std of uniform arm", ["1900"], None),
    ("p-value at 5e-5", ["0.0055"], None),
    ("reversal 3e-4 experimental", ["+5968", "5968"], None),
    ("reversal 3e-4 uniform", ["+2842", "2842"], None),
    ("matched loss arms", ["0.5872", "0.5826"], None),
    ("random-allocation p-value", ["0.2057"], None),
    ("AdaLoRA margin", ["-1468", "1468"], None),
    ("AdaLoRA margin 2", ["-757", "757"], None),
    ("permutation p for crossing", ["0.100"], None),
    ("between-rank variance share", ["98.9"], None),
    ("matched parameter budget", ["7,237,632", "7237632"], None),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    rd = io.open(PC / "README.md", encoding="utf-8").read()

    # collect all numeric tokens present anywhere in outputs/
    print("  Indexing numeric tokens under outputs/ ...")
    r = subprocess.run(["git", "ls-files", "outputs"], cwd=str(PC), capture_output=True)
    files = [x for x in r.stdout.decode("utf-8", errors="replace").splitlines() if x.strip()]
    blob = []
    for rel in files:
        if not rel.endswith((".json", ".txt", ".md")):
            continue
        p = PC / rel
        if not p.exists():
            continue
        try:
            blob.append(p.read_text(encoding="utf-8", errors="ignore"))
        except Exception:
            pass
    all_text = "\n".join(blob)
    print(f"  {len(files)} archived files, {len(all_text):,} characters indexed")
    print()

    rows = []
    ok = 0
    for label, variants, _ in CLAIMS:
        # is the claim present in the README at all?
        in_readme = any(v.lstrip("+") in rd for v in variants)
        found = None
        for v in variants:
            if v in all_text:
                found = v
                break
        status = "OK " if (found and in_readme) else ("READMEmissing" if not in_readme else "NOSOURCE")
        if status == "OK ":
            ok += 1
        rows.append({"label": label, "in_readme": in_readme, "found_in_archive": found,
                     "status": status})
        print(f"  {status:<14} {label:<32} archive match: {found}")

    print()
    print(f"  {ok}/{len(CLAIMS)} claims have a literal match in the archive")
    print()
    print("  Note on the limits of this check: a literal match proves the digits exist")
    print("  somewhere under outputs/, not that the README attributes them to the right")
    print("  run. The manuscript's own claim ledger is the stronger gate.")
    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(
            {"claims": rows, "ok": ok, "total": len(CLAIMS),
             "archived_files": len(files)}, ensure_ascii=False, indent=1))
        print(f"\n  Wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
