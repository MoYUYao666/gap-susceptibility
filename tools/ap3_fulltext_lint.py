"""paper_ap3 full-text content-level health check (catches the class of defects a compile audit misses).

Checks:
  A residual artefacts: Python source fragments (r'...'), TODO/FIXME/placeholders, `??`, empty
    \\ref{}/\\cite{}, a trailing isolated `: '`, unclosed `` quote pairs
  B duplicate paragraphs/sentences: normalized sentences >= 70 chars appearing >= 2 times
  C limitation numbering: ordinals in the limitations paragraph vs global `Limitation~N` refs
  D number provenance: whether body numbers (incl. inside $..$) trace to outputs/*.json and
    paper3/scripts/outputs/experiments/*.json; list untraceable candidates
  E floats & refs: every table/figure \\ref-ed; every \\ref resolves to a \\label

Usage: python tools/ap3_fulltext_lint.py [paper_ap3]
Exit code: 0 = no A/C/E-level problems (B/D are advisory)
"""
import glob
import json
import os
import re
import sys
from collections import Counter

# 2026-09-20: argv[1] used to be taken as the paper directory whatever it was, so passing a flag
# (e.g. --all) made the glob match nothing and every check pass vacuously -- a false PASS.  Options
# are now separated from the positional directory, and an empty file set aborts instead.
_args = [a for a in sys.argv[1:] if not a.startswith('--')]
SHOW_ALL = '--all' in sys.argv
DIR = _args[0] if _args else 'paper_ap3'
TEX = sorted(glob.glob(os.path.join(DIR, '*.tex')) + glob.glob(os.path.join(DIR, 'sections', '*.tex')))
if not TEX:
    print('ABORT: no .tex files found under %r — refusing to report a vacuous PASS' % DIR)
    sys.exit(2)
ORDINALS = ['First,', 'Second,', 'Third,', 'Fourth,', 'Fifth,', 'Sixth,', 'Seventh,', 'Eighth,',
            'Ninth,', 'Tenth,', 'Eleventh,', 'Twelfth,', 'Thirteenth,', 'Fourteenth,',
            'Fifteenth,', 'Sixteenth,', 'Seventeenth,']
WORD2NUM = {w: i + 1 for i, w in enumerate(ORDINALS)}

problems = {'A': [], 'B': [], 'C': [], 'D': [], 'E': []}

# ---------- Reading ----------
files = {}
for p in TEX:
    files[p] = open(p, encoding='utf-8', errors='replace').read()


def lines_of(txt):
    return txt.splitlines()


# ---------- A residual artefacts ----------
PAT_ARTIFACT = [
    (re.compile(r"^\s*r'"), 'Python raw-string fragment'),
    (re.compile(r'^\s*(import |from \w+ import|def |class |print\(|json\.dump|torch\.)'), 'Python source line'),
    (re.compile(r'\b(TODO|FIXME|XXX|TBD|PLACEHOLDER|待补|待填|WIP)\b'), 'placeholder marker'),
    (re.compile(r'\?\?'), 'unresolved reference marker ??'),
    (re.compile(r'\\ref\{\s*\}'), 'empty \\ref{}'),
    (re.compile(r'\\cite\{\s*\}'), 'empty \\cite{}'),
    (re.compile(r":\s*'\s*$"), 'trailing isolated quote fragment'),
    (re.compile(r'```'), 'Markdown code fence'),
    (re.compile(r'\\begin\{tabular\}.*\\end\{tabular\}.*\\end\{tabular\}'), 'duplicated tabular end'),
]
for p, txt in files.items():
    for i, ln in enumerate(lines_of(txt), 1):
        for rx, why in PAT_ARTIFACT:
            if rx.search(ln):
                problems['A'].append(f'{os.path.relpath(p, DIR)}:{i}  [{why}]  {ln.strip()[:110]}')

# ---------- B duplicate sentences ----------
sent_counter = Counter()
sent_where = {}
for p, txt in files.items():
    flat = re.sub(r'\s+', ' ', txt)
    for m in re.finditer(r'[^.!?]{70,}?[.!?]', flat):
        s = m.group(0).strip()
        s = re.sub(r'\\[a-zA-Z]+\{[^}]*\}', 'X', s)      # strip \ref{} and the like
        s = re.sub(r'\s+', ' ', s)
        sent_counter[s] += 1
        sent_where.setdefault(s, []).append(os.path.relpath(p, DIR))
for s, c in sent_counter.items():
    if c >= 2:
        problems['B'].append(f'appears {c} times in {sorted(set(sent_where[s]))}: {s[:130]}')

# ---------- C limitation numbering ----------
lim_txt = files.get(os.path.join(DIR, 'sections', '07_discussion.tex'), '')
found = [(m.start(), w) for w in ORDINALS for m in re.finditer(re.escape(w), lim_txt)]
found.sort()
order = [w for _, w in found]
nums = [WORD2NUM[w] for w in order]
if nums != sorted(nums):
    problems['C'].append(f'ordinals are not monotone in order of appearance: {order}')
gaps = [n for n in range(1, max(nums) + 1) if n not in nums] if nums else []
if gaps:
    problems['C'].append(f'ordinal numbers missing (limitation numbers never used): {gaps}')
maxlim = max(nums) if nums else 0
refs = set()
for p, txt in files.items():
    for m in re.finditer(r'Limitation~?(\d+)', txt):
        refs.add(int(m.group(1)))
    for m in re.finditer(r'Limitation[s]?~?(\d+)', txt):
        refs.add(int(m.group(1)))
over = sorted(r for r in refs if r > maxlim)
if over:
    problems['C'].append(f'reference to a nonexistent limitation number: {over} (actual max {maxlim})')
missing_refs = sorted(set(range(1, maxlim + 1)) - refs)
print(f'  [C] limitations paragraph has {maxlim} items; numbers ever \\ref-ed: {sorted(refs)}')
if missing_refs:
    print(f'      (numbers never referenced, advisory only: {missing_refs})')

# ---------- D number provenance ----------
# 2026-09-20: the source glob was `outputs/*.json` (non-recursive), so every nested archive —
# including outputs/theory/siglip/, outputs/siglip/ and outputs/analysis/, i.e. exactly the files
# behind the SigLIP claims — was invisible and its numbers were reported as untraceable.  It is now
# recursive, and the rounding variants reach four decimals because the manuscript quotes up to four.
data_tokens = set()
num_files = 0
for pat in ('outputs/**/*.json', 'paper3/scripts/outputs/**/*.json',
            'paper3/scripts/outputs/**/*.log'):
    for p in glob.glob(pat, recursive=True):
        num_files += 1
        try:
            txt = open(p, encoding='utf-8', errors='replace').read()
        except Exception:  # noqa: BLE001
            continue
        for m in re.finditer(r'-?\d+\.?\d*', txt):
            t = m.group(0)
            data_tokens.add(t)
            try:
                f = float(t)
                data_tokens.add(f'{f:.0f}')
                data_tokens.add(f'{f:.1f}')
                data_tokens.add(f'{abs(f):.0f}')
                if f != 0:
                    data_tokens.add(f'{abs(f):.2f}')
                    data_tokens.add(f'{abs(f):.3f}')
                    data_tokens.add(f'{abs(f):.4f}')
            except ValueError:
                pass

SKIP = {'0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '100', '1000',
        '2024', '2025', '2026', '16', '20', '24', '32', '64', '128', '256',
        # documentation facts rather than measurements (and split by the thousands comma anyway)
        '52002', '002'}
suspicious = []
for p, txt in files.items():
    if 'sections' not in p and os.path.basename(p) == 'main.tex':
        continue
    if 'cover_letter' in os.path.basename(p):
        continue  # disclosure text: manuscript numbers, dates and journal IDs, not measurements
    for m in re.finditer(r'(?<![\w.])(\d+(?:\.\d+)?)(?![\w.])', txt):
        tok = m.group(1)
        if tok in SKIP or tok in data_tokens:
            continue
        ctx = txt[max(0, m.start() - 60):m.end() + 40].replace('\n', ' ')
        suspicious.append((tok, os.path.relpath(p, DIR), ctx.strip()[:120]))
# only list numbers appearing >=3 times or of length>=3 (a single small number is usually an enumeration/page)
# 2026-09-20: the list used to be truncated here with [:40], and the report printed that truncated
# length, so "40 candidates" was a saturated cap rather than a count and real improvements were
# invisible.  Keep the full list; the printer slices for display.
cnt = Counter(t for t, _, _ in suspicious)
problems['D'] = [f'{t}  (×{cnt[t]})  … {c}' for t, f, c in suspicious if cnt[t] >= 3 or len(t) >= 3]
print(f'  [D] {num_files} data files, {len(data_tokens)} numeric tokens extracted; '
      f'{len(problems["D"])} body numbers with no located source (advisory, needs human judgement)')

# ---------- E floats and references ----------
labels = set()
for p, txt in files.items():
    labels |= set(re.findall(r'\\label\{([^}]+)\}', txt))
refs_all = set()
for p, txt in files.items():
    refs_all |= set(re.findall(r'\\ref\{([^}]+)\}', txt))
floats = {}
for p, txt in files.items():
    for m in re.finditer(r'\\begin\{(table|figure)\}', txt):
        seg = txt[m.start():m.start() + 4000]
        lm = re.search(r'\\label\{([^}]+)\}', seg)
        if lm:
            floats[lm.group(1)] = (m.group(1), os.path.relpath(p, DIR))
unref = sorted(k for k in floats if k not in refs_all)
if unref:
    problems['E'].append(f'unreferenced floats: {[(k, floats[k][1]) for k in unref]}')
dangling = sorted(r for r in refs_all if r not in labels)
if dangling:
    problems['E'].append(f'\\ref points to a nonexistent label: {dangling}')

# ---------- Output ----------
print()
for k in 'ABCE':
    print(f'=== Check {k}: {len(problems[k])} items ===')
    for item in problems[k][:25]:
        print('   -', item)
    print()
print(f'=== Check D (number-provenance candidates, advisory): {len(problems["D"])} items ===')
# by default show only the first 15; `--all` prints the full list for item-by-item manual triage (derived / documentation / truly unsourced)
for item in (problems['D'] if SHOW_ALL else problems['D'][:15]):
    print('   -', item)

print()
hard = len(problems['A']) + len(problems['C']) + len(problems['E'])
print(f'Verdict: {hard} A/C/E-level problems in total → {"PASS" if hard == 0 else "NEEDS REVIEW"}; '
      f'{len(problems["B"])} duplicate sentences, {len(problems["D"])} numbers to verify (advisory)')
sys.exit(0 if hard == 0 else 1)
