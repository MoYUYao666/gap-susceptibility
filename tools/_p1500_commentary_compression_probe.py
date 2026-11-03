# -*- coding: utf-8 -*-
r"""Probe the PRL Commentary length budget and validate a compression proposal.

This script is read-only: it never writes MANUSCRIPT.md, main_prl.tex or any PDF.
It produces the three facts the compression proposal has to rest on.

1. Section word counts, from paper_review_prl/MANUSCRIPT.md, split into
   *prose* words (paragraphs and list items) and *table* words (pipe-table
   rows), counted per "##" section and per "###" subsection together with the
   1-based markdown line range of each block.
2. PDF layout facts, from paper_review_prl/main_prl.pdf: the page count, the
   word count per page, and per-page vertical text extents obtained from the
   text matrices (pypdf visitor_text), which show how much of the last page is
   still free and how tall the full-width Figure 1 block is on its page.
3. Validation of the cut list in CUTS below: each quoted "old" string must
   occur exactly once in MANUSCRIPT.md (so line numbers and quotes are exact),
   and each replacement must preserve every [citation key], every number and
   every internal cross-reference (section sign + number) that the old text
   carried.  Word deltas are summed to the proposal's total.

Usage:  python tools/_p1500_commentary_compression_probe.py
"""
from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MD = REPO / "paper_review_prl" / "MANUSCRIPT.md"
PDF = REPO / "paper_review_prl" / "main_prl.pdf"

WORD_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9'’\-\.%]*")
BRACKET_RE = re.compile(r"\[([^\[\]]+)\]")
KEY_RE = re.compile(r"[a-z][a-z0-9_]*[0-9][a-z0-9_]*$")
NUM_RE = re.compile(r"[0-9]+(?:\.[0-9]+)?%?")
XREF_RE = re.compile(r"§[0-9]+(?:\.[0-9]+)?")


def cite_keys(s: str) -> set:
    """Citation keys carried by any [key] or [key1; key2] bracket in a span of text."""
    keys = set()
    for m in BRACKET_RE.finditer(s):
        parts = [p.strip() for p in re.split(r"[;,]", m.group(1))]
        if parts and all(KEY_RE.match(p) for p in parts):
            keys.update(parts)
    return keys

# ---------------------------------------------------------------------------
# the cut list: every "old" string is quoted verbatim from MANUSCRIPT.md and is
# proved unique by the validator below; "lines" are 1-based inclusive markdown
# line numbers.  exempt_numbers lists numerals that the replacement drops on
# purpose (checklist-item pointers, not reported quantities); each one is
# justified in docs/commentary_compression_and_table.md.
# ---------------------------------------------------------------------------
CUTS: list = [
    dict(
        id="C1", section="2.1", lines="97-98", risk="low",
        old="The sites available for adaptation are not interchangeable; the choice is constrained by "
            "architecture and task data.",
        new="",
        why="Topic sentence deleted. Both halves survive: 'not two answers to the same question' (S1, "
            "lines 52-53), 'They are not [alternatives]' (2.1, lines 123-124), and 'The first follows "
            "architecture and data volume' (2.3, lines 164-166). No citation, number or claim is lost.",
    ),
    dict(
        id="C2", section="2.1", lines="110-111", risk="low",
        old="The two settings answer different questions and their results do not transfer: a method that "
            "improves ImageNet transfer has not thereby been shown to improve instruction following.",
        new="Their results do not transfer: a method that improves ImageNet transfer has not thereby been "
            "shown to improve instruction following.",
        why="'answer different questions' repeats S1, lines 52-53 verbatim in substance. The ImageNet "
            "claim itself is kept in full.",
    ),
    dict(
        id="C3", section="2.2", lines="148-149", risk="low",
        old="This strategy is attractive because it is the only one that can in principle transfer across "
            "base models; the evidence that it does so remains thin, and we return to this in §3.6.",
        new="This strategy is attractive because it is the only one that can in principle transfer across "
            "base models, though the evidence that it does so remains thin.",
        why="Deletes a forward pointer that does not resolve: 3.6 is 'The freeze is an assumption, not a "
            "neutral baseline' and no section returns to transfer across base models. The substantive "
            "claim ('only one that can in principle transfer', 'evidence remains thin') is kept.",
        exempt_numbers=["3.6"], exempt_xrefs=["§3.6"],
        exempt_why="The numeral and the section sign occur only inside the broken pointer being removed; "
                   "the destination section itself is untouched.",
    ),
    dict(
        id="C4", section="3 (opening)", lines="185-186", risk="low",
        old="Each is stated so that a reader can check it against the cited sources; where our reading "
            "rests on an inference rather than on data, we say so.",
        new="Where our reading rests on an inference rather than on data, we say so.",
        why="The checkability of the instances is already stated in S1, lines 71-72 "
            "('chosen because each is checkable against its source'). The disclosure commitment is kept.",
    ),
    dict(
        id="C5", section="3.1", lines="195-200", risk="low",
        old="The two papers may be reporting the same quantity, or different quantities; the published "
            "text does not determine which. We deliberately do not claim that the values disagree, because "
            "that claim would require knowing the evaluation protocol of the second paper, which is "
            "precisely what is missing. The instance is useful for what it demonstrates: comparing these "
            "numbers across papers is not a legitimate operation, and the reason is a reporting omission "
            "rather than an error.",
        new="The two papers may be reporting the same quantity or different quantities; the published text "
            "does not determine which. We do not claim that the values disagree: that would require the "
            "second paper's evaluation protocol, which is precisely what is missing. Comparing these "
            "numbers across papers is therefore not a legitimate operation, for a reason of omission "
            "rather than error.",
        why="Three sentences merged, no claim dropped: (i) same or different quantity, (ii) the published "
            "text does not determine which, (iii) we do not claim disagreement, (iv) because the second "
            "paper's protocol is what is missing, (v) comparing across papers is not legitimate, (vi) the "
            "cause is omission rather than error.",
    ),
    dict(
        id="C6", section="3.5", lines="240-242", risk="low",
        old="The remedy is trivial — state the number of runs and the convention — and its absence is a "
            "common reason why otherwise careful results cannot be re-used. A comparison whose dispersion "
            "convention is unstated cannot be combined with another.",
        new="The remedy is trivial — state the number of runs and the convention — and without it an "
            "otherwise careful comparison cannot be combined with another.",
        why="The second sentence restates the first in the negative. Kept: the remedy (runs + convention) "
            "and the consequence (cannot be combined / re-used).",
    ),
    dict(
        id="C7", section="3.6", lines="250-252", risk="low",
        old="This instance is a direct consequence of the siting decision of §2.1: without a stated site, "
            "the description of what was adapted is incomplete.",
        new="This instance follows from the siting decision of §2.1: without a stated site, the "
            "description is incomplete.",
        why="Compression only: the §2.1 cross-reference and both claims (it follows from the siting "
            "decision; an unstated site leaves the description incomplete) are kept.",
    ),
    dict(
        id="C8", section="4", lines="334-335", risk="medium",
        old="**How the items map onto the failures of §3.** The correspondence is one to one, which is the "
            "justification for each item's inclusion rather than an appeal to good practice in general.",
        new="",
        why="The bold lead-in repeats the following table caption word for word ('How the checklist items "
            "map onto the failures of §3'). The justification is already in the first remark, lines "
            "329-330 ('every item corresponds to a specific inability that its absence creates, as "
            "documented in §3'). Note for the author: the deleted sentence also asserts 'the "
            "correspondence is one to one', which the table below it does not literally satisfy (items "
            "2,3 and 5,6 and 9,10 share an instance), so the deletion removes an inexact claim.",
        exempt_xrefs=["§3"], exempt_numbers=["3"],
        exempt_why="The '§3' pointer survives verbatim in the table caption that follows (MANUSCRIPT.md "
                   "line 337) and in the first remark (lines 329-330).",
    ),
    dict(
        id="C9", section="4", lines="350", risk="low",
        old="The list cannot be shortened much further: items 5 and 6 look like one until one notices that "
            "a paper can state its rank while leaving the division unstated, and items 9 and 10 separate a "
            "design fact from a reporting convention.",
        new="The list cannot be shortened much further: a paper can state its rank while leaving the "
            "division unstated (items 5 and 6), and items 9 and 10 separate a design fact from a "
            "reporting convention.",
        why="Compression only; every item number and both claims (5/6 are separable; 9/10 separate a "
            "design fact from a convention) are kept.",
    ),
    dict(
        id="C10", section="4", lines="354", risk="medium",
        old="**From aspiration to acceptance test.** Each item can be checked by a reader in a minute: "
            "item 1 requires the exact checkpoint (not just the model family); item 4 an absolute "
            "parameter count as well as a fraction; item 5 the rank array or the word ``uniform''; item 9 "
            "the number of runs and the dispersion convention. A paper that passes these tests enters a "
            "comparison table without correspondence with its authors, which is the operational meaning of "
            "the reporting standard.",
        new="**From aspiration to acceptance test.** Each item can be checked by a reader in a minute; a "
            "paper that passes them enters a comparison table without correspondence with its authors, "
            "which is the operational meaning of the reporting standard.",
        why="The middle enumeration re-states items 1, 4, 5 and 9 (checkpoint; absolute count and "
            "fraction; rank array or 'uniform'; runs and dispersion convention), which remain intact in "
            "the twelve-item list, and 'without access to code' is already in the section opening (lines "
            "295-296). The 'acceptance test' claim (a paper that passes enters a comparison table without "
            "correspondence) is kept in full.",
        exempt_numbers=["1", "4", "5", "9"],
    ),
    dict(
        id="C11", section="5", lines="366-367", risk="low",
        old="The instances are not allegations of error: in each case the information needed for "
            "comparison is absent rather than wrong, and the checklist in §4 is the minimum that removes "
            "these obstacles.",
        new="The instances are not allegations of error: the information needed for comparison is absent "
            "rather than wrong.",
        why="Keeps the non-accusatory claim and the 'absent rather than wrong' formulation; the deleted "
            "tail restates the S4 opening, lines 294-296 ('the remedy is a reporting standard. The twelve "
            "items below are the minimum needed to compare two multimodal adaptation results').",
        exempt_xrefs=["§4"], exempt_numbers=["4"],
        exempt_why="The '§4' pointer survives in S1, line 67 ('a twelve-item reporting checklist intended "
                   "to make future results comparable, and therefore citable (§4)').",
    ),
    dict(
        id="C12", section="5", lines="362-364", risk="low",
        old="The two are governed by different variables — architecture and data volume for the first, the "
            "target metric for the second — and they are routinely conflated, which is why many published "
            "numbers cannot share a table.",
        new="The two are governed by different variables — architecture and data volume for the first, the "
            "target metric for the second — and they are routinely conflated.",
        why="The consequence clause repeats the S3 opening ('a substantial part of its numerical content "
            "cannot be compared', lines 182-184) and the abstract ('why much of the published evidence "
            "cannot be compared'). The conflations claim and the two governing variables are kept.",
    ),
    dict(
        id="C13", section="1", lines="71-72", risk="medium",
        old="And it is argumentative rather than systematic: the instances in §3 are individual cases "
            "chosen because each is checkable against its source, not a sample from which frequencies can "
            "be estimated.",
        new="It is argumentative rather than systematic: the instances in §3 are cases checkable against "
            "their sources, not a sample (§3.7).",
        why="Keeps the scope limitation ('argumentative rather than systematic', 'not a sample') and the "
            "checkability that the deleted S3 opening relied on, and points to 3.7, which states the same "
            "limit at greater length ('checkable illustrations rather than a systematic sample'). The "
            "weaker implicit element 'frequencies cannot be estimated' is carried by 'not a sample'; keep "
            "the longer form if the author prefers it explicit.",
    ),
]


def words(s: str) -> int:
    return len(WORD_RE.findall(s))


def norm(s: str) -> str:
    """Whitespace-normalised text, which is how the markdown wraps paragraphs."""
    return re.sub(r"\s+", " ", s).strip()


# ---------------------------------------------------------------------------
# 1. section word counts
# ---------------------------------------------------------------------------

def section_counts(text: str):
    lines = text.splitlines()
    heads = [(i, ln.strip()) for i, ln in enumerate(lines) if ln.strip().startswith(("## ", "### "))]
    blocks = []
    for n, (i, head) in enumerate(heads):
        end = heads[n + 1][0] if n + 1 < len(heads) else len(lines)
        level = 3 if head.startswith("### ") else 2
        title = head[4:].strip() if level == 3 else head[3:].strip()
        prose, table = [], []
        for ln in lines[i + 1:end]:
            s = ln.strip()
            if not s or s == "---" or s.startswith(("#", ">")):
                continue
            (table if s.startswith("|") else prose).append(s)
        blocks.append({
            "level": level, "title": title, "line_from": i + 1, "line_to": end,
            "prose_words": words(" ".join(prose)), "table_words": words(" ".join(table)),
        })
    return blocks


def print_section_counts(blocks, heading: str) -> None:
    print(heading)
    print("  %-46s %5s %6s %6s" % ("heading", "lines", "prose", "table"))
    total_prose = total_table = 0
    for b in blocks:
        total_prose += b["prose_words"]
        total_table += b["table_words"]
        print("  %-46s %5s %6d %6d" % (
            ("  " * (b["level"] - 2)) + b["title"][:44],
            "%d-%d" % (b["line_from"], b["line_to"]),
            b["prose_words"], b["table_words"]))
    print("  %-46s %5s %6d %6d" % ("TOTAL (all headings)", "", total_prose, total_table))
    print()


# ---------------------------------------------------------------------------
# 2. PDF layout facts
# ---------------------------------------------------------------------------

def pdftotext_page_words() -> dict:
    """Per-page word counts via pdftotext (pypdf loses spaces at tight kerning)."""
    import subprocess
    out = {}
    try:
        for pno in range(1, 40):
            r = subprocess.run(["pdftotext", "-f", str(pno), "-l", str(pno), str(PDF), "-"],
                               capture_output=True)
            if r.returncode != 0:
                break
            txt = r.stdout.decode("utf-8", "ignore")
            if not txt.strip() and pno > 7:
                break
            out[pno] = len(WORD_RE.findall(txt))
    except Exception:
        pass
    return out


def pdf_pages():
    from pypdf import PdfReader
    reader = PdfReader(str(PDF))
    words_by_page = pdftotext_page_words()
    out = []
    for pno, page in enumerate(reader.pages, start=1):
        ys = []

        def visitor(text, cm, tm, font_dict, font_size, ys=ys):
            if text.strip():
                ys.append((round(float(tm[5]), 1), round(float(tm[4]), 1), text.strip()))

        txt = page.extract_text(visitor_text=visitor)
        out.append({
            "page": pno,
            "width": float(page.mediabox.width),
            "height": float(page.mediabox.height),
            "words": words_by_page.get(pno, -1),
            "ys": ys,
        })
    return out


HEAD_Y = 740.0    # running head sits above this baseline
FOOT_Y = 40.0     # page footer (and a stray figure-text copy) sits below this
COL_SPLIT = 300.0  # cas-dc column gutter for a 595pt-wide page


def column_extents(page) -> dict:
    """Top/bottom baselines of the two text columns, head and footer excluded."""
    body = [(y, x) for y, x, _ in page["ys"] if FOOT_Y < y < HEAD_Y]
    left = [y for y, x in body if x < COL_SPLIT]
    right = [y for y, x in body if x >= COL_SPLIT]
    return {
        "left_top": max(left) if left else None, "left_bot": min(left) if left else None,
        "right_top": max(right) if right else None, "right_bot": min(right) if right else None,
        "left_lines": len(set(round(y) for y in left)), "right_lines": len(set(round(y) for y in right)),
    }


def print_slack(pages) -> None:
    full_pages = [p for p in pages if p["page"] in (4, 5, 6)]
    col_top = max(column_extents(p)["left_top"] for p in full_pages)
    col_bot = min(column_extents(p)["left_bot"] for p in full_pages)
    col_h = col_top - col_bot
    print("  column geometry (from pages 4-6, both columns full):")
    print("    top baseline %.1f pt, bottom baseline %.1f pt, column height %.1f pt" % (col_top, col_bot, col_h))
    print()
    print("  %5s %7s %10s %10s %10s %10s %9s" % ("page", "words", "L top", "L bot", "R top", "R bot", "free col-pt"))
    free_pt = {}
    for p in pages:
        e = column_extents(p)
        if e["left_top"] is None:
            print("  %5d %7d %10s %10s %10s %10s %9s" % (p["page"], p["words"], "-", "-", "-", "-", "-"))
            continue
        free = 0.0
        if e["left_bot"] is not None:
            free += max(0.0, e["left_bot"] - col_bot)
        if e["right_bot"] is not None:
            free += max(0.0, e["right_bot"] - col_bot)
        free_pt[p["page"]] = free
        print("  %5d %7d %10.1f %10.1f %10s %10s %9.1f" % (
            p["page"], p["words"], e["left_top"], e["left_bot"],
            "%.1f" % e["right_top"] if e["right_top"] else "-",
            "%.1f" % e["right_bot"] if e["right_bot"] else "-", free))
    # body density: words per column-point on the three full body pages
    dens = []
    for p in full_pages:
        used = col_h * 2 - free_pt.get(p["page"], 0.0)
        if used > 0 and p["words"] > 0:
            dens.append(p["words"] / used)
    if dens:
        d = sum(dens) / len(dens)
        print()
        print("  body density from pages %s: %.4f words per column-pt  (%.0f words per full column, %.0f per page)"
              % (", ".join(str(p["page"]) for p in full_pages), d, d * col_h, d * col_h * 2))
    p7 = next(p for p in pages if p["page"] == len(pages))
    print("  last page (%d) free column-pt: %.1f  -> absorbable body text before an 8th page: %s words"
          % (p7["page"], free_pt.get(p7["page"], 0.0),
             "%.0f" % (d * free_pt.get(p7["page"], 0.0)) if dens else "n/a"))
    print()


def line_clusters(ys, tol=3.0):
    """Group baseline y values into lines, top of page first (PDF y grows upward)."""
    rows = sorted(ys, key=lambda r: -r[0])
    clusters = []
    for y, x, t in rows:
        if clusters and abs(clusters[-1][0] - y) <= tol:
            clusters[-1][1].append((y, x, t))
            clusters[-1][0] = max(clusters[-1][0], y)
        else:
            clusters.append([y, [(y, x, t)]])
    return clusters


def print_pdf_layout(pages, detail_pages) -> None:
    print("PDF layout probe: %s" % PDF.relative_to(REPO))
    print("  pages: %d   page size: %.1f x %.1f pt" % (len(pages), pages[0]["width"], pages[0]["height"]))
    print()
    print("  %5s %7s %9s %9s %9s" % ("page", "words", "top y", "bot y", "text h"))
    for p in pages:
        top = max(y for y, _, _ in p["ys"])
        bot = min(y for y, _, _ in p["ys"])
        print("  %5d %7d %9.1f %9.1f %9.1f" % (p["page"], p["words"], top, bot, top - bot))
    print()
    print_slack(pages)
    for pno in detail_pages:
        p = next(q for q in pages if q["page"] == pno)
        cl = line_clusters(p["ys"])
        print("  --- page %d: %d text lines (baseline clusters), by descending y ---" % (pno, len(cl)))
        for y, items in cl:
            text = " ".join(t for _, _, t in sorted(items, key=lambda r: r[1]))
            print("    y=%7.1f  x_min=%6.1f  %s" % (y, min(x for _, x, _ in items), text[:110]))
        print()


# ---------------------------------------------------------------------------
# 3. cut-list validation
# ---------------------------------------------------------------------------

def _flat_index(text: str):
    """Normalised whole document plus a map from character offset to 1-based line."""
    starts, flat_parts, pos = [], [], 0
    for i, line in enumerate(text.splitlines(), start=1):
        s = norm(line)
        if not s:
            continue
        starts.append((pos, i))
        flat_parts.append(s)
        pos += len(s) + 1
    return " ".join(flat_parts), starts


def _lines_of(starts, offset: int) -> int:
    lo, hi = 0, len(starts) - 1
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if starts[mid][0] <= offset:
            lo = mid
        else:
            hi = mid - 1
    return starts[lo][1]


def validate_cuts(text: str) -> int:
    flat, starts = _flat_index(text)
    print("Cut-list validation (%d proposed edits)" % len(CUTS))
    print("  %-4s %-11s %-11s %6s %-8s %s" % ("id", "section", "lines(MD)", "saved", "risk", "checks"))
    total = 0
    ok = True
    for c in CUTS:
        old_flat = norm(c["old"])
        occurrences = flat.count(old_flat)
        checks = []
        if occurrences != 1:
            checks.append("OLD_NOT_UNIQUE(%d)" % occurrences)
            ok = False
            measured = "-"
        else:
            at = flat.find(old_flat)
            first = _lines_of(starts, at)
            last = _lines_of(starts, at + len(old_flat) - 1)
            measured = "%d-%d" % (first, last) if first != last else str(first)
            if measured != c["lines"]:
                checks.append("LINE_MISMATCH(measured %s)" % measured)
                ok = False
        exempt = set(c.get("exempt_numbers", []))
        exempt_x = set(c.get("exempt_xrefs", []))
        for name, rx in (("num", NUM_RE), ("xref", XREF_RE)):
            lost = set(rx.findall(c["old"])) - set(rx.findall(c["new"]))
            if name == "num":
                lost -= exempt
            if name == "xref":
                lost -= exempt_x
            if lost:
                checks.append("%s_LOST:%s" % (name, ",".join(sorted(lost))))
                ok = False
        lost_cites = cite_keys(c["old"]) - cite_keys(c["new"])
        if lost_cites:
            checks.append("cite_LOST:%s" % ",".join(sorted(lost_cites)))
            ok = False
        saved = words(c["old"]) - words(c["new"])
        total += saved
        if saved <= 0:
            checks.append("NO_SAVING")
            ok = False
        print("  %-4s %-11s %-11s %6d %-8s %s" % (
            c["id"], "S" + c["section"], c["lines"], saved, c["risk"],
            "ok" if not checks else "; ".join(checks)))
    print()
    print("  total words saved: %d  (target band 120-200)" % total)
    core = [c for c in CUTS if c["id"] in ("C1", "C2", "C3", "C4", "C5", "C6", "C7", "C9", "C11", "C12", "C13")]
    print("  core subset (%s): %d words" % (", ".join(c["id"] for c in core),
                                            sum(words(c["old"]) - words(c["new"]) for c in core)))
    print("  status: %s" % ("all edits verified against MANUSCRIPT.md" if ok else "PROBLEMS FOUND"))
    return 0 if ok else 1


# ---------------------------------------------------------------------------
# 4. draft table, rendered by the manuscript's own builder
# ---------------------------------------------------------------------------

TABLE_MD = [
    "| Family | Where capacity goes | How the budget is divided | Cited as |",
    "|---|---|---|---|",
    "| LoRA / DoRA | Language backbone; vision encoder frozen | Uniform rank across the targeted projections | [hu2021lora; liu2024dora] |",
    "| AdaLoRA / ARD-LoRA | Language backbone, the low-rank family's usual site | Estimated importance: rank raised where updates are large | [zhang2023adalora; shinwari2026ardlora] |",
    "| VPT / SSF | Visual encoder: prompt vectors; feature scaling and shifting | Uniform: the same configuration in every module | [jia2022vpt; lian2022ssf] |",
    "| Encoder-side bottlenecks | Encoder feed-forward path; feature side of either branch | Not determinable from the cited sources: no allocation rule | [chen2022adaptformer; jie2022convpass; gao2024clipadapter] |",
    "| Projector redesign | Projector | Not a parameter division: the knob is the visual-token count | [cha2024honeybee; li2025tokenpacker] |",
    "| Search-based | Selected by the search, so it spans sites | Search over the configuration | [zhou2024autopeft; liu2022ia3] |",
]

TABLE_CAPTION = ("Adaptation families on the two decisions. Placements follow the sources cited in the last "
                 "column and the statements of §2.1 and §2.2; where a family defines no rule for dividing "
                 "a parameter budget, the third column says so rather than assigning a strategy.")


def print_table_fragment(text: str) -> bool:
    import importlib.util
    builder = Path(__file__).resolve().parent / "_build_prl_tex.py"
    spec = importlib.util.spec_from_file_location("_build_prl_tex", builder)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    tex = mod.table_tex(TABLE_MD, TABLE_CAPTION)
    print("Draft table, Markdown source (%d rows incl. header):" % len(TABLE_MD))
    for row in TABLE_MD:
        print("  " + row)
    print()
    ncol = len([c for c in TABLE_MD[0].strip().strip("|").split("|")])
    print("Draft table, LaTeX fragment emitted by tools/_build_prl_tex.py table_tex() "
          "(%d columns -> %s):" % (ncol, "table* (full width)" if ncol >= 4 else "table (single column)"))
    for ln in tex.splitlines():
        print("  " + ln)
    print()

    # every key in the table must already be cited in the manuscript and be in the reference list
    tbl_keys = set()
    for row in TABLE_MD:
        tbl_keys |= cite_keys(row)
    md_keys = cite_keys(text)
    import json
    refs = {r["key"] for r in json.loads((REPO / "paper_review_prl" / "_refs_used.json")
                                         .read_text(encoding="utf-8"))}
    missing_cite = sorted(tbl_keys - md_keys)
    missing_ref = sorted(tbl_keys - refs)
    print("Table key coverage: %d keys (%s)" % (len(tbl_keys), ", ".join(sorted(tbl_keys))))
    print("  all cited in MANUSCRIPT.md: %s%s" % ("yes" if not missing_cite else "NO ",
                                                  "" if not missing_cite else missing_cite))
    print("  all in _refs_used.json:     %s%s" % ("yes" if not missing_ref else "NO ",
                                                  "" if not missing_ref else missing_ref))
    print()
    return not (missing_cite or missing_ref)


def main() -> int:
    text = MD.read_text(encoding="utf-8")
    blocks = section_counts(text)
    print("Section word counts: %s" % MD.relative_to(REPO))
    print_section_counts(blocks, "")
    if PDF.exists():
        pages = pdf_pages()
        print_pdf_layout(pages, detail_pages=[])
    else:
        print("PDF not found: %s" % PDF)
    keys_ok = print_table_fragment(text)
    cuts_ok = validate_cuts(text) == 0
    return 0 if (keys_ok and cuts_ok) else 1


if __name__ == "__main__":
    raise SystemExit(main())