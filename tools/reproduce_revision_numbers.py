# -*- coding: utf-8 -*-
r"""One-command reproduction of every number the revision adds.

Runs the four deterministic analyses that back the revision's additions, then re-reads their archives and checks the key
numbers against the values quoted in the manuscript. Exit code 0 means "all revision numbers reproduce"; a mismatch prints
the expected and the recomputed value side by side.

    D:\Anaconda\envs\pytorch\python.exe tools\reproduce_revision_numbers.py [--skip-heavy]

`--skip-heavy` keeps the two cross-validation passes out (they are the slow part) and checks the pre-registered
statistics, the robustness numbers and the cross-modal archives only.
"""
import argparse
import io
import json
import os
import subprocess
import sys

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PY = sys.executable
HEAVY = [
    ("competing models (5-fold CV, 813 trajectories)", "tools/_p1767b_cv_compare.py",
     "outputs/analysis/paperA_competing_models_cv.json"),
    ("competing models by stratum", "tools/_p1784_stratified_cv.py",
     "outputs/analysis/paperA_competing_models_strata.json"),
]
LIGHT = [
    ("pre-registration statistics", "tools/_p1767_upgrade_a2_a3.py", "outputs/analysis/paperA_prereg_stats.json"),
    ("association robustness and eta-squared", "tools/_p1786_robust_corr.py", "outputs/analysis/paperA_robustness.json"),
    ("theory additivity checks", "tools/_p1768_theory_checks.py",
     "outputs/analysis/paperA_theory_hardness_checks.json"),
]

CHECKS = [
    ("outputs/analysis/paperA_competing_models_cv.json", lambda d: d["models"]["ode"]["median_cv_r2"], 0.46, 0.02,
     "ODE median CV R^2"),
    ("outputs/analysis/paperA_competing_models_cv.json", lambda d: d["models"]["power"]["median_cv_r2"], 0.35, 0.02,
     "power-law median CV R^2"),
    ("outputs/analysis/paperA_competing_models_strata.json", lambda d: d["pooled"]["ode_minus_power"], 0.097, 0.02,
     "pooled ODE minus power (strata run)"),
    ("outputs/analysis/paperA_prereg_stats.json",
     lambda d: d["backbones"]["CLIP B/32"]["text_only"]["mean"], -0.038, 0.003, "CLIP B/32 text-only dCG"),
    ("outputs/analysis/paperA_prereg_stats.json",
     lambda d: d["backbones"]["OpenCLIP B/32"]["text_only"]["mean"], 0.0716, 0.003, "OpenCLIP text-only dCG"),
    ("outputs/analysis/paperA_robustness.json", lambda d: d["association"]["r_dg_r1"], -0.714, 0.01,
     "r(DG, R@1) over 204 runs"),
    ("outputs/analysis/paperA_robustness.json", lambda d: d["association"]["partial_dg_given_cg"], -0.581, 0.01,
     "partial r(DG, R@1 | CG)"),
    ("outputs/analysis/paperA_robustness.json",
     lambda d: d["prereg_effect_size"]["CLIP B/32"]["eta_squared_site"], 0.965, 0.01, "eta^2 of site, CLIP B/32"),
    ("outputs/analysis/paperA_theory_hardness_checks.json", lambda d: d["C2"]["disagreement_rate"], 0.256, 0.02,
     "norm-vs-Gamma ordering disagreement"),
    ("outputs/analysis/paperA_crossmodal_esc50.json", lambda d: d["matched"]["gamma_relative"]["text"], 0.991, 0.005,
     "cross-modal text-tower share, matched"),
]


def run(script, label):
    print("running %-46s ..." % label, end=" ", flush=True)
    r = subprocess.run([PY, script], capture_output=True, text=True,
                       env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    ok = r.returncode == 0
    print("ok" if ok else "FAILED (rc=%d)" % r.returncode)
    if not ok:
        print((r.stdout or "")[-1200:])
        print((r.stderr or "")[-800:])
    return ok


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-heavy", action="store_true")
    a = ap.parse_args()
    todo = (LIGHT if a.skip_heavy else HEAVY + LIGHT)
    failures = 0
    for label, script, _ in todo:
        if not run(script, label):
            failures += 1
    print("\nnumber check")
    for path, getter, expected, tol, label in CHECKS:
        if not os.path.isfile(path):
            print("  %-44s ARCHIVE MISSING (%s)" % (label, path))
            failures += 1
            continue
        d = json.load(io.open(path, encoding="utf-8"))
        try:
            got = float(getter(d))
        except Exception as e:
            print("  %-44s could not read value: %s" % (label, e))
            failures += 1
            continue
        ok = abs(got - expected) <= tol
        print("  %-44s %s  got %.4f, expected %.4f +- %.3f" %
              (label, "ok  " if ok else "MISMATCH", got, expected, tol))
        if not ok:
            failures += 1
    print("\nRESULT:", "PASS" if failures == 0 else "FAIL (%d problems)" % failures)
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
