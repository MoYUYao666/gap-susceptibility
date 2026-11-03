# -*- coding: utf-8 -*-
r"""Audit every table float in Paper A's reframed tree and apply the mechanical formatting fixes:

  - `\centering` present;
  - `\footnotesize` (tables here are wide) present;
  - `\setlength{\tabcolsep}{...}` present;
  - booktabs rules present (toprule/midrule/bottomrule);
  - caption length reported (long captions need prose-level shortening, which a script must not fake).

The script prints a per-table report and only adds what is missing; it never edits table contents.
"""
import io
import os
import re

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

FILES = []
for root, _, files in os.walk(os.path.join("paper合", "reframed")):
    for f in sorted(files):
        if f.endswith(".tex"):
            FILES.append(os.path.join(root, f))

TBL_RE = re.compile(r"\\begin\{table\*?\}(.*?)\\end\{table\*?\}", re.S)
CAP_RE = re.compile(r"\\caption\{", re.S)

rows = []
changed = []
for p in FILES:
    t = io.open(p, encoding="utf-8").read()
    out = t
    for m in TBL_RE.finditer(t):
        body = m.group(1)
        # caption length: count characters up to the balancing brace (approximate by scanning)
        i = body.find("\\caption{")
        cap_len = 0
        if i >= 0:
            depth = 0
            for k in range(i + len("\\caption"), len(body)):
                if body[k] == "{":
                    depth += 1
                elif body[k] == "}":
                    depth -= 1
                    if depth == 0:
                        cap_len = k - i
                        break
        has = lambda s: s in body
        label = re.search(r"\\label\{([^}]*)\}", body)
        rows.append((os.path.basename(p), label.group(1) if label else "-", cap_len,
                     has("\\centering"), has("\\footnotesize"), has("\\tabcolsep"),
                     has("\\toprule"), has("\\bottomrule")))
        patch = ""
        if not has("\\centering"):
            patch += "\\centering\n"
        if not has("\\footnotesize"):
            patch += "\\footnotesize\n"
        if not has("\\tabcolsep"):
            patch += "\\setlength{\\tabcolsep}{4pt}\n"
        if patch:
            start = m.start(1) + 1           # just after \begin{table}[...]
            # insert right after the begin line
            nl = out.find("\n", m.start())
            out = out[:nl + 1] + patch + out[nl + 1:]
    if out != t:
        io.open(p, "w", encoding="utf-8", newline="").write(out)
        changed.append(os.path.basename(p))

print("%-24s %-28s %6s %3s %3s %3s %3s %3s" % ("file", "label", "capLen", "cen", "fs", "sep", "top", "bot"))
for r in rows:
    print("%-24s %-28s %6d %3s %3s %3s %3s %3s" % (r[0], r[1], r[2],
          "y" if r[3] else "-", "y" if r[4] else "-", "y" if r[5] else "-",
          "y" if r[6] else "-", "y" if r[7] else "-"))
print("\ntables:", len(rows), "| files patched:", changed if changed else "none")
long_caps = [r for r in rows if r[2] > 900]
print("captions longer than 900 chars (need prose-level shortening):")
for r in long_caps:
    print("  %-24s %-28s %d chars" % (r[0], r[1], r[2]))
