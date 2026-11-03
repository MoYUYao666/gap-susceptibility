# -*- coding: utf-8 -*-
"""Verify the Paper 3 audit gate and the post-fix build (2026-10-17 evening).

Runs the two audit scripts, records the page counts and SHA-256 digests, proves that
the copies under SUBMISSION/ (the 2026-10-15 submitted replacement) are still byte-for-byte
unchanged, and records how the local build now differs from them: the local sources were
fixed for the next revision (restored nabla in the abstract, breakable texttt paths), so
main.pdf/supplementary.pdf are no longer expected to equal the submitted copies.

    python tools/_p1172_verify_p3_audit.py [--apply]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
P3 = REPO / "paper3" / "paper_ieee"
OUT = REPO / "outputs" / "analysis" / "p3_audit_postfix_2026-10-17.json"
CORR = REPO / "SUBMISSION" / "P3_PRL_revision" / "CORRECTED_2026-10-15"
UPLOAD = REPO / "SUBMISSION" / "P3_PRL_revision" / "UPLOAD_2026-10-15"

FREEZE_PAIRS = [
    ("main", P3 / "main.pdf", CORR / "main_corrected.pdf",
     UPLOAD / "P3_PRLETTERS-D-26-02378_Manuscript.pdf"),
    ("supplement", P3 / "supplementary" / "supplementary.pdf",
     CORR / "supplementary_corrected.pdf",
     UPLOAD / "P3_PRLETTERS-D-26-02378_Supplementary.pdf"),
]

AUDITS = [("audit_check.py", P3 / "audit_check.py"), ("audit_pdf.py", P3 / "audit_pdf.py")]

# SHA-256 of the PDFs actually submitted with the 2026-10-15 replacement: these digit strings
# are the freeze of the submitted artefacts and must not change when the local build changes.
SUBMITTED_SHA = {
    "main": "b96f4dcb007b2e99c390ccb9aee9de7a57d347e947de0bd22ce684c517943010",
    "supplement": "e9b754e44d29392a4f021b625dc0902cd5c1736919000f4e0fa40bf5038c1031",
}

FAILS: list[str] = []
WARNS: list[str] = []


def fail(msg: str) -> None:
    print("FAIL  " + msg)
    FAILS.append(msg)


def ok(msg: str) -> None:
    print("PASS  " + msg)


def warn(msg: str) -> None:
    print("WARN  " + msg)
    WARNS.append(msg)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def pages(path: Path) -> int:
    out = subprocess.run(["pdfinfo", str(path)], capture_output=True, check=True).stdout.decode("utf-8", "ignore")
    m = re.search(r"^Pages:\s+(\d+)", out, re.M)
    if not m:
        raise RuntimeError(f"pdfinfo did not report pages for {path}")
    return int(m.group(1))


def run_audit(name: str, path: Path) -> dict:
    proc = subprocess.run([sys.executable, path.name], cwd=P3, capture_output=True, text=True)
    out = proc.stdout
    counts = {
        "pass": len(re.findall(r"^PASS ", out, re.M)),
        "fail": len(re.findall(r"^FAIL ", out, re.M)),
        "warn": len(re.findall(r"^WARN ", out, re.M)),
    }
    summary = [ln.strip() for ln in out.splitlines() if ln.strip().startswith("RESULT:")]
    record = {
        "script": name,
        "exit_code": proc.returncode,
        "counts": counts,
        "summary": summary[-1] if summary else "",
        "tail": out.strip().splitlines()[-6:],
    }
    if proc.returncode == 0 and counts["fail"] == 0:
        ok(f"{name}: exit 0, {counts['pass']} PASS / {counts['fail']} FAIL / {counts['warn']} WARN")
    else:
        fail(f"{name}: exit {proc.returncode}, {counts['pass']} PASS / {counts['fail']} FAIL")
        if proc.stderr.strip():
            print(proc.stderr.strip()[-800:])
    return record


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="write the evidence JSON")
    a = ap.parse_args()

    print("=" * 72)
    print("P3 frozen-submission audit verification")
    print("=" * 72)

    audits = {name: run_audit(name, path) for name, path in AUDITS}

    evidence: dict = {"generated_at": "2026-10-17", "audits": audits, "pdfs": {}, "freeze": {}}

    # Page counts of the working tree PDFs.
    for label, path, expect in (
        ("main.pdf", P3 / "main.pdf", 10),
        ("main_full.pdf", P3 / "main_full.pdf", 13),
        ("supplementary.pdf", P3 / "supplementary" / "supplementary.pdf", 6),
    ):
        if not path.exists():
            fail(f"missing PDF: {path.relative_to(REPO)}")
            continue
        n = pages(path)
        evidence["pdfs"][label] = {"path": str(path.relative_to(REPO)), "pages": n, "expected": expect}
        if n == expect:
            ok(f"{label}: {n} pages")
        else:
            fail(f"{label}: {n} pages, expected {expect}")

    # Freeze of the submitted artefacts: the copies under SUBMISSION/ must be unchanged.
    # The local build is now the next-revision build and is expected to differ.
    for label, working, corrected, upload in FREEZE_PAIRS:
        if not working.exists():
            fail(f"missing working PDF for {label}")
            continue
        digest = sha256(working)
        entry = {"working": {"path": str(working.relative_to(REPO)), "sha256": digest, "bytes": working.stat().st_size},
                 "submitted_sha": SUBMITTED_SHA[label]}
        for tag, other in (("corrected", corrected), ("upload", upload)):
            if other.exists():
                od = sha256(other)
                entry[tag] = {"path": str(other.relative_to(REPO)), "sha256": od, "bytes": other.stat().st_size}
                if od == SUBMITTED_SHA[label]:
                    ok(f"{label}: submitted {tag} copy unchanged")
                else:
                    fail(f"{label}: submitted {tag} copy CHANGED (was {SUBMITTED_SHA[label][:16]}...)")
            else:
                warn(f"{label}: {tag} copy absent ({other})")
        if digest == SUBMITTED_SHA[label]:
            ok(f"{label}: local build identical to the submitted copy")
            entry["drift"] = False
        else:
            entry["drift"] = True
            print(f"INFO  {label}: local build differs from the submitted copy (expected: editorial fixes for the next revision)")
        evidence["freeze"][label] = entry

    summary = {
        "hard_failures": len(FAILS),
        "warnings": len(WARNS),
        "audits_pass": all(rec["exit_code"] == 0 and rec["counts"]["fail"] == 0 for rec in audits.values()),
    }
    evidence["summary"] = summary

    print("-" * 72)
    print(f"RESULT: {len(FAILS)} hard failure(s), {len(WARNS)} warning(s)")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(evidence, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
        print(f"evidence written: {OUT.relative_to(REPO)}")
    else:
        print("(dry run; pass --apply to write the evidence JSON)")

    return 0 if not FAILS else 1


if __name__ == "__main__":
    raise SystemExit(main())
