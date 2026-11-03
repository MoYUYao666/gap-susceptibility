# -*- coding: utf-8 -*-
"""Patch the two helper scripts.

1. tools/build_submission_packages.py -- the submission system labels the upload slot
   "Cover letter", and the author renamed the generated file to match.  Make the generator
   emit that name itself, so the folder and its generated README cannot disagree again.
2. tools/build_abstract_standalone.py -- report how many dangling cross-references were
   dropped, so the fix is visible in the build output rather than silent."""
import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def patch(rel, pairs):
    p = os.path.join(ROOT, rel.replace('/', os.sep))
    with io.open(p, encoding='utf-8') as f:
        t = f.read()
    for old, new, label in pairs:
        n = t.count(old)
        if n != 1:
            print('ABORT %s: %s -- expected 1 occurrence, found %d' % (rel, label, n))
            sys.exit(1)
        t = t.replace(old, new)
        print('  OK  %s: %s' % (rel, label))
    with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
        f.write(t)

patch('tools/build_submission_packages.py', [
    ("    'files': [\n        ('LaTeX source (manuscript)', ['main.tex', 'related_work.tex', 'related_work_bibitems.tex']),",
     "    'renames': {'cover_letter.pdf': 'Cover letter.pdf'},\n"
     "    'files': [\n        ('LaTeX source (manuscript)', ['main.tex', 'related_work.tex', 'related_work_bibitems.tex']),",
     'A1 spec gains the rename'),
    ("    'files': [\n        ('LaTeX source (manuscript + extension parts)', [",
     "    'renames': {'cover_letter.pdf': 'Cover letter.pdf'},\n"
     "    'files': [\n        ('LaTeX source (manuscript + extension parts)', [",
     'A23 spec gains the rename'),
    ('            shutil.copy2(s, d)\n'
     '            copied.append(rel)\n'
     '            total_bytes += os.path.getsize(s)\n'
     "            lines.append('| `%s` | %d B | `%s` |' % (rel, os.path.getsize(s), sha256(s)[:16]))",
     '            shutil.copy2(s, d)\n'
     "            final_rel = spec.get('renames', {}).get(rel, rel)\n"
     '            if final_rel != rel:\n'
     '                os.replace(d, os.path.join(dest_dir, final_rel.replace("/", os.sep)))\n'
     '            copied.append(final_rel)\n'
     '            total_bytes += os.path.getsize(s)\n'
     "            lines.append('| `%s` | %d B | `%s` |' % (final_rel, os.path.getsize(s), sha256(s)[:16]))",
     'copy loop applies the rename'),
])

patch('tools/build_abstract_standalone.py', [
    ("        print('%-10s abstract.tex/pdf written   pages %s   errors %d   size %d B'\n"
     "              % (folder, pages.group(1) if pages else '?', errs,\n"
     "                 os.path.getsize(os.path.join(ROOT, folder, 'abstract.pdf'))))",
     "        print('%-10s abstract.tex/pdf written   pages %s   errors %d   size %d B   cross-refs dropped %d'\n"
     "              % (folder, pages.group(1) if pages else '?', errs,\n"
     "                 os.path.getsize(os.path.join(ROOT, folder, 'abstract.pdf')),\n"
     "                 before_refs - after_refs))",
     'abstract build reports dropped cross-references'),
])

print('')
print('both helper scripts patched')
