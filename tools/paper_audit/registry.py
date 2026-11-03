# -*- coding: utf-8 -*-
"""The paper-audit check registry (English-only artifact).

One entry per check. The runner executes every registered check and records a
Finding with PASS / FAIL / WARN / SKIP / MANUAL / ERROR. Checks marked
automated=False are reported as MANUAL with the prescribed evidence to attach.

Dimension codes
---------------
A  Reproducibility and provenance
B  Build and compilation integrity
C  Structure and completeness
D  Journal / venue compliance
E  References and citations
F  Content consistency and number traceability
G  Typography and PDF rendering
H  Data, ethics and declarations
I  Submission package and freeze safety
J  Evidence and hand-off documentation
"""
from __future__ import annotations

from .model import Check, Severity

S = Severity


def _c(cid, dim, sev, title, method, automated=True):
    return Check(id=cid, dimension=dim, severity=sev, title=title, method=method, automated=automated)


CHECKS = [
    # ------------------------------------------------------------------ A
    _c("A-01", "A", S.P1, "Git working tree is clean for the manuscript paths",
       "git status --porcelain limited to the manuscript directory is empty"),
    _c("A-02", "A", S.P3, "Audit records the git commit, branch and timestamp",
       "git rev-parse HEAD / branch --show-current captured in the report"),
    _c("A-03", "A", S.P2, "A build command is documented for this profile",
       "profile.build_command is set (or the README documents the build)"),
    _c("A-04", "A", S.P1, "The PDF is not older than the LaTeX sources",
       "mtime(pdf) >= max(mtime(*.tex, *.bib, figures referenced by included sources))"),
    _c("A-05", "A", S.P2, "Compilation log belongs to the current PDF",
       "mtime(pdf) and mtime(log) differ by less than 120 s"),
    _c("A-06", "A", S.P3, "Environment recorded (pdflatex, python, OS, git)",
       "versions captured in the report metadata"),
    _c("A-07", "A", S.P2, "Documented build cannot silently change tracked sources",
       "the build entry writes only generated artifacts (manual review if custom)", automated=False),
    _c("A-08", "A", S.P2, "No untracked artifacts inside the manuscript directory",
       "git status shows no untracked build products under the manuscript dir"),

    # ------------------------------------------------------------------ B
    _c("B-01", "B", S.P0, "Compilation finished without errors",
       "count of lines starting with '!' in the latest log == 0"),
    _c("B-02", "B", S.P0, "No undefined references",
       "count of 'Reference ... undefined' == 0"),
    _c("B-03", "B", S.P0, "No undefined citations",
       "count of 'Citation ... undefined' == 0"),
    _c("B-04", "B", S.P1, "No overfull horizontal boxes",
       "count of 'Overfull \\hbox' == 0"),
    _c("B-05", "B", S.P1, "No floats larger than the text block",
       "count of 'Float too large' == 0"),
    _c("B-06", "B", S.P2, "No unresolved LaTeX warnings",
       "'LaTeX Warning' lines reviewed; each must be explained"),
    _c("B-07", "B", S.P1, "No 'Rerun to get' request left in the log",
       "the final pass converged"),
    _c("B-08", "B", S.P2, "Page count in the log equals the PDF page count",
       "parse 'Output written on ... (N pages' and compare with pdfinfo"),
    _c("B-09", "B", S.P2, "No font warnings that indicate substitution",
       "LaTeX Font Warning lines are empty or explained"),
    _c("B-10", "B", S.P1, "A clean-room rebuild reproduces the expected page count",
       "copy sources to a temp dir, compile from scratch, compare pages (--staged)"),

    # ------------------------------------------------------------------ C
    _c("C-01", "C", S.P1, "All profile-required sections are present",
       "search the merged sources for each entry of profile.required_sections"),
    _c("C-02", "C", S.P0, "An abstract is present and unique",
       "exactly one abstract environment/command as declared by the profile"),
    _c("C-03", "C", S.P1, "Keywords are present",
       "keyword block found in the sources"),
    _c("C-04", "C", S.P0, "A bibliography is present",
       "external .bib or inline thebibliography found"),
    _c("C-05", "C", S.P2, "Every figure and table is referenced in the text",
       "all figure/table labels appear in at least one \\ref"),
    _c("C-06", "C", S.P2, "No unresolved cross-reference in the PDF",
       "PDF text contains no '??' or '(?)'"),
    _c("C-07", "C", S.P2, "No dead labels in the included sources",
       "labels defined in included files but never referenced (ignoring external references)"),
    _c("C-08", "C", S.P0, "Declarations precede the bibliography",
       "position of the first declaration < position of the bibliography"),
    _c("C-09", "C", S.P0, "All profile-required declarations are present",
       "each entry of profile.required_declarations is found"),
    _c("C-10", "C", S.P1, "Title, authors and affiliations are present",
       "\\title / \\author / affiliation block found"),

    # ------------------------------------------------------------------ D
    _c("D-01", "D", S.P0, "Page count respects the venue limit / target",
       "pdfinfo pages compared with profile.limits.pages_max / pages_target"),
    _c("D-02", "D", S.P0, "Abstract word count respects the venue limit",
       "source-side count (math expressions count as one token) <= limits.abstract_words_max"),
    _c("D-03", "D", S.P1, "Keyword count within the venue range",
       "number of keywords between limits.keywords_min and limits.keywords_max"),
    _c("D-04", "D", S.P1, "Highlights within the venue rules",
       "count and per-item character count within profile.limits.highlights_*"),
    _c("D-05", "D", S.P1, "Blinding rule respected",
       "if limits.blinded: author names / affiliations / acknowledgements must be absent"),
    _c("D-06", "D", S.P1, "Title within the venue character limit",
       "len(title) <= limits.title_chars_max (when set)"),
    _c("D-07", "D", S.P2, "Supplementary material page count as declared",
       "pdfinfo of the supplementary PDF compared with the profile / README"),
    _c("D-08", "D", S.P2, "Portal file names and item types are respected",
       "package files use the portal-facing names (Manuscript / Cover Letter / Highlights ...)"),
    _c("D-09", "D", S.P1, "Cover-letter claims agree with the built manuscript",
       "page count, abstract words and headline counts extracted from the cover letter are re-measured"),
    _c("D-10", "D", S.P2, "Declarations use the wording required by the venue",
       "manual review of funding / competing-interest / AI-disclosure phrasing", automated=False),

    # ------------------------------------------------------------------ E
    _c("E-01", "E", S.P0, "Every cited key exists in the reference database",
       "cite keys - bib keys == empty"),
    _c("E-02", "E", S.P2, "No unused bibliography entries",
       "bib keys - cite keys == empty (or each unused entry explained)"),
    _c("E-03", "E", S.P1, "Inline bibliography matches the cited keys",
       "count of \\bibitem equals distinct cite keys and all aux citation numbers resolve"),
    _c("E-04", "E", S.P2, "Citation numbering is contiguous in the PDF",
       "max numeric citation marker equals the number of references", automated=False),
    _c("E-05", "E", S.P2, "DOIs are syntactically valid",
       "every '10.<prefix>/<suffix>' DOI matches a conservative regex"),
    _c("E-06", "E", S.P2, "Software / data citations include a URL or DOI",
       "manual review of dataset and software references", automated=False),
    _c("E-07", "E", S.P1, "No duplicate bibliography entries",
       "same DOI or normalised title appearing twice"),
    _c("E-08", "E", S.P3, "Self-citations recorded (blinding / disclosure)",
       "list of candidate self-citations for manual review"),
    _c("E-09", "E", S.P2, "Reference ordering matches the style",
       "numeric styles sorted; author-year styles alphabetical (manual if style unclear)", automated=False),
    _c("E-10", "E", S.P2, "Every reference item has authors, title, venue and year",
       "manual spot check or parser for the active bibliography style", automated=False),

    # ------------------------------------------------------------------ F
    _c("F-01", "F", S.P0, "No placeholders or unresolved markers",
       "TODO / TBD / FIXME / XXX / [?] / ?? / lorem ipsum / 待补 found in sources or PDF"),
    _c("F-02", "F", S.P1, "No CJK characters in the manuscript sources",
       "regex scan of included .tex files (comments included)"),
    _c("F-03", "F", S.P1, "No corrupted LaTeX tokens in the PDF",
       "known broken tokens such as 'abla', 'nablaM', '<abla' absent from the PDF text"),
    _c("F-04", "F", S.P0, "Configured numerical claim ledgers pass",
       "profile.commands: claim-ledger scripts exit 0 and print the expected pass count"),
    _c("F-05", "F", S.P0, "Configured consistency gates pass",
       "profile.commands: consistency gates exit 0"),
    _c("F-06", "F", S.P1, "Key numbers appear in the expected contexts",
       "each value from profile.key_numbers is present in the listed files"),
    _c("F-07", "F", S.P1, "No stale counts or retired wording",
       "profile.forbidden_strings absent from sources, cover letter and PDF"),
    _c("F-08", "F", S.P2, "No duplicated sentences",
       "normalised sentences longer than 15 words appearing more than once"),
    _c("F-09", "F", S.P1, "Cover-letter page / word / experiment claims are true",
       "re-measured against the built PDF and the claim ledger"),
    _c("F-10", "F", S.P1, "No question-mark artefacts in the PDF",
       "isolated '?' markers that indicate missing references or data"),

    # ------------------------------------------------------------------ G
    _c("G-01", "G", S.P2, "No double-numbered section headings",
       "regex for headings such as '1. 1. Introduction' in the PDF text"),
    _c("G-02", "G", S.P1, "No HTML / XML markup in the PDF",
       "<scp>, <i>, <b>, &amp;, &lt;, &gt; absent"),
    _c("G-03", "G", S.P1, "No literal LaTeX commands in the PDF",
       "strings such as \\cite, \\ref, \\nabla, \\textbf absent from the text layer"),
    _c("G-04", "G", S.P2, "All fonts are embedded",
       "pdffonts shows no 'no' in the embedded column"),
    _c("G-05", "G", S.P2, "PDF metadata title / author match the manuscript",
       "pdfinfo Title / Author compared with the source \\title / \\author"),
    _c("G-06", "G", S.P2, "No blank pages except intentional ones",
       "pages with fewer than 20 extracted characters, excluding declared exceptions"),
    _c("G-07", "G", S.P2, "List numbering is monotone",
       "manual review of long checklists and enumerated contributions", automated=False),
    _c("G-08", "G", S.P3, "Line and page numbers behave as the venue expects",
       "page numbers present; line numbers continuous if required by the profile", automated=False),

    # ------------------------------------------------------------------ H
    _c("H-01", "H", S.P0, "Data availability statement present",
       "required by profile; must state where the data/results live"),
    _c("H-02", "H", S.P2, "Data statement links are well formed",
       "every URL / DOI in the data statement syntactically valid; if none is present, an explicit "
       "'no new data were generated' declaration passes, because the quantitative values are then quoted "
       "from the cited literature and a repository pointer would be false (rationale 2026-10-25: the PRL "
       "Commentary generates no data; removed its archive/DOI sentence rather than inventing one)"),
    _c("H-03", "H", S.P1, "Generative-AI disclosure present if the profile requires it",
       "declaration found and mentions the tools used"),
    _c("H-04", "H", S.P1, "Competing-interest declaration present",
       "declaration found"),
    _c("H-05", "H", S.P1, "Funding declaration present",
       "declaration found"),
    _c("H-06", "H", S.P2, "CRediT / author-contribution statement present if required",
       "declaration found"),
    _c("H-07", "H", S.P3, "Ethics / consent statement present if applicable",
       "manual: no human-subject data in this project; record N/A"),

    # ------------------------------------------------------------------ I
    _c("I-01", "I", S.P0, "Submission package contains the expected files",
       "profile.package contains all expected portal items"),
    _c("I-02", "I", S.P1, "Package copies match the live manuscript files",
       "byte-first: sha256(package file) == sha256(live source) per mapped pair; a PDF pair that "
       "byte-differs is re-checked in content mode (page count + extracted-text hash + size delta "
       "<= 1%) because pdfTeX embeds a creation date/trailer ID, so a rebuild is not byte-stable. "
       "A frozen package (package_frozen) is reported as a NAMED warning giving the package path, its "
       "snapshot date, the file count and the per-file page/text divergence, and pointing at the "
       "frozen-hash check I-04; it is never compared byte-wise and never silently skipped"),
    _c("I-03", "I", S.P1, "Package LaTeX source compiles standalone",
       "independent temp-dir compile of the package source (--staged)"),
    _c("I-04", "I", S.P0, "Frozen submission artefacts are unchanged",
       "sha256 tree equals tools/paper_audit/freeze/<profile>.json"),
    _c("I-05", "I", S.P2, "Package file sizes within portal limits",
       "every file <= profile.limits.portal_size_mb"),
    _c("I-06", "I", S.P2, "Package README states the measured facts",
       "page count / word count / ledger numbers recomputed and compared"),
    _c("I-07", "I", S.P2, "Source archive is valid and complete",
       "zipfile.testzip() is None and entry count matches the source tree"),
    _c("I-08", "I", S.P2, "No manuscript / PDF leaks into the public repository mirror",
       "publish_clean contains no paper* / main*.tex / main*.pdf (profile.public_mirror)"),

    # ------------------------------------------------------------------ J
    _c("J-01", "J", S.P1, "Claim-ledger evidence file exists and is current",
       "outputs/analysis claim-ledger JSON newer than the manuscript sources"),
    _c("J-02", "J", S.P2, "An audit report is archived with a stable identifier",
       "this report is written to docs/audits/ and the JSON carries the git commit"),
    _c("J-03", "J", S.P2, "HANDOFF.md and 文件地图.md record the current status",
       "manual: the latest status block mentions the profile label and date", automated=False),
    _c("J-04", "J", S.P3, "A fix-evidence file exists for the latest fix round",
       "FIXES_<date>.md present in the manuscript directory when fixes were made"),
    _c("J-05", "J", S.P2, "The audit itself is reproducible",
       "the report lists every command executed and the environment versions"),
    # ------------------------------------------------------------------ N
    # Phase-1 mechanical gates (2026-10-25). Data-driven by versioned docs/ registries; a check
    # that cannot determine an answer reports MANUAL, never PASS.
    _c("N-01", "F", S.P1, "One canonical value per quantity, archive-backed",
       "docs/QUANTITY_REGISTRY.json: the archive field equals the canonical value at the stated "
       "rounding, and every registered text mention prints the canonical rounding or an explicitly "
       "allowed variant (catches one quantity printed with two different values)"),
    _c("N-02", "F", S.P1, "Sign/direction statements match the registered semantics",
       "docs/SIGN_REGISTRY.json: a paired-difference sentence that calls a negative value better "
       "(or worse) against lower_is is a failure; directional sentences without a parsable value "
       "are MANUAL"),
    _c("N-03", "C", S.P1, "Cross-references resolve to real targets",
       "built PDF text: no leaked \\ref fragment / 'ref{' / '??', no 'Appendix Appendix', every "
       "Section/Appendix/Table/Figure pointer exists in the counter index simulated from the "
       "LaTeX source, and no starred section label is referenced by number"),
    _c("N-04", "H", S.P1, "Data/archive statements are verifiable",
       "docs/RELEASE_LEDGER.json: every DOI/URL in the data statement is registered, and every "
       "'contains/archived' claim names an object the release actually holds (manuscripts and "
       "compiled PDFs are excluded by the release policy)"),
    _c("N-05", "E", S.P1, "Reference metadata matches the verified cache",
       "docs/REF_VERIFICATION.json: title / first author / year of every DOI- or arXiv-bearing "
       "bibliography entry equals the cached verified metadata; uncached entries are MANUAL"),
    _c("N-07", "A", S.P2, "Audit runs leave no untracked artifacts",
       "docs/audits/* is git-ignored except .gitkeep, and git status shows no untracked AUD-* file"),
]

DIMENSIONS = {
    "A": "Reproducibility and provenance",
    "B": "Build and compilation integrity",
    "C": "Structure and completeness",
    "D": "Journal / venue compliance",
    "E": "References and citations",
    "F": "Content consistency and number traceability",
    "G": "Typography and PDF rendering",
    "H": "Data, ethics and declarations",
    "I": "Submission package and freeze safety",
    "J": "Evidence and hand-off documentation",
}


def by_id(cid: str):
    for c in CHECKS:
        if c.id == cid:
            return c
    raise KeyError(cid)
