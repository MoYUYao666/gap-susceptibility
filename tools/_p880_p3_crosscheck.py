# -*- coding: utf-8 -*-
r"""Check that P3's main text and its supplementary material correspond.

The main text ends with a "Supplementary material" pointer that names Supplementary Sections S1--S6,
so the first thing to verify is that those sections exist and are numbered as claimed. Beyond that,
the two documents have to agree on

* section numbers quoted in the main text (S1--S6) versus the supplement's own headings;
* labels and references: a `\ref` whose `\label` lives in the other document cannot resolve, which is
  a real possibility here because the two are compiled separately;
* numbers that appear in both, which is where a split paper usually drifts.

    python tools/_p880_p3_crosscheck.py
"""
from __future__ import annotations

import collections
import io
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
P3 = REPO / "paper3" / "paper_ieee"
MAIN = P3 / "main.tex"
SUPP = P3 / "supplementary" / "supplementary.tex"
SECTIONS = P3 / "sections"


def headings(text: str) -> list[str]:
    return [m.group(1).strip() for m in
            re.finditer(r"\\(?:sub)?section\*?\{([^}]*)\}", text)]


def labels(text: str) -> set[str]:
    return {m.group(1) for m in re.finditer(r"\\label\{([^}]*)\}", text)}


def refs(text: str) -> collections.Counter:
    return collections.Counter(m.group(1) for m in
                              re.finditer(r"\\(?:eq)?ref\{([^}]*)\}", text))


def main() -> int:
    main_t = MAIN.read_text(encoding="utf-8", errors="replace")
    for p in sorted(SECTIONS.glob("*.tex")):
        if ".bak" not in p.name:
            main_t += "\n" + p.read_text(encoding="utf-8", errors="replace")
    supp_t = SUPP.read_text(encoding="utf-8", errors="replace")

    print("=== main text: sections quoted from the supplement ===")
    quoted = sorted(set(re.findall(r"Supplementary Section[s]?~?(S\d+(?:--S\d+)?)", main_t)))
    print(f"  quoted: {quoted}")
    for pat in (r"Supplementary Sections?~?(S\d+--S\d+)", r"Section~?(S\d+)"):
        for m in re.finditer(pat, main_t):
            print(f"    -> {m.group(0)}")

    print()
    print("=== supplement: own headings ===")
    for h in headings(supp_t):
        print(f"  {h}")

    print()
    print("=== label / reference resolution ===")
    main_labels, supp_labels = labels(main_t), labels(supp_t)
    main_refs, supp_refs = refs(main_t), refs(supp_t)
    unresolved_main = sorted(set(main_refs) - main_labels)
    unresolved_supp = sorted(set(supp_refs) - supp_labels)
    print(f"  main labels {len(main_labels)} ｜ main refs {len(main_refs)}")
    print(f"  supplement labels {len(supp_labels)} ｜ supplement refs {len(supp_refs)}")
    print(f"  main refs with no label in main:        {unresolved_main}")
    print(f"  supplement refs with no label in supp:  {unresolved_supp}")
    cross = sorted(set(main_refs) & supp_labels)
    cross2 = sorted(set(supp_refs) & main_labels)
    print(f"  main refers to a supplement label:      {cross}")
    print(f"  supplement refers to a main label:      {cross2}")

    print()
    print("=== numbers quoted in both documents ===")
    num = re.compile(r"\b\d+\.\d{3,}\b")
    m_nums = collections.Counter(num.findall(main_t))
    s_nums = collections.Counter(num.findall(supp_t))
    shared = sorted(set(m_nums) & set(s_nums))
    print(f"  distinct 3+ decimal numbers: main {len(m_nums)} ｜ supplement {len(s_nums)} ｜ shared {len(shared)}")
    print(f"  shared values: {shared[:20]}{' ...' if len(shared) > 20 else ''}")
    only_main = sorted(set(m_nums) - set(s_nums))
    print(f"  only in main (first 20): {only_main[:20]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
