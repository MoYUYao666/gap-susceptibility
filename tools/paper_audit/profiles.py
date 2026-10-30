# -*- coding: utf-8 -*-
"""Manuscript / venue profiles for the paper-audit mode (English-only artifact).

A profile tells the runner where the manuscript lives, which constraints the
venue imposes, which claim ledgers and consistency gates must pass, and which
artefacts are frozen (never to be modified while a manuscript is under review).

Paths are relative to the repository root unless stated otherwise.
"""
from __future__ import annotations

from copy import deepcopy

BASE_LIMITS = {
    "pages_max": None,
    "pages_target": None,
    "abstract_words_max": 250,
    "keywords_min": 1,
    "keywords_max": 8,
    "highlights_min": None,
    "highlights_max": None,
    "highlight_chars_max": 85,
    "title_chars_max": None,
    "blinded": False,
    "portal_size_mb": 50,
}

BASE_PROFILE = {
    "id": "",
    "label": "",
    "manuscript": ".",
    "tex": [],
    "pdfs": [],
    "logs": [],
    "package": None,
    "package_expected": [],
    "package_map": [],
    # A frozen (already submitted) package legitimately diverges from the live draft: the
    # submitted version stays fixed while the draft is revised under review. When this is
    # True the package is NOT compared byte-wise with the live files (I-02 reports a NAMED
    # warning instead) and its integrity is covered by the freeze manifest (I-04).
    "package_frozen": False,
    "supplementary": None,
    "cover_letter": None,
    "highlights": None,
    "abstract_style": "env",
    "limits": BASE_LIMITS,
    "required_sections": [],
    "required_declarations": [],
    "forbidden_strings": [],
    "key_numbers": {},
    "commands": [],
    "freeze_paths": [],
    "freeze_manifest": None,
    "public_mirror": "publish_clean",
    "notes": "",
}


def _p(pid, label, **overrides):
    prof = deepcopy(BASE_PROFILE)
    prof["id"] = pid
    prof["label"] = label
    prof["freeze_manifest"] = "tools/paper_audit/freeze/%s.json" % pid
    lim = deepcopy(BASE_LIMITS)
    lim.update(overrides.pop("limits", {}))
    prof["limits"] = lim
    prof.update(overrides)
    return prof


PAPER_A_SECTIONS = [
    "Introduction", "Related Work", "Empirical", "Theory", "Validation",
    "Discussion", "Conclusion",
]
PAPER_A_DECLARATIONS = [
    "Data availability", "Funding", "Declaration of competing interests",
    "CRediT", "Declaration of generative AI",
]
PAPER_A_COMMANDS = [
    {"name": "Paper A claim ledger", "cmd": ["python", "tools/_claim_ledger_paperA.py", "--apply"],
     "expect": "PASS 88", "kind": "ledger"},
    {"name": "Main claim ledger", "cmd": ["python", "tools/_claim_ledger.py", "--apply"],
     "expect": "通过 96", "kind": "ledger"},
    {"name": "Paper A consistency gate", "cmd": ["python", "tools/_p1181_verify_paperA_consistency.py"],
     "expect": "0 failure", "kind": "gate"},
]

PROFILES = {
    "paperA_nc": _p(
        "paperA_nc", "Paper A - Neurocomputing (elsarticle)",
        manuscript="paper合",
        tex=["main_nc.tex"],
        pdfs=["main_nc.pdf"],
        logs=["main_nc.log"],
        package="SUBMISSION/PaperA_Neurocomputing",
        package_expected=["Manuscript.pdf", "Cover Letter.pdf", "Highlights.pdf",
                          "Highlights.txt", "Abstract.pdf", "latex_source.zip", "README.md"],
        package_map=[["Manuscript.pdf", "main_nc.pdf"],
                     ["Cover Letter.pdf", "cover_letter_nc.pdf"],
                     ["Highlights.pdf", "highlights_nc.pdf"],
                     ["Highlights.txt", "highlights_nc.txt"],
                     ["Abstract.pdf", "abstract_nc.pdf"]],
        cover_letter="cover_letter_nc.tex",
        highlights="highlights_nc.txt",
        limits={"pages_max": None, "abstract_words_max": 250, "keywords_min": 1,
                "keywords_max": 6, "highlights_min": 3, "highlights_max": 5},
        required_sections=PAPER_A_SECTIONS,
        required_declarations=PAPER_A_DECLARATIONS,
        forbidden_strings=["383 experiments", "68 pages", "234 words", "five random seeds",
                           "95 under strict freezing", "BLIP-2", "two PEFT methods"],
        key_numbers={"317": ["paper合/sections", "paper合/main_nc.tex"],
                     "221": ["paper合/sections"],
                     "96": ["paper合/sections"],
                     "104": ["paper合/sections"]},
        commands=PAPER_A_COMMANDS,
        build_command=["python", "tools/_p1174_build_paperA_editorial.py", "--apply"],
        staged_command=["python", "tools/_p1169_refresh_nc_submission.py"],
        staged_expect="staged build OK",
        # 2026-10-25: the submitted package is FROZEN while the revision is prepared; I-02 then
        # reports a NAMED warning (package path + snapshot + divergence) and I-04 covers integrity.
        package_frozen=True,
        freeze_paths=["SUBMISSION/PaperA_Neurocomputing"],
        notes=("Submitted to Neurocomputing (NEUCOM-D-26-23760, With Editor since 2026-10-19); "
               "the package SUBMISSION/PaperA_Neurocomputing/ is frozen at its upload snapshot "
               "while the live draft continues to be revised."),
    ),
    "paperA_springer": _p(
        "paperA_springer", "Paper A - Springer variant (sn-jnl)",
        manuscript="paper合",
        tex=["main_springer.tex"],
        pdfs=["main_springer.pdf"],
        logs=["main_springer.log"],
        abstract_style="command",
        highlights="highlights_nc.txt",
        limits={"abstract_words_max": 250, "keywords_min": 1, "keywords_max": 6,
                "highlights_min": 3, "highlights_max": 5},
        required_sections=PAPER_A_SECTIONS,
        required_declarations=["Data availability", "Declarations", "Funding",
                               "Conflict of interest", "Author contribution", "Use of AI"],
        forbidden_strings=["383 experiments", "68 pages", "234 words", "five random seeds"],
        key_numbers={"317": ["paper合/sections"], "221": ["paper合/sections"]},
        commands=PAPER_A_COMMANDS,
        # 2026-10-25: the Springer file is a rendering of the same content, so the frozen package
        # it is declared against is the Neurocomputing submission of record (Paper A).
        package="SUBMISSION/PaperA_Neurocomputing",
        package_expected=["Manuscript.pdf", "Cover Letter.pdf", "Highlights.pdf",
                          "Highlights.txt", "Abstract.pdf", "latex_source.zip", "README.md"],
        package_map=[["Manuscript.pdf", "main_nc.pdf"]],
        package_frozen=True,
        freeze_paths=["SUBMISSION/PaperA_Neurocomputing"],
        build_command=["python", "tools/_p1174_build_paperA_editorial.py", "--apply"],
        notes=("Springer template variant of Paper A; not the submission of record. Its frozen "
               "reference is the Neurocomputing package SUBMISSION/PaperA_Neurocomputing/ "
               "(same Paper A content), so I-02 reports a named warning, not a failure."),
    ),
    "p3_prl": _p(
        "p3_prl", "Paper 3 - Pattern Recognition Letters (IEEEtran)",
        manuscript="paper3/paper_ieee",
        tex=["main.tex", "main_10pp.tex", "main_full.tex"],
        pdfs=["main.pdf", "main_10pp.pdf", "main_full.pdf", "supplementary/supplementary.pdf"],
        logs=["main.log", "main_10pp.log", "main_full.log", "supplementary/supplementary.log"],
        supplementary="supplementary/supplementary.pdf",
        limits={"pages_max": 10, "abstract_words_max": 250, "keywords_min": 1,
                "keywords_max": 6},
        required_sections=["Introduction", "Related", "Theory", "Experiments", "Conclusion"],
        required_declarations=[],
        forbidden_strings=["⟨abla", "ablaM"],
        commands=[
            {"name": "P3 audit_check", "cmd": ["python", "paper3/paper_ieee/audit_check.py"],
             "expect": "PASS", "kind": "gate"},
            {"name": "P3 audit_pdf", "cmd": ["python", "paper3/paper_ieee/audit_pdf.py"],
             "expect": "PASS", "kind": "gate"},
        ],
        build_command=["pdflatex", "-interaction=nonstopmode", "main.tex"],
        # D-8 fix (2026-10-25): the submitted P3 package is declared explicitly as FROZEN so the
        # gate can tell "deliberately frozen and diverged" apart from "package forgotten/stale".
        # Frozen snapshot 2026-10-21: Manuscript 10 pp, Supplement 8 pp (S1--S17); the live draft
        # is 10 pp + 26 pp supplement (S1--S46) and keeps moving. Do not modify the package.
        package="SUBMISSION/P3_PRL_resubmission",
        package_expected=["Manuscript.pdf", "Supplementary.pdf", "TitlePage.pdf",
                          "Highlights.pdf", "AuthorshipConfirmation.pdf", "CoverLetter.pdf",
                          "EM_FIELDS.md", "LaTeXSource.zip", "README.md"],
        package_map=[["Manuscript.pdf", "main.pdf"],
                     ["Supplementary.pdf", "supplementary/supplementary.pdf"]],
        package_frozen=True,
        freeze_paths=["SUBMISSION/_archive/P3_PRL_rejected_2026-10-21/CORRECTED_2026-10-15",
                      "SUBMISSION/_archive/P3_PRL_rejected_2026-10-21/UPLOAD_2026-10-15",
                      "SUBMISSION/P3_PRL_resubmission"],
        notes=("Under review (PRLETTERS-D-26-02378R1). The submitted package "
               "SUBMISSION/P3_PRL_resubmission/ is FROZEN at the 2026-10-21 snapshot (10 pp main, "
               "8 pp supplement = S1--S17) and must not change; the local draft is being revised "
               "for the next revision (10 pp + 26 pp supplement = S1--S46)."),
    ),
    "a1_nn": _p(
        "a1_nn", "A1 - Neural Networks (elsarticle review)",
        manuscript="paper_a1",
        tex=["main.tex"],
        pdfs=["main.pdf", "cover_letter.pdf", "declaration.pdf", "highlights.pdf", "abstract.pdf"],
        logs=["main.log", "cover_letter.log", "declaration.log", "highlights.log",
              "abstract.log"],
        package="SUBMISSION/_archive/A1_NeuralNetworks_rejected_2026-10-18",
        package_expected=["main.pdf", "cover_letter.pdf", "declaration.pdf",
                          "highlights.pdf", "abstract.pdf"],
        package_map=[["main.pdf", "main.pdf"], ["cover_letter.pdf", "cover_letter.pdf"],
                     ["declaration.pdf", "declaration.pdf"],
                     ["highlights.pdf", "highlights.pdf"], ["abstract.pdf", "abstract.pdf"]],
        cover_letter="cover_letter.tex",
        highlights="highlights.tex",
        limits={"abstract_words_max": 250, "keywords_min": 1, "keywords_max": 6,
                "highlights_min": 3, "highlights_max": 5,
                "required_declarations_optional": True},
        required_sections=["Introduction", "Method", "Results", "Conclusion"],
        required_declarations=[],   # historical profile: the NN submission was desk-rejected 2026-10-18
        forbidden_strings=["10 October 2026", "under review at Pattern Recognition",
                           "Manuscript under review."],
        commands=[],
        build_command=["pdflatex", "-interaction=nonstopmode", "main.tex"],
        package_frozen=True,
        freeze_paths=["SUBMISSION/_archive/A1_NeuralNetworks_rejected_2026-10-18"],
        notes="Desk-rejected 2026-10-18 (NEUNET-D-26-09426); working copy carries revision fixes.",
    ),
    "a1_paa": _p(
        "a1_paa", "A1 - Pattern Analysis and Applications (Springer)",
        manuscript="paper_a1",
        tex=["main.tex", "title_page.tex"],
        pdfs=["main.pdf", "title_page.pdf"],
        logs=["main.log", "title_page.log"],
        limits={"abstract_words_min": 150, "abstract_words_max": 250,
                "keywords_min": 4, "keywords_max": 6},
        required_sections=["Introduction", "Setup", "Results", "Discussion", "Conclusion"],
        required_declarations=["Funding", "Competing interests", "Ethics approval",
                               "Consent for publication", "Data and code availability",
                               "Authors' contributions", "Use of artificial-intelligence tools"],
        forbidden_strings=["under review at Pattern Recognition", "Manuscript under review."],
        commands=[],
        package="SUBMISSION/A1_PatternAnalysisApplications",
        package_expected=["Manuscript.pdf", "Title Page.pdf", "Cover Letter.pdf",
                          "latex_source.zip", "README.md"],
        package_map=[["Manuscript.pdf", "main.pdf"], ["Title Page.pdf", "title_page.pdf"],
                     ["Cover Letter.pdf", "cover_letter_paa.pdf"]],
        cover_letter="cover_letter_paa.tex",
        build_command=["pdflatex", "-interaction=nonstopmode", "main.tex"],
        # 2026-10-25: submitted to PAA on 2026-10-18; the submitted package is frozen while the
        # live draft carries revision fixes (I-02 = named warning, I-04 = integrity check).
        package_frozen=True,
        freeze_paths=["SUBMISSION/_archive/A1_NeuralNetworks_rejected_2026-10-18",
                      "SUBMISSION/A1_PatternAnalysisApplications"],
        notes=("Submitted to Pattern Analysis and Applications (SCIE) on 2026-10-18; the package "
               "SUBMISSION/A1_PatternAnalysisApplications/ is FROZEN at that snapshot while the "
               "live draft carries the revision fixes. The Neural Networks package under "
               "SUBMISSION/ also stays frozen."),
    ),

    "a23_joe": _p(
        "a23_joe", "A23 - IEEE Journal of Oceanic Engineering (IEEEtran)",
        manuscript="paper_a2",
        tex=["main_ieee.tex"],
        pdfs=["main_ieee.pdf", "cover_letter.pdf", "abstract.pdf"],
        logs=["main_ieee.log", "cover_letter.log", "abstract.log"],
        cover_letter="cover_letter.tex",
        limits={"abstract_words_max": 250, "abstract_words_min": 150,
                "keywords_min": 3, "keywords_max": 5},
        required_sections=["Introduction", "Method", "Results", "Conclusion"],
        required_declarations=["Data availability", "Funding",
                               "Declaration of competing interest", "CRediT"],
        forbidden_strings=["a critical review of parameter-efficient adaptation", "\\journal{Ocean Engineering}"],
        commands=[
            {"name": "A23 fix verification", "cmd": ["python", "paper_a2/verify_a23_fix.py"],
             "expect": "ALL CHECKS PASSED", "kind": "gate"},
        ],
        build_command=["pdflatex", "-interaction=nonstopmode", "main_ieee.tex"],
        # 2026-10-25: aligned with the other frozen profiles -- explicit package path, expected
        # portal items, package-to-live map and package_frozen, so I-02 reports a NAMED warning
        # (package + snapshot + per-file divergence, pointing at I-04) instead of a bare skip.
        package="SUBMISSION/A23_JOE",
        package_expected=["A23_latex_source.zip", "abstract_plaintext.txt", "README.md",
                          "current/main_ieee.pdf", "current/cover_letter.pdf",
                          "current/abstract.pdf"],
        package_map=[["current/main_ieee.pdf", "main_ieee.pdf"],
                     ["current/cover_letter.pdf", "cover_letter.pdf"],
                     ["current/abstract.pdf", "abstract.pdf"]],
        package_frozen=True,
        freeze_paths=["SUBMISSION/A23_JOE"],
        notes=("Under review (IEEE JOE 26-0663); the package SUBMISSION/A23_JOE/ is FROZEN at "
               "the submitted snapshot (64 pp main) while the working copy carries the revision "
               "(73 pp), so I-02 is a named warning and I-04 covers package integrity."),
    ),
    "prl_commentary": _p(
        "prl_commentary", "PRL Commentary - Pattern Recognition Letters (cas-dc)",
        manuscript="paper_review_prl",
        tex=["main_prl.tex"],
        pdfs=["main_prl.pdf", "cover_letter.pdf", "highlights.pdf"],
        logs=["main_prl.log", "cover_letter.log", "highlights.log"],
        cover_letter="cover_letter.tex",
        limits={"pages_max": 7, "abstract_words_max": 250, "keywords_min": 5,
                "keywords_max": 7},
        required_sections=["Introduction", "Conclusions"],
        required_declarations=["Declarations", "Funding", "Data availability",
                               "Declaration of generative AI"],
        forbidden_strings=["a critical review of parameter-efficient adaptation",
                           "<scp>", "&amp;", "ORCID(s)"],
        commands=[
            {"name": "PRL final check", "cmd": ["python", "tools/_final_check_prl.py"],
             "expect": "全部通过", "kind": "gate"},
        ],
        build_command=["python", "tools/_build_prl_tex.py"],
        # 2026-10-25: the submitted Commentary package is FROZEN (under review); I-02 reports a
        # named warning instead of comparing it with the revised live draft.
        package="SUBMISSION/Review_PRL",
        package_expected=["main_prl.pdf", "cover_letter.pdf", "highlights.pdf"],
        package_map=[["main_prl.pdf", "main_prl.pdf"],
                     ["cover_letter.pdf", "cover_letter.pdf"],
                     ["highlights.pdf", "highlights.pdf"]],
        package_frozen=True,
        freeze_paths=["paper_review_prl/UPLOAD", "SUBMISSION/Review_PRL"],
        notes=("Under review (PRLETTERS-D-26-02402); the package SUBMISSION/Review_PRL/ is "
               "frozen at the submitted snapshot while the working copy carries revision fixes."),
    ),
}

# Generic templates: useful before a target journal is fixed.
for _pid, _label, _style in [
    ("generic_elsevier", "Generic Elsevier manuscript (elsarticle)", "env"),
    ("generic_ieee", "Generic IEEE manuscript (IEEEtran)", "env"),
    ("generic_prl", "Generic Pattern Recognition Letters manuscript (cas-dc)", "env"),
]:
    PROFILES[_pid] = _p(
        _pid, _label, manuscript=".", abstract_style=_style,
        limits={"abstract_words_max": 250, "keywords_min": 1, "keywords_max": 8},
        commands=[],
        notes="Template profile: copy this entry in profiles.py and fill manuscript/tex/pdfs/logs before use.",
    )


def get_profile(pid: str) -> dict:
    if pid not in PROFILES:
        raise KeyError("unknown profile %r; known: %s" % (pid, ", ".join(sorted(PROFILES))))
    return deepcopy(PROFILES[pid])
