# -*- coding: utf-8 -*-
r"""Build the PRL Commentary LaTeX source and PDF from MANUSCRIPT.md.

    MANUSCRIPT.md  ->  main_prl.tex  ->  main_prl.pdf   (three pdflatex passes)

The conversion enforces the fixes recorded in FIXES_2026-10-18.md:

* manual heading numbers in the markdown are stripped, so the cas-dc class is
  the only source of section numbers ("1. 1. Introduction" cannot recur);
* a numbered checklist interrupted by bold sub-headings is emitted as ONE
  enumerate, so continuation lines stay inside their item and the printed
  items run 1..12;
* publication markup (<scp>, &amp;) leaked from the reference database is
  removed and the empty "ORCID(s):" footnote label is suppressed;
* table captions are attached to their floats instead of being left behind as
  body paragraphs;
* keywords are read from MANUSCRIPT.md (the submitted PDF and the submission
  portal had drifted apart: 5 vs 6 keywords);
* after the build the result is checked: page count, LaTeX errors, undefined
  references/citations, Overfull boxes, the 1..12 checklist, keyword count,
  residual HTML artefacts, and that cover_letter.tex carries the same title.

Usage:  python tools/_build_prl_tex.py
"""
from __future__ import annotations

import html
import json
import re
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "paper_review_prl"
MD = OUT / "MANUSCRIPT.md"
TEX = OUT / "main_prl.tex"
PDF = OUT / "main_prl.pdf"
LOG = OUT / "main_prl.log"
REFS = OUT / "_refs_used.json"
COVER = OUT / "cover_letter.tex"

MAX_PAGES = 7              # PRL Commentary: double column, 7 pages including all material
MAX_ABSTRACT_WORDS = 250   # PRL guide
MAX_KEYWORDS = 7           # PRL guide: 1 to 7 keywords
MAX_HIGHLIGHT_CHARS = 85   # PRL guide: 3 to 5 bullets, each at most 85 characters
CHECKLIST_ITEMS = 12       # "twelve-item reporting checklist" (Section 4)

SHORT_TITLE = "Allocation, not selection"
AUTHOR = "Hongrui Wan"
EMAIL = "hw4c24@soton.ac.uk"

HIGHLIGHTS = [
    "Adaptation is two decisions: where capacity goes, and how it is divided",
    "Most multimodal PEFT papers conflate the two decisions",
    "Reported POPE values are incomparable when one paper does not name the subset",
    "A protocol change moves MMBench scores by an order of magnitude",
    "Twelve reporting items would make adaptation results comparable",
]

BS = chr(92)   # backslash, kept in a variable so that this file has no fragile escapes
NL = chr(10)

# ---------------------------------------------------------------------------
# text conversion helpers
# ---------------------------------------------------------------------------

ESCAPES = {
    BS: BS + "textbackslash{}",
    "&": BS + "&",
    "%": BS + "%",
    "$": BS + "$",
    "#": BS + "#",
    "_": BS + "_",
    "{": BS + "{",
    "}": BS + "}",
    "~": BS + "textasciitilde{}",
    "^": BS + "textasciicircum{}",
}

# publisher markup that leaks out of the reference database, e.g. <scp>AutoPEFT</scp>
TAG_RE = re.compile(r"</?(?:scp|italic|bold|sub|sup|sm|hi|tt|sc|small|big)>", re.I)

KEY_RE = re.compile(r"^[a-z][a-z0-9_]*[0-9][a-z0-9_]*$")
BRACKET_RE = re.compile(r"\[([^\[\]]+)\]")


def latex_escape(s: str) -> str:
    """Escape LaTeX special characters (one pass, no double escaping)."""
    return "".join(ESCAPES.get(ch, ch) for ch in s)


def clean_markup(s: str) -> str:
    """Remove publisher tags and decode HTML entities left in bibliographic data."""
    return TAG_RE.sub("", html.unescape(str(s)))


def _split_citations(s: str):
    """Replace [key] / [key1; key2] citations by placeholders; return the keys."""
    keys: list = []

    def repl(m):
        parts = [p.strip() for p in re.split(r"[;,]", m.group(1))]
        if parts and all(KEY_RE.match(p) for p in parts):
            keys.append(",".join(parts))
            return chr(0) + "C" + str(len(keys) - 1) + chr(0)
        return m.group(0)

    return BRACKET_RE.sub(repl, s), keys


def _restore_citations(s: str, keys: list) -> str:
    def repl(m):
        return BS + "cite{" + keys[int(m.group(1))] + "}"

    return re.sub(chr(0) + "C([0-9]+)" + chr(0), repl, s)


def _emphasis(s: str) -> str:
    """Markdown emphasis to LaTeX; run after escaping so the braces stay intact."""
    s = re.sub(r"\*\*(.+?)\*\*", lambda m: BS + "textbf{" + m.group(1) + "}", s, flags=re.S)
    s = re.sub(r"(?<!\*)\*([^*]+?)\*(?!\*)", lambda m: BS + "emph{" + m.group(1) + "}", s, flags=re.S)
    return s


def inline(s: str) -> str:
    """Convert one span of markdown prose (or one table cell) to LaTeX."""
    s = clean_markup(s)
    s = re.sub(r"\s+", " ", s).strip()
    s, keys = _split_citations(s)
    s = latex_escape(s)
    s = _emphasis(s)
    return _restore_citations(s, keys)


# ---------------------------------------------------------------------------
# markdown -> LaTeX
# ---------------------------------------------------------------------------

ITEM_RE = re.compile(r"^(?:(\d+)\.|[-*])\s+(.*)$")
BOLD_ONLY_RE = re.compile(r"^\*\*([^*]+)\*\*.?$")
TABLE_CAPTION_RE = re.compile(r"^\*\*Table\s+[0-9]+\.\*\*\s*(.*)$")
UNNUMBERED_RE = re.compile(r"\s*{\.unnumbered}\s*$")
HEADING_NUM_RE = re.compile(r"^[0-9]+(?:\.[0-9]+)*\.?\s+")


def _strip_heading_number(s: str) -> str:
    return HEADING_NUM_RE.sub("", s, count=1)


def _skip_blank(lines: list, i: int) -> int:
    while i < len(lines) and not lines[i].strip():
        i += 1
    return i


def _list_items(lines: list, i: int):
    """Parse one markdown list.

    Returns (kind, items, next_index).  Each item is a two-element list
    [label, text]; a bold sub-heading inside the list becomes [label, None].
    An indented continuation line is appended to the previous item instead of
    becoming an item of its own (this is what produced 18 instead of 12 items).
    """
    items: list = []
    kind = None
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            break
        m = ITEM_RE.match(line.strip())
        if m:
            this = "ol" if m.group(1) else "ul"
            if kind is None:
                kind = this
            elif this != kind:
                break
            items.append([None, m.group(2).strip()])
            i += 1
            continue
        if items and line.startswith((" ", chr(9))) and not ITEM_RE.match(line.strip()):
            items[-1][1] = (items[-1][1] + " " + line.strip()).strip()
            i += 1
            continue
        break
    return kind, items, i


def _list_tex(kind: str, items: list) -> str:
    env = "enumerate" if kind == "ol" else "itemize"
    body = []
    for label, text in items:
        if text is None:
            body.append("  " + BS + "item[] " + BS + "textbf{" + inline(label) + "}")
        else:
            body.append("  " + BS + "item " + inline(text))
    return BS + "begin{" + env + "}" + NL + NL.join(body) + NL + BS + "end{" + env + "}"


def table_tex(rows: list, caption: str) -> str:
    """Markdown pipe table to a single-column tabularx float that fits the column.

    The previous fixed-width tabular was 21.9pt wider than the column (an
    Overfull hbox that overlapped the gutter); tabularx cannot overflow.
    """
    cells = [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows]
    header = cells[0]
    body = [r for r in cells[1:] if not re.match(r"^[\s:|-]+$", "|".join(r))]
    ncol = len(header)
    body = [(r + [""] * ncol)[:ncol] for r in body]
    full = ncol >= 4
    env = "table*" if full else "table"
    width = BS + "textwidth" if full else BS + "linewidth"
    xcols = " ".join([">{" + BS + "raggedright" + BS + "arraybackslash}X"] * (ncol - 1))
    spec = "@{}l " + xcols + " @{}"
    out = [BS + "begin{" + env + "}[t]", BS + "centering", BS + "footnotesize"]
    if caption:
        out.append(BS + "caption{" + inline(caption) + "}")
    out += [BS + "begin{tabularx}{" + width + "}{" + spec + "}",
            BS + "toprule",
            " & ".join(inline(c) for c in header) + " " + BS + BS,
            BS + "midrule"]
    for r in body:
        out.append(" & ".join(inline(c) for c in r) + " " + BS + BS)
    out += [BS + "bottomrule", BS + "end{tabularx}", BS + "end{" + env + "}"]
    return NL.join(out)


def md_to_tex(text: str) -> str:
    """Minimal markdown to LaTeX for the blocks this manuscript uses."""
    lines = text.splitlines()
    out: list = []
    i, n = 0, len(lines)
    while i < n:
        stripped = lines[i].strip()
        if not stripped:
            i += 1
            continue

        # --- table caption placed before its table -------------------------
        cm = TABLE_CAPTION_RE.match(stripped)
        if cm:
            j = _skip_blank(lines, i + 1)
            if j < n and lines[j].strip().startswith("|"):
                rows = []
                i = j
                while i < n and lines[i].strip().startswith("|"):
                    rows.append(lines[i].strip())
                    i += 1
                out.append(table_tex(rows, cm.group(1).strip()))
                continue

        # --- pipe table + its caption (the caption follows the table) ------
        if stripped.startswith("|"):
            rows = []
            while i < n and lines[i].strip().startswith("|"):
                rows.append(lines[i].strip())
                i += 1
            caption = ""
            j = _skip_blank(lines, i)
            if j < n:
                cm = TABLE_CAPTION_RE.match(lines[j].strip())
                if cm:
                    caption = cm.group(1).strip()
                    i = j + 1
            out.append(table_tex(rows, caption))
            continue

        # --- headings (manual numbers are stripped; {.unnumbered} -> *) ----
        if stripped.startswith("### ") or stripped.startswith("## "):
            level = 3 if stripped.startswith("### ") else 2
            title = stripped[level:].strip()
            unnumbered = bool(UNNUMBERED_RE.search(title))
            title = UNNUMBERED_RE.sub("", title)
            title = _strip_heading_number(title)
            cmd = BS + ("subsection" if level == 3 else "section") + ("*" if unnumbered else "")
            out.append(cmd + "{" + inline(title) + "}")
            i += 1
            continue

        # --- skipped material: title, block quotes, rules ------------------
        if stripped.startswith("# ") or stripped.startswith(">") or stripped == "---":
            i += 1
            continue

        # --- lists, including checklist groups split by bold sub-headings --
        start_list = bool(ITEM_RE.match(stripped))
        lead_label = None
        if not start_list:
            bm = BOLD_ONLY_RE.match(stripped)
            if bm:
                j = _skip_blank(lines, i + 1)
                if j < n and ITEM_RE.match(lines[j].strip()) and ITEM_RE.match(lines[j].strip()).group(1):
                    lead_label = bm.group(1).strip()
                    i = j
                    start_list = True
        if start_list:
            kind, items, i = _list_items(lines, i)
            if lead_label and kind == "ol":
                items = [[lead_label, None]] + items
            if kind == "ol":
                while True:
                    j = _skip_blank(lines, i)
                    if j >= n:
                        break
                    bm = BOLD_ONLY_RE.match(lines[j].strip())
                    if not bm:
                        break
                    k = _skip_blank(lines, j + 1)
                    if k >= n:
                        break
                    nxt = ITEM_RE.match(lines[k].strip())
                    if not nxt or not nxt.group(1):
                        break
                    kind2, items2, i = _list_items(lines, k)
                    if kind2 != "ol":
                        break
                    items.append([bm.group(1).strip(), None])
                    items.extend(items2)
            out.append(_list_tex(kind, items))
            continue

        # --- ordinary paragraph -------------------------------------------
        para = [stripped]
        i += 1
        while i < n:
            nxt = lines[i].strip()
            if (not nxt or nxt.startswith("|") or nxt.startswith("#") or nxt.startswith(">")
                    or ITEM_RE.match(nxt) or nxt == "---"):
                break
            para.append(nxt)
            i += 1
        out.append(inline(" ".join(para)))
    return NL.join(out)


# ---------------------------------------------------------------------------
# bibliography
# ---------------------------------------------------------------------------

def bibitems() -> str:
    items = json.loads(REFS.read_text(encoding="utf-8"))
    out = [BS + "begin{thebibliography}{00}", BS + "scriptsize"]
    for r in sorted(items, key=lambda x: x["key"]):
        au = clean_markup(r.get("authors") or "Unknown")
        if au.count(", ") >= 4 and "et al" not in au:
            au = ", ".join(au.split(", ")[:3]) + " et al."
        ti = clean_markup(r.get("title") or "")
        ve = clean_markup(r.get("venue") or "")
        yr = str(r.get("year") or "")
        bits = au + ", " + ti
        if ve:
            bits += ", " + ve
        if yr:
            bits += " (" + yr + ")"
        out.append(BS + "bibitem{" + r["key"] + "} " + latex_escape(bits) + ".")
    out.append(BS + "end{thebibliography}")
    return NL.join(out)


# ---------------------------------------------------------------------------
# document template
# ---------------------------------------------------------------------------

FIGURE = NL.join([
    BS + "begin{figure*}[t]",
    BS + "centering",
    BS + "includegraphics[width=0.75" + BS + "textwidth]{figures/fig1_decision_space.pdf}",
    BS + "caption{The two decisions and their independence. The horizontal axis is where adaptive capacity is",
    "placed; the vertical axis is how a fixed budget is divided. Points mark the approximate position of",
    "representative methods (a qualitative sketch, not measured coordinates). The shaded column shows that",
    "one site admits several allocation strategies, which is why the two decisions have to be reported",
    "separately.}",
    BS + "label{fig:decision}",
    BS + "end{figure*}",
])

# cas-dc 2.4 typesets the keyword column in a 0pt-wide hbox inside its Abstract
# environment; that is what produced the 123.6pt Overfull hbox at \maketitle.
# The replacement below is the class code with .25\textwidth as the hbox width,
# which is the column's real width, so the box can no longer overflow.
ABSTRACT_PATCH = NL.join([
    BS + "ExplSyntaxOn",
    BS + "RenewDocumentEnvironment { Abstract } { o }",
    "{",
    "  " + BS + "group_begin:",
    "  " + BS + "IfNoValueTF { #1 } { } { " + BS + "tex_gdef:D " + BS + "abstractname { #1 } }",
    "  " + BS + "parindent = 0pt",
    "  " + BS + "box_if_empty:NTF " + BS + "g_stm_key_box",
    "  { " + BS + "leftskip = .35 " + BS + "textwidth }",
    "  {",
    "    " + BS + "dim_gset:Nn " + BS + "l_tmpa_dim { " + BS + "box_ht:N " + BS + "g_stm_key_box }",
    "    " + BS + "dim_gadd:Nn " + BS + "l_tmpa_dim { " + BS + "box_dp:N " + BS + "g_stm_key_box }",
    "    " + BS + "leftskip .35" + BS + "textwidth",
    "    " + BS + "hspace*{-.35 " + BS + "textwidth }",
    "    " + BS + "noindent" + BS + "hbox_to_wd:nn { .25" + BS + "textwidth } { " + BS + "box " + BS + "g_stm_key_box }",
    "    " + BS + "skip_vertical:n { -" + BS + "l_tmpa_dim }",
    "  }",
    "  " + BS + "noindent " + BS + "abstractname " + BS + "par",
    "  " + BS + "skip_vertical:n { -4pt}",
    "  " + BS + "noindent " + BS + "rule{.65" + BS + "textwidth}{.2pt}" + BS + "par " + BS + "footnotesize",
    "  " + BS + "ignorespaces " + BS + "everypar { " + BS + "parindent=1.5em }",
    "}{ " + BS + "par " + BS + "group_end: }",
    BS + "ExplSyntaxOff",
])


def template(title: str, abstract: str, keywords: list, body: str, bib: str) -> str:
    hl = NL.join(BS + "item " + latex_escape(h) for h in HIGHLIGHTS)
    kw = (" " + BS + "sep ").join(latex_escape(k) for k in keywords)
    head = [
        "%% PRL Commentary -- generated from MANUSCRIPT.md by tools/_build_prl_tex.py",
        "%% Edit MANUSCRIPT.md, not this file; re-run the builder after any change.",
        BS + "documentclass[a4paper]{cas-dc}",
        BS + "usepackage[numbers,sort&compress]{natbib}",
        BS + "usepackage{amsmath,amssymb}",
        BS + "usepackage{booktabs}",
        BS + "usepackage{tabularx}",
        BS + "usepackage{graphicx}",
        BS + "usepackage{hyperref}",
        BS + "hypersetup{pdftitle={" + latex_escape(title) + "}}",
        "",
        "%% --- cas-dc 2.4 output fixes (see paper_review_prl/FIXES_2026-10-18.md) ---",
        "%% 1. The class always prints an ORCID(s): footnote label, even with no ORCID iD given.",
        BS + "RenewDocumentCommand{" + BS + "printorcid}{}{}",
        ABSTRACT_PATCH,
        "",
        BS + "begin{document}",
        BS + "shorttitle{" + latex_escape(SHORT_TITLE) + "}",
        BS + "shortauthors{H. Wan}",
        "",
        BS + "title[mode=title]{" + latex_escape(title) + "}",
        "",
        BS + "author[1]{" + AUTHOR + "}",
        BS + "cormark[1]",
        BS + "ead{" + EMAIL + "}",
        BS + "affiliation[1]{organization={University of Southampton}, city={Southampton},",
        "  postcode={SO17 1BJ}, country={United Kingdom}}",
        BS + "cortext[1]{Corresponding author. Institutional email: " + EMAIL + "}",
        "",
        BS + "begin{abstract}",
        abstract,
        BS + "end{abstract}",
        "",
        BS + "begin{highlights}",
        hl,
        BS + "end{highlights}",
        "",
        BS + "begin{keywords}",
        kw,
        BS + "end{keywords}",
        "",
        BS + "maketitle",
        "",
        "",
        body,
        "",
        bib,
        "",
        BS + "end{document}",
    ]
    return NL.join(head) + NL


# ---------------------------------------------------------------------------
# build + verification
# ---------------------------------------------------------------------------

def main() -> int:
    md = MD.read_text(encoding="utf-8")
    lines = md.splitlines()

    title = next((ln[2:].strip() for ln in lines if ln.startswith("# ")), "")
    if not title:
        print("ERROR: no H1 title in " + MD.name)
        return 1

    try:
        abs_at = next(i for i, ln in enumerate(lines) if ln.strip() == "## Abstract")
    except StopIteration:
        print("ERROR: no '## Abstract' section in " + MD.name)
        return 1

    abstract_lines, keywords = [], []
    i = abs_at + 1
    while i < len(lines):
        s = lines[i].strip()
        if s.startswith("**Keywords"):
            kw_lines = [s]
            j = i + 1
            while j < len(lines) and lines[j].strip() and not lines[j].strip().startswith(("## ", "# ")):
                kw_lines.append(lines[j].strip())
                j += 1
            kw_text = " ".join(kw_lines)
            kw_text = re.sub(r"^\*\*Keywords:?\*\*:?", "", kw_text).strip()
            keywords = [k.strip() for k in re.split(r"[·;]", kw_text) if k.strip()]
            break
        if s.startswith("## "):
            break
        if s:
            abstract_lines.append(s)
        i += 1
    abstract = " ".join(abstract_lines).strip()
    if not abstract or not keywords:
        print("ERROR: abstract or keywords not found in " + MD.name)
        return 1

    try:
        body_at = next(i for i, ln in enumerate(lines) if ln.strip().startswith("## 1. Introduction"))
    except StopIteration:
        body_at = next((i for i, ln in enumerate(lines) if ln.startswith("## ")), None)
        if body_at is None:
            print("ERROR: no body sections in " + MD.name)
            return 1
    body = md_to_tex(NL.join(lines[body_at:]))

    tex = template(title, inline(abstract), keywords, body, bibitems())
    TEX.write_text(tex, encoding="utf-8", newline="")

    # --- checks on the generated source (the defects must not come back) ---
    problems: list = []
    if "<scp>" in tex or "&amp;" in tex:
        problems.append("HTML/XML artefacts in main_prl.tex")
    if re.search(r"\\(?:sub)?section\{[0-9]", tex):
        problems.append("a heading still carries a manual number")
    if BS + "printorcid" not in tex:
        problems.append("ORCID label fix missing from the preamble")
    sec = re.search(r"\\section{A reporting checklist}(.*?)\\section{Conclusions}", body, re.S)
    checklist = -1
    if not sec:
        problems.append("reporting-checklist section not found")
    else:
        envs = re.findall(r"\\begin{enumerate}(.*?)\\end{enumerate}", sec.group(1), re.S)
        if len(envs) != 1:
            problems.append("the checklist is split into " + str(len(envs)) + " enumerate blocks")
        else:
            real = [ln for ln in envs[0].splitlines() if ln.strip().startswith(BS + "item ")]
            checklist = len(real)
            if checklist != CHECKLIST_ITEMS:
                problems.append("checklist has " + str(checklist) + " items, expected " + str(CHECKLIST_ITEMS))
    cite_keys: set = set()
    for m in re.finditer(r"\\cite{([^}]*)}", tex):
        cite_keys.update(m.group(1).split(","))
    n_bib = tex.count(BS + "bibitem{")
    if len(cite_keys) != n_bib:
        problems.append("cite keys (" + str(len(cite_keys)) + ") != bibliography entries (" + str(n_bib) + ")")

    # --- compile ------------------------------------------------------------
    for _ in range(3):
        subprocess.run(["pdflatex", "-interaction=nonstopmode", TEX.name], cwd=OUT, capture_output=True)
    if not LOG.exists() or not PDF.exists():
        print("ERROR: pdflatex produced no log/pdf")
        return 1
    log = LOG.read_text(encoding="utf-8", errors="ignore")
    errors = [ln for ln in log.splitlines() if ln.startswith("!")]
    undef_ref = len(re.findall("Reference " + chr(96) + "[^']*' on page [0-9]+ undefined", log))
    undef_cite = len(re.findall("Citation " + chr(96) + "[^']*' .*undefined", log))
    overfull = re.findall(r"Overfull \\hbox \(([0-9.]+)pt", log)

    info = subprocess.run(["pdfinfo", str(PDF)], capture_output=True).stdout.decode("utf-8", "ignore")
    pm = re.search(r"Pages:\s+([0-9]+)", info)
    pages = int(pm.group(1)) if pm else -1
    pdf_text = ""
    try:
        pdf_text = subprocess.run(["pdftotext", str(PDF), "-"],
                                  capture_output=True).stdout.decode("utf-8", "ignore")
    except Exception:
        pass

    if pages > MAX_PAGES:
        problems.append("PDF has " + str(pages) + " pages (limit " + str(MAX_PAGES) + ")")
    if errors:
        problems.append(str(len(errors)) + " LaTeX error(s)")
    if undef_ref or undef_cite:
        problems.append("undefined references/citations: " + str(undef_ref) + "/" + str(undef_cite))
    for artefact in ("<scp>", "&amp;", "ORCID (s):", "ORCID(s):"):
        if artefact in pdf_text:
            problems.append("PDF text contains " + repr(artefact))
    if "??" in pdf_text:
        problems.append("PDF text contains '??'")
    abs_words = len(abstract.split())
    if abs_words > MAX_ABSTRACT_WORDS:
        problems.append("abstract has " + str(abs_words) + " words (limit " + str(MAX_ABSTRACT_WORDS) + ")")
    if not 1 <= len(keywords) <= MAX_KEYWORDS:
        problems.append("keyword count outside 1.." + str(MAX_KEYWORDS))

    cl_text = re.sub(r"\s+", " ", COVER.read_text(encoding="utf-8")) if COVER.exists() else ""
    if not cl_text:
        problems.append("cover_letter.tex missing")
    elif re.sub(r"\s+", " ", title) not in cl_text:
        problems.append("cover_letter.tex does not carry the manuscript title")

    # --- report -------------------------------------------------------------
    print("build: " + TEX.name + " -> " + PDF.name)
    print("  pages            : %d (limit %d)" % (pages, MAX_PAGES))
    print("  LaTeX errors     : %d" % len(errors))
    print("  undefined refs   : %d / cites: %d" % (undef_ref, undef_cite))
    print("  overfull hboxes  : %d %s" % (len(overfull), str(overfull) if overfull else ""))
    print("  abstract words   : %d (limit %d)" % (abs_words, MAX_ABSTRACT_WORDS))
    print("  keywords         : %d (limit %d)" % (len(keywords), MAX_KEYWORDS))
    print("  highlights       : %d (max %d chars)" % (len(HIGHLIGHTS), max(len(h) for h in HIGHLIGHTS)))
    print("  bibliography     : %d entries" % n_bib)
    print("  checklist items  : %d" % checklist)
    if overfull:
        print("WARNING: Overfull hboxes remain; check the log.")
    if problems:
        print("FAILED checks:")
        for p in problems:
            print("  - " + p)
        return 1
    print("OK: all build checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
