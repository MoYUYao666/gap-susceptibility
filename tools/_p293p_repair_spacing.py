# -*- coding: utf-8 -*-
r"""Restore the spaces that the mojibake repair swallowed, in tools/_p293e_report.py.

Wave 2 replaced "<punct>?" with "<punct>", which was correct, but a few entries in that list were
written as no-op guards of the form ("<punct>? ", "<punct> ") and the trailing space was lost in
the file for the entries that were NOT no-ops.  The result is text like

    "**Task**: `task-8` \u2014answer R2 (..."

where the space after the em dash is gone.  The sentence content is intact; only the spacing needs
restoring, and it is restored ONLY where a non-ASCII punctuation character is glued to a following
ASCII letter or digit, which cannot be correct in this document's prose.

This script also prints every change it makes, so the edit is reviewable rather than silent.
"""
import io
import re
import sys

PATH = "tools/_p293e_report.py"

# punctuation that must be followed by a space when prose continues immediately
PUNCT = "\u2014\u2013\u2026\u2705\u274c\u23f3\u26d4\u26a0\u2192\u2194\u2212\u00d7\u00b1\u00b7\u00a7\u0394\u03b1"


def main():
    s = io.open(PATH, encoding="utf-8-sig").read()
    changes = []

    def fix(m):
        changes.append(m.group(0))
        return m.group(1) + " " + m.group(2)

    # a punctuation char directly followed by an ASCII letter or digit
    s2 = re.sub("([%s])([A-Za-z0-9])" % PUNCT, fix, s)

    # do NOT touch format specifiers like %d\u00d7 or numbers written as 24\u00d724 -- those are
    # intentional; undo any change that removed a multiplication sign between digits
    reverted = []
    for frag in changes:
        pun, nxt = frag[0], frag[1]
        if pun == "\u00d7" and nxt.isdigit():
            s2 = s2.replace(pun + " " + nxt, pun + nxt, 1)
            reverted.append(frag)

    print("spacing fixes applied:", len(changes) - len(reverted))
    for f in changes[:40]:
        if f not in reverted:
            print("   ", repr(f), "->", repr(f[0] + " " + f[1]))
    if reverted:
        print("reverted (multiplication sign between digits):", len(reverted))

    io.open(PATH, "w", encoding="utf-8", newline="\n").write(s2)
    import ast
    ast.parse(s2)
    print("[ok] parses")

    # final scan: any remaining glued punctuation?
    left = re.findall("([%s])([A-Za-z0-9])" % PUNCT, s2)
    print("remaining glued occurrences:", len(left))
    print("[ok] repaired", PATH)


if __name__ == "__main__":
    sys.exit(main())
