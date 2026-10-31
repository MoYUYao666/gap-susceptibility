# -*- coding: utf-8 -*-
"""One-shot repair of the DOI block in docs/P3_SUBMISSION_STATUS.md (2026-10-24 consistency round)."""
import io

P = "docs/P3_SUBMISSION_STATUS.md"
t = io.open(P, encoding="utf-8").read()

old = "\n".join([
    "- `v2.2` (DOI cited by the submitted manuscript PRLETTERS-D-26-02671): 10.5281/zenodo.23523263; kept frozen.",
    "- `v1.0-prl-revision` (historical): 10.5281/zenodo.23341223.",
    "- `v2.4` (current repository release, 2026-10-24): **10.5281/zenodo.23614290**.",
])
new = "\n".join([
    "- `v2.4` (current repository release, 2026-10-24): **10.5281/zenodo.23614290**.",
    "- `v2.2` (DOI cited by the submitted manuscript PRLETTERS-D-26-02671): 10.5281/zenodo.23523263; kept frozen.",
    "- `v2.3` (superseded release, recorded 2026-10-24): 10.5281/zenodo.23609295; kept frozen.",
    "- `v1.0-prl-revision` (historical): 10.5281/zenodo.23341223.",
])
assert old in t, "DOI block anchor not found"
t = t.replace(old, new, 1)
io.open(P, "w", encoding="utf-8", newline="").write(t)
print("DOI block rewritten")
for line in t.splitlines()[-6:]:
    print("   ", line)