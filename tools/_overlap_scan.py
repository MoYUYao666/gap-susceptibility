# -*- coding: utf-8 -*-
"""Verbatim word-run scanner: find maximal common word runs between two LaTeX trees.

Reproduces the mechanical scan behind docs/P1_REVIEW_OVERLAP.md: strip markup, tokenise to words,
then report every maximal common run of at least MIN_WORDS words with its location on both sides.
Re-run it after a rewrite to show the overlap actually fell.

Usage: python tools/_overlap_scan.py paper paper合 [min_words]
"""
import io
import os
import re
import sys

MIN = int(sys.argv[3]) if len(sys.argv) > 3 else 20
CMD = re.compile(r'\\[a-zA-Z@]+\*?(\[[^\]]*\])?')
TOKEN = re.compile(r"[A-Za-z][A-Za-z'\-]+")


def words(path):
    """Return (tokens, line_of_token) so a match can be reported by file line."""
    text = io.open(path, encoding='utf-8', errors='replace').read()
    text = re.sub(r'(?<!\\)%.*', ' ', text)          # comments
    text = re.sub(r'\$[^$]*\$', ' ', text)            # inline math
    text = CMD.sub(' ', text)
    text = text.replace('{', ' ').replace('}', ' ').replace('&', ' ').replace('\\\\', ' ')
    toks, lines = [], []
    for m in TOKEN.finditer(text):
        toks.append(m.group(0).lower())
        lines.append(text.count('\n', 0, m.start()) + 1)
    return toks, lines


def collect(root):
    docs = {}
    for base, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in ('.git', '_superseded_2026')]
        for f in files:
            if f.endswith('.tex'):
                p = os.path.join(base, f)
                docs[p] = words(p)
    return docs


def main():
    a_root, b_root = sys.argv[1], sys.argv[2]
    A, B = collect(a_root), collect(b_root)
    a_index = {}
    for path, (ws, _ln) in A.items():
        for i in range(len(ws) - MIN + 1):
            a_index.setdefault(tuple(ws[i:i + MIN]), []).append((path, i))
    runs = []
    for path, (ws, blines) in B.items():
        i = 0
        while i <= len(ws) - MIN:
            key = tuple(ws[i:i + MIN])
            hit = a_index.get(key)
            if not hit:
                i += 1
                continue
            apath, ai = hit[0]
            aws = A[apath][0]
            length = MIN
            while (ai + length < len(aws) and i + length < len(ws)
                   and aws[ai + length] == ws[i + length]):
                length += 1
            runs.append((length, apath, A[apath][1][ai], path, blines[i]))
            i += length
    runs.sort(reverse=True)
    total = sum(r[0] for r in runs)
    show = '--text' in sys.argv
    print('A = %s (%d files, %d words)' % (a_root, len(A), sum(len(w[0]) for w in A.values())))
    print('B = %s (%d files, %d words)' % (b_root, len(B), sum(len(w[0]) for w in B.values())))
    print('common runs >= %d words: %d, total shared words: %d' % (MIN, len(runs), total))
    print('')
    for length, apath, aline, bpath, bline in runs[:30]:
        print('  %4d words  %s:%d  <->  %s:%d' % (length, apath, aline, bpath, bline))
        if show:
            ws, blines = B[bpath]
            idx = blines.index(bline)
            print('        B text: %s' % ' '.join(ws[max(0, idx - 6): idx + min(length, 55)]))
    return 0


if __name__ == '__main__':
    sys.exit(main())
