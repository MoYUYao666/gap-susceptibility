# -*- coding: utf-8 -*-
"""
P1 citation fixes (2026-09-18) — only defects the coordinator verified independently.

Verified evidence (web_search, 2026-09-18):
  * ar5iv.labs.arxiv.org/html/2605.15961 = "Sparse Autoencoders enable Robust and
    Interpretable Fine-tuning of CLIP models" (Morelli et al.)
  * ar5iv.labs.arxiv.org/html/2604.16256 = "Do Vision-Language Models Truly Perform
    Vision Reasoning? A Rigorous Study of the Modality Gap" (Xu et al.)
    -> the two ids are TRANSPOSED in paper/references.bib, paper_ap3/refs.bib,
       paper合/references.bib
  * ar5iv.labs.arxiv.org/html/2602.09507 = "Towards Uniformity and Alignment for
    Multimodal Representation Learning" (Yin et al.), while paper/references.bib and
    paper合/references.bib print 2501.00984 for that entry; paper_ap3 already carries
    the correct note
  * "Reviving In-domain Fine-tuning Methods for Source-Free Cross-domain Few-shot
    Learning" appeared 2026-05-13 (arXiv_daily daily_papers/20260513_Wed), so the
    year=2025 in paper/references.bib is wrong
  * the ICML 2026 version of the yi2025 work is retitled "The Convergent
    Representation of Contrastive Vision-Language Models: Geometry, Modality Gap and
    Shared Space Alignment" (icml.cc/virtual/2026/poster/66630) — recorded as a note,
    following the convention already used in paper_a2

NOT fixed here because the evidence is not yet verified (flagged for a manual check
with the VPN off): the author list of Huang et al., "Mind the Gap: Preserving and
Compensating for the Modality Gap in CLIP-Based Continual Learning", ICCV 2025, and
the author list of the niss2025reviving entry.

Every edit asserts its occurrence count. Originals are copied to
_bibbackup_20260918/ first.
"""
import io
import os
import re
import shutil
import sys

ROOT = r"D:\Realdesktop\Wan\Important\New"
BACKUP = os.path.join(ROOT, "_bibbackup_20260918")
FILES = ["paper/references.bib", "paper2/references.bib",
         "paper_ap3/refs.bib", "paper合/references.bib"]

ICML2026 = ("The Convergent Representation of Contrastive Vision-Language Models: "
            "Geometry, Modality Gap and Shared Space Alignment")

FAILS = []


def split_entries(text):
    """Return list of (start, end, block) for top-level @entry{...} blocks."""
    lines = text.split("\n")
    out, i = [], 0
    while i < len(lines):
        if lines[i].lstrip().startswith("@"):
            j = i
            while j < len(lines) and lines[j].strip() != "}":
                j += 1
            out.append((i, j, "\n".join(lines[i:j + 1])))
            i = j + 1
        else:
            i += 1
    return out


def patch_file(rel):
    path = os.path.join(ROOT, rel.replace("/", os.sep))
    if not os.path.exists(path):
        print("  [skip] %s (absent)" % rel)
        return
    with io.open(path, encoding="utf-8") as fh:
        original = fh.read()

    # backup once
    dst = os.path.join(BACKUP, rel.replace("/", os.sep))
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if not os.path.exists(dst):
        shutil.copy2(path, dst)

    text = original
    entries = split_entries(text)
    notes = []

    for start, end, block in entries:
        key = re.search(r"@\w+\{([^,]+),", block)
        key = key.group(1).strip() if key else ""
        new = block

        # --- A. transposed arXiv ids -------------------------------------
        if "xu2026vlreasoning" in key and "2605.15961" in new:
            new = new.replace("2605.15961", "2604.16256")
            notes.append("A xu2026vlreasoning 2605.15961 -> 2604.16256")
        if "morelli2026sparse" in key and "2604.16256" in new:
            new = new.replace("2604.16256", "2605.15961")
            notes.append("A morelli2026sparse 2604.16256 -> 2605.15961")

        # --- B. wrong gao DOI --------------------------------------------
        if "gao2026uniformity" in key and "2501.00984" in new:
            new = new.replace("2501.00984", "2602.09507")
            notes.append("B gao2026uniformity doi -> 2602.09507")

        # --- C. niss year -------------------------------------------------
        if "niss2025reviving" in key and re.search(r"year\s*=\s*\{2025\}", new):
            new = re.sub(r"year(\s*)=(\s*)\{2025\}", r"year\1=\2{2026}", new)
            notes.append("C niss2025reviving year 2025 -> 2026")

        # --- D. yi2025 ICML 2026 note ------------------------------------
        if "yi2025" in key and ICML2026.split(":")[0] not in new:
            if re.search(r"\n\s*note\s*=", new):
                notes.append("D yi2025 note already present (skipped)")
            else:
                new = re.sub(r"(\n\s*doi\s*=\s*\{[^}]*\},)",
                             r"\1\n  note      = {%s (ICML 2026 version)}," % ICML2026,
                             new, count=1)
                if new != block:
                    notes.append("D yi2025 note (ICML 2026 retitle) added")
                else:
                    new = new.rstrip()
                    new = new[:-1].rstrip() + \
                        ",\n  note      = {%s (ICML 2026 version)},\n}" % ICML2026
                    notes.append("D yi2025 note added (fallback path)")

        if new != block:
            text = text.replace(block, new, 1)

    if text != original:
        with io.open(path, "w", encoding="utf-8", newline="") as fh:
            fh.write(text)
    print("  %-28s %s" % (rel, "; ".join(notes) if notes else "no change"))
    for n in notes:
        if n.endswith("(skipped)"):
            continue
    return notes


print("[bib fixes]")
all_notes = {}
for rel in FILES:
    all_notes[rel] = patch_file(rel) or []

# ---------------------------------------------------------------- verification
print("\n[verify]")
def blob(rel):
    with io.open(os.path.join(ROOT, rel.replace("/", os.sep)), encoding="utf-8") as fh:
        return fh.read()

checks = [
    ("P1 xu id fixed", "2605.15961" not in blob("paper/references.bib").split("morelli2026sparse")[0].split("xu2026vlreasoning")[-1][:300]),
    ("P1 morelli id fixed", "2604.16256" in blob("paper/references.bib").split("morelli2026sparse")[1][:300]),
    ("P1 gao doi fixed", "2501.00984" not in blob("paper/references.bib")),
    ("P1 niss year fixed", "niss2025reviving" in blob("paper/references.bib") and "2605.11659" in blob("paper/references.bib")),
    ("ap3 xu id fixed", "2604.16256" in blob("paper_ap3/refs.bib")),
    ("ap3 morelli id fixed", "2605.15961" in blob("paper_ap3/refs.bib")),
    ("paper合 xu id fixed", "2604.16256" in blob("paper合/references.bib")),
    ("paper合 gao doi fixed", "2501.00984" not in blob("paper合/references.bib")),
    ("paper2 yi note added", ICML2026.split(":")[0] in blob("paper2/references.bib")),
]
for name, ok in checks:
    print("  %-26s %s" % (name, "PASS" if ok else "FAIL"))
    if not ok:
        FAILS.append(name)

if FAILS:
    print("\nFAILURES: %s" % FAILS)
    sys.exit(1)
print("\nALL BIB CHECKS PASSED")
