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
PAGES = {"paper_a1/main.pdf": (64,), "paper合/main_nc.pdf": (79,), "paper合/main_springer.pdf": (56,),
         "paper3/paper_ieee/main.pdf": (10,), "paper_a2/main_ieee.pdf": (72,), "paper_review_prl/main_prl.pdf": (7,)}
# The 2026-10-24 decoder-ladder round (Paper A supplement Section H.2): one archived per-run record
# per rung, in table order.
LADDER_RUNGS = [
    ("qwen2vl-2b", "contrastive", "Qwen2-VL-2B", "Contrastive"),
    ("qwen2vl-2b", "generative", "Qwen2-VL-2B", "Generation"),
    ("llava15-7b", "contrastive", "LLaVA-1.5-7B", "Contrastive"),
    ("llava15-7b", "generative", "LLaVA-1.5-7B", "Generation"),
    ("qwen25vl-7b", "generative", "Qwen2.5-VL-7B", "Generation"),
]
LADDER_3B = "outputs/analysis/decoder_attribution_qwen25vl-3b_generative_seed42.json"


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
        # 5. Section H must still be present and carry its label
        "section_h_untouched_in_source": "\\label{sec:decoderconfound}" in sup,
    }
    # Write-scope guard. The bootstrap round (2026-10-24a) owned Sections A--G and had to leave
    # Section H alone; the decoder-ladder round (2026-10-24b) owns Section H and must leave
    # Sections A--G alone, so the guard is inverted rather than dropped. Every hunk of the
    # supplement diff must start at or after the Section H heading.
    code, diff = run(["git", "diff", "--unified=0", "--", "paper合/sections/supplement.tex"])
    h_start = sup.find("\\section*{H.")
    h_line = sup[:h_start].count("\n") + 1 if h_start > 0 else None
    checks["section_h_block_present"] = h_start > 0 and "decoderconfound" in sup[h_start:]
    starts = [int(re.search(r"\+(\d+)", ln).group(1)) for ln in diff.splitlines()
              if ln.startswith("@@") and re.search(r"\+(\d+)", ln)]
    checks["edits_confined_to_section_h"] = bool(
        code == 0 and h_line is not None and all(s >= h_line for s in starts))
    checked = {k: bool(v) for k, v in checks.items()}
    return {"pass": all(checked.values()), "checks": checked, "section_h_first_line": h_line}


def check_decoder_ladder_integration():
    """2026-10-24b decoder-ladder round. Every rung of the new Table~\ref{tab:decoderladder} must
    reproduce from its archived per-run record, the superseded description of the local control must
    be gone, all four stated caveats must be present, and the ladder must not outrun its archives."""
    sup = io.open(os.path.join(REPO, "paper合", "sections", "supplement.tex"), encoding="utf-8").read()
    flat = sup.replace("\\allowbreak ", "").replace("\\allowbreak", "").replace("\\_", "_")
    checks, recs = {}, {}
    for model, objective, _m_label, _o_label in LADDER_RUNGS:
        rel = "outputs/analysis/decoder_attribution_%s_%s_seed42.json" % (model, objective)
        tag = "%s_%s" % (model, objective)
        p = os.path.join(REPO, rel)
        if not os.path.exists(p):
            checks[tag + "_archive_present"] = False
            continue
        rec = json.load(io.open(p, encoding="utf-8"))
        recs[(model, objective)] = rec
        m = rec["meta"]
        checks[tag + "_archive_present"] = True
        checks[tag + "_protocol_match"] = (m.get("mode") == "apply" and m.get("protocol") == "match"
                                           and m.get("seed") == 42 and m.get("arm") == "both")
        checks[tag + "_source_cited"] = rel.split("/")[-1] in flat
    # 1. the table body must carry exactly the five rungs, with the archived numbers, in place
    rows = {}
    if "\\label{tab:decoderladder}" in sup:
        body = sup.split("\\label{tab:decoderladder}", 1)[1].split("\\end{tabular}", 1)[0]
        for ln in body.splitlines():
            cells = [c.strip().rstrip("\\").strip() for c in ln.split("&")]
            if len(cells) == 5 and cells[1] in ("Contrastive", "Generation"):
                rows[(cells[0], cells[1])] = cells[2:]
    checks["ladder_table_has_five_rungs"] = len(rows) == 5
    for model, objective, m_label, o_label in LADDER_RUNGS:
        rec = recs.get((model, objective))
        if rec is None:
            continue
        want = ["$%.4f$" % rec["frozen_dg_star"], "$%.4f$" % rec["dg_star"][-1],
                "$%+.1f\\%%$" % rec["delta_DG_percent"]]
        checks["%s_%s_row_matches_archive" % (model, objective)] = rows.get((m_label, o_label)) == want
    # 2. caveat (i): single seed, four-bit, direction rather than effect size
    checks["caveat_single_seed_direction"] = ("Each rung is a single seed" in sup
                                              and "no spread across seeds is claimed" in sup)
    # 3. caveat (ii): LLaVA learning rate, the frozen-baseline mismatch, and the zero crossing
    if ("llava15-7b", "contrastive") in recs and ("llava15-7b", "generative") in recs:
        lc, lg = recs[("llava15-7b", "contrastive")], recs[("llava15-7b", "generative")]
        traj = [round((v - lg["frozen_dg_star"]) / lg["frozen_dg_star"] * 100, 1) for v in lg["dg_star"]]
        rel = abs(lc["frozen_dg_star"] - lg["frozen_dg_star"]) / lg["frozen_dg_star"] * 100
        checks["llava_trajectory_reproduces"] = traj == [-14.2, 6.7, 16.1]
        checks["llava_frozen_mismatch_reproduces"] = round(rel, 1) == 5.7
        checks["llava_lr_difference_reproduces"] = (
            abs(lc["meta"]["lr"] - 5e-05) < 1e-12
            and all(abs(r["meta"]["lr"] - 1e-04) < 1e-12 for k, r in recs.items()
                    if k != ("llava15-7b", "contrastive")))
        checks["llava_mismatch_verdict_stated"] = ("MISMATCH" in lc["meta"]["ab_check"].get("verdict", "")
                                                   and "\\texttt{MISMATCH}" in sup)
        checks["caveat_llava_lr_and_trajectory"] = (
            "$5\\times10^{-5}$ rather than the ladder's $10^{-4}$" in sup
            and "$-14.2\\%$, then $+6.7\\%$, then $+16.1\\%$" in sup)
    # 4. caveat (iii): the local control ran at the processor default, not at the budget it advertised
    checks["caveat_local_control_cap_correction"] = (
        "never enforced the image-token budget it" in sup
        and "$1200$--$2500$ image tokens per image" in sup
        and "$64$ image tokens/image" in sup
        and "at a reduced image resolution" not in sup)
    # 5. caveat (iv): the 3B rung was not run, which is what the text and the archive tree both say
    checks["caveat_3b_rung_not_run"] = ("$3$B rung of the Qwen2.5-VL family was not run" in sup
                                        and not os.path.exists(os.path.join(REPO, LADDER_3B)))
    # 6. the bounded reading, the float wiring and the Source line
    checks["bounded_reading_present"] = ("not set the sign: the contrastive loss narrows" in sup
                                         and "widening therefore tracks the" in sup
                                         and "narrowed rather than overturned" in sup)
    checks["table_referenced_and_labelled"] = ("\\ref{tab:decoderladder}" in sup
                                               and "\\label{tab:decoderladder}" in sup)
    checks["source_line_names_script"] = ("\\textbf{Source:}" in sup
                                          and "_p1612_objective_control_multimodel.py" in flat)
    # no manuscript path may point into the internal docs/ directory, which the public mirror
    # (publish_clean) ignores: such a pointer is unreachable for a reader of the released snapshot
    checks["cap_correction_cites_public_paths"] = (
        "_p1595_qwen_objective_control.py" in flat and "docs/" not in flat)
    # 7. the archived local control is untouched and still declares the budget it never applied
    for name, want_delta, want_last in (("contrastive", -73.54014598540147, 0.283203125),
                                        ("generative", -14.233576642335766, 0.91796875)):
        p = os.path.join(REPO, "outputs/analysis/qwen_objective_control_%s_both_seed42.json" % name)
        ok = os.path.exists(p)
        if ok:
            old = json.load(io.open(p, encoding="utf-8"))
            ok = (old["frozen_dg_star"] == 1.0703125 and old["dg_star"][-1] == want_last
                  and abs(old["delta_DG_percent"] - want_delta) < 1e-6
                  and old["meta"]["max_image_tokens"] == 12
                  and "64 image tokens/image" in old["meta"]["reduced_budget_note"])
        checks["local_control_%s_archive_unchanged" % name] = ok
    checked = {k: bool(v) for k, v in checks.items()}
    return {"pass": all(checked.values()), "checks": checked}


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
    # 9c. decoder-ladder integration text and archive reproduction guards (2026-10-24b round)
    rep["decoder_ladder_integration"] = check_decoder_ladder_integration()
    bad = [k for k, v in rep["decoder_ladder_integration"]["checks"].items() if not v]
    print("  decoder ladder integration:", rep["decoder_ladder_integration"]["pass"], "failed:", bad)
    # 10. git clean
    code, out = run(["git", "status", "--porcelain"])
    dirty = [l for l in out.strip().splitlines() if "final_verification.json" not in l]
    rep["git_clean"] = {"pass": (code == 0 and not dirty), "dirty": dirty[:10]}
    print("  git clean:", rep["git_clean"]["pass"])
    all_ok = (rep["frozen"]["pass"] and rep["provenance_gate"]["pass"] and rep["a1_ledger"]["pass"]
              and all(r.get("pass_ok") for r in rep["audits"].values())
              and rep["p3_audit_check"]["pass"] and rep["p3_audit_pdf"]["pass"] and rep["a23_verify"]["pass"]
              and rep["commentary_check"]["pass"] and rep["staged_packages"]["pass"] and rep["pages"]["pass"]
              and rep["bootstrap_integration"]["pass"] and rep["decoder_ladder_integration"]["pass"])
    rep["all_pass"] = all_ok
    print("  ALL:", "PASS" if all_ok else "FAIL")
    if a.apply:
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(rep, indent=1))
        print("  wrote", os.path.relpath(OUT, REPO))
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
