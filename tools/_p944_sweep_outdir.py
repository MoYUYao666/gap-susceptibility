# -*- coding: utf-8 -*-
r"""Give the sweep an `--out-dir`, so timing runs cannot collide with the real records.

The first benchmark run produced only one usable number: configuration 1 wrote
`outputs/llava_sites/text_only_s42.json`, and configurations 2 and 3 then hit the sweep's
"already complete, skipping" branch and returned in 30 s. The skip logic is right for the real sweep and
wrong for timing runs, so the output directory becomes a parameter.

    python tools/_p944_sweep_outdir.py [--apply]
"""
from __future__ import annotations

import argparse
import ast
import re
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "tools" / "_p820_llava_sites.py"
PY = r"D:\Anaconda\envs\pytorch\python.exe"

ARG_RE = re.compile(r'( *ap\.add_argument\("--bench-steps", type=int, default=0,\n(?: .*\n)*?.*\)\n)')
ARG_NEW = ('    ap.add_argument("--out-dir", type=str, default="",\n'
           '                    help="write records here instead of outputs/llava_sites (timing runs)")\n')

OUTDIR_RE = re.compile(r'^OUT_DIR = .*$', re.M)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    t = SCRIPT.read_text(encoding="utf-8")
    if "--out-dir" in t:
        print("  already patched")
        return 0
    print("  OUT_DIR line:", OUTDIR_RE.search(t).group(0)[:90])

    m = ARG_RE.search(t)
    assert m, "the --bench-steps argument block was not found"
    out = t[: m.end(1)] + ARG_NEW + t[m.end(1):]

    # apply the override after the arguments are parsed
    anchor = "    a = ap.parse_args()\n"
    assert out.count(anchor) == 1, "the parse_args line was not found exactly once"
    out = out.replace(anchor, anchor + '    if a.out_dir:\n'
                                    '        global OUT_DIR\n'
                                    '        OUT_DIR = Path(a.out_dir)\n'
                                    '        OUT_DIR.mkdir(parents=True, exist_ok=True)\n', 1)

    ast.parse(out)
    print("  added --out-dir and the OUT_DIR override")
    if not a.apply:
        print("  (dry run)")
        return 0
    SCRIPT.write_text(out, encoding="utf-8", newline="")
    check = SCRIPT.read_text(encoding="utf-8")
    assert "--out-dir" in check and "global OUT_DIR" in check
    r = subprocess.run([PY, "-c", "import ast,io;ast.parse(io.open(r'" + str(SCRIPT)
                        + "',encoding='utf-8').read());print('ok')"], capture_output=True)
    assert r.returncode == 0, r.stderr.decode("utf-8", "replace")
    print("  written; the sweep's own interpreter parses it")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
