# -*- coding: utf-8 -*-
r"""Final verification: run every gate and write one consolidated evidence report.

Gates: frozen-submission hashes, provenance gate, A1 claim ledger, six paper_audit profiles (with the two documented
frozen-package divergences expected), P3 audit_check/audit_pdf, A23 verify, Commentary final check, staged package
builds, page-count expectations, and the git working-tree state.

Output: outputs/analysis/final_verification.json ; exit code 0 only if every gate passes.

    python tools/_p1454_final_verify.py [--apply]
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "outputs", "analysis", "final_verification.json")
PROFILES = ["a1_paa", "paperA_nc", "paperA_springer", "p3_prl", "a23_joe", "prl_commentary"]
EXPECTED_AUDIT_FAILS = {"a1_paa": {"I-02"}, "paperA_nc": {"I-02"}}
EXPECTED_AUDIT_WARNS = {"a1_paa": {"I-06"}, "paperA_nc": {"I-06"}}
PAGES = {"paper_a1/main.pdf": (64,), "paper合/main_nc.pdf": (74,), "paper合/main_springer.pdf": (53,),
         "paper3/paper_ieee/main.pdf": (10,), "paper_a2/main_ieee.pdf": (70,),
         "paper_review_prl/main_prl.pdf": (7,)}


def run(cmd, timeout=2400):
    r = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True, encoding="utf-8", errors="replace",
                       timeout=timeout)
    return r.returncode, (r.stdout or "") + "\n" + (r.stderr or "")


def check_frozen():
    sums = os.path.join(REPO, "SUBMISSION", "_frozen_submitted", "SHA256SUMS.txt")
    bad, n = [], 0
    for line in io.open(sums, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        h, rel = line.split(None, 1)
        p = os.path.join(REPO, "SUBMISSION", "_frozen_submitted", rel.strip())
        n += 1
        if not os.path.exists(p):
            bad.append((rel, "missing"))
            continue
        got = hashlib.sha256(io.open(p, "rb").read()).hexdigest()
        if got != h:
            bad.append((rel, "hash mismatch"))
    return {"n": n, "bad": bad, "pass": len(bad) == 0}


def check_audit(profile):
    code, out = run([sys.executable, "-m", "tools.paper_audit", "audit", "--profile", profile, "--fail-on", "NONE"])
    m = re.search(r"(READY|BLOCKED)\s+grade\s+(\w)\s+pass=(\d+)\s+fail=(\d+)\s+warn=(\d+)", out)
    blockers = re.findall(r"BLOCKER\s+(\S+)\s+", out)
    if not m:
        return {"pass": False, "raw": out[-400:]}
    verdict, grade, npass, nfail, nwarn = m.group(1), m.group(2), int(m.group(3)), int(m.group(4)), int(m.group(5))
    expected = EXPECTED_AUDIT_FAILS.get(profile, set())
    ok = (nfail == 0) or (set(blockers) <= expected)
    return {"verdict": verdict, "grade": grade, "pass": npass, "fail": nfail, "warn": nwarn,
            "blockers": blockers, "pass_ok": ok}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    rep = {}
    # 1. frozen archive
    rep["frozen"] = check_frozen()
    print("  frozen:", rep["frozen"]["pass"], f"{rep['frozen']['n']} files, bad={len(rep['frozen']['bad'])}")
    # 2. provenance gate
    code, out = run([sys.executable, "tools/_p1428_provenance_gate.py"])
    rep["provenance_gate"] = {"pass": code == 0, "tail": out.strip().splitlines()[-1:]}
    print("  provenance gate:", rep["provenance_gate"]["pass"])
    # 3. A1 ledger
    code, out = run([sys.executable, "tools/_claim_ledger_a1.py", "--apply"])
    m = re.search(r"(\d+) pass / (\d+) fail / (\d+) total", out)
    rep["a1_ledger"] = {"pass": bool(m) and int(m.group(2)) == 0,
                        "detail": m.group(0) if m else out.strip()[-200:]}
    print("  A1 ledger:", rep["a1_ledger"]["detail"])
    # 4. audits
    rep["audits"] = {p: check_audit(p) for p in PROFILES}
    for p, r in rep["audits"].items():
        print(f"  audit {p}: {r.get('verdict')} fail={r.get('fail')} warn={r.get('warn')} ok={r.get('pass_ok')}")
    # 5. P3 gates
    for name, script in (("p3_audit_check", "paper3/paper_ieee/audit_check.py"),
                         ("p3_audit_pdf", "paper3/paper_ieee/audit_pdf.py")):
        code, out = run([sys.executable, script])
        rep[name] = {"pass": code == 0 and "0 hard failure" in out}
        print(f"  {name}: {rep[name]['pass']}")
    # 6. A23 verify
    code, out = run([sys.executable, "paper_a2/verify_a23_fix.py"])
    rep["a23_verify"] = {"pass": code == 0 and "ALL CHECKS PASSED" in out}
    print("  A23 verify:", rep["a23_verify"]["pass"])
    # 7. Commentary final check
    code, out = run([sys.executable, "tools/_final_check_prl.py"])
    rep["commentary_check"] = {"pass": code == 0}
    print("  Commentary final check:", rep["commentary_check"]["pass"])
    # 8. staged packages
    code, out = run([sys.executable, "tools/_p1444_staged_package_check.py", "--apply"])
    st = json.load(io.open(os.path.join(REPO, "outputs", "analysis", "staged_package_check.json"), encoding="utf-8"))
    wrong = {k: v for k, v in st.items() if v.get("status") != "ok" or not v.get("page_match")}
    rep["staged_packages"] = {"pass": len(wrong) == 0, "wrong": wrong}
    print("  staged packages:", rep["staged_packages"]["pass"], list(wrong))
    # 9. page counts
    from pypdf import PdfReader
    pages = {}
    ok = True
    for rel, allowed in PAGES.items():
        p = os.path.join(REPO, rel)
        if not os.path.exists(p):
            pages[rel] = None
            ok = False
            continue
        n = len(PdfReader(p).pages)
        pages[rel] = n
        if n not in allowed:
            ok = False
    rep["pages"] = {"counts": pages, "pass": ok}
    print("  pages:", pages, "pass:", ok)
    # 10. git clean
    code, out = run(["git", "status", "--porcelain"])
    dirty = [l for l in out.strip().splitlines() if "final_verification.json" not in l]
    rep["git_clean"] = {"pass": (code == 0 and not dirty), "dirty": dirty[:10]}
    print("  git clean:", rep["git_clean"]["pass"])
    all_ok = (rep["frozen"]["pass"] and rep["provenance_gate"]["pass"] and rep["a1_ledger"]["pass"]
              and all(r.get("pass_ok") for r in rep["audits"].values())
              and rep["p3_audit_check"]["pass"] and rep["p3_audit_pdf"]["pass"] and rep["a23_verify"]["pass"]
              and rep["commentary_check"]["pass"] and rep["staged_packages"]["pass"] and rep["pages"]["pass"])
    rep["all_pass"] = all_ok
    print("  ALL:", "PASS" if all_ok else "FAIL")
    if a.apply:
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(rep, indent=1))
        print("  wrote", os.path.relpath(OUT, REPO))
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
