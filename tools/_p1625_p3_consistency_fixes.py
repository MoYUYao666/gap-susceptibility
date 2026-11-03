# -*- coding: utf-8 -*-
r"""Apply the document-side fixes of the 2026-10-24 P3 consistency round.

Idempotent. Each edit is asserted against the current file content, so re-running the script is a
no-op and a missing anchor raises instead of silently writing nothing.

    python tools/_p1625_p3_consistency_fixes.py --apply

Edits:
  1. docs/P3_RESPONSE_LETTER.md -- append the final "Title." paragraph that only the archived
     copy SUBMISSION/_archive/P3_PRL_rejected_2026-10-21/response/P3_RESPONSE_LETTER.md carries
     (44,995 B there against 44,468 B here; the paragraph is the whole difference).
  2. docs/P3_SUBMISSION_STATUS.md -- four stale spots, each re-pointed to the current files:
     the S17 claims-table row count (24 -> 25), the "three-stack" environment wording (-> four
     stacks / four-stack matrix), the next_revision page wording (17 pp / S1-S43 -> 18 pp and the
     built-artefact counts), and the two conflicting "current repository release" DOIs
     (v2.4 is the current release; v2.3 is a superseded release, both kept as history).
"""
from __future__ import annotations

import argparse
import io
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LETTER = os.path.join(REPO, "docs", "P3_RESPONSE_LETTER.md")
ARCHIVED = os.path.join(REPO, "SUBMISSION", "_archive", "P3_PRL_rejected_2026-10-21",
                        "response", "P3_RESPONSE_LETTER.md")
STATUS = os.path.join(REPO, "docs", "P3_SUBMISSION_STATUS.md")

TITLE_ANCHOR = "did not survive them, and the paper is a narrower and more defensible document as a result."

TITLE_PARAGRAPH = """
Title. The title has changed from "Gradient Structure Laws as Predictors of PEFT Design: Zero-Shot Cross-Architecture Rank Allocation" to "Zero-Shot Cross-Architecture Rank Allocation from Gradient Geometry". The revision withdrew the claim that gradient structure predicts PEFT design, so the original title no longer described the paper. The new title names the result that does hold: a rank allocation transferred zero-shot across architectures from gradient geometry, with the limits of that transfer stated in the paper.
"""

# (old, new) replacement pairs for docs/P3_SUBMISSION_STATUS.md. Applied in order; an absent anchor
# is reported instead of raising, so a second run is a clean no-op.
STATUS_EDITS: list[tuple[str, str]] = [
    # 1. next_revision package: the built artefact is 18 supplementary pages (S1--S43), while the
    #    17-page figure belongs to the 2026-10-23 freeze; state both so neither reads as stale.
    ("| finalized local draft | `SUBMISSION/P3_PRL_next_revision/` (Manuscript 10 pp; Supplementary 17 pp, S1\u2013S43) |",
     "| finalized local draft | `SUBMISSION/P3_PRL_next_revision/` (Manuscript 10 pp; Supplementary 18 pp, S1\u2013S43; the 2026-10-23 freeze was 17 pp) |"),
    # 2. Main-text wording: the environment matrix has four stacks (S29), not three.
    ("(three-stack environment matrix, newer-family and third-family controls, high-rank curvature).",
     "(four-stack environment matrix, newer-family and third-family controls, high-rank curvature)."),
    # 3. Claims table row count: 25 data rows (24 plus the SmolVLM-500M row), verified against
    #    supplementary.tex S17.
    ("- **Claim status table (S17):** rewritten to 24 rows so that every row matches the current evidence.",
     "- **Claim status table (S17):** rewritten to 25 rows (24 plus the SmolVLM-500M row) so that every row\n  matches the current evidence."),
    # 3b. Supplement page count in the same bullet, and the freeze date of the built artefact: the
    #     supplement is 18 pp (S1--S43) and the package was last rebuilt on 2026-10-24.
    ("- **Supplement:** 8 \u2192 17 pages, S1\u2013S43",
     "- **Supplement:** 8 \u2192 18 pages, S1\u2013S43"),
    ("| frozen draft built | 2026-10-23 |",
     "| frozen draft built | 2026-10-23; rebuilt 2026-10-24 |"),
    # 4. Repository DOI versions: exactly one release is current (v2.4); v2.3 becomes a superseded
    #    release kept for history, so no conclusion is dropped. The block is pinned on one anchor
    #    line and left alone when already correct, which keeps the script idempotent.
    ("- `v2.3` (current repository release): **10.5281/zenodo.23609295**.\n",
     "- `v2.4` (current repository release, 2026-10-24): **10.5281/zenodo.23614290**.\n"
     "- `v2.3` (superseded release, recorded 2026-10-24): 10.5281/zenodo.23609295; kept frozen.\n"),
]


def read(path: str) -> str:
    return io.open(path, encoding="utf-8").read()


def write(path: str, text: str) -> None:
    io.open(path, "w", encoding="utf-8", newline="").write(text)


def fix_letter(apply: bool) -> None:
    archived = read(ARCHIVED)
    live = read(LETTER)
    idx = archived.find("Title. The title has changed")
    if idx < 0:
        raise SystemExit("archived response letter does not contain the 'Title.' paragraph")
    paragraph = archived[idx:].strip()
    if "Title. The title has changed" in live:
        print("letter: 'Title.' paragraph already present -- no change")
        return
    if TITLE_ANCHOR not in live:
        raise SystemExit("live response letter does not contain the anchor sentence")
    if not live.rstrip().endswith("as a result."):
        raise SystemExit("live response letter does not end with the anchor clause")
    out = live.rstrip() + "\n\n" + paragraph + "\n"
    print("letter: appending the 'Title.' paragraph (%d chars)" % len(paragraph))
    if apply:
        write(LETTER, out)
    print("letter: %d -> %d bytes" % (len(live.encode('utf-8')), len(out.encode('utf-8'))))


def fix_status(apply: bool) -> None:
    text = read(STATUS)
    for old, new in STATUS_EDITS:
        if old not in text:
            print("status: anchor absent (already applied?): %.70s" % old.replace("\n", " "))
            continue
        print("status: replacing %.70s" % old.replace("\n", " "))
        text = text.replace(old, new, 1)
    if apply:
        write(STATUS, text)
        text = read(STATUS)
    checks = [
        ("25 rows", "rewritten to 25 rows" in text),
        ("four-stack wording", "four-stack environment matrix" in text),
        ("no three-stack wording", "three-stack environment matrix" not in text),
        ("18 pp next_revision", "Supplementary 18 pp, S1\u2013S43" in text),
        ("single current release", text.count("(current repository release") == 1),
        ("v2.4 is the current release",
         "- `v2.4` (current repository release, 2026-10-24): **10.5281/zenodo.23614290**." in text),
        ("v2.2 still the cited DOI", "cited by the submitted manuscript" in text
         and "10.5281/zenodo.23523263" in text),
        ("v2.3 kept as superseded", "v2.3` (superseded release" in text
         and "10.5281/zenodo.23609295" in text),
        ("no duplicate v2.4 line", text.count("**10.5281/zenodo.23614290**") == 1),
        ("supplement listed as 18 pages", "8 \u2192 18 pages, S1\u2013S43" in text),
        ("rebuild date recorded", "rebuilt 2026-10-24" in text),
    ]
    for name, ok in checks:
        print("  %s  %s" % ("PASS" if ok else "FAIL", name))
    if not all(ok for _, ok in checks):
        raise SystemExit("status doc checks failed")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    fix_letter(a.apply)
    fix_status(a.apply)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())