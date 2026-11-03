# -*- coding: utf-8 -*-
"""Compress two Commentary sentences by index slicing (line-wrap safe) to fit the 7-page limit."""
import io

md = "paper_review_prl/MANUSCRIPT.md"
t = io.open(md, encoding="utf-8").read()

# sentence 1: from "The two differ" to the period after "warns about"
i = t.index("The two differ by a factor")
j = t.index("warns about", i) + len("warns about")
k = t.index(".", j) + 1
new1 = ("The two differ by a factor that is not negligible at these sample sizes, and a reader recomputing a\n"
        "published interval can obtain a different value [\u2014] a discrepancy of exactly the kind the "
        "benchmark-variance literature warns about.")
t = t[:i] + new1.replace("[\u2014]", "\u2014") + t[k:]
print("sentence 1 compressed")

# sentence 2: from "Because the visual encoder's behaviour" to "move."
a = t.index("Because the visual encoder's behaviour")
b = t.index("allowed to", a)
c = t.index(".", b) + 1
new2 = ("Differences attributed to a low-rank or adapter design may therefore reflect differences in what was allowed to "
        "move.")
t = t[:a] + new2 + t[c:]
print("sentence 2 compressed")

io.open(md, "w", encoding="utf-8", newline="").write(t)
