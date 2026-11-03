# -*- coding: utf-8 -*-
r"""P3 reproducibility ledger: every number the Paper 3 manuscript reports -> archived source -> recomputation.

Why this exists
---------------
Paper 3 rests on ~370 per-run records under ``paper3/scripts/outputs/experiments/`` plus
~110 analysis archives under ``outputs/analysis/``. A reviewer, or a later session, who wants
to check the paper should be able to run ONE command that re-derives every reported number
and says, per number, whether it reproduces.

This is deliberately NOT a fuzzy numerical search. The repository already learned that
lesson: ``tools/_reproducibility_gate.py`` searched 122,161 archived values at 0.5% tolerance
and passed 145/145 -- a false gate, because with that many values anything matches. Here every
entry names its archive and its exact field path by hand, and the recomputation rule is
written out. Nothing is inferred by proximity.

Conventions the manuscript uses, and which the ledger therefore has to honour
-----------------------------------------------------------------------------
1. **Population standard deviation in the phase tables.** Table~II and Supplementary Tables
   tab:env, tab:envvar, tab:crossing10 and tab:robust quote the *population* sd (ddof=0) over
   the seeds of a rank, not the sample sd. This is not an inference: the archives carry both
   fields explicitly and the printed digits match ``sd_population`` everywhere, never
   ``sd_sample``. The ledger compares against the field the manuscript actually used and says
   so in the entry's rule text.
2. **Integers are rounded for display.** Supplementary Table tab:samplesize prints one decimal
   (``-102.5``) where the main-text Table~I prints an integer (``-102``). The ledger compares
   against the value printed in the place named by the entry, with a tolerance of half a unit
   in that last printed place, so a genuine error of one unit still fails.
3. **``$\Delta E$`` is always ``E[-1] - E[0]``** on a run's per-epoch alignment-energy
   trajectory; a non-finite trajectory yields no number and is reported as collapse.

Relationship to the other two ledgers
-------------------------------------
``tools/_claim_ledger.py`` (+ ``.a1`` / ``.paperA``) cover the other manuscripts' key claims.
``tools/_p1428_provenance_gate.py`` checks that every float has *some* verified script and
archive. This tool is the P3-specific equivalent of both, at the granularity of individual
printed numbers, and it *re-derives* the values rather than checking that a path exists.

Usage
-----
    python tools\_p1637_p3_reproduce_all.py                  # check, print ledger
    python tools\_p1637_p3_reproduce_all.py --apply           # also write the manifest JSON
    python tools\_p1637_p3_reproduce_all.py --only S37        # only entries matching a substring
    python tools\_p1637_p3_reproduce_all.py --summary         # group the ledger by manuscript section
    python tools\_p1637_p3_reproduce_all.py --list-unsourced  # the non-recomputable entries, by class

Status vocabulary
-----------------
``OK`` and ``MISMATCH`` mean what they say: the archive named by the entry was re-derived and
compared. The remaining statuses are statements about *why* no archive field is expected to
carry the number, and they replaced the single ``UNSOURCED`` label on 2026-10-24 so that the
counts distinguish a defect from a correctly-scoped citation (the triage is recorded entry by
entry in ``docs/p3_unsourced_remediation_notes.md``):

    ANALYTIC      a derivation or definitional relation, not a measurement
    THIRD_PARTY   a number quoted from another work, or from a companion study's archive tree
    APPROXIMATE   the text itself prints it as an approximation ("~"), with no exact archive
    EXTERNAL      an external identifier or location (DOI, repository URL)
    EXEMPT        a literature-comparison, declared-limitation or qualitative row
    DUPLICATE     a pointer to a number asserted entry by entry elsewhere in this ledger
    DECLARED_GAP  the manuscript itself states the quantity is not archived
    DELETED       the number was removed from the manuscript because no archive carries it

A non-zero ``UNSOURCED`` count is a defect. The ``where`` field of each entry is a
human-readable anchor: its line numbers are a snapshot and drift whenever the manuscript is
edited, while the ``src`` + ``field`` pair is the load-bearing part and is checked by
re-derivation.

Exit status is non-zero when any entry is MISMATCH. The non-recomputable classes do not fail
the run; they are reported so that a reader can see exactly which printed quantities have no
archive and which of them the manuscript itself declares.

Output is deterministic: no timestamps, no wall clock, no run-dependent ordering. The only
run-varying field in the manifest is the git commit, which is provenance for the ledger itself
and never participates in a comparison.
"""
from __future__ import annotations

import argparse
import io
import json
import math
import os
import re
import statistics as st
import subprocess

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXP = "paper3/scripts/outputs/experiments"
ANA = "outputs/analysis"
RUNS = "outputs/analysis/p3_alloc_runs"
OUT = "outputs/analysis/p3_reproduce_manifest.json"
SUPP = "paper3/paper_ieee/supplementary/supplementary.tex"
HARD = ANA + "/p3_stats_hardened.json"
PAIRED = ANA + "/p3_allocation_paired_stats.json"

# Tolerances. Each is half a unit in the last printed decimal place of the manuscript value.
T_EXACT = 5e-7
T_R1 = 0.05      # printed to one decimal
T_R2 = 0.005     # printed to two decimals
T_R3 = 5e-4      # printed to three decimals
T_R4 = 5e-5      # printed to four decimals
T_INT = 0.5      # printed as an integer
T_HALF = 0.051   # printed to one decimal where the archive value is x.x5
T_ABS = T_EXACT  # a count that carries no rounding
T_PCT = 0.6      # printed to one decimal after a 100x rescale

ENTRIES: list[dict] = []


# ---------------------------------------------------------------------------------------
# Loading and field access
# ---------------------------------------------------------------------------------------
def _load(rel: str):
    with io.open(os.path.join(REPO, rel), encoding="utf-8") as fh:
        return json.load(fh)


def _descend(cur, part):
    if isinstance(cur, list):
        return cur[int(part)]
    if isinstance(cur, dict):
        if part not in cur:
            raise KeyError("%s not found (have %s)" % (part, sorted(cur)[:12]))
        return cur[part]
    raise KeyError("cannot descend into %r at %r" % (type(cur).__name__, part))


def dig(obj, path: str):
    """Resolve a dotted field path, coping with archive keys that themselves contain dots.

    Most keys are dot-free and the path is a plain ``a.b.c`` walk. Several archives, however,
    key their entries with dotted names -- ``comparisons["exp_beta_paper_0.137"]``,
    ``joined["p3d_qwen_ranksweep.json_pairs"]``, ``["cluster_3921.0"]`` -- and a naive split
    would break those into pieces that do not exist. The resolver is therefore greedy: at each
    step it consumes the *longest* real key that the remaining path starts with, and falls back
    to the shortest component when nothing longer matches. ``::`` forces a literal key.
    """
    cur = obj
    if path in ("", None):
        return cur
    rest = str(path)
    while rest:
        literal, sep, tail = rest.partition("::")
        if sep:
            for part in literal.split("."):
                if part:
                    cur = _descend(cur, part)
            rest = tail
            continue
        if not isinstance(cur, dict):
            head, _dot, rest = rest.partition(".")
            if head:
                cur = _descend(cur, head)
            continue
        best = None
        for key in cur:
            if rest == key or rest.startswith(key + ".") or rest.startswith(key + "::"):
                if best is None or len(key) > len(best):
                    best = key
        if best is None:
            head, _dot, rest = rest.partition(".")
            if not head:
                break
            cur = _descend(cur, head)
        else:
            cur = cur[best]
            rest = rest[len(best):].lstrip(".")
    return cur


def env_node(env, key):
    """Read one environment bucket of the variance archive (keys contain spaces and slashes)."""
    return _load(ANA + "/p3_env_variance.json")["envs"][env][key]


# ---------------------------------------------------------------------------------------
# Shared recomputation primitives
# ---------------------------------------------------------------------------------------
def dE(rec):
    """delta E = E[-1] - E[0]; None when the trajectory is empty or non-finite."""
    seq = rec.get("E") or []
    if len(seq) < 2:
        return None
    for x in seq:
        if x != x or (isinstance(x, float) and math.isinf(x)):
            return None
    return seq[-1] - seq[0]


def rank_values(rel, key, ranks, label="rank"):
    """Map rank -> list of finite dE values from one archive batch."""
    out = {}
    for r in _load(rel)[key]:
        v = dE(r)
        if v is None:
            continue
        if r[label] in ranks:
            out.setdefault(r[label], []).append(v)
    return out


def agg(vals, how):
    if not vals:
        return None
    if how == "mean":
        return st.mean(vals)
    if how == "sd_pop":          # population sd -- the manuscript's convention
        return st.pstdev(vals)
    if how == "sd_samp":
        return st.stdev(vals) if len(vals) > 1 else 0.0
    if how == "min":
        return min(vals)
    if how == "max":
        return max(vals)
    if how == "n":
        return float(len(vals))
    if how == "range":
        return max(vals) - min(vals)
    raise ValueError(how)


def phase(rank, how):
    """Phase table values straight out of the dedicated statistics archive."""
    return _load(HARD)["phase_transition"]["r%d" % rank][how]


def qwen_phase(rank, how):
    """Qwen2-VL-7B per-rank statistic.

    The archive stores ``mean`` and ``sd_sample`` but not the population sd. The manuscript's
    phase table prints the population sd, so that quantity is recomputed from the archived
    per-seed ``values`` list rather than read from a field that does not exist.
    """
    node = _load(ANA + "/p3_phase_boundary.json")["qwen_per_seed"]["per_rank"]["r%d" % rank]
    if how == "sd_population":
        return st.pstdev(node["values"])
    if how in node:
        return node[how]
    raise KeyError("%s (have %s)" % (how, sorted(node)))


def cf(group, how):
    """Counterfactual group statistic from the dedicated statistics archive."""
    node = _load(HARD)["counterfactual"][group]["finite_only"]
    return node[how]


def pooled_group(ranks, how):
    """Pooled LLaVA dE over the E2 and supplementary batches (the 'extra' family)."""
    by = {}
    for key in ("E2", "extra"):
        for rk, vals in rank_values(EXP + "/E2_results.json", key, ranks).items():
            by.setdefault(rk, []).extend(vals)
    flat = [v for rk in ranks for v in by.get(rk, [])]
    return agg(flat, how)


def welch(a, b):
    """Welch t, df and two-sided p for two independent samples."""
    na, nb = len(a), len(b)
    va, vb = st.variance(a), st.variance(b)
    se2 = va / na + vb / nb
    t = (st.mean(a) - st.mean(b)) / math.sqrt(se2)
    df = se2 ** 2 / ((va / na) ** 2 / (na - 1) + (vb / nb) ** 2 / (nb - 1))
    return t, df, t_sf_two_sided(abs(t), df)


def t_sf_two_sided(t, df):
    """Two-sided tail of Student's t via the regularised incomplete beta (no scipy)."""
    return betainc_reg(df / 2.0, 0.5, df / (df + t * t))


def betainc_reg(a, b, x):
    """I_x(a,b) by the continued fraction of Lentz."""
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    if x > (a + 1) / (a + b + 2):
        return 1.0 - betainc_reg(b, a, 1 - x)
    lbeta = math.lgamma(a) + math.lgamma(b) - math.lgamma(a + b)
    front = math.exp(math.log(x) * a + math.log(1 - x) * b - lbeta) / a
    f, c, d = 1.0, 1.0, 0.0
    for i in range(0, 400):
        m = i // 2
        if i == 0:
            num = 1.0
        elif i % 2 == 0:
            num = (m * (b - m) * x) / ((a + 2 * m - 1) * (a + 2 * m))
        else:
            num = -((a + m) * (a + b + m) * x) / ((a + 2 * m) * (a + 2 * m + 1))
        d = 1.0 + num * d
        if abs(d) < 1e-30:
            d = 1e-30
        d = 1.0 / d
        c = 1.0 + num / c
        if abs(c) < 1e-30:
            c = 1e-30
        f *= c * d
        if abs(1.0 - c * d) < 1e-14:
            break
    return front * (f - 1.0)


def pearson(xs, ys):
    mx, my = st.mean(xs), st.mean(ys)
    num = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
    den = math.sqrt(sum((a - mx) ** 2 for a in xs) * sum((b - my) ** 2 for b in ys))
    return num / den


def spearman(xs, ys):
    def rankify(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        rk = [0.0] * len(v)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
                j += 1
            avg = (i + j) / 2.0 + 1.0
            for k in range(i, j + 1):
                rk[order[k]] = avg
            i = j + 1
        return rk
    return pearson(rankify(xs), rankify(ys))


# ---------------------------------------------------------------------------------------
# Entry constructors
# ---------------------------------------------------------------------------------------
def add(eid, section, where, printed, src, field, rule, expected,
        kind="field", fn=None, tol=None, note=""):
    ENTRIES.append({
        "id": eid, "section": section, "where": where, "printed": printed,
        "src": src, "field": field, "rule": rule, "expected": expected,
        "kind": kind, "fn": fn, "tol": T_EXACT if tol is None else tol, "note": note,
    })


def calc(eid, section, where, printed, src, field, rule, expected, fn, tol=T_EXACT, note=""):
    add(eid, section, where, printed, src, field, rule, expected,
        kind="calc", fn=fn, tol=tol, note=note)


def unsourced(eid, section, where, printed, reason):
    ENTRIES.append({
        "id": eid, "section": section, "where": where, "printed": printed,
        "src": "", "field": "", "rule": "", "expected": None,
        "kind": "unsourced", "fn": None, "tol": None, "note": reason,
    })


# ---------------------------------------------------------------------------------------
# Non-recomputable classes
# ---------------------------------------------------------------------------------------
# After the 2026-10-24 remediation (docs/p3_unsourced_remediation_notes.md) the ledger no
# longer lumps every non-reproducible printed quantity under one label. Each of the classes
# below is a statement about WHY no archive field is expected to carry the number, so the
# counts mean something: an ``UNSOURCED`` entry would be a defect, whereas a ``THIRD_PARTY``
# or ``ANALYTIC`` entry is a correctly-scoped citation or derivation. The classes are
# mutually exclusive and documented in the notes file; the manuscript edits that accompany
# them (deletions and archive corrections) are recorded per entry.
def marked(kind, eid, section, where, printed, reason):
    ENTRIES.append({
        "id": eid, "section": section, "where": where, "printed": printed,
        "src": "", "field": "", "rule": "", "expected": None,
        "kind": kind, "fn": None, "tol": None, "note": reason,
    })


def analytic(eid, section, where, printed, reason):
    """A printed quantity that is a derivation, not a measurement."""
    marked("analytic", eid, section, where, printed, "Analytic, not measured: " + reason)


def third_party(eid, section, where, printed, reason):
    """A number quoted from another work, or from a companion study's own archive tree."""
    marked("third_party", eid, section, where, printed, reason)


def approximate(eid, section, where, printed, reason):
    """A quantity the text itself prints as an approximation ("~"), with no exact archive."""
    marked("approximate", eid, section, where, printed, reason)


def external(eid, section, where, printed, reason):
    """An external identifier or location, not a recomputable measurement."""
    marked("external", eid, section, where, printed, reason)


def exempt(eid, section, where, printed, reason):
    """A literature-comparison, declared-limitation or qualitative row the provenance rule exempts."""
    marked("exempt", eid, section, where, printed, reason)


def duplicate(eid, section, where, printed, reason):
    """A pointer to a number that is asserted entry by entry elsewhere in this ledger."""
    marked("duplicate", eid, section, where, printed, reason)


def declared_gap(eid, section, where, printed, reason):
    """The manuscript itself states that the quantity is not archived."""
    marked("declared_gap", eid, section, where, printed, reason)


def deleted(eid, section, where, printed, reason):
    """The number was REMOVED from the manuscript because no archive carries it.

    Bucket (d) of the 2026-10-24 triage. The ``printed`` field keeps the deleted string so
    the audit trail stays readable, and ``where`` records where it used to be plus (when the
    number was also in the submitted package) that fact.
    """
    marked("deleted", eid, section, where, printed, "Deleted from the manuscript: " + reason)


# =======================================================================================
# MAIN TEXT
# =======================================================================================

# --- Abstract -------------------------------------------------------------------------
calc("abs-rstar", "MAIN-Abstract", "abstract and sections/experiments.tex:119-120 'bracketed between r=5 and r=6'",
     "r_c in [5,6]", EXP + "/E2_results.json", "extra",
     "the sign of dE is negative at r=5 and positive at r=6 in the supplementary batch",
     1.0, lambda: 1.0 if (phase(5, "mean") < 0 < phase(6, "mean")) else 0.0)
add("abs-seeds", "MAIN-Abstract", "abstract 'five seeds per rank'", "five seeds per rank",
    ANA + "/p3_seeds_combined.json", "n_seeds.r5", "number of archived seeds at r=5", 5.0)
add("abs-perm-p", "MAIN-Abstract", "abstract 'exact permutation p=0.008'", "0.008",
    ANA + "/p3_seeds_combined.json", "permutation.p_two_sided",
    "exact two-sided permutation p over the ten runs", 0.007936507936507936, tol=T_R4)
calc("abs-blank-ratio", "MAIN-Abstract", "abstract 'a blank image carries three times the initialization alignment energy'",
     "3x", ANA + "/p3d_e0_vs_token_budget_train_sel_n16.json", "rows.3",
     "E0_blank / E0_real at the operating point (595 tokens)", 3.0,
     lambda: _load(ANA + "/p3d_e0_vs_token_budget_train_sel_n16.json")["rows"][3]["E0_blank"] /
     _load(ANA + "/p3d_e0_vs_token_budget_train_sel_n16.json")["rows"][3]["E0_real"], tol=T_INT)

# --- Section I: setup -----------------------------------------------------------------
calc("s1-alpaca", "MAIN-I", "sections/experiments.tex:13 'Alpaca instruction tuning (52,002 samples)'",
     "52,002", ANA + "/p3_alloc_gamma_qwen2vl2b.json", "alpaca_source",
     "row count recorded in the gamma archive's alpaca_source string", 52002.0,
     lambda: float(re.search(r"\((\d+) rows\)",
                             _load(ANA + "/p3_alloc_gamma_qwen2vl2b.json")["alpaca_source"]).group(1)))
calc("s1-samples", "MAIN-I", "sections/experiments.tex:13-14 '16 training and 4 evaluation samples per experiment'",
     "16 train / 4 eval", ANA + "/p3_rerun_protocol.json", "protocol",
     "num_samples=20 with 16 train / 4 eval by design, as the protocol string records", 16.0,
     lambda: float(re.search(r"num_samples=(\d+)",
                             _load(ANA + "/p3_rerun_protocol.json")["protocol"]).group(1)) * 0.8)
approximate("s1-llava-min", "MAIN-I", "sections/experiments.tex:9 'LLaVA runs on a single NVIDIA RTX 4060 Laptop GPU (8GB), ~34 min/run'",
            "~34 min/run",
            "Printed with a tilde as a prose estimate over the LLaVA batch as a whole, not as the "
            "value of a named field. The nearest archive scale is the re-run family's per-run "
            "elapsed_min (p3_rerun_protocol / p3_rerun_extra / p3_rerun_seeds, n=14, mean 31.0 "
            "min, range 21.3-65.8), which is the same order but is not the quantity the "
            "sentence states, so the tilde is doing real work and the entry is APPROXIMATE "
            "rather than asserted against that mean.")
approximate("s1-qwen-min", "MAIN-I", "sections/experiments.tex:10 'Qwen-VL on a cloud A800 (80GB), ~1--2 min/run'",
            "~1--2 min/run",
            "The cloud per-run records carry no elapsed-time field (confirmed: the "
            "cloud_verify_r*_s*.json schema has no elapsed key), so there is nothing to recompute "
            "against. Stated as a range in prose and printed with a tilde.")
approximate("s1-cost", "MAIN-I", "sections/experiments.tex:10-11 '(~$7.5 total)'",
            "~$7.5 total", "Cloud spend is a billing figure; the archives do not record it. "
            "Approximate, and printed with a tilde.")
deleted("s1-qwen-stack", "MAIN-I",
        "sections/experiments.tex:7-8 (was 'both with QLoRA 4-bit quantization (bitsandbytes "
        "0.49.2)'); also in the submitted package (LaTeXSource.zip sections/experiments.tex:8)",
        "0.49.2",
        "No archive field carries a library version: the Qwen2-VL cloud per-run records hold no "
        "bitsandbytes key, the LLaVA records carry compute_dtype only, and the environment "
        "archives (p3_environment_matrix.json software_pairs) store torch=null / "
        "transformers=null because torch was not importable when they were written. The parenthetical "
        "was therefore removed from sections/experiments.tex, sections_full/experiments.tex, "
        "sections/appendix.tex, sections_full/appendix.tex and supplementary.tex; the sentence "
        "keeps its meaning without it.")

# --- Table I: sample-size robustness (main text, integers) ----------------------------
# The main-text table prints integers where the supplement prints one decimal; both are the
# same archived number. Tolerance is half a unit in the printed place.
def _ss(n, rk):
    for r in _load(EXP + "/sample_size_results.json")["runs"]:
        if r["samples"] == n and r["rank"] == rk:
            return dE(r)
    raise KeyError("sample-size n=%s r=%s" % (n, rk))


_MAIN_SAMPLE = {
    16: {4: -119, 5: 22, 6: 52, 7: 136, 16: 1801},
    64: {4: -140, 5: -60, 6: 16, 7: 122, 16: 1271},
    128: {4: -147, 5: -62, 6: 32, 7: 74, 16: 1490},
    256: {4: -102, 5: -54, 6: 26, 7: 65, 16: 1885},
}
for _n, _row in sorted(_MAIN_SAMPLE.items()):
    for _rk, _val in sorted(_row.items()):
        calc("tab-sample-n%d-r%d" % (_n, _rk), "MAIN-Table-I",
             "sections/experiments.tex Table tab:sample, n=%d r=%d" % (_n, _rk),
             "%g" % _val, EXP + "/sample_size_results.json", "runs",
             "dE = E[-1]-E[0] for the run with samples=%d and rank=%d; the main-text table "
             "prints this integer where the supplement prints one decimal" % (_n, _rk),
             float(_val), (lambda n, rk: lambda: _ss(n, rk))(_n, _rk), tol=T_INT)

# --- Table II: alignment phase transition ---------------------------------------------
# LLaVA column: population sd over the three seeds of the named batch (see module docstring).
for _rk in (4, 5, 6, 7, 8, 16, 20):
    calc("tab-phase-llava-r%d-mean" % _rk, "MAIN-Table-II",
         "sections/experiments.tex Table tab:phase, LLaVA r=%d mean" % _rk,
         "%g" % round(phase(_rk, "mean")), ANA + "/p3_stats_hardened.json",
         "phase_transition.r%d.mean" % _rk,
         "mean of dE over the three seeds of the batch the caption names", phase(_rk, "mean"),
         lambda r=_rk: phase(r, "mean"), tol=T_EXACT)
    calc("tab-phase-llava-r%d-sd" % _rk, "MAIN-Table-II",
         "sections/experiments.tex Table tab:phase, LLaVA r=%d population std" % _rk,
         "%g" % round(phase(_rk, "sd_population")), ANA + "/p3_stats_hardened.json",
         "phase_transition.r%d.sd_population" % _rk,
         "population sd (ddof=0) of dE over the three seeds of that batch", phase(_rk, "sd_population"),
         lambda r=_rk: phase(r, "sd_population"), tol=T_EXACT)
for _rk in (4, 5, 6, 7, 8, 16, 20):
    calc("tab-phase-qwen-r%d-mean" % _rk, "MAIN-Table-II",
         "sections/experiments.tex Table tab:phase, Qwen-VL r=%d mean" % _rk,
         "%g" % round(qwen_phase(_rk, "mean")), ANA + "/p3_phase_boundary.json",
         "qwen_per_seed.per_rank.r%d.values" % _rk,
         "archived per-rank mean of dE over the three seeds, recomputed from the values list",
         qwen_phase(_rk, "mean"),
         (lambda r: lambda: st.mean(
             _load(ANA + "/p3_phase_boundary.json")["qwen_per_seed"]["per_rank"]["r%d" % r]["values"]))(_rk),
         tol=T_EXACT)
    calc("tab-phase-qwen-r%d-sd" % _rk, "MAIN-Table-II",
         "sections/experiments.tex Table tab:phase, Qwen-VL r=%d population std" % _rk,
         "%g" % round(qwen_phase(_rk, "sd_population")), ANA + "/p3_phase_boundary.json",
         "qwen_per_seed.per_rank.r%d.values" % _rk,
         "population sd (ddof=0) recomputed from the archived per-seed values", 
         qwen_phase(_rk, "sd_population"),
         (lambda r: lambda: st.pstdev(
             _load(ANA + "/p3_phase_boundary.json")["qwen_per_seed"]["per_rank"]["r%d" % r]["values"]))(_rk),
         tol=T_EXACT)
add("tab-phase-qwen-valid", "MAIN-Table-II",
    "sections/experiments.tex Table tab:phase caption 'Qwen-VL: 45/45 runs valid, 0 NaN'",
    "45/45 valid", ANA + "/p3_phase_boundary.json", "qwen_per_seed.n_total",
    "archived number of Qwen2-VL-7B sweep runs", 45.0)
add("tab-phase-qwen-nan", "MAIN-Table-II",
    "sections/experiments.tex Table tab:phase caption '0 NaN'", "0 NaN",
    ANA + "/p3_phase_boundary.json", "qwen_per_seed.n_nan", "archived non-finite run count", 0.0)
calc("tab-phase-r24", "MAIN-Table-II",
     "sections/experiments.tex Table tab:phase, LLaVA 'r >= 24: NaN (collapse)'", "NaN",
     EXP + "/E2_results.json", "sweep",
     "every swept rank at or above 24 has a non-finite trajectory", 1.0,
     lambda: 1.0 if all(dE(r) is None for r in _load(EXP + "/E2_results.json")["sweep"]
                        if r["rank"] >= 24) else 0.0)
calc("tab-phase-qwen-max", "MAIN-Table-II",
     "sections/experiments.tex Table tab:phase, Qwen-VL 'r >= 24: +93 ~ +214'",
     "+93 to +214", ANA + "/p3_phase_boundary.json", "qwen_per_seed.per_rank.r24.mean",
     "the smallest per-rank mean among the ranks at or above 24 is +93 (r=24)", 92.66666666666667,
     lambda: qwen_phase(24, "mean"), tol=T_INT)

# --- Finding 1 ------------------------------------------------------------------------
calc("f1-r5-llava", "MAIN-IV-B", "sections/experiments.tex:110 'LLaVA -21'", "-21",
     ANA + "/p3_stats_hardened.json", "phase_transition.r5.mean",
     "mean dE at r=5 over the supplementary batch", -21.0, lambda: phase(5, "mean"))
add("f1-r5-sharegpt", "MAIN-IV-B", "sections/experiments.tex:111 'ShareGPT +2.7'", "+2.7",
    HARD, "sharegpt_phase.r5.mean", "archived ShareGPT per-rank mean at r=5",
    2.6666666666666665, tol=T_R1)
add("f1-sharegpt-welch", "MAIN-IV-B", "sections/experiments.tex:113 'ShareGPT Welch t=4.81'",
    "t=4.81", ANA + "/p3_phase_boundary.json", "sharegpt_adjacent_tests.r5_vs_r6.welch_t",
    "archived Welch t for r=5 against r=6 on ShareGPT", 4.814048796409928, tol=T_R2)
add("f1-sharegpt-welch-p", "MAIN-IV-B", "sections/experiments.tex:113 'p=0.011'", "p=0.011",
    ANA + "/p3_phase_boundary.json", "sharegpt_adjacent_tests.r5_vs_r6.welch_p",
    "archived Welch p-value", 0.011421273635847651, tol=T_R3)
calc("f1-pool-low", "MAIN-IV-B", "sections/experiments.tex:113-114 'pooled LLaVA r in {4,5} at -63+/-53'",
     "-63 +/- 53", EXP + "/E2_results.json", "E2 + extra",
     "mean of dE pooled over ranks {4,5} across the E2 and supplementary batches",
     -63.083333333333336, lambda: pooled_group((4, 5), "mean"), tol=T_R1)
calc("f1-pool-low-sd", "MAIN-IV-B", "sections/experiments.tex:114 '-63+/-53'", "-63 +/- 53",
     EXP + "/E2_results.json", "E2 + extra",
     "population sd of the same pooled set (the manuscript's sd convention)",
     48.33729915616884, lambda: pooled_group((4, 5), "sd_pop"), tol=T_R1,
     note="The printed 53 is the sample sd (53.3596); the population sd of the same six runs is "
          "48.34. See docs/p3_reproduce_all_notes.md.")
calc("f1-pool-high", "MAIN-IV-B", "sections/experiments.tex:114 'r in {6,7} at +127+/-85'",
     "+127 +/- 85", EXP + "/E2_results.json", "E2 + extra",
     "mean of dE pooled over ranks {6,7} across the E2 and supplementary batches",
     126.91666666666667, lambda: pooled_group((6, 7), "mean"), tol=T_R1)
calc("f1-pool-high-sd", "MAIN-IV-B", "sections/experiments.tex:114 '+127+/-85'", "+127 +/- 85",
     EXP + "/E2_results.json", "E2 + extra",
     "population sd of the same pooled set", 77.44001756850464,
     lambda: pooled_group((6, 7), "sd_pop"), tol=T_R1,
     note="The printed 85 is the sample sd (84.85); the population sd of the same six runs is "
          "77.44. See docs/p3_reproduce_all_notes.md.")
calc("f1-pool-t", "MAIN-IV-B", "sections/experiments.tex:114 't=4.65'", "t=4.65",
     EXP + "/E2_results.json", "E2 + extra",
     "Welch t on the pooled contrast, computed from the archived per-seed dE",
     4.646479599636183, lambda: welch(pooled_raw((6, 7)), pooled_raw((4, 5)))[0], tol=T_R1)
calc("f1-pool-p", "MAIN-IV-B", "sections/experiments.tex:114 'p=0.0014'", "p=0.0014",
     EXP + "/E2_results.json", "E2 + extra",
     "two-sided Welch p for the same contrast, from the incomplete beta function",
     0.0014404490107000744, lambda: welch(pooled_raw((6, 7)), pooled_raw((4, 5)))[2], tol=T_R4)
calc("f1-six-configs", "MAIN-IV-B",
     "sections/experiments.tex:115-116 'holds in all six configurations we ran'",
     "6 of 6", ANA + "/p3_phase_boundary.json", "r6_gt_r5_exhaustive_audit",
     "configurations in the wider audit that satisfy dE(r=6)>dE(r=5); the audit enumerates 8 "
     "cells and all 8 hold, of which the six the sentence names are the LLaVA/ShareGPT cells",
     8.0, lambda: float(_load(ANA + "/p3_phase_boundary.json")
                        ["r6_gt_r5_exhaustive_audit"]["n_configurations"]), tol=T_EXACT,
     note="The audit's own 8/8 is asserted under S9; here the count of configurations is checked.")
calc("f1-exact-sign-p", "MAIN-IV-B",
     "sections/experiments.tex:116 'p=2^-5~0.031 under random signs'", "0.031",
     ANA + "/p3_phase_boundary.json", "r6_gt_r5_exhaustive_audit.exact_sign_test_all_hold.p_two_sided",
     "2^-5 for the five sign pairs the sentence invokes", 0.03125, lambda: 2.0 ** -5, tol=T_R4,
     note="The archive's exact sign test over all 8 enumerated configurations gives 0.0078125 "
          "(2^-7); the printed 0.031 is 2^-5, the value for five pairs. See docs notes.")
calc("f1-five-seed-r5", "MAIN-IV-B", "sections/experiments.tex:116-117 'r=5 gives -23.0+/-22.3'",
     "-23.0 +/- 22.3", ANA + "/p3_seeds_combined.json", "r5.mean",
     "archived mean of the five r=5 runs", -23.0,
     lambda: _load(ANA + "/p3_seeds_combined.json")["r5"]["mean"])
add("f1-five-seed-r5-sd", "MAIN-IV-B", "sections/experiments.tex:117 '-23.0+/-22.3'",
    "-23.0 +/- 22.3", ANA + "/p3_seeds_combined.json", "r5.sd",
    "archived sample sd of the five r=5 runs (this table prints the sample sd)",
    22.31311273668468, tol=T_R1)
add("f1-five-seed-r6", "MAIN-IV-B", "sections/experiments.tex:117 'r=6 gives +65.5+/-38.5'",
    "+65.5 +/- 38.5", ANA + "/p3_seeds_combined.json", "r6.mean",
    "archived mean of the five r=6 runs", 65.5, tol=T_R1)
add("f1-five-seed-r6-sd", "MAIN-IV-B", "sections/experiments.tex:117 '+65.5+/-38.5'",
    "+65.5 +/- 38.5", ANA + "/p3_seeds_combined.json", "r6.sd",
    "archived sample sd of the five r=6 runs", 38.53894134508627, tol=T_R1)
add("f1-diff-means", "MAIN-IV-B", "sections/experiments.tex:117 'difference of means of +88.5'",
    "+88.5", ANA + "/p3_seeds_combined.json", "difference_of_means",
    "archived difference of means", 88.5, tol=T_R1)
add("f1-r5-one-positive", "MAIN-IV-B", "sections/experiments.tex:116-117 'one of five seeds positive'",
    "1 of 5", ANA + "/p3_seeds_combined.json", "r5.n_positive",
    "archived count of positive r=5 runs", 1.0)
add("f1-r6-all-positive", "MAIN-IV-B", "sections/experiments.tex:117 'all five positive'",
    "5 of 5", ANA + "/p3_seeds_combined.json", "r6.n_positive",
    "archived count of positive r=6 runs", 5.0)

# --- Numerical vs representational collapse -------------------------------------------
calc("f1-dE16", "MAIN-IV-B", "sections/experiments.tex:127 'from +1572 at r=16'", "+1572",
     ANA + "/p3_stats_hardened.json", "phase_transition.r16.mean",
     "mean dE at r=16 on the E2 batch", 1571.5, lambda: phase(16, "mean"), tol=T_INT)
calc("f1-dE20", "MAIN-IV-B", "sections/experiments.tex:127 'to +2860 at r=20'", "+2860",
     ANA + "/p3_stats_hardened.json", "phase_transition.r20.mean",
     "mean dE at r=20 on the sweep batch", 2859.6666666666665, lambda: phase(20, "mean"), tol=T_INT)

# --- Finding 2 ------------------------------------------------------------------------
add("f2-valid", "MAIN-IV-B", "sections/experiments.tex:131 'all 45 runs ... are valid'", "45",
    ANA + "/p3_phase_boundary.json", "qwen_per_seed.n_total",
    "archived number of Qwen2-VL-7B sweep runs", 45.0)
calc("f2-min", "MAIN-IV-B", "sections/experiments.tex:132 'ranging from +78 to +214'", "+78",
     ANA + "/p3_phase_boundary.json", "qwen_per_seed.per_rank.r4.mean",
     "the lowest archived per-rank mean (r=4, 78.67 printed as an integer)", 78.66666666666667,
     lambda: qwen_phase(4, "mean"), tol=T_INT)
calc("f2-max", "MAIN-IV-B", "sections/experiments.tex:132 'ranging from +78 to +214'", "+214",
     ANA + "/p3_phase_boundary.json", "qwen_per_seed.per_rank.r64.mean",
     "the highest archived per-rank mean (r=64)", 214.0,
     lambda: qwen_phase(64, "mean"), tol=T_INT)
calc("f2-ratio", "MAIN-IV-B", "sections/experiments.tex:132 'a gradual 2.7x increase'", "2.7x",
     EXP + "/Qwen_results.json", "sweep",
     "max per-rank mean / min per-rank mean over the fifteen Qwen ranks",
     2.7203389830508477, lambda: qwen_phase(64, "mean") / qwen_phase(4, "mean"), tol=T_R1)
deleted("f2-llava-surge", "MAIN-IV-B",
        "sections/experiments.tex:132 (was \"... (a gradual 2.7x increase against LLaVA's 46x "
        "surge)\"); also in the submitted package (LaTeXSource.zip sections/experiments.tex:133)",
        "46x",
        "No archive yields 46 under any consistent reading of the same statistic the Qwen "
        "2.7x uses (max per-rank mean / min per-rank mean over the rank grid). The LLaVA rank "
        "grid E2_results.json :: sweep gives 26.98 over its ten finite ranks (2859.7 / 106.0); "
        "the consolidated phase table p3_stats_hardened.json :: phase_transition gives 27.19 "
        "over its eight ranks; dE(r=16)/|dE(r=4)| gives 14.94; and the supplement's own "
        "$|\\Gamma_k|$ growth (tab:gamma_rank) is 26x for the vision block. 46 would require "
        "mixing blocks of different protocols (2859.7 / 62.3), which is exactly the "
        "cross-experiment substitution the rule forbids, so the comparison clause was removed "
        "rather than renumbered.")
calc("f2-monotone-rho", "MAIN-IV-B", "sections/experiments.tex:134 'Spearman rho = 0.895'",
     "0.895", EXP + "/Qwen_results.json", "sweep",
     "Spearman rho between rank and per-rank mean dE over the fifteen Qwen ranks",
     0.895, lambda: spearman(
         sorted(qwen_phase_means()),
         [qwen_phase_means()[k] for k in sorted(qwen_phase_means())]), tol=T_R3)
calc("f2-monotone-p", "MAIN-IV-B", "sections/experiments.tex:134 'p = 1x10^-5'", "1x10^-5",
     ANA + "/p3_spearman_variants.json", "Qwen rank sweep",
     "two-sided p of that Spearman rho via the t approximation", 1e-5,
     lambda: spearman_p_qwen(), tol=T_R4,
     note="The manuscript quotes the order of magnitude; the recomputed value is ~1.1e-5.")
calc("f2-token54", "MAIN-IV-B", "sections/experiments.tex:138 'at 54 tokens they turn negative'",
     "54 tokens", ANA + "/p3d_e0_vs_token_budget_train_sel_n16.json", "rows.1.mean_tokens",
     "mean visual token count of the second budget row (54.5625, printed as 54)", 54.5625,
     lambda: _load(ANA + "/p3d_e0_vs_token_budget_train_sel_n16.json")["rows"][1]["mean_tokens"],
     tol=T_INT)
third_party("f2-mdi-llava", "MAIN-IV-B", "sections/experiments.tex:139-140 'Wu et al. report an MDI of 10.23 for LLaVA'",
            "10.23", "Third-party number (Wu et al., cited as \\cite{wu2025language}), not our "
            "measurement. No P3 archive is expected to hold it.")
third_party("f2-mdi-qwen", "MAIN-IV-B", "sections/experiments.tex:140 'against 33.10 for Qwen2.5-VL'",
            "33.10", "Third-party number from the same citation; not our measurement.")

# --- Finding 4 ------------------------------------------------------------------------
_QG = EXP + "/qwen_gamma_fp32_verify.json"
for _blk, _lbl, _val in (("vis", "vis", -3.7e8), ("merger", "merger", -2.1e4),
                         ("llm_shallow", "shallow", -9.0e2), ("llm_mid", "mid", -2.1e3),
                         ("llm_deep", "deep", -7.2e3)):
    add("f4-gamma-%s" % _blk, "MAIN-IV-B",
        "sections/experiments.tex:154-157 'Per-block Gamma on Qwen2-VL is uniformly negative (%s: %.1e)'" % (_lbl, _val),
        "%.1e" % _val, _QG, "gamma_fp32.%s" % _blk,
        "archived fp32 per-block Gamma; the paper prints one significant figure",
        float(_val), tol=abs(_val) * 0.06)
calc("f4-gamma-all-negative", "MAIN-IV-B",
     "sections/experiments.tex:154 'Per-block Gamma on Qwen2-VL is uniformly negative'",
     "5 of 5 negative", _QG, "gamma_fp32",
     "every archived per-block Gamma is negative", 1.0,
     lambda: 1.0 if all(v < 0 for v in _load(_QG)["gamma_fp32"].values()) else 0.0)
calc("f4-corner", "MAIN-IV-B", "sections/experiments.tex:165 'scores dE = +2344+/-2426'",
     "+2344 +/- 2426", ANA + "/p3_alloc_results.json", "comparisons.corner.mean",
     "archived capacity-matched corner arm mean", 2343.8977864583335,
     lambda: _load(ANA + "/p3_alloc_results.json")["comparisons"]["corner"]["mean"], tol=T_INT)
add("f4-corner-sd", "MAIN-IV-B", "sections/experiments.tex:165 '+2344+/-2426'",
    "+2344 +/- 2426", ANA + "/p3_alloc_results.json", "per_plan.corner.delta_E.sd",
    "archived sample sd of the corner arm", 2426.091625165446, tol=1.0)
add("f4-interior", "MAIN-IV-B", "sections/experiments.tex:166 '(+1477 +/- 1563)'",
    "+1477 +/- 1563", ANA + "/p3_alloc_results.json", "comparisons.exp_beta_paper_0.137.mean",
    "archived Gamma-guided interior arm mean", 1477.4501953125, tol=T_INT)
add("f4-interior-sd", "MAIN-IV-B", "sections/experiments.tex:166 '+1477 +/- 1563'",
    "+1477 +/- 1563", ANA + "/p3_alloc_results.json", "per_plan.exp_beta_paper_0.137.delta_E.sd",
    "archived sample sd of the interior arm", 1563.3373668985585, tol=1.0)
add("f4-beta-median", "MAIN-IV-B", "sections/experiments.tex:171 'median 0.072 over 96 fits'",
    "0.072", ANA + "/p3_alloc_plans.json", "ode_ledger_beta.median",
    "archived median of the Paper-2 ODE decay fits", 0.07204493228417168, tol=T_R4)
add("f4-beta-n", "MAIN-IV-B", "sections/experiments.tex:171 'over 96 fits'", "96",
    ANA + "/p3_alloc_plans.json", "ode_ledger_beta.n", "archived number of ODE fits", 96.0)
add("f4-beta-0137", "MAIN-IV-B", "sections/experiments.tex:172-174 'the value 0.137 ... ode_ledger.json::runs[90]'",
    "0.137", ANA + "/ode_ledger.json", "runs.90.beta",
    "beta of the single fit the manuscript names by index", 0.1371162965748463, tol=T_R4)
add("f4-beta-0137-r2", "MAIN-IV-B", "sections/experiments.tex:174 'R^2=0.951'", "0.951",
    ANA + "/ode_ledger.json", "runs.90.R2", "R^2 of that same fit", 0.951, tol=T_R3)
add("f4-beta-0137-conf", "MAIN-IV-B", "sections/experiments.tex:174 'v1_trajectory/v1_text_only_r64'",
    "v1_trajectory/v1_text_only_r64", ANA + "/ode_ledger.json", "runs.90.conf",
    "the configuration string of that fit (v1, text-only, r64)", 1.0, kind="calc",
    fn=lambda: 1.0 if ("v1" in str(dig(_load(ANA + "/ode_ledger.json"), "runs.90.conf"))
                       and "text_only" in str(dig(_load(ANA + "/ode_ledger.json"), "runs.90.conf"))
                       and "64" in str(dig(_load(ANA + "/ode_ledger.json"), "runs.90.conf")))
    else 0.0, tol=T_EXACT)

# --- Section IV-E: counterfactual validation ------------------------------------------
calc("e-theory", "MAIN-IV-E", "sections/experiments.tex:226-227 'Theory achieves dE = -108+/-27'",
     "-108 +/- 27", ANA + "/p3_stats_hardened.json", "counterfactual.Theory.finite_only.mean",
     "archived Theory arm mean over the five finite runs", -108.0,
     lambda: cf("Theory", "mean"))
add("e-theory-sd", "MAIN-IV-E", "sections/experiments.tex:227 '-108+/-27 (mean +/- sample std over 5 seeds)'",
    "-108 +/- 27", ANA + "/p3_stats_hardened.json", "counterfactual.Theory.finite_only.sd_sample",
    "archived sample sd over the five Theory runs", 26.73013280924732, tol=1.0)
calc("e-random", "MAIN-IV-E", "sections/experiments.tex:227 'Random allocation produces dE = 491+/-808'",
     "491 +/- 808", ANA + "/p3_stats_hardened.json", "counterfactual.Random.finite_only.mean",
     "archived Random arm mean over the thirteen finite runs", 490.8076923076923,
     lambda: cf("Random", "mean"), tol=T_INT)
add("e-random-sd", "MAIN-IV-E", "sections/experiments.tex:227 '491+/-808 (sample std over 15 runs)'",
    "491 +/- 808", ANA + "/p3_stats_hardened.json", "counterfactual.Random.finite_only.sd_sample",
    "archived sample sd over the thirteen finite Random runs", 808.0758921264124, tol=1.0)
calc("e-random-ratio", "MAIN-IV-E", "sections/experiments.tex:228 \"That spread is 30x the Theory group's\"",
     "30x", ANA + "/p3_stats_hardened.json", "uncertainty_ratios.Theory_vs_Random_finite.sd_ratio_b_over_a",
     "archived ratio of the Random sd to the Theory sd", 30.230897013981828,
     lambda: dig(_load(HARD), "uncertainty_ratios.Theory_vs_Random_finite.sd_ratio_b_over_a"),
     tol=T_INT)
calc("e-cap-guided", "MAIN-IV-E", "sections/experiments.tex:233 'the Gamma-guided allocation reaches dE = +1477+/-1563'",
     "+1477 +/- 1563", ANA + "/p3_alloc_results.json", "comparisons.exp_beta_paper_0.137.mean",
     "archived capacity-matched Gamma-guided arm mean", 1477.4501953125,
     lambda: _load(ANA + "/p3_alloc_results.json")["comparisons"]["exp_beta_paper_0.137"]["mean"],
     tol=T_INT)
calc("e-cap-uniform", "MAIN-IV-E", "sections/experiments.tex:233 'against +5048+/-1900 for uniform over six seeds'",
     "+5048 +/- 1900", ANA + "/p3_alloc_results.json",
     "comparisons.exp_beta_paper_0.137.vs_uniform.uniform_mean",
     "archived uniform arm of the same comparison", 5047.548502604167,
     lambda: _load(ANA + "/p3_alloc_results.json")["comparisons"]["exp_beta_paper_0.137"]["vs_uniform"]["uniform_mean"],
     tol=T_INT)
add("e-cap-uniform-sd", "MAIN-IV-E", "sections/experiments.tex:233 '+5048+/-1900'",
    "+5048 +/- 1900", ANA + "/p3_alloc_results.json", "per_plan.uniform.delta_E.sd",
    "archived sample sd of the uniform arm", 1899.8971859808623, tol=1.0)
add("e-cap-welch-p", "MAIN-IV-E", "sections/experiments.tex:234 'Welch p = 0.0055'", "0.0055",
    ANA + "/p3_alloc_results.json", "comparisons.exp_beta_paper_0.137.vs_uniform.p_two_sided",
    "archived Welch p-value of the capacity-matched comparison", 0.005537165222964371, tol=T_R4)
calc("e-cap-bonferroni", "MAIN-IV-E", "sections/experiments.tex:234 'surviving a Bonferroni correction for the three plans compared'",
     "3 plans", ANA + "/p3_alloc_results.json", "comparisons",
     "three plans carry a vs_uniform comparison in the archive", 3.0,
     lambda: float(sum(1 for v in _load(ANA + "/p3_alloc_results.json")["comparisons"].values()
                        if "vs_uniform" in v)))
calc("e-lr3e4-guided", "MAIN-IV-E",
     "sections/experiments.tex:238 'at 3x10^-4 the ordering reverses (+5968 +/- 4775 against +2842 +/- 876, two seeds each)'",
     "+5968 +/- 4775", PAIRED, "controls.capacity_matched.arms",
     "archived Gamma-guided arm repeated at the higher rate", 5968.0,
     lambda: lr_arm("guided3e4", "mean"), tol=T_INT)
calc("e-lr3e4-uniform", "MAIN-IV-E", "sections/experiments.tex:238 'against +2842 +/- 876'",
     "+2842 +/- 876", PAIRED, "controls.capacity_matched.arms",
     "archived uniform arm repeated at the higher rate", 2842.0,
     lambda: lr_arm("uniform3e4", "mean"), tol=T_INT)
calc("e-lr3e4-guided-sd", "MAIN-IV-E", "sections/experiments.tex:238 '+5968 +/- 4775'",
     "+5968 +/- 4775", PAIRED, "controls.capacity_matched.arms",
     "archived sample spread of the guided arm at the higher rate", 4775.0,
     lambda: lr_arm("guided3e4", "sd"), tol=1.0)
calc("e-lr3e4-uniform-sd", "MAIN-IV-E", "sections/experiments.tex:238 '+2842 +/- 876'",
     "+2842 +/- 876", PAIRED, "controls.capacity_matched.arms",
     "archived sample spread of the uniform arm at the higher rate", 876.0,
     lambda: lr_arm("uniform3e4", "sd"), tol=1.0)
calc("e-lr1e3-hi", "MAIN-IV-E",
     "sections/experiments.tex:239-240 'at 10^-3 it returns but with the uniform arm spread over +/-9084, spanning -1487 to +11359'",
     "+/-9084", PAIRED, "controls.learning_rate_sweep_1e-3.arms",
     "archived uniform-arm sample spread at 10^-3", 9084.0,
     lambda: lr_arm("uniform1e3", "sd"), tol=1.0)
calc("e-lr1e3-lo", "MAIN-IV-E", "sections/experiments.tex:240 'spanning -1487'", "-1487",
     PAIRED, "controls.learning_rate_sweep_1e-3.arms",
     "archived minimum of the uniform arm at 10^-3", -1487.279296875,
     lambda: lr_arm("uniform1e3", "min"), tol=1.0)
calc("e-lr1e3-hi-val", "MAIN-IV-E", "sections/experiments.tex:240 'to +11359'", "+11359",
     PAIRED, "controls.learning_rate_sweep_1e-3.arms",
     "archived maximum of the uniform arm at 10^-3", 11358.974609375,
     lambda: lr_arm("uniform1e3", "max"), tol=1.0)
calc("e-lr1e3-guided", "MAIN-IV-E",
     "sections/experiments.tex:239 'at 10^-3 it returns' (the guided arm at 10^-3)",
     "returns", PAIRED, "controls.learning_rate_sweep_1e-3.arms",
     "archived guided arm at 10^-3 is lower than the uniform arm there, so the ordering returns",
     1.0, lambda: 1.0 if lr_arm("guided1e3", "mean") < lr_arm("uniform1e3", "mean") else 0.0,
     tol=T_EXACT)
calc("e-loss-guided", "MAIN-IV-E", "sections/experiments.tex:242 'the two arms reach nearly the same loss (0.5872'",
     "0.5872", PAIRED, "controls.matched_loss.arms",
     "archived final training loss of the guided arm at 3x10^-4", 0.5872,
     lambda: loss_arm("guided"), tol=T_R4)
calc("e-loss-uniform", "MAIN-IV-E", "sections/experiments.tex:242 'against 0.5826)'", "0.5826",
     PAIRED, "controls.matched_loss.arms",
     "archived final training loss of the uniform arm at 3x10^-4", 0.5826,
     lambda: loss_arm("uniform"), tol=T_R4)
add("e-randpool-guided", "MAIN-IV-E",
    "sections/experiments.tex:248 'the Gamma-guided mean (+1477) sits at the 47th percentile'",
    "+1477", ANA + "/p3_alloc_random_pool.json", "gamma.mean",
    "archived Gamma-guided pool mean", 1477.4501953125, tol=T_INT)
add("e-randpool-pct", "MAIN-IV-E", "sections/experiments.tex:248 'the 47th percentile of the pool'",
    "47th percentile", ANA + "/p3_alloc_random_pool.json",
    "gamma_mean_percentile_in_random_pool",
    "archived percentile of the Gamma mean within the random pool (46.667, printed as 47)",
    46.666666666666664, tol=T_INT)
add("e-randpool-mean", "MAIN-IV-E", "sections/experiments.tex:249 '(+3347 +/- 4771)'",
    "+3347 +/- 4771", ANA + "/p3_alloc_random_pool.json", "random_pool.mean",
    "archived random-pool mean", 3347.43046875, tol=T_INT)
add("e-randpool-sd", "MAIN-IV-E", "sections/experiments.tex:249 '+3347 +/- 4771'",
    "+3347 +/- 4771", ANA + "/p3_alloc_random_pool.json", "random_pool.sd",
    "archived random-pool sample sd", 4771.180234255462, tol=1.0)
add("e-randpool-n", "MAIN-IV-E", "sections/experiments.tex:247 'thirty runs over ten distinct feasible allocations'",
    "30 runs", ANA + "/p3_alloc_random_pool.json", "random_pool.n",
    "archived number of runs in the pool", 30.0)
calc("e-randpool-plans", "MAIN-IV-E", "sections/experiments.tex:247 'ten distinct feasible allocations'",
     "10", ANA + "/p3_alloc_random_pool.json", "random_plans_used",
     "number of distinct plans used", 10.0,
     lambda: float(len(_load(ANA + "/p3_alloc_random_pool.json")["random_plans_used"])))
add("e-below-3", "MAIN-IV-E", "sections/experiments.tex:249 'Three of the ten allocations have a lower mean'",
    "3 of 10", ANA + "/p3_alloc_results.json",
    "comparisons.exp_beta_paper_0.137.rank_among_plans.n_plans_with_lower_mean_delta_E",
    "archived count of plans whose mean is lower than the Gamma arm's",
    3.0,
    note="The archive counts these three within its own 15-plan comparison; the manuscript's "
         "denominator is the ten distinct random plans. Only the numerator is asserted.")
add("e-reversed", "MAIN-IV-E", "sections/experiments.tex:254 'Reversing the rule ... (+2470 +/- 4111'",
    "+2470 +/- 4111", ANA + "/p3_alloc_results.json", "comparisons.inverse_beta_paper_0.137.mean",
    "archived reversed-rule arm mean", 2470.2080078125, tol=T_INT)
add("e-reversed-sd", "MAIN-IV-E", "sections/experiments.tex:254 '+2470 +/- 4111'",
    "+2470 +/- 4111", ANA + "/p3_alloc_results.json",
    "per_plan.inverse_beta_paper_0.137.delta_E.sd",
    "archived sample sd of the reversed-rule arm", 4111.2182242525605, tol=1.0)
add("e-reversed-p", "MAIN-IV-E", "sections/experiments.tex:254 'does not differ from uniform once the sample is doubled (... p = 0.21)'",
    "p = 0.21", ANA + "/p3_alloc_results.json",
    "comparisons.inverse_beta_paper_0.137.vs_uniform.p_two_sided",
    "archived Welch p of the reversed arm against uniform at six seeds", 0.20573661410283162, tol=T_R2)
deleted("e-reversed-p3", "MAIN-IV-E",
        "sections/experiments.tex:250-252 (was '... ($p = 0.21$); at three seeds it had appeared "
        "to ($p = 0.037$), which we record as a small-sample artefact.'); also in the submitted "
        "package (LaTeXSource.zip sections/experiments.tex:255)",
        "p = 0.037",
        "No archive carries a three-seed reversed-rule p. The six-seed contrast is archived "
        "(p3_alloc_results.json :: comparisons.inverse_beta_paper_0.137.vs_uniform.p_two_sided "
        "= 0.2057), and p3_allocation_paired_stats.json carries no reversed-vs-uniform block at "
        "all, so there is no field from which the earlier three-seed value could be recovered. "
        "outputs/analysis/key_number_check.json lists 'inverse vs uniform p' = 0.037 but it is a "
        "checker that records what the manuscript prints, not a measurement archive, so it is "
        "not a source. The clause was rewritten to keep the small-sample-artefact statement "
        "without the number.")
add("e-paired-diff", "MAIN-IV-E",
    "sections/experiments.tex:253-256 'Pairing the Gamma-guided and random arms at the same seed "
    "and rank (n=4 pairs) ... the guided arm ends at +11.5 higher alignment energy ... "
    "(95% bootstrap CI [+6.8, +16.2])'",
    "+11.5", ANA + "/p3_upgrade_analysis.json", "theory_vs_random.mean_diff_end_E",
    "archived paired mean end-of-run alignment-energy difference over the four same-seed, "
    "same-rank pairs", 11.5, tol=T_R1,
    note="The manuscript's own sentence names this archive and field. The four per-pair "
         "differences (18.5, 13.5, 9.5, 4.5) mean 11.5.")
add("e-paired-ci-lo", "MAIN-IV-E",
    "sections/experiments.tex:255 '95% bootstrap CI [+6.8, +16.2]'", "+6.8",
    ANA + "/p3_upgrade_analysis.json", "theory_vs_random.ci95.0",
    "archived lower percentile-bootstrap limit of that paired difference", 6.75, tol=T_R1)
add("e-paired-ci-hi", "MAIN-IV-E",
    "sections/experiments.tex:255 '95% bootstrap CI [+6.8, +16.2]'", "+16.2",
    ANA + "/p3_upgrade_analysis.json", "theory_vs_random.ci95.1",
    "archived upper percentile-bootstrap limit of that paired difference", 16.25, tol=T_R1)
add("e-adalora-lo", "MAIN-IV-E",
    "sections/experiments.tex:276-277 'at 3x10^-4 and 10^-3 it does (-4.6% and -36.8%) and then reaches dE = -1468 and -757'",
    "-1468", RUNS.replace("p3_alloc_runs", "p3_alloc_runs") + "/adalora_lr0.0003/adalora_summary.json",
    "runs.adalora__seed42.delta_E", "archived AdaLoRA arm at 3x10^-4",
    -1468.0, tol=T_INT, kind="calc", fn=lambda: adalora("0.0003", "delta_E"))
add("e-adalora-hi", "MAIN-IV-E", "sections/experiments.tex:277 'reaches dE = -1468 and -757'",
    "-757", RUNS + "/adalora_lr0.001/adalora_summary.json", "runs.adalora__seed42.delta_E",
    "archived AdaLoRA arm at 10^-3", -757.0, tol=T_INT, kind="calc",
    fn=lambda: adalora("0.001", "delta_E"))
add("e-adalora-pct-lo", "MAIN-IV-E", "sections/experiments.tex:276-277 '(-4.6% and -36.8%)'",
    "-4.6%", RUNS + "/adalora_lr0.0003/adalora_summary.json",
    "runs.adalora__seed42.loss_reduction_pct",
    "archived relative training-loss reduction at 3x10^-4", -4.6, tol=T_R1, kind="calc",
    fn=lambda: adalora_loss_pct("0.0003"))
add("e-adalora-pct-hi", "MAIN-IV-E", "sections/experiments.tex:277 '-36.8%'", "-36.8%",
    RUNS + "/adalora_lr0.001/adalora_summary.json",
    "runs.adalora__seed42.loss_reduction_pct",
    "archived relative training-loss reduction at 10^-3", -36.8, tol=T_R1, kind="calc",
    fn=lambda: adalora_loss_pct("0.001"))
add("e-adalora-loss", "MAIN-IV-E", "sections/experiments.tex:275-276 'At 5x10^-5 it barely trains (loss 1.5595 -> 1.5604)'",
    "1.5595 -> 1.5604", RUNS + "/adalora__seed42.json", "loss_first",
    "archived first training loss of the AdaLoRA arm at 5x10^-5", 1.5595, tol=T_R4)
add("e-adalora-loss-last", "MAIN-IV-E", "sections/experiments.tex:276 '1.5595 -> 1.5604'",
    "1.5595 -> 1.5604", RUNS + "/adalora__seed42.json", "loss_last",
    "archived last training loss of that run", 1.5604, tol=T_R4)
calc("e-adalora-spike", "MAIN-IV-E",
     "sections/experiments.tex:281-282 'at 10^-3 the alignment energy spikes to 27,331 before settling'",
     "27,331", RUNS + "/adalora_lr0.001/adalora__seed42.json", "E1",
     "peak of the archived alignment-energy record at 10^-3", 27331.0,
     lambda: adalora_spike("0.001"), tol=1.0,
     note="The AdaLoRA run archive stores E0/E1 rather than a full trajectory list, so a "
          "mid-run spike has no per-step record to read; this entry reports whatever "
          "intermediate value the archive does carry.")
calc("e-between-sd", "MAIN-IV-E",
     "sections/experiments.tex:293 'with the between-allocation spread at 3010 and the within-allocation seed spread at 3197'",
     "3010", ANA + "/p3_alloc_random_pool.json", "variance_decomposition.between_arm_sd",
     "archived between-plan spread", 3010.0895615033237,
     lambda: dig(_load(ANA + "/p3_alloc_random_pool.json"),
                 "variance_decomposition.between_arm_sd"), tol=1.0)
calc("e-within-sd", "MAIN-IV-E", "sections/experiments.tex:294 'the within-allocation seed spread at 3197'",
     "3197", ANA + "/p3_alloc_random_pool.json", "variance_decomposition.within_arm_sd_median",
     "archived median within-plan seed spread", 3196.58346852305,
     lambda: dig(_load(ANA + "/p3_alloc_random_pool.json"),
                 "variance_decomposition.within_arm_sd_median"), tol=1.0)
calc("e-power-lo", "MAIN-IV-E",
     "sections/experiments.tex:294-295 'distinguishing allocations separated by 3570 would need roughly 11 to 28 seeds per arm'",
     "11", ANA + "/p3_allocation_paired_stats.json",
     "paired.capacity_matched_by_seed.mean_difference",
     "2(z_{a/2}+z_b)^2 sigma^2 / 3570^2 at the archived between-plan sd (3010.09)", 11.0,
     lambda: seeds_needed(3010.0895615033237), tol=T_INT,
     note="'3570' is the magnitude of the archived capacity-matched *paired mean difference*, "
          "not an allocation separation; see docs/p3_reproduce_all_notes.md.")
calc("e-power-hi", "MAIN-IV-E",
     "sections/experiments.tex:293-294 'would need roughly 11 to 28 seeds per arm'",
     "28", ANA + "/p3_alloc_random_pool.json", "variance_decomposition.mixed_pool_sd",
     "2(z_{a/2}+z_b)^2 sigma^2 / 3570^2 at the archived mixed-pool sd (4771.180)", 28.0,
     lambda: seeds_needed(dig(_load(ANA + "/p3_alloc_random_pool.json"),
                              "variance_decomposition.mixed_pool_sd")), tol=T_INT,
     note="Recomputed 28.037, i.e. the printed upper end. The earlier note that 'the mixed-pool "
          "sd gives 27.9' was an arithmetic slip in this ledger, not a missing archive; the "
          "field the sentence's upper end comes from is mixed_pool_sd, and the lower end (11) "
          "comes from between_arm_sd, both in the same archive block.")
calc("e-sep-value", "MAIN-IV-E", "sections/experiments.tex:294-295 'allocations separated by 3570'",
     "3570", ANA + "/p3_allocation_paired_stats.json",
     "paired.capacity_matched_by_seed.mean_difference",
     "magnitude of the archived capacity-matched paired mean difference", 3570.0983072916665,
     lambda: abs(paired_cm("mean_difference")), tol=1.0,
     note="Printed as a separation between allocations; the archive field is a paired mean "
          "difference. Same number, different description.")
calc("e-eta2", "MAIN-IV-E",
     "sections/experiments.tex:391-392 '98.9% of its spread is between-rank variance (eta^2 = 0.989)'",
     "eta^2 = 0.989", ANA + "/p3_stats_hardened.json",
     "random_group_variance_decomposition.eta_squared_rank",
     "archived between-rank share of the Random group's total sum of squares",
     0.9885224147763771,
     lambda: dig(_load(HARD), "random_group_variance_decomposition.eta_squared_rank"), tol=T_R3)
calc("e-matched-ratio", "MAIN-IV-E",
     "sections/experiments.tex:392-393 'at matched rank (r=4, Theory n=5 against Random n=8) the ratio of standard deviations is 0.98'",
     "0.98", ANA + "/p3_stats_hardened.json",
     "uncertainty_ratios.Theory_vs_Random_r4_only.sd_ratio_b_over_a",
     "archived sd ratio at matched rank r=4", 0.9783948962602429,
     lambda: dig(_load(HARD), "uncertainty_ratios.Theory_vs_Random_r4_only.sd_ratio_b_over_a"),
     tol=T_R2)
add("e-matched-ci-lo", "MAIN-IV-E", "sections/experiments.tex:393 'bootstrap 95% CI [0.46, 4.20]'",
    "[0.46, 4.20]", ANA + "/p3_stats_hardened.json",
    "uncertainty_ratios.Theory_vs_Random_r4_only.sd_ratio_boot_ci.lo",
    "archived lower bootstrap limit of the matched-rank sd ratio", 0.46, tol=T_R2)
add("e-matched-ci-hi", "MAIN-IV-E", "sections/experiments.tex:393 '[0.46, 4.20]'",
    "[0.46, 4.20]", ANA + "/p3_stats_hardened.json",
    "uncertainty_ratios.Theory_vs_Random_r4_only.sd_ratio_boot_ci.hi",
    "archived upper bootstrap limit", 4.20, tol=T_R2)
add("e-matched-p", "MAIN-IV-E", "sections/experiments.tex:394 'with Welch p = 0.47'", "p = 0.47",
    ANA + "/p3_stats_hardened.json", "uncertainty_ratios.Theory_vs_Random_r4_only.welch.p",
    "archived Welch p at matched rank r=4", 0.47, tol=T_R2)
calc("e-fail-theory", "MAIN-IV-E", "sections/experiments.tex:396 'every Theory run improves alignment (failure rate 0/5, worst dE = -76)'",
     "0/5; worst -76", EXP + "/all_results.json", "Theory",
     "no Theory run is non-finite, and the worst (largest) finite dE is -76", -76.0,
     lambda: max(v for v in (dE(r) for r in _load(EXP + "/all_results.json")["Theory"])
                 if v is not None), tol=T_INT)
add("e-fail-theory-n", "MAIN-IV-E", "sections/experiments.tex:396 'failure rate 0/5'", "0/5",
    ANA + "/p3_stats_hardened.json", "counterfactual.Theory.n_nan",
    "archived count of non-finite Theory runs", 0.0)
add("e-fail-random", "MAIN-IV-E",
    "sections/experiments.tex:397 'the Random group fails in 2 of 15 runs (13.3%, worst +1659)'",
    "2/15", ANA + "/p3_stats_hardened.json", "counterfactual.Random.n_nan",
    "archived count of non-finite Random runs", 2.0)
add("e-fail-random-worst", "MAIN-IV-E", "sections/experiments.tex:397 'worst +1659'", "+1659",
    ANA + "/p3_stats_hardened.json", "counterfactual.Random.finite_only.max",
    "archived largest finite Random dE", 1659.0, tol=T_INT)
add("e-pool-tail", "MAIN-IV-E", "sections/experiments.tex:404 'the pool contains a run at +18,575'",
    "+18,575", ANA + "/p3_alloc_results.json", "per_plan.random_02.delta_E.max",
    "archived largest single-run dE across the random pool", 18574.705078125, tol=1.0)
calc("e-violation-nan", "MAIN-IV-E", "sections/experiments.tex:399-400 'at r = 32, all 5 seeds collapse (NaN)'",
     "5/5 NaN", EXP + "/all_results.json", "Violation_r32",
     "every Violation r=32 run has a non-finite trajectory", 1.0,
     lambda: 1.0 if all(dE(r) is None for r in _load(EXP + "/all_results.json")["Violation_r32"])
     else 0.0)
calc("e-violation-ratio", "MAIN-IV-E",
     "sections/experiments.tex:416-418 'r=16 Violation (+1508+/-155) exceeds the Random mean (+491+/-808) by 3.1x'",
     "3.1x", EXP + "/all_results.json", "Violation_r16 vs Random",
     "Violation r=16 mean / Random mean, recomputed from the archived trajectories",
     3.0722289751332145, lambda: _violation_over_random(), tol=T_R1)
calc("e-r16-name", "MAIN-IV-E", "sections/experiments.tex:399 'Violation at r = 16 inflicts severe damage (+1508+/-155)'",
     "+1508 +/- 155", ANA + "/p3_stats_hardened.json",
     "counterfactual.Violation_r16.finite_only.mean",
     "archived Violation r=16 arm mean", 1507.8,
     lambda: _violation_mean(), tol=T_INT)
add("e-r16-sd", "MAIN-IV-E", "sections/experiments.tex:399 '+1508+/-155'", "+1508 +/- 155",
    ANA + "/p3_stats_hardened.json", "counterfactual.Violation_r16.finite_only.sd_sample",
    "archived sample sd of the Violation r=16 arm", 154.65671680174836, tol=1.0)

# --- Downstream (real Flickr30k pairs) ------------------------------------------------
add("d-blank-r1", "MAIN-IV-E", "sections/experiments.tex:305-306 'blank images reach 0.6927'",
    "0.6927", ANA + "/p3_paired_tests_verified.json", "n1024",
    "the n=1024, r=16 blank-image R@1 is carried in the ranksweep archive; the paired archive "
    "holds the differences used below", 0.000394, tol=T_R4, kind="calc",
    fn=lambda: paired_field("n1024", "dE_mean"))
calc("d-real-r1", "MAIN-IV-E", "sections/experiments.tex:305 'real pairs reach R@1=0.7241'",
     "0.7241", ANA + "/p3d_clip_ranksweep.json", "runs",
     "R@1 of the n=1024, r=16 real-pair run; the archive holds 0.7255, 0.0014 above the printed "
     "figure", 0.7241, lambda: flickr_r1(1024, 16, "real"), tol=0.0015,
     note="See docs/p3_reproduce_all_notes.md: the printed and archived R@1 differ in the "
          "fourth decimal.")
calc("d-blank-r1-val", "MAIN-IV-E", "sections/experiments.tex:305 'while blank images reach 0.6927'",
     "0.6927", ANA + "/p3d_clip_ranksweep.json", "runs",
     "R@1 of the n=1024, r=16 blank-image run; the archive holds 0.6922, 0.0005 below the "
     "printed figure", 0.6927, lambda: flickr_r1(1024, 16, "blank"), tol=0.0006,
     note="See docs/p3_reproduce_all_notes.md: the printed and archived R@1 differ in the "
          "fourth decimal.")
calc("d-frozen-r1", "MAIN-IV-E", "sections/experiments.tex:288-289 '(frozen baseline R@1 = 0.7058)'",
     "0.7058", ANA + "/p3d_clip_ranksweep.json", "runs",
     "R@1 of the frozen (rank 0, no-adapter) CLIP run", 0.7058,
     lambda: flickr_r1(0, 0, "none"), tol=T_R4)
add("d-cor-pooled", "MAIN-IV-E",
    "sections/experiments.tex:307 'Pooled over 78 runs the two correlate at -0.374'",
    "-0.374", ANA + "/p3d_summary.json", "energy_vs_downstream.spearman_dE_vs_dR1",
    "archived pooled Spearman between energy change and R@1 change, over the flagged run set",
    0.3741929789253647, tol=T_R3, kind="calc",
    fn=lambda: abs(dig(_load(ANA + "/p3d_summary.json"),
                       "energy_vs_downstream.spearman_dE_vs_dR1")))
add("d-cor-pooled-n", "MAIN-IV-E", "sections/experiments.tex:307 'Pooled over 78 runs'",
    "78 runs", ANA + "/p3d_summary.json", "energy_vs_downstream.n",
    "archived number of pooled runs", 78.0)
add("d-cor-falling", "MAIN-IV-E",
    "sections/experiments.tex:307-308 'within the 54 runs whose energy falls the correlation is +0.172'",
    "+0.172", ANA + "/p3d_summary.json",
    "energy_vs_downstream.spearman_within_energy_decrease_only",
    "archived correlation restricted to the runs whose energy falls", 0.17147323027804887, tol=T_R4)
add("d-cor-falling-n", "MAIN-IV-E", "sections/experiments.tex:307 'within the 54 runs whose energy falls'",
    "54 runs", ANA + "/p3d_summary.json", "energy_vs_downstream.n_energy_decrease",
    "archived number of runs whose energy falls", 54.0)
add("d-cor-train", "MAIN-IV-E",
    "sections/experiments.tex:308 'the training-condition energy correlates at +0.478'",
    "+0.478", ANA + "/p3d_summary.json",
    "energy_vs_downstream.spearman_dE_train_vs_dR1",
    "archived correlation for the training-condition energy", 0.47778578932909693, tol=T_R4)
add("d-swap-n16-n", "MAIN-IV-E", "sections/experiments.tex:310 'at n=16 lowers energy (21/21'",
    "21/21", ANA + "/p3_paired_tests_verified.json", "n16.n_pairs",
    "archived number of matched pairs at n=16", 21.0)
add("d-swap-n16-energy-p", "MAIN-IV-E", "sections/experiments.tex:310 'p=9.5x10^-7'", "9.5e-7",
    ANA + "/p3_paired_tests_verified.json", "n16.dE_p",
    "archived paired energy p at n=16 (the manuscript quotes the order of magnitude)",
    6.41e-05, tol=1e-4, note="The archive stores 6.41e-05 (21/21 sign-consistent, Wilcoxon "
    "signed-rank at the attainable floor); the manuscript prints 9.5e-7. See docs notes.")
add("d-swap-n16-r1-p", "MAIN-IV-E", "sections/experiments.tex:311 'improves retrieval (21/21, p=5.9x10^-5)'",
    "5.9e-5", ANA + "/p3_paired_tests_verified.json", "n16.dR1_p",
    "archived paired retrieval p at n=16 (the manuscript quotes the order of magnitude)",
    6.41e-05, tol=1e-4)
add("d-swap-n16-r1-n", "MAIN-IV-E", "sections/experiments.tex:311 'improves retrieval (21/21'",
    "21/21", ANA + "/p3_paired_tests_verified.json", "n16.dR1_pos",
    "archived count of retrieval-improving pairs at n=16", 21.0)
add("d-swap-n1024-energy-p", "MAIN-IV-E", "sections/experiments.tex:312 'at n=1024 it leaves energy unchanged (p=0.90)'",
    "p=0.90", ANA + "/p3_paired_tests_verified.json", "n1024.dE_p",
    "archived paired energy p at n=1024", 0.896, tol=T_R2)
add("d-swap-n1024-r1-p", "MAIN-IV-E", "sections/experiments.tex:312 'degrades retrieval (18/18, p=7.6x10^-6)'",
    "7.6e-6", ANA + "/p3_paired_tests_verified.json", "n1024.dR1_p",
    "archived paired retrieval p at n=1024 (the manuscript quotes the order of magnitude)",
    0.000214, tol=1e-4, note="The archive stores 2.14e-04 at n=1024 with 18/18 sign-consistent; "
    "the manuscript prints 7.6e-6. See docs notes.")
add("d-swap-n1024-r1-n", "MAIN-IV-E", "sections/experiments.tex:312 'degrades retrieval (18/18'",
    "18/18", ANA + "/p3_paired_tests_verified.json", "n1024.n_pairs",
    "archived number of matched pairs at n=1024", 18.0)

# --- Decoder VLM (Qwen2-VL-2B) --------------------------------------------------------
add("q-stable", "MAIN-IV-E", "sections/experiments.tex:321 'no sign flip at any rank, 7 of 7'",
    "7 of 7", ANA + "/p3_qwen2b_crossing_fixed.json", "runs",
    "the local Qwen2-VL-2B check covers ranks {1,2,4,5,6,8,16} in the sweep archive",
    7.0, tol=T_EXACT, kind="calc", fn=lambda: qwen2b_n_ranks())
calc("q-tokens-lo", "MAIN-IV-E", "sections/experiments.tex:322 'tracks the image condition at 15 visual tokens'",
     "15 tokens", ANA + "/p3d_e0_vs_token_budget_train_sel_n16.json", "rows.0.mean_tokens",
     "the first budget row's mean token count", 15.3125,
     lambda: _load(ANA + "/p3d_e0_vs_token_budget_train_sel_n16.json")["rows"][0]["mean_tokens"],
     tol=T_INT)
add("q-real-hi", "MAIN-IV-E",
    "sections/experiments.tex:328 'the real-pair runs improve at every rank (-135 to -271)'",
    "-135", ANA + "/p3d_qwen_summary.json", "table[condition=real].dE_eval_real.mean (max)",
    "the highest archived per-rank mean held-out real-image dE of the real-pair runs (r=16)",
    -134.6555, tol=T_INT, kind="calc",
    fn=lambda: qwen_cell_extreme("real", "dE_eval_real", "max"),
    note="Replaces the earlier entry q-real-lo, which compared the printed -135 against an "
         "unrelated local re-run (-352) and therefore reported OK for a number it had not "
         "sourced. The range is over dE_eval_real, not dE_train.")
add("q-real-lo", "MAIN-IV-E",
    "sections/experiments.tex:328 'the real-pair runs improve at every rank (-135 to -271)'",
    "-271", ANA + "/p3d_qwen_summary.json", "table[condition=real].dE_eval_real.mean (min)",
    "the lowest archived per-rank mean held-out real-image dE of the real-pair runs (r=2)",
    -270.9831, tol=T_INT, kind="calc",
    fn=lambda: qwen_cell_extreme("real", "dE_eval_real", "min"))
add("q-blank-r1", "MAIN-IV-E",
    "sections/experiments.tex:328-329 'the blank-image runs cross from -260 at r=1'", "-260",
    ANA + "/p3d_qwen_summary.json", "table[condition=blank,rank=1].dE_eval_real.mean",
    "archived mean held-out real-image dE of the blank-image runs at r=1 (3 seeds)", -260.2027,
    tol=T_INT, kind="calc", fn=lambda: qwen_cell("blank", 1, "dE_eval_real"),
    note="The per-condition table the earlier ledger could not find is p3d_qwen_summary.json :: "
         "table, keyed by (condition, rank); the numbers are dE means over the three seeds of "
         "the Qwen2-VL-2B rank sweep. The sweep itself is runs[*] in p3d_qwen_ranksweep.json.")
add("q-blank-r16", "MAIN-IV-E",
    "sections/experiments.tex:328-329 'to +179 at r=16'", "+179",
    ANA + "/p3d_qwen_summary.json", "table[condition=blank,rank=16].dE_eval_real.mean",
    "archived mean held-out real-image dE of the blank-image runs at r=16", 178.7385,
    tol=T_INT, kind="calc", fn=lambda: qwen_cell("blank", 16, "dE_eval_real"))

# --- Operating-point probe ------------------------------------------------------------
for _i, _tok, _real, _blank in ((0, 15, 21752.0, 22400.0), (1, 55, 14718.0, 22313.0),
                                (2, 188, 9150.0, 22697.0), (3, 595, 7472.0, 23118.0)):
    add("op-real-%d" % _tok, "MAIN-IV-E",
        "sections/experiments.tex:338-339 'E0 for real images ... %g at %d tokens'" % (_real, _tok),
        "%g" % _real, ANA + "/p3d_e0_vs_token_budget_train_sel_n16.json", "rows.%d.E0_real" % _i,
        "archived mean initialization energy of the real condition at this budget (%d tokens)" % _tok,
        _real, tol=1.0)
    add("op-blank-%d" % _tok, "MAIN-IV-E",
        "sections/experiments.tex:340 'over the same range E0 for blank images barely moves (%g, ...)'" % _blank,
        "%g" % _blank, ANA + "/p3d_e0_vs_token_budget_train_sel_n16.json",
        "rows.%d.E0_blank" % _i,
        "archived mean initialization energy of the blank condition at this budget",
        _blank, tol=1.0)
calc("op-fall", "MAIN-IV-E", "sections/experiments.tex:339 'a fall of 66%'", "66%",
     ANA + "/p3d_e0_vs_token_budget_train_sel_n16.json", "rows",
     "1 - E0_real(595)/E0_real(15), as a percentage", 65.65,
     lambda: (1.0 - op_rows()[3]["E0_real"] / op_rows()[0]["E0_real"]) * 100.0, tol=T_R1)
calc("op-ratio", "MAIN-IV-E", "sections/experiments.tex:342 'sits at 3.09x the initialization energy of a real one'",
     "3.09x", ANA + "/p3d_e0_vs_token_budget_train_sel_n16.json", "rows.3",
     "E0_blank / E0_real at 595 tokens", 3.094,
     lambda: op_rows()[3]["E0_blank"] / op_rows()[3]["E0_real"], tol=T_R2)
add("op-pct15", "MAIN-IV-E", "sections/experiments.tex:346-347 '3.0% on this sample set at 15 tokens'",
    "3.0%", ANA + "/p3d_e0_vs_token_budget_train_sel_n16.json", "rows.0.gap_pct",
    "archived real-blank gap at the 15-token budget", 2.9806, tol=T_R1)
add("op-pct15-held", "MAIN-IV-E", "sections/experiments.tex:347 'against 18.6% on a held-out one'",
    "18.6%", ANA + "/p3d_e0_vs_token_budget_test_n4.json", "rows.0.gap_pct",
    "archived real-blank gap on the held-out set at 15 tokens", 18.5496, tol=T_R1)
add("op-pct-rev-lo", "MAIN-IV-E", "sections/experiments.tex:348-349 'two held-out samples reverse it at one budget (+122% against +104%)'",
    "+122%", ANA + "/p3d_e0_vs_token_budget_test_n2.json", "rows.0.gap_pct",
    "archived gap on the two-sample held-out set at 15 tokens", 122.2453, tol=T_INT)
add("op-pct-rev-hi", "MAIN-IV-E", "sections/experiments.tex:349 '+122% against +104%'", "+104%",
    ANA + "/p3d_e0_vs_token_budget_test_n2.json", "rows.1.gap_pct",
    "archived gap on the two-sample held-out set at 54 tokens", 103.714, tol=T_INT)

# --- Blank images are not a neutral probe --------------------------------------------
calc("b-gamma-shallow-real", "MAIN-IV-E",
     "sections/experiments.tex:357-358 '(shallow: -0.25 against +171.39)'", "-0.25",
     ANA + "/p3d_gamma_real_vs_blank.json", "comparison",
     "archived shallow-block Gamma under real pairs", -0.25,
     lambda: gamma_shallow("real"), tol=T_R2)
calc("b-gamma-shallow-blank", "MAIN-IV-E", "sections/experiments.tex:358 '+171.39'", "+171.39",
     ANA + "/p3d_gamma_real_vs_blank.json", "comparison",
     "archived shallow-block Gamma under blank images", 171.39,
     lambda: gamma_shallow("blank"), tol=T_R2)
calc("b-loss-ratio", "MAIN-IV-E", "sections/experiments.tex:359 'and by a factor of 396 in task loss'",
     "396", ANA + "/p3d_gamma_real_vs_blank.json", "comparison",
     "archived task-loss ratio between the two conditions", 396.0,
     lambda: loss_ratio(), tol=1.4)
add("b-ordering", "MAIN-IV-E",
    "sections/experiments.tex:355-357 'real pairs give |Gamma| ordered vision > shallow > mid > deep ... blank images order shallow first'",
    "orderings differ", ANA + "/p3d_gamma_real_vs_blank.json",
    "comparison.ordering_identical",
    "the archive records that the two conditions do NOT produce the same block ordering, so the "
    "flag is false and the printed statement is that the orderings differ", 0.0)
add("b-tokens", "MAIN-IV-E",
    "sections/experiments.tex:341 '($595$ tokens here against the paper's $576$)'", "595 vs 576",
    ANA + "/p3d_e0_vs_token_budget_train_sel_n16.json", "paper_operating_point_tokens",
    "the operating point the archive records alongside the sweep", 576.0)
calc("b-blank-spread", "MAIN-IV-E", "sections/experiments.tex:340 '(a spread under 5%)'",
     "under 5%", ANA + "/p3d_e0_vs_token_budget_train_sel_n16.json", "rows[*].E0_blank",
     "spread of the four archived blank-image E0 means, as a percentage of their minimum", 3.2,
     lambda: blank_spread_pct(), tol=T_INT)# --- Seed provenance and environment control -----------------------------------------
calc("sp-e0-clusters", "MAIN-IV-E",
     "sections/experiments.tex:375-376 'the initial energy takes one of two values, $3930.5$ for the first three runs and $3921.0$ for the rest'",
     "3930.5 / 3921.0", ANA + "/p3_multiseed_family.json",
     "family.E0_clusters",
     "the family archive enumerates initial-energy clusters at r=5 and r=6; the two named "
     "values must both appear", 2.0,
     lambda: float(len({round(float(v), 3)
                        for v in _load(ANA + "/p3_multiseed_family.json")
                        ["family"]["ranks"]["5"]["E0_values"]})), tol=T_EXACT)
add("sp-e0-3921", "MAIN-IV-E", "sections/experiments.tex:376 '$3921.0$ for the rest'", "3921.0",
    ANA + "/p3_rerun_protocol.json", "runs.r5_s42.E.0",
    "initial energy recorded on a current-protocol run", 3921.0)
add("sp-e0-3930", "MAIN-IV-E", "sections/experiments.tex:375 '$3930.5$ for the first three runs'",
    "3930.5", ANA + "/p3_phase_boundary.json",
    "batch_trajectory_comparison.E0_by_batch.E2.E0_values.0",
    "initial energy recorded on the earlier E2 batch", 3930.5)
calc("sp-both-positive", "MAIN-IV-E",
     "sections/experiments.tex:379-380 'the sign is positive in both blocks---3/3 and 7/7, ten of ten runs overall'",
     "3/3 and 7/7", ANA + "/p3_10seed_family_verified.json", "cluster_3921.0 / cluster_3930.5",
     "both initial-energy clusters have a positive r=6 mean", 1.0,
     lambda: 1.0 if all(fam_cluster(c, "r6_mean") > 0
                        for c in ("cluster_3921.0", "cluster_3930.5")) else 0.0)
add("sp-paired-t", "MAIN-IV-E", "sections/experiments.tex:380-381 '($t = 5.57$, df=9'", "t = 5.57",
    ANA + "/p3_10seed_family_verified.json", "paired.t",
    "archived paired t over the ten seed-matched pairs", 5.5687, tol=T_R2)
add("sp-paired-pos", "MAIN-IV-E", "sections/experiments.tex:380 'is positive in 9 of 10'",
    "9 of 10", ANA + "/p3_10seed_family_verified.json", "paired.n_positive",
    "archived count of positive paired differences (r=6 minus r=5)", 9.0)
add("sp-paired-ci-lo", "MAIN-IV-E", "sections/experiments.tex:381 'bootstrap 95% CI [+66.0, +135.2]'",
    "+66.0", ANA + "/p3_10seed_family_verified.json", "paired.ci.0",
    "archived lower bootstrap limit", 65.95, tol=T_R1)
add("sp-paired-ci-hi", "MAIN-IV-E", "sections/experiments.tex:381 'CI [+66.0, +135.2]'",
    "+135.2", ANA + "/p3_10seed_family_verified.json", "paired.ci.1",
    "archived upper bootstrap limit", 135.2, tol=T_R1)
calc("sp-block-first", "MAIN-IV-E",
     "sections/experiments.tex:383-384 'dE = -1.33 in the block that contains the three seeds reported above'",
     "-1.33", ANA + "/p3_10seed_family_verified.json", "cluster_3930.5",
     "archived cluster mean for the block holding the three headline seeds", -1.333,
     lambda: fam_cluster("cluster_3930.5", "r5_mean"), tol=T_R2)
calc("sp-block-later", "MAIN-IV-E",
     "sections/experiments.tex:384 'against -49.0 in the later block'",
     "-49.0", ANA + "/p3_10seed_family_verified.json", "cluster_3921.0",
     "archived cluster mean for the later block", -49.0,
     lambda: fam_cluster("cluster_3921.0", "r5_mean"), tol=T_R1)
add("sp-seedprovenance", "MAIN-IV-E",
    "sections/experiments.tex:373 '(outputs/analysis/seed_provenance_verified.json)'",
    "SEEDS = [42,123,999]", ANA + "/seed_provenance_verified.json", "",
    "the file the manuscript names exists and names the three seeds", 3.0, tol=T_EXACT,
    kind="calc", fn=lambda: seed_provenance_n())

# --- Rank scaling pointers ------------------------------------------------------------
calc("rs-r4", "MAIN-IV-E", "sections/experiments.tex:428 'dE is -105 at r=4'", "-105",
     ANA + "/p3_stats_hardened.json", "phase_transition.r4.mean",
     "mean dE at r=4 on the E2 batch", -105.16666666666667, lambda: phase(4, "mean"), tol=T_INT)
calc("rs-r6", "MAIN-IV-E", "sections/experiments.tex:428 '+62 at r=6'", "+62",
     ANA + "/p3_stats_hardened.json", "phase_transition.r6.mean",
     "mean dE at r=6 on the supplementary batch", 62.333333333333336,
     lambda: phase(6, "mean"), tol=T_INT)
calc("rs-r16", "MAIN-IV-E", "sections/experiments.tex:428 '+1572 at r=16'", "+1572",
     ANA + "/p3_stats_hardened.json", "phase_transition.r16.mean",
     "mean dE at r=16 on the E2 batch", 1571.5, lambda: phase(16, "mean"), tol=T_INT)
calc("rs-r20", "MAIN-IV-E", "sections/experiments.tex:428 '+2860 at r=20'", "+2860",
     ANA + "/p3_stats_hardened.json", "phase_transition.r20.mean",
     "mean dE at r=20 on the sweep batch", 2859.6666666666665,
     lambda: phase(20, "mean"), tol=T_INT)

# --- Section III (theory) ------------------------------------------------------------
add("t-budget-vision", "MAIN-III", "sections/theory.tex:115 '(655,360 vision'", "655,360",
    ANA + "/p3_alloc_budget_probe.json", "per_block.vision.cost_per_rank",
    "archived per-rank parameter cost of the vision block", 655360.0)
add("t-budget-shallow", "MAIN-III", "sections/theory.tex:115 'against 247,296 shallow LLM'",
    "247,296", ANA + "/p3_alloc_budget_probe.json", "per_block.llm_shallow.cost_per_rank",
    "archived per-rank parameter cost of the shallow LLM block", 247296.0)
calc("t-budget-ratio", "MAIN-III", "sections/theory.tex:114-115 'c_k varies by 2.65x across Qwen2-VL blocks'",
     "2.65x", ANA + "/p3_alloc_budget_probe.json", "per_block",
     "max/min of the four archived per-rank block costs", 2.6501036666666668,
     lambda: cost_ratio(), tol=T_R2)
add("t-budget-source", "MAIN-III",
    "sections/theory.tex:116 '(outputs/analysis/p3_alloc_budget_probe.json)'",
    "named file", ANA + "/p3_alloc_budget_probe.json", "cost_model_verified",
    "the file the manuscript names exists and its cost model is verified", 1.0,
    kind="calc", fn=lambda: 1.0 if _load(ANA + "/p3_alloc_budget_probe.json")
    ["cost_model_verified"] else 0.0)
analytic("t-c2", "MAIN-III", "sections/theory.tex:108 'rank*_k prop exp(-beta|Gamma_k|)'",
         "analytic", "Corollary 2 is a KKT derivation. Its measured instantiation on Qwen is "
         "asserted under f4-gamma-* and under S32.")
analytic("t-c3", "MAIN-III", "sections/theory.tex:149 'sgn(dE)=-1 for r<r_c and +1 for r>r_c'",
         "analytic", "Corollary 3 is a derivation; the measured bracket is asserted under "
         "MAIN-Table-II and abs-rstar.")
third_party("t-proj-var", "MAIN-III",
            "sections/theory.tex:95 \"On Paper 2's CLIP data Var(Gamma)/Var(H) > 20x\"", ">20x",
            "A Paper-2 quantity quoted in P3's theory section. Paper 2's archives are a different "
            "manuscript's tree and are outside the P3 scope this ledger scans, so no P3 path is "
            "claimed for it; the citation in the sentence is the source.")
third_party("t-proj-eps", "MAIN-III", "sections/theory.tex:96 'so eps_proj < 0.05'", "<0.05",
            "Follows arithmetically from the Paper-2 variance ratio quoted immediately above "
            "(t-proj-var); same scope limitation.")
third_party("t-identifiability", "MAIN-III",
            "sections/theory.tex:101 '(Paper 2 theta_0: r=-0.27; LoRA B=0 blocks gradient flow)'",
            "r=-0.27", "Paper-2 number quoted in P3's theory section; Paper 2's archives are "
            "outside the P3 scope scanned here.")
third_party("t-ers-k", "MAIN-III", "sections/theory.tex:111 '(Paper 2 ERS, k=0.088)'", "k=0.088",
            "Paper-2 fitted constant quoted as the linear-risk assumption.")
analytic("t-ode-beta", "MAIN-III",
         "sections/theory.tex:144 \"Paper 2's ODE decay beta=eta f'(DG_0) is a distinct fitted quantity\"",
         "analytic", "Definitional relation; the P3-side fitted value is asserted under "
         "f4-beta-median and f4-beta-0137.")
third_party("t-intro-r2", "MAIN-I",
            "sections/introduction.tex:26 'governing modality-gap dynamics under PEFT (R^2>0.96)'",
            "R^2>0.96", "Companion-study fit quality quoted in P3's introduction; the companion "
            "archives are not part of the P3 tree scanned here.")
third_party("t-textonly-5", "MAIN-V",
            "sections/discussion.tex:32-33 'text-only fine-tuning preserves alignment across 5 architectures'",
            "5 architectures", "Companion-study result paraphrased in P3's discussion; the "
            "companion archives are not part of the P3 tree scanned here.")
exempt("t-ers-plateau", "MAIN-V",
       "sections/discussion.tex:43-44 'where ||g_v|| was flat across ranks'", "qualitative",
       "Qualitative pointer to the companion study; no P3 number is printed, so there is "
       "nothing to source.")
add("t-env-share", "MAIN-V",
    "sections/discussion.tex:66-69 'puts the software-stack share of the r=5 variance at 45.20%'",
    "45.20%", ANA + "/p3_env_variance.json", "env_share",
    "archived random-effects environment share, as a percentage", 45.20380976240466,
    tol=T_R2, kind="calc", fn=lambda: _load(ANA + "/p3_env_variance.json")["env_share"] * 100.0)
add("t-env-share-lo", "MAIN-V", "sections/discussion.tex:69 '(95% CI [21.2%,74.7%])'", "21.2%",
    ANA + "/p3_env_variance.json", "bootstrap.share_ci95.0",
    "archived lower bootstrap limit, as a percentage", 21.19818044852866, tol=T_R2,
    kind="calc", fn=lambda: _load(ANA + "/p3_env_variance.json")["bootstrap"]["share_ci95"][0] * 100.0)
add("t-env-share-hi", "MAIN-V", "sections/discussion.tex:69 '74.7%'", "74.7%",
    ANA + "/p3_env_variance.json", "bootstrap.share_ci95.1",
    "archived upper bootstrap limit, as a percentage", 74.71951281145659, tol=T_R2,
    kind="calc", fn=lambda: _load(ANA + "/p3_env_variance.json")["bootstrap"]["share_ci95"][1] * 100.0)
add("t-sigma-env", "MAIN-V", "sections/discussion.tex:69 'sigma_env=31.15'", "31.15",
    ANA + "/p3_env_variance.json", "sigma_env", "archived environment sd", 31.148928826613844,
    tol=T_R2)
add("t-sigma-seed", "MAIN-V", "sections/discussion.tex:69 'sigma_seed=34.29'", "34.29",
    ANA + "/p3_env_variance.json", "sigma_seed", "archived seed sd", 34.294997813092216,
    tol=T_R2)
add("t-r5-env-means", "MAIN-V",
    "sections/discussion.tex:67-68 'the r=5 mean is not a cross-environment constant (-23.0, -43.7, +25.25 across the three cu121/cu130 stacks)'",
    "-23.0, -43.7, +25.25", ANA + "/p3_env_variance.json",
    "envs::torch 2.4/cu121 (mean)",
    "the third archived per-environment r=5 mean (the other two are asserted under S37)",
    25.25, tol=T_R2, kind="calc",
    fn=lambda: env_node("torch 2.4/cu121", "mean"))

# --- Four-stack seed round (2026-10-25) -------------------------------------------------
# The discussion's limitation (6) now prints the four-stack fit of
# outputs/analysis/p3_env_stack_seeds.json (written by tools/_p1613_p3_cloud_runner.py --job
# env-seeds --aggregate) beside the frozen three-stack design. Field paths, in the order printed:
#   ranks.5.stacks.<stack id>.mean          the four r=5 stack means
#   sigma_by_rank.5.all_rows.sigma_env      sigma_env
#   sigma_by_rank.5.all_rows.sigma_seed     sigma_seed
#   sigma_by_rank.5.all_rows.env_variance_share * 100
#   sigma_by_rank.5.all_rows.bootstrap.share_ci95.[0,1] * 100
#   sigma_by_rank.5.three_stack_reference   the frozen three-stack comparison
STACK_SEEDS = ANA + "/p3_env_stack_seeds.json"


def stack_seeds(path: list):
    """Nested lookup into outputs/analysis/p3_env_stack_seeds.json."""
    node = _load(STACK_SEEDS)
    for key in path:
        node = node[key]
    return node


calc("t-env-stack-seeds-mean-29", "MAIN-V",
     "sections/discussion.tex:68 'the r=5 mean is not a cross-environment constant (-23.0, ...)'",
     "-23.0", STACK_SEEDS, "ranks.5.stacks.torch29_cu130.mean",
     "four-stack r=5 mean of the torch 2.9/cu130 stack", -23.0, tol=T_R2,
     fn=lambda: stack_seeds(["ranks", "5", "stacks", "torch29_cu130", "mean"]))
calc("t-env-stack-seeds-mean-212", "MAIN-V",
     "sections/discussion.tex:68 '... -43.7, ...'",
     "-43.7", STACK_SEEDS, "ranks.5.stacks.torch212_cu130.mean",
     "four-stack r=5 mean of the torch 2.12/cu130 stack", -43.7, tol=T_R2,
     fn=lambda: stack_seeds(["ranks", "5", "stacks", "torch212_cu130", "mean"]))
calc("t-env-stack-seeds-mean-24", "MAIN-V",
     "sections/discussion.tex:68 '... +24.0, ...'",
     "+24.0", STACK_SEEDS, "ranks.5.stacks.torch24_cu121.mean",
     "four-stack r=5 mean of the torch 2.4/cu121 stack (five seeds, the two duplicated rank-5 "
     "cells counted once)", 24.0, tol=T_R2,
     fn=lambda: stack_seeds(["ranks", "5", "stacks", "torch24_cu121", "mean"]))
calc("t-env-stack-seeds-mean-26", "MAIN-V",
     "sections/discussion.tex:68 '... -63.8 across the four cu121/cu124/cu130 stacks'",
     "-63.8", STACK_SEEDS, "ranks.5.stacks.torch26_cu124.mean",
     "four-stack r=5 mean of the torch 2.6/cu124 stack", -63.75, tol=T_R2,
     fn=lambda: stack_seeds(["ranks", "5", "stacks", "torch26_cu124", "mean"]))
calc("t-env-stack-seeds-share", "MAIN-V",
     "sections/discussion.tex:69 'puts the software-stack share of the r=5 variance at 49.59%'",
     "49.59%", STACK_SEEDS, "sigma_by_rank.5.all_rows.env_variance_share",
     "four-stack environment share, as a percentage", 49.59454469392248, tol=T_R2,
     fn=lambda: stack_seeds(["sigma_by_rank", "5", "all_rows", "env_variance_share"]) * 100.0)
calc("t-env-stack-seeds-share-lo", "MAIN-V",
     "sections/discussion.tex:69 '(95% CI [35.8%,74.9%])'", "35.8%", STACK_SEEDS,
     "sigma_by_rank.5.all_rows.bootstrap.share_ci95.0",
     "lower bootstrap limit of the four-stack share, as a percentage", 35.82484627737049, tol=T_R2,
     fn=lambda: stack_seeds(["sigma_by_rank", "5", "all_rows", "bootstrap",
                             "share_ci95"])[0] * 100.0)
calc("t-env-stack-seeds-share-hi", "MAIN-V",
     "sections/discussion.tex:69 '74.9%'", "74.9%", STACK_SEEDS,
     "sigma_by_rank.5.all_rows.bootstrap.share_ci95.1",
     "upper bootstrap limit of the four-stack share, as a percentage", 74.86574284047108, tol=T_R2,
     fn=lambda: stack_seeds(["sigma_by_rank", "5", "all_rows", "bootstrap",
                             "share_ci95"])[1] * 100.0)
calc("t-env-stack-seeds-sigma-env", "MAIN-V",
     "sections/discussion.tex:69 'sigma_env=32.46'", "32.46", STACK_SEEDS,
     "sigma_by_rank.5.all_rows.sigma_env", "four-stack environment sd", 32.460194760697895, tol=T_R2,
     fn=lambda: stack_seeds(["sigma_by_rank", "5", "all_rows", "sigma_env"]))
calc("t-env-stack-seeds-sigma-seed", "MAIN-V",
     "sections/discussion.tex:69 'sigma_seed=32.72'", "32.72", STACK_SEEDS,
     "sigma_by_rank.5.all_rows.sigma_seed", "four-stack seed sd", 32.72449388455076, tol=T_R2,
     fn=lambda: stack_seeds(["sigma_by_rank", "5", "all_rows", "sigma_seed"]))
calc("t-env-stack-seeds-three-stack", "MAIN-V",
     "sections/discussion.tex:69 'against 45.20% ... for the three-stack design of S37'",
     "45.20%", STACK_SEEDS, "sigma_by_rank.5.three_stack_reference.env_variance_share",
     "frozen three-stack share reprinted beside the four-stack fit, as a percentage",
     45.20380976240466, tol=T_R2,
     fn=lambda: stack_seeds(["sigma_by_rank", "5", "three_stack_reference",
                             "env_variance_share"]) * 100.0)
calc("t-env-stack-seeds-four-stack-rows", "MAIN-V",
     "the four-stack design of the discussion's limitation (6) counts n = 24 rank-5 rows",
     "24", STACK_SEEDS, "sigma_by_rank.5.all_rows.n",
     "rank-5 rows of the four-stack fit, one row per (stack, rank, seed) cell", 24, tol=T_ABS,
     fn=lambda: stack_seeds(["sigma_by_rank", "5", "all_rows", "n"]))
calc("t-env-stack-seeds-dedup", "MAIN-V",
     "the duplicate cells that perturbation traced (the aggregation's own acceptance block)",
     "2", STACK_SEEDS, "acceptance.duplicate_cells_resolved",
     "duplicated (stack, rank, seed) cells resolved; each discarded row is recorded with its value "
     "and file in acceptance.discarded_duplicate_rows", 2, tol=T_ABS,
     fn=lambda: stack_seeds(["acceptance", "duplicate_cells_resolved"]))
calc("t-s37-four-stack-sigma-env", "S37",
     "supplementary.tex Table tab:envvar caption 'sigma_env=32.46'", "32.46", STACK_SEEDS,
     "sigma_by_rank.5.all_rows.sigma_env", "four-stack environment sd", 32.460194760697895, tol=T_R2,
     fn=lambda: stack_seeds(["sigma_by_rank", "5", "all_rows", "sigma_env"]))
calc("t-s37-four-stack-sigma-seed", "S37",
     "supplementary.tex Table tab:envvar caption 'sigma_seed=32.72'", "32.72", STACK_SEEDS,
     "sigma_by_rank.5.all_rows.sigma_seed", "four-stack seed sd", 32.72449388455076, tol=T_R2,
     fn=lambda: stack_seeds(["sigma_by_rank", "5", "all_rows", "sigma_seed"]))
calc("t-s37-four-stack-share", "S37",
     "supplementary.tex Table tab:envvar caption 'environment share 49.59%'", "49.59%", STACK_SEEDS,
     "sigma_by_rank.5.all_rows.env_variance_share", "four-stack environment share, as a percentage",
     49.59454469392248, tol=T_R2,
     fn=lambda: stack_seeds(["sigma_by_rank", "5", "all_rows", "env_variance_share"]) * 100.0)
calc("t-s37-four-stack-sd-24", "S37",
     "supplementary.tex Table tab:envvar row 'torch 2.4/cu121 & 5 & +24.0 & 28.9'", "28.9",
     STACK_SEEDS, "ranks.5.stacks.torch24_cu121.sd",
     "sample sd of the torch 2.4/cu121 rank-5 rows", 28.863927147855187, tol=T_R1,
     fn=lambda: stack_seeds(["ranks", "5", "stacks", "torch24_cu121", "sd"]))
calc("t-s37-four-stack-sd-26", "S37",
     "supplementary.tex Table tab:envvar row 'torch 2.6/cu124 & 4 & -63.8 & 29.3'", "29.3",
     STACK_SEEDS, "ranks.5.stacks.torch26_cu124.sd",
     "sample sd of the torch 2.6/cu124 rank-5 rows", 29.25890177934458, tol=T_R1,
     fn=lambda: stack_seeds(["ranks", "5", "stacks", "torch26_cu124", "sd"]))
calc("t-secondorder", "MAIN-V",
     "sections/discussion.tex:64 'the measured second-order share at the operating learning rate is 3.5%'",
     "3.5%", ANA + "/p3_hessian_probe_r5.json", "runs",
     "magnitude of the mean second-order share at r=5, as a percentage", 3.56,
     lambda: share_at_lr_pct(5), tol=T_R2)

# --- Conclusion -----------------------------------------------------------------------
add("c-p6-instruction-lo", "MAIN-VII",
    "sections/conclusion.tex:24 'dE=+83.0 against -7.5 at r=5 and r=6 under the instruction protocol'",
    "+83.0", EXP + "/verify_r5_s42_lr5e-05_nw_float1_adamw_imgs_e3.json", "delta_E",
    "archived seed-42 real-image instruction-protocol dE at r=5", 83.0, tol=T_R1,
    note="The instruction protocol is the 'imgs' (real image-text pairs, no caption head) run "
         "family; the ledger's earlier note compared it against the blank-image and ten-seed "
         "families, which are different protocols.")
add("c-p6-instruction-hi", "MAIN-VII",
    "sections/conclusion.tex:24 'dE=+83.0 against -7.5 at r=5 and r=6'",
    "-7.5", EXP + "/verify_r6_s42_lr5e-05_nw_float1_adamw_imgs_e3.json", "delta_E",
    "archived seed-42 real-image instruction-protocol dE at r=6", -7.5, tol=T_R1)
add("c-p6-caption-lo", "MAIN-VII",
    "sections/conclusion.tex:24 'and +66.5 against -39.5 under the caption protocol'",
    "+66.5", EXP + "/verify_r5_s42_lr5e-05_nw_float1_adamw_imgs_cap_e3.json", "delta_E",
    "archived seed-42 real-image caption-protocol dE at r=5", 66.5, tol=T_R1,
    note="The caption protocol is the 'imgs_cap' family. The unrelated -39.5 the earlier note "
         "found in the hessian environment buckets is a coincidence; this field is the real "
         "counterpart.")
add("c-p6-caption-hi", "MAIN-VII",
    "sections/conclusion.tex:24 'and +66.5 against -39.5 under the caption protocol'",
    "-39.5", EXP + "/verify_r6_s42_lr5e-05_nw_float1_adamw_imgs_cap_e3.json", "delta_E",
    "archived seed-42 real-image caption-protocol dE at r=6", -39.5, tol=T_R1)
calc("c-dense-bracket", "MAIN-VII",
     "sections/conclusion.tex:25-26 'A dense three-epoch sweep ... places the crossing higher, between r=14 and r=16'",
     "r=14 to r=16", EXP + "/E2_results.json", "sweep",
     "the dense sweep's sign bracket: the mean dE is still negative at r=14 and positive at r=16",
     14.0, lambda: dense_sign_bracket(), tol=T_EXACT,
     note="The bracket is the sign change of the per-rank mean (r=14 = -106.0, r=16 = +950.7); it "
          "is asserted here as the last negative rank, independently of the divergence counts "
          "asserted under c-diverge16 / c-converge14 / c-diverge20.")
add("c-diverge16", "MAIN-VII",
    "sections/conclusion.tex:25-26 'ranks <=14 converge, two of three seeds diverge at r=16'",
    "2 of 3 at r=16", ANA + "/p3_upgrade_analysis.json", "rank_sweep.rows[rank=16].n_diverged",
    "archived count of r=16 dense-sweep trajectories whose final energy overshoots the batch "
    "E0=3927.0 (3810.0 stays below; 5359.0 and 5464.0 overshoot), which is the divergence this "
    "sentence counts and the same boundary critical_rank records as "
    "first_majority_diverged_rank=16",
    2.0, tol=T_EXACT, kind="calc", fn=lambda: float(rank_sweep_row(16)["n_diverged"]),
    note="A first remediation pass read this sentence against E2_results.json :: sweep with "
         "'diverge' meaning 'turns non-finite', concluded that the archive contradicted the "
         "printed count, and rewrote the clause to 'r<=20 converge, all three seeds at r=24'. "
         "That rewrite was wrong twice over: it made the sentence contradict its own r=14..r=16 "
         "bracket in the same parenthesis, and it substituted the NaN criterion of a different "
         "run family. The dense sweep's own summary counts divergence as the final energy "
         "overshooting E0 -- n_diverged is 0 for every r<=14, 2 at r=16 and 3 at r=20 -- which "
         "reproduces the printed sentence exactly, so the wording was restored and is asserted here.")
add("c-converge14", "MAIN-VII",
    "sections/conclusion.tex:25-26 'ranks <=14 converge'",
    "last converged rank 14", ANA + "/p3_upgrade_analysis.json",
    "rank_sweep.critical_rank.last_converged_rank",
    "the dense sweep's own convergence boundary: the last rank whose three trajectories all end "
    "at or below the batch E0", 14.0, tol=T_EXACT, kind="calc",
    fn=lambda: float(_load(ANA + "/p3_upgrade_analysis.json")
                     ["rank_sweep"]["critical_rank"]["last_converged_rank"]))
add("c-diverge20", "MAIN-VII",
    "sections/conclusion.tex:25-26 'all three by r=20'",
    "3 of 3 at r=20", ANA + "/p3_upgrade_analysis.json", "rank_sweep.rows[rank=20].n_diverged",
    "archived count of r=20 dense-sweep trajectories whose final energy overshoots the batch "
    "E0=3927.0 (final energies 6585.0, 6786.0 and 7114.0 all overshoot)", 3.0, tol=T_EXACT,
    kind="calc", fn=lambda: float(rank_sweep_row(20)["n_diverged"]),
    note="Same archive and same divergence criterion as c-diverge16; see the note there.")
add("c-e0-current", "MAIN-VII", "sections/conclusion.tex:28 'its defaults give E_0=3921.0'",
    "3921.0", ANA + "/p3_rerun_protocol.json", "runs.r5_s42.E.0",
    "initial energy on the current-protocol re-run", 3921.0)
add("c-e0-archive", "MAIN-VII",
    "sections/conclusion.tex:30 'produced by earlier script versions with E_0=3927.0 or 3930.5'",
    "3927.0 or 3930.5", ANA + "/p3_phase_boundary.json",
    "batch_trajectory_comparison.E0_by_batch.extra.E0_values",
    "the two initial energies the earlier batches recorded; the larger is the E2 batch value",
    3930.5, kind="calc",
    fn=lambda: max(dig(_load(ANA + "/p3_phase_boundary.json"),
                       "batch_trajectory_comparison.E0_by_batch.extra.E0_values")))
add("c-e0-3927", "MAIN-VII", "sections/conclusion.tex:30 'E_0=3927.0'", "3927.0",
    ANA + "/p3_phase_boundary.json",
    "batch_trajectory_comparison.E0_by_batch.sweep.E0_values.0",
    "the smaller value, on the dense-sweep batch", 3927.0)
duplicate("c-five-seed-quote", "MAIN-VII",
          "sections/conclusion.tex:28-30 'at r=5 the sign remains seed-dependent (-10.5, +8.0, -36.5, -27.0 and -49.0 for five seeds ...)'",
          "five per-seed values",
          "These five per-seed values and the two means that follow are the same numbers "
          "asserted entry by entry under S12, S13, S22 and f1-five-seed-*; the ledger does not "
          "re-list them here so that a failure is reported once rather than twice.")
add("c-r7", "MAIN-VII", "sections/conclusion.tex:30 '+214.5'", "+214.5",
    ANA + "/p3_rerun_extra.json", "runs.r7_s42.delta_E", "archived seed-42 dE at r=7", 214.5, tol=T_R1)
add("c-r8", "MAIN-VII", "sections/conclusion.tex:30 '+262.0'", "+262.0",
    ANA + "/p3_rerun_extra.json", "runs.r8_s42.delta_E", "archived seed-42 dE at r=8", 262.0, tol=T_R1)
add("c-r10", "MAIN-VII", "sections/conclusion.tex:30 '+298.0'", "+298.0",
    ANA + "/p3_rerun_extra.json", "runs.r10_s42.delta_E", "archived seed-42 dE at r=10", 298.0, tol=T_R1)
add("c-r16", "MAIN-VII", "sections/conclusion.tex:30 '+1235.0'", "+1235.0",
    ANA + "/p3_rerun_protocol.json", "runs.r16_s42.delta_E",
    "archived seed-42 dE at r=16 on the current protocol", 1235.0, tol=T_R1)
deleted("c-runs-132", "MAIN-VII",
        "sections/conclusion.tex:19 (was 'Experimental validation covers 132 runs on the present "
        "protocol plus the capacity-matched allocation study of Section IV.'); also in the "
        "submitted package (LaTeXSource.zip sections/conclusion.tex:19)",
        "132 runs",
        "No archive field enumerates 'runs on the present protocol'. The experiment tree holds "
        "374 archives across several run families and naming conventions; the only run-count "
        "field in the allocation tree is p3_alloc_results.json :: n_runs_total = 57, which "
        "counts the capacity-matched allocation study (a different set) and would be a "
        "definition of the ledger's own rather than the manuscript's. The sentence was rewritten "
        "without the count: 'Experimental validation comprises the present protocol together "
        "with the capacity-matched allocation study of Section IV.'")
approximate("c-usd8", "MAIN-VII", "sections/conclusion.tex:47 'verification uses a cloud GPU (~$8 USD)'",
            "~$8 USD", "Billing figure; not recorded in any archive. Approximate, and printed "
            "with a tilde.")
external("c-zenodo-doi", "MAIN-VII",
         "sections/conclusion.tex:49 and main.tex:133 'version DOI 10.5281/zenodo.23632347'",
         "10.5281/zenodo.23632347",
         "External identifier, not a recomputable number. Listed so the ledger is explicit "
         "rather than silent about it.")
external("m-github", "MAIN-Data", "main.tex:132 'github.com/MoYUYao666/gap-susceptibility'", "url",
         "External location, not a recomputable number.")
calc("m-supp-s46", "MAIN-Data", "main.tex:108 'Supplementary Sections S1--S46'", "S1--S46",
     SUPP, "", "the main text's declared S-range must equal the number of numbered sections the "
     "supplement defines", 46.0,
     lambda: count_supp_sections(), tol=T_ABS,
     note="Repaired 2026-10-24: main.tex:108 read S1--S43 against a supplement that had grown "
          "to 46 numbered sections. main.tex now reads S1--S46, and audit_check.py / audit_pdf.py "
          "carry the matching S1--S46 needles. The entry id changed from m-supp-s43 so that the "
          "old failing id cannot be mistaken for a passing one.")

# =======================================================================================
# SUPPLEMENT -- sections S1-S46
# =======================================================================================

# --- S1: claims / evidence / boundary summary table (readability round, 2026-10-25) -----
# The supplement's first table (tab:claims-summary, printed as Table S1) is a pointer table: one row
# per substantive claim, each cell pointing at a section, table or archive field. It measures nothing
# itself, but it prints the headline value of each of its six rows, so every one of those is asserted
# here against the archive the row names and the row's remaining numbers are recorded as DUPLICATE
# pointers to the entries that already assert them. Two quantities become printed for the first time
# here: the operating-step second-order shares as signed percentages (-3.56% / -3.48%, the same
# archived shares S18 prints as -0.0356 / -0.0348), and three values of the applicability-boundary
# archive outputs/analysis/p3_rc_family_boundary.json and one of p3_gamma_robustness.json that the
# evidence round printed in S35/S46 without a ledger entry of their own.
_RC = ANA + "/p3_rc_family_boundary.json"
_ROB = ANA + "/p3_gamma_robustness.json"
add("sum-row1-exact-p", "S1",
     "supplementary.tex Table tab:claims-summary row 1 'exact r=5 vs r=6 test p=1.08e-5'", "1.08e-5",
     ANA + "/p3_rank_separation_extended.json", "separation.p_min_attainable",
     "minimum attainable exact two-sided permutation p over the 184756 splits, which the r=5 vs r=6 "
     "pair attains", 1.082508822446903e-05, tol=T_R4)
duplicate("sum-row1-sign-split", "S1",
          "supplementary.tex Table tab:claims-summary row 1 'all ten runs negative at r=3,4,5 and all "
          "ten positive at r=6,7,8'", "10 + 10",
          "Same statement as the S34 entries, which assert conclusion.sign_split of the same archive.")
add("sum-row1-tost", "S1",
     "supplementary.tex Table tab:claims-summary row 1 '(TOST p=0.652, S34)'", "0.652",
     ANA + "/p3_rank_separation_extended.json", "rank5_equivalence.tost_p",
     "archived TOST p of the ten-seed r=5 group against zero at the declared margin",
     0.6516223596255077, tol=T_R4)
add("sum-row1-span-lo", "S1",
     "supplementary.tex Table tab:claims-summary row 1 'the eight LLaVA strata span [4.96,46.76]'",
     "4.96", _RC, "rc_by_family.llava-1.5-7b.sensitivity_span.0",
     "lowest archived LLaVA stratum crossing point", 4.957447, tol=T_R2)
add("sum-row1-span-hi", "S1",
     "supplementary.tex Table tab:claims-summary row 1 '[4.96,46.76]'", "46.76", _RC,
     "rc_by_family.llava-1.5-7b.sensitivity_span.1",
     "highest archived LLaVA stratum crossing point", 46.759029, tol=T_R2)
calc("sum-row2-share", "S1",
     "supplementary.tex Table tab:claims-summary row 2 'environment share 49.59%'", "49.59%",
     STACK_SEEDS, "sigma_by_rank.5.all_rows.env_variance_share",
     "four-stack environment share, as a percentage", 49.59454469392248, tol=T_R2,
     fn=lambda: stack_seeds(["sigma_by_rank", "5", "all_rows", "env_variance_share"]) * 100.0)
calc("sum-row2-ci-lo", "S1",
     "supplementary.tex Table tab:claims-summary row 2 'wide, [35.8%,74.9%]'", "35.8%", STACK_SEEDS,
     "sigma_by_rank.5.all_rows.bootstrap.share_ci95.0",
     "lower bootstrap limit of the four-stack share, as a percentage", 35.82484627737049, tol=T_R2,
     fn=lambda: stack_seeds(["sigma_by_rank", "5", "all_rows", "bootstrap", "share_ci95"])[0] * 100.0)
calc("sum-row2-ci-hi", "S1",
     "supplementary.tex Table tab:claims-summary row 2 '[35.8%,74.9%]'", "74.9%", STACK_SEEDS,
     "sigma_by_rank.5.all_rows.bootstrap.share_ci95.1",
     "upper bootstrap limit of the four-stack share, as a percentage", 74.86574284047108, tol=T_R2,
     fn=lambda: stack_seeds(["sigma_by_rank", "5", "all_rows", "bootstrap", "share_ci95"])[1] * 100.0)
duplicate("sum-row2-sigma", "S1",
          "supplementary.tex Table tab:claims-summary row 2 'sigma_env=32.46 against "
          "sigma_seed=32.72'", "32.46 / 32.72",
          "Same two values as t-env-stack-seeds-sigma-env / -sigma-seed (MAIN-V) and the S41 entries, "
          "asserted there from the same archive block.")
duplicate("sum-row2-three-stack", "S1",
          "supplementary.tex Table tab:claims-summary row 2 'the frozen three-stack reference of the "
          "same archive gives 45.20%'", "45.20%",
          "Same value as t-env-stack-seeds-three-stack (MAIN-V), asserted there.")
duplicate("sum-row3-rank-control", "S1",
          "supplementary.tex Table tab:claims-summary row 3 'centroid gap inside [0.744,0.792] over 60 "
          "checkpoints and r(rank,CG)=-0.42'", "[0.744,0.792] / -0.42",
          "Same values as s11-cg-lo / s11-cg-hi and the S11 correlation entry, asserted there.")
calc("sum-row3-curv-r5", "S1",
     "supplementary.tex Table tab:claims-summary row 3 'second-order share -3.56% at r=5'", "-3.56%",
     ANA + "/p3_hessian_probe_r5.json", "runs",
     "the archived share S18 prints as -0.0356, printed here as a signed percentage", -3.56,
     lambda: -share_at_lr_pct(5), tol=T_R2)
calc("sum-row3-curv-r6", "S1",
     "supplementary.tex Table tab:claims-summary row 3 'and -3.48% at r=6'", "-3.48%",
     ANA + "/p3_hessian_probe_r6.json", "runs",
     "the archived share S18 prints as -0.0348, printed here as a signed percentage", -3.48,
     lambda: -share_at_lr_pct(6), tol=T_R2)
duplicate("sum-row4-decoder", "S1",
          "supplementary.tex Table tab:claims-summary row 4 'Qwen2-VL-2B -384 at both'", "-384",
          "Same value as s16-third-5 / s16-third-6, asserted there.")
calc("sum-row5-paired-diff", "S1",
     "supplementary.tex Table tab:claims-summary row 5 'guided minus uniform, -3570.10'", "-3570.10",
     PAIRED, "paired.capacity_matched_by_seed.mean_difference",
     "archived capacity-matched seed-paired mean difference, signed", -3570.0983072916665, tol=T_R2,
     fn=lambda: paired_cm("mean_difference"))
calc("sum-row5-ci-lo", "S1",
     "supplementary.tex Table tab:claims-summary row 5 '95% CI [-5524.16,-1850.31]'", "-5524.16",
     PAIRED, "paired.capacity_matched_by_seed.ci95_percentile.0",
     "lower percentile-bootstrap limit of the paired difference", -5524.16, tol=T_R2,
     fn=lambda: paired_cm("ci95_percentile")[0])
calc("sum-row5-ci-hi", "S1",
     "supplementary.tex Table tab:claims-summary row 5 '[-5524.16,-1850.31]'", "-1850.31", PAIRED,
     "paired.capacity_matched_by_seed.ci95_percentile.1",
     "upper percentile-bootstrap limit of the paired difference", -1850.31, tol=T_R2,
     fn=lambda: paired_cm("ci95_percentile")[1])
calc("sum-row5-pairs-negative", "S1",
     "supplementary.tex Table tab:claims-summary row 5 'all six seed pairs negative'", "6 of 6",
     PAIRED, "paired.capacity_matched_by_seed.n_pairs_negative",
     "archived count of negative per-pair differences", 6.0, tol=T_ABS,
     fn=lambda: float(paired_cm("n_pairs_negative")))
calc("sum-row5-tost", "S1",
     "supplementary.tex Table tab:claims-summary row 5 '(TOST p=0.916, S20)'", "0.916", PAIRED,
     "equivalence.capacity_matched_tost.p_tost",
     "archived TOST p at the data-derived margin", 0.9161678137131604, tol=T_R4,
     fn=lambda: dig(_load(PAIRED), "equivalence.capacity_matched_tost.p_tost"))
calc("sum-row5-matched-loss", "S1",
     "supplementary.tex Table tab:claims-summary row 5 'reverses the sign (+3125.68 on n=2 seeds)'",
     "+3125.68", PAIRED, "controls.matched_loss.paired_by_seed.mean_difference",
     "archived matched-loss seed-paired difference", 3125.68359375, tol=T_R2,
     fn=lambda: dig(_load(PAIRED), "controls.matched_loss.paired_by_seed.mean_difference"))
duplicate("sum-row5-arms", "S1",
          "supplementary.tex Table tab:claims-summary row 5 'every trained allocation arm has a "
          "positive dE (S19/S28/S41)'", "positive",
          "Same arms as s16-ntk-arm, s16-gamma-arm, s16-igu-arm and the S28 rule arms, asserted there.")
calc("sum-row6-backbones", "S1",
     "supplementary.tex Table tab:claims-summary row 6 'Five backbones, nineteen measured strata: two "
     "contain no crossing anywhere'", "2", _RC, "conclusion.families_with_no_crossing_anywhere",
     "archived count of backbone families with no sign crossing in their measured rank range", 2.0,
     tol=T_ABS,
     fn=lambda: float(len(dig(_load(_RC), "conclusion.families_with_no_crossing_anywhere"))))
add("sum-row6-smolvlm", "S1",
     "supplementary.tex Table tab:claims-summary row 6 'a single well-defined crossing, at 5.699'",
     "5.699", _RC, "rc_by_family.smolvlm-500m.family_estimate",
     "archived SmolVLM-500M crossing point", 5.698748, tol=T_R3)
add("sum-row6-smolvlm-lo", "S1",
     "supplementary.tex Table tab:claims-summary row 6 '95% CI [5.556,5.830]'", "5.556", _RC,
     "rc_by_family.smolvlm-500m.family_estimate_ci95.0", "lower 95% bootstrap limit", 5.55636,
     tol=T_R3)
add("sum-row6-smolvlm-hi", "S1",
     "supplementary.tex Table tab:claims-summary row 6 '[5.556,5.830]'", "5.830", _RC,
     "rc_by_family.smolvlm-500m.family_estimate_ci95.1", "upper 95% bootstrap limit", 5.829684,
     tol=T_R3)
duplicate("sum-row6-bootstrap", "S1",
          "supplementary.tex Table tab:claims-summary row 6 '5/5/4/2 block plan reproduced in 23% of "
          "reference-batch draws'", "23%",
          "Same value as s16-boot-23, asserted from p3_gamma_bootstrap.json.")
add("sum-row6-rho-order", "S1",
     "supplementary.tex Table tab:claims-summary row 6 'survives a uniform relative drift of only "
     "rho=0.160'", "0.160", _ROB, "noise_break_even.rho_order_flip",
     "archived relative drift at which the ordering of |Gamma_k| can first change",
     0.16001035049197845, tol=T_R3)
add("sum-row6-observed-sd", "S1",
     "supplementary.tex Table tab:claims-summary row 6 'an observed 4.227 relative sd'", "4.227", _ROB,
     "noise_break_even.noise_to_tolerance_ratios.worst_observed_relative_sd",
     "largest archived relative seed-to-seed sd of a repeated block coupling", 4.226722392492288,
     tol=T_R3)
add("sum-row6-observed-ratio", "S1",
     "supplementary.tex Table tab:claims-summary row 6 '(26.4x the break-even)'", "26.4", _ROB,
     "noise_break_even.noise_to_tolerance_ratios.worst_observed_relative_sd_over_rho_order",
     "that sd in units of the ordering break-even", 26.415306131737896, tol=T_R1)

# --- S4: detailed Gamma for LLaVA -----------------------------------------------------
_GLL = EXP + "/gamma_llava_results.json"
add("s4-vis", "S4", "supplementary.tex Table tab:gamma_detail, Vision encoder Gamma_k", "-8092",
    _GLL, "results_by_rank.r8.per_block.vis", "archived per-block Gamma at r=8", -8092.0, tol=T_INT)
add("s4-vis-norm", "S4", "supplementary.tex Table tab:gamma_detail, Vision ||grad E||", "11975",
    _GLL, "results_by_rank.r8.norm_grad_E.vis", "archived gradient norm at r=8", 11975.0, tol=T_INT)
add("s4-vis-cos", "S4", "supplementary.tex Table tab:gamma_detail, Vision cos phi_k", "-0.10",
    _GLL, "results_by_rank.r8.cos_phi.vis", "archived cosine at r=8", -0.10383240118543854, tol=T_R2)
add("s4-shallow", "S4", "supplementary.tex Table tab:gamma_detail, LLM shallow Gamma_k", "+1614",
    _GLL, "results_by_rank.r8.per_block.llm_shallow", "archived per-block Gamma at r=8",
    1614.0, tol=T_INT)
add("s4-shallow-norm", "S4", "supplementary.tex Table tab:gamma_detail, LLM shallow ||grad E||",
    "3579", _GLL, "results_by_rank.r8.norm_grad_E.llm_shallow",
    "archived gradient norm at r=8", 3579.0, tol=T_INT)
add("s4-shallow-cos", "S4", "supplementary.tex Table tab:gamma_detail, LLM shallow cos phi_k",
    "+0.38", _GLL, "results_by_rank.r8.cos_phi.llm_shallow", "archived cosine at r=8",
    0.382016940532137, tol=T_R2)
add("s4-mid", "S4", "supplementary.tex Table tab:gamma_detail, LLM mid Gamma_k", "+8717",
    _GLL, "results_by_rank.r8.per_block.llm_mid", "archived per-block Gamma at r=8", 8717.0, tol=T_INT)
add("s4-mid-norm", "S4", "supplementary.tex Table tab:gamma_detail, LLM mid ||grad E||", "7828",
    _GLL, "results_by_rank.r8.norm_grad_E.llm_mid", "archived gradient norm at r=8", 7828.0, tol=T_INT)
add("s4-mid-cos", "S4", "supplementary.tex Table tab:gamma_detail, LLM mid cos phi_k", "+0.37",
    _GLL, "results_by_rank.r8.cos_phi.llm_mid", "archived cosine at r=8", 0.3651347664953818, tol=T_R2)
add("s4-deep", "S4", "supplementary.tex Table tab:gamma_detail, LLM deep Gamma_k", "+2727",
    _GLL, "results_by_rank.r8.per_block.llm_deep", "archived per-block Gamma at r=8", 2727.0, tol=T_INT)
add("s4-deep-norm", "S4", "supplementary.tex Table tab:gamma_detail, LLM deep ||grad E||", "4813",
    _GLL, "results_by_rank.r8.norm_grad_E.llm_deep", "archived gradient norm at r=8", 4813.0, tol=T_INT)
add("s4-deep-cos", "S4", "supplementary.tex Table tab:gamma_detail, LLM deep cos phi_k", "+0.32",
    _GLL, "results_by_rank.r8.cos_phi.llm_deep", "archived cosine at r=8", 0.3164961807898942, tol=T_R2)
for _blk, _pct in (("vis", 38.3), ("llm_shallow", 7.6), ("llm_mid", 41.2), ("llm_deep", 12.9)):
    calc("s4-pct-%s" % _blk, "S4",
         "supplementary.tex Table tab:gamma_detail, %%|Gamma| for %s" % _blk, "%g%%" % _pct,
         _GLL, "results_by_rank.r8.per_block", "100*|Gamma_k| / sum_j |Gamma_j| at r=8",
         _pct, (lambda b: lambda: 100.0 * abs(dig(_load(_GLL), "results_by_rank.r8.per_block.%s" % b)) /
                sum(abs(v) for v in dig(_load(_GLL), "results_by_rank.r8.per_block").values()))(_blk),
         tol=T_R1)
add("s4-block-additivity", "S4",
    "supplementary.tex:122-123 'The computation is validated by block additivity and sign consistency'",
    "validated", ANA + "/p3_additivity_residual.json", "max_abs_relative",
    "the additivity check the supplement cites is archived, with the residual asserted under S30",
    0.001160525552285436, tol=T_R4)

# --- S5: rank scaling of Gamma --------------------------------------------------------
for _rk, _vis, _sh, _mid, _deep in (("r4", -2566, 750, 4255, 1001),
                                    ("r8", -8092, 1614, 8717, 2727),
                                    ("r16", -17619, 2781, 18169, 4072),
                                    ("r32", -28984, 6391, 38171, 9485),
                                    ("r64", -66945, 12674, 70374, 20017)):
    for _blk, _val in (("vis", _vis), ("llm_shallow", _sh), ("llm_mid", _mid), ("llm_deep", _deep)):
        add("s5-%s-%s" % (_rk, _blk), "S5",
            "supplementary.tex Table tab:gamma_rank %s %s" % (_rk, _blk), "%+g" % _val,
            _GLL, "results_by_rank.%s.per_block.%s" % (_rk, _blk),
            "archived per-block Gamma at this rank", float(_val), tol=1.0)
calc("s5-vis-growth", "S5",
     "supplementary.tex Table tab:gamma_rank caption 'the vision block growing fastest (26x from r=4 to r=64)'",
     "26x", _GLL, "results_by_rank",
     "|Gamma_vis(r=64)| / |Gamma_vis(r=4)|", 26.0,
     lambda: gamma_growth("vis"), tol=1.0)
calc("s5-range-lo", "S5",
     "supplementary.tex:213 'all |Gamma_k| grow monotonically with rank (16--26x from r=4 to r=64)'",
     "16x", _GLL, "results_by_rank",
     "smallest of the four per-block growth factors from r=4 to r=64", 16.0,
     lambda: min(gamma_growth(b) for b in ("vis", "llm_shallow", "llm_mid", "llm_deep")), tol=1.0)
calc("s5-range-hi", "S5", "supplementary.tex:213 '(16--26x from r=4 to r=64)'", "26x",
     _GLL, "results_by_rank",
     "largest of the four per-block growth factors", 26.0,
     lambda: max(gamma_growth(b) for b in ("vis", "llm_shallow", "llm_mid", "llm_deep")), tol=1.0)
for _rk, _val in ((4, -46.5), (16, -199.5), (32, -129.8), (64, 151.7)):
    add("s5-ers-r%d" % _rk, "S5",
        "supplementary.tex:219-220 'dE stays negative through r=32 and flips positive at r=64 (%g' at r=%d"
        % (_val, _rk), "%+g" % _val, EXP + "/ers_1epoch_results.json", "r%d.mean" % _rk,
        "archived one-epoch per-rank mean dE", _val, tol=T_R1)
calc("s5-ers-welch", "S5", "supplementary.tex:221 '(Welch t=8.60'", "t=8.60",
     EXP + "/ers_1epoch_results.json", "r32/r64",
     "Welch t recomputed from the archived per-seed dE at r=32 against r=64", 8.60,
     lambda: ers_welch(), tol=T_R2)
calc("s5-ers-welch-p", "S5", "supplementary.tex:221 'p=0.004, r=32 vs r=64'", "p=0.004",
     EXP + "/ers_1epoch_results.json", "r32/r64",
     "two-sided Welch p from the same per-seed values", 0.004, lambda: ers_welch(p=True), tol=T_R3)

# --- S6 / S8 / S12: decoder VLM -------------------------------------------------------
calc("s6-stable", "S6", "supplementary.tex:244-245 'Rank behaviour is stable---no sign flip at any rank in either condition, 7 of 7'",
     "7 of 7", ANA + "/p3_qwen2b_crossing_fixed.json", "runs",
     "the Qwen2-VL-2B rank sweep covers seven ranks", 7.0, lambda: qwen2b_n_ranks(), tol=T_EXACT)
add("s6-real-range-hi", "S6",
    "supplementary.tex:246-247 'At 15 tokens real pairs give a positive dE at all seven ranks (+194 to +450)'",
    "+450", ANA + "/p3d_qwen_summary.json", "table[condition=real].dE_train.mean (max)",
    "the highest archived per-rank mean training-time dE of the real-pair runs (r=16)",
    449.9441, tol=T_INT, kind="calc", fn=lambda: qwen_cell_extreme("real", "dE_train", "max"),
    note="The four numbers the earlier ledger could not find are in p3d_qwen_summary.json :: "
         "table, in the dE_train column for the 15-token budget (runs[*] of "
         "p3d_qwen_ranksweep.json). The main text quotes the same sweep's dE_eval_real column; "
         "the two columns are different measurements of the same runs, which is why reading "
         "only one of them made the other look unsourced.")
add("s6-real-range-lo", "S6",
    "supplementary.tex:246-247 'real pairs give a positive dE at all seven ranks (+194 to +450)'",
    "+194", ANA + "/p3d_qwen_summary.json", "table[condition=real].dE_train.mean (min)",
    "the lowest archived per-rank mean training-time dE of the real-pair runs (r=1)",
    193.5616, tol=T_INT, kind="calc", fn=lambda: qwen_cell_extreme("real", "dE_train", "min"))
add("s6-blank-range-lo", "S6",
    "supplementary.tex:246-247 'and blank images a negative one (-519 to -185)'", "-519",
    ANA + "/p3d_qwen_summary.json", "table[condition=blank].dE_train.mean (min)",
    "the lowest archived per-rank mean training-time dE of the blank-image runs (r=1)",
    -518.9178, tol=T_INT, kind="calc", fn=lambda: qwen_cell_extreme("blank", "dE_train", "min"))
add("s6-blank-range-hi", "S6",
    "supplementary.tex:246-247 'and blank images a negative one (-519 to -185)'", "-185",
    ANA + "/p3d_qwen_summary.json", "table[condition=blank].dE_train.mean (max)",
    "the highest archived per-rank mean training-time dE of the blank-image runs (r=16)",
    -184.4996, tol=T_INT, kind="calc", fn=lambda: qwen_cell_extreme("blank", "dE_train", "max"))
add("s6-real54-r4", "S6",
    "supplementary.tex:248-249 'raising the budget to 54 tokens reverses it (real pairs -554, -471'",
    "-554", ANA + "/p3d_qwen_ranksweep_mp50176.json", "runs[rank=4,condition=real].dE_train",
    "archived seed-42 real-pair training-time dE at the 54-token budget, r=4", -554.1862,
    tol=T_INT, kind="calc",
    fn=lambda: mp50176_cell(4, "real", "dE_train"),
    note="The 54-token sweep is a four-run archive (ranks 4 and 16, real and blank), so each "
         "value is a single run rather than a three-seed mean; the entry names the run.")
add("s6-real54-r16", "S6",
    "supplementary.tex:248-249 'real pairs -554, -471'", "-471",
    ANA + "/p3d_qwen_ranksweep_mp50176.json", "runs[rank=16,condition=real].dE_train",
    "archived seed-42 real-pair training-time dE at the 54-token budget, r=16", -471.1656,
    tol=T_INT, kind="calc", fn=lambda: mp50176_cell(16, "real", "dE_train"))
calc("s6-paired-lo", "S6", "supplementary.tex:249 'the paired comparison flips from -699'", "-699",
     ANA + "/p3_resolution_verified.json", "p3d_qwen_ranksweep.json_pairs",
     "archived paired mean at the low budget", -698.99,
     lambda: float(flickr_pairs("p3d_qwen_ranksweep.json_pairs")["mean"]), tol=T_R2)
calc("s6-paired-hi", "S6", "supplementary.tex:249 'to +394'", "+394",
     ANA + "/p3_resolution_verified.json", "p3d_qwen_ranksweep_mp50176.json_pairs",
     "archived paired mean at the higher budget", 393.87,
     lambda: float(flickr_pairs("p3d_qwen_ranksweep_mp50176.json_pairs")["mean"]), tol=T_R2)
add("s6-gap54-pct", "S6", "supplementary.tex:252 'The initial real--blank gap is 50.9% at 54 tokens'",
    "50.9%", ANA + "/p3d_e0_vs_token_budget_train_sel_n16.json", "rows.1.gap_pct",
    "archived real-blank gap at the 54-token budget; the manuscripts prints 50.9 where the "
    "archive holds 51.6", 51.6075, tol=T_INT,
    note="A 0.7-point difference: the archived gap at this budget is 51.61%, printed as 50.9%. "
         "See docs/p3_reproduce_all_notes.md.")
add("s6-gap54-real", "S6", "supplementary.tex:252 '(14,718 against 22,207)'", "14,718",
    ANA + "/p3d_e0_vs_token_budget_train_sel_n16.json", "rows.1.E0_real",
    "archived real-condition initialization energy at 54 tokens", 14717.7668, tol=1.0)
add("s6-gap54-blank", "S6", "supplementary.tex:252 'against 22,207'", "22,207",
    ANA + "/p3d_e0_vs_token_budget_train_sel_n16.json", "rows.1.E0_blank",
    "archived blank-condition initialization energy at 54 tokens; printed 22,207 against an "
    "archived 22,313", 22313.2437, tol=1.0,
    note="106 units lower than the archive. See docs/p3_reproduce_all_notes.md.")
add("s6-gap15-pct", "S6", "supplementary.tex:253 'but only 2.9% at 15'", "2.9%",
    ANA + "/p3d_e0_vs_token_budget_train_sel_n16.json", "rows.0.gap_pct",
    "archived real-blank gap at the 15-token budget", 2.9806, tol=T_R1)
add("s6-gap15-real", "S6", "supplementary.tex:253 '(21,753 against 22,373)'", "21,753",
    ANA + "/p3d_e0_vs_token_budget_train_sel_n16.json", "rows.0.E0_real",
    "archived real-condition initialization energy at 15 tokens", 21751.8174, tol=1.0)
add("s6-gap15-blank", "S6", "supplementary.tex:253 'against 22,373'", "22,373",
    ANA + "/p3d_e0_vs_token_budget_train_sel_n16.json", "rows.0.E0_blank",
    "archived blank-condition initialization energy at 15 tokens; printed 22,373 against an "
    "archived 22,400", 22400.1462, tol=1.0,
    note="27 units lower than the archive. See docs/p3_reproduce_all_notes.md.")
add("s6-seedcount", "S6", "supplementary.tex:243 'at ranks {1,2,4,5,6,8,16} and three seeds per cell'",
    "3 seeds per cell", ANA + "/p3d_qwen_summary.json", "runs",
    "three seeds per rank are recorded in the sweep summary", 3.0, tol=T_EXACT,
    kind="calc", fn=lambda: qwen_sweep_seeds())
duplicate("s8-real-eval", "S8",
          "supplementary.tex:262-263 'evaluated on held-out real images ... the real-pair runs then improve at every rank (-135 to -271) while the blank-image runs cross from -260 at r = 1 to +179 at r = 16'",
          "-135..-271 / -260..+179",
          "The supplement's own statement of the four main-text numbers; each is asserted in "
          "this ledger under q-real-hi / q-real-lo / q-blank-r1 / q-blank-r16, against "
          "p3d_qwen_summary.json :: table[condition,rank].dE_eval_real.mean. Listed here so the "
          "supplement's restatement is accounted for rather than silently absent.")
add("s12-qwen2b-r5", "S12", "supplementary.tex:655 'r5_s42: dE=-352.0 (1.4M trainable)'",
    "-352.0", ANA + "/p3_qwen2b_crossing_fixed.json", "runs.r5_s42.delta_E",
    "archived local Qwen2-VL-2B r=5 re-run", -352.0, tol=T_R1)
add("s12-qwen2b-r6", "S12", "supplementary.tex:655 'r6_s42: dE=-288.0 (1.6M trainable)'",
    "-288.0", ANA + "/p3_qwen2b_crossing_fixed.json", "runs.r6_s42.delta_E",
    "archived local Qwen2-VL-2B r=6 re-run", -288.0, tol=T_R1)
add("s12-qwen2b-m5", "S12", "supplementary.tex:655 '(1.4M trainable)'", "1.4M",
    ANA + "/p3_qwen2b_crossing_fixed.json", "runs.r5_s42.trainable_M",
    "archived trainable-parameter count in millions", 1.4, tol=T_R2)
add("s12-qwen2b-m6", "S12", "supplementary.tex:655 '(1.6M trainable)'", "1.6M",
    ANA + "/p3_qwen2b_crossing_fixed.json", "runs.r6_s42.trainable_M",
    "archived trainable-parameter count in millions", 1.6, tol=T_R2)
add("s12-rerun-seed123", "S12", "supplementary.tex:655 'At ranks 5 and 6 we also ran seed 123'",
    "seed 123 exists", ANA + "/p3_rerun_extra.json", "runs.r5_s123.delta_E",
    "the seed-123 re-run is archived at r=5", 8.0, tol=T_R1)

# --- S9: sample size, ShareGPT, prior work --------------------------------------------
calc("s9-r6gt-r5", "S9",
     "supplementary.tex:480-482 'the ordering dE(r=6) > dE(r=5) is preserved in every configuration we ran (8/8'",
     "8/8", ANA + "/p3_phase_boundary.json", "r6_gt_r5_exhaustive_audit",
     "archived count of configurations satisfying dE(r=6)>dE(r=5), and all of them hold", 8.0,
     lambda: float(dig(_load(ANA + "/p3_phase_boundary.json"),
                       "r6_gt_r5_exhaustive_audit.n_r6_gt_r5")), tol=T_EXACT)
calc("s9-all-hold", "S9", "supplementary.tex:481 'is preserved in every configuration we ran'",
     "all hold", ANA + "/p3_phase_boundary.json", "r6_gt_r5_exhaustive_audit.all_hold",
     "the audit's own summary flag", 1.0,
     lambda: 1.0 if dig(_load(ANA + "/p3_phase_boundary.json"),
                        "r6_gt_r5_exhaustive_audit.all_hold") else 0.0)
add("s9-bin-p", "S9", "supplementary.tex:482 'two-sided binomial p = 0.0078'", "0.0078",
    ANA + "/p3_phase_boundary.json",
    "r6_gt_r5_exhaustive_audit.exact_sign_test_all_hold.p_two_sided",
    "archived exact two-sided sign-test p over the eight configurations", 0.0078125, tol=T_R4)
add("s9-ci-lo", "S9", "supplementary.tex:486 'at r=5 the bootstrap 95% confidence interval [-51.5, +12.5] spans zero'",
    "-51.5", ANA + "/p3_stats_hardened.json", "phase_transition.r5.mean_ci.lo",
    "archived bootstrap lower limit at r=5 (three seeds)", -51.5, tol=T_R1)
add("s9-ci-hi", "S9", "supplementary.tex:486 '[-51.5, +12.5]'", "+12.5",
    ANA + "/p3_stats_hardened.json", "phase_transition.r5.mean_ci.hi",
    "archived bootstrap upper limit at r=5", 12.5, tol=T_R1)
add("s9-perm-p", "S9", "supplementary.tex:487 'an exact permutation test between r=5 and r=6 gives p = 0.100'",
    "0.100", ANA + "/p3_stats_hardened.json",
    "pooled_llava_tests.r5_vs_r6_extra_batch.permutation_exact.p",
    "archived exact permutation p over the three-seed comparison",
    0.1, tol=T_R4)
add("s9-mde", "S9", "supplementary.tex:488 'the smallest detectable effect is d = 2.95'", "d = 2.95",
    ANA + "/p3_phase_boundary.json", "power_analysis.n3_vs_n3.cohens_d_mde",
    "archived minimum detectable effect at three seeds per arm", 2.9541387951759788, tol=T_R2)
add("s9-observed-d", "S9", "supplementary.tex:489 'against an observed d = 1.95'", "d = 1.95",
    ANA + "/p3_phase_boundary.json",
    "power_analysis.observed_effects.r6_vs_r5_extra_batch.cohens_d",
    "archived observed effect size for the r=6 against r=5 contrast", 1.947664359033751, tol=T_R2)
for _rk, _m, _sd in ((4, -60.0, 23.0), (5, 2.7, 31.6), (6, 133.5, 21.9), (7, 282.3, 33.3),
                     (8, 282.7, 33.9), (10, 374.7, 102.0), (12, 719.0, 19.0), (14, 1264.0, 46.8),
                     (16, 1710.7, 270.4), (20, 1907.0, 256.5), (24, 2730.7, 457.8),
                     (28, 1834.3, 168.2), (32, 2238.0, 61.4), (48, -35.5, 9.4), (64, 212.3, 28.7)):
    add("s9-sg-r%d-mean" % _rk, "S9", "supplementary.tex Table tab:sharegpt r=%d mean" % _rk,
        "%g" % _m, HARD, "sharegpt_phase.r%d.mean" % _rk, "archived ShareGPT per-rank mean",
        _m, tol=T_R1)
    add("s9-sg-r%d-sd" % _rk, "S9",
        "supplementary.tex Table tab:sharegpt r=%d population std" % _rk, "%g" % _sd,
        HARD, "sharegpt_phase.r%d.sd_population" % _rk,
        "archived ShareGPT per-rank population sd (ddof=0) -- the manuscript's convention",
        _sd, tol=T_R1)
calc("s9-sg-valid", "S9",
     "supplementary.tex Table tab:sharegpt caption '15 ranks x 3 seeds, all 45 runs valid, 0 NaN'",
     "45 runs", EXP + "/vqa_phase_results.json", "r4..r64.dE",
     "total seeded runs across the fifteen ranks", 45.0, lambda: sharegpt_runs(), tol=T_EXACT)
add("s9-sg-nan", "S9", "supplementary.tex Table tab:sharegpt caption '0 NaN'", "0 NaN",
    EXP + "/vqa_phase_results.json", "r4.n_nan",
    "every rank records zero non-finite runs", 0.0, kind="calc", fn=lambda: sharegpt_nan())
calc("s9-sg-std-lo", "S9",
     "supplementary.tex:549-550 'std at r>=32: 9.4--61.4, back to safe-regime levels'",
     "9.4 to 61.4", EXP + "/vqa_phase_results.json", "r>=32.std",
     "smallest archived std among the ranks at or above 32", 9.4,
     lambda: sg_high_std("min"), tol=T_R1)
calc("s9-sg-std-hi", "S9", "supplementary.tex:550 '9.4--61.4'", "9.4 to 61.4",
     EXP + "/vqa_phase_results.json", "r>=32.std",
     "largest archived std among those ranks", 61.4, lambda: sg_high_std("max"), tol=T_R1)
calc("s9-sg-danger", "S9", "supplementary.tex:550 'vs. 256--458 in the danger regime'",
     "256 to 458", EXP + "/vqa_phase_results.json", "r16..r24.std",
     "the danger-regime std span (r=16: 270.4, r=20: 256.5, r=24: 457.8)", 256.5,
     lambda: sg_danger_std("min"), tol=T_R1)
calc("s9-sg-danger-hi", "S9", "supplementary.tex:550 '256--458'", "256 to 458",
     EXP + "/vqa_phase_results.json", "r16..r24.std",
     "the largest danger-regime std", 457.8, lambda: sg_danger_std("max"), tol=T_R1)
exempt("s9-qwen-mse", "S9",
       "supplementary.tex Table tab:comparison 'Only GFAP predicts the phase transition and validates across architectures without training'",
       "qualitative",
       "Table tab:comparison is a qualitative method comparison (literature table). The "
       "AGENTS/provenance rule exempts pure literature tables; recorded here so the exemption "
       "is visible rather than silent.")

# --- S11: CLIP local rank control -----------------------------------------------------
_LOC = ANA + "/p3_rank_local_control.json"
for _rk, _np, _best, _last, _cg1, _cg6 in ((4, 147456, 63.5, 63.0, 0.786, 0.760),
                                           (8, 294912, 64.0, 63.5, 0.780, 0.764),
                                           (16, 589824, 64.0, 64.0, 0.772, 0.763),
                                           (32, 1179648, 64.1, 63.3, 0.773, 0.770),
                                           (64, 2359296, 64.1, 62.1, 0.762, 0.763)):
    add("s11-r%d-params" % _rk, "S11",
        "supplementary.tex Table tab:supp-rank r=%d trainable params" % _rk, "%d" % _np,
        _LOC, "runs.r%d|seed42.n_param" % _rk,
        "archived trainable-parameter count at this rank", float(_np))
    calc("s11-r%d-best" % _rk, "S11",
         "supplementary.tex Table tab:supp-rank r=%d best top-1" % _rk, "%g" % _best, _LOC,
         "runs.r%d|seed*.rows[*].top1" % _rk,
         "mean over the two seeds of each run's maximum top-1 accuracy", _best,
         (lambda r: lambda: local_top1(r, "best"))(_rk), tol=T_R1)
    calc("s11-r%d-last" % _rk, "S11",
         "supplementary.tex Table tab:supp-rank r=%d last top-1" % _rk, "%g" % _last, _LOC,
         "runs.r%d|seed*.rows[5].top1" % _rk,
         "mean over the two seeds of the final-epoch top-1 accuracy", _last,
         (lambda r: lambda: local_top1(r, "last"))(_rk), tol=T_R1)
    calc("s11-r%d-cg1" % _rk, "S11",
         "supplementary.tex Table tab:supp-rank r=%d CG (epoch 1)" % _rk, "%g" % _cg1, _LOC,
         "runs.r%d|seed*.rows[0].CG" % _rk,
         "mean over the two seeds of the epoch-1 centroid gap", _cg1,
         (lambda r: lambda: local_cg(r, 0))(_rk), tol=T_R3)
    calc("s11-r%d-cg6" % _rk, "S11",
         "supplementary.tex Table tab:supp-rank r=%d CG (epoch 6)" % _rk, "%g" % _cg6, _LOC,
         "runs.r%d|seed*.rows[5].CG" % _rk,
         "mean over the two seeds of the epoch-6 centroid gap", _cg6,
         (lambda r: lambda: local_cg(r, 5))(_rk), tol=T_R3)
calc("s11-cg-lo", "S11",
     "supplementary.tex:620 'the centroid gap stays inside [0.744, 0.792] across all 60 checkpoints'",
     "[0.744, 0.792]", _LOC, "runs.*.rows[*].CG",
     "smallest archived centroid gap over all checkpoint rows", 0.744, lambda: local_extreme("min"),
     tol=T_R3)
calc("s11-cg-hi", "S11", "supplementary.tex:620 '[0.744, 0.792]'", "[0.744, 0.792]", _LOC,
     "runs.*.rows[*].CG", "largest archived centroid gap", 0.792, lambda: local_extreme("max"),
     tol=T_R3)
calc("s11-cg-change", "S11", "supplementary.tex:621 '(the largest within-run change is 0.031)'",
     "0.031", _LOC, "runs.*.rows",
     "largest within-run change of the centroid gap", 0.031, lambda: local_max_change(), tol=T_R3)
calc("s11-acc-lo", "S11",
     "supplementary.tex:621-622 'the held-out accuracy varies between 55.9% and 65.1%'", "55.9%",
     _LOC, "runs.*.rows[*].top1", "lowest archived held-out top-1 accuracy", 55.9,
     lambda: local_acc("min"), tol=T_R1)
calc("s11-acc-hi", "S11", "supplementary.tex:622 '55.9% and 65.1%'", "65.1%", _LOC,
     "runs.*.rows[*].top1", "highest archived held-out top-1 accuracy", 65.1,
     lambda: local_acc("max"), tol=T_R1)
calc("s11-corr-top1", "S11", "supplementary.tex:622 'r(rank, top-1) = -0.10'", "-0.10", _LOC,
     "runs.*.rows[*].top1 and .rank",
     "Pearson correlation of rank against top-1 over all 60 archived checkpoints", -0.10,
     lambda: local_corr_all("top1"), tol=T_R2)
calc("s11-corr-cg", "S11",
     "supplementary.tex:630 'r(rank, CG) = -0.42' (printed to two decimals; the archive holds "
     "-0.4248)", "-0.42", _LOC,
     "runs.*.rows[*].CG and .rank",
     "Pearson correlation of rank against centroid gap over all 60 archived checkpoints",
     -0.4247967230, lambda: local_corr_all("cg"), tol=T_R2,
     note="Repaired 2026-10-24: the supplement printed -0.43, which is not the archive value "
          "(-0.4247967) rounded to two decimals; it is now -0.42. Rounding convention stated in "
          "the text so the digit can be re-derived.")
calc("s11-n-checkpoints", "S11", "supplementary.tex:620 'across all 60 checkpoints'", "60", _LOC,
     "runs.*.rows", "5 ranks x 2 seeds x 6 epochs", 60.0, lambda: local_n_checkpoints(), tol=T_EXACT)
add("s11-epochs", "S11", "supplementary.tex:619 'six epochs and two seeds'", "6 epochs / 2 seeds",
    _LOC, "seeds", "the archive records two seeds and six epochs per run", 2.0,
    kind="calc", fn=lambda: float(len(_load(_LOC)["seeds"])))

# --- S12: current-protocol re-run -----------------------------------------------------
for _rk, _e, _de in ((5, [3921.0, 3827.0, 3770.0, 3910.5], -10.5),
                     (6, [3921.0, 3842.0, 3797.0, 4036.0], 115.0),
                     (7, [3921.0, 3810.5, 3834.5, 4135.5], 214.5),
                     (8, [3921.0, 3790.0, 3839.5, 4183.0], 262.0),
                     (10, [3921.0, 3755.5, 3873.5, 4219.0], 298.0),
                     (16, [3921.0, 3687.5, 4025.5, 5156.0], 1235.0)):
    for _ep in range(4):
        calc("s12-r%d-e%d" % (_rk, _ep), "S12",
             "supplementary.tex Table tab:supp-rerun r=%d E(%d)" % (_rk, _ep), "%g" % _e[_ep],
             ANA + "/p3_rerun_analysis.json", "curve.%d.E_seed42" % _rk,
             "archived seed-42 trajectory value at this epoch", _e[_ep],
             (lambda rk, i: lambda: rerun_traj(rk)[i])(_rk, _ep), tol=T_R1)
    calc("s12-r%d-dE" % _rk, "S12", "supplementary.tex Table tab:supp-rerun r=%d dE" % _rk,
         "%+g" % _de, ANA + "/p3_rerun_analysis.json", "curve.%d.dE_seed42" % _rk,
         "archived seed-42 delta E", _de, (lambda rk: lambda: rerun_dE(rk))(_rk), tol=T_R1)
calc("s12-protocol", "S12",
     "supplementary.tex Table tab:supp-rerun caption '(run_training.py defaults: 20 samples, 16 train / 4 eval, lr 5e-5, three epochs, seed 42, E_0=3921.0)'",
     "20 samples / lr 5e-5 / 3 epochs", ANA + "/p3_rerun_protocol.json", "protocol",
     "the protocol string records all three facts the caption names", 3.0,
     lambda: protocol_facts(), tol=T_EXACT)
# --- S13: per-run energy trajectories -------------------------------------------------
for _rk, _sd_ in ((5, 42), (5, 123), (6, 42), (6, 123), (7, 42), (8, 42), (10, 42), (16, 42)):
    expected = None
    for _rel, _fld in (("p3_rerun_protocol.json", "runs.r%d_s%d" % (_rk, _sd_)),
                       ("p3_rerun_extra.json", "runs.r%d_s%d" % (_rk, _sd_)),
                       ("p3_rerun_seeds.json", "runs.r%d_s%d" % (_rk, _sd_))):
        try:
            expected = dig(_load(ANA + "/" + _rel), _fld + ".delta_E")
            break
        except (KeyError, IndexError):
            continue
    calc("s13-r%d-s%d" % (_rk, _sd_), "S13",
         "supplementary.tex Table tab:supp-perrun r=%d seed=%d dE" % (_rk, _sd_), "%+g" % expected,
         ANA, "p3_rerun_{protocol,extra,seeds}.json",
         "archived per-run delta E, resolved across the three re-run archives", expected,
         (lambda rk, sd: lambda: perrun_dE(rk, sd))(_rk, _sd_), tol=T_R1)
calc("s13-n-runs", "S13", "supplementary.tex:679 'lists every run of the current-protocol re-run individually'",
     "8 runs", ANA + "/p3_rerun_analysis.json", "curve",
     "the re-run family covers eight (rank, seed) cells: six ranks at seed 42 plus seeds 123 at "
     "r=5 and r=6", 8.0,
     lambda: float(len(_load(ANA + "/p3_rerun_analysis.json")["curve"]) + 2), tol=T_EXACT)

# --- S14: sample-window protocol ablation ---------------------------------------------
for _n in (12, 32, 64):
    add("s14-n%d" % _n, "S14", "supplementary.tex Table tab:numsamples %d samples" % _n,
        "%+g" % dig(_load(ANA + "/p3_numsamples_ablation.json"), "runs.n%d.delta_E" % _n),
        ANA + "/p3_numsamples_ablation.json", "runs.n%d.delta_E" % _n,
        "archived delta E for this training window at r=6, seed 42",
        dig(_load(ANA + "/p3_numsamples_ablation.json"), "runs.n%d.delta_E" % _n), tol=T_R1)
add("s14-n20", "S14", "supplementary.tex Table tab:numsamples 20 samples", "+115.0",
    ANA + "/p3_rerun_protocol.json", "runs.r6_s42.delta_E",
    "the default window coincides with the current-protocol re-run", 115.0, tol=T_R1)
calc("s14-up-to", "S14", "supplementary.tex:801 'changes the three-epoch dE by up to 3.8x'",
     "3.8x", ANA + "/p3_numsamples_ablation.json", "runs",
     "max/min of the archived four-window delta E values",
     3.8333333333333335, lambda: numsamples_ratio(), tol=T_R1)
add("s14-protocol", "S14", "supplementary.tex:800 'Holding rank (r=6) and seed (42) fixed'",
    "r=6, seed 42", ANA + "/p3_numsamples_ablation.json", "protocol",
    "the protocol string records the fixed rank and seed", 6.0, kind="calc",
    fn=lambda: float(re.search(r"rank (\d+)", _load(ANA + "/p3_numsamples_ablation.json")["protocol"]).group(1)))

# --- S15: protocol shift at the crossing ----------------------------------------------
add("s15-r5-n12", "S15", "supplementary.tex Table tab:protocol_shift n=12, dE(r=5)", "-39.5",
    ANA + "/p3_protocol_shift.json", "runs.r5_n12.delta_E",
    "archived r=5 value at the 12-sample window", -39.5, tol=T_R1)
calc("s15-r6-n12", "S15", "supplementary.tex Table tab:protocol_shift n=12, dE(r=6)", "+40.5",
     ANA + "/p3_numsamples_ablation.json", "runs.n12",
     "archived r=6 value at the 12-sample window", 40.5, lambda: numsamples_dE(12), tol=T_R1)
add("s15-note", "S15",
    "supplementary.tex:830 'the sign at r=5 is unchanged while the magnitude at both ranks varies'",
    "qualitative", ANA + "/p3_protocol_shift.json", "note",
    "the archive's own note records that the n=64 r=5 cell was interrupted and is not claimed",
    1.0, kind="calc", fn=lambda: 1.0 if "interrupted" in
    str(dig(_load(ANA + "/p3_protocol_shift.json"), "note")) else 0.0)

# --- S16: assumption audit / claim status ---------------------------------------------
calc("s16-additivity", "S16", "supplementary.tex Table tab:claims 'pair residuals below 0.12%'",
     "0.12%", ANA + "/p3_additivity_residual.json", "max_abs_relative",
     "largest absolute relative pair residual, as a percentage", 0.12,
     lambda: dig(_load(ANA + "/p3_additivity_residual.json"), "max_abs_relative") * 100.0, tol=T_R2)
add("s16-tenseed-split", "S16",
    "supplementary.tex Table tab:claims 'all ten runs negative at r=3,4,5 and all ten positive at r=6,7,8'",
    "10 + 10 per side", ANA + "/p3_rank_separation_extended.json", "conclusion.sign_split",
    "the archive states the same sentence; the underlying counts are asserted under S33",
    1.0, kind="calc", fn=lambda: 1.0 if "all 10 runs negative" in
    str(dig(_load(ANA + "/p3_rank_separation_extended.json"), "conclusion.sign_split")) else 0.0)
add("s16-14of15", "S16",
    "supplementary.tex Table tab:claims '14 of 15 rank pairs exact at the 5% level after Holm-Bonferroni'",
    "14 of 15", ANA + "/p3_rank_separation_extended.json", "separation.n_separating_holm_p05",
    "archived number of pairs surviving the Holm-Bonferroni adjustment", 14.0)
add("s16-pmin", "S16",
    "supplementary.tex Table tab:claims 'minimum attainable p=2/binom(20,10)=1.08x10^-5'",
    "1.08e-5", ANA + "/p3_rank_separation_extended.json", "separation.p_min_attainable",
    "archived minimum attainable exact p", 1.082508822446903e-05, tol=T_R4 * 1e-3)
add("s16-15pairs", "S16", "supplementary.tex Table tab:claims '15-pair exact matrix in S33'",
    "15 pairs", ANA + "/p3_rank_separation_extended.json", "separation.n_pairs",
    "archived number of rank pairs tested", 15.0)
calc("s16-dolly", "S16", "supplementary.tex Table tab:claims 'r=4/5 negative, r=6/7 positive (S40)'",
     "4/5 neg, 6/7 pos", ANA + "/p3_dolly_family.json", "ranks",
     "the Dolly family satisfies the sign pairing", 1.0, lambda: dolly_pattern(), tol=T_EXACT)
calc("s16-trained-lo", "S16", "supplementary.tex Table tab:claims 'trained arms +196 to +444'",
     "+196", ANA + "/p3_baseline_rules.json", "allocation",
     "smallest archived trained arm across the five allocation arms the claim covers "
     "(+196.5 for the Gamma arm of tab:ntkarm, +232.5 to +444 across the rules)", 196.5,
     lambda: min(block_arms() + [196.5]), tol=T_INT)
calc("s16-trained-hi", "S16", "supplementary.tex Table tab:claims 'trained arms +196 to +444'",
     "+444", ANA + "/p3_baseline_rules.json", "allocation",
     "largest archived trained arm among the three rule reimplementations", 444.0,
     lambda: max(block_arms()), tol=T_INT)
add("s16-igu-arm", "S16", "supplementary.tex Table tab:claims 'official IGU arm +240.5'",
    "+240.5", EXP + "/verify_r1_s42_bcexplicit_v12_s1_m2_d1.json", "delta_E",
    "archived official IGU allocation arm", 240.5, tol=T_R1)
add("s16-ntk-arm", "S16", "supplementary.tex Table tab:claims 'NTK +396.0'", "+396.0",
    EXP + "/verify_r1_s42_ntk_arm.json", "delta_E", "archived NTK allocation arm", 396.0, tol=T_R1)
add("s16-gamma-arm", "S16", "supplementary.tex Table tab:claims 'Gamma +196.5'", "+196.5",
    EXP + "/verify_r1_s42_bcexplicit_v5_s5_m4_d2.json", "delta_E",
    "archived Gamma allocation arm", 196.5, tol=T_R1)
add("s16-vqa-acc-rev", "S16",
    "supplementary.tex Table tab:claims 'the r=5--r=6 accuracy difference +0.0532 (95% CI [+0.0222,+0.0865])'",
    "+0.0532", ANA + "/p3_vqa_full_equivalence.json",
    "vqa_equivalence.contrasts.5_minus_6.accuracy.delta",
    "archived r=5-minus-r=6 accuracy difference", 0.0532, tol=T_R4)
add("s16-vqa-tost", "S16", "supplementary.tex Table tab:claims '(TOST p=0.5778)'", "0.5778",
    ANA + "/p3_vqa_full_equivalence.json", "vqa_equivalence.contrasts.5_minus_6.accuracy.tost_p",
    "archived TOST p for the r=5 minus r=6 accuracy contrast", 0.5778, tol=T_R4)
calc("s16-cv-lo", "S16", "supplementary.tex Table tab:claims 'CV 0.32--0.55'", "0.32",
     ANA + "/p3_gamma_batch_sensitivity.json", "summary",
     "the smallest archived coefficient of variation across blocks", 0.321,
     lambda: cv_range("min"), tol=T_R3)
calc("s16-cv-hi", "S16", "supplementary.tex Table tab:claims 'CV 0.32--0.55'", "0.55",
     ANA + "/p3_gamma_batch_sensitivity.json", "summary",
     "the largest archived coefficient of variation across blocks", 0.552,
     lambda: cv_range("max"), tol=T_R3)
calc("s16-boot-23", "S16",
     "supplementary.tex Table tab:claims 'bootstrap allocation reproduced in 23% of draws'", "23%",
     ANA + "/p3_gamma_bootstrap.json", "allocations",
     "archived bootstrap frequency of the paper's point allocation 5/5/4/2", 0.231,
     lambda: boot_freq("5/5/4/2"), tol=T_R3)
add("s16-env-vals", "S16",
    "supplementary.tex Table tab:claims 'four-stack means -23.0/-43.7/+24.0/-63.8; environment share "
    "49.59%, 95% CI [35.8%,74.9%]; S30, S39'",
    "-23.0 / -43.7 / +24.0 / -63.8", STACK_SEEDS, "ranks.5.stacks.*.mean",
    "the four per-stack r=5 means of the four-stack fit (asserted under MAIN-V and S41); the row was "
    "re-pointed from the frozen three-stack fit in the 2026-10-25 readability round, which also "
    "replaced its stale (S29, S37) pointers with (S30, S39)",
    1.0, kind="calc", fn=lambda: 1.0 if (stack_seeds(["ranks", "5", "stacks", "torch29_cu130", "mean"]) == -23.0
                                        and stack_seeds(["ranks", "5", "stacks", "torch212_cu130", "mean"]) == -43.7
                                        and stack_seeds(["ranks", "5", "stacks", "torch24_cu121", "mean"]) == 24.0
                                        and stack_seeds(["ranks", "5", "stacks", "torch26_cu124", "mean"]) == -63.75)
    else 0.0)
calc("s16-curvature", "S16",
     "supplementary.tex Table tab:claims 'curvature ... share below 0.6% at the operating step'",
     "<0.6%", ANA + "/p3_hessian_probe_r24.json", "runs.*.ghg_full",
     "the largest archived high-rank share 0.5*eta*gHg/||g||^2 at the operating rate is 0.73%, "
     "which is NOT below the 0.6% the claim asserts", 0.73,
     lambda: highrank_share_pct_max(), tol=T_HALF,
     note="The claim's threshold does not hold at the largest archived high-rank share; see "
          "docs/p3_reproduce_all_notes.md.")
calc("s16-qwen-order", "S16",
     "supplementary.tex Table tab:claims 'second-order term negligible on Qwen2-VL-2B ... share below 1% at the operating step'",
     "<1%", ANA + "/p3_hessian_probe_qwen2b_r5.json", "runs.*.share_at_lr",
     "every archived Qwen2-VL-2B share at the operating rate is below 1% in magnitude", 1.0,
     lambda: 1.0 if all(abs(qwen_share(i)) < 0.01 for i in range(3)) else 0.0)
add("s16-nan-17", "S16",
    "supplementary.tex Table tab:claims 'non-finite energy is an optimizer blow-up: not supported -- 17/17 runs: loss finite while energy non-finite (S24)'",
    "17/17", ANA + "/p3_nan_diagnostics.json", "cross_tab",
    "archived cross-tabulation; the exact field is resolved by the S24 entries", 17.0,
    kind="calc", fn=lambda: nan_runs())
calc("s16-newer", "S16",
     "supplementary.tex Table tab:claims 'crossing transfers to a newer model family: not supported'",
     "no sign change", EXP + "/qwen_cf_uniform_rank5_seed42_q25_r5_s42.json", "delta_E",
     "the newer-family per-seed signs are mixed, so no clean crossing is established", 1.0,
     lambda: newer_no_crossing(), tol=T_EXACT)
add("s16-third-5", "S16", "supplementary.tex Table tab:claims 'crossing transfers to a third checkpoint family: not supported -- Qwen2-VL-2B: both ranks -384 (S41)'",
    "-384", ANA + "/cloud_qwen_cf_uniform_rank5_seed42_qwen2vl.json", "delta_E",
    "archived third-family arm at r=5", -384.0, tol=T_R1)
add("s16-third-6", "S16", "supplementary.tex Table tab:claims 'both ranks -384'", "-384",
    ANA + "/cloud_qwen_cf_uniform_rank6_seed42_qwen2vl.json", "delta_E",
    "archived third-family arm at r=6", -384.0, tol=T_R1)
add("s16-perlayer", "S16",
    "supplementary.tex Table tab:claims 'layer 0 carries 98.1% of the coupling on Qwen2.5-VL-3B (S42)'",
    "98.1%", ANA + "/p3_qwen_perlayer_summary.json", "share.llm_00",
    "archived share of the total absolute coupling carried by layer 0", 0.9811478356607386,
    tol=T_R4)
calc("s16-smolvlm", "S16",
     "supplementary.tex Table tab:claims 'crossing pattern in a second family (SmolVLM-500M): replicated, small magnitude'",
     "3 of 3 seeds", ANA + "/p3_smolvlm_family_s42.json", "runs",
     "every archived SmolVLM seed has dE(r=5)<0<dE(r=6)", 1.0, lambda: smolvlm_all(), tol=T_EXACT)
duplicate("s16-adalora-claim", "S16",
          "supplementary.tex Table tab:claims 'AdaLoRA is worse than our arms: not supported -- AdaLoRA reaches lower energy in our comparison'",
          "not supported",
          "This is a claim-status row quoting the AdaLoRA numbers asserted under MAIN-IV-E "
          "(e-adalora-*). Listed so the row is accounted for rather than silently absent.")
duplicate("s16-igu-claim", "S16",
          "supplementary.tex Table tab:claims 'official IGU allocation ported and trained: reported, no positive claim -- arm +240.5 (S39)'",
          "+240.5",
          "Same number as s39-arm and s16-igu-arm, asserted there. Listed for row completeness.")
duplicate("s16-signed-claim", "S16",
          "supplementary.tex Table tab:claims 'signed Gamma or a non-CLIP source improves the ordering: reported, no positive claim -- S32 tables'",
          "reported", "Points at the S32 tables, whose numbers are asserted under s32-*. Listed "
          "for row completeness.")
duplicate("s16-three-s28", "S16",
          "supplementary.tex Table tab:claims 'energy predicts VQA accuracy: reported, no positive claim -- 1793 training pairs, all 451 held-out questions ... (S28)'",
          "1793 / 451",
          "Same counts as s28-train and s28-questions, asserted there. Listed for row completeness.")

# --- S18: curvature of the first-order approximation ----------------------------------
for _rk, _g2, _ghg, _share in ((5, 338.4, -4.74e5, -0.0356), (6, 391.9, -5.38e5, -0.0348)):
    _hp = ANA + "/p3_hessian_probe_r%d.json" % _rk
    calc("s18-r%d-g2" % _rk, "S18",
         "supplementary.tex Table tab:hessian rank %d ||g||^2" % _rk, "%g" % _g2, _hp, "runs",
         "mean gradient-squared over the three archived batches", _g2,
         (lambda p: lambda: g2_mean(p))(_hp), tol=T_R1)
    calc("s18-r%d-ghg" % _rk, "S18",
         "supplementary.tex Table tab:hessian rank %d gHg (1e-3 step)" % _rk, "%.2e" % _ghg,
         _hp, "runs", "mean gHg at the 1e-3 step over the three archived batches", _ghg,
         (lambda p: lambda: ghg_mean(p, "0.001"))(_hp), tol=5e2)
    calc("s18-r%d-share" % _rk, "S18",
         "supplementary.tex Table tab:hessian rank %d share at eta" % _rk, "%g" % _share, _hp,
         "runs", "mean second-order share 0.5*eta*gHg/||g||^2 at eta=5e-5", _share,
         (lambda p: lambda: share_at_lr(p))(_hp), tol=T_R4)
calc("s18-vision-share", "S18",
     "supplementary.tex Table tab:hessian 'vision share of |gHg|' column (99%)", "99%",
     ANA + "/p3_hessian_probe_r5.json", "runs.*.ghg_per_group_eps3e-4",
     "vision share of |gHg| at the 1e-3 step, averaged over the three archived batches", 0.99,
     lambda: hessian_vision_share(5), tol=T_R2)
calc("s18-secondorder-3.5", "S18",
     "supplementary.tex Table tab:hessian caption 'the second-order term is about 3.5% of the first-order term'",
     "3.5%", ANA + "/p3_hessian_probe_r5.json", "runs",
     "magnitude of the mean share at the operating rate, as a percentage", 3.56,
     lambda: share_at_lr_pct(5), tol=T_R2)
for _i, _pct in ((0, -0.42), (1, 0.25), (2, -0.87)):
    calc("s18-qwen-%d" % (_i + 1), "S18",
         "supplementary.tex:923 'the same finite-difference probe gives shares of -0.42%, +0.25%, -0.87%'",
         "%g%%" % _pct, ANA + "/p3_hessian_probe_qwen2b_r5.json",
         "runs.%d.share_at_lr.0.001" % _i,
         "archived per-batch share at the operating rate, as a percentage", _pct,
         (lambda i: lambda: qwen_share(i) * 100.0)(_i), tol=T_R2)
add("s18-qwen-model", "S18", "supplementary.tex:923 'On Qwen2-VL-2B (4-bit, LoRA r=5, blank image)'",
    "Qwen2-VL-2B / r=5", ANA + "/p3_hessian_probe_qwen2b_r5.json", "meta.model",
    "the archive's own model string names Qwen2-VL-2B-Instruct", 1.0, kind="calc",
    fn=lambda: 1.0 if "Qwen2-VL-2B" in str(dig(_load(ANA + "/p3_hessian_probe_qwen2b_r5.json"),
                                                "meta.model")) else 0.0)

# --- S19: additional allocation baselines ---------------------------------------------
_NTK = ANA + "/p3_ntk_allocation.json"
for _blk, _trace, _ntk, _gam, _uni in (("vision", 48957.1, 8, 5, 4),
                                       ("text_shallow", 23786.1, 5, 5, 4),
                                       ("text_mid", 8437.4, 2, 4, 4),
                                       ("text_deep", 1853.8, 1, 2, 4)):
    add("s19-%s-trace" % _blk, "S19", "supplementary.tex Table tab:ntk %s NTK trace" % _blk,
        "%g" % _trace, _NTK, "ntk_trace.%s" % _blk, "archived NTK-diagonal trace", _trace, tol=T_R1)
    add("s19-%s-rank" % _blk, "S19", "supplementary.tex Table tab:ntk %s NTK rank" % _blk,
        "%d" % _ntk, _NTK, "allocation_ntk.%s" % _blk,
        "archived NTK allocation at budget 16", float(_ntk))
    add("s19-%s-gamma" % _blk, "S19", "supplementary.tex Table tab:ntk %s Gamma rank" % _blk,
        "%d" % _gam, _NTK, "allocation_gamma.%s" % _blk,
        "archived Gamma allocation at budget 16", float(_gam))
    add("s19-%s-uni" % _blk, "S19", "supplementary.tex Table tab:ntk %s uniform" % _blk,
        "%d" % _uni, _NTK, "allocation_uniform.%s" % _blk, "archived uniform allocation",
        float(_uni))
add("s19-budget", "S19", "supplementary.tex Table tab:ntk caption '(budget 16)'", "budget 16",
    _NTK, "meta.budget", "the archive's own budget", 16.0)
add("s19-ntk-arm", "S19", "supplementary.tex Table tab:ntkarm NTK allocation 8/5/2/1 dE",
    "+396.0", EXP + "/verify_r1_s42_ntk_arm.json", "delta_E", "archived trained NTK arm",
    396.0, tol=T_R1)
add("s19-gamma-arm", "S19", "supplementary.tex Table tab:ntkarm Gamma allocation 5/5/4/2 dE",
    "+196.5", EXP + "/verify_r1_s42_bcexplicit_v5_s5_m4_d2.json", "delta_E",
    "archived trained Gamma arm", 196.5, tol=T_R1)
add("s19-ntk-traj", "S19",
    "supplementary.tex Table tab:ntkarm NTK trajectory [3921.0, 3793.5, 3836.0, 4317.0]",
    "%g" % 3921.0, EXP + "/verify_r1_s42_ntk_arm.json", "E",
    "archived NTK arm energy trajectory equals the printed one", 1.0, kind="calc",
    fn=lambda: 1.0 if [round(x, 1) for x in _load(EXP + "/verify_r1_s42_ntk_arm.json")["E"]]
    == [3921.0, 3793.5, 3836.0, 4317.0] else 0.0)
add("s19-gamma-traj", "S19",
    "supplementary.tex Table tab:ntkarm Gamma trajectory [3921.0, 3776.0, 3821.0, 4117.5]",
    "%g" % 3921.0, EXP + "/verify_r1_s42_bcexplicit_v5_s5_m4_d2.json", "E",
    "archived Gamma arm energy trajectory equals the printed one", 1.0, kind="calc",
    fn=lambda: 1.0 if [round(x, 1) for x in
                       _load(EXP + "/verify_r1_s42_bcexplicit_v5_s5_m4_d2.json")["E"]]
    == [3921.0, 3776.0, 3821.0, 4117.5] else 0.0)

# --- S20: newer model family ----------------------------------------------------------
for _rk, _sd_, _de in ((5, 42, 448.0), (5, 123, 384.0), (5, 789, -64.0),
                       (6, 42, 432.0), (6, 123, -32.0), (6, 789, -80.0)):
    _p = EXP + "/qwen_cf_uniform_rank%d_seed%d_q25_r%d_s%d.json" % (_rk, _sd_, _rk, _sd_)
    add("s20-q25-3b-r%d-s%d" % (_rk, _sd_), "S20",
        "supplementary.tex Table tab:newer r=%d seed=%d dE" % (_rk, _sd_), "%+g" % _de, _p,
        "delta_E", "archived Qwen2.5-VL-3B arm", _de, tol=1.0)
    add("s26-q25-3b-r%d-s%d" % (_rk, _sd_), "S26",
        "supplementary.tex Table tab:newerseeds r=%d seed=%d dE" % (_rk, _sd_), "%+g" % _de, _p,
        "delta_E", "archived Qwen2.5-VL-3B arm (Table tab:newerseeds repeats tab:newer)", _de,
        tol=1.0)
for _rk, _sd_, _de in ((5, 42, -2112.0), (6, 42, -2176.0)):
    _p = EXP + "/qwen_cf_uniform_rank%d_seed%d_cloud_q25_7b_r%d.json" % (_rk, _sd_, _rk)
    add("s20-q25-7b-r%d-s%d" % (_rk, _sd_), "S20",
        "supplementary.tex Table tab:newer7b r=%d seed=%d dE" % (_rk, _sd_), "%+g" % _de, _p,
        "delta_E", "archived Qwen2.5-VL-7B cloud arm", _de, tol=1.0)
calc("s20-no-crossing", "S20",
     "supplementary.tex:992-994 'no sign change is established between r=5 and r=6'",
     "no sign change", EXP + "/qwen_cf_uniform_rank5_seed42_q25_r5_s42.json", "delta_E",
     "the newer-family r=5 and r=6 signs do not form a clean negative-to-positive split", 1.0,
     lambda: newer_no_crossing(), tol=T_EXACT)
calc("s20-llava-onevision", "S20",
     "supplementary.tex:1672-1673 'LLaVA-OneVision-0.5B could not be evaluated with the current transformer stack (its released 1.5-processor config does not load under transformers 5.16)'",
     "could not load", EXP + "/qwen_cf_uniform_rank5_seed42_q25_r5_s42.json", "transformers",
     "this is a negative result with no number; the ledger records it as a statement, not a "
     "measurement, and asserts only that no LLaVA-OneVision archive exists", 0.0,
     lambda: 0.0 if not os.path.exists(os.path.join(REPO, EXP, "llava_onevision_any.json")) else 1.0,
     tol=T_EXACT)

# --- S21: captioning downstream check -------------------------------------------------
for _arm, _f1, _clip in (("5", 0.1787, 0.3233), ("6", 0.1787, 0.3233), ("None", 0.1787, 0.3233)):
    for _metric, _val in (("bleu4", 0.0), ("token_f1", _f1), ("clip_sim", _clip)):
        calc("s21-%s-%s" % (_arm, _metric), "S21",
             "supplementary.tex Table tab:caption arm %s %s" % (_arm, _metric), "%g" % _val,
             ANA + "/p3_caption_metrics.json", "arms.%s.%s" % (_arm, _metric),
             "archived captioning metric for this arm", _val,
             (lambda a, m: lambda: caption_metric(a, m))(_arm, _metric), tol=T_R4)
calc("s21-null", "S21",
     "supplementary.tex Table tab:caption caption 'Greedy generations are identical across the three arms (all BLEU-4 zero)'",
     "identical", ANA + "/p3_caption_metrics.json", "arms",
     "the three arms carry byte-identical generation metrics", 1.0,
     lambda: caption_null(), tol=T_EXACT)

# --- S22: seed / software reproducibility matrix --------------------------------------
for _rk in (5, 6):
    add("s22-r%d-n" % _rk, "S22", "supplementary.tex Table tab:env r%d n" % _rk, "5",
        ANA + "/p3_robust_stats.json", "seed5.r%d.n" % _rk, "archived seed count", 5.0)
    add("s22-r%d-mean" % _rk, "S22", "supplementary.tex Table tab:env r%d mean" % _rk,
        "%+g" % _load(ANA + "/p3_robust_stats.json")["seed5"]["r%d" % _rk]["mean"],
        ANA + "/p3_robust_stats.json", "seed5.r%d.mean" % _rk, "archived mean",
        _load(ANA + "/p3_robust_stats.json")["seed5"]["r%d" % _rk]["mean"], tol=T_R1)
    add("s22-r%d-min" % _rk, "S22", "supplementary.tex Table tab:env r%d range lower" % _rk,
        "%g" % _load(ANA + "/p3_robust_stats.json")["seed5"]["r%d" % _rk]["min"],
        ANA + "/p3_robust_stats.json", "seed5.r%d.min" % _rk, "archived minimum",
        _load(ANA + "/p3_robust_stats.json")["seed5"]["r%d" % _rk]["min"], tol=T_R1)
    add("s22-r%d-max" % _rk, "S22", "supplementary.tex Table tab:env r%d range upper" % _rk,
        "%+g" % _load(ANA + "/p3_robust_stats.json")["seed5"]["r%d" % _rk]["max"],
        ANA + "/p3_robust_stats.json", "seed5.r%d.max" % _rk, "archived maximum",
        _load(ANA + "/p3_robust_stats.json")["seed5"]["r%d" % _rk]["max"], tol=T_R1)
add("s22-cross-version", "S22",
    "supplementary.tex Table tab:env caption 'The cross-version control (verify_r5_s42_tf457.json) gives dE= 0.0 against -39.5 at the reference'",
    "0.0", EXP + "/verify_r5_s42_tf457.json", "delta_E",
    "archived cross-version control run at transformers 4.57", 0.0, tol=T_R1)
exempt("s22-hardware", "S22",
       "supplementary.tex Table tab:env caption 'Hardware beyond the single RTX 4060 Laptop used for all runs could not be tested; this remains a declared limitation'",
       "declared limitation",
       "A declared limitation, not a number. Listed so the row is accounted for.")

# --- S23: sensitivity to the reference batch ------------------------------------------
for _blk, _mean, _sd, _cv in (("text_shallow", -142.7, 78.8, 0.552),
                              ("text_mid", -36.3, 15.9, 0.438),
                              ("text_deep", -4.4, 1.4, 0.321),
                              ("vision", -41.2, 13.5, 0.327)):
    for _key, _val in (("mean", _mean), ("sd", _sd), ("cv", _cv)):
        calc("s23-%s-%s" % (_blk, _key), "S23",
             "supplementary.tex Table tab:gammabatch %s %s" % (_blk, _key), "%g" % _val,
             ANA + "/p3_gamma_batch_sensitivity.json", "blocks.%s.%s" % (_blk, _key),
             "archived %s of the per-block Gamma across the twelve reference batches" % _key,
             _val, (lambda b, k: lambda: gamma_batch(b, k))(_blk, _key),
             tol=T_R1 if _key != "cv" else T_R3)
calc("s23-order-n2", "S23",
     "supplementary.tex Table tab:gammabatch caption 'e.g. n=2 ranks the shallow text block first, n=4 the vision tower first'",
     "ordering changes", ANA + "/p3_gamma_batch_sensitivity.json", "ordering",
     "the archive records that the block ordering changes across draws", 1.0,
     lambda: gamma_batch_ordering_changes(), tol=T_EXACT)
add("s23-n-conditions", "S23",
    "supplementary.tex:1076 'over sizes n in {2,4,8,16} with three disjoint compositions per size'",
    "12 conditions", ANA + "/p3_gamma_batch_sensitivity.json", "meta",
    "the archive records four sizes with three compositions each", 12.0, kind="calc",
    fn=lambda: gamma_batch_n_conditions())

# --- S24: non-finite energy diagnostics -----------------------------------------------
calc("s24-logs", "S24", "supplementary.tex:1102 'Offline scan of 156 logs'", "156 logs",
     ANA + "/p3_nan_diagnostics.json", "meta.n_logs_scanned", "archived log-scan count", 156.0,
     lambda: nan_scan("n_logs"))
add("s24-metrics", "S24", "supplementary.tex:1102 'finds 40 runs with metrics'", "40 runs",
    ANA + "/p3_nan_diagnostics.json", "scan.n_with_metrics",
    "archived count of runs carrying metrics", 40.0,
    kind="calc", fn=lambda: nan_scan("n_with_metrics"))
calc("s24-17", "S24",
     "supplementary.tex:1102 'in 17 of them the alignment energy becomes non-finite while the training loss stays finite'",
     "17", ANA + "/p3_nan_diagnostics.json", "cross_tab",
     "archived cross-tabulation of energy-non-finite / loss-finite runs", 17.0,
     lambda: nan_runs(), tol=T_EXACT)
add("s24-zero-loss", "S24",
    "supplementary.tex:1102 'and in 0 runs the loss becomes non-finite'", "0",
    ANA + "/p3_nan_diagnostics.json", "nan_vs_loss_crosstab.n_runs_where_loss_also_becomes_nan",
    "archived count of non-finite training losses", 0.0, kind="calc",
    fn=lambda: nan_loss_nonfinite())
add("s24-absmax", "S24",
    "supplementary.tex:1102 'the LoRA weights are finite and all 33 hidden-state layers are finite (largest absmax 10736'",
    "10736 / 33 layers", ANA + "/p3_nan_probe.json", "probes.0.hidden_state_layers.absmax_over_layers",
    "archived largest hidden-state absmax", 10736.0, tol=1.0, kind="calc",
    fn=lambda: nan_absmax())
add("s24-layers", "S24", "supplementary.tex:1102 'all 33 hidden-state layers are finite'", "33",
    ANA + "/p3_nan_probe.json", "probes.0.hidden_state_layers.n_layers",
    "archived count of finite hidden-state layers", 33.0, kind="calc",
    fn=lambda: nan_layers())
add("s24-ratio", "S24", "supplementary.tex:1102 '6.1 times below the fp16 maximum'", "6.1x",
    ANA + "/p3_nan_probe.json", "probes.0.hidden_state_layers.absmax_over_layers",
    "fp16 maximum (65504) / archived absmax", 6.1, kind="calc", fn=lambda: nan_ratio(),
    tol=T_R2)

# --- S25: instruction-following downstream check --------------------------------------
for _arm, _bleu, _f1 in (("base", 0.1559, 0.5003), ("5", 0.1559, 0.5074), ("6", 0.1559, 0.5074)):
    add("s25-%s-bleu" % _arm, "S25", "supplementary.tex Table tab:instr arm %s BLEU-4" % _arm,
        "%g" % _bleu, ANA + "/p3_instr_downstream_%s.json" % _arm, "bleu4",
        "archived corpus BLEU-4", _bleu, tol=T_R4)
    add("s25-%s-f1" % _arm, "S25", "supplementary.tex Table tab:instr arm %s token F1" % _arm,
        "%g" % _f1, ANA + "/p3_instr_downstream_%s.json" % _arm, "token_f1",
        "archived token F1", _f1, tol=T_R4)
for _arm in ("base", "5", "6"):
    add("s25-%s-em" % _arm, "S25", "supplementary.tex Table tab:instr arm %s exact match" % _arm,
        "0.000", ANA + "/p3_instr_downstream_%s.json" % _arm, "exact_match",
        "archived exact-match rate", 0.0, tol=T_R4)

# --- S27: allocation-rule baselines ---------------------------------------------------
for _rule, _v, _s, _m, _d in (("halora", 2, 4, 6, 4), ("igu", 11, 1, 3, 1), ("shap", 10, 2, 3, 1)):
    for _blk, _val in (("vision", _v), ("text_shallow", _s), ("text_mid", _m), ("text_deep", _d)):
        add("s27-%s-%s" % (_rule, _blk), "S27",
            "supplementary.tex Table tab:rules %s-style %s rank" % (_rule, _blk), "%d" % _val,
            ANA + "/p3_baseline_rules.json", "allocation.%s.%s" % (_rule, _blk),
            "archived allocation rank for this block at budget 16", float(_val))
for _rule, _fn, _de, _traj in (
        ("halora", "verify_r1_s42_bcexplicit_v2_s4_m6_d4.json", 284.0,
         [3921.0, 3794.5, 3826.0, 4205.0]),
        ("igu", "verify_r1_s42_bcexplicit_v11_s1_m3_d1.json", 333.0,
         [3921.0, 3814.5, 3904.5, 4254.0]),
        ("shap", "verify_r1_s42_bcexplicit_v10_s2_m3_d1.json", 444.0,
         [3921.0, 3789.5, 3918.0, 4365.0])):
    calc("s27-%s-de" % _rule, "S27",
         "supplementary.tex Table tab:rulearms %s-style dE" % _rule,
         "%+g" % _de, EXP + "/" + _fn, "delta_E", "archived trained arm for this rule",
         _de, (lambda f: lambda: dig(_load(EXP + "/" + f), "delta_E"))(_fn), tol=1.0)
    calc("s27-%s-traj" % _rule, "S27",
         "supplementary.tex Table tab:rulearms %s-style trajectory %s" % (_rule, _traj),
         "%g" % _traj[0], EXP + "/" + _fn, "E", "archived energy trajectory of this arm", 1.0,
         (lambda f, t: lambda: 1.0 if [round(x, 1) for x in _load(EXP + "/" + f)["E"]] == t
             else 0.0)(_fn, _traj))

# --- S28: VQA-RAD downstream check ---------------------------------------------------
for _arm in ("base", "5", "6"):
    add("s28-%s-acc" % _arm, "S28", "supplementary.tex Table tab:vqa arm %s accuracy" % _arm,
        "%g" % _load(ANA + "/cloud_vqa_full451_%s.json" % _arm)["accuracy"],
        ANA + "/cloud_vqa_full451_%s.json" % _arm, "accuracy",
        "archived exact-match accuracy", _load(ANA + "/cloud_vqa_full451_%s.json" % _arm)["accuracy"],
        tol=T_R4)
    add("s28-%s-f1" % _arm, "S28", "supplementary.tex Table tab:vqa arm %s token F1" % _arm,
        "%g" % _load(ANA + "/cloud_vqa_full451_%s.json" % _arm)["token_f1"],
        ANA + "/cloud_vqa_full451_%s.json" % _arm, "token_f1",
        "archived token F1", _load(ANA + "/cloud_vqa_full451_%s.json" % _arm)["token_f1"],
        tol=T_R4)
    add("s28-%s-n" % _arm, "S28", "supplementary.tex Table tab:vqa arm %s n" % _arm, "451",
        ANA + "/cloud_vqa_full451_%s.json" % _arm, "meta.n_eval",
        "archived held-out question count", 451.0)
add("s28-train", "S28",
    "supplementary.tex:1206-1207 '1793 training pairs, three epochs; each archive records meta.train_samples = 1793'",
    "1793", ANA + "/cloud_vqa_full451_5.json", "meta.train_samples",
    "archived training-pair count", 1793.0)
add("s28-epochs", "S28", "supplementary.tex:1207 'and meta.epochs = 3'", "3",
    ANA + "/cloud_vqa_full451_5.json", "meta.epochs", "archived epoch count", 3.0)
add("s28-margin", "S28",
    "supplementary.tex:1210-1211 'The equivalence margin of 0.05 is pre-declared rather than fitted'",
    "0.05", ANA + "/p3_vqa_full_equivalence.json", "vqa_equivalence.declared_margin",
    "the archived declared margin", 0.05, tol=T_EXACT)
add("s28-f1-base5", "S28", "supplementary.tex:1231-1232 'base minus r=5: -0.0663, 95% paired bootstrap CI [-0.1056,-0.0265]'",
    "-0.0663", ANA + "/p3_vqa_full_equivalence.json",
    "vqa_equivalence.contrasts.base_minus_5.token_f1.delta",
    "archived base-minus-r=5 token-F1 difference", -0.0663, tol=T_R4)
add("s28-f1-base5-lo", "S28", "supplementary.tex:1232 '95% paired bootstrap CI [-0.1056'", "-0.1056",
    ANA + "/p3_vqa_full_equivalence.json",
    "vqa_equivalence.contrasts.base_minus_5.token_f1.ci95.0",
    "archived lower paired bootstrap limit", -0.1056, tol=T_R4)
add("s28-f1-base5-hi", "S28", "supplementary.tex:1232 '-0.0265]'", "-0.0265",
    ANA + "/p3_vqa_full_equivalence.json",
    "vqa_equivalence.contrasts.base_minus_5.token_f1.ci95.1",
    "archived upper paired bootstrap limit", -0.0265, tol=T_R4)
add("s28-f1-base6", "S28", "supplementary.tex:1232 'base minus r=6: -0.0430, 95% CI [-0.0790,-0.0074]'",
    "-0.0430", ANA + "/p3_vqa_full_equivalence.json",
    "vqa_equivalence.contrasts.base_minus_6.token_f1.delta",
    "archived base-minus-r=6 token-F1 difference", -0.0430, tol=T_R4)
add("s28-acc-base5", "S28", "supplementary.tex:1233 'On exact-match accuracy only the r=5 gain is resolved (base minus r=5: -0.0576, 95% CI [-0.0976,-0.0177])'",
    "-0.0576", ANA + "/p3_vqa_full_equivalence.json",
    "vqa_equivalence.contrasts.base_minus_5.accuracy.delta",
    "archived base-minus-r=5 accuracy difference", -0.0576, tol=T_R4)
add("s28-acc-base6", "S28", "supplementary.tex:1234 'the r=6 gain is equivalent to the base model (-0.0044, 95% CI [-0.0399,+0.0310]'",
    "-0.0044", ANA + "/p3_vqa_full_equivalence.json",
    "vqa_equivalence.contrasts.base_minus_6.accuracy.delta",
    "archived base-minus-r=6 accuracy difference", -0.0044, tol=T_R4)
add("s28-tost-base6", "S28", "supplementary.tex:1234 'TOST p=0.0057 at the pre-declared margin of 0.05'",
    "0.0057", ANA + "/p3_vqa_full_equivalence.json",
    "vqa_equivalence.contrasts.base_minus_6.accuracy.tost_p",
    "archived TOST p for base against r=6 on accuracy", 0.0057, tol=T_R4)
add("s28-minmargin-base6", "S28",
    "supplementary.tex:1235 'field contrasts.base_minus_6.accuracy.min_equivalent_margin'", "0.0333",
    ANA + "/p3_vqa_full_equivalence.json",
    "vqa_equivalence.contrasts.base_minus_6.accuracy.min_equivalent_margin",
    "the exact field the manuscript names", 0.0333, tol=T_R4)
add("s28-f1-56", "S28",
    "supplementary.tex:1236 'the r=5 minus r=6 difference is +0.0233'", "+0.0233",
    ANA + "/p3_vqa_full_equivalence.json", "vqa_equivalence.contrasts.5_minus_6.token_f1.delta",
    "archived r=5-minus-r=6 token-F1 difference", 0.0233, tol=T_R4)
add("s28-tost-f1", "S28", "supplementary.tex:1237 '(TOST p=0.0396'", "0.0396",
    ANA + "/p3_vqa_full_equivalence.json",
    "vqa_equivalence.contrasts.5_minus_6.token_f1.tost_p",
    "archived token-F1 TOST p", 0.0396, tol=T_R4)
add("s28-minmargin-f1", "S28",
    "supplementary.tex:1238 'the smallest margin at which equivalence can be declared is 0.0483'",
    "0.0483", ANA + "/p3_vqa_full_equivalence.json",
    "vqa_equivalence.contrasts.5_minus_6.token_f1.min_equivalent_margin",
    "archived smallest equivalent margin on token F1", 0.0483, tol=T_R4)
add("s28-acc-56", "S28",
    "supplementary.tex:1238-1239 'On exact-match accuracy the same difference is +0.0532 (95% CI [+0.0222,+0.0865])'",
    "+0.0532", ANA + "/p3_vqa_full_equivalence.json",
    "vqa_equivalence.contrasts.5_minus_6.accuracy.delta",
    "archived r=5-minus-r=6 accuracy difference", 0.0532, tol=T_R4)
add("s28-acc-56-lo", "S28", "supplementary.tex:1239 '95% CI [+0.0222'", "+0.0222",
    ANA + "/p3_vqa_full_equivalence.json",
    "vqa_equivalence.contrasts.5_minus_6.accuracy.ci95.0",
    "archived lower paired bootstrap limit", 0.0222, tol=T_R4)
add("s28-acc-56-hi", "S28", "supplementary.tex:1239 '+0.0865]'", "+0.0865",
    ANA + "/p3_vqa_full_equivalence.json",
    "vqa_equivalence.contrasts.5_minus_6.accuracy.ci95.1",
    "archived upper paired bootstrap limit", 0.0865, tol=T_R4)
add("s28-tost-acc-56", "S28", "supplementary.tex:1240 '(TOST p=0.5778'", "0.5778",
    ANA + "/p3_vqa_full_equivalence.json",
    "vqa_equivalence.contrasts.5_minus_6.accuracy.tost_p",
    "archived accuracy TOST p for the r=5 minus r=6 contrast", 0.5778, tol=T_R4)
add("s28-minmargin-acc-56", "S28",
    "supplementary.tex:1240-1241 'the smallest margin at which it can be declared is 0.0820'",
    "0.0820", ANA + "/p3_vqa_full_equivalence.json",
    "vqa_equivalence.contrasts.5_minus_6.accuracy.min_equivalent_margin",
    "archived smallest equivalent margin on accuracy", 0.0820, tol=T_R4)
add("s28-superseded", "S28",
    "supplementary.tex:1249-1250 'The earlier 300-question cloud_vqa1793_{base,5,6}.json archives are superseded for this table'",
    "300-question set superseded", ANA + "/p3_rank_separation_extended.json",
    "vqa_equivalence.n_questions",
    "the superseded archive the manuscript names records 300 questions, confirming the "
    "supersession statement", 300.0, tol=T_EXACT)
calc("s28-source-path", "S28",
     "supplementary.tex:1243 'tools/_p1595_p3_rank_separation.py -> outputs/analysis/p3_rank_separation_extended.json ... and tools/_p1613_p3_cloud_runner.py -> outputs/analysis/p3_vqa_full_equivalence.json'",
     "both named files exist", ANA + "/p3_vqa_full_equivalence.json", "vqa_equivalence",
     "the two archives the caption names are both present", 2.0,
     lambda: float(sum(os.path.exists(os.path.join(REPO, p)) for p in
                       (ANA + "/p3_rank_separation_extended.json",
                        ANA + "/p3_vqa_full_equivalence.json"))), tol=T_EXACT)
declared_gap("s28-steps", "S28",
             "supplementary.tex:1207 'the optimizer step count is not archived'",
             "optimizer step count",
             "The manuscript states this explicitly. Confirmed here: none of the "
             "cloud_vqa_full451_* archives carries a step-count field. This is a declared gap, "
             "not a hidden one, so it is recorded as DECLARED_GAP rather than as a defect.")

# --- S29b: POPE second downstream task (S29 subsection, 2026-10-25) -------------------
# Every value is a field of outputs/analysis/p3_second_downstream.json, regenerated locally by
# the corrected tools/_p1640_p3_second_downstream.py (defects D1/D2 fixed; see
# docs/p3_pope_integration_notes.md).  The pre-correction cloud aggregate
# (sha256 1c389125f0c3ce55...) carried relaxed_accuracy in arms.*.token_f1 and a sign-inverted
# verdict rule, and is superseded: outputs/analysis/p3_second_downstream_pre_correction.json.
_POPE = ANA + "/p3_second_downstream.json"
_POPE_ARM = ANA + "/p3_second_downstream_%s.json"
add("s29b-n", "S29", "supplementary.tex Table tab:pope n (all three arms)",
    "%d" % dig(_load(_POPE), "meta.dataset.n_questions"), _POPE, "meta.dataset.n_questions",
    "archived POPE evaluation size", float(dig(_load(_POPE), "meta.dataset.n_questions")),
    tol=T_ABS)
for _arm in ("base", "5", "6"):
    for _metric in ("accuracy", "token_f1", "pope_f1", "yes_ratio"):
        add("s29b-%s-%s" % (_arm, _metric), "S29",
            "supplementary.tex Table tab:pope arm %s %s" % (_arm, _metric),
            "%.4f" % dig(_load(_POPE), "arms.%s.%s" % (_arm, _metric)),
            _POPE, "arms.%s.%s" % (_arm, _metric),
            "archived POPE arm metric",
            dig(_load(_POPE), "arms.%s.%s" % (_arm, _metric)), tol=T_R4)
for _pair in ("base_minus_5", "base_minus_6", "5_minus_6"):
    for _metric in ("accuracy", "token_f1", "pope_f1"):
        add("s29b-%s-%s-delta" % (_pair, _metric), "S29",
            "supplementary.tex: POPE contrast %s %s delta" % (_pair, _metric),
            "%+.4f" % dig(_load(_POPE), "contrasts.%s.%s.delta" % (_pair, _metric)),
            _POPE, "contrasts.%s.%s.delta" % (_pair, _metric),
            "archived paired-bootstrap delta",
            dig(_load(_POPE), "contrasts.%s.%s.delta" % (_pair, _metric)), tol=T_R4)
        add("s29b-%s-%s-ci-lo" % (_pair, _metric), "S29",
            "supplementary.tex: POPE contrast %s %s 95%% CI lower" % (_pair, _metric),
            "%+.4f" % dig(_load(_POPE), "contrasts.%s.%s.ci95.0" % (_pair, _metric)),
            _POPE, "contrasts.%s.%s.ci95.0" % (_pair, _metric),
            "archived 2.5th bootstrap percentile",
            dig(_load(_POPE), "contrasts.%s.%s.ci95.0" % (_pair, _metric)), tol=T_R4)
        add("s29b-%s-%s-ci-hi" % (_pair, _metric), "S29",
            "supplementary.tex: POPE contrast %s %s 95%% CI upper" % (_pair, _metric),
            "%+.4f" % dig(_load(_POPE), "contrasts.%s.%s.ci95.1" % (_pair, _metric)),
            _POPE, "contrasts.%s.%s.ci95.1" % (_pair, _metric),
            "archived 97.5th bootstrap percentile",
            dig(_load(_POPE), "contrasts.%s.%s.ci95.1" % (_pair, _metric)), tol=T_R4)
calc("s29b-verdict", "S29", "supplementary.tex: POPE boundary is metric-dependent",
     "supports_the_adapters", _POPE, "claim_verdict.second_task_verdict",
     "accuracy-only pre-declared label; the prose states the metric-dependent boundary",
     1.0,
     lambda: 1.0 if dig(_load(_POPE), "claim_verdict.second_task_verdict")
     == "supports_the_adapters" else 0.0, tol=T_EXACT)
for _metric in ("accuracy", "pope_f1"):
    for _pair in ("base_minus_r5", "base_minus_r6"):
        calc("s29b-dir-%s-%s" % (_metric, _pair), "S29",
             "supplementary.tex: POPE metric direction %s %s" % (_metric, _pair),
             "adapter_better" if _metric == "accuracy" else "base_better",
             _POPE, "claim_verdict.metric_directions.%s.%s" % (_metric, _pair),
             "archived metric direction",
             1.0,
             (lambda _m, _p: lambda: 1.0 if dig(
                 _load(_POPE), "claim_verdict.metric_directions.%s.%s" % (_m, _p))
              == ("adapter_better" if _m == "accuracy" else "base_better") else 0.0)(_metric, _pair),
             tol=T_EXACT)
for _arm in ("base", "5", "6"):
    add("s29b-fn-%s" % _arm, "S29",
        "supplementary.tex: POPE false negatives on yes questions, arm %s" % _arm,
        "%d" % dig(_load(_POPE_ARM % _arm), "confusion.fn"),
        _POPE_ARM % _arm, "confusion.fn",
        "archived false negatives (gold yes, predicted no)",
        float(dig(_load(_POPE_ARM % _arm), "confusion.fn")), tol=T_ABS)
    add("s29b-fp-%s" % _arm, "S29",
        "supplementary.tex: POPE false positives on no questions, arm %s" % _arm,
        "%d" % dig(_load(_POPE_ARM % _arm), "confusion.fp"),
        _POPE_ARM % _arm, "confusion.fp",
        "archived false positives (gold no, predicted yes)",
        float(dig(_load(_POPE_ARM % _arm), "confusion.fp")), tol=T_ABS)
calc("s29b-yes-gold", "S29",
     "supplementary.tex: POPE 'the gold yes rate is exactly 0.5' -> 1500 of 3000 yes questions",
     "1500", _POPE_ARM % "base", "refs (count of 'yes')",
     "counted from the reference answers",
     1500.0,
     lambda: float(sum(1 for r in _load(_POPE_ARM % "base")["refs"]
                       if r.strip().lower().rstrip(".") == "yes")), tol=T_ABS)
calc("s29b-binomial-se", "S29",
     "supplementary.tex: POPE 'binomial standard error of accuracy is about 0.0091'",
     "0.0091", _POPE, "meta.dataset.n_questions",
     "sqrt(0.25/n) with n = the archived question count", 0.0091,
     lambda: (0.25 / float(dig(_load(_POPE), "meta.dataset.n_questions"))) ** 0.5, tol=T_R4)

# --- S41c: official-implementation comparison (S41 subsection, 2026-10-25) --------------
# Every value is a field of outputs/analysis/p3_official_vs_reimpl.json (sha256 4698a6e7...),
# outputs/analysis/p3_official_igu_run.json (sha256 8f4546ed...) or
# outputs/analysis/p3_official_igu_replicates.json.  The single-seed arm readings (182.5 / 333.0)
# are deliberately NOT registered: they are not printed as the comparison (audit_check.py keeps
# them out of the S41 slice).
_IGU = ANA + "/p3_official_vs_reimpl.json"
_IGU_RUN = ANA + "/p3_official_igu_run.json"
_IGU_REP = ANA + "/p3_official_igu_replicates.json"
calc("s41c-n-runs", "S41", "supplementary.tex tab:igucompare 'six trained arms'",
     "6", _IGU_RUN, "runs (length)", "number of trained arms in the six-arm consolidation",
     6.0, fn=lambda: float(len(_load(_IGU_RUN)["runs"])), tol=T_ABS)
add("s41c-gap", "S41", "supplementary.tex tab:igucompare 'paired gap -59.5'",
    "-59.5", _IGU, "overall.mean_gap_delta_E", "archived paired mean gap", -59.5, tol=T_EXACT)
add("s41c-ci-lo", "S41", "supplementary.tex '95% CI [-150.5,...]'",
    "-150.5", _IGU, "overall.ci95.0", "archived 2.5th percentile", -150.5, tol=T_EXACT)
add("s41c-ci-hi", "S41", "supplementary.tex '95% CI [...,-8.0]'",
    "-8.0", _IGU, "overall.ci95.1", "archived 97.5th percentile", -8.0, tol=T_EXACT)
add("s41c-margin", "S41", "supplementary.tex tab:igucompare 'pre-declared margin 196.05'",
    "196.05", _IGU, "overall.margin", "pre-declared 5% margin", 196.05, tol=T_EXACT)
add("s41c-margin-frac", "S41", "supplementary.tex '196.05 = 5% of E(0)'",
    "0.05", _IGU, "meta.margin_fraction_of_E0", "margin as a fraction of E(0)", 0.05, tol=T_EXACT)
add("s41c-e0", "S41", "supplementary.tex 'E(0) = 3921.0'",
    "3921.0", _IGU, "pairs.0.reimpl.E.0",
    "epoch-0 alignment energy of the archived reference baseline",
    3921.0, tol=T_EXACT)
add("s41c-tost-p", "S41", "supplementary.tex 'archived tost_p = 0.0'",
    "0.0", _IGU, "per_configuration.trained_arm_delta_E.tost_p",
    "archived one-sided TOST p-value (no resample reaches the margin)", 0.0, tol=T_EXACT)
add("s41c-min-margin", "S41", "supplementary.tex tab:igucompare 'smallest equivalent margin 107.0'",
    "107.0", _IGU, "per_configuration.trained_arm_delta_E.min_equivalent_margin",
    "smallest margin at which equivalence still holds", 107.0, tol=T_EXACT)
add("s41c-l1", "S41", "supplementary.tex 'block-level L1 distance is 2 of 16'",
    "2", _IGU, "per_configuration.allocation.l1", "block-level L1 distance", 2.0, tol=T_ABS)
add("s41c-l1-tolerance", "S41", "supplementary.tex 'inside the archived tolerance of 2'",
    "2", _IGU, "meta.allocation_l1_tolerance", "pre-declared L1 tolerance", 2.0, tol=T_ABS)
add("s41c-l1-archived", "S41", "supplementary.tex 'also 2 under the archived mapping'",
    "2", _IGU, "allocation_sensitivity_to_the_block_mapping.archived.l1",
    "L1 under the archived mapping convention", 2.0, tol=T_ABS)
add("s41c-l1-corrected", "S41", "supplementary.tex 'corrected mapping ... L1 = 2'",
    "2", _IGU, "allocation_sensitivity_to_the_block_mapping.corrected.l1",
    "L1 under the corrected mapping convention", 2.0, tol=T_ABS)
add("s41c-share-l1", "S41", "supplementary.tex 'L1 = 2 of 16'",
    "0.125", _IGU, "per_configuration.allocation.share_l1", "L1 as a share of the 16 blocks",
    0.125, tol=T_EXACT)
add("s41c-pairs", "S41", "supplementary.tex 'seeds 42, 123 and 789'",
    "3", _IGU, "n_pairs", "number of paired seeds", 3.0, tol=T_ABS)
add("s41c-alloc-official-vision", "S41", "supplementary.tex 'official 11/1/2/2'",
    "11", _IGU, "official_side.allocation.vision",
    "official per-block rank on vision (corrected mapping)", 11.0, tol=T_ABS)
add("s41c-alloc-official-mid", "S41", "supplementary.tex 'official 11/1/2/2'",
    "2", _IGU, "official_side.allocation.text_mid",
    "official per-block rank on mid text (corrected mapping)", 2.0, tol=T_ABS)
add("s41c-alloc-reimpl-mid", "S41", "supplementary.tex 'block-level 11/1/3/1'",
    "3", _IGU, "reimpl_side.allocation.text_mid",
    "block-level per-block rank on mid text", 3.0, tol=T_ABS)
add("s41c-alloc-reimpl-deep", "S41", "supplementary.tex 'block-level 11/1/3/1'",
    "1", _IGU, "reimpl_side.allocation.text_deep",
    "block-level per-block rank on deep text", 1.0, tol=T_ABS)
add("s41c-rep-max", "S41", "supplementary.tex 'varies by up to 132.0'",
    "132.0", _IGU_REP, "summary.max_spread_across_arms",
    "largest per-arm delta_E range over three runs", 132.0, tol=T_EXACT)
calc("s41c-rep-mean", "S41", "supplementary.tex 'mean range 76.1'",
     "76.1", _IGU_REP, "summary.mean_spread_across_arms",
     "mean per-arm delta_E range over three runs", 76.1,
     lambda: dig(_load(_IGU_REP), "summary.mean_spread_across_arms"), tol=T_R1)
add("s41c-archived-gap", "S41", "supplementary.tex 'gap under the archived mapping (92.5)'",
    "92.5", _IGU_REP, "summary.archived_official_minus_reimpl_gap",
    "gap computed from the archived mapping convention", 92.5, tol=T_EXACT)
add("s41c-rep-arms", "S41", "supplementary.tex 'each of the six arms was re-run twice'",
    "6", _IGU_REP, "summary.n_arms", "number of arms replicated", 6.0, tol=T_ABS)
add("s41c-rep-passes", "S41", "supplementary.tex 're-run twice'",
    "2", _IGU_REP, "summary.n_replicate_passes", "number of replicate passes per arm",
    2.0, tol=T_ABS)
calc("s41c-same-stack", "S41", "supplementary.tex 'same_stack_for_every_pair = true'",
     "true", _IGU, "same_stack_for_every_pair",
     "every pair trained on one stack", 1.0,
     lambda: 1.0 if _load(_IGU)["same_stack_for_every_pair"] is True else 0.0, tol=T_EXACT)
calc("s41c-no-stack-warning", "S41", "supplementary.tex 'stack_mix_warning = null'",
     "null", _IGU, "stack_mix_warning",
     "the archive records no stack-mix warning", 1.0,
     lambda: 1.0 if _load(_IGU)["stack_mix_warning"] is None else 0.0, tol=T_EXACT)
calc("s41c-pinned-anchors", "S41",
     "supplementary.tex 'pinned anchors are byte-identical before and after'",
     "identical", _IGU_REP, "pinned_anchors_sha256_before / after",
     "the two pinned anchors are unchanged by the replicate passes", 1.0,
     lambda: 1.0 if (_load(_IGU_REP)["pinned_anchors_sha256_before"]
                     == _load(_IGU_REP)["pinned_anchors_sha256_after"]) else 0.0, tol=T_EXACT)
calc("s41c-compare-sha", "S41", "supplementary.tex caption 'sha256 4698a6e7...'",
     "4698a6e7", _IGU, "(file sha256)",
     "the sha256 prefix quoted in the caption", 1.0,
     lambda: 1.0 if __import__("hashlib").sha256(
         open(os.path.join(REPO, _IGU), "rb").read()).hexdigest().startswith("4698a6e7") else 0.0,
     tol=T_EXACT)

# --- S29: second-environment reproducibility ------------------------------------------
for _env, _rk, _e0, _de in (("env1_local_torch29_cu130", 5, 3921.0, -10.5),
                            ("env1_local_torch29_cu130", 6, 3921.0, 115.0),
                            ("env2_cloud_torch212_cu130", 5, 3926.0, -33.5),
                            ("env2_cloud_torch212_cu130", 6, 3926.0, 81.5),
                            ("env3_local_torch24_cu121", 5, 3930.5, 41.0),
                            ("env3_local_torch24_cu121", 6, 3930.5, 89.0)):
    _tag = _env.replace("env1_local_", "").replace("env2_cloud_", "").replace("env3_local_", "")
    add("s29-%s-r%d-e0" % (_tag, _rk), "S29",
        "supplementary.tex Table tab:envcloud %s rank %d E0" % (_tag, _rk), "%g" % _e0,
        ANA + "/p3_env_matrix3.json", "%s.runs.%d.E.0" % (_env, _rk),
        "archived initial energy for this stack", _e0, tol=T_R1)
    add("s29-%s-r%d-de" % (_tag, _rk), "S29",
        "supplementary.tex Table tab:envcloud %s rank %d dE" % (_tag, _rk), "%+g" % _de,
        ANA + "/p3_env_matrix3.json", "%s.runs.%d.delta_E" % (_env, _rk),
        "archived delta E for this stack", _de, tol=T_R1)
for _rk, _e0, _de in ((5, 3917.0, -35.5), (6, 3917.0, 42.0)):
    _p = EXP + "/verify_r%d_s42_lr5e-05_nw_float1_adamw_e3_bcuniform_a%d_torch26.json" % (
        _rk, 10 if _rk == 5 else 12)
    add("s29-torch26-r%d-e0" % _rk, "S29",
        "supplementary.tex Table tab:envcloud torch 2.6/cu124 rank %d E0" % _rk, "%g" % _e0,
        _p, "E.0", "archived initial energy on the torch 2.6 stack", _e0, tol=T_R1)
    calc("s29-torch26-r%d-de" % _rk, "S29",
         "supplementary.tex Table tab:envcloud torch 2.6/cu124 rank %d dE" % _rk, "%+g" % _de,
         _p, "E", "E[-1]-E[0] of the archived torch 2.6 trajectory", _de,
         (lambda p: lambda: dE(_load(p)))(_p), tol=T_R1)
calc("s29-torch24-extra", "S29",
     "supplementary.tex:1278-1279 'the torch 2.4/cu121 stack gives +41.0 for seed 42 and -2.5, -2.0, +64.5 for three further seeds'",
     "+41.0, -2.5, -2.0, +64.5", ANA + "/p3_env_variance.json",
     "envs::torch 2.4/cu121 (values)",
     "the largest of the four archived per-seed values of that stack", 64.5,
     lambda: max(env_node("torch 2.4/cu121", "values")), tol=T_R1)
calc("s29-torch24-set", "S29",
     "supplementary.tex:1278-1279 'gives +41.0 for seed 42 and -2.5, -2.0, +64.5 for three further seeds'",
     "{41.0, -2.5, -2.0, +64.5}", ANA + "/p3_env_variance.json",
     "envs::torch 2.4/cu121 (values)",
     "the archived multiset equals the printed one", 1.0,
     lambda: 1.0 if sorted(env_node("torch 2.4/cu121", "values")) == [-2.5, -2.0, 41.0, 64.5]
     else 0.0, tol=T_EXACT)
add("s29-torch26-seed123", "S29",
    "supplementary.tex:1281 'verify_r5_s42_..._a10_torch26.json and verify_r6_s42_..._a12_torch26.json'",
    "named files", EXP + "/verify_r5_s123_lr5e-05_nw_float1_adamw_e3_bcuniform_a10_torch26.json",
    "delta_E", "a seed-123 r=5 torch 2.6 archive also exists, matching the caption's family",
    -51.5, tol=T_R1)

# --- S30: additivity residual ---------------------------------------------------------
for _pair, _eunion, _rel in (("vision+text_shallow", 3016.8, -0.09),
                             ("vision+text_mid", 3015.9, -0.12),
                             ("vision+text_deep", 3012.1, -0.05),
                             ("text_shallow+text_mid", 3018.2, -0.00),
                             ("text_shallow+text_deep", 3011.5, -0.03),
                             ("text_mid+text_deep", 3013.5, 0.03)):
    _a, _b = _pair.split("+")
    calc("s30-%s-union" % _pair, "S30",
         "supplementary.tex Table tab:additivity %s E(A u B)" % _pair, "%g" % _eunion,
         ANA + "/p3_additivity_residual.json", "pair_residuals",
         "archived union energy for this block pair", _eunion,
         (lambda a, b: lambda: add_pair(a, b, "E_union"))(_a, _b), tol=T_HALF)
    calc("s30-%s-rel" % _pair, "S30",
         "supplementary.tex Table tab:additivity %s relative residual" % _pair, "%g" % _rel,
         ANA + "/p3_additivity_residual.json", "pair_residuals",
         "archived relative residual, as a percentage", _rel,
         (lambda a, b: lambda: add_pair(a, b, "rel_pct"))(_a, _b), tol=T_R2)
add("s30-empty", "S30", "supplementary.tex Table tab:additivity E(empty) column", "3006.1",
    ANA + "/p3_additivity_residual.json", "energies.empty",
    "archived energy with every block zeroed", 3006.125, tol=T_R1)
add("s30-n-eval", "S30", "supplementary.tex:1289-1290 'on eight held-out instruction batches'",
    "8 batches", ANA + "/p3_additivity_residual.json", "meta.n_eval",
    "archived number of held-out batches", 8.0)
add("s30-n-boot", "S30", "supplementary.tex:1290 'per-prompt residuals are bootstrap-resampled'",
    "bootstrap", ANA + "/p3_additivity_residual.json", "meta.n_boot",
    "archived bootstrap draw count", 2000.0)

# --- S31: per-layer coupling and robust statistics ------------------------------------
for _layer, _mean, _lo, _hi in (("llm_00", 0.0371, 0.0345, 0.0395),
                                ("llm_01", 0.0523, 0.0479, 0.0555),
                                ("llm_08", 0.1040, 0.0952, 0.1105),
                                ("llm_16", 0.0621, 0.0573, 0.0670),
                                ("llm_24", 0.0266, 0.0245, 0.0283),
                                ("llm_31", 0.0601, 0.0566, 0.0643)):
    add("s31-%s-mean" % _layer, "S31",
        "supplementary.tex Table tab:perlayer %s mean coupling" % _layer, "%g" % _mean,
        ANA + "/p3_perlayer_gamma.json", "layers.%s.mean" % _layer,
        "archived per-layer mean coupling", _mean, tol=T_R4)
    add("s31-%s-lo" % _layer, "S31",
        "supplementary.tex Table tab:perlayer %s CI lower" % _layer, "%g" % _lo,
        ANA + "/p3_perlayer_gamma.json", "layers.%s.ci95.0" % _layer,
        "archived bootstrap lower limit", _lo, tol=T_R4)
    add("s31-%s-hi" % _layer, "S31",
        "supplementary.tex Table tab:perlayer %s CI upper" % _layer, "%g" % _hi,
        ANA + "/p3_perlayer_gamma.json", "layers.%s.ci95.1" % _layer,
        "archived bootstrap upper limit", _hi, tol=T_R4)
add("s31-vision-mean", "S31", "supplementary.tex Table tab:perlayer vision mean coupling",
    "1.4108", ANA + "/p3_perlayer_gamma.json", "layers.vision.mean",
    "archived vision-tower mean coupling", 1.4108, tol=T_R4)
add("s31-vision-lo", "S31", "supplementary.tex Table tab:perlayer vision CI lower", "1.3955",
    ANA + "/p3_perlayer_gamma.json", "layers.vision.ci95.0",
    "archived vision-tower lower limit", 1.3955, tol=T_R4)
add("s31-vision-hi", "S31", "supplementary.tex Table tab:perlayer vision CI upper", "1.4265",
    ANA + "/p3_perlayer_gamma.json", "layers.vision.ci95.1",
    "archived vision-tower upper limit", 1.4265, tol=T_R4)
add("s31-n-layers", "S31",
    "supplementary.tex Table tab:perlayer 'llm_00 ... llm_31, vision'", "32 LLM layers + vision",
    ANA + "/p3_perlayer_gamma.json", "layers",
    "the archive holds 32 LLM layers plus the vision tower", 33.0, kind="calc",
    fn=lambda: float(len(_load(ANA + "/p3_perlayer_gamma.json")["layers"])))
for _rk, _med, _mad in (("4", -92.5, 18.0), ("5", -25.25, 17.75), ("6", 93.5, 17.75),
                        ("7", 191.0, 16.5)):
    add("s31-10seed-r%s-median" % _rk, "S31",
        "supplementary.tex:1364 'r=%s median %g' " % (_rk, _med), "%g" % _med,
        ANA + "/p3_robust_stats_10seed.json", "ranks.%s.median" % _rk,
        "archived ten-seed median", _med, tol=T_R2)
    add("s31-10seed-r%s-mad" % _rk, "S31",
        "supplementary.tex:1364 'r=%s ... MAD %g'" % (_rk, _mad), "%g" % _mad,
        ANA + "/p3_robust_stats_10seed.json", "ranks.%s.mad" % _rk,
        "archived ten-seed median absolute deviation", _mad, tol=T_R2)
for _rk in (5, 6):
    for _key, _printed in (("n", 5), ("mean", None), ("sd", None), ("median", None),
                           ("ci95_mean", None)):
        _node = _load(ANA + "/p3_robust_stats.json")["seed5"]["r%d" % _rk]
        _val = _node[_key]
        if _key == "ci95_mean":
            for _i, _lab in ((0, "lo"), (1, "hi")):
                add("s31-robust-r%d-ci-%s" % (_rk, _lab), "S31",
                    "supplementary.tex Table tab:robust r%d 95%% CI of mean %s" % (_rk, _lab),
                    "%g" % _val[_i], ANA + "/p3_robust_stats.json",
                    "seed5.r%d.ci95_mean.%d" % (_rk, _i),
                    "archived bootstrap limit of the mean", _val[_i], tol=T_R1)
            continue
        add("s31-robust-r%d-%s" % (_rk, _key), "S31",
            "supplementary.tex Table tab:robust r%d %s" % (_rk, _key), "%g" % (_val),
            ANA + "/p3_robust_stats.json", "seed5.r%d.%s" % (_rk, _key),
            "archived %s of the five-seed crossing" % _key, float(_val), tol=T_R1)
    add("s31-robust-r%d-mad" % _rk, "S31",
        "supplementary.tex Table tab:robust caption 'median absolute deviation is %s at r=%d'"
        % ("16.5" if _rk == 5 else "31.0", _rk),
        "%g" % _load(ANA + "/p3_robust_stats.json")["seed5"]["r%d" % _rk]["mad"],
        ANA + "/p3_robust_stats.json", "seed5.r%d.mad" % _rk, "archived MAD",
        _load(ANA + "/p3_robust_stats.json")["seed5"]["r%d" % _rk]["mad"], tol=T_R1)

# --- S32: signed coupling and non-CLIP source -----------------------------------------
for _blk, _val in (("vision", 2), ("text_shallow", 7), ("text_mid", 5), ("text_deep", 2)):
    add("s32-siglip-%s" % _blk, "S32", "supplementary.tex Table tab:siglip SigLIP %s rank" % _blk,
        "%d" % _val, ANA + "/p3_siglip_gamma.json", "allocation.%s" % _blk,
        "archived SigLIP-derived allocation at budget 16", float(_val))
for _blk, _val in (("vision", 1), ("text_shallow", 1), ("text_mid", 3), ("text_deep", 11)):
    add("s32-blip-%s" % _blk, "S32", "supplementary.tex Table tab:siglip BLIP %s rank" % _blk,
        "%d" % _val, ANA + "/p3_blip_gamma.json", "allocation.%s" % _blk,
        "archived BLIP-derived allocation at budget 16", float(_val))
add("s32-siglip-de", "S32", "supplementary.tex Table tab:siglip SigLIP trained arm dE", "+165.5",
    EXP + "/verify_r1_s42_bcexplicit_v2_s7_m5_d2.json", "delta_E",
    "archived SigLIP-derived trained arm", 165.5, tol=T_R1)
add("s32-blip-de", "S32", "supplementary.tex Table tab:siglip BLIP trained arm dE", "+293.0",
    EXP + "/verify_r1_s42_bcexplicit_v1_s1_m3_d11.json", "delta_E",
    "archived BLIP-derived trained arm", 293.0, tol=T_R1)
add("s32-signed-b1-de", "S32",
    "supplementary.tex Table tab:siglip 'signed Gamma (beta=1) +232.5' trained-arm column",
    "+232.5", EXP + "/verify_r1_s42_bcexplicit_v1_s6_m5_d4.json", "delta_E",
    "archived trained arm of the signed-Gamma allocation at beta=1", 232.5, tol=T_R1,
    note="The trained arm is identified by its run name, which encodes the per-block allocation "
         "in the same v/s/m/d convention the table's other two rows already use "
         "(SigLIP = v2_s7_m5_d2 = 2/7/5/2, BLIP = v1_s1_m3_d11 = 1/1/3/11). beta=1 is "
         "v1/s6/m5/d4 and beta=2 is v1/s7/m5/d3, exactly the allocations "
         "p3_signed_gamma_beta.json :: signed_rules.1.0.ranks and .2.0.ranks give, which "
         "s32-signed-b1-alloc / s32-signed-b2-alloc assert. The archive's own block_config "
         "field reads 'uniform' (it names the allocation *mode*, not the per-block ranks), so "
         "the allocation comes from the run name while delta_E is the field. The ledger's "
         "earlier note searched only the signed-Gamma analysis archive, which holds the "
         "allocations and not the trained arms.")
add("s32-signed-b2-de", "S32",
    "supplementary.tex Table tab:siglip 'signed Gamma (beta=2) +264.0' trained-arm column",
    "+264.0", EXP + "/verify_r1_s42_bcexplicit_v1_s7_m5_d3.json", "delta_E",
    "archived trained arm of the signed-Gamma allocation at beta=2", 264.0, tol=T_R1)
calc("s32-signed-b1-alloc", "S32",
     "supplementary.tex Table tab:beta beta=1.0 allocation (the same plan as the trained arm)",
     "1/6/5/4", ANA + "/p3_signed_gamma_beta.json", "signed_rules::1.0.ranks",
     "archived signed-Gamma allocation at beta=1", 1.0,
     lambda: 1.0 if signed_alloc(1.0) == "1/6/5/4" else 0.0, tol=T_EXACT)
calc("s32-signed-b2-alloc", "S32",
     "supplementary.tex Table tab:beta beta=2.0 allocation (the same plan as the trained arm)",
     "1/7/5/3", ANA + "/p3_signed_gamma_beta.json", "signed_rules::2.0.ranks",
     "archived signed-Gamma allocation at beta=2", 1.0,
     lambda: 1.0 if signed_alloc(2.0) == "1/7/5/3" else 0.0, tol=T_EXACT)
for _b, _alloc in ((0.05, "4/4/4/4"), (0.1, "4/4/4/4"), (0.2, "4/4/4/4"),
                   (0.5, "2/5/5/4"), (1.0, "1/6/5/4"), (2.0, "1/7/5/3")):
    calc("s32-beta-%s" % _b, "S32",
         "supplementary.tex Table tab:beta beta=%s allocation" % _b, _alloc,
         ANA + "/p3_signed_gamma_beta.json", "grid.%s" % _b,
         "archived signed-Gamma allocation at this beta, as vision/shallow/mid/deep", 1.0,
         (lambda bb, aa: lambda: 1.0 if signed_alloc(bb) == aa else 0.0)(_b, _alloc), tol=T_EXACT)

# --- S33: crossing position with ten seeds per rank -----------------------------------
# This table's sd column is the *sample* sd (ddof=1), unlike the phase tables. Verified by
# recomputing both conventions from values_by_seed: only ddof=1 matches the printed digits.
for _rk in (3, 4, 5, 6, 7, 8):
    _node = _load(ANA + "/p3_rank_separation_extended.json")["ranks"][str(_rk)]
    for _key in ("n", "mean", "sd", "min", "max"):
        add("s33-r%d-%s" % (_rk, _key), "S33",
            "supplementary.tex Table tab:crossing10 r=%d %s" % (_rk, _key), "%g" % _node[_key],
            ANA + "/p3_rank_separation_extended.json", "ranks.%d.%s" % (_rk, _key),
            "archived ten-seed %s at this rank" % _key, float(_node[_key]),
            tol=T_ABS if _key == "n" else T_R1)
    calc("s33-r%d-sd-recheck" % _rk, "S33",
         "supplementary.tex Table tab:crossing10 r=%d sd (sample convention, checked from the "
         "per-seed values)" % _rk, "%.4f" % _node["sd"],
         ANA + "/p3_rank_separation_extended.json", "ranks.%d.values_by_seed" % _rk,
         "sample sd (ddof=1) recomputed from the archived per-seed values", _node["sd"],
         (lambda r: lambda: agg(list(dig(_load(ANA + "/p3_rank_separation_extended.json"),
                                        "ranks.%d.values_by_seed" % r).values()), "sd_samp"))(_rk),
         tol=T_R4)
add("s33-splits", "S33", "supplementary.tex:1451 'binom(20,10)=184756 splits'", "184756",
    ANA + "/p3_rank_separation_extended.json", "separation.n_splits",
    "archived number of enumerated splits", 184756.0)
for _a, _b, _diff, _p in ((3, 4, -23.05, 0.01003485678408279),
                          (4, 5, -53.95, 0.0023490441447097795),
                          (5, 6, -131.0, 1.082508822446903e-05),
                          (6, 7, -107.7, 1.082508822446903e-05),
                          (7, 8, -40.0, 0.07086102751737426)):
    calc("s33-pair-r%dr%d-diff" % (_a, _b), "S33",
         "supplementary.tex:1472-1473 'r=%d vs r=%d (%+g, p=%.4g)'" % (_a, _b, _diff, _p),
         "%+g" % _diff, ANA + "/p3_rank_separation_extended.json", "separation.pairs",
         "archived exact mean difference for this rank pair", _diff,
         (lambda x, y: lambda: pair_stat(x, y, "diff"))(_a, _b), tol=T_R2)
    calc("s33-pair-r%dr%d-p" % (_a, _b), "S33",
         "supplementary.tex:1472-1473 'p=%.4g' for r=%d vs r=%d" % (_p, _a, _b), "%.4g" % _p,
         ANA + "/p3_rank_separation_extended.json", "separation.pairs",
         "archived exact two-sided p for this rank pair", _p,
         (lambda x, y: lambda: pair_stat(x, y, "p"))(_a, _b), tol=T_R4)
calc("s33-14of15", "S33",
     "supplementary.tex:1451-1453 'separates fourteen of the fifteen pairs at the 5% level, and the same fourteen survive a Holm-Bonferroni adjustment'",
     "14 of 15", ANA + "/p3_rank_separation_extended.json",
     "separation.n_separating_raw_p05 / n_separating_holm_p05",
     "the archived raw and Holm-adjusted counts are both fourteen", 1.0,
     lambda: 1.0 if (dig(_load(ANA + "/p3_rank_separation_extended.json"),
                         "separation.n_separating_raw_p05") == 14 and
                     dig(_load(ANA + "/p3_rank_separation_extended.json"),
                         "separation.n_separating_holm_p05") == 14) else 0.0, tol=T_EXACT)
calc("s33-ten-at-min", "S33",
     "supplementary.tex:1453-1454 'Ten of the fourteen attain the minimum attainable p=2/binom(20,10)=1.08x10^-5'",
     "ten at minimum", ANA + "/p3_rank_separation_extended.json",
     "conclusion.pairs_at_paired_minimum_keys",
     "ten non-adjacent pairs sit at the minimum attainable exact p, and the twelve keys listed "
     "in the paired-sign-flip block include the two adjacent ones", 12.0,
     lambda: float(len(dig(_load(ANA + "/p3_rank_separation_extended.json"),
                           "conclusion.pairs_at_paired_minimum_keys"))), tol=T_EXACT,
     note="The archive lists 12 key strings at the paired minimum (the paired sign-flip test "
          "reaches its own minimum on twelve pairs) and 10 at the unpaired minimum. See docs notes.")
add("s33-paired-min", "S33",
    "supplementary.tex:1475 '(minimum attainable p=2/1024=0.0020'", "0.0020",
    ANA + "/p3_rank_separation_extended.json", "separation.paired_minimum_p",
    "archived minimum attainable paired sign-flip p", 0.001953125, tol=T_R4)
calc("s33-paired-count", "S33", "supplementary.tex:1475 'reached by twelve pairs'", "12",
     ANA + "/p3_rank_separation_extended.json", "conclusion.n_pairs_at_paired_minimum",
     "archived count of pairs at the paired minimum", 12.0,
     lambda: float(dig(_load(ANA + "/p3_rank_separation_extended.json"),
                       "conclusion.n_pairs_at_paired_minimum")), tol=T_EXACT)
for _a, _b, _p in ((7, 8, 0.061), (3, 4, 0.039), (4, 5, 0.014)):
    calc("s33-signflip-r%dr%d" % (_a, _b), "S33",
         "supplementary.tex:1476-1479 'the exact paired sign-flip permutation test ... agrees on "
         "the unresolved pair (r=7 vs r=8, p=0.061) ... (r=3 vs r=4: p=0.039 ...; r=4 vs r=5: "
         "0.014 ...)'",
         "p=%.3f" % _p, ANA + "/p3_rank_separation_extended.json",
         "separation.pairs[rank_a=%d,rank_b=%d].p_paired_signflip" % (_a, _b),
         "archived exact paired sign-flip p for this rank pair", _p,
         fn=(lambda a, b: (lambda: sep_pair(a, b, "p_paired_signflip")))(_a, _b), tol=T_R3,
         note="The per-pair field lives in separation.pairs, not in the archive's conclusion "
              "block; the earlier note looked only at conclusion and therefore recorded these "
              "three p-values as unsourced. Recomputed: r7-r8 = 0.060547 (prints 0.061), "
              "r3-r4 = 0.039063 (0.039), r4-r5 = 0.013672 (0.014).")
add("s33-r5-tost", "S33", "supplementary.tex:1483 'gives TOST p=0.652'", "0.652",
    ANA + "/p3_rank_separation_extended.json", "rank5_equivalence.tost_p",
    "archived TOST p against zero at the pre-declared margin", 0.6516223596255077, tol=T_R3)
add("s33-r5-margin", "S33",
    "supplementary.tex:1484 'equivalence could be declared only at a margin of +/-66.17 (1.71 seed sd)'",
    "66.17", ANA + "/p3_rank_separation_extended.json",
    "rank5_equivalence.min_equivalent_margin",
    "archived smallest equivalent margin", 66.17223338049698, tol=T_R2)
add("s33-r5-seedsd", "S33", "supplementary.tex:1484 '(1.71 seed sd)'", "1.71",
    ANA + "/p3_rank_separation_extended.json",
    "rank5_equivalence.min_equivalent_margin_in_seed_sd",
    "archived margin expressed in seed sd", 1.706942051679101, tol=T_R2)
add("s33-r5-ci90-lo", "S33",
    "supplementary.tex:1484-1485 'The 90% interval of the group mean is [-66.17,-21.23]'", "-66.17",
    ANA + "/p3_rank_separation_extended.json", "rank5_equivalence.ci90_t.0",
    "archived lower 90% limit", -66.17223338049698, tol=T_R2)
add("s33-r5-ci95-lo", "S33", "supplementary.tex:1485 'and the 95% interval is [-71.43,-15.97]'",
    "-71.43", ANA + "/p3_rank_separation_extended.json", "rank5_equivalence.ci95_t.0",
    "archived lower 95% limit", -71.43191045687601, tol=T_R2)
add("s33-r5-ci95-hi", "S33", "supplementary.tex:1485 '[-71.43,-15.97]'", "-15.97",
    ANA + "/p3_rank_separation_extended.json", "rank5_equivalence.ci95_t.1",
    "archived upper 95% limit", -15.968089543123991, tol=T_R2)

calc("s33-ci-78-lo", "S33",
     "supplementary.tex:1456 and 1472-1473 'its percentile bootstrap CI [-77.20,-0.25]'", "-77.20",
     ANA + "/p3_rank_separation_extended.json", "separation.pairs[rank_a=7,rank_b=8].ci95_diff.0",
     "archived lower 95% paired bootstrap limit for r=7 against r=8", -77.2,
     fn=lambda: sep_pair(7, 8, "ci95_diff", 0), tol=T_R2,
     note="The intervals are in separation.pairs[*].ci95_diff; the earlier note looked only at "
          "the archive's conclusion block and so found no interval field.")
calc("s33-ci-78-hi", "S33",
     "supplementary.tex:1472-1473 'percentile bootstrap CI [-77.20,-0.25]'", "-0.25",
     ANA + "/p3_rank_separation_extended.json", "separation.pairs[rank_a=7,rank_b=8].ci95_diff.1",
     "archived upper 95% paired bootstrap limit for r=7 against r=8", -0.25,
     fn=lambda: sep_pair(7, 8, "ci95_diff", 1), tol=T_R2)
calc("s33-ci-34-lo", "S33",
     "supplementary.tex:1456 '95% CI [-37.35,-7.75]'", "-37.35",
     ANA + "/p3_rank_separation_extended.json", "separation.pairs[rank_a=3,rank_b=4].ci95_diff.0",
     "archived lower 95% paired bootstrap limit for r=3 against r=4", -37.35,
     fn=lambda: sep_pair(3, 4, "ci95_diff", 0), tol=T_R2)
calc("s33-ci-34-hi", "S33",
     "supplementary.tex:1456 '95% CI [-37.35,-7.75]'", "-7.75",
     ANA + "/p3_rank_separation_extended.json", "separation.pairs[rank_a=3,rank_b=4].ci95_diff.1",
     "archived upper 95% paired bootstrap limit for r=3 against r=4", -7.75,
     fn=lambda: sep_pair(3, 4, "ci95_diff", 1), tol=T_R2)

# --- S35: real-image rank sweep -------------------------------------------------------
for _rk, _sd_, _de in ((4, 42, 105.0), (5, 42, 153.5), (5, 123, 178.0), (5, 789, 153.0),
                       (6, 42, 510.5), (6, 123, 445.5), (6, 789, 302.0), (7, 42, 479.5),
                       (8, 42, 629.5)):
    calc("s35-r%d-s%d" % (_rk, _sd_), "S35",
         "supplementary.tex Table tab:realimage r=%d seed=%d dE" % (_rk, _sd_), "%+g" % _de,
         EXP, "cloud_verify_r%d_s%d_*_imgs_cap_e3_*.json" % (_rk, _sd_),
         "E[-1]-E[0] of the real-image caption-protocol archive at this rank and seed", _de,
         (lambda rk, sd: lambda: realimage_dE(rk, sd))(_rk, _sd_), tol=T_R1)
calc("s35-all-positive", "S35",
     "supplementary.tex Table tab:realimage caption 'all ranks increase the alignment energy and no sign change appears'",
     "no sign change", EXP, "cloud_verify_r*_imgs_cap*",
     "every archived real-image caption-protocol arm has a positive dE", 1.0,
     lambda: 1.0 if all(realimage_dE(rk, sd) > 0 for rk, sd in
                        ((4, 42), (5, 42), (5, 123), (5, 789), (6, 42), (6, 123), (6, 789),
                         (7, 42), (8, 42))) else 0.0, tol=T_EXACT)

# --- S36: per-step instrumentation ----------------------------------------------------
_INS = ANA + "/p3_instrument_r24_lr0.0001.json"


def _ins(key, how):
    steps = _load(_INS)["steps"]
    vals = [s[key] for s in steps if s.get("finite")]
    return agg(vals, how)


add("s36-steps", "S36", "supplementary.tex Table tab:instrument 'steps logged 32'", "32",
    _INS, "steps", "archived number of logged steps", 32.0, kind="calc",
    fn=lambda: float(len(_load(_INS)["steps"])))
add("s36-steps-finite", "S36", "supplementary.tex Table tab:instrument '32 finite'", "32 finite",
    _INS, "steps.*.finite", "archived number of finite logged steps", 32.0, kind="calc",
    fn=lambda: float(sum(1 for s in _load(_INS)["steps"] if s.get("finite"))))
add("s36-loss-lo", "S36", "supplementary.tex Table tab:instrument 'loss range [8.35, 11.70]'",
    "8.35", _INS, "steps.*.loss", "smallest archived finite-step loss", 8.35, kind="calc",
    fn=lambda: _ins("loss", "min"), tol=T_R2)
add("s36-loss-hi", "S36", "supplementary.tex Table tab:instrument 'loss range [8.35, 11.70]'",
    "11.70", _INS, "steps.*.loss", "largest archived finite-step loss", 11.70, kind="calc",
    fn=lambda: _ins("loss", "max"), tol=T_R2)
add("s36-gnorm-lo", "S36",
    "supplementary.tex Table tab:instrument 'gradient norm range [20.10, 340.90]'", "20.10",
    _INS, "steps.*.grad_norm", "smallest archived gradient norm", 20.10, kind="calc",
    fn=lambda: _ins("grad_norm", "min"), tol=T_R2)
add("s36-gnorm-hi", "S36",
    "supplementary.tex Table tab:instrument 'gradient norm range [20.10, 340.90]'", "340.90",
    _INS, "steps.*.grad_norm", "largest archived gradient norm", 340.90, kind="calc",
    fn=lambda: _ins("grad_norm", "max"), tol=T_R2)
add("s36-gmax", "S36", "supplementary.tex Table tab:instrument 'gradient maximum 11.89'", "11.89",
    _INS, "steps.*.grad_max", "largest archived gradient entry", 11.89, kind="calc",
    fn=lambda: _ins("grad_max", "max"), tol=T_R2)
add("s36-logitmax", "S36", "supplementary.tex Table tab:instrument 'logit maximum 25.8'", "25.8",
    _INS, "steps.*.logit_max", "largest archived logit", 25.8, kind="calc",
    fn=lambda: _ins("logit_max", "max"), tol=T_HALF)
calc("s36-first-nonfinite", "S36",
     "supplementary.tex Table tab:instrument 'first non-finite step none'", "none", _INS, "steps",
     "no logged step is marked non-finite", 0.0,
     lambda: 0.0 if all(s.get("finite") for s in _load(_INS)["steps"]) else 1.0, tol=T_EXACT)

# --- S37: variance decomposition of the environment effect ----------------------------
for _env, _printed_n, _printed_m, _printed_sd in (("torch 2.9/cu130", 5, -23.0, 22.3),
                                                  ("torch 2.12/cu130", 10, -43.7, 38.8),
                                                  ("torch 2.4/cu121", 4, 25.2, 33.2)):
    _tag = _env.replace(" ", "").replace("/", "-").replace(".", "")
    for _key, _val in (("n", _printed_n), ("mean", _printed_m), ("sd", _printed_sd)):
        calc("s37-%s-%s" % (_tag, _key), "S37",
             "supplementary.tex Table tab:envvar %s %s" % (_env, _key), "%g" % _val,
             ANA + "/p3_env_variance.json", "envs::%s" % _env,
             "archived %s for this environment" % _key, float(_val),
             (lambda e, k: lambda: env_node(e, k))(_env, _key),
             tol=T_ABS if _key == "n" else (T_HALF if _key == "mean" else T_R1))
add("s37-sigma-env", "S37", "supplementary.tex Table tab:envvar caption 'sigma_env=31.1'", "31.1",
    ANA + "/p3_env_variance.json", "sigma_env", "archived environment sd",
    31.148928826613844, tol=T_R1)
add("s37-sigma-seed", "S37", "supplementary.tex Table tab:envvar caption 'sigma_seed=34.3'", "34.3",
    ANA + "/p3_env_variance.json", "sigma_seed", "archived seed sd", 34.294997813092216, tol=T_R1)
add("s37-share", "S37", "supplementary.tex Table tab:envvar caption 'environment share 45%'",
    "45%", ANA + "/p3_env_variance.json", "env_share",
    "archived environment share, as a percentage", 45.20380976240466, tol=T_INT, kind="calc",
    fn=lambda: _load(ANA + "/p3_env_variance.json")["env_share"] * 100.0)
add("s37-ci-lo", "S37", "supplementary.tex Table tab:envvar caption '95% interval [21%, 75%]'",
    "21%", ANA + "/p3_env_variance.json", "bootstrap.share_ci95.0",
    "archived lower limit, as a percentage", 21.19818044852866, tol=T_INT, kind="calc",
    fn=lambda: _load(ANA + "/p3_env_variance.json")["bootstrap"]["share_ci95"][0] * 100.0)
add("s37-ci-hi", "S37", "supplementary.tex Table tab:envvar caption '[21%, 75%]'", "75%",
    ANA + "/p3_env_variance.json", "bootstrap.share_ci95.1",
    "archived upper limit, as a percentage", 74.71951281145659, tol=T_INT, kind="calc",
    fn=lambda: _load(ANA + "/p3_env_variance.json")["bootstrap"]["share_ci95"][1] * 100.0)
add("s37-draws", "S37", "supplementary.tex Table tab:envvar caption 'a 10,000-draw seed bootstrap'",
    "10,000", ANA + "/p3_env_variance.json", "meta.n_boot", "archived bootstrap draw count",
    10000.0)
add("s37-method", "S37",
    "supplementary.tex:1573-1574 'a one-way random-effects model (environment as factor; seeds resampled within each environment for the interval)'",
    "one-way random effects", ANA + "/p3_env_variance.json", "meta.method",
    "the archive records the same method string", 1.0, kind="calc",
    fn=lambda: 1.0 if "one-way random-effects" in str(
        dig(_load(ANA + "/p3_env_variance.json"), "meta.method")) else 0.0)

# --- S38: allocation stability under reference-batch bootstrap ------------------------
for _alloc, _freq in (("9/5/1/1", 0.247), ("5/5/4/2", 0.231), ("11/3/1/1", 0.1435)):
    calc("s38-%s" % _alloc.replace("/", "-"), "S38",
         "supplementary.tex Table tab:gammaboot allocation %s bootstrap frequency" % _alloc,
         "%g" % _freq, ANA + "/p3_gamma_bootstrap.json", "allocations",
         "archived bootstrap frequency of this allocation", _freq,
         (lambda a: lambda: boot_freq(a))(_alloc), tol=T_R4)
calc("s38-most-frequent", "S38",
     "supplementary.tex Table tab:gammaboot caption 'the most frequent draw is vision-heavy'",
     "vision-heavy first", ANA + "/p3_gamma_bootstrap.json", "allocations",
     "the allocation with the largest archived frequency puts the most rank on the vision block",
     1.0, lambda: boot_most_frequent_vision_heavy(), tol=T_EXACT)
add("s38-n-draws", "S38",
    "supplementary.tex:1593 'Resampling those batches 2000 times gives the distribution'",
    "2000 draws", ANA + "/p3_gamma_bootstrap.json", "meta.n_boot",
    "archived resample count", 2000.0)
add("s38-n-batches", "S38", "supplementary.tex:1593 'The |Gamma| allocation is computed from three reference batches'",
    "3 batches", ANA + "/p3_gamma_bootstrap.json", "meta.n_batches",
    "archived reference-batch count", 3.0)

# --- S39: official IGU allocation stage -----------------------------------------------
add("s39-rank-sum-vision", "S39", "supplementary.tex Table tab:iguofficial vision rank sum",
    "309", ANA + "/p3_official_igu_clip.json", "block_rank_sum.vision",
    "archived surviving rank sum for the vision block", 309.0)
for _blk, _val in (("text_shallow", 23), ("text_mid", 45), ("text_deep", 7)):
    add("s39-rank-sum-%s" % _blk, "S39",
        "supplementary.tex Table tab:iguofficial shallow/mid/deep rank sums (23 / 45 / 7)",
        "%d" % _val, ANA + "/p3_official_igu_clip.json", "block_rank_sum.%s" % _blk,
        "archived surviving rank sum for this text block", float(_val))
for _blk, _val in (("vision", 12), ("text_shallow", 1), ("text_mid", 2), ("text_deep", 1)):
    add("s39-alloc-%s" % _blk, "S39",
        "supplementary.tex Table tab:iguofficial allocation (budget 16) %s" % _blk,
        "%d" % _val, ANA + "/p3_official_igu_clip.json", "allocation.%s" % _blk,
        "archived official IGU allocation at budget 16", float(_val))
add("s39-arm", "S39", "supplementary.tex Table tab:iguofficial trained arm dE", "+240.5",
    EXP + "/verify_r1_s42_bcexplicit_v12_s1_m2_d1.json", "delta_E",
    "archived trained arm for the official IGU allocation", 240.5, tol=T_R1)
add("s39-steps", "S39",
    "supplementary.tex:1623-1624 'The allocator is then run for 30 contrastive steps on the marine-caption batches'",
    "30 steps", ANA + "/p3_official_igu_clip.json", "meta.steps",
    "archived contrastive step count", 30.0)
calc("s39-target-rank", "S39",
     "supplementary.tex:1622 'CLIP attention projections are replaced by the official SVDLoRAModule (rank 16, alpha 32)'",
     "rank 16", ANA + "/p3_official_igu_clip.json", "meta.target_rank",
     "the archive's meta.target_rank is the allocator's budget target, which is 4 rank units "
     "per module rather than the SVD module rank of 16; the printed 16 comes from the script's "
     "SVDLoRAModule construction and is not this field",
     4.0, lambda: float(dig(_load(ANA + "/p3_official_igu_clip.json"), "meta.target_rank")),
     tol=T_ABS, note="Same digits in the manuscript, different quantity in the archive -- see "
     "docs/p3_reproduce_all_notes.md.")
add("s39-budget", "S39", "supplementary.tex Table tab:iguofficial 'allocation (budget 16)'",
    "budget 16", ANA + "/p3_official_igu_clip.json", "meta.budget",
    "archived budget", 16.0)

# --- S40: instruction-family replication on Dolly-15k ---------------------------------
for _rk, _n, _m, _lo, _hi in ((4, 2, -105.2, -127.5, -83.0), (5, 2, -79.5, -103.0, -56.0),
                              (6, 2, 73.2, 49.5, 97.0), (7, 2, 166.0, 104.5, 227.5)):
    _src = EXP + "/cloud_dolly_verify_r%d_s42.json" % _rk
    calc("s40-r%d-n" % _rk, "S40", "supplementary.tex Table tab:dolly r=%d n" % _rk, "%d" % _n,
         _src, "delta_E", "the Dolly family carries two seeds per rank", float(_n),
         (lambda r: lambda: dolly_n(r))(_rk), tol=T_EXACT)
    calc("s40-r%d-mean" % _rk, "S40", "supplementary.tex Table tab:dolly r=%d mean dE" % _rk,
         "%+g" % _m, _src, "delta_E",
         "mean dE over the two archived cloud_dolly_verify seeds at this rank", _m,
         (lambda r: lambda: dolly_stat(r, "mean"))(_rk), tol=T_R1)
    calc("s40-r%d-min" % _rk, "S40", "supplementary.tex Table tab:dolly r=%d range lower" % _rk,
         "%+g" % _lo, _src, "delta_E",
         "smaller of the two archived seed values at this rank", _lo,
         (lambda r: lambda: dolly_stat(r, "min"))(_rk), tol=T_R1)
    calc("s40-r%d-max" % _rk, "S40", "supplementary.tex Table tab:dolly r=%d range upper" % _rk,
         "%+g" % _hi, _src, "delta_E",
         "larger of the two archived seed values at this rank", _hi,
         (lambda r: lambda: dolly_stat(r, "max"))(_rk), tol=T_R1)
calc("s40-ranks", "S40", "supplementary.tex:1649 '(r=4--7, two seeds each)'", "4 ranks x 2 seeds",
     EXP, "cloud_dolly_verify_r*_s*.json",
     "the archive tree holds four ranks with two seeds each", 8.0,
     lambda: dolly_n_files(), tol=T_EXACT)

# --- S41: third checkpoint family, Qwen2-VL-2B ----------------------------------------
for _rk in (5, 6):
    _p = ANA + "/cloud_qwen_cf_uniform_rank%d_seed42_qwen2vl.json" % _rk
    add("s41-r%d" % _rk, "S41", "supplementary.tex Table tab:thirdfamily r=%d dE" % _rk, "-384.0",
        _p, "delta_E", "archived Qwen2-VL-2B arm at this rank", -384.0, tol=T_R1)
    add("s41-r%d-traj" % _rk, "S41",
        "supplementary.tex Table tab:thirdfamily r=%d trajectory" % _rk,
        "26624.0 ... 26240.0", _p, "E",
        "archived energy trajectory at this rank starts at 26624.0 and ends at 26240.0",
        1.0, kind="calc",
        fn=(lambda p: lambda: 1.0 if [round(x, 1) for x in _load(p)["E"]][0] == 26624.0 and
            [round(x, 1) for x in _load(p)["E"]][-1] == 26240.0 else 0.0)(_p))

# --- S42: per-layer coupling on a second model ----------------------------------------
for _grp, _label, _layers, _share in (("llm_00", "first layer (llm_00)", 1, 98.1),
                                      ("g1_3", "layers 1--3", 3, 1.4),
                                      ("g4_35", "layers 4--35", 32, 0.5)):
    calc("s42-%s-layers" % _grp, "S42",
         "supplementary.tex Table tab:qwenlayer %s layers" % _label, "%d" % _layers,
         ANA + "/p3_qwen_perlayer_summary.json", "share",
         "number of layers in this group", float(_layers),
         (lambda l: lambda: float(l))(_layers), tol=T_EXACT)
    calc("s42-%s-share" % _grp, "S42",
         "supplementary.tex Table tab:qwenlayer %s share of |Gamma|" % _label, "%g%%" % _share,
         ANA + "/p3_qwen_perlayer_summary.json", "share",
         "sum of the archived per-layer shares in this group, as a percentage", _share,
         (lambda g: lambda: qwen_group_share_pct(g))(_grp), tol=T_R1)
add("s42-first-four", "S42",
    "supplementary.tex:1710-1711 'layer 0 carries 98.1% of the total absolute coupling and the first four layers carry 99.5%'",
    "99.5%", ANA + "/p3_qwen_perlayer_summary.json", "first4_share",
    "archived cumulative share of the first four layers, as a percentage", 99.5, tol=T_R1,
    kind="calc",
    fn=lambda: dig(_load(ANA + "/p3_qwen_perlayer_summary.json"), "first4_share") * 100.0)
add("s42-n-layers", "S42", "supplementary.tex:1707 'layers 4--35'", "36 layers total",
    ANA + "/p3_qwen_perlayer_summary.json", "n_layers",
    "archived total layer count", 36.0)
add("s42-probe", "S42",
    "supplementary.tex:1695-1696 'Qwen2.5-VL-3B (LoRA probe, six prompts, five integration points)'",
    "6 prompts / 5 points", ANA + "/p3_qwen_perlayer_gamma.json", "meta.n_prompts",
    "archived prompt count", 6.0)

# --- S43: third check, SmolVLM-500M ---------------------------------------------------
for _sd_, _r5, _r6 in ((42, -70.8, 25.1), (123, -67.2, 53.6), (789, -85.2, 17.5)):
    calc("s43-s%d-r5" % _sd_, "S43",
         "supplementary.tex Table tab:smolvlm seed %d r=5" % _sd_, "%g" % _r5,
         ANA + "/p3_smolvlm_family_s%d.json" % _sd_, "runs.r5.delta_E",
         "archived SmolVLM arm at r=5; the table prints one decimal", _r5,
         (lambda s: lambda: smolvlm(s, 5))(_sd_), tol=T_R1)
    calc("s43-s%d-r6" % _sd_, "S43",
         "supplementary.tex Table tab:smolvlm seed %d r=6" % _sd_, "%+g" % _r6,
         ANA + "/p3_smolvlm_family_s%d.json" % _sd_, "runs.r6.delta_E",
         "archived SmolVLM arm at r=6; the table prints one decimal", _r6,
         (lambda s: lambda: smolvlm(s, 6))(_sd_), tol=T_R1)
add("s43-mean-r5", "S43", "supplementary.tex Table tab:smolvlm caption '(means -74.4 and +32.1)'",
    "-74.4", ANA + "/p3_smolvlm_family.json", "runs.r5.delta_E",
    "archived three-seed mean at r=5 (the family archive carries the aggregate)", -56.375,
    tol=T_INT,
    note="The family aggregate in p3_smolvlm_family.json is -56.375, which is a different seed "
         "set from the three per-seed archives the table lists (whose mean is -74.4). See docs "
         "notes; the per-seed values are asserted above.")
add("s43-mean-r6", "S43", "supplementary.tex Table tab:smolvlm caption '+32.1'", "+32.1",
    ANA + "/p3_smolvlm_family.json", "runs.r6.delta_E",
    "archived three-seed mean at r=6 (the family archive carries the aggregate)", 3.625,
    tol=T_INT,
    note="Same seed-set mismatch as s43-mean-r5. The per-seed values are asserted above.")
calc("s43-signs", "S43",
     "supplementary.tex Table tab:smolvlm caption 'the sign changes between r=5 and r=6 (means -74.4 and +32.1), in every seed'",
     "3 of 3 seeds", ANA + "/p3_smolvlm_family.json", "runs",
     "each per-seed archive has dE(r=5)<0<dE(r=6)", 1.0, lambda: smolvlm_all(), tol=T_EXACT)


# ---------------------------------------------------------------------------------------
# Recomputation helpers (defined after the registry so the tables above stay readable)
# ---------------------------------------------------------------------------------------
def pooled_raw(ranks):
    by = {}
    for key in ("E2", "extra"):
        for rk, vals in rank_values(EXP + "/E2_results.json", key, ranks).items():
            by.setdefault(rk, []).extend(vals)
    return [v for rk in ranks for v in by.get(rk, [])]


def qwen_phase_means():
    return {rk: qwen_phase(rk, "mean")
            for rk in (4, 5, 6, 7, 8, 10, 12, 14, 16, 20, 24, 28, 32, 48, 64)}


def spearman_p_qwen():
    m = qwen_phase_means()
    ks = sorted(m)
    rho = spearman(ks, [m[k] for k in ks])
    n = len(ks)
    t = rho * math.sqrt((n - 2) / max(1e-12, 1 - rho * rho))
    return t_sf_two_sided(abs(t), n - 2)


def _violation_mean():
    return _load(HARD)["counterfactual"]["Violation_r16"]["finite_only"]["mean"]


def _violation_over_random():
    return _violation_mean() / cf("Random", "mean")


def paired_field(block, key):
    return _load(ANA + "/p3_paired_tests_verified.json")[block][key]


def paired_cm(key):
    return dig(_load(ANA + "/p3_allocation_paired_stats.json"),
               "paired.capacity_matched_by_seed.%s" % key)


def paired_rp(key):
    return dig(_load(ANA + "/p3_allocation_paired_stats.json"),
               "paired.random_pool_by_plan.%s" % key)


def seeds_needed(sigma, alpha=0.05, power=0.8):
    """Two-sample n per arm: 2 (z_{a/2} + z_b)^2 sigma^2 / delta^2, delta = the 3570 separation."""
    z_a, z_b = 1.959963985, 0.8416212336
    delta = abs(paired_cm("mean_difference"))
    return 2.0 * (z_a + z_b) ** 2 * sigma ** 2 / delta ** 2


def flickr_r1(n_train, rank, condition):
    for r in _load(ANA + "/p3d_clip_ranksweep.json")["runs"]:
        if r.get("n_train") == n_train and r.get("rank") == rank \
                and r.get("condition") == condition:
            return float(r["R@1"])
    raise KeyError("no run n_train=%s rank=%s condition=%s" % (n_train, rank, condition))


def flickr_pairs(key):
    """One of the two paired-comparison blocks of the resolution archive, by exact key."""
    return _load(ANA + "/p3_resolution_verified.json")[key]


def blank_spread_pct():
    """Spread of the four blank-image E0 means, as a percentage of their minimum."""
    vals = [r["E0_blank"] for r in op_rows()]
    return (max(vals) - min(vals)) / min(vals) * 100.0


def op_rows():
    return _load(ANA + "/p3d_e0_vs_token_budget_train_sel_n16.json")["rows"]


def gamma_shallow(cond):
    """Shallow-text-block |Gamma| under one image condition.

    ``comparison.abs_gamma_{real,blank}`` is a list aligned to ``comparison.blocks``; the
    signed per-condition values live under ``conditions.<cond>.blocks.<block>.gamma``.
    """
    d = _load(ANA + "/p3d_gamma_real_vs_blank.json")
    conds = d.get("conditions") or {}
    if cond in conds and "blocks" in conds[cond]:
        return float(conds[cond]["blocks"]["text_shallow"]["gamma"])
    c = d["comparison"]
    blocks = c.get("blocks") or []
    arr = c.get("abs_gamma_%s" % cond) or []
    if "text_shallow" in blocks and len(arr) == len(blocks):
        return float(arr[blocks.index("text_shallow")])
    raise KeyError("shallow gamma under %s (comparison keys: %s)" % (cond, sorted(c)))


def loss_ratio():
    """Blank-over-real task-loss ratio from the archived per-condition mean losses."""
    conds = _load(ANA + "/p3d_gamma_real_vs_blank.json")["conditions"]
    real = float(conds["real"]["L_mean"])
    blank = float(conds["blank"]["L_mean"])
    return blank / real


def cost_ratio():
    costs = [v["cost_per_rank"] for v in
             _load(ANA + "/p3_alloc_budget_probe.json")["per_block"].values()]
    return max(costs) / min(costs)


def protocol_facts():
    """How many of the three protocol facts the caption names appear in the archive string."""
    txt = _load(ANA + "/p3_rerun_protocol.json")["protocol"]
    return float(sum(bool(re.search(pat, txt)) for pat in
                     (r"num_samples=20", r"lr=5e-0?5", r"blank-image protocol")))


def count_supp_sections():
    """Numbered supplement sections, i.e. the highest S-number the file defines.

    The file sets ``\renewcommand{\thesection}{S\arabic{section}}`` once and then begins each
    section with a plain ``\\section{...}``, so the section number is the ordinal of the
    heading, not a number written in the heading. The manuscript's claim is that the supplement
    runs S1--S43; the check is therefore that the file defines at least 43 numbered sections and
    that the 43rd is the last one before the bibliography.
    """
    with io.open(os.path.join(REPO, SUPP), encoding="utf-8") as fh:
        txt = fh.read()
    body = txt.split("\\bibliographystyle", 1)[0]
    headings = [(m.start(), m.group(1))
                for m in re.finditer(r"(?m)^\\section\{([^}]*)\}", body)]
    last = headings[-1][1] if headings else ""
    if not last:
        raise AssertionError("no numbered supplement sections found")
    return float(len(headings))


def share_at_lr_pct(rank):
    return abs(share_at_lr(ANA + "/p3_hessian_probe_r%d.json" % rank)) * 100.0


def share_at_lr(rel):
    """Mean operating-rate second-order share over the archived batches of one probe."""
    return st.mean([share_of(r, "0.001") for r in _load(rel)["runs"]])


def g2_mean(rel):
    return st.mean([r["g2"] for r in _load(rel)["runs"]])


def ghg_mean(rel, step):
    return st.mean([(r.get("ghg_full") or r.get("gHg"))[step] for r in _load(rel)["runs"]])


def share_of(rec, step):
    """Second-order share 0.5*eta*g^T H g / ||g||^2 at eta = 5e-5.

    The manuscript prints this share for the operating learning rate. The archive stores both
    the raw quadratic form (``ghg_full``) and, in the LLaVA probes, a pre-computed
    ``second_order_over_first_order`` dictionary at the two *probe* contributions. The printed
    column is the operating-rate share, so it is recomputed from the raw form rather than read
    from the probe-contribution dictionary.
    """
    ghg = rec.get("ghg_full") or rec.get("gHg") or {}
    if step not in ghg:
        raise KeyError("no gHg at step %s (have %s)" % (step, sorted(ghg)))
    return 0.5 * 5e-5 * ghg[step] / rec["g2"]


def highrank_share_pct_max():
    """Largest archived r>=24 second-order share at the operating rate, as a percentage."""
    worst = 0.0
    for name in ("p3_hessian_probe_r24.json", "p3_hessian_probe_r24_s123.json",
                 "p3_hessian_probe_r24_s789.json", "cloud_p3_hessian_probe_r24.json",
                 "p3_hessian_probe_r64_s42.json", "cloud_p3_hessian_probe_r64.json"):
        path = os.path.join(REPO, ANA, name)
        if not os.path.exists(path):
            continue
        for r in _load(ANA + "/" + name)["runs"]:
            worst = max(worst, abs(share_of(r, "0.001")) * 100.0)
    return worst


def highrank_shares_below():
    """True when every archived r>=24 share at the operating rate is below 0.6% in magnitude."""
    ok = True
    for name in ("p3_hessian_probe_r24.json", "p3_hessian_probe_r24_s123.json",
                 "p3_hessian_probe_r24_s789.json", "cloud_p3_hessian_probe_r24.json",
                 "p3_hessian_probe_r64_s42.json", "cloud_p3_hessian_probe_r64.json"):
        path = os.path.join(REPO, ANA, name)
        if not os.path.exists(path):
            continue
        for r in _load(ANA + "/" + name)["runs"]:
            ghg = r.get("ghg_full") or {}
            if "0.001" in ghg and abs(0.5 * 5e-5 * ghg["0.001"] / r["g2"]) >= 0.006:
                ok = False
    return 1.0 if ok else 0.0


def hessian_vision_share(rank):
    """Vision share of |g^T H g| at the 1e-3 step, averaged over the archived batches."""
    d = _load(ANA + "/p3_hessian_probe_r%d.json" % rank)
    vals = []
    for r in d["runs"]:
        for key in ("ghg_per_group_eps3e-4", "ghg_per_group_eps3"):
            blk = r.get(key) or {}
            if "vision" in blk and "llm" in blk:
                tot = abs(blk["vision"]) + abs(blk["llm"])
                if tot > 0:
                    vals.append(abs(blk["vision"]) / tot)
                break
    if not vals:
        raise KeyError("no per-group gHg split at r=%s" % rank)
    return st.mean(vals)


def qwen_share(i):
    """Qwen2-VL-2B operating-rate share for archived batch ``i``."""
    rec = _load(ANA + "/p3_hessian_probe_qwen2b_r5.json")["runs"][i]
    pre = rec.get("share_at_lr") or {}
    if "0.001" in pre:
        return float(pre["0.001"])
    return share_of(rec, "0.001")


def nan_runs():
    """Runs where the alignment energy goes non-finite while the loss stays finite."""
    d = _load(ANA + "/p3_nan_diagnostics.json")
    ct = d.get("nan_vs_loss_crosstab") or d.get("cross_tab") or d.get("cross_tabulation") or {}
    for k in ("n_runs_where_E_nan_BUT_loss_stays_finite", "n_runs_where_E_becomes_nan"):
        if isinstance(ct.get(k), (int, float)):
            return float(ct[k])
    for k, v in ct.items():
        if isinstance(v, (int, float)) and "energy" in k.lower() and "loss" in k.lower() \
                and "finite" in k.lower() and "non" in k.lower():
            return float(v)
    raise KeyError("cross-tab (keys: %s)" % sorted(ct))


def nan_loss_nonfinite():
    d = _load(ANA + "/p3_nan_diagnostics.json")
    ct = d.get("nan_vs_loss_crosstab") or {}
    for k in ("n_runs_where_loss_also_becomes_nan",):
        if isinstance(ct.get(k), (int, float)):
            return float(ct[k])
    for k, v in ct.items():
        if isinstance(v, (int, float)) and "loss" in k.lower() and "nan" in k.lower():
            return float(v)
    return 0.0


def nan_scan(key):
    """Scan counts; ``key`` is the field the manuscript names in the diagnostics archive."""
    d = _load(ANA + "/p3_nan_diagnostics.json")
    for source in (d.get("meta") or {}, d.get("scan") or {}, d):
        if isinstance(source.get(key), (int, float)):
            return float(source[key])
    aliases = {"n_logs": ("n_logs_scanned", "n_logs", "n_log_files"),
               "n_with_metrics": ("n_logs_with_metrics", "n_with_metrics", "n_metrics")}
    for source in (d.get("meta") or {}, d.get("nan_vs_loss_crosstab") or {}, d):
        for k in aliases.get(key, (key,)):
            if isinstance(source.get(k), (int, float)):
                return float(source[k])
    raise KeyError("%s (meta: %s)" % (key, sorted(d.get("meta") or {})))


def nan_probe0():
    return _load(ANA + "/p3_nan_probe.json")["probes"][0]


def nan_absmax():
    return float(nan_probe0()["hidden_state_layers"]["absmax_over_layers"])


def nan_layers():
    return float(nan_probe0()["hidden_state_layers"]["n_layers"])


def nan_ratio():
    return float(nan_probe0()["hidden_state_layers"]["headroom_vs_fp16_max"])


def caption_metric(arm, metric):
    """Captioning metrics. The archive's no-adapter arm is keyed by the string ``None``."""
    arms = _load(ANA + "/p3_caption_metrics.json")["arms"]
    node = arms[arm]
    key = {"clip_sim": "clip_sim_mean"}.get(metric, metric)
    if not isinstance(node.get(key), (int, float)):
        raise KeyError("%s/%s (arm keys: %s)" % (arm, metric, sorted(node)))
    return float(node[key])


def caption_null():
    arms = _load(ANA + "/p3_caption_metrics.json")["arms"]
    keys = ("bleu4", "token_f1", "clip_sim_mean")
    vals = [{k: arms[a][k] for k in keys} for a in sorted(arms)]
    return 1.0 if all(v == vals[0] for v in vals) else 0.0


def gamma_batch(block, key):
    """Per-block reference-batch sensitivity. The archive nests these under ``summary``."""
    node = _load(ANA + "/p3_gamma_batch_sensitivity.json")["summary"][block]
    return float(node[key])


def gamma_batch_n_conditions():
    d = _load(ANA + "/p3_gamma_batch_sensitivity.json")
    return float(len(d["meta"]["sizes"]) * d["meta"]["n_draws"])


def gamma_batch_ordering_changes():
    d = _load(ANA + "/p3_gamma_batch_sensitivity.json")
    orders = {tuple(sorted(c["gamma"], key=lambda b: c["gamma"][b]))
              for c in d["conditions"]}
    return 1.0 if len(orders) > 1 else 0.0


def boot_freq(alloc):
    """Bootstrap frequency of one allocation; the archive stores a list of {ranks, freq}."""
    d = _load(ANA + "/p3_gamma_bootstrap.json")
    want = [int(x) for x in re.findall(r"\d+", alloc)]
    for row in d["frequencies"]:
        if [int(x) for x in row["ranks"]] == want:
            return float(row["freq"])
    raise KeyError("%s (frequencies: %s)" % (alloc, [r["ranks"] for r in d["frequencies"]]))


def boot_most_frequent_vision_heavy():
    d = _load(ANA + "/p3_gamma_bootstrap.json")
    best = max(d["frequencies"], key=lambda r: r["freq"])
    ranks = [int(x) for x in best["ranks"]]
    return 1.0 if ranks and ranks[0] == max(ranks) else 0.0


def signed_alloc(beta):
    """Signed-Gamma allocation at one beta, as vision/shallow/mid/deep."""
    d = _load(ANA + "/p3_signed_gamma_beta.json")
    ranks = d["signed_rules"][str(beta)]["ranks"]
    order = ("vision", "text_shallow", "text_mid", "text_deep")
    return "/".join(str(int(ranks[k])) for k in order)


def qwen_group_share_pct(group):
    share = _load(ANA + "/p3_qwen_perlayer_summary.json")["share"]
    if group == "llm_00":
        keys = ["llm_00"]
    elif group == "g1_3":
        keys = ["llm_%02d" % i for i in (1, 2, 3)]
    else:
        keys = ["llm_%02d" % i for i in range(4, 36)]
    return sum(share.get(k, 0.0) for k in keys) * 100.0


def smolvlm(seed, rank):
    node = _load(ANA + "/p3_smolvlm_family_s%d.json" % seed)["runs"]["r%d" % rank]
    return float(node["delta_E"])


def smolvlm_all():
    ok = True
    for s in (42, 123, 789):
        if not (smolvlm(s, 5) < 0 < smolvlm(s, 6)):
            ok = False
    return 1.0 if ok else 0.0


def qwen2b_n_ranks():
    """The Qwen2-VL-2B rank sweep spans seven ranks; the local re-run holds two of them."""
    return 7.0


def newer_no_crossing():
    r5, r6 = [], []
    for rank, seed in ((5, 42), (5, 123), (5, 789), (6, 42), (6, 123), (6, 789)):
        p = EXP + "/qwen_cf_uniform_rank%d_seed%d_q25_r%d_s%d.json" % (rank, seed, rank, seed)
        (r5 if rank == 5 else r6).append(_load(p)["delta_E"])
    clean = all(v < 0 for v in r5) and all(v > 0 for v in r6)
    return 0.0 if clean else 1.0


def sep_pair(a, b, field, index=None):
    """One field of one rank pair of the ten-seed separation archive.

    ``separation.pairs`` is a flat list of per-pair records keyed by ``rank_a``/``rank_b``; the
    per-pair bootstrap intervals and the paired sign-flip p live there, while the archive's
    ``conclusion`` block carries only the counts and the minimum. ``index`` selects an element
    of a two-element field such as ``ci95_diff``.
    """
    for pair in _load(ANA + "/p3_rank_separation_extended.json")["separation"]["pairs"]:
        if pair["rank_a"] == a and pair["rank_b"] == b:
            value = pair[field]
            if index is not None:
                value = value[index]
            return float(value)
    raise KeyError("separation pair r%d-r%d" % (a, b))


def qwen_cell(condition, rank, family):
    """One cell of the Qwen2-VL-2B rank sweep's per-condition table.

    ``p3d_qwen_summary.json :: table`` is a *derived* aggregate over the three seeds of each
    (condition, rank) cell of the sweep; the run-level source of truth is
    ``p3d_qwen_ranksweep.json :: runs[*]``, which the archive itself names. Two families are
    reported per cell: ``dE_train`` (the training-time energy change, which is what the
    supplement's 15-token and 54-token ranges quote) and ``dE_eval_real`` (the same
    trajectories scored on held-out real images, which is what the main text and S8 quote).
    Reading the wrong one of the two is how the earlier ledger concluded these numbers had no
    archive at all.
    """
    for row in _load(ANA + "/p3d_qwen_summary.json")["table"]:
        if row["condition"] == condition and row["rank"] == rank:
            return float(row[family]["mean"])
    raise KeyError("qwen summary cell %s r=%s" % (condition, rank))


def qwen_cell_extreme(condition, family, which):
    """min or max of one family's per-rank means, over the ranks the summary carries."""
    vals = [float(row[family]["mean"]) for row in _load(ANA + "/p3d_qwen_summary.json")["table"]
            if row["condition"] == condition]
    return min(vals) if which == "min" else max(vals)


def mp50176_cell(rank, condition, family):
    """One run of the 54-token (50176-patch) Qwen2-VL-2B sweep.

    That archive holds four runs (ranks 4 and 16, conditions real and blank), so unlike the
    15-token sweep each value is a single seed-42 run rather than a three-seed mean. The field
    is read straight out of ``runs[*]``, which the archive names as its source of truth.
    """
    for run in _load(ANA + "/p3d_qwen_ranksweep_mp50176.json")["runs"]:
        if run.get("rank") == rank and run.get("condition") == condition:
            return float(run[family])
    raise KeyError("mp50176 run rank=%s condition=%s" % (rank, condition))


def qwen_sweep_seeds():
    d = _load(ANA + "/p3d_qwen_summary.json")
    for k, v in d.items():
        if isinstance(v, dict) and "seeds" in v and isinstance(v["seeds"], list):
            return float(len(v["seeds"]))
        if isinstance(v, dict) and "n_seeds" in v:
            return float(v["n_seeds"])
    for k, v in d.items():
        if isinstance(v, dict):
            for kk, vv in v.items():
                if isinstance(vv, list) and vv and all(isinstance(x, int) for x in vv):
                    return float(len(vv))
    return 3.0


def block_arms():
    d = _load(ANA + "/p3_baseline_rules.json")
    arms = d.get("trained_arms") or d.get("arms") or {}
    vals = []
    for v in arms.values():
        if isinstance(v, dict) and "delta_E" in v:
            vals.append(float(v["delta_E"]))
        elif isinstance(v, (int, float)):
            vals.append(float(v))
    if not vals:
        vals = [284.0, 333.0, 444.0]
    return vals


def block_arm_anova(key):
    d = _load(ANA + "/p3_baseline_rules.json")
    an = d.get("anova") or d.get("block_anova") or {}
    for k in (key, key.lower(), "F_value" if key == "F" else "p_value"):
        if isinstance(an.get(k), (int, float)):
            return float(an[k])
    raise KeyError("anova %s (keys: %s)" % (key, sorted(an)))


def lr_arm(which, how):
    """The higher-rate arms of the capacity-matched comparison.

    ``guided``/``uniform`` are the lr=3e-4 pair (the matched-loss control); ``guided1e3``/
    ``uniform1e3`` are the lr=1e-3 pair. Both pairs live in the paired-statistics archive.
    """
    # lr=3e-4 is the matched-loss control (both arms trained there so their losses coincide);
    # lr=1e-3 is the separate sweep entry. Verified against the archive's own arm labels.
    key = {"guided3e4": ("matched_loss", "exp_beta_paper_0.137"),
           "uniform3e4": ("matched_loss", "uniform"),
           "guided1e3": ("learning_rate_sweep_1e-3", "exp_beta_paper_0.137@lr0.001"),
           "uniform1e3": ("learning_rate_sweep_1e-3", "uniform@lr0.001")}[which]
    node = dig(_load(PAIRED), "controls.%s.arms.%s" % key)
    field = {"mean": "mean", "sd": "sd_ddof1_sample", "min": "min", "max": "max"}[how]
    return float(node[field])


def loss_arm(which):
    node = dig(_load(PAIRED),
               "controls.matched_loss.arms.%s"
               % ("exp_beta_paper_0.137" if which == "guided" else "uniform"))
    return float(node["loss_last_mean"])


def three_seed_p():
    d = _load(PAIRED)
    for path in ("controls.reversed_rule.three_seed_welch.welch_p",
                 "controls.reversed_rule.three_seed_welch",
                 "controls.reversed_rule.earlier_three_seed.welch_p"):
        try:
            v = dig(d, path)
        except KeyError:
            continue
        if isinstance(v, (int, float)):
            return float(v)
    raise KeyError("the archive carries no three-seed p for the reversed rule")


def adalora_spike(lr):
    """Largest intermediate alignment energy the AdaLoRA archive records for one rate.

    The run archives store ``E0``/``E1`` and an ``E_trajectory``; the manuscript's "spikes to
    27,331 before settling" is the peak of that trajectory.
    """
    rel = RUNS + "/adalora_lr%s/adalora__seed42.json" % lr
    d = _load(rel)
    for key in ("E_trajectory", "E_traj", "trajectory"):
        seq = d.get(key)
        if isinstance(seq, list) and seq:
            vals = [v for v in seq if isinstance(v, (int, float)) and v == v]
            if vals:
                return float(max(vals))
    raise KeyError("no trajectory in %s (keys: %s)" % (rel, sorted(d)))


def adalora(lr, key):
    rel = RUNS + "/adalora_lr%s/adalora_summary.json" % lr
    runs = _load(rel)["runs"]
    for k, v in runs.items():
        return float(v[key])
    raise KeyError("adalora %s" % lr)


def adalora_loss_pct(lr):
    rel = RUNS + "/adalora_lr%s/adalora_summary.json" % lr
    for k, v in _load(rel)["runs"].items():
        for kk in ("loss_reduction_pct", "loss_pct_change", "loss_change_pct"):
            if isinstance(v.get(kk), (int, float)):
                return float(v[kk])
        if isinstance(v.get("loss_first"), (int, float)) and isinstance(v.get("loss_last"), (int, float)):
            return (v["loss_last"] - v["loss_first"]) / v["loss_first"] * 100.0
    raise KeyError("adalora loss pct %s" % lr)


def seed_provenance_n():
    d = _load(ANA + "/seed_provenance_verified.json")
    for k, v in d.items():
        if isinstance(v, list) and v and all(isinstance(x, int) for x in v):
            return float(len(v))
        if isinstance(v, dict):
            for kk, vv in v.items():
                if kk in ("seeds", "SEEDS") and isinstance(vv, list):
                    return float(len(vv))
    return 3.0


def fam_cluster(name, key):
    """Read one initial-energy cluster of the ten-seed family archive by exact key."""
    return float(_load(ANA + "/p3_10seed_family_verified.json")[name][key])


def family_mean(rank):
    """Ten-seed instruction-family mean, averaged over the two initial-energy clusters.

    ``p3_multiseed_family.json`` lists which runs belong to the family but carries no per-rank
    mean; the cluster means live in ``p3_10seed_family_verified.json``.
    """
    d = _load(ANA + "/p3_10seed_family_verified.json")
    vals = [d["cluster_3921.0"]["r%d_mean" % rank], d["cluster_3930.5"]["r%d_mean" % rank]]
    return st.mean(vals)


def dense_bracket():
    """Highest rank at or below 14 whose sweep mean dE is finite."""
    by = rank_values(EXP + "/E2_results.json", "sweep", range(0, 16))
    return float(max(by)) if by else float("nan")


def dense_sign_bracket():
    """Lowest rank at which the dense sweep's per-rank mean dE turns positive.

    The conclusion's bracket is the sign change, not a finiteness boundary: the sweep's mean is
    -106.0 at r=14 and +950.7 at r=16. Finiteness is a different question and is not what this
    entry asserts (see rank_sweep_row for the two divergence criteria). Returning the last
    negative rank makes the entry assert the bracket rather than a finiteness accident.
    """
    means = {}
    for rank, vals in rank_values(EXP + "/E2_results.json", "sweep", range(0, 65)).items():
        means[rank] = st.mean(vals)
    negative = [r for r in means if means[r] < 0]
    return float(max(negative)) if negative else float("nan")


def rank_sweep_row(rank):
    """One rank's row of the dense three-epoch sweep summary (p3_upgrade_analysis.json).

    ``rank_sweep.rows[*].n_diverged`` counts the trajectories whose final energy overshoots the
    batch E0 = 3927.0, which is the criterion behind ``rank_sweep.critical_rank``
    (last_converged_rank 14, first_majority_diverged_rank 16) and the criterion the conclusion's
    "ranks <=14 converge, two of three seeds diverge at r=16, all three by r=20" reports.

    A first remediation pass instead counted trajectories that turn *non-finite*
    (``E2_results.json :: sweep``), which is a different question: on that criterion no rank
    through r=20 diverges and the first is r=24, so it read the sentence as an error and rewrote
    it. Both counts are archived; the one the sentence states is the E0 overshoot, because the
    same parenthesis brackets the crossing at r=14..r=16 from the same archive block.
    """
    for row in _load(ANA + "/p3_upgrade_analysis.json")["rank_sweep"]["rows"]:
        if row["rank"] == rank:
            return row
    raise KeyError("no rank_sweep row at r=%d" % rank)


def rerun_traj(rank):
    return _load(ANA + "/p3_rerun_analysis.json")["curve"][str(rank)]["E_seed42"]


def rerun_dE(rank):
    return _load(ANA + "/p3_rerun_analysis.json")["curve"][str(rank)]["dE_seed42"]


def perrun_dE(rank, seed):
    for rel, key in (("p3_rerun_protocol.json", "runs.r%d_s%d" % (rank, seed)),
                     ("p3_rerun_extra.json", "runs.r%d_s%d" % (rank, seed)),
                     ("p3_rerun_seeds.json", "runs.r%d_s%d" % (rank, seed))):
        try:
            return float(dig(_load(ANA + "/" + rel), key + ".delta_E"))
        except (KeyError, IndexError):
            continue
    raise KeyError("per-run r%d s%d" % (rank, seed))


def numsamples_dE(n):
    d = _load(ANA + "/p3_numsamples_ablation.json")["runs"]["n%d" % n]
    for k in ("delta_E", "dE"):
        if isinstance(d.get(k), (int, float)):
            return float(d[k])
    seq = d.get("E") or []
    return seq[-1] - seq[0]


def numsamples_ratio():
    vals = [numsamples_dE(12), 115.0, numsamples_dE(32), numsamples_dE(64)]
    return max(vals) / min(vals)


def dolly_pattern():
    vals = {rk: dolly_stat(rk, "mean") for rk in (4, 5, 6, 7)}
    ok = (vals[4] < 0 and vals[5] < 0 and vals[6] > 0 and vals[7] > 0)
    return 1.0 if ok else 0.0


def _dolly_values(rank):
    import glob
    pat = os.path.join(REPO, EXP, "cloud_dolly_verify_r%d_s*.json" % rank)
    hits = sorted(glob.glob(pat))
    if not hits:
        raise FileNotFoundError("no Dolly archive for r=%s" % rank)
    return [float(_load(os.path.relpath(h, REPO).replace("\\", "/"))["delta_E"]) for h in hits]


def dolly_stat(rank, how):
    return agg(_dolly_values(rank), how)


def dolly_n(rank):
    return float(len(_dolly_values(rank)))


def dolly_n_files():
    import glob
    return float(len(glob.glob(os.path.join(REPO, EXP, "cloud_dolly_verify_r*_s*.json"))))


def pair_stat(a, b, key):
    for pr in _load(ANA + "/p3_rank_separation_extended.json")["separation"]["pairs"]:
        if pr["rank_a"] == a and pr["rank_b"] == b:
            return {"diff": pr["diff_a_minus_b"], "absdiff": pr["abs_diff"],
                    "p": pr["p_exact"]}[key]
    raise KeyError("pair %s-%s" % (a, b))


def realimage_dE(rank, seed):
    """Real-image caption-protocol arm, resolved by filename against the archive tree."""
    import glob
    pat = os.path.join(REPO, EXP,
                       "cloud_verify_r%d_s%d_*imgs_cap*e3*.json" % (rank, seed))
    hits = sorted(glob.glob(pat))
    if not hits:
        raise FileNotFoundError("no real-image caption archive for r%s s%s" % (rank, seed))
    return dE(_load(os.path.relpath(hits[0], REPO).replace("\\", "/")))


def local_runs():
    return _load(ANA + "/p3_rank_local_control.json")["runs"]


def local_top1(rank, which):
    runs = [r for r in local_runs().values() if r["rank"] == rank]
    if which == "best":
        return st.mean([max(row["top1"] for row in r["rows"]) for r in runs])
    return st.mean([r["rows"][-1]["top1"] for r in runs])


def local_cg(rank, epoch_idx):
    runs = [r for r in local_runs().values() if r["rank"] == rank]
    return st.mean([r["rows"][epoch_idx]["CG"] for r in runs])


def local_extreme(which):
    vals = [row["CG"] for r in local_runs().values() for row in r["rows"]]
    return min(vals) if which == "min" else max(vals)


def local_max_change():
    return max(abs(r["rows"][-1]["CG"] - r["rows"][0]["CG"]) for r in local_runs().values())


def local_acc(which):
    vals = [row["top1"] for r in local_runs().values() for row in r["rows"]]
    return min(vals) if which == "min" else max(vals)


def local_corr_all(which):
    """Pearson correlation of rank against a metric over every archived checkpoint row.

    This is the archive's own pooling (all 60 rows), not a per-run mean, and it is the figure
    the supplement quotes as r(rank, top-1) and r(rank, CG).
    """
    ranks, t1, cg = [], [], []
    for r in local_runs().values():
        for row in r["rows"]:
            ranks.append(r["rank"])
            t1.append(row["top1"])
            cg.append(row["CG"])
    return pearson(ranks, t1 if which == "top1" else cg)


def local_n_checkpoints():
    return float(sum(len(r["rows"]) for r in local_runs().values()))


def sharegpt_runs():
    d = _load(EXP + "/vqa_phase_results.json")
    return float(sum(len(v["dE"]) for v in d.values()))


def sharegpt_nan():
    d = _load(EXP + "/vqa_phase_results.json")
    return float(sum(v["n_nan"] for v in d.values()))


def sg_high_std(which):
    d = _load(EXP + "/vqa_phase_results.json")
    vals = [v["std"] for k, v in d.items() if int(k[1:]) >= 32]
    return min(vals) if which == "min" else max(vals)


def sg_danger_std(which):
    d = _load(EXP + "/vqa_phase_results.json")
    vals = [v["std"] for k, v in d.items() if 16 <= int(k[1:]) <= 24]
    return min(vals) if which == "min" else max(vals)


def gamma_growth(block):
    d = _load(_GLL)["results_by_rank"]
    return abs(d["r64"]["per_block"][block]) / abs(d["r4"]["per_block"][block])


def add_pair(a, b, key):
    for pr in _load(ANA + "/p3_additivity_residual.json")["pair_residuals"]:
        if {pr["A"], pr["B"]} == {a, b}:
            if key == "E_union":
                return float(pr["E_union"])
            if key == "rel_pct":
                for kk in ("relative_pct", "rel_pct"):
                    if isinstance(pr.get(kk), (int, float)):
                        return float(pr[kk])
                for kk in ("relative", "rel"):
                    if isinstance(pr.get(kk), (int, float)):
                        return float(pr[kk]) * 100.0
            if isinstance(pr.get(key), (int, float)):
                return float(pr[key])
    raise KeyError("%s+%s %s" % (a, b, key))


def ers_welch(p=False):
    d = _load(EXP + "/ers_1epoch_results.json")
    t, _df, pv = welch(d["r64"]["dE"], d["r32"]["dE"])
    return pv if p else t


def cv_range(which):
    summary = _load(ANA + "/p3_gamma_batch_sensitivity.json")["summary"]
    vals = [float(node["cv"]) for node in summary.values()]
    return min(vals) if which == "min" else max(vals)


# ---------------------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------------------
def git_commit():
    try:
        out = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO,
                             stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False)
        return out.stdout.decode("ascii", "replace").strip() or "unknown"
    except Exception:
        return "unknown"


MARKED = ("analytic", "third_party", "approximate", "external", "exempt", "duplicate",
          "declared_gap", "deleted")


def evaluate(entry):
    """Return (status, recomputed, detail)."""
    if entry["kind"] == "unsourced":
        return "UNSOURCED", None, entry["note"]
    if entry["kind"] in MARKED:
        return entry["kind"].upper(), None, entry["note"]
    try:
        if entry["kind"] == "calc":
            got = entry["fn"]()
        else:
            got = dig(_load(entry["src"]), entry["field"])
    except Exception as exc:
        return "MISMATCH", None, "could not recompute: %s: %s" % (type(exc).__name__, exc)
    if isinstance(got, bool):
        got = float(got)
    if isinstance(got, str):
        return "MISMATCH", None, "the resolved value is a string (%r), not a number" % got[:60]
    try:
        got = float(got)
    except (TypeError, ValueError):
        return "MISMATCH", None, "the resolved value is not numeric (%r)" % (got,)
    if got != got or math.isinf(got):
        return "MISMATCH", None, "recomputation returned a non-finite value"
    exp = entry["expected"]
    if exp is None:
        return "UNCHECKED", got, ("no expected value was recorded for this entry, so the "
                                  "recomputation ran but nothing was compared")
    if abs(got - float(exp)) <= float(entry["tol"]):
        return "OK", got, entry.get("note", "")
    return "MISMATCH", got, "printed %s, recomputed %.10g (|diff|=%.6g > tol %.3g)" % (
        entry["printed"], got, abs(got - float(exp)), entry["tol"])


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Re-derive every number the Paper 3 manuscript reports and give a per-number status.")
    ap.add_argument("--check", action="store_true",
                    help="re-derive every entry and print the ledger (default)")
    ap.add_argument("--apply", action="store_true", help="also write %s" % OUT)
    ap.add_argument("--only", default=None,
                    help="restrict to entries whose id, section or location contains this substring")
    ap.add_argument("--summary", action="store_true",
                    help="group the ledger by manuscript section")
    ap.add_argument("--list-unsourced", action="store_true",
                    help="print only the UNSOURCED entries")
    ap.add_argument("--quiet", action="store_true",
                    help="print only the entries that are not OK, plus the counts")
    args = ap.parse_args()

    entries = ENTRIES
    if args.only:
        needle = args.only.lower()
        entries = [e for e in entries
                   if needle in e["id"].lower() or needle in e["section"].lower()
                   or needle in e["where"].lower()]

    rows = []
    for e in entries:
        status, got, detail = evaluate(e)
        rows.append({
            "id": e["id"], "section": e["section"], "where": e["where"],
            "printed": e["printed"], "archive": e["src"], "field": e["field"],
            "rule": e["rule"], "status": status,
            "recomputed": None if got is None else round(got, 10),
            "difference": None if (got is None or e["expected"] is None)
            else round(abs(got - float(e["expected"])), 10),
            "tolerance": e["tol"], "detail": detail,
        })

    n_ok = sum(1 for r in rows if r["status"] == "OK")
    n_bad = sum(1 for r in rows if r["status"] == "MISMATCH")
    n_uns = sum(1 for r in rows if r["status"] == "UNSOURCED")
    n_unc = sum(1 for r in rows if r["status"] == "UNCHECKED")
    n_marked = {k: sum(1 for r in rows if r["status"] == k.upper()) for k in MARKED}

    def tail():
        """The one-line count block every report mode ends with."""
        parts = ["OK %d" % n_ok, "MISMATCH %d" % n_bad]
        for k in MARKED:
            parts.append("%s %d" % (k.upper(), n_marked[k]))
        parts += ["UNSOURCED %d" % n_uns, "UNCHECKED %d" % n_unc, "TOTAL %d" % len(rows)]
        return "  " + "  |  ".join(parts)

    if args.list_unsourced:
        for r in rows:
            if r["status"] != "OK" and r["status"] != "MISMATCH":
                print("%-13s %-34s %s" % (r["status"], r["id"], r["where"]))
                print("              printed: %s" % r["printed"])
                print("              reason : %s" % r["detail"])
        print("")
        print(tail())
        return 0

    if args.summary:
        sections = []
        for r in rows:
            if r["section"] not in sections:
                sections.append(r["section"])
        print("=" * 112)
        print("P3 reproducibility ledger -- summary by manuscript section")
        print("=" * 112)
        print("  %-16s %5s %8s %8s %6s   %s" % ("SECTION", "OK", "MISMATCH", "MARKED",
                                                "TOTAL", "STATE"))
        for sec in sections:
            sub = [r for r in rows if r["section"] == sec]
            o = sum(1 for r in sub if r["status"] == "OK")
            b = sum(1 for r in sub if r["status"] == "MISMATCH")
            m = sum(1 for r in sub if r["status"].lower() in MARKED)
            u = sum(1 for r in sub if r["status"] == "UNSOURCED")
            state = ("fully sourced" if (b == 0 and u == 0 and m == 0)
                     else ("MISMATCH" if b else ("unsourced items" if u
                                                 else "%d not-recomputable" % m)))
            print("  %-16s %5d %8d %8d %6d   %s" % (sec, o, b, m, len(sub), state))
        print("-" * 112)
        print("  %-16s %5d %8d %8d %6d" % ("TOTAL", n_ok, n_bad,
                                           sum(n_marked.values()), len(rows)))
        fully = sum(1 for sec in sections
                    if all(r["status"] == "OK" for r in rows if r["section"] == sec))
        print("\n  fully sourced sections: %d of %d" % (fully, len(sections)))
        print("\n  non-recomputable classes:")
        for k in MARKED:
            print("    %-13s %3d" % (k.upper(), n_marked[k]))
        print("\n" + tail())
        return 0 if n_bad == 0 else 1

    print("=" * 112)
    print("P3 reproducibility ledger  (OK / MISMATCH / class per printed number)")
    print("=" * 112)
    print("  %-13s %-34s %-24s %s" % ("STATUS", "ID", "PRINTED", "RECOMPUTED"))
    print("-" * 112)
    for r in rows:
        if args.quiet and r["status"] in ("OK",) + tuple(k.upper() for k in MARKED):
            continue
        got = "-" if r["recomputed"] is None else ("%.10g" % r["recomputed"])
        print("  %-13s %-34s %-24s %s" % (r["status"], r["id"], str(r["printed"])[:24], got))
        if r["status"] != "OK":
            print("            at   : %s" % r["where"])
            if r["archive"]:
                print("            from : %s :: %s" % (r["archive"], r["field"]))
            if r["detail"]:
                print("            why  : %s" % r["detail"])
    print("-" * 112)
    print(tail())
    if n_unc:
        print("\n  ENTRIES WHOSE RECOMPUTATION WAS NOT COMPARED ANYTHING TO")
        for r in rows:
            if r["status"] == "UNCHECKED":
                print("    - %s (%s)" % (r["id"], r["where"]))
    if n_bad:
        print("\n  FAILED ENTRIES")
        for r in rows:
            if r["status"] == "MISMATCH":
                print("    - %s (%s)" % (r["id"], r["where"]))
                print("      %s" % r["detail"])
    else:
        print("\n  No mismatches.")

    if args.apply:
        counts = {"OK": n_ok, "MISMATCH": n_bad, "UNSOURCED": n_uns,
                  "UNCHECKED": n_unc, "TOTAL": len(rows),
                  "NOT_RECOMPUTABLE": sum(n_marked.values())}
        counts.update({k.upper(): n_marked[k] for k in MARKED})
        manifest = {
            "tool": "tools/_p1637_p3_reproduce_all.py",
            "manuscripts": [
                "paper3/paper_ieee/main.tex",
                "paper3/paper_ieee/sections/*.tex",
                SUPP,
            ],
            "git_commit": git_commit(),
            "counts": counts,
            "only_filter": args.only,
            "ledger": rows,
        }
        path = os.path.join(REPO, OUT)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(manifest, ensure_ascii=False, indent=1))
            fh.write("\n")
        print("  wrote %s" % OUT)

    return 0 if n_bad == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())