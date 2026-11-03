# -*- coding: utf-8 -*-
"""Estimate A1's body word count (title through references), stripping LaTeX commands and captions."""
import io
import os
import re

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def body_words(path, seen=None):
    seen = seen or set()
    if path in seen or not os.path.exists(path):
        return 0
    seen.add(path)
    t = io.open(path, encoding="utf-8", errors="ignore").read()
    # expand \input
    total = 0
    for m in re.finditer(r"\\input\{([^}]+)\}", t):
        name = m.group(1)
        cand = os.path.join(REPO, "paper_a1", name if name.endswith(".tex") else name + ".tex")
        total += body_words(cand, seen)
    t = re.sub(r"\\input\{[^}]+\}", " ", t)
    t = re.sub(r"(?m)%.*$", " ", t)                     # comments
    t = re.sub(r"\\(begin|end)\{[^}]+\}", " ", t)
    t = re.sub(r"\\[a-zA-Z]+\*?(\[[^\]]*\])?", " ", t)  # commands
    t = re.sub(r"[{}$&_^~\\]", " ", t)
    words = [w for w in re.split(r"\s+", t) if re.search(r"[A-Za-z]{2,}", w)]
    return total + len(words)


main = os.path.join(REPO, "paper_a1", "main.tex")
t = io.open(main, encoding="utf-8").read()
has_inputs = "\\input{" in t
n = body_words(main)
print("  main.tex uses \\input:", has_inputs)
print("  estimated body words (all included files):", n)
print("  references count:", len(re.findall(r"\\bibitem|@\w+\{", io.open(os.path.join(REPO, 'paper_a1', 'main.bbl'), encoding='utf-8', errors='ignore').read())) if os.path.exists(os.path.join(REPO, 'paper_a1', 'main.bbl')) else "?")
