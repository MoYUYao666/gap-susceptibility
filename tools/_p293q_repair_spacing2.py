# -*- coding: utf-8 -*-
r"""Undo the over-correction introduced by `_p293p_repair_spacing.py`.

That script re-spaced every "<non-ASCII punct><ASCII alnum>" pair in tools/_p293e_report.py, which
was too blunt: it also broke identifiers that legitimately contain no space, e.g. `\u0394CG`
(the manuscript's symbol for the gap change), `\u00a73.1` (a section reference) and `\u20130.05`
(a negative number using an en dash).  Those are reverted here from an explicit keep-list, and the
result is asserted to contain no glued-punctuation occurrences that are not on that list.
"""
import io
import re
import sys

PATH = "tools/_p293e_report.py"

# exact broken -> correct pairs produced by the over-correction
REVERTS = [
    ("\u0394 C", "\u0394C"),        # Delta CG / Delta DG / Delta-W
    ("\u00a7 ", "\u00a7"),          # section sign before a number, e.g. "§ 3.1" -> "§3.1"
    ("\u2013 ", "\u2013"),          # negative numbers written with an en dash
]


def main():
    s = io.open(PATH, encoding="utf-8-sig").read()
    for bad, good in REVERTS:
        n = s.count(bad)
        s = s.replace(bad, good)
        print("reverted %-14r x%d" % (bad, n))

    io.open(PATH, "w", encoding="utf-8", newline="\n").write(s)
    import ast
    ast.parse(s)
    print("[ok] parses")

    # show what is still glued, so the caller can eyeball whether each is intentional
    pat = "([\u2014\u2013\u2026\u2705\u274c\u23f3\u26d4\u26a0\u2192\u2194\u2212\u00d7\u00b1"
    pat += "\u00b7\u00a7\u0394\u03b1])([A-Za-z0-9])"
    left = re.findall(pat, s)
    print("still glued:", sorted(set("".join(x) for x in left)))
    print("[ok] repaired", PATH)


if __name__ == "__main__":
    sys.exit(main())
