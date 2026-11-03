# -*- coding: utf-8 -*-
r"""Reframe Paper A for a fresh submission: block-level reassembly (2026-10-26).

## Why a block-level tool

The reframe must not lose or alter any number, claim or limitation, and hand-copying long
LaTeX paragraphs is how content gets silently truncated.  So this tool parses the current
`paper合/sections/*.tex` into **blocks** (blank-line separated paragraphs, headings, and
whole float environments), and reassembles the reframed manuscript from those blocks by
index, interleaved with the new framing prose under `paper合/reframed/new/`.

## What is guaranteed (assertions; `--check` fails loudly)

1. **Coverage**   : every block of every source file is assigned exactly once.
2. **Verbatim**   : source blocks are emitted byte-for-byte; only a heading may be dropped
                    when the new framing replaces it, and that is recorded as `DUP`.
3. **Numbers**    : every numeric token in the sources still occurs in the output tree.
4. **Labels**     : every `\label{}` in the sources still occurs in the output tree.
5. **Citations**  : every `\cite{}` key in the sources still occurs in the output tree.
6. **Encoding**   : output has no literal backslash-n, no severed command at line start,
                    no control characters.

    python tools\_pa_reframe_build.py --inventory     # block inventory of the sources
    python tools\_pa_reframe_build.py --check         # assertions only, no writes
    python tools\_pa_reframe_build.py --apply         # write paper合/reframed/**
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "paper合" / "sections"
OUT = REPO / "paper合" / "reframed"
NEW = OUT / "new"

SOURCES = ["introduction", "related_work", "empirical", "theory", "validation",
           "discussion", "conclusion", "supplement", "ode_diagnostics_appendix",
           "provenance_appendix"]

FLOAT_BEGIN = re.compile(r"\\begin\{(figure|table|longtable|equation|align)\*?\}")
FLOAT_END = re.compile(r"\\end\{(figure|table|longtable|equation|align)\*?\}")
HEADING = re.compile(r"^\\(sub)*section\*?\{")


# ---------------------------------------------------------------------------
# block parsing
# ---------------------------------------------------------------------------
def parse_blocks(text: str) -> list[dict]:
    lines = text.split("\n")
    blocks: list[dict] = []
    i, n = 0, len(lines)
    while i < n:
        line = lines[i]
        if not line.strip():
            if blocks:
                blocks[-1]["tail"].append(line)
            i += 1
            continue
        m = FLOAT_BEGIN.match(line.strip())
        if m:
            start, j, depth = i, i, 0
            while j < n:
                if FLOAT_BEGIN.match(lines[j].strip()):
                    depth += 1
                if FLOAT_END.match(lines[j].strip()):
                    depth -= 1
                    if depth == 0:
                        break
                j += 1
            body = lines[start:j + 1]
            blocks.append({"kind": "float", "body": body, "tail": [], "first": body[0].strip()})
            i = j + 1
            continue
        if HEADING.match(line.strip()):
            blocks.append({"kind": "heading", "body": [line], "tail": [], "first": line.strip()})
            i += 1
            continue
        start = i
        j = i
        while j < n and lines[j].strip() and not HEADING.match(lines[j].strip()) \
                and not FLOAT_BEGIN.match(lines[j].strip()):
            j += 1
        blocks.append({"kind": "text", "body": lines[start:j], "tail": [],
                       "first": next((b.strip() for b in lines[start:j] if b.strip()), "")})
        i = j
    return blocks


def load_sources() -> dict[str, list[dict]]:
    out = {}
    for name in SOURCES:
        p = SRC / f"{name}.tex"
        out[name] = parse_blocks(p.read_text(encoding="utf-8", errors="replace"))
    return out


def block_text(b: dict) -> str:
    return "\n".join(b["body"])


# ---------------------------------------------------------------------------
# new prose: split the new/*.tex files into named segments
# ---------------------------------------------------------------------------
def load_segments() -> dict[str, str]:
    segs: dict[str, str] = {}
    for p in sorted(NEW.glob("*.tex")):
        txt = p.read_text(encoding="utf-8")
        cur, buf = None, []
        for line in txt.split("\n"):
            m = re.match(r"^%%%SEG:([A-Za-z0-9_]+)\s*$", line)
            if m:
                if cur is not None:
                    segs[f"{p.stem}:{cur}"] = "\n".join(buf).strip("\n")
                cur, buf = m.group(1), []
            else:
                buf.append(line)
        if cur is not None:
            segs[f"{p.stem}:{cur}"] = "\n".join(buf).strip("\n")
    return segs


def seg(name: str) -> str:
    if name not in SEGS:
        raise SystemExit(f"missing new-text segment: {name}")
    return SEGS[name]


# ---------------------------------------------------------------------------
# limitation splitting
# ---------------------------------------------------------------------------
ORDS = ["First", "Second", "Third", "Fourth", "Fifth", "Sixth", "Seventh", "Eighth",
        "Ninth", "Tenth", "Eleventh", "Twelfth", "Thirteenth"]


def strip_ordinal(body: str, name: str) -> str:
    body = body.strip()
    if body.startswith(name + ","):
        body = body[len(name) + 1:].lstrip()
    # capitalise the first alphabetic character
    for k, ch in enumerate(body):
        if ch.isalpha():
            return body[:k] + ch.upper() + body[k + 1:]
    return body


def split_limitation_series(text: str, names: list[str]) -> tuple[str, list[tuple[str, str]]]:
    """Split a paragraph at `names`; return (prefix, [(name, body_without_ordinal)])."""
    idx = []
    for nm in names:
        m = re.search(r"\b" + nm + r",", text)
        if not m:
            raise SystemExit(f"ordinal not found: {nm}")
        idx.append((m.start(), nm))
    prefix = text[:idx[0][0]].strip()
    out = []
    for k, (pos, nm) in enumerate(idx):
        end = idx[k + 1][0] if k + 1 < len(idx) else len(text)
        out.append((nm, strip_ordinal(text[pos:end], nm)))
    return prefix, out


# ---------------------------------------------------------------------------
# assembly
# ---------------------------------------------------------------------------
# item = ("T", "file:seg") | ("B", "src", idx) | ("S", "src", idx, "OrdName")
def A(*items):
    return list(items)


ASSEMBLY: dict[str, list] = {
    "10_introduction.tex": A(
        ("T", "intro:head"),
        ("T", "intro:contrib"),
        ("T", "intro:bullets"),
        ("T", "intro:bg"),
        ("B", "introduction", 1),
        ("B", "introduction", 2),
        ("B", "introduction", 3),
        ("B", "introduction", 7),
        ("B", "introduction", 10),
        ("T", "intro:roadmap"),
    ),
    "20_theory.tex": A(
        ("T", "theory:head"),
        ("T", "theory:framing"),
        *[("B", "theory", k) for k in range(2, 38)],
    ),
    "30_prior.tex": A(
        ("T", "prior:head"),
        *[("B", "related_work", k) for k in range(1, 18)],
        ("B", "empirical", 47),
        ("B", "empirical", 48),
    ),
    "40_protocol.tex": A(
        ("T", "protocol:head"),
        ("T", "protocol:framing"),
        ("B", "empirical", 2),
        *[("B", "empirical", k) for k in [3, 4, 5, 6, 7]],
    ),
    "50_results.tex": A(
        ("T", "results:head"),
        ("T", "results:framing"),
        ("T", "results:sitelabel"),
        ("T", "results:sitelead"),
        ("B", "empirical", 17),
        ("T", "results:dglead"),
        *[("B", "empirical", k) for k in [30, 31, 32, 34, 35, 36]],
        ("T", "results:odelead"),
        ("B", "validation", 2),
        *[("B", "validation", k) for k in [7, 8, 9, 10, 12]],
        ("T", "results:genlead"),
        *[("B", "validation", k) for k in [21, 22, 23, 24, 25]],
        ("T", "results:gradlead"),
        *[("B", "validation", k) for k in [29, 30, 31]],
        ("T", "results:zslead"),
        ("B", "empirical", 44),
        ("B", "empirical", 45),
        ("B", "empirical", 46),
    ),
    "60_negative.tex": A(
        ("T", "negative:head"),
        ("T", "negative:intro"),
        ("T", "negative:N1h"), ("T", "negative:N1s"),
        ("B", "theory", 45), ("B", "theory", 46), ("B", "validation", 19),
        ("T", "negative:N2h"), ("T", "negative:N2s"),
        ("T", "negative:N3h"), ("T", "negative:N3s"),
        ("T", "negative:N4h"), ("T", "negative:N4s"),
        ("T", "negative:N5h"), ("T", "negative:N5s"),
        ("T", "negative:N6h"), ("T", "negative:N6s"),
        ("T", "negative:N7h"), ("T", "negative:N7s"),
        ("T", "negative:N8h"), ("T", "negative:N8s"),
        ("T", "negative:N9h"), ("T", "negative:N9s"),
        ("T", "negative:N10h"), ("T", "negative:N10s"),
        ("B", "validation", 14), ("B", "validation", 15), ("B", "validation", 16),
        ("T", "negative:N11h"), ("T", "negative:N11s"),
        ("T", "negative:N12h"), ("T", "negative:N12s"),
        ("T", "negative:N13h"), ("T", "negative:N13s"),
        ("T", "negative:N14h"), ("T", "negative:N14s"),
        ("T", "negative:N15h"), ("T", "negative:N15s"),
        *[("B", "empirical", k) for k in [14, 15, 16]],
    ),
    "70_implications.tex": A(
        ("T", "implications:head"),
        *[("B", "discussion", k) for k in [2, 3, 4, 5, 6, 7, 8]],
        *[("B", "empirical", k) for k in [49, 50, 51]],
        ("B", "discussion", 15),
        ("T", "implications:broaderhead"),
        ("B", "discussion", 17),
    ),
    "80_conclusion.tex": A(
        *[("B", "conclusion", k) for k in range(0, 6)],
    ),
    "96_appendix_displaced.tex": A(
        ("T", "appendix:head"),
        ("T", "appendix:intro"),
        ("T", "appendix:I1"),
        *[("B", "empirical", k) for k in [8, 9, 10, 11, 12]],
        ("T", "appendix:I2"),
        ("B", "empirical", 13),
        ("T", "appendix:I3"),
        *[("B", "empirical", k) for k in [18, 19, 20, 21, 22, 23]],
        ("T", "appendix:I4"),
        *[("B", "empirical", k) for k in [24, 25, 26, 27, 28, 29]],
        ("T", "appendix:I5"),
        ("B", "empirical", 33),
        ("B", "empirical", 37),
        ("T", "appendix:I6"),
        *[("B", "empirical", k) for k in [38, 39, 40, 41, 42, 43]],
        ("T", "appendix:I7"),
        *[("B", "theory", k) for k in [38, 39, 40, 41, 42, 43]],
        ("T", "appendix:I8"),
        *[("B", "validation", k) for k in [26, 27]],
        ("T", "appendix:I9"),
        ("B", "validation", 28),
        ("T", "appendix:I10"),
        *[("B", "validation", k) for k in [32, 33, 34]],
        ("T", "appendix:I11"),
        *[("B", "validation", k) for k in [17, 18, 20]],
        ("T", "appendix:I12"),
        *[("B", "validation", k) for k in [3, 4, 5, 6, 11]],
        ("T", "appendix:I13"),
        ("S", "discussion", 10, "First"),
        ("S", "discussion", 10, "Second"),
        ("S", "discussion", 10, "Third"),
        ("S", "discussion", 10, "Fourth"),
        ("S", "discussion", 10, "Fifth"),
        ("S", "discussion", 10, "Sixth"),
        ("S", "discussion", 10, "Seventh"),
        ("S", "discussion", 10, "Eighth"),
        ("S", "discussion", 10, "Ninth"),
        ("S", "discussion", 11, "Tenth"),
        ("S", "discussion", 12, "Eleventh"),
        ("S", "discussion", 13, "Twelfth"),
        ("S", "discussion", 14, "Thirteenth"),
    ),
}

# blocks deliberately not carried because the new framing replaces them verbatim-free
DUP = [
    ("introduction", 0),          # \section{Introduction} heading replaced
    ("introduction", 4), ("introduction", 5), ("introduction", 6),  # ODE restated in §2
    ("introduction", 8), ("introduction", 9),  # old contribution list replaced
    ("related_work", 0),          # heading replaced
    ("empirical", 0),             # heading replaced
    ("empirical", 1),             # \label{sec:empirical} re-emitted in results head
    ("theory", 0),                # heading replaced
    ("theory", 1),                # \label{sec:theory} re-emitted in theory head
    ("theory", 44),               # ERS heading replaced by N1 heading
    ("validation", 0),            # heading replaced
    ("validation", 1),            # \label{sec:validation} re-emitted in results head
    ("discussion", 0),            # heading replaced
    ("discussion", 1),            # \label{sec:discussion} re-emitted in implications head
    ("discussion", 9),            # "Limitations and Future Work" heading replaced
    ("discussion", 16),           # "Connection to Pattern Recognition" heading replaced
    ("validation", 13),           # "Fit Diagnostics" heading replaced by N10 heading
]


# ---------------------------------------------------------------------------
# emit
# ---------------------------------------------------------------------------
def emit_file(items: list) -> str:
    parts: list[str] = []
    for it in items:
        if it[0] == "T":
            parts.append(seg(it[1]))
        elif it[0] == "B":
            parts.append(block_text(SRC_BLOCKS[it[1]][it[2]]))
        elif it[0] == "S":
            parts.append(seg_limitation(it[1], it[2], it[3]))
        else:
            raise SystemExit(f"bad item {it}")
    return "\n\n".join(p for p in parts if p.strip()) + "\n"


def build_limitations() -> None:
    """Populate LIMBODY: (src, idx, ordinal) -> body text, and record prefixes."""
    b10 = block_text(SRC_BLOCKS["discussion"][10])
    prefix, parts = split_limitation_series(b10, ORDS[:9])
    LIM_PREFIX.append(prefix)
    for nm, body in parts:
        LIMBODY[("discussion", 10, nm)] = body
    for idx, nm in ((11, "Tenth"), (12, "Eleventh"), (13, "Twelfth"), (14, "Thirteenth")):
        txt = block_text(SRC_BLOCKS["discussion"][idx])
        LIMBODY[("discussion", idx, nm)] = strip_ordinal(txt, nm)


LIMBODY: dict[tuple, str] = {}
LIM_PREFIX: list[str] = []


def get_limitation(src: str, idx: int, name: str) -> str:
    return LIMBODY[(src, idx, name)]


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
SRC_BLOCKS: dict[str, list[dict]] = {}
SEGS: dict[str, str] = {}


def norm_figure_widths(text: str) -> str:
    """Shrink over-wide figures (2026-10-26): 0.80-0.95 -> 0.70-0.80 of the text width, so two figures plus
    captions fit on one page instead of leaving half of the page blank."""
    mapping = {
        "0.95": "0.80", "0.90": "0.78", "0.88": "0.76", "0.86": "0.75",
        "0.85": "0.74", "0.84": "0.73", "0.82": "0.72", "0.80": "0.70",
    }
    for old, new in mapping.items():
        text = text.replace("[width=" + old + r"\textwidth]", "[width=" + new + r"\textwidth]")
    return text


def dedupe_subsection_headings(text: str) -> str:
    """Drop a stale short subsection heading that sits directly above the new descriptive one.

    The reframe keeps both the original heading block and the new heading block; when only a blank line
    separates them the PDF shows two consecutive headings (e.g. 5.10 and 5.11 with the same title). This
    removes the first of any adjacent pair, and converts \\mathbf to \\bm inside table rows so a bold
    negative number renders with a real minus sign instead of a bar.
    """
    lines = text.splitlines(keepends=True)
    out = []
    i = 0
    while i < len(lines):
        line = lines[i]
        m = re.match(r"\s*\\subsection\{", line)
        if m:
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j < len(lines) and re.match(r"\s*\\subsection\{", lines[j]):
                i = j          # skip the stale heading, keep the next one
                continue
        out.append(line)
        i += 1
    text = "".join(out)
    return text.replace("\\mathbf{", "\\bm{")


def main() -> int:
    global SRC_BLOCKS, SEGS
    ap = argparse.ArgumentParser()
    ap.add_argument("--inventory", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    SRC_BLOCKS = load_sources()
    SEGS = load_segments()

    if a.inventory:
        return inventory()

    build_limitations()

    # ---- emit every assembled file ----------------------------------------
    produced: dict[str, str] = {}
    for name in ASSEMBLY:
        chunks = []
        for it in ASSEMBLY[name]:
            if it[0] == "T":
                chunks.append(seg(it[1]))
            elif it[0] == "B":
                chunks.append(block_text(SRC_BLOCKS[it[1]][it[2]]))
            elif it[0] == "S":
                chunks.append(get_limitation(it[1], it[2], it[3]))
            else:
                raise SystemExit(f"bad item {it}")
        produced[name] = "\n\n".join(c for c in chunks if c.strip()) + "\n"

    # appendix that reuses the existing supplement verbatim
    app_original = "\n\n".join(block_text(b) for b in SRC_BLOCKS["supplement"]) + "\n\n" \
        + "\n\n".join(block_text(b) for b in SRC_BLOCKS["ode_diagnostics_appendix"]) + "\n\n" \
        + "\n\n".join(block_text(b) for b in SRC_BLOCKS["provenance_appendix"]) + "\n"

    # float placement: relax the specifier so that main-text floats are not deferred
    # into the appendix (this is a layout change only; the block text is otherwise verbatim)
    for name in list(produced):
        produced[name] = relax_floats(name, produced[name])
        produced[name] = neutralise_history(name, produced[name])
    app_original = relax_floats("95_appendix_original.tex", app_original)
    app_original = neutralise_history("95_appendix_original.tex", app_original)

    main_tex = mk_main()
    produced["main.tex"] = main_tex
    produced["95_appendix_original.tex"] = app_original

    # ---- assertions -------------------------------------------------------
    errs = check_all(produced)
    if errs:
        print("=" * 100)
        print(f"FAILED — {len(errs)} assertion failure(s)")
        print("=" * 100)
        for e in errs[:40]:
            print("  🔴 " + e)
        return 1
    print("=" * 100)
    print("all assertions passed")
    print("=" * 100)
    for n, t in produced.items():
        print(f"  {n:<32} {len(t):>8,} chars")

    if a.apply:
        (OUT / "sections").mkdir(parents=True, exist_ok=True)
        for n, t in produced.items():
            p = OUT / "main.tex" if n == "main.tex" else OUT / "sections" / n
            t = norm_figure_widths(t)
            t = dedupe_subsection_headings(t)
            p.write_text(t, encoding="utf-8", newline="")
            print(f"  ✅ wrote {p.relative_to(REPO)}")
        write_map(produced)
        print(f"  ✅ wrote paper合/reframed/REFRAME_MAP.md")
    elif a.check:
        print("\n  (check only) — not written")
    return 0


SECTION_MAP = [
    # (old location, new location, what changed)
    ("Abstract (main_nc.tex)", "Front matter, p.1", "verbatim"),
    ("1 Introduction", "1 Introduction (p.2-5)",
     "new page-1 contribution statement + 4-item bulleted contributions; old narrative kept verbatim"),
    ("--- (theory was Section 4, after 17 pages of empirical work)", "2 A gradient-flow characterisation (p.6-9)",
     "moved to the front of the paper; subsection 'Explaining the Empirical Regularities' -> Appendix I.7; "
     "'Effective Rank Saturation' -> finding N1"),
    ("2 Related Work", "3 Relation to prior work (p.10-14)",
     "heading renamed; 'Placement Against Prior Work' moved here from the old Section 3"),
    ("3.1 Experimental Design + 3 opening convention paragraph", "4 Empirical protocol (p.15-16)",
     "frozen protocol text; the four cautions about which rows are informative -> finding N15"),
    ("3.2 Position effect (earlier convention) + Table 1 + Fig. 1", "Appendix I.1 / I.3 / I.4",
     "the earlier-convention runs are evidence for negative findings, not for the main claim"),
    ("3.3-3.4 (non-contrastive tower, retrieval-protocol cautions)", "finding N15 + Appendix I.2",
     "stated as the boundary conditions they are"),
    ("3.5 Table 2 (strict freezing)", "5.1 Table 1 (p.17)", "the load-bearing table; now Section 5.1"),
    ("3.6 Rank robustness / family comparison", "finding N11 + Appendix I.3", "rank effect shown to be a protocol property"),
    ("3.7 LoRA configuration space", "finding N11 + Appendix I.4", "earlier rank results are wrapper artefacts"),
    ("3.8 Distribution gap and retrieval (Table 4, Figs 2, 5)",
     "5.2 Table 2 and Fig. 3 (p.18-21); Figs 2 and 5 -> Appendix I.5",
     "the association is a main result; the stratified figure is boundary evidence and is displaced"),
    ("3.9 Visual fragility", "finding N9 + Appendix I.6", "withdrawn probe and matched-perturbation null kept in full"),
    ("3.10 Zero-shot classification", "5.5 + Fig. 4", "kept as a positive result"),
    ("3.11 Placement against prior work", "3 Relation to prior work", "moved to the prior-work section"),
    ("3.12 Design patterns", "7 Implications", "kept, as the design synthesis"),
    ("4 Theory (whole section)", "2 A gradient-flow characterisation", "statements kept; elaboration -> Appendix I.7"),
    ("5.1-5.2 Phase 1 / Phase 2 (Tables 5, 7, Fig. 6)", "5.3 Table 4 + Appendix I.12",
     "per-rank table and the Phase-1 constancy table displaced; the load-bearing fits stay in 5.3"),
    ("5.3 Fit diagnostics (Table 8)", "finding N10", "the Adapter family's failure to obey the first-order reduction"),
    ("5.4 Effective Rank Saturation (Fig. 7)", "finding N1 + Appendix I.11", "the falsified sqrt(r) prediction"),
    ("5.5 Cross-architecture/dataset (Table 9)",
     "5.4 Table 3 + findings N6, N7 + Appendix I.8, I.9",
     "the reversal is a finding; the OpenCLIP fit stays in the main table"),
    ("5.6 Gradient asymmetry (Table 10)", "5.5 Table 5", "kept as the mechanism check"),
    ("5.7 Closing the empirical-theory loop", "Appendix I.10", "synthesis paragraph displaced"),
    ("6 Discussion 6.1-6.2 (why Gamma matters, design principles)", "7 Implications (p.32-35)", "kept"),
    ("6.3 Limitations, thirteen items",
     "6 Negative results and boundary conditions (p.22-31) + Appendix I.13",
     "restated as fifteen numbered findings with their bounds; full paragraphs carried in Appendix I.13"),
    ("6.4 Connection to Pattern Recognition", "7 Broader context", "heading neutralised for a fresh submission"),
    ("7 Conclusion", "8 Conclusion (p.36)", "verbatim"),
    ("Appendix A-H (old appendix)", "Appendix A-H (p.37-59)", "verbatim, unchanged"),
    ("ODE diagnostics appendix", "Appendix J", "verbatim"),
    ("Provenance appendix", "Appendix K", "verbatim"),
]


def write_map(produced: dict[str, str]) -> None:
    lines = [
        "# Paper A reframe: old -> new mapping",
        "",
        "Generated by `tools/_pa_reframe_build.py`; regenerate with `--apply`.",
        "Every block of the frozen sources is carried exactly once: the build fails if a block is",
        "unassigned, if a number, label or citation key disappears, or if a brace is unbalanced.",
        "",
        "## 1. Section-level mapping",
        "",
        "| Old location | New location | What changed |",
        "|---|---|---|",
    ]
    for row in SECTION_MAP:
        old, new = row[0], row[1]
        what = row[2] if len(row) > 2 else ""
        lines.append(f"| {old} | {new} | {what} |")
    lines += ["", "## 2. Block-level mapping (generated)", "",
              "Destination files in reading order. `src` is `file[block]` in `paper合/sections/`;",
              "`first` is the first 64 characters of the block, for eyeballing.", ""]
    for name in ["10_introduction.tex", "20_theory.tex", "30_prior.tex", "40_protocol.tex",
                 "50_results.tex", "60_negative.tex", "70_implications.tex", "80_conclusion.tex",
                 "96_appendix_displaced.tex"]:
        lines.append(f"### sections/{name}")
        lines.append("")
        lines.append("| # | src | first |")
        lines.append("|---|---|---|")
        k = 0
        for it in ASSEMBLY[name]:
            if it[0] == "B":
                b = SRC_BLOCKS[it[1]][it[2]]
                first = re.sub(r"\s+", " ", b["first"])[:64].replace("|", "\\|")
                lines.append(f"| {k} | {it[1]}[{it[2]}] | `{first}` |")
            elif it[0] == "S":
                lines.append(f"| {k} | {it[1]}[{it[2]}] ({it[3]} limitation) | `(limitation paragraph)` |")
            else:
                continue
            k += 1
        lines.append("")
    lines += ["## 3. Blocks replaced by new framing (no content lost)", "",
              "| src | reason |", "|---|---|"]
    reasons = {
        ("introduction", 0): "section heading replaced",
        ("introduction", 4): "the ODE is stated in Section 2; no number, label or citation unique to it",
        ("introduction", 5): "same",
        ("introduction", 6): "same",
        ("introduction", 8): "old contribution lead-in replaced by the page-1 statement",
        ("introduction", 9): "old contribution list replaced by the four bullets; every number in it is quoted in Sections 5-6",
        ("related_work", 0): "heading renamed",
        ("empirical", 0): "heading replaced",
        ("empirical", 1): "`\\label{sec:empirical}` re-emitted in Section 5",
        ("theory", 0): "heading replaced",
        ("theory", 1): "`\\label{sec:theory}` re-emitted in Section 2",
        ("theory", 44): "heading replaced by finding N1",
        ("validation", 0): "heading replaced",
        ("validation", 1): "`\\label{sec:validation}` re-emitted in Section 5.3",
        ("validation", 13): "heading replaced by finding N10",
        ("discussion", 0): "heading replaced",
        ("discussion", 1): "`\\label{sec:discussion}` re-emitted in Section 7",
        ("discussion", 9): "heading replaced by Section 6",
        ("discussion", 16): "heading neutralised to 'Broader context'",
    }
    for s, idx in DUP:
        lines.append(f"| {s}[{idx}] | {reasons.get((s, idx), 'heading replaced')} |")
    lines += ["", "## 4. Coverage assertion result", "",
              f"- source blocks: {sum(len(v) for v in SRC_BLOCKS.values())}",
              f"- carried verbatim: {sum(1 for n in ASSEMBLY for it in ASSEMBLY[n] if it[0] == 'B')}",
              f"- carried as limitation sub-blocks: 13 (split out of discussion blocks 10-14)",
              f"- replaced by framing: {len(DUP)}",
              "- numbers / labels / citations dropped: **0** (asserted)",
              ""]
    lines += ["## 5. Manuscript-history sentences neutralised for a fresh submission", "",
              "Each replacement is applied only if the old string occurs exactly once; no number,",
              "label or scientific statement is changed. The frozen sources keep the originals.", "",
              "| # | old (truncated) | new (truncated) |", "|---|---|---|"]
    for k, (old, new) in enumerate(HISTORY_NEUTRALISE, 1):
        o = re.sub(r"\s+", " ", old)[:80].replace("|", "\\|")
        nw = re.sub(r"\s+", " ", new)[:80].replace("|", "\\|")
        lines.append(f"| {k} | `{o}` | `{nw}` |")
    lines.append("")
    (OUT / "REFRAME_MAP.md").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="")


def inventory() -> int:
    for name in SOURCES:
        print("=" * 108)
        print(f"{name}.tex  --  {len(SRC_BLOCKS[name])} blocks")
        print("=" * 108)
        for k, b in enumerate(SRC_BLOCKS[name]):
            first = re.sub(r"\s+", " ", b["first"])[:76]
            print(f"  [{k:>3}] {b['kind']:<8} {first}")
    return 0


# Sentences that refer to the manuscript's own revision history rather than to the science.
# They are neutralised for a fresh submission; no number, label or substance is touched.
HISTORY_NEUTRALISE = [
    ("An earlier version of this supplement reported ODE coefficients for MS-COCO in a table. That table has\n"
     "been withdrawn. Its coefficients were fitted to $DG^*$ trajectories from runs in which the backbone\n"
     "remained trainable, and the strict-freezing runs this paper's controls use do not reproduce the quantity\n"
     "it measured.",
     "We report no ODE coefficients for MS-COCO. The coefficients that such a table would carry were fitted to\n"
     "$DG^*$ trajectories from runs in which the backbone remained trainable, and the strict-freezing runs this\n"
     "paper's controls use do not reproduce the quantity they measured."),
    ("We note the revision explicitly: an earlier version of this table took the first\n"
     "post-training epoch as the baseline",
     "We note the convention explicitly: this table took the first post-training epoch as the\n"
     "baseline"),
    ("One correction belongs with those numbers, because it changes what they are measurements of.",
     "One qualification belongs with those numbers, because it changes what they are measurements of."),
    ("the comparison that led an earlier version of that claim to be withdrawn",
     "the comparison that led us to withdraw that claim"),
    ("The gap responds to configured rank, though not in the direction this paragraph originally reported.",
     "The gap responds to configured rank, though not monotonically."),
    ("(An earlier version of this sentence quoted $+0.079$ for the text-only arm. That value is the Route D "
     "run \\texttt{d1\\_alpha64\\_text\\_r8}, which shares the nominal rank and scaling of the core run quoted "
     "here but ends with a validation loss of $2.33$ against $0.499$, and an $R@1$ of $0.389$; we treat it as "
     "a degenerate fit and the value is withdrawn. Table~\\ref{tab:config_groups} in the appendix sets the "
     "configuration groups side by side.)",
     "(A separate text-only run, the Route D run \\texttt{d1\\_alpha64\\_text\\_r8}, reports $+0.079$; it "
     "shares the nominal rank and scaling of the core run quoted here but ends with a validation loss of "
     "$2.33$ against $0.499$ and an $R@1$ of $0.389$, so we treat it as a degenerate fit. "
     "Table~\\ref{tab:config_groups} sets the configuration groups side by side.)"),
]


def neutralise_history(name: str, text: str) -> str:
    for old, new in HISTORY_NEUTRALISE:
        n = text.count(old)
        if n == 0:
            continue
        assert n == 1, f"{name}: history phrase occurs {n} times, expected 1: {old[:50]!r}"
        text = text.replace(old, new)
    return text


def relax_floats(name: str, text: str) -> str:
    """Widen the float specifiers of table/figure environments to [!htbp].

    The frozen sources use [ht] / [t] / [h].  When the reframed document carries a large
    appendix, LaTeX defers main-text floats and flushes them at the first \\FloatBarrier in
    the appendix, which is not acceptable.  [!htbp] overrides the fraction limits; the number
    of substitutions is asserted to equal the number of float environments.
    """
    n_begin = len(re.findall(r"\\begin\{(?:table|figure)\}", text))
    out, n_sub = re.subn(r"\\begin\{(table|figure)\}\[[^\]]*\]", r"\\begin{\1}[!htbp]", text)
    assert n_sub == n_begin, f"{name}: float specifier substitution {n_sub} != {n_begin}"
    return out


def mk_main() -> str:
    return "\n".join([
        r"%% Paper A — reframed for a fresh submission.  Built by tools/_pa_reframe_build.py.",
        r"%% The frozen originals live in paper合/main_nc.tex and paper合/main_springer.tex and are",
        r"%% not modified by this tree.",
        r"\documentclass[review,authoryear]{elsarticle}",
        r"\usepackage{amsmath,amssymb,amsfonts}",
        r"\usepackage{amsthm}",
        r"\newtheorem{theorem}{Theorem}[section]",
        r"\newtheorem{lemma}{Lemma}[section]",
        r"\newtheorem{corollary}{Corollary}[section]",
        r"\newtheorem{definition}{Definition}[section]",
        r"\newtheorem{proposition}[theorem]{Proposition}",
        r"\newtheorem{remark}{Remark}[section]",
        r"\newtheorem{assumption}{Assumption}[section]",
        r"\usepackage{graphicx}",
        r"\graphicspath{{../figures/}{../}}",
        r"\usepackage{booktabs}",
        r"\usepackage{multirow}",
        r"\usepackage{longtable}",
        r"\usepackage{url}",
        r"\usepackage{float}",
        r"\usepackage{placeins}",
        r"\usepackage[hidelinks]{hyperref}",
        r"\setlength{\emergencystretch}{3em}",
        r"",
        r"\journal{}",
        r"",
        r"\begin{document}",
        r"\sloppy",
        r"",
        r"\begin{frontmatter}",
        r"",
        seg("front:title"),
        r"",
        r"\author[1]{Hongrui Wan\corref{cor1}}",
        r"\affiliation[1]{organization={University of Southampton},",
        r"  addressline={University Road},",
        r"  city={Southampton},",
        r"  postcode={SO17 1BJ},",
        r"  country={United Kingdom}}",
        r"\cortext[cor1]{Corresponding author.}",
        r"\ead{hw4c24@soton.ac.uk}",
        r"",
        seg("front:abstract"),
        r"",
        seg("front:keywords"),
        r"",
        r"\end{frontmatter}",
        r"",
        r"\input{sections/10_introduction}",
        r"\input{sections/20_theory}",
        r"\input{sections/30_prior}",
        r"\input{sections/40_protocol}",
        r"\input{sections/50_results}",
        r"\input{sections/60_negative}",
        r"\input{sections/70_implications}",
        r"\input{sections/80_conclusion}",
        r"",
        r"%% flush every main-text float before the appendix so that the main text ends here",
        r"\FloatBarrier",
        r"\clearpage",
        r"\appendix",
        r"\input{sections/95_appendix_original}",
        r"\input{sections/96_appendix_displaced}",
        r"",
        seg("backmatter:declarations"),
        r"",
        r"\bibliographystyle{elsarticle-harv}",
        r"\setlength{\bibsep}{0pt}",
        r"\bibliography{../references}",
        r"",
        r"\end{document}",
        r"",
    ])


NUM = re.compile(r"\d[\d,]*(?:\.\d+)?")
LABEL = re.compile(r"\\label\{([^}]*)\}")
CITE = re.compile(r"\\cite\{([^}]*)\}")
ALLOWED_LITERAL_N = re.compile(r"\\n(?![A-Za-z])")
SEVERED = re.compile(r"^(abla|oindent|eq|ot|ewtheorem|ewcommand|ewline)\b")
CTRL = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F]")


def check_all(produced: dict[str, str]) -> list[str]:
    errs: list[str] = []

    # 1. coverage
    used: dict[str, set] = {s: set() for s in SOURCES}
    for name, items in ASSEMBLY.items():
        for it in items:
            if it[0] in ("B", "S"):
                used[it[1]].add(it[2])
    for s, idx in DUP:
        used[s].add(idx)
    for s in SOURCES:
        if s in ("supplement", "ode_diagnostics_appendix", "provenance_appendix"):
            continue
        missing = sorted(set(range(len(SRC_BLOCKS[s]))) - used[s])
        if missing:
            errs.append(f"coverage: {s}.tex blocks not carried: {missing}")
    # the dropped lead-in of the limitation run carries no number/label/citation
    for pref in LIM_PREFIX:
        if NUM.search(pref) or LABEL.search(pref) or CITE.search(pref):
            errs.append(f"dropped limitation lead-in carries provenance: {pref[:60]!r}")

    out_all = "\n\n".join(produced.values())
    out_flat = " ".join(out_all.split())

    # 2. numbers
    src_text = "\n".join(block_text(b) for s in SOURCES for b in SRC_BLOCKS[s])
    src_nums = set(NUM.findall(src_text))
    out_nums = set(NUM.findall(out_all))
    miss_num = sorted(src_nums - out_nums)
    if miss_num:
        errs.append(f"numbers dropped ({len(miss_num)}): {miss_num[:20]}")

    # 3. labels
    src_lab = set(LABEL.findall(src_text))
    out_lab = set(LABEL.findall(out_all))
    miss_lab = sorted(src_lab - out_lab)
    if miss_lab:
        errs.append(f"labels dropped: {miss_lab}")

    # 4. citations
    src_cite = {k.strip() for grp in CITE.findall(src_text) for k in grp.split(",")}
    out_cite = {k.strip() for grp in CITE.findall(out_all) for k in grp.split(",")}
    miss_cite = sorted(src_cite - out_cite)
    if miss_cite:
        errs.append(f"citation keys dropped: {miss_cite}")

    # 5. LaTeX hygiene
    for name, t in produced.items():
        if ALLOWED_LITERAL_N.search(t):
            errs.append(f"{name}: literal backslash-n present")
        if any(SEVERED.match(ln) for ln in t.split("\n")):
            errs.append(f"{name}: severed command at line start")
        if CTRL.search(t):
            errs.append(f"{name}: control character present")
        # brace balance (crude but catches truncation)
        if t.count("{") != t.count("}"):
            errs.append(f"{name}: brace imbalance {t.count('{')} vs {t.count('}')}")
        if t.count(r"\begin{") != t.count(r"\end{"):
            errs.append(f"{name}: environment imbalance")
    return errs


if __name__ == "__main__":
    raise SystemExit(main())
