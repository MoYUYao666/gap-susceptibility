# -*- coding: utf-8 -*-
r"""Make the aggregate file report the precision that actually ran, instead of a hard-coded "4-bit nf4".

The twelve archived records came from a bfloat16 run, but the summary they are written into says:

    "quantisation": "4-bit nf4"
    "caveat": "4-bit is required to fit the 8.6 GB device; ..."

Those two strings were written for the earlier 4-bit development runs and were never tied to `--precision`.
Anyone citing that file -- for example a table caption in a manuscript -- would state the wrong configuration,
which is exactly the kind of unsourced number this project forbids. The values are therefore derived from the
run's own arguments, and the bf16 wording is written for bf16.

The existing `llava_sites.json` in the pulled-back archive is corrected in place by the companion script
`tools/_p1053_fix_archive_metadata.py`, since the file is an archived result and must not be regenerated.

    python tools/_p1052_fix_quant_label.py [--apply]
"""
from __future__ import annotations

import argparse
import ast
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "tools" / "_p820_llava_sites.py"
PY = r"D:\Anaconda\envs\pytorch\python.exe"

OLD = '''    results = {"model": MODEL, "quantisation": "4-bit nf4",
               "caveat": ("4-bit is required to fit the 8.6 GB device; the supplement records that "
                          "4-bit made its gap measurement unreproducible, so these numbers carry "
                          "that limitation and the seed spread is reported alongside"),
               "isolation_verified": verified, "runs": []}
'''
NEW = '''    # The precision is reported from the run that produced the file. The earlier hard-coded "4-bit nf4"
    # was written for the development runs and stayed in place after --precision bf16 was added, so a bf16
    # run wrote a 4-bit label into its own summary; that mislabels the configuration for anyone citing it.
    if a.precision == "4bit":
        _quant = "4-bit nf4"
        _caveat = ("4-bit is required for small devices; the supplement records that 4-bit made its gap "
                   "measurement unreproducible, so these numbers carry that limitation and the seed spread "
                   "is reported alongside")
    else:
        _quant = "bfloat16 (no quantisation)"
        _caveat = ("bfloat16 throughout, which the supplement reports as reproducible; the model needs "
                   "about 30 GB of device memory at this precision")
    results = {"model": MODEL, "quantisation": _quant, "precision": a.precision,
               "caveat": _caveat, "isolation_verified": verified, "runs": []}
'''


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = SCRIPT.read_text(encoding="utf-8")
    if "_quant = " in t:
        print("  already fixed")
        return 0
    assert OLD in t, "the hard-coded label block was not found verbatim"
    t = t.replace(OLD, NEW, 1)
    ast.parse(t)
    print("  the summary now derives its precision label from --precision")
    if not a.apply:
        print("  (dry run)")
        return 0
    SCRIPT.write_text(t, encoding="utf-8", newline="")
    r = subprocess.run([PY, "-c", "import ast,io;ast.parse(io.open(r'" + str(SCRIPT)
                        + "',encoding='utf-8').read());print('local parse ok')"], capture_output=True)
    print("  " + r.stdout.decode("utf-8", "replace").strip())
    return 0 if r.returncode == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
