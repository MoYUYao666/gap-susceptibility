# -*- coding: utf-8 -*-
"""Fix the backbone-count statements in Paper A after the count audit (2026-10-17).

Ground truth from the archives (established by the read-only count audit):
  383 experiments = 221 catalogue runs + 162 ODE fits;
  the 221 catalogue includes 104 strict-freezing runs: CLIP B/32 (45), OpenCLIP (25),
  SigLIP (25), BioCLIP (9);
  CLIP ViT-B/16's 15 later runs are NOT part of the 383.
Hence: the six checkpoints of the 383 are CLIP B/32, CLIP ViT-L/14, OpenCLIP B/32,
SigLIP B/16, BioCLIP B/16 and BLIP-1; the strict-freezing three-arm protocol covers
five checkpoints (three contrastive plus SigLIP and BioCLIP) in seven rank configurations.

Fixes (idempotent, one expected occurrence each; already-applied items are skipped).
Run without --apply for a dry run.  python tools/_p1176_fix_paperA_counts.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PA = REPO / "paper合"
FAILS: list[str] = []


def need(cond: bool, msg: str) -> None:
    if not cond:
        FAILS.append(msg)
        print("FAIL  " + msg)


def abstract_words() -> int:
    tex = io.open(PA / "main_nc.tex", encoding="utf-8").read()
    m = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", tex, re.S)
    need(m is not None, "main_nc.tex: abstract not found")
    if not m:
        return 0
    a = re.sub(r"\$[^$]*\$", " X ", m.group(1))
    a = re.sub(r"\\[a-zA-Z]+\*?", " ", a)
    a = a.replace("{", " ").replace("}", " ")
    return len([w for w in a.split() if any(ch.isalnum() for ch in w)])


def highlights_longest() -> int:
    items = []
    for line in io.open(PA / "highlights_nc.txt", encoding="utf-8").read().splitlines():
        s = line.strip()
        if not s or s.lower() == "highlights":
            continue
        items.append(s.lstrip("-*\u2022 ").strip())
    return max((len(s) for s in items), default=0)


def patched(path: Path, pairs: list[tuple[str, str]]) -> str:
    text = io.open(path, encoding="utf-8").read()
    for old, new in pairs:
        n_old = text.count(old)
        n_new = text.count(new)
        if n_new >= 1 and n_old == 0:
            print("  %s: already applied -> %s" % (path.name, new[:60]))
            continue
        if n_old != 1:
            if n_old == 0:
                print("  %s: already applied or superseded -> %s" % (path.name, old[:60]))
                continue
            need(False, "%s: expected one match for %r, found %d" % (path.name, old[:60], n_old))
            continue
        text = text.replace(old, new)
        print("  %s: %r -> %r" % (path.name, old[:48], new[:48]))
    return text


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    words = abstract_words()
    hl = highlights_longest()
    print("  measured: abstract=%d words, longest highlight=%d chars" % (words, hl))
    need(words <= 250, "abstract %d > 250" % words)
    need(hl <= 85, "highlight %d > 85" % hl)

    pairs_by_file = {}
    pairs_by_file["sections/conclusion.tex"] = [
        ("six backbones (CLIP ViT-B/32, CLIP ViT-B/16, CLIP ViT-L/14, OpenCLIP laion2B, SigLIP, and BLIP-1)",
         "six backbones (CLIP ViT-B/32, CLIP ViT-L/14, OpenCLIP laion2B, SigLIP, BioCLIP, and BLIP-1)"),
    ]
    pairs_by_file["sections/introduction.tex"] = [
        ("across 383 experiments on five architectures", "across 383 experiments over six backbones"),
        ("reverses on one of the three backbones tested", "reverses on SigLIP"),
        ("spanning 383 experiments across two PEFT methods, five architectures, and two datasets",
         "spanning 383 experiments across three PEFT methods, six backbones, and two datasets"),
    ]
    pairs_by_file["sections/empirical.tex"] = [
        ("The complete experiment catalog (383 experiments) is provided in Appendix~A.",
         "The complete experiment catalog (221 runs) is provided in Appendix~A."),
        ("Every row is a five-seed mean at batch $128$,", "Every row is a five-seed mean (BioCLIP: three seeds) at batch $128$,"),
        ("measure the same three arms on seven backbones under a protocol",
         "measure the same three arms on five backbones (seven configurations) under a protocol"),
    ]
    for rel in ("cover_letter_nc.tex", "cover_letter.tex"):
        pairs_by_file[rel] = [
            ("validation across 383 experiments spanning five architectures and three PEFT methods",
             "validation across 383 experiments spanning six backbones and three PEFT methods"),
            ("highlights (five items, longest 59 characters)", "highlights (five items, longest %d characters)" % hl),
        ]
    pairs_by_file["cover_letter_nc.tex"].append(("an abstract of 234 words", "an abstract of %d words" % words))
    pairs_by_file["cover_letter.tex"].append(("an abstract of 234 words", "an abstract of %d words" % words))

    new_texts = {}
    for rel in pairs_by_file:
        new_texts[rel] = patched(PA / rel, pairs_by_file[rel])

    if FAILS:
        print("RESULT: %d failure(s); nothing written" % len(FAILS))
        return 1

    def read(rel: str) -> str:
        return new_texts.get(rel) or io.open(PA / rel, encoding="utf-8").read()

    concl_parts = read("sections/conclusion.tex").split("spanning 317 experiments")
    need(len(concl_parts) == 2, "conclusion: cannot locate the 383 sentence")
    if len(concl_parts) == 2:
        head = concl_parts[1][:220]
        need("CLIP ViT-B/16" not in head, "conclusion: CLIP ViT-B/16 still in the 383 list")
        need("BioCLIP" in head, "conclusion: BioCLIP missing from the 383 list")
    intro = read("sections/introduction.tex")
    need("five architectures" not in intro, "introduction: five architectures still present")
    need("two PEFT methods" not in intro, "introduction: two PEFT methods still present")
    need("reverses on SigLIP" in intro, "introduction: reverses on SigLIP missing")
    empir = read("sections/empirical.tex")
    need("seven backbones" not in empir, "empirical: seven backbones still present")
    need("five backbones (seven configurations)" in empir, "empirical: five-backbone wording missing")
    need("(383 experiments)" not in empir, "empirical: (383 experiments) still present")
    for rel in ("cover_letter_nc.tex", "cover_letter.tex"):
        t = read(rel)
        need("five architectures" not in t, rel + ": five architectures still present")
        need("six backbones and three adaptation methods" in t, rel + ": six-backbone wording missing")
    if FAILS:
        print("RESULT: %d failure(s); nothing written" % len(FAILS))
        return 1

    if a.apply:
        for rel, text in new_texts.items():
            io.open(PA / rel, "w", encoding="utf-8", newline="").write(text)
        print("applied: %d file(s)" % len(new_texts))
    else:
        print("(dry run; pass --apply to write)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
