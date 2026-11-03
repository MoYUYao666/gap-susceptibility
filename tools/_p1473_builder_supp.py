# -*- coding: utf-8 -*-
r"""Add a --supplementary option to the venue package builder (copies the PDF and lists it in the README)."""
import ast
import io

p = "tools/_p1336_build_venue_package.py"
t = io.open(p, encoding="utf-8").read()
if "--supplementary" in t:
    print("already patched")
    raise SystemExit(0)
old = '    ap.add_argument("--zip-exclude", default="", help="comma-separated file names to omit from latex_source.zip")'
new = ('    ap.add_argument("--zip-exclude", default="", help="comma-separated file names to omit from latex_source.zip")\n'
       '    ap.add_argument("--supplementary", default=None, help="supplementary PDF to copy into the package")')
assert t.count(old) == 1
t = t.replace(old, new, 1)
old2 = '''    items = [("manuscript", abs_(a.manuscript), "Manuscript.pdf")]
    for name, rel in (("title_page", a.title_page), ("cover_letter", a.cover_letter),
                      ("abstract", a.abstract), ("highlights", a.highlights)):'''
new2 = '''    items = [("manuscript", abs_(a.manuscript), "Manuscript.pdf")]
    if a.supplementary:
        items.append(("supplementary", abs_(a.supplementary), "Supplementary.pdf"))
    for name, rel in (("title_page", a.title_page), ("cover_letter", a.cover_letter),
                      ("abstract", a.abstract), ("highlights", a.highlights)):'''
assert t.count(old2) == 1
t = t.replace(old2, new2, 1)
old3 = "| LaTeX source | `latex_source.zip` | {n_source} files |"
new3 = "| Supplementary | `{supp_name}` | {supp_note} |\n| LaTeX source | `latex_source.zip` | {n_source} files |"
assert t.count(old3) == 1
t = t.replace(old3, new3, 1)
old4 = "        n_source=n_source,"
new4 = ('        n_source=n_source,\n'
        '        supp_name=facts["supplementary"]["file"] if facts.get("supplementary") else "-",\n'
        '        supp_note=(f"{facts[\'supplementary\'][\'pages\']} pages" if facts.get("supplementary") else "not supplied"),')
assert t.count(old4) == 1
t = t.replace(old4, new4, 1)
io.open(p, "w", encoding="utf-8", newline="").write(t)
ast.parse(t)
print("builder supplementary option added")
