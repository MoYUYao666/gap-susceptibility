# -*- coding: utf-8 -*-
r"""Item B: move three tables and the proof of Proposition 3 into an appendix, keeping the main text lean.

Moved to the appendix (each is referenced from the main text, so numbering still resolves):
  tab:protocol   checkpoint-selection rules
  tab:morebench  further benchmarks with bootstrap intervals
  tab:standard   minimum reporting standard
  the proof of Proposition 3 (text-side confound)

The appendix is inserted before the bibliography. Extraction is anchored on the labels, so it fails loudly if the
document structure changes instead of cutting the wrong block.

    python tools/_p1271_move_to_appendix.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAIN = os.path.join(REPO, "paper_a1", "main.tex")
BIB = "\\begin{thebibliography}"


def extract_table(t: str, label: str):
    i = t.find("\\label{%s}" % label)
    assert i > 0, label
    start = t.rfind("\\begin{table}", 0, i)
    end_marker = "\\end{table}"
    end = t.find(end_marker, i)
    assert start > 0 and end > i, label
    return t[start:end + len(end_marker)]


def extract_proof(t: str, label: str):
    i = t.find("\\label{%s}" % label)
    assert i > 0, label
    start = t.find("\\begin{proof}", i)
    end_marker = "\\end{proof}"
    end = t.find(end_marker, start)
    assert start > i and end > start
    return t[start:end + len(end_marker)]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(MAIN, encoding="utf-8").read()
    assert "\\appendix" not in t, "appendix already present"

    tables = {lab: extract_table(t, lab) for lab in ("tab:protocol", "tab:morebench", "tab:standard")}
    proof3 = extract_proof(t, "prop:confound")
    print("  extracted tables:", {k: len(v) for k, v in tables.items()})
    print("  extracted proof of Proposition 3:", len(proof3), "chars")

    # remove the found blocks from the main text (longest first keeps the search valid for distinct blocks)
    for block in list(tables.values()) + [proof3]:
        assert t.count(block) == 1, block[:60]
        t = t.replace(block, "", 1)
    # tidy the whitespace left behind by the removals
    while "\n\n\n" in t:
        t = t.replace("\n\n\n", "\n\n")

    appendix = (
        "\n\\appendix\n"
        "\\section{Appendix: proofs and full tables}\n\n"
        "\\subsection{Proof of Proposition~\\ref{prop:confound}}\n"
        + proof3.strip() + "\n\n"
        "\\subsection{Full tables}\n\n"
        "Tables~\\ref{tab:protocol}, \\ref{tab:morebench} and \\ref{tab:standard} collect the checkpoint-selection\n"
        "outcome, the further-benchmark replication with bootstrap intervals, and the reporting standard.\n\n"
        + tables["tab:protocol"] + "\n\n"
        + tables["tab:morebench"] + "\n\n"
        + tables["tab:standard"] + "\n"
    )

    k = t.find(BIB)
    print(f"  bibliography anchor: {k}")
    assert k > 0
    t = t[:k] + appendix + "\n" + t[k:]

    for lab in ("tab:protocol", "tab:morebench", "tab:standard"):
        print(f"  {lab}: label count {t.count('label{%s}' % lab)}, ref count {t.count('ref{%s}' % lab)}")
    if not a.apply:
        print("  (dry run)")
        return 0
    io.open(MAIN, "w", encoding="utf-8", newline="").write(t)
    print("  written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
