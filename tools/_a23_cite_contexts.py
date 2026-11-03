"""Extract every \citet/\citep occurrence with context, so each can be
rewritten for IEEE numeric citation style. Read-only."""
import re
import pathlib

BASE = pathlib.Path(r"D:\Realdesktop\Wan\Important\New\paper_a2")
FILES = [
    "main.tex",
    "ext_partI_theory.tex",
    "ext_partII_domains.tex",
    "ext_partIII_dynamics.tex",
    "ext_partIV_degradation.tex",
    "ext_partV_mechanisms.tex",
]

CMD = re.compile(r"\\cite([tp]?)\{([^}]*)\}")

rows = []
for fn in FILES:
    p = BASE / fn
    if not p.exists():
        continue
    text = p.read_text(encoding="utf-8")
    for m in CMD.finditer(text):
        kind = "citep" if m.group(1) == "p" else ("citet" if m.group(1) == "t" else "cite")
        key = m.group(2)
        # context window
        a = max(0, m.start() - 110)
        b = min(len(text), m.end() + 70)
        ctx = text[a:b].replace("\n", " ")
        ctx = re.sub(r"\s+", " ", ctx)
        ctx = ctx.replace(m.group(0), f"[[{kind}:{key}]]")
        line_no = text[: m.start()].count("\n") + 1
        rows.append((fn, line_no, kind, key, ctx))

out = BASE.parent / "outputs" / "_a23_cite_contexts.txt"
with out.open("w", encoding="utf-8") as f:
    f.write(f"total occurrences: {len(rows)}\n")
    f.write(f"citet: {sum(1 for r in rows if r[2]=='citet')}  "
            f"citep: {sum(1 for r in rows if r[2]=='citep')}  "
            f"plain: {sum(1 for r in rows if r[2]=='cite')}\n")
    f.write("=" * 100 + "\n")
    for fn, ln, kind, key, ctx in rows:
        f.write(f"\n[{fn}:{ln}]  {kind}  key={key}\n  {ctx}\n")

# also: distinct keys cited, and order of first citation (for IEEE ordering)
seen = []
for fn, ln, kind, key, ctx in rows:
    if key not in seen:
        seen.append(key)
with (BASE.parent / "outputs" / "_a23_cite_order.txt").open("w", encoding="utf-8") as f:
    f.write("first-citation order (by file order main -> ext I..V):\n")
    for i, k in enumerate(seen, 1):
        f.write(f"{i:3d}. {k}\n")

print(f"occurrences={len(rows)} lines={len(seen)}")
print("wrote", out)
