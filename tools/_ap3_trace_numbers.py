# -*- coding: utf-8 -*-
"""Trace manuscript numbers back to the archive by nearest-value lookup.

Why this exists: tools/ap3_fulltext_lint.py matches manuscript tokens against *literal* archive
tokens, which can never find a derived quantity (a mean, a standard deviation, a difference, a
ratio) or a rounded one.  This tool instead loads every number out of the archives with its JSON
path and reports the closest archived values.

READ THE AMBIGUITY COLUMN.  At the precision a manuscript quotes, a nearest-value match is usually
NOT evidence of provenance: every value tried so far matches 19-586 archived numbers, because the
archives contain index lists, distances and embeddings where any small number occurs somewhere.
A hit is only meaningful when the path names the quantity (e.g.
clip_beta_selection.json.separation...) and the match is exact to the quoted digits.

The reliable method, used to verify ap3's section-6 tables, is different: find the archive that
*defines* the table (by experiment name, e.g. sample_size_results.json for the n x rank table),
then recompute the quantity from the stored arrays and compare.  Use this tool to generate hints and
to notice that a number is absent, not to claim provenance.

Usage: python tools/_ap3_trace_numbers.py 1508 34.7 8.97 33.10 1112
"""
import glob
import json
import os
import sys

PATTERNS = ('outputs/**/*.json', 'paper3/scripts/outputs/**/*.json')
TOL = 0.02  # relative tolerance for calling a value "present"


def numbers(obj, path, out):
    if isinstance(obj, dict):
        for k, v in obj.items():
            numbers(v, path + '.' + str(k), out)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            numbers(v, path + '[%d]' % i, out)
    elif isinstance(obj, bool):
        return
    elif isinstance(obj, (int, float)):
        out.append((float(obj), path))


def main():
    wanted = []
    for a in sys.argv[1:]:
        try:
            wanted.append(float(a))
        except ValueError:
            pass
    if not wanted:
        print('usage: _ap3_trace_numbers.py <number> [number ...]')
        return 2

    pool = []
    files = 0
    for pat in PATTERNS:
        for p in glob.glob(pat, recursive=True):
            try:
                data = json.load(open(p, encoding='utf-8'))
            except Exception:  # noqa: BLE001
                continue
            files += 1
            numbers(data, os.path.basename(p), pool)
    print('scanned %d files, %d numbers' % (files, len(pool)))
    print()
    for w in wanted:
        hits = [(abs(v - w), v, path) for v, path in pool
                if abs(v - w) <= max(TOL * abs(w), 1e-9)]
        hits.sort()
        if not hits:
            near = sorted(pool, key=lambda t: abs(t[0] - w))[:1]
            d, v, path = near[0]
            rel = d / max(abs(w), 1e-9)
            print('%-10s nearest %-14.6g  %-32s  NOT FOUND (%.3g%% away) -> derived or unsourced'
                  % (w, v, path[:32], rel * 100))
            continue
        # a value that matches hundreds of index lists is not evidence of provenance
        note = '' if len(hits) <= 5 else '  AMBIGUOUS: matches %d archived numbers' % len(hits)
        for d, v, path in hits[:3]:
            print('%-10s match   %-14.6g  %-32s  %s%s'
                  % (w, v, path[:32], 'EXACT' if d <= max(TOL * abs(w), 1e-9) else 'near', note))
    return 0


if __name__ == '__main__':
    sys.exit(main())
