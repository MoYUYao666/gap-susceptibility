# -*- coding: utf-8 -*-
r"""Fix the two 'Anon.' bibliography entries found during the A1 audit's manual reference review.

A1 keeps a manual thebibliography; two of its 56 items carry the placeholder label "Anon." instead of the author-year
label natbib renders, so the PDF cites them as "(Anon., 2026)". The correct metadata is in paper合/references.bib:

  hu2021lora    Hu, Edward J.; Shen, Yelong; Wallis, Phillip; Allen-Zhu, Zeyuan; Li, Yuanzhi; Wang, Shean; Wang, Lu;
                Chen, Weizhu. LoRA. ICLR 2022.
  zhang2026imod Zhang, Mingfang; Wang, Yunhong; Wang, Lu; Chen, Jiaxin. CVPR 2026, pp. 37745-37755.

    python tools/_p1228_fix_a1_anon_bibitems.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAIN = os.path.join(REPO, "paper_a1", "main.tex")

PAIRS = [
    (r"\bibitem[Anon., 2021]{hu2022lora} LoRA: Low-rank adaptation of large language models. ICLR 2022.",
     r"\bibitem[Hu et al., 2022]{hu2022lora} Hu, E.~J., Shen, Y., Wallis, P., Allen-Zhu, Z., Li, Y., Wang, S., "
     r"Wang, L., Chen, W. LoRA: Low-rank adaptation of large language models. ICLR 2022."),
    (r"\bibitem[Anon., 2026]{imod} Parameter-efficient adaptation for MLLMs via implicit modality decomposition. CVPR 2026.",
     r"\bibitem[Zhang et al., 2026]{imod} Zhang, M., Wang, Y., Wang, L., Chen, J. Parameter-efficient adaptation for "
     r"MLLMs via implicit modality decomposition. CVPR 2026."),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(MAIN, encoding="utf-8").read()
    for old, new in PAIRS:
        n = t.count(old)
        print(f"  {old[:38]!r}... occurrences {n}")
        if n != 1:
            print("  !! not found verbatim; aborting")
            return 1
        t = t.replace(old, new, 1)
    left = t.count("[Anon.")
    print(f"  remaining '[Anon.' labels: {left}")
    if left:
        return 1
    if not a.apply:
        print("  (dry run)")
        return 0
    io.open(MAIN, "w", encoding="utf-8", newline="").write(t)
    print("  written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
