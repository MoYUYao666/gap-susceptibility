# -*- coding: utf-8 -*-
"""Make the staged package check try every candidate main .tex and keep the one matching the shipped page count."""
import ast
import io

p = "tools/_p1444_staged_package_check.py"
t = io.open(p, encoding="utf-8").read()
old = '''def find_main(d):
    cands = []
    for f in os.listdir(d):
        if f.endswith(".tex"):
            p = os.path.join(d, f)
            t = io.open(p, encoding="utf-8", errors="ignore").read()
            if "\\\\documentclass" in t and "\\\\begin{document}" in t:
                cands.append(f)
    cands.sort(key=lambda x: (0 if x.startswith("main") else 1, len(x)))
    return cands[0] if cands else None'''
new = '''def find_main(d, want_pages=None):
    cands = []
    for f in os.listdir(d):
        if f.endswith(".tex"):
            p = os.path.join(d, f)
            t = io.open(p, encoding="utf-8", errors="ignore").read()
            if "\\\\documentclass" in t and "\\\\begin{document}" in t:
                cands.append(f)
    cands.sort(key=lambda x: (0 if x.startswith("main") else 1, len(x)))
    if want_pages is None:
        return cands[0] if cands else None
    best = cands[0] if cands else None
    for f in cands[:3]:
        errs, undef, over, pages, _ = compile_pdf(d, f)
        if pages is not None and pages == want_pages:
            return f
    return best'''
assert t.count(old) == 1, t.count(old)
t = t.replace(old, new, 1)
old2 = '''            main_tex = find_main(tmp)
            if not main_tex:
                entry["status"] = "no main tex"
            else:'''
new2 = '''            shipped_pages0 = None
            sp0 = os.path.join(pk, "Manuscript.pdf")
            if os.path.exists(sp0):
                from pypdf import PdfReader
                shipped_pages0 = len(PdfReader(sp0).pages)
            main_tex = find_main(tmp, want_pages=shipped_pages0)
            if not main_tex:
                entry["status"] = "no main tex"
            else:'''
assert t.count(old2) == 1
t = t.replace(old2, new2, 1)
io.open(p, "w", encoding="utf-8", newline="").write(t)
ast.parse(t)
print("staged checker patched")
