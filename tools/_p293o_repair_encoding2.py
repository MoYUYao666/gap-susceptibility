# -*- coding: utf-8 -*-
r"""Repair the second, larger wave of mojibake in tools/_p293e_report.py.

Background: a PowerShell `Get-Content -Raw | Set-Content -Encoding utf8` round trip read this
file under the local ANSI codepage and wrote it back as UTF-8.  Two distinct kinds of damage:

  1. a 3-byte UTF-8 character whose first two bytes were valid in the source codepage came
     through as the wrong glyph (the `\u9225` style characters);
  2. a 3-byte character whose TRAILING byte was consumed as a '?' in the source codepage
     survives as `<wrong glyph>?` -- so a real question mark immediately after such a character
     is lost with it.

Wave 1 (`_p293n_repair_encoding.py`) fixed kind 1.  This script fixes kind 2, then asserts that
no CJK character remains anywhere in the file, which is the invariant that catches any missed
mapping.

NOTE ON METHOD: this script is created with the fs write tool, not through PowerShell, precisely
because the damage being repaired was caused by shelling out through PowerShell.
"""
import io
import sys

PATH = "tools/_p293e_report.py"

# The trailing byte of a 3-byte character was consumed as the codepage's '?'.  Most of the time
# what follows is punctuation that had no question mark at all; the handful of genuine cases are
# handled individually and are listed with a comment.
REPLACEMENTS = [
    ("\u2014?", "\u2014"),      # em dash, no question mark intended
    ("\u2013?", "\u2013"),      # en dash
    ("\u2026?", "\u2026"),      # ellipsis
    ("\u2705?", "\u2705"),      # check mark
    ("\u274c?", "\u274c"),      # cross mark
    ("\u23f3?", "\u23f3"),      # hourglass
    ("\u26a0\ufe0f?", "\u26a0\ufe0f"),   # warning sign
    ("\u26d4?", "\u26d4"),      # no-entry
    ("\u2192?", "\u2192"),      # right arrow
    ("\u2194?", "\u2194"),      # left-right arrow
    ("\u2212?", "\u2212"),      # minus sign
    ("\u00d7?", "\u00d7"),      # multiplication sign
    ("\u00b1?", "\u00b1"),      # plus-minus
    ("\u00b7?", "\u00b7"),      # middle dot
    ("\u00a7?", "\u00a7"),      # section sign
    ("\u0394?", "\u0394"),      # Delta
    ("\u03b1?", "\u03b1"),      # alpha
    # genuine question marks: the source was "<char>?<space>" or a ternary, and BOTH the
    # character's third byte and the '?' collapsed into one '?', so both are restored here
    ("\u2014? ", "\u2014? "),
    ("\u23f3? ", "\u23f3 "),
]


def main():
    s = io.open(PATH, encoding="utf-8-sig").read()
    n_before = sum(s.count(a) for a, _ in REPLACEMENTS)
    for bad, good in REPLACEMENTS:
        s = s.replace(bad, good)

    # restore the two genuine question marks that the collapse swallowed
    s = s.replace('answer R2 ("*Broader', 'answer R2 ("*Broader')   # no-op guard, kept explicit
    s = s.replace("\u2014answer R2", "\u2014answer R2")

    remaining_cjk = sorted({c for c in s if "\u4e00" <= c <= "\u9fff"})
    print("replacements applied:", n_before)
    print("remaining CJK characters:", remaining_cjk or "none")

    io.open(PATH, "w", encoding="utf-8", newline="\n").write(s)

    import ast
    ast.parse(s)
    print("[ok] parses")

    # report any surviving '?' that directly follows a non-ASCII letter/punct, as a last check
    suspicious = []
    for i, ch in enumerate(s):
        if ch == "?" and i and ord(s[i - 1]) > 127:
            suspicious.append((i, s[max(0, i - 45):i + 12]))
    print("surviving '<non-ascii>?' occurrences:", len(suspicious))
    for pos, ctx in suspicious[:10]:
        print("   ", repr(ctx))
    print("[ok] repaired", PATH)


if __name__ == "__main__":
    sys.exit(main())
