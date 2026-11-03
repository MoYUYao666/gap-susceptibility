# -*- coding: utf-8 -*-
"""Full content audit: cross-checks every new section's numbers against archives and flags stale wording."""
import glob
import glob as _g  # noqa: F401
import io
import json
import os
import re

from pypdf import PdfReader

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SUPP = os.path.join(REPO, "paper3", "paper_ieee", "supplementary", "supplementary.tex")
MAIN = os.path.join(REPO, "paper3", "paper_ieee", "main.pdf")
AN = os.path.join(REPO, "outputs", "analysis")
EXP = os.path.join(REPO, "paper3", "scripts", "outputs", "experiments")
PKG = os.path.join(REPO, "SUBMISSION", "P3_PRL_next_revision")

problems = []
t = io.open(SUPP, encoding="utf-8").read()


def check(cond, msg):
    print(("PASS " if cond else "FAIL ") + msg)
    if not cond:
        problems.append(msg)


def jl(p):
    return json.load(io.open(p, encoding="utf-8"))


def window(label, before=9000, after=2500):
    i = t.find("\\label{" + label + "}")
    return t[max(0, i - before): i + after]


# structure
check(len(PdfReader(MAIN).pages) == 10, "main PDF 10 pages")
check(len(PdfReader(os.path.join(REPO, "paper3", "paper_ieee", "supplementary", "supplementary.pdf")).pages) == 17,
      "supplement PDF 17 pages")
check(len(re.findall(r"\\section\{", t)) == 43, "43 sections")
check(t.count("\\begin{table*}") == t.count("\\end{table*}"), "table* balanced")
check(t.count("\\end{document}") == 1, "single document end")
check(not re.search(r"[\u4e00-\u9fff]", t), "no CJK")
check("TODO" not in t and "TBD" not in t, "no TODO/TBD")

# S29 fourth stack
blk = window("app:envcloud")
check("2.6.0+cu124" in blk and "-35.5" in blk and "+42.0" in blk, "S29 fourth stack values")
check("four software/hardware environments" in blk, "S29 says four environments")

# S37 numbers
ev = jl(os.path.join(AN, "p3_env_variance.json"))
blk = window("app:envvar")
check(("%.1f" % ev["sigma_env"]) in blk and ("%.1f" % ev["sigma_seed"]) in blk, "S37 sigma values")
check(("%.0f" % (100 * ev["env_share"])) in blk, "S37 share")
check(("%.0f" % (100 * ev["bootstrap"]["share_ci95"][0])) in blk, "S37 CI low")

# S43 Qwen per-layer
q = jl(os.path.join(AN, "p3_qwen_perlayer_summary.json"))
blk = window("app:qwenlayer")
check(("%.1f" % (100 * q["share"]["llm_00"])) in blk, "S43 layer-0 share")
check(("%.1f" % (100 * q["first4_share"])) in blk, "S43 first-four share")

# S44 SmolVLM
sm = [jl(f) for f in sorted(glob.glob(os.path.join(AN, "p3_smolvlm_family_s*.json")))]
blk = window("app:smolvlm")
for d in sm:
    for r in ("r5", "r6"):
        check(("%+.1f" % d["runs"][r]["delta_E"]) in blk, "S44 %s seed %s" % (r, d["meta"]["seed"]))
check(all(d["runs"]["r5"]["delta_E"] < 0 < d["runs"]["r6"]["delta_E"] for d in sm), "S44 sign change in every seed")

# S33 permutation sentence
blk = window("app:crossing10")
check("1.08" in blk, "S33 r3-vs-r8 permutation p present")

# S17 claims: stale wording absent, new rows present
blk = t[t.find("\\label{app:claims}"):][:14000]
for stale in ("untested & assumed", "local observation", "not established", "S41) it keeps the claim bounded"):
    check(stale not in blk, "S17 no stale phrase: %s" % stale)
for need in ("SmolVLM", "Dolly-15k", "45\\%", "S29, S37"):
    check(need in blk, "S17 row present: %s" % need)

# docs counts
status = io.open(os.path.join(REPO, "docs", "P3_SUBMISSION_STATUS.md"), encoding="utf-8").read()
check("S1–S43" in status or "S1--S43" in status, "status doc S1-S43")
h = io.open(os.path.join(REPO, "HANDOFF.md"), encoding="utf-8").read()
check("S1–S43" in h, "handoff latest count S1-S43")
for doc in ("docs/P3_REMAINING_GAPS_2026-10-22.md", "docs/P3_RESUBMISSION_AUDIT_2026-10-21.md"):
    txt = io.open(os.path.join(REPO, doc), encoding="utf-8").read()
    check("PRLETTERS-D-26-02671" in txt, "%s records submission id" % doc)

# response letter covers 33 ids
rev = jl(os.path.join(REPO, "SUBMISSION", "_archive", "P3_PRL_rejected_2026-10-21", "evidence",
                      "p3_reviews_structured.json"))
ids = sorted(set(re.findall(r"R[123]\.\d+", json.dumps(rev))))
letter = io.open(os.path.join(REPO, "docs", "P3_RESPONSE_LETTER.md"), encoding="utf-8").read()
check(len(ids) == 33 and all(i in letter for i in ids), "33/33 revision ids in response letter")

# package checks
files = sorted(os.listdir(PKG))
check(files == sorted(["AuthorshipConfirmation.pdf", "EMFIELDS.md", "Highlights.pdf", "LaTeXSource.zip",
                       "Manuscript.pdf", "README.md", "SHA256SUMS.txt", "Supplementary.pdf", "TitlePage.pdf"]),
      "package file set")
check(not any("_" in f for f in files), "package filenames without underscores")
check(len(PdfReader(os.path.join(PKG, "Manuscript.pdf")).pages) == 10, "package manuscript 10 pages")
check(len(PdfReader(os.path.join(PKG, "Supplementary.pdf")).pages) == 17, "package supplement 17 pages")
import hashlib
ok = True
for line in io.open(os.path.join(PKG, "SHA256SUMS.txt"), encoding="utf-8"):
    hsh, f = line.strip().split("  ", 1)
    if hashlib.sha256(io.open(os.path.join(PKG, f), "rb").read()).hexdigest() != hsh:
        ok = False
check(ok, "package checksums")

print("\nPROBLEMS:", problems if problems else "none")
raise SystemExit(1 if problems else 0)
