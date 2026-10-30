# -*- coding: utf-8 -*-
r"""Build the provenance corpora on the cloud machine (same scripts as locally).

Produces, for RSICD and NWPU-Captions:
  corpora/<dataset>/human.jsonl, segmented.jsonl, templated.jsonl, metadata.jsonl
  corpora/<dataset>/humanrich.jsonl
with the same provenance_manifest.json files as the local build.

Usage
  python build_corpora.py
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = sys.executable


def run(script, args):
    cmd = [PY, os.path.join(ROOT, "scripts", script)] + args
    print("==", " ".join(os.path.basename(c) for c in cmd))
    subprocess.run(cmd, check=True, cwd=ROOT)


def main():
    for dataset in ("rsicd", "nwpu_captions"):
        ann = os.path.join(ROOT, "data", dataset + ".jsonl")
        out = os.path.join(ROOT, "corpora", dataset)
        run("build_text_provenance.py", ["--input", ann, "--out", out])
        run("make_humanrich_corpus.py", ["--dataset", dataset])
    print("corpora ready")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
