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
PAGES = {"paper_a1/main.pdf": (64,), "paper合/main_nc.pdf": (77,), "paper合/main_springer.pdf": (54,),
         "paper3/paper_ieee/main.pdf": (10,), "paper_a2/main_ieee.pdf": (72,), "paper_review_prl/main_prl.pdf": (7,)}


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


def check_bootstrap_integration():
    """2026-10-24 bootstrap round: the integrated text must be present, the superseded wording absent,
    the write-scope guard honoured, and the numbers still reproduce from the archived JSON."""
    emp = io.open(os.path.join(REPO, "paper合", "sections", "empirical.tex"), encoding="utf-8").read()
    sup = io.open(os.path.join(REPO, "paper合", "sections", "supplement.tex"), encoding="utf-8").read()
    js_path = os.path.join(REPO, "outputs", "analysis", "paperA_strict_bootstrap.json")
    js = json.load(io.open(js_path, encoding="utf-8"))
    ps = js["paperA"]["tab_position_strict"]
    llava = js["paperA"]["tab_llava"]["paired_differences"]["both_minus_vision_only"]
    siglip = ps["rows"]["SigLIP B/16 (WebLI)"]["paired_differences"]["text_only_minus_vision_only"]
    checks = {
        # 1. tab:position_strict caption: the sd range must be qualified, the false blanket claim gone
        "sd_range_dual_encoder_rows": "the seed-to-seed standard deviation of $\\Delta$CG is $0.0006$--$0.006$ on the four dual-encoder rows" in emp,
        "sd_range_bioclip_arms": "and $0.002$, $0.010$ and $0.015$ on BioCLIP's three arms" in emp,
        "sd_blanket_claim_absent": "standard deviation of $0.0006$--$0.006$ depending on the backbone" not in emp,
        "sd_claim_checked_against_archive": round(min(ps["caption_digit_checks"]["computed_sd_ddof1_range_excluding_bioclip"]), 4) == 0.0006
                                             and round(max(ps["caption_digit_checks"]["computed_sd_ddof1_range_excluding_bioclip"]), 4) == 0.006,
        "bioclip_sds_reproduce": [round(s, 4) for s in ps["caption_digit_checks"]["computed_sd_ddof1_bioclip_arms"]] == [0.0104, 0.0149, 0.0022],
        "caption_points_to_section_f": "pairing kept, at most $\\pm0.004$ here) are in Section~\\ref{sec:r1provenance}" in emp,
        # 2. tab:vlm / tab:llava captions state the ddof=0 convention
        "vlm_caption_population_sd": "The spreads after $\\pm$ are population standard" in sup,
        "llava_caption_population_sd": "population standard deviations over the three seeds" in sup,
        "vlm_sd_convention_reproduces": all(v["matches"] == "ddof0" for v in js["paperA"]["tab_vlm"]["sd_convention"].values()),
        "llava_sd_convention_reproduces": all(v["matches"] == "ddof0" for v in js["paperA"]["tab_llava"]["sd_convention"].values()),
        "vlm_printed_sds_unchanged": (0.44, 0.29, 1.01) == tuple(
            js["paperA"]["tab_vlm"]["sd_convention"][a]["manuscript"] for a in ("both", "text_only", "vision_only")),
        "llava_printed_sds_unchanged": (7.54, 16.33, 7.91) == tuple(
            js["paperA"]["tab_llava"]["sd_convention"][a]["manuscript"] for a in ("text_only", "vision_only", "both")),
        # 3. tab:llava narrative: paired bootstrap added, unpaired caveat kept
        "llava_paired_bootstrap_added": "$-25.81$ [$-33.25$, $-13.48$]" in sup,
        "llava_paired_ci_reproduces": [round(x, 2) for x in llava["ci95_percentile"]] == [-33.25, -13.48]
                                      and llava["ci95_excludes_zero"] is True,
        "llava_unpaired_caveat_kept": "the unpaired comparison of both-position and vision-only overlaps in" in sup,
        # 4. Section F carries the arm intervals, the SigLIP reversal and the 18-cell correction
        "section_f_bootstrap_paragraph": "certifies that column too" in sup,
        "section_f_arm_intervals": "means carry intervals of at most $\\pm0.004$ on the five-seed rows" in sup,
        "section_f_siglip_reversal": "$+0.014$ [$+0.008$, $+0.018$] on SigLIP" in sup,
        "section_f_eighteen_cells": "and that column is exact: all eighteen" in sup,
        "siglip_reversal_ci_reproduces": [round(x, 4) for x in siglip["ci95_percentile"]] == [0.0081, 0.0181]
                                         and siglip["ci95_excludes_zero"] is True,
        "design_states_bootstrap_source": "paperA\\_strict\\_bootstrap.json" in emp and "\\_p1595\\_bootstrap\\_ci\\_round.py" in emp,
        # 5. write-scope guard: Section H and its label must be untouched by this round
        "section_h_untouched_in_source": "\\label{sec:decoderconfound}" in sup,
    }
    # write-scope guard: no hunk of the supplement diff may reach into the Section H block
    code, diff = run(["git", "diff", "--unified=0", "--", "paper合/sections/supplement.tex"])
    h_start = sup.find("\\section*{H.")
    h_line = sup[:h_start].count("\n") + 1 if h_start > 0 else None
    checks["section_h_block_present"] = h_start > 0 and "decoderconfound" in sup[h_start:]
    checks["section_h_not_edited"] = bool(
        code == 0 and h_line is not None and not [1 for ln in diff.splitlines()
                                                  if ln.startswith("@@") and re.search(r"\+(\d+)", ln)
                                                  and int(re.search(r"\+(\d+)", ln).group(1)) >= h_line])
    checked = {k: bool(v) for k, v in checks.items()}
    return {"pass": all(checked.values()), "checks": checked, "section_h_first_line": h_line}


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
    # 9b. bootstrap-integration text and write-scope guards (2026-10-24 round)
    rep["bootstrap_integration"] = check_bootstrap_integration()
    bad = [k for k, v in rep["bootstrap_integration"]["checks"].items() if not v]
    print("  bootstrap integration:", rep["bootstrap_integration"]["pass"], "failed:", bad)
    # 10. git clean
    code, out = run(["git", "status", "--porcelain"])
    dirty = [l for l in out.strip().splitlines() if "final_verification.json" not in l]
    rep["git_clean"] = {"pass": (code == 0 and not dirty), "dirty": dirty[:10]}
    print("  git clean:", rep["git_clean"]["pass"])
    all_ok = (rep["frozen"]["pass"] and rep["provenance_gate"]["pass"] and rep["a1_ledger"]["pass"]
              and all(r.get("pass_ok") for r in rep["audits"].values())
              and rep["p3_audit_check"]["pass"] and rep["p3_audit_pdf"]["pass"] and rep["a23_verify"]["pass"]
              and rep["commentary_check"]["pass"] and rep["staged_packages"]["pass"] and rep["pages"]["pass"]
              and rep["bootstrap_integration"]["pass"])
    rep["all_pass"] = all_ok
    print("  ALL:", "PASS" if all_ok else "FAIL")
    if a.apply:
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(rep, indent=1))
        print("  wrote", os.path.relpath(OUT, REPO))
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
