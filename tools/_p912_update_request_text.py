# -*- coding: utf-8 -*-
r"""Note the extra corrections in the prepared request and the upload READMEs.

The replacement files now carry more than the pointer fixes, because the operator asked for the odd
theorem rendering and the corollary/lemma numbering to be put right as well. The Editorial Office
should be told, so the request text and the two READMEs are updated to say what else changed. The
already-sent EM query cannot be edited, so this text is kept ready for a follow-up message.

    python tools/_p912_update_request_text.py [--apply]
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
REV = REPO / "SUBMISSION" / "P3_PRL_revision"
EMAIL = REV / "EMAIL_TO_EM_2026-10-15.txt"

ANCHOR = ("I have checked the corrected pair against each other, and both compile without\n"
          "any unresolved reference.")
EXTRA = """In addition to the two defects above, the replacement corrects three typographical
faults in the manuscript that I found while preparing it. The theorem-like environments
did not separate their number from the following note, so a statement read
"Theorem III.2(Projection Error Bound)"; the five corollaries were named in subsection
headings rather than set as corollaries; and hyperref drew a coloured box around every
citation and cross-reference. None of these changes a result, a number, a table or a
figure. The supplement is unchanged apart from the cross-reference repairs and the added
table described above.
"""

README_ADD = """Also corrected in these files (2026-10-15, after the operator reviewed the rendering):

  - theorem-like statements now separate the number from the note, so they read
    "Theorem III.2 (Projection Error Bound)" instead of "Theorem III.2(Projection Error Bound)";
  - the five corollaries are set as corollaries and are cross-referenced, instead of being named in
    subsection headings that printed as "III.D. Corollary 1: ...";
  - the lemma is numbered by section (Lemma III.1) rather than as a third-level number (Lemma III.1.1);
  - hyperref no longer draws a coloured box around citations and cross-references.

No result, number, table or figure changes.
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    if not a.apply:
        print("  (dry run)")
        return 0

    t = io.open(EMAIL, encoding="utf-8").read()
    if EXTRA.strip() not in t:
        assert ANCHOR in t, "the anchor paragraph was not found in the request text"
        t = t.replace(ANCHOR, EXTRA + ANCHOR, 1)
        io.open(EMAIL, "w", encoding="utf-8", newline="").write(t)
        print("  email text: noted the three typographical corrections")
    else:
        print("  email text: already noted")

    for folder in (REV / "UPLOAD_2026-10-15", REV / "CORRECTED_2026-10-15"):
        rp = folder / "README.md"
        if not rp.exists():
            print(f"  {folder.name}/README.md: missing")
            continue
        r = io.open(rp, encoding="utf-8").read()
        if "theorem-like statements now separate" in r:
            print(f"  {folder.name}/README.md: already noted")
            continue
        io.open(rp, "w", encoding="utf-8", newline="").write(r.rstrip() + "\n\n" + README_ADD)
        print(f"  {folder.name}/README.md: noted the extra corrections")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
