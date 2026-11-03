# -*- coding: utf-8 -*-
"""Assert the 2026-10-17 consistency fixes in Paper A's live sources (read-only gate).

Checks every corrected sentence is present and every superseded wording is absent.
    python tools/_p1181_verify_paperA_consistency.py
"""
from __future__ import annotations

import io
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PA = REPO / "paper合"
FAILS = []


def read(rel):
    return io.open(PA / rel, encoding="utf-8").read()


def need(text, needle, label, present=True):
    ok = (needle in text) if present else (needle not in text)
    print(("PASS  " if ok else "FAIL  ") + label)
    if not ok:
        FAILS.append(label)


def main():
    emp = read("sections/empirical.tex")
    need(emp, "117 under the earlier convention and 104 under strict freezing", "empirical: 104 strict-freezing count")
    need(emp, "95 under strict freezing", "empirical: stale 95 absent", present=False)
    need(emp, "BLIP-1 $1.97", "empirical: BLIP-1 naming")
    need(emp, "BLIP-2", "empirical: stale BLIP-2 absent", present=False)
    need(emp, "decoder-model controls (Appendix Sections E and G) use batch size 2", "empirical: decoder batch scope")
    val = read("sections/validation.tex")
    need(val, "three random seeds", "validation: three seeds")
    need(val, "Full FT (matched sweep, 5 seeds)", "validation: phase2 FT row")
    need(val, "five-seed matched full-fine-tuning sweep fits at $0.987$", "validation: figure caption FT R2")
    need(val, "across the 11 archived fits", "validation: 0.922 provenance")
    need(val, "The rank-trend $\\beta$ values quoted in Section", "validation: two-batch note")
    need(val, "spanning the LoRA, Adapter and full-fine-tuning adaptations", "validation: adaptation wording")
    theo = read("sections/theory.tex")
    need(theo, "five-seed native fits (reported separately from the per-run fits", "theory: rank-trend batch label")
    need(theo, "five-seed matched sweep", "theory: full-FT batch label")
    disc = read("sections/discussion.tex")
    need(disc, "averaged over the 11 archived fits", "discussion: 0.922 provenance")
    supp = read("sections/supplement.tex")
    need(supp, "221 catalogued experiments, together with the 96 archived ODE-fit records", "supplement: release scope")
    need(supp, "all 383 experiments are released", "supplement: stale all-383 claim absent", present=False)
    need(supp, "$89.41\\%$ reduction against $96.74\\%$", "supplement: E numbers in E comparison")
    need(supp, "$121.48\\%$ against $73.27\\%$ and $95.66\\%$ increases", "supplement: G numbers in G comparison")
    # 2026-10-24b decoder-ladder round: Section H.2 is new, and the local control's budget claim is
    # corrected there, so the corrected sentence must be present and the old description gone.
    need(supp, "\\subsection*{H.2 A matched ladder over family and scale}", "supplement: Section H.2 exists")
    need(supp, "\\label{sec:decoderladder}", "supplement: ladder label exists")
    need(supp, "$1200$--$2500$ image tokens per image", "supplement: local control real resolution stated")
    need(supp, "at a reduced image resolution", "supplement: stale reduced-resolution claim absent", present=False)
    rw = read("sections/related_work.tex")
    need(rw, "driving coefficient estimated from the gradient identity", "related_work: coefficient name")
    # abstract word count must equal the source-side count (math expressions as one token)
    am = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", read("main_nc.tex"), re.S)
    aa = re.sub(r"\$[^$]*\$", " X ", am.group(1))
    aa = re.sub(r"\\[a-zA-Z]+\*?", " ", aa)
    aw = len([w for w in aa.replace("{", " ").replace("}", " ").split() if any(ch.isalnum() for ch in w)])
    for rel in ("cover_letter_nc.tex", "cover_letter.tex"):
        t = read(rel)
        need(t, "driving coefficient estimated from the gradient identity", rel + ": coefficient name")
        need(t, "batch size 128 and the decoder-model controls batch size 2", rel + ": batch sizes")
        need(t, "automated claim ledger (74 assertions, no gaps)", rel + ": ledger claim")
        need(t, "dual-encoder result files", rel + ": data scope")
        need(t, "decoder-model per-run", rel + ": decoder data on request")
        need(t, "three adaptation methods", rel + ": adaptation wording")
        need(t, "an abstract of %d words" % aw, rel + ": abstract count matches source")
        need(t, "longest 62 characters", rel + ": highlights length")
    for rel in ("main_nc.tex", "main_springer.tex"):
        t = read(rel)
        need(t, "three adaptation methods", rel + ": adaptation wording")
        need(t, "Across $n=204$ archived runs,", rel + ": abstract cells wording")
        need(t, "drawn from six", rel + ": stale cells wording absent", present=False)
        # v2.3 (2026-10-24) includes the decoder per-run records; only the adapters are withheld.
        need(t, "10.5281/zenodo.23632347", rel + ": data DOI is the v2.3 snapshot")
        need(t, "includes the decoder-model records of Appendix Sections E and G", rel + ": data scope")
        need(t, "adapters are not redistributed", rel + ": adapters withheld")
    conc = read("sections/conclusion.tex")
    need(conc, "three adaptation methods", "conclusion: adaptation wording")
    need(conc, "Across the $96$ archived ODE fits, $\\alpha < 0$ in $92$", "conclusion: alpha count")
    intro = read("sections/introduction.tex")
    need(intro, "spanning three adaptation methods", "introduction: adaptation wording")
    hl = read("highlights_nc.tex")
    need(hl, "reproduces measured gap trajectories", "highlights: reproduces wording")
    # dynamic checks: cover-letter page count and abstract word count must match the built sources
    from pypdf import PdfReader
    nc_pages = len(PdfReader(str(PA / "main_nc.pdf")).pages)
    for rel in ("cover_letter_nc.tex", "cover_letter.tex"):
        t = read(rel)
        m = re.search(r"The manuscript is (\d+) pages", t)
        ok = m is not None and int(m.group(1)) == nc_pages
        print(("PASS  " if ok else "FAIL  ") + rel + ": cover-letter page count matches main_nc.pdf")
        if not ok:
            FAILS.append(rel + ": cover-letter page count")
    print("RESULT: %d failure(s)" % len(FAILS))
    return 0 if not FAILS else 1


if __name__ == "__main__":
    raise SystemExit(main())
