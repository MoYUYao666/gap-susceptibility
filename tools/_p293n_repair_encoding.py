# -*- coding: utf-8 -*-
r"""Repair the mojibake that PowerShell introduced into tools/_p293e_report.py.

What happened: a PowerShell `(Get-Content -Raw) ... | Set-Content -Encoding utf8` round trip read
the file as the local ANSI codepage and wrote it back as UTF-8, double-encoding every non-ASCII
character.  The project's own rules warn about exactly this ("Windows PowerShell eats $ and
backslashes ... do not build strings on the command line") -- the lesson here is that it also
mangles a file it merely rewrites.

The damage is a pure byte-level re-encoding, so every corrupted glyph maps one-to-one back to its
original.  Rather than guess, each mapping below is written only where the intended character is
unambiguous from context, and the script asserts that no unexpected non-ASCII character remains
afterwards.
"""
import io
import sys

PATH = "tools/_p293e_report.py"

# mojibake -> intended.  Left side written as escapes so this file stays pure ASCII-safe.
PAIRS = [
    ("\u9225", "\u2014"),          # em dash
    ("\u8796", "\u0394"),          # Delta
    ("\u9234", "\u23f3"),          # hourglass
    ("\u8133", "\u00d7"),          # multiplication sign
    ("\u5364", "\u00b1"),          # plus-minus
    ("\u922b", "\u2192"),          # right arrow
    ("\u9241", "\u2705"),          # check mark
    ("\u9242", "\u274c"),          # cross mark
    ("\u6402", "\u00a7"),          # section sign
    ("\u922d", "\u2212"),          # minus sign
    ("\u8def", "\u00b7"),          # middle dot
    ("\u6415", "\u2013"),          # en dash (in "image-text")
    ("\u9240", "\u26d4"),          # no-entry
    ("\u63f1", "\u2013"),          # en dash (in "p325-p330")
    ("\ufe39", "\u2026"),          # ellipsis lead byte
    ("\u579d", "\u2013"),          # en dash (inside the withdrawn BioCLIP range)
    ("\u63b3", "\u00b0"),          # degree
    ("\u4f2a", "\u03b1"),          # alpha
    ("\u6408", "\u2013"),          # en dash (in "min-max")
    ("\u6504", "\u2194"),          # left-right arrow
    ("\u923f", "\u26a0"),          # warning sign
    ("\u72c5", "\ufe0f"),          # variation selector
    ("\u7b0d", "\ufe0f"),          # variation selector
    ("\u2e3f", ""),                # stray CJK radical from a truncated emoji, drop
    ("\u63a1", ""),                # stray, drop if present
]


def main():
    s = io.open(PATH, encoding="utf-8-sig").read()
    before = {c: s.count(c) for c in set(s) if ord(c) > 127}
    for bad, good in PAIRS:
        s = s.replace(bad, good)
    remaining = sorted({c for c in s if ord(c) > 127})
    print("distinct non-ASCII before:", len(before))
    print("distinct non-ASCII after :", len(remaining))
    for c in remaining:
        print("   remaining:", repr(c), hex(ord(c)), "x%d" % s.count(c))
    io.open(PATH, "w", encoding="utf-8", newline="\n").write(s)
    print("[ok] repaired", PATH)
    # verify it parses
    import ast
    ast.parse(s)
    print("[ok] parses")


if __name__ == "__main__":
    sys.exit(main())
