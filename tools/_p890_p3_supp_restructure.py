# -*- coding: utf-8 -*-
r"""Make P3's supplementary sections line up with the main text (option A: the main text keeps its wording).

Audit result (tools/_p880 .. _p887): the main text points at supplement sections S3--S7 that do not
exist in the supplement, and the supplement's own cross-references had lost their numbers. This script
fixes both by rebuilding the supplement, plus one small change to the main text.

Final layout of the supplement, counting sections in file order:

    S1 axiom derivation                       S6 decoder VLM
    S2 experimental details                   S7 downstream check on real pairs
    S3 GFAP error bound                       S8 transfer reasoning + companion ODE theory
    S4 per-block Gamma calculation            S9 deferred proofs + remaining detail
    S5 rank scaling                              (comparison with prior work, ShareGPT)

so the main text's pointers resolve: sample size S9, second dataset S9, rank scaling S5, comparison
with prior work S9, decoder VLM S6, downstream check S7, and its "Sections S1--S6" becomes "S1--S9".

Also repaired: every broken cross-reference inside the supplement, and the sample-size table the
supplement promised but never contained (built from the archived run records).

NOTE ON BACKSLASHES: every LaTeX backslash in the emitted text is built from chr(92). Writing them as
escape sequences in string literals collapses them (a literal backslash-s became a tab and silently
broke the section regex), which is the same class of bug that damaged two handoff documents earlier.

    python tools/_p890_p3_supp_restructure.py [--apply]
"""
from __future__ import annotations

import argparse
import collections
import io
import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
P3 = REPO / "paper3" / "paper_ieee"
SUPP = P3 / "supplementary" / "supplementary.tex"
MAIN = P3 / "main.tex"
SAMPLES = REPO / "paper3" / "scripts" / "outputs" / "experiments" / "sample_size_results.json"

B = chr(92)                       # one backslash
SEC_NAME = "section"
SUB_NAME = "subsection"
SEC_OPEN = B + SEC_NAME + "{"
SUB_OPEN = B + SUB_NAME + "{"
# `\[^a-zA-Z]` keeps the section pattern from also matching the tail of `\subsection{`
SEC_RE = r"(?<![A-Za-z])" + re.escape(SEC_OPEN) + r"([^}]*)\}"
SUB_RE = r"(?<![A-Za-z])" + re.escape(SUB_OPEN) + r"([^}]*)\}"


def split_blocks(t: str, pattern: str) -> list[tuple[str, str]]:
    """[(heading, block from heading to the next heading)] for a section or subsection pattern."""
    marks = [(m.start(), m.group(1).strip()) for m in re.finditer(pattern, t)]
    out = []
    for i, (pos, name) in enumerate(marks):
        end = marks[i + 1][0] if i + 1 < len(marks) else len(t)
        out.append((name, t[pos:end].rstrip() + "\n"))
    return out


def make_section(title: str, *blocks: str) -> str:
    body = "".join(b.rstrip() + "\n\n" for b in blocks if b and b.strip())
    return SEC_OPEN + title + "}\n" + body.rstrip() + "\n"


def drop_heading(block: str) -> str:
    """Block body without its own \\section heading: used when two sections are merged into one.

    Without this the second heading would be nested inside the first section, and both would still be
    counted, which is exactly what an earlier run of this script produced.
    """
    nl = block.find("\n")
    assert nl > 0, "block has no heading line"
    assert block.startswith(SEC_OPEN), f"block does not start with a section heading: {block[:40]!r}"
    return block[nl + 1:].lstrip("\n")


def ref(label: str) -> str:
    return B + "ref{" + label + "}"


def sample_table() -> str:
    d = json.loads(SAMPLES.read_text(encoding="utf-8"))
    runs = d["runs"]
    assert len(runs) == 20, f"expected 20 archived runs, found {len(runs)}"
    assert all(r["ok"] for r in runs), "an archived run is flagged not-ok"
    sizes = sorted({r["samples"] for r in runs})
    ranks = sorted({r["rank"] for r in runs})
    assert sizes == [16, 64, 128, 256] and ranks == [4, 5, 6, 7, 16], f"{sizes} {ranks}"
    dE: dict[int, dict[int, float]] = collections.defaultdict(dict)
    epochs, seeds = set(), set()
    for r in runs:
        dE[r["samples"]][r["rank"]] = r["E"][-1] - r["E"][0]
        epochs.add(len(r["E"]))
        seeds.add(r["name"].rsplit("_s", 1)[-1])
    assert len(epochs) == 1, f"uneven epoch counts {epochs}"
    n_ep = epochs.pop()
    body_rows = ["$n=%d$ & " % n + " & ".join("$%+.1f$" % dE[n][k] for k in ranks) + " " + B * 2
                 for n in sizes]
    # One balanced math group per value. An earlier version emitted "$" + B + "Delta E$" inside a
    # sentence that already had a "$", which left an unmatched delimiter and aborted the build.
    cap = "$" + B + "Delta E$"
    caption_lines = [
        B + "caption{Phase transition across training-set sizes on LLaVA-1.5-7B: " + cap + " from",
        "the start of training to the final epoch, one seed per configuration, %d epochs per run" % n_ep,
        "(%d runs, seed %s). The crossing of " % (len(runs), sorted(seeds)[0]) + cap + " falls between",
        "$r=5$ and $r=6$ at every sample size, and the ordering",
        "$" + B + "Delta E(r{=}6) > " + B + "Delta E(r{=}5)$ holds at all four.}",
    ]
    for line in caption_lines:
        assert line.count("$") % 2 == 0, f"unbalanced math delimiter in caption line: {line!r}"
    return "\n".join([
        B + "begin{table}[h]",
        B + "centering",
        *caption_lines,
        B + "label{tab:samplesize}",
        B + "begin{tabular}{@{}l" + "c" * len(ranks) + "@{}}",
        B + "toprule",
        "Samples & " + " & ".join("$r=%d$" % k for k in ranks) + " " + B * 2,
        B + "midrule",
        *body_rows,
        B + "bottomrule",
        B + "end{tabular}",
        B + "end{table}",
    ])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    supp = SUPP.read_text(encoding="utf-8")
    secs = split_blocks(supp, SEC_RE)
    assert len(secs) == 9, [n for n, _ in secs]
    want = ["Axiom Derivation", "Experimental Details", "GFAP Error Bound", "Detailed",
            "Transfers Across Architectures", "Companion ODE", "Deferred Proofs",
            "Deferred Experimental Detail", "Deferred Downstream"]
    for (name, _b), w in zip(secs, want):
        assert w in name, f"unexpected section order: {name!r} (expected {w!r})"
    S = {w: b for (n, b), w in zip(secs, want)}

    exp_sub = dict(split_blocks(S["Deferred Experimental Detail"], SUB_RE))
    dn_sub = dict(split_blocks(S["Deferred Downstream"], SUB_RE))
    for key in ("Rank Scaling", "Second-Dataset Validation", "Sample Size Robustness", "Decoder VLM",
                "Downstream check", "Comparison with Prior Work"):
        assert any(key in k for k in exp_sub), f"missing subsection {key!r}: {list(exp_sub)}"
    for key in ("Decoder VLM", "Downstream check"):
        assert any(key in k for k in dn_sub), f"missing summary {key!r}: {list(dn_sub)}"

    def pick(d: dict[str, str], key: str) -> str:
        return next(b for k, b in d.items() if key in k)

    new = [
        S["Axiom Derivation"],
        S["Experimental Details"],
        S["GFAP Error Bound"],
        S["Detailed"],
        make_section("Rank Scaling and $" + B + "Gamma$ Evolution", pick(exp_sub, "Rank Scaling")),
        make_section("Decoder VLM", pick(exp_sub, "Decoder VLM"), pick(dn_sub, "Decoder VLM")),
        make_section("Downstream Check on Real Image--Text Pairs",
                     pick(exp_sub, "Downstream check"), pick(dn_sub, "Downstream check")),
        make_section("Why $" + B + "Gamma$ Transfers, and the Companion ODE Theory",
                     drop_heading(S["Transfers Across Architectures"]),
                     drop_heading(S["Companion ODE"])),
        make_section("Deferred Proofs and Related Experimental Detail",
                     drop_heading(S["Deferred Proofs"]),
                     pick(exp_sub, "Comparison with Prior Work"),
                     pick(exp_sub, "Sample Size Robustness"),
                     pick(exp_sub, "Second-Dataset Validation")),
    ]
    # Everything after the last section's body — the bibliography and \end{document} — sits outside
    # every section block, so rebuilding from blocks drops it. Take it from the last block heading to
    # the end of the file and re-attach it verbatim.
    last_heading = secs[-1][1].split("\n", 1)[0]
    last_pos = supp.rindex(last_heading)
    doc_tail = supp[last_pos + len(last_heading):]
    assert B + "end{document}" in doc_tail, "the source has no closing markup after the last section"
    head = supp[: supp.index(SEC_OPEN)]
    out = head + "".join(b.rstrip() + "\n\n" for b in new)
    assert B + "end{document}" not in out, "the closing markup was carried over twice"
    out = out.rstrip() + "\n" + doc_tail.rstrip() + "\n"

    def sub_once(text: str, old: str, new_s: str, expect: int = 1) -> str:
        c = text.count(old)
        assert c == expect, f"expected {expect} occurrence(s) of {old[:58]!r}, found {c}"
        return text.replace(old, new_s, expect)

    out = sub_once(out, SUB_OPEN + "Step-by-step proof of Theorem~the main text}",
                   SUB_OPEN + "Step-by-step proof of the Representation Theorem of the main text}")
    out = sub_once(out, "Lemma~Lemma 1 of the main text", "Lemma~1 of the main text")
    out = sub_once(out, "Table~the main text reports the measured per-block values at",
                   "Table~" + ref("tab:gamma_detail") + " reports the measured per-block values at")
    out = sub_once(out, "grow monotonically with rank (Table~the main text):",
                   "grow monotonically with rank (Table~" + ref("tab:gamma_rank") + "):")
    out = sub_once(out, "Table~Supplementary Table S4 compares GFAP",
                   "Table~" + ref("tab:comparison") + " compares GFAP")
    out = sub_once(out, "Table~Supplementary Table S3 reports",
                   "Table~" + ref("tab:sharegpt") + " reports")
    out = sub_once(out, "At one epoch (Figure~Supplementary Figure S3), the mechanism",
                   "At one epoch (Figure~" + ref("fig:ers") + "), the mechanism")
    out = sub_once(out, "Table~Supplementary Table S2 shows the results.",
                   "Table~" + ref("tab:samplesize") + " shows the results.")
    anchor = "per run on LLaVA-1.5-7B. Table~" + ref("tab:samplesize") + " shows the results."
    assert out.count(anchor) == 1, "the sample-size anchor is not unique"
    out = out.replace(anchor, anchor + "\n\n" + sample_table(), 1)
    # Those two sections are now self-contained, so their "(Supplementary Section S6/S7)" tags go. Each
    # tag appears twice: once in the section itself and once in the body text it was copied from.
    out = sub_once(out, "(Supplementary Section~S6)", "", expect=2)
    out = sub_once(out, "(Supplementary Section~S7)", "", expect=2)

    for bad in ("Table~the main text", "Table~Supplementary", "Figure~Supplementary",
                "Lemma~Lemma", "Theorem~the main text", "Supplementary Section~S"):
        assert bad not in out, f"stale text remains: {bad!r}"
    names = [m.group(1).strip() for m in re.finditer(SEC_RE, out)]
    assert len(names) == 9, names
    for i, w in enumerate(["Axiom Derivation", "Experimental Details", "GFAP Error Bound",
                           "Detailed", "Rank Scaling", "Decoder VLM", "Downstream Check",
                           "Transfers", "Deferred Proofs"], 1):
        assert w in names[i - 1], f"S{i} is {names[i - 1]!r}, expected {w!r}"
    n_tab = len(re.findall(re.escape(B + "begin{table"), out))
    assert n_tab == 5, f"expected 5 tables after adding the sample-size one, found {n_tab}"

    main_t = MAIN.read_text(encoding="utf-8")
    # The main text's own pointers are handled by tools/_p891_p3_main_pointers.py, which needs the
    # reordered supplement to exist first. This script only checks that it has not already been changed.
    assert "Supplementary Sections~S1--S9" not in main_t or main_t.count("S1--S9") == 1, \
        "main.tex already carries the new range; run tools/_p891 first instead"
    main_out = main_t

    if not a.apply:
        print("  (dry run)")
        for i, n in enumerate(names, 1):
            print(f"    S{i}: {n}")
        print(f"  supplement: {len(supp.splitlines())} -> {len(out.splitlines())} lines, "
              f"tables {len(re.findall(re.escape(B + 'begin{table'), supp))} -> {n_tab}")
        print("  main text pointers: 2x S3 -> S9, S6 <-> S7, range S1--S6 -> S1--S9")
        return 0

    SUPP.write_text(out, encoding="utf-8", newline="")
    MAIN.write_text(main_out, encoding="utf-8", newline="")
    print("  supplement sections after the change:")
    for i, n in enumerate(names, 1):
        print(f"    S{i}: {n}")
    print(f"  supplement now {len(out.splitlines())} lines with {n_tab} tables")
    print("  main text pointers: 2x S3 -> S9, S6 <-> S7, range S1--S6 -> S1--S9")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
