# -*- coding: utf-8 -*-
r"""Final verification: run every gate and write one consolidated evidence report.

Gates: frozen-submission hashes, provenance gate, A1 claim ledger, six paper_audit profiles,
P3 audit_check/audit_pdf, A23 verify, Commentary final check, staged package builds (with a
freshness check against the live drafts), page-count expectations, and the git working-tree
state.

VERDICT SEMANTICS (hardened 2026-10-25; audit A findings D-2..D-5):
  PASS                  every hard gate passed and nothing is reported.
  PASS WITH N WARNING(S) every hard gate passed, but N deviations are REPORTED: accepted
                        package-vs-live lags (named, with the package snapshot date and the
                        reason), per-profile audit warnings, a dirty git tree, stale staged
                        package snapshots.  Warnings never hide a failure and the verdict
                        never reads a bare PASS.
  FAIL                  at least one hard gate failed, or an audit blocker is not covered by
                        an explicitly declared accepted deviation.
  A bare "ALL: PASS" next to "git clean: False" is impossible: the final line always carries
  the warning count and the dirty-path count.

Accepted deviations live in ACCEPTED_DEVIATIONS (reason + package); each is resolved to the
package's actual snapshot date at run time and counted as a warning.  `--no-accepted-deviations`
turns every acceptance into a hard failure (shows the strict reading of the same tree).

Output: outputs/analysis/final_verification.json ; exit code 0 iff there is no hard failure.

    python tools/_p1454_final_verify.py [--apply] [--no-accepted-deviations]
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
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "outputs", "analysis", "final_verification.json")
PROFILES = ["a1_paa", "paperA_nc", "paperA_springer", "p3_prl", "a23_joe", "prl_commentary"]
PAGES = {
    "paper_a1/main.pdf": (64,),
    "paper合/main_nc.pdf": (79,),
    "paper合/main_springer.pdf": (56,),
    "paper3/paper_ieee/main.pdf": (10,),
    # 2026-10-28: moving the table captions above the bodies added one page to the A23 manuscript
    "paper_a2/main_ieee.pdf": (74,),
    "paper_review_prl/main_prl.pdf": (7,),
}

# D-2 fix: a frozen submission/revision package may legitimately lag the live draft (the
# submitted version is what is under review while the local draft keeps moving).  Such a lag
# must never be absorbed silently.  Every acceptance is NAMED here with the reason and the
# package directory; at run time it is resolved to the package's actual snapshot date and is
# reported as a WARNING in the verdict line.  Any blocker NOT listed here is a hard failure.
# 2026-10-25: both entries resolve to 0 deviations because both packages are byte-synced to
# their live PDFs -- the channel exists only for the legitimate frozen-package-lag case.
ACCEPTED_DEVIATIONS = {
    "a1_paa": {
        "checks": {"I-02"},
        "package": "SUBMISSION/A1_PatternAnalysisApplications",
        "reason": ("the PAA submission (received 2026-10-18) is under review; its package is "
                   "frozen at the snapshot date resolved below, while the local draft is being "
                   "revised, so package-vs-live divergence is legitimate here"),
    },
    "paperA_nc": {
        "checks": {"I-02"},
        "package": "SUBMISSION/PaperA_Neurocomputing",
        "reason": ("the Neurocomputing submission NEUCOM-D-26-23760 (With Editor since "
                   "2026-10-19) is under review; its package is frozen at the snapshot date "
                   "resolved below, while the local draft is being revised"),
    },
}

# D-5 fix: staged package -> live manuscript PDF, used by the freshness check.
STAGED_TO_LIVE = {
    "A1_PAA_next": "paper_a1/main.pdf",
    "A23_JOE_next": "paper_a2/main_ieee.pdf",
    "Commentary_PRL_next": "paper_review_prl/main_prl.pdf",
    "P3_PRL_next": "paper3/paper_ieee/main.pdf",
    "PaperA_Neurocomputing_next": "paper合/main_nc.pdf",
}
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


def git_head():
    """(short hash, commit time, subject) of HEAD, or None outside a repo."""
    code, out = run(["git", "log", "-1", "--format=%h %ci %s"])
    return out.strip() if code == 0 and out.strip() else None


def package_snapshot(package_rel):
    """Newest mtime + file count of a package directory -> the package's snapshot date."""
    root = os.path.join(REPO, package_rel)
    newest, n = 0.0, 0
    for dirpath, _dirnames, filenames in os.walk(root):
        for fn in filenames:
            try:
                m = os.path.getmtime(os.path.join(dirpath, fn))
            except OSError:
                continue
            newest = max(newest, m)
            n += 1
    if not n:
        return {"exists": False, "package": package_rel}
    return {"exists": True, "package": package_rel, "n_files": n,
            "newest_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(newest)),
            "newest_local": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(newest))}


def classify_audit_result(profile, nfail, blockers, no_accepted=False):
    """Split one profile's audit result into (hard_failures, accepted_deviations).

    Hard rule (D-2): nfail > 0 passes ONLY when every BLOCKER id is covered by an explicitly
    declared ACCEPTED_DEVIATIONS entry and acceptances are switched on.  A profile that
    reports failures without a parsable blocker id is always a hard failure, because the
    failure cannot be named, classified or accepted.
    """
    hard, accepted = [], []
    if nfail <= 0:
        return hard, accepted
    if not blockers:
        hard.append({"profile": profile, "check": "?", "n_fail": nfail,
                     "why": "audit reports %d failure(s) but no BLOCKER id could be parsed, "
                            "so the failure can be neither classified nor accepted" % nfail})
        return hard, accepted
    spec = {} if no_accepted else ACCEPTED_DEVIATIONS.get(profile, {})
    covered = set(spec.get("checks", set()))
    snap = package_snapshot(spec["package"]) if spec else None
    for cid in blockers:
        if cid in covered:
            accepted.append({"profile": profile, "check": cid, "package": spec["package"],
                             "package_snapshot": snap, "reason": spec["reason"]})
        else:
            hard.append({"profile": profile, "check": cid, "n_fail": nfail,
                         "why": "hard failure not covered by any accepted deviation"})
    return hard, accepted


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


def check_audit(profile, no_accepted=False):
    code, out = run([sys.executable, "-m", "tools.paper_audit", "audit", "--profile", profile, "--fail-on", "NONE"])
    m = re.search(r"(READY|BLOCKED)\s+grade\s+(\w)\s+pass=(\d+)\s+fail=(\d+)\s+warn=(\d+)", out)
    blockers = re.findall(r"BLOCKER\s+(\S+)\s+", out)
    if not m:
        return {"pass": False, "rc": code, "raw": out[-400:], "warn_findings": [],
                "hard_failures": [{"profile": profile, "check": "?",
                                   "why": "audit output could not be parsed (rc=%s)" % code}],
                "accepted_deviations": []}
    verdict, grade, npass, nfail, nwarn = (m.group(1), m.group(2), int(m.group(3)),
                                           int(m.group(4)), int(m.group(5)))
    hard, accepted = classify_audit_result(profile, nfail, blockers, no_accepted)
    # D-3: the warn channel is now real -- read the exact WARN findings from the report the
    # audit just wrote, so every warning is named in the verdict line instead of being dropped.
    warn_findings = []
    jm = re.search(r"^json:\s+(\S+\.json)\s*$", out, re.M)
    mm = re.search(r"^markdown:\s+(\S+\.md)\s*$", out, re.M)
    report_paths = [os.path.relpath(p, REPO) for p in
                    ([jm.group(1)] if jm else []) + ([mm.group(1)] if mm else [])]
    if jm:
        try:
            aj = json.load(io.open(jm.group(1), encoding="utf-8"))
            warn_findings = [{"check": f.get("check_id"), "severity": f.get("severity"),
                              "title": f.get("title"),
                              "message": (f.get("message") or "")[:240]}
                             for f in aj.get("findings", []) if f.get("status") == "WARN"]
        except Exception:  # noqa: BLE001
            warn_findings = []
    return {"verdict": verdict, "grade": grade, "pass": npass, "fail": nfail, "warn": nwarn,
            "blockers": blockers, "rc": code, "pass_ok": not hard,
            "hard_failures": hard, "accepted_deviations": accepted,
            "warn_findings": warn_findings, "report_paths": report_paths}


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


def check_staged_freshness(st):
    """D-5 fix: record each staged package's snapshot and compare it with the live draft.

    The staged-package gate compiles `SUBMISSION/_venue_builds/<pkg>/latex_source.zip` and
    compares the result with the *same directory's* shipped PDF.  Both sides come from one
    snapshot, so the comparison can never notice that the manuscript has moved on.  This
    function makes the snapshot explicit: it re-measures the shipped PDF, compares the page
    count with the live manuscript, and emits a WARNING for every package whose snapshot is
    older than the live draft.  A `PASS` can therefore no longer be stale silently.
    """
    from pypdf import PdfReader
    rows, warns = {}, []
    for pkg, live_rel in STAGED_TO_LIVE.items():
        shipped = os.path.join(REPO, "SUBMISSION", "_venue_builds", pkg, "Manuscript.pdf")
        live = os.path.join(REPO, live_rel)
        row = {"package": pkg, "live": live_rel,
               "shipped_pdf": os.path.relpath(shipped, REPO) if os.path.exists(shipped) else None}
        if not os.path.exists(shipped) or not os.path.exists(live):
            row["status"] = "missing"
            rows[pkg] = row
            warns.append({"code": "staged_missing", "package": pkg,
                          "detail": "staged or live PDF missing (%s / %s)" % (shipped, live)})
            continue
        smt, lmt = os.path.getmtime(shipped), os.path.getmtime(live)
        sp, lp = len(PdfReader(shipped).pages), len(PdfReader(live).pages)
        rec = (st.get(pkg) or {}).get("shipped_pages")
        row.update({
            "status": "ok",
            "shipped_snapshot_local": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(smt)),
            "live_pdf_local": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(lmt)),
            "shipped_pages_actual": sp, "live_pages": lp, "recorded_shipped_pages": rec,
        })
        if sp != lp:
            warns.append({"code": "stale_staged_snapshot", "package": pkg,
                          "detail": "staged snapshot (%s) has %d pages but the live draft %s has "
                                    "%d pages" % (row["shipped_snapshot_local"], sp, live_rel, lp)})
        if rec is not None and rec != sp:
            warns.append({"code": "stale_staged_record", "package": pkg,
                          "detail": "staged_package_check.json records %s shipped pages but the "
                                    "staged PDF now has %d" % (rec, sp)})
        if lmt > smt + 3600:
            warns.append({"code": "live_draft_newer_than_staged", "package": pkg,
                          "detail": "live draft %s is newer than the staged snapshot (%s vs %s)"
                                    % (live_rel, row["live_pdf_local"],
                                       row["shipped_snapshot_local"])})
        rows[pkg] = row
    return {"rows": rows, "warnings": warns, "n_warnings": len(warns)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--no-accepted-deviations", action="store_true",
                    help="treat every audit blocker as a hard failure (shows the strict reading "
                         "of the same tree; the accepted-deviation channel is switched off)")
    a = ap.parse_args()
    t0 = time.time()
    rep = {
        "script": "tools/_p1454_final_verify.py",
        "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "head_at_start": git_head(),
        "accepted_deviations_enabled": not a.no_accepted_deviations,
    }
    hard, warns, accepted = [], [], []

    def add_hard(code, detail, **extra):
        hard.append({"code": code, "detail": detail, **extra})

    def add_warn(code, detail, **extra):
        warns.append({"code": code, "detail": detail, **extra})

    # 1. frozen archive
    rep["frozen"] = check_frozen()
    print("  frozen:", rep["frozen"]["pass"], f"{rep['frozen']['n']} files, bad={len(rep['frozen']['bad'])}")
    if not rep["frozen"]["pass"]:
        add_hard("frozen_archive", "%d frozen file(s) changed or missing: %s"
                 % (len(rep["frozen"]["bad"]), rep["frozen"]["bad"][:6]))
    # 2. provenance gate
    code, out = run([sys.executable, "tools/_p1428_provenance_gate.py"])
    rep["provenance_gate"] = {"pass": code == 0, "tail": out.strip().splitlines()[-1:]}
    print("  provenance gate:", rep["provenance_gate"]["pass"])
    if code != 0:
        add_hard("provenance_gate", "tools/_p1428_provenance_gate.py exited %d: %s"
                 % (code, out.strip().splitlines()[-1:]))
    # 3. A1 ledger
    code, out = run([sys.executable, "tools/_claim_ledger_a1.py", "--apply"])
    m = re.search(r"(\d+) pass / (\d+) fail / (\d+) total", out)
    rep["a1_ledger"] = {"pass": bool(m) and int(m.group(2)) == 0,
                        "detail": m.group(0) if m else out.strip()[-200:]}
    print("  A1 ledger:", rep["a1_ledger"]["detail"])
    if not rep["a1_ledger"]["pass"]:
        add_hard("a1_ledger", "A1 claim ledger failed: %s" % rep["a1_ledger"]["detail"])
    # 4. audits (D-2/D-3: hard failures vs named accepted deviations vs reported warnings)
    rep["audits"] = {p: check_audit(p, a.no_accepted_deviations) for p in PROFILES}
    for p, r in rep["audits"].items():
        print(f"  audit {p}: {r.get('verdict')} fail={r.get('fail')} warn={r.get('warn')} ok={r.get('pass_ok')}")
        hard.extend(r.get("hard_failures") or [])
        accepted.extend(r.get("accepted_deviations") or [])
        for wf in (r.get("warn_findings") or []):
            add_warn("audit_warn:%s:%s" % (p, wf.get("check")),
                     "%s %s (%s): %s" % (p, wf.get("check"), wf.get("severity"),
                                         (wf.get("title") or "")[:120]))
        if r.get("warn") and not r.get("warn_findings"):
            add_warn("audit_warn:%s" % p,
                     "%d warning(s) reported by the audit (details unavailable)" % r["warn"])
    # 5. P3 gates
    for name, script in (("p3_audit_check", "paper3/paper_ieee/audit_check.py"),
                         ("p3_audit_pdf", "paper3/paper_ieee/audit_pdf.py")):
        code, out = run([sys.executable, script])
        rep[name] = {"pass": code == 0 and "0 hard failure" in out}
        print(f"  {name}: {rep[name]['pass']}")
        if not rep[name]["pass"]:
            add_hard(name, "%s failed (rc=%d): %s" % (script, code,
                                                      out.strip().splitlines()[-2:]))
    # 6. A23 verify
    code, out = run([sys.executable, "paper_a2/verify_a23_fix.py"])
    rep["a23_verify"] = {"pass": code == 0 and "ALL CHECKS PASSED" in out}
    print("  A23 verify:", rep["a23_verify"]["pass"])
    if not rep["a23_verify"]["pass"]:
        add_hard("a23_verify", "paper_a2/verify_a23_fix.py failed (rc=%d)" % code)
    # 7. Commentary final check
    code, out = run([sys.executable, "tools/_final_check_prl.py"])
    rep["commentary_check"] = {"pass": code == 0}
    print("  Commentary final check:", rep["commentary_check"]["pass"])
    if not rep["commentary_check"]["pass"]:
        add_hard("commentary_check", "tools/_final_check_prl.py exited %d" % code)
    # 8. staged packages (D-5: the exit code is kept, the evidence JSON is re-checked for
    #    completeness, and the snapshot freshness is measured against the live drafts)
    code, out = run([sys.executable, "tools/_p1444_staged_package_check.py", "--apply"])
    rep["staged_packages"] = {"rc": code, "pass": False, "wrong": {}, "missing_packages": []}
    if code != 0:
        add_hard("staged_package_check_rc",
                 "tools/_p1444_staged_package_check.py exited %d, so its JSON evidence cannot "
                 "be trusted (tail: %s)"
                 % (code, " | ".join((out.strip().splitlines() or [""])[-2:])))
    st_path = os.path.join(REPO, "outputs", "analysis", "staged_package_check.json")
    try:
        st = json.load(io.open(st_path, encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        st = {}
        add_hard("staged_package_check_json", "cannot read %s: %s: %s"
                 % (os.path.relpath(st_path, REPO), type(exc).__name__, exc))
    missing_pkgs = sorted(set(STAGED_TO_LIVE) - set(st))
    if missing_pkgs:
        add_hard("staged_packages_missing",
                 "staged_package_check.json has no record for: %s" % ", ".join(missing_pkgs))
    wrong = {k: v for k, v in st.items() if v.get("status") != "ok" or not v.get("page_match")}
    if wrong:
        add_hard("staged_packages", "staged package(s) failed the compile/page match: %s"
                 % json.dumps(wrong)[:400])
    rep["staged_packages"].update({
        "pass": code == 0 and not wrong and not missing_pkgs,
        "wrong": wrong, "missing_packages": missing_pkgs,
        "json": os.path.relpath(st_path, REPO),
        "json_mtime_local": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(os.path.getmtime(st_path)))
        if os.path.exists(st_path) else None,
    })
    fresh = check_staged_freshness(st)
    rep["staged_freshness"] = fresh
    for w in fresh["warnings"]:
        add_warn(w["code"], w["detail"], package=w.get("package"))
    print("  staged packages:", rep["staged_packages"]["pass"], "wrong:", list(wrong),
          "| freshness warnings:", fresh["n_warnings"])
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
    if not ok:
        add_hard("pages", "page count mismatch: %s" % json.dumps(pages))
    # 9b. bootstrap-integration text and write-scope guards (2026-10-24 round)
    rep["bootstrap_integration"] = check_bootstrap_integration()
    bad = [k for k, v in rep["bootstrap_integration"]["checks"].items() if not v]
    print("  bootstrap integration:", rep["bootstrap_integration"]["pass"], "failed:", bad)
    if not rep["bootstrap_integration"]["pass"]:
        add_hard("bootstrap_integration", "failed checks: %s" % bad)
    # 9c. decoder-ladder integration text and archive reproduction guards (2026-10-24b round)
    rep["decoder_ladder_integration"] = check_decoder_ladder_integration()
    bad = [k for k, v in rep["decoder_ladder_integration"]["checks"].items() if not v]
    print("  decoder ladder integration:", rep["decoder_ladder_integration"]["pass"], "failed:", bad)
    if not rep["decoder_ladder_integration"]["pass"]:
        add_hard("decoder_ladder_integration", "failed checks: %s" % bad)
    # 10. working-tree state (D-4: part of the verdict, never a silent side note).
    #     Excluded from the count: this script's own report and the audit reports that THIS run
    #     just generated (they are the gate's byproducts, not pending work) -- both are still
    #     listed in the report so nothing is hidden.
    code, out = run(["git", "status", "--porcelain"])
    lines = [ln for ln in out.strip().splitlines() if ln.strip()]
    self_reports = set()
    for r in rep["audits"].values():
        self_reports.update(r.get("report_paths") or [])
    self_out = [ln for ln in lines if "outputs/analysis/final_verification.json" in ln]
    self_audits = [ln for ln in lines
                   if ln.lstrip(" ?!MADRCU").strip().strip('"') in self_reports]
    dirty = [ln for ln in lines
             if "outputs/analysis/final_verification.json" not in ln
             and ln.lstrip(" ?!MADRCU").strip().strip('"') not in self_reports]
    # separate leftovers of *previous* audit runs from real pending work: both are reported,
    # but conflating them would either hide pending work or make the warning permanent noise
    dirty_audit_reports = [ln for ln in dirty
                           if ln.lstrip(" ?!MADRCU").strip().strip('"').startswith("docs/audits/AUD-")]
    dirty_other = [ln for ln in dirty if ln not in dirty_audit_reports]
    head = git_head()
    rep["git_clean"] = {
        "pass": code == 0 and not dirty, "n_dirty": len(dirty), "dirty": dirty,
        "n_dirty_other": len(dirty_other), "dirty_other": dirty_other,
        "n_dirty_audit_reports": len(dirty_audit_reports),
        "dirty_audit_reports": dirty_audit_reports,
        "n_self_output_excluded": len(self_out),
        "n_self_audit_reports_excluded": len(self_audits),
        "self_reports": sorted(self_reports),
        "head": head,
        "note": ("excluded from the count: outputs/analysis/final_verification.json (this "
                 "script's own output) and the docs/audits/AUD-* reports this run generated; "
                 "leftover audit reports from earlier runs are counted separately from real "
                 "pending work, and both are listed"),
    }
    print("  git clean:", rep["git_clean"]["pass"], "dirty_paths:", len(dirty),
          "(self-output excluded: %d, this-run audit reports excluded: %d)"
          % (len(self_out), len(self_audits)))
    if code != 0:
        add_hard("git_status", "git status --porcelain exited %d" % code)
    if dirty_other:
        add_warn("dirty_tree",
                 "%d uncommitted non-audit path(s) at HEAD %s: %s%s"
                 % (len(dirty_other), (head or "?").split()[0], "; ".join(dirty_other[:5]),
                    " ..." if len(dirty_other) > 5 else ""),
                 n_dirty=len(dirty_other), paths=dirty_other, head=head)
    if dirty_audit_reports:
        add_warn("untracked_audit_reports",
                 "%d untracked docs/audits/AUD-* file(s) left over from earlier audit runs: %s"
                 % (len(dirty_audit_reports),
                    "; ".join(ln.strip() for ln in dirty_audit_reports[:5])
                    + (" ..." if len(dirty_audit_reports) > 5 else "")),
                 n_dirty=len(dirty_audit_reports), paths=dirty_audit_reports, head=head)
    # 11. verdict (hard failures > accepted deviations + warnings > clean PASS)
    rep["hard_failures"] = hard
    rep["accepted_deviations"] = accepted
    rep["warnings"] = warns
    n_warn = len(warns) + len(accepted)
    rep["warning_count"] = n_warn
    hard_ok = not hard
    verdict = "FAIL" if hard else ("PASS WITH %d WARNING(S)" % n_warn if n_warn else "PASS")
    rep["verdict"] = verdict
    rep["all_pass"] = hard_ok           # hard-gate status (kept for continuity)
    rep["all_green"] = hard_ok and n_warn == 0
    # Hard invariant (D-2): a PASS verdict can never coexist with a hard failure.
    assert not (hard and verdict.startswith("PASS")), \
        "verdict %r cannot read PASS while %d hard failure(s) exist" % (verdict, len(hard))
    if accepted:
        print("  ACCEPTED DEVIATIONS (%d) -- named, with package snapshot date and reason:" % len(accepted))
        for d in accepted:
            snap = d.get("package_snapshot") or {}
            print("    - profile=%s check=%s package=%s snapshot=%s reason=%s"
                  % (d["profile"], d["check"], d["package"],
                     snap.get("newest_local", "unknown"), d["reason"]))
    if warns:
        print("  WARNINGS (%d):" % len(warns))
        for w in warns:
            print("    - [%s] %s" % (w["code"], w["detail"]))
    suffix = ""
    gc = rep["git_clean"]
    if gc["n_dirty"]:
        suffix = (" | git_clean=False: %d uncommitted path(s) = %d pending + %d leftover audit "
                  "report(s); this run's own output excluded"
                  % (gc["n_dirty"], gc["n_dirty_other"], gc["n_dirty_audit_reports"]))
    print("  VERDICT:", verdict + suffix)
    print("  ALL:", verdict + suffix)
    rep["finished_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    rep["elapsed_sec"] = round(time.time() - t0, 1)
    rep["head_at_finish"] = git_head()
    if a.apply:
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(rep, indent=1))
        print("  wrote", os.path.relpath(OUT, REPO))
    return 0 if hard_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
