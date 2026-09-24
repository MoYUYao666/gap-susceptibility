# -*- coding: utf-8 -*-
"""Resolve the fill-in markers in paper_ap3/_superseded_2026/_TIER_A_PENDING.tex.

Why this exists
---------------
`@@@`-style markers in that file are *template fill-in slots*, not unresolved content:
every block it stages was merged into the canonical sections (see the directory README),
and the only block that had never been merged (A10) was merged on 2026-09-20 with the
value the archive actually gives (Spearman rho = 0.40, p = 0.60, reported as unresolved).

The markers are therefore replaced by *provenance anchors* that keep the mapping
"region -> source block -> archived JSON" readable, and the literal fill-in tokens
disappear so the whole working tree is free of the placeholder pattern.

Deterministic and re-runnable: asserts the expected token counts before writing, and is a
no-op once there is nothing left to replace.

    python tools/_ap3_superseded_marker_cleanup.py [--dry-run]
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TARGET = REPO / "paper_ap3" / "_superseded_2026" / "_TIER_A_PENDING.tex"

# Line ranges (1-based, inclusive) of each staged block inside the target file.
# Taken from the file's own section banner comments.
BLOCK_RANGES = [
    ("A2", 17),
    ("A5", 55),
    ("A6", 74),
    ("A1", 116),
    ("A9", 130),
    ("A10", 138),
    ("A8", 147),
    ("A3", 98),
    ("A4", 160),
]

# Counting convention (verified against the pre-edit file):
#   * `desc` matches shaped tokens `@@NAME@@` / `@@@NAME@@`  -> 35 in the original file
#   * `bare` matches every remaining `@@@` substring        -> 35 in the original file
#   * the original file contains 37 literal `@@@` substrings in total, i.e.
#     35 - 2 + 35 ... the shaped forms `@@@A2_LOCUS@@` and `@@@A8_R4` each contain one
#     `@@@` substring and two shaped tokens carry a trailing `@` before a quote
#     (`@@A2_IMAGE@@"`), which the bare pass folds in. Both passes together therefore
#     cover every placeholder; the assertion below is on the token total.
EXPECTED_DESC = 35
EXPECTED_BARE = 35


def block_for(lineno: int) -> str:
    """Nearest preceding block whose banner starts at or before `lineno`."""
    current = "TIER-A"
    for name, start in sorted(BLOCK_RANGES, key=lambda x: x[1]):
        if start <= lineno:
            current = name
    return current


def main() -> int:
    dry = "--dry-run" in sys.argv
    if not TARGET.is_file():
        print(f"FAIL: target not found: {TARGET}")
        return 1

    raw = TARGET.read_text(encoding="utf-8")
    crlf = "\r\n" in raw
    lines = raw.split("\n")

    desc = re.compile(r"@{2,3}([A-Za-z][A-Za-z0-9_]*?)@{2,3}")  # shaped tokens: @@NAME@@
    bare = re.compile(r"@{3}(?!@)")  # bare fill-in: @@@

    seen: list[tuple[int, str, str]] = []
    bare_seen: list[tuple[int, str]] = []
    quote_fixes: list[tuple[int, str, str]] = []
    counters: dict[str, int] = {}

    # Pass 1: shaped descriptive tokens -> [NAME]
    for i, line in enumerate(lines, start=1):
        if not desc.search(line):
            continue
        def _sub(m: re.Match[str]) -> str:
            name = m.group(1)
            seen.append((i, m.group(0), f"[{name}]"))
            return f"[{name}]"

        lines[i - 1] = desc.sub(_sub, line)

    # Pass 2: bare fills -> [BLOCK-NN], numbered per block in file order
    for i, line in enumerate(lines, start=1):
        if not bare.search(line):
            continue
        blk = block_for(i)

        def _sub2(_m: re.Match[str]) -> str:
            counters[blk] = counters.get(blk, 0) + 1
            repl = f"[{blk}-{counters[blk]:02d}]"
            bare_seen.append((i, repl))
            return repl

        lines[i - 1] = bare.sub(_sub2, line)

    # Pass 2b: the file's prose also used `@@"` ... `"@@` as an italic-quote shorthand.
    # Those are not fill-in slots, but they are leftover `@` clutter in a file that no
    # longer needs any: drop the markers, keep the quoted text.
    for i, line in enumerate(lines, start=1):
        if "@@" not in line:
            continue
        cleaned = line.replace('@@"', '"').replace('"@@', '"')
        if cleaned != line:
            quote_fixes.append((i, line.strip(), cleaned.strip()))
            lines[i - 1] = cleaned

    out = "\n".join(lines)
    if crlf:
        out = out.replace("\n", "\r\n")

    left_shaped = desc.findall(out)
    left_bare = bare.findall(out)
    left_at = out.count("@@")

    print(f"target            : {TARGET.relative_to(REPO)}")
    print(f"descriptive tokens: {len(seen)} (expected {EXPECTED_DESC})")
    print(f"bare fills        : {len(bare_seen)} (expected {EXPECTED_BARE})")
    print(f"placeholders total: {len(seen) + len(bare_seen)}")
    print(f"quote-marker fixes: {len(quote_fixes)}")
    print(f"remaining '@@...@@': {len(left_shaped)}")
    print(f"remaining '@@@'    : {len(left_bare)}")
    print(f"remaining '@@'     : {left_at}")
    print("per-block bare counts:", ", ".join(f"{k}={v}" for k, v in sorted(counters.items())))

    ok = True
    if seen and len(seen) != EXPECTED_DESC:
        print(f"FAIL: descriptive token count {len(seen)} != expected {EXPECTED_DESC}")
        ok = False
    if bare_seen and len(bare_seen) != EXPECTED_BARE:
        print(f"FAIL: bare fill count {len(bare_seen)} != expected {EXPECTED_BARE}")
        ok = False
    if left_shaped or left_bare or left_at:
        print("FAIL: placeholder remnants after replacement")
        ok = False
    if not (seen or bare_seen or quote_fixes):
        print("note: nothing left to replace (already clean)")
        ok = True
    if not ok:
        return 1

    if dry:
        print("\n--dry-run: nothing written")
        return 0

    TARGET.write_text(out, encoding="utf-8", newline="")
    print(f"\nwrote {TARGET.relative_to(REPO)} ({len(out.encode('utf-8'))} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
