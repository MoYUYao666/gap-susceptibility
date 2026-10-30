# -*- coding: utf-8 -*-
r"""Add a `--model` path override to the sweep, without touching anything else.

The retrain runs on a host where the weights were fetched through the mirror into the hub cache layout
(`.../snapshots/main`), and there is no `refs/main` file for the hub client to resolve, so loading by repo name
would fail under `HF_HUB_OFFLINE=1`. A plain path override is the smallest fix and does not touch the prompt or
the metric.

    python tools/_p1122_add_model_flag.py [--apply]
"""
from __future__ import annotations

import argparse
import ast
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "tools" / "_p820_llava_sites.py"
PY = r"D:\Anaconda\envs\pytorch\python.exe"

ARG_ANCHOR = '    ap.add_argument("--precision", choices=["4bit", "bf16"], default="4bit",\n'
ARG_NEW = ('    ap.add_argument("--model", type=str, default="",\n'
           '                    help="checkpoint path or repo id; empty keeps the LLaVA default")\n')

# right after the arguments are parsed, before MODEL is used
PARSE_ANCHOR = "    a = ap.parse_args()\n"
PARSE_NEW = ("    global MODEL\n"
             "    if a.model:\n"
             "        MODEL = a.model\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = SCRIPT.read_text(encoding="utf-8")
    if '"--model"' in t:
        print("  already present")
        return 0
    assert t.count(ARG_ANCHOR) == 1, "precision argument anchor not found once"
    assert t.count(PARSE_ANCHOR) == 1, "parse_args anchor not found once"
    t = t.replace(ARG_ANCHOR, ARG_NEW + ARG_ANCHOR, 1)
    t = t.replace(PARSE_ANCHOR, PARSE_ANCHOR + PARSE_NEW, 1)
    ast.parse(t)
    print("  added --model and the override right after parsing")
    if not a.apply:
        print("  (dry run)")
        return 0
    SCRIPT.write_text(t, encoding="utf-8", newline="")
    r = subprocess.run([PY, "-c", "import ast,io;ast.parse(io.open(r'" + str(SCRIPT)
                        + "',encoding='utf-8').read());print('local parse ok')"], capture_output=True)
    print("  " + r.stdout.decode("utf-8", "replace").strip())
    if r.returncode != 0:
        print(r.stderr.decode("utf-8", "replace"))
        return 1
    check = SCRIPT.read_text(encoding="utf-8")
    print("  --model present:", '"--model"' in check, "| override present:", "if a.model:" in check)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
