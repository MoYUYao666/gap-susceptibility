"""Classify every top-level item in outputs/ by how it is referenced.

Read-only. Produces the data needed to decide what can be moved safely and what
must stay put, and to build the per-paper ownership map.
"""
import collections
import pathlib
import re

ROOT = pathlib.Path(r"D:\Realdesktop\Wan\Important\New")
OUT = ROOT / "outputs"

# every top-level item in outputs/
items = sorted(p.name for p in OUT.iterdir())
dirs = {p.name for p in OUT.iterdir() if p.is_dir()}

# collect references from every script / doc / notebook outside outputs/ itself
SCAN_EXT = {".py", ".ps1", ".sh", ".md", ".ipynb", ".json", ".tex"}
SKIP = {"data", "models", "coco", "flickr30k", ".git", ".worktrees", "envs",
        "outputs", "备选", ".codegraph"}

refs = collections.Counter()
files_scanned = 0
for p in ROOT.rglob("*"):
    if not p.is_file() or p.suffix.lower() not in SCAN_EXT:
        continue
    parts = set(p.relative_to(ROOT).parts)
    if parts & SKIP:
        continue
    files_scanned += 1
    try:
        txt = p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        continue
    for m in re.finditer(r"outputs[/\\]([A-Za-z0-9_\-\.]+)", txt):
        refs[m.group(1)] += 1

print(f"scanned {files_scanned} files outside outputs/")
print(f"distinct names referenced: {len(refs)}")
print(f"top-level items in outputs/: {len(items)}  ({len(dirs)} dirs)")
print()

referenced = [i for i in items if refs.get(i, 0) > 0]
unreferenced = [i for i in items if refs.get(i, 0) == 0]

print("=" * 74)
print(f"REFERENCED — must stay at their current path: {len(referenced)} items")
print("=" * 74)
for i in sorted(referenced, key=lambda x: -refs[x])[:15]:
    print(f"  {refs[i]:4d}x  {i}")
print(f"  ... and {max(0, len(referenced) - 15)} more")

print()
print("=" * 74)
print(f"UNREFERENCED — candidates for tidying: {len(unreferenced)} items")
print("=" * 74)
for i in unreferenced:
    p = OUT / i
    if p.is_dir():
        n = sum(1 for _ in p.rglob("*") if _.is_file())
        sz = sum(f.stat().st_size for f in p.rglob("*") if f.is_file())
        print(f"  [dir ] {i:<44} {n:5d} files {sz/1e6:8.1f} MB")
    else:
        print(f"  [file] {i:<44} {p.stat().st_size/1e6:8.2f} MB")

# dynamic construction check: how many places build the path instead of
# writing it literally, which a text substitution could never catch
dyn = 0
for p in ROOT.rglob("*.py"):
    parts = set(p.relative_to(ROOT).parts)
    if parts & SKIP:
        continue
    txt = p.read_text(encoding="utf-8", errors="ignore")
    dyn += len(re.findall(r"""join\(\s*['"]outputs['"]""", txt))
    dyn += len(re.findall(r"""(?:Path|ROOT|BASE)\s*/\s*['"]outputs['"]""", txt))
print()
print(f"dynamic path constructions (join/Path) a literal replace would MISS: {dyn}")
