# -*- coding: utf-8 -*-
"""Key-independent verification of the arXiv-id pairing, by TITLE not by key."""
import io
import os
import re

ROOT = r"D:\Realdesktop\Wan\Important\New"
FILES = ["paper/references.bib", "paper2/references.bib",
         "paper合/references.bib", "paper合/references.bib"]

PAIRS = [
    ("vision reasoning", "2604.16256"),     # title fragment -> correct id
    ("Sparse autoencoders", "2605.15961"),
    ("Uniformity and Alignment", "2602.09507"),
]

fails = []
for rel in FILES:
    path = os.path.join(ROOT, rel.replace("/", os.sep))
    if not os.path.exists(path):
        print("%-26s (absent)" % rel)
        continue
    text = io.open(path, encoding="utf-8").read()
    lines = text.split("\n")
    blocks = []
    i = 0
    while i < len(lines):
        if lines[i].lstrip().startswith("@"):
            j = i
            while j < len(lines) and lines[j].strip() != "}":
                j += 1
            blocks.append("\n".join(lines[i:j + 1]))
            i = j + 1
        else:
            i += 1
    print("%-26s %d entries" % (rel, len(blocks)))
    for frag, want in PAIRS:
        hits = [b for b in blocks if frag.lower() in b.lower()]
        if not hits:
            continue
        for b in hits:
            ids = set(re.findall(r"2[0-9]{3}\.[0-9]{4,5}", b))
            ok = want in ids
            print("    %-22s want %s -> ids %s  %s"
                  % (frag, want, sorted(ids), "OK" if ok else "WRONG"))
            if not ok:
                fails.append("%s :: %s" % (rel, frag))
    # niss year
    for b in blocks:
        if "Reviving In-Domain Fine-Tuning" in b or "Reviving In-domain" in b:
            yr = re.search(r"year\s*=\s*\{(\d{4})\}", b)
            print("    niss year = %s %s" % (yr.group(1) if yr else "?",
                                             "OK" if yr and yr.group(1) == "2026" else "WRONG"))
            if not yr or yr.group(1) != "2026":
                fails.append("%s :: niss year" % rel)
    # yi note
    for b in blocks:
        if "Decipher the Modality Gap" in b:
            has = "Convergent Representation" in b
            print("    yi2025 ICML-2026 note: %s" % ("present" if has else "ABSENT"))

print("\nFAILS: %s" % (fails if fails else "none"))
raise SystemExit(1 if fails else 0)
