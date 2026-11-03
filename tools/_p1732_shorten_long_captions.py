# -*- coding: utf-8 -*-
r"""Shorten the two remaining over-long table captions (Table 1 and the decoder-VLM table) the way Table 10 was
handled: a two-to-three-line caption states what the table is, the protocol/provenance detail moves into a
`Notes.` paragraph under the rules. Numbers are preserved by assertion, not by trust.
"""
import io
import os
import re

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

RES = "paper合/reframed/sections/50_results.tex"
APP = "paper合/reframed/sections/95_appendix_original.tex"

NEWS = {
    "tab:position_strict": {
        "path": RES,
        "caption": ("The three adaptation positions under strict freezing, scored by the change in the centroid gap "
                    "$\\Delta$CG with $R@1$ beneath it; bold marks the smallest $\\Delta$CG and the best $R@1$ in the "
                    "row. Negative $\\Delta$CG means the gap narrowed."),
        "notes": ("Every row is a five-seed mean (BioCLIP: three seeds) at 5000 samples, 10 epochs, $\\alpha=2r$ and "
                  "batch $128$; the seed-to-seed standard deviation of $\\Delta$CG is $0.0006$--$0.006$ on the four "
                  "dual-encoder rows and $0.002$, $0.010$ and $0.015$ on BioCLIP's three arms. Seed-level percentile "
                  "bootstrap intervals ($20{,}000$ resamples, seed pairing kept, at most $\\pm0.004$ here) are in "
                  "Section~\\ref{sec:r1provenance}, with the arm differences they resolve. Rows are grouped by "
                  "pre-training objective, which is what the ordering tracks: every contrastive image--text backbone "
                  "puts text-only smallest, and the two backbones trained with other objectives put both-position "
                  "there. Patch size does not separate the groups, and the two rows marked $\\dagger$ show this "
                  "directly, having been measured at the same rank under the same protocol. On the contrastive "
                  "backbones the arm that minimizes the gap (text-only) retrieves worst, so the ordering by gap runs "
                  "opposite to the ordering by $R@1$. BioCLIP was measured at rank~$4$ and its retrievals were not "
                  "recorded, so those cells are left blank rather than estimated. The provenance of the $R@1$ column, "
                  "including the one cell that does not reproduce, is in Section~\\ref{sec:r1provenance}."),
    },
    "tab:vlm": {
        "path": APP,
        "caption": ("Adaptation site on a decoder-based VLM under strict freezing (Qwen2-VL-2B-Instruct, thirteen "
                    "seeds per arm), together with the centroid gap for the same arms."),
        "notes": ("Qwen2-VL-2B-Instruct, $320$ training pairs, three epochs, batch $2$, rank $8$, bfloat16, thirteen "
                  "seeds per arm. $DG^*$ is the paired squared distance after $L_2$ normalisation, image-token pool "
                  "against caption pool, with no projection; the reduction is relative to the untrained model "
                  "($DG^* = 0.7778$, $\\mathrm{CG} = 0.7421$) and a positive entry denotes a gap smaller than the "
                  "untrained model's. The centroid gap is reported alongside and ranks the arms identically. The "
                  "spreads after $\\pm$ are population standard deviations over the thirteen seeds (the sample "
                  "standard deviations are $0.46$, $0.30$ and $1.06$), and a seed-level percentile bootstrap "
                  "($20{,}000$ resamples; \\texttt{outputs/\\allowbreak analysis/\\allowbreak "
                  "paperA\\_strict\\_bootstrap.json}) puts the arms at $98.57\\%$ [$98.33$, $98.81\\%$], "
                  "$96.74\\%$ [$96.57$, $96.88\\%$] and $89.41\\%$ [$88.82$, $89.93\\%$]."),
    },
}


def find_block(t, label):
    i = t.find("\\label{%s}" % label)
    assert i >= 0, "label not found: " + label
    start = t.rfind("\\begin{table", 0, i)
    end = t.find("\\end{table", i) + len("\\end{table}")
    return start, end


def caption_span(block):
    i = block.find("\\caption{")
    assert i >= 0
    depth = 0
    for k in range(i + len("\\caption"), len(block)):
        if block[k] == "{":
            depth += 1
        elif block[k] == "}":
            depth -= 1
            if depth == 0:
                return i, k + 1
    raise AssertionError("unbalanced caption")


def numbers(s):
    return re.findall(r"\d[\d,\.]*", s)


for label, spec in NEWS.items():
    p = spec["path"]
    t = io.open(p, encoding="utf-8").read()
    if "\\emph{Notes.}" in t and "short caption" in t:
        print("  already done:", label)
        continue
    s, e = find_block(t, label)
    block = t[s:e]
    ci, cj = caption_span(block)
    old_cap = block[ci:cj]
    # number-preservation guard: every number in the old caption must survive in caption+notes
    keep = set(numbers(old_cap))
    new_all = spec["caption"] + spec["notes"]
    missing = sorted(n for n in keep if n not in new_all)
    assert not missing, "%s: numbers dropped in the rewrite: %s" % (label, missing)
    new_block = block[:ci] + "\\caption{" + spec["caption"] + "}" + block[cj:]
    # insert the notes paragraph before \end{table}
    cut = new_block.rfind("\\end{table}")
    new_block = (new_block[:cut] + "\nvspace{2pt}\n{\\footnotesize\n\\emph{Notes.} " + spec["notes"] + "}\n"
                 + new_block[cut:])
    t = t[:s] + new_block + t[e:]
    io.open(p, "w", encoding="utf-8", newline="").write(t)
    print("  shortened caption + notes added:", label, "| old caption %d chars -> new %d + notes %d"
          % (len(old_cap), len(spec["caption"]), len(spec["notes"])))
print("done")
