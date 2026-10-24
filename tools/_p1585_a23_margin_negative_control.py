# -*- coding: utf-8 -*-
r"""A23 margin-quality certificate: negative-control evidence summary.

The margin-mass certificate M(eps) = mean(1[margin <= 2 eps]) is informative where it was validated (A1, ImageNet-5k,
CLIP ViT-B/32: M(0.01) correlates with top-1 at Pearson -0.996 across 17 configurations) and saturates on the A23
control domains, where every archived configuration has M(0.05) = M(0.1) = 1.0 and the archived correlation is NaN.

This script does not re-run any model. It reads the archived results, re-verifies every number that the manuscript
paragraph would cite against the exact JSON field that carries it, records the manuscript/notes line numbers, and
writes one evidence summary with an explicit conclusion. Every existing archive is opened read-only.

Sources (read-only):
  outputs/analysis/a23_certificate_control.json    generic CLIP ViT-B/32 control   (tools/_p1344_...)
  outputs/analysis/a23_certificate_adapted.json    BioCLIP / OceanCLIP, 67 classes  (tools/_p1352_...)
  outputs/analysis/a23_tau_control.json            tau counterpart, same surgery family (tools/_p1370_...)
  outputs/analysis/a1_margin_mass.json             informative reference, ImageNet-5k (tools/_p1299_...)
  outputs/analysis/a1_margin_templates.json        M(0.01) across 10 prompt templates
  outputs/ocean_subset.json                        class set behind the 67-class marine subset

Output: outputs/analysis/a23_margin_negative_control.json

    python tools/_p1585_a23_margin_negative_control.py --apply
"""
from __future__ import annotations

import argparse
import io
import json
import math
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "outputs", "analysis", "a23_margin_negative_control.json")

CONTROL = "outputs/analysis/a23_certificate_control.json"
ADAPTED = "outputs/analysis/a23_certificate_adapted.json"
TAUCTL = "outputs/analysis/a23_tau_control.json"
A1MASS = "outputs/analysis/a1_margin_mass.json"
A1TMPL = "outputs/analysis/a1_margin_templates.json"
SUBSET = "outputs/ocean_subset.json"

MANUSCRIPT_WORKING = "paper_a2/ext_partII_domains.tex"
MANUSCRIPT_MAIN = "paper_a2/main_ieee.tex"
FROZEN_TEX = "SUBMISSION/A23_JOE/current/ext_partII_domains.tex"
FROZEN_MAIN = "SUBMISSION/A23_JOE/current/main_ieee.tex"
NOTES = [
    "HANDOFF.md",
    "docs/UPGRADE_PLAN_P3_A23_COMMENTARY_2026-10-19.md",
    "docs/A23_REVIEWER_OBJECTIONS.md",
    "文件地图.md",
]

IMAGE_EXT = (".jpg", ".jpeg", ".png")


def load(rel):
    with io.open(os.path.join(REPO, rel), encoding="utf-8") as fh:
        return json.load(fh)


def lines_of(rel, needles):
    """Line numbers (1-based) of literal needles in a text file, for citable quotes."""
    path = os.path.join(REPO, rel)
    if not os.path.exists(path):
        return {n: None for n in needles}
    with io.open(path, encoding="utf-8", errors="replace") as fh:
        text = fh.read().splitlines()
    out = {}
    for n in needles:
        out[n] = [i + 1 for i, ln in enumerate(text) if n in ln]
    return out


def pearson(xs, ys):
    """Pearson r, or None when either input is constant (the archived value is then NaN)."""
    n = len(xs)
    if n < 2:
        return None
    mx, my = sum(xs) / n, sum(ys) / n
    sxy = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
    sxx = sum((a - mx) ** 2 for a in xs)
    syy = sum((b - my) ** 2 for b in ys)
    if sxx == 0 or syy == 0:
        return None
    return sxy / math.sqrt(sxx * syy)


def stats(values):
    return {
        "n": len(values),
        "min": min(values),
        "max": max(values),
        "n_unique": len(set(values)),
        "constant": len(set(values)) == 1,
        "value_if_constant": values[0] if len(set(values)) == 1 else None,
    }


def infer_n(percentages, limit=4000):
    """Recover the image count behind 'percent' fields: percentages are 100 * correct / n."""
    best = []
    for n in range(2, limit + 1):
        vals = [p * n / 100.0 for p in percentages]
        if max(abs(v - round(v)) for v in vals) < 1e-6:
            best.append(n)
    return best[:4]


def count_images(rel_root):
    """Recompute the loader's glob: image files directly inside each class directory."""
    root = os.path.join(REPO, rel_root)
    if not os.path.isdir(root):
        return {"path": rel_root, "exists": False}
    per_class = {}
    for cls in sorted(d for d in os.listdir(root) if os.path.isdir(os.path.join(root, d))):
        files = [f for f in os.listdir(os.path.join(root, cls)) if f.lower().endswith(IMAGE_EXT)]
        per_class[cls] = len(files)
    return {"path": rel_root, "exists": True, "n_classes": len(per_class),
            "n_images_direct": sum(per_class.values()), "per_class": per_class}


def control_block():
    d = load(CONTROL)
    block = {"archive": CONTROL, "script": "tools/_p1344_a23_certificate_control.py",
             "model_field": d["model"], "protocol": d["protocol"], "eps_grid": d["eps"], "domains": {}}
    for name, rows in d["domains"].items():
        lam = [r["lambda"] for r in rows]
        top1 = [r["top1"] for r in rows]
        frozen = [r for r in rows if r["lambda"] == 0.0][0]
        entry = {
            "n_configurations": len(rows),
            "lambdas": lam,
            "top1_percent_at_lambda_0_frozen": frozen["top1"],
            "top1_percent_range_across_lambdas": [min(top1), max(top1)],
            "CG_at_lambda_0": frozen["CG"],
            "mass": {},
            "inferred_n_images_candidates": infer_n(top1),
        }
        for e in d["eps"]:
            key = "mass_%g" % e
            vals = [r[key] for r in rows]
            s = stats(vals)
            s["values"] = vals
            entry["mass"][key] = s
        block["domains"][name] = entry
    pooled = [r for rows in d["domains"].values() for r in rows]
    top = [r["top1"] for r in pooled]
    block["pooled"] = {
        "n_configurations": len(pooled),
        "top1_percent_range": [min(top), max(top)],
        "mass_0.05_all_equal_1": all(r["mass_0.05"] == 1.0 for r in pooled),
        "mass_0.1_all_equal_1": all(r["mass_0.1"] == 1.0 for r in pooled),
        "mass_0.02_range": [min(r["mass_0.02"] for r in pooled), max(r["mass_0.02"] for r in pooled)],
    }
    block["correlation_archived"] = d["correlation"]
    block["correlation_recomputed"] = {
        "pearson_top1_vs_mass_0.02": pearson(top, [r["mass_0.02"] for r in pooled]),
        "pearson_top1_vs_mass_0.05": pearson(top, [r["mass_0.05"] for r in pooled]),
        "pearson_top1_vs_mass_0.1": pearson(top, [r["mass_0.1"] for r in pooled]),
        "pearson_top1_vs_CG": pearson(top, [r["CG"] for r in pooled]),
    }
    block["threshold_transfer_archived"] = d["threshold_transfer"]
    block["field_name_caveat"] = (
        "tools/_p1344_a23_certificate_control.py:123-125 fills the archive keys 'M(0.01)' and 'M(0.05)' from the same "
        "mass_0.05 column, so no M(0.01) value exists in this archive; both keys are NaN because mass_0.05 is "
        "identically 1.0 across all 14 configurations (zero variance)."
    )
    return block


def adapted_block():
    d = load(ADAPTED)
    block = {"archive": ADAPTED, "script": "tools/_p1352_a23_certificate_adapted.py",
             "protocol": d["protocol"], "n_images": d["n_images"], "n_classes": d["n_classes"],
             "eps_grid": d["eps"], "models": {}}
    for tag, m in d["models"].items():
        rows = [r for r in m["rows"] if isinstance(r["lambda"], (int, float))]
        top = [r["top1"] for r in rows]
        frozen = [r for r in rows if r["lambda"] == 0.0][0]
        entry = {
            "n_lambda_rows": len(rows),
            "top1_percent_at_lambda_0": frozen["top1"],
            "top1_percent_range": [min(top), max(top)],
            "mass_0.02": stats([r["mass_0.02"] for r in rows]),
            "mass_0.05": stats([r["mass_0.05"] for r in rows]),
            "mass_0.1": stats([r["mass_0.1"] for r in rows]),
            "r_M005_archived": m["r_M005"],
            "r_M005_recomputed": pearson(top, [r["mass_0.05"] for r in rows]),
            "r_CG_archived": m["r_CG"],
            "r_CG_recomputed": pearson(top, [r["CG"] for r in rows]),
        }
        block["models"][tag] = entry
    block["threshold_transfer_archived"] = d["threshold_transfer"]
    return block


def tau_block():
    d = load(TAUCTL)
    return {"archive": TAUCTL, "script": "tools/_p1370_a23_tau_control.py",
            "n_images": d["n_images"],
            "models": {tag: {"r_tau": m["r_tau"], "r_mass": m["r_mass"], "r_cg": m["r_cg"]}
                       for tag, m in d["models"].items()},
            "threshold_transfer_archived": d["threshold_transfer"]}


def a1_reference_block():
    d = load(A1MASS)
    rows = d["rows"]
    top = [r["top1"] for r in rows]
    frozen = [r for r in rows if r["family"] == "frozen"][0]
    block = {
        "archive": A1MASS, "script": "tools/_p1299_margin_mass.py",
        "benchmark": d["benchmark"], "n_images": d["n_images"], "model": d["model"],
        "n_configurations": len(rows),
        "definition": d["definition"],
        "frozen_row": {"family": frozen["family"], "top1": frozen["top1"], "CG": frozen["CG"],
                       "margin_mean": frozen["margin_mean"], "margin_median": frozen["margin_median"],
                       "mass_eps_0.01": frozen["mass_eps_0.01"], "mass_eps_0.02": frozen["mass_eps_0.02"],
                       "mass_eps_0.05": frozen["mass_eps_0.05"], "mass_eps_0.1": frozen["mass_eps_0.1"]},
        "mass_eps_0.01_range": [min(r["mass_eps_0.01"] for r in rows), max(r["mass_eps_0.01"] for r in rows)],
        "mass_eps_0.05_range": [min(r["mass_eps_0.05"] for r in rows), max(r["mass_eps_0.05"] for r in rows)],
        "mass_eps_0.1": stats([r["mass_eps_0.1"] for r in rows]),
        "mass_eps_0.2": stats([r["mass_eps_0.2"] for r in rows]),
        "mass_eps_0.5": stats([r["mass_eps_0.5"] for r in rows]),
        "correlation_with_top1_archived": d["correlation_with_top1"],
        "correlation_with_top1_recomputed": {
            "mass_eps_0.01": pearson(top, [r["mass_eps_0.01"] for r in rows]),
            "mass_eps_0.02": pearson(top, [r["mass_eps_0.02"] for r in rows]),
            "mass_eps_0.05": pearson(top, [r["mass_eps_0.05"] for r in rows]),
        },
    }
    tmpl = load(A1TMPL)
    per_model = {}
    for tag, m in tmpl["models"].items():
        vals = [r["mass_0.01"] for r in m["rows"]]
        per_model[tag] = {"n_templates": len(vals), "mass_0.01_range": [min(vals), max(vals)]}
    block["template_control"] = {"archive": A1TMPL, "eps": tmpl["eps"], "models": per_model}
    return block


def dataset_block():
    out = {
        "control_marine_optical": count_images("data/fathomnet8"),
        "control_acoustic_sonar": count_images(os.path.join("data", "NKSID", "NKSID")),
        "note": ("Both control datasets carry 7 class directories on disk although the directory name 'fathomnet8' and "
                 "the script docstring say 8 classes; the control archive stores no class count, so chance level is "
                 "1/7 = 14.29% under the loader's own class list (sorted subdirectories)."),
    }
    if os.path.exists(os.path.join(REPO, SUBSET)):
        sub = load(SUBSET)
        out["adapted_subset"] = {"archive": SUBSET, "n_classes_field": len(sub["classes"]) if "classes" in sub else None,
                                 "n_subset_idx_field": len(sub["subset_idx"]) if "subset_idx" in sub else None}
    return out


def manuscript_state():
    working = lines_of(MANUSCRIPT_WORKING, ["margin-mass variant", "The margin mass $M(\\varepsilon)$",
                                            "$M(0.01)=0.681$", "a23\\_certificate\\_control"])
    main_tex = lines_of(MANUSCRIPT_MAIN, ["\\input{ext_partII_domains}"])
    frozen = lines_of(FROZEN_TEX, ["margin", "certificate", "saturat"])
    frozen_main = lines_of(FROZEN_MAIN, ["margin-mass variant", "certificate"])
    notes = {rel: lines_of(rel, ["A23-P0-1", "饱和失效", "negative control", "M\\approx1",
                                 "升级为适配模型实验并写入正文", "写入正文", "Certificate control"]) for rel in NOTES}
    wpath = os.path.join(REPO, MANUSCRIPT_WORKING)
    working_stat = {"n_lines": None, "mtime": None}
    if os.path.exists(wpath):
        working_stat = {"n_lines": len(io.open(wpath, encoding="utf-8", errors="replace").read().splitlines()),
                        "mtime": __import__("datetime").datetime.fromtimestamp(
                            os.path.getmtime(wpath)).strftime("%Y-%m-%d %H:%M:%S")}
    return {
        "working_copy": {
            "file": MANUSCRIPT_WORKING,
            "n_lines_and_mtime": working_stat,
            "lines_with_certificate_text": working["margin-mass variant"] + working["The margin mass $M(\\varepsilon)$"],
            "lines_with_validated_reference_numbers": working["$M(0.01)=0.681$"],
            "lines_citing_control_archive": working["a23\\_certificate\\_control"],
            "included_from_main_at": {MANUSCRIPT_MAIN: main_tex["\\input{ext_partII_domains}"]},
            "position": "Results body (Part II of the domain-model matrix section), not an appendix",
            "introduced_by_commit": "93aa30d (2026-10-19 18:10, i.e. after the 2026-09-21 submission)",
            "note": ("The paragraph was rewritten on 2026-10-24 (workspace mtime above) with the corrected wording: "
                     "'margin-mass variant' is the pre-edit phrase from commit 93aa30d, 'The margin mass M(eps)' is the "
                     "current one."),
        },
        "frozen_submitted_26_0663": {
            "file": FROZEN_TEX,
            "lines_with_margin": frozen["margin"],
            "lines_with_certificate": frozen["certificate"],
            "lines_with_saturation": frozen["saturat"],
            "main_file": FROZEN_MAIN,
            "main_lines_with_certificate": frozen_main["certificate"],
            "verdict": "absent from the submitted manuscript (26-0663, submitted 2026-09-21)",
        },
        "notes_lines": notes,
    }


def saturation_survey():
    """Every archived arm that carries a margin-mass field, scanned for the saturation claim."""
    arms = []  # (archive, epsilon, value, label)

    def add(archive, eps, value, label):
        arms.append({"archive": archive, "eps": eps, "value": value, "label": label})

    ctl = load(CONTROL)
    for name, rows in ctl["domains"].items():
        for r in rows:
            for e in ctl["eps"]:
                add(CONTROL, e, r["mass_%g" % e], "%s|lambda=%s" % (name, r["lambda"]))
    for rel in (ADAPTED, TAUCTL, "outputs/analysis/a23_uatd_domain.json",
                "outputs/analysis/a23_watertank_domain.json"):
        if not os.path.exists(os.path.join(REPO, rel)):
            continue
        d = load(rel)
        eps = d.get("eps", [0.02, 0.05, 0.1])
        for tag, m in d.get("models", {}).items():
            for r in m.get("rows", []):
                for e in eps:
                    key = "mass_%g" % e
                    if key in r:
                        add(rel, e, r[key], "%s|lambda=%s" % (tag, r["lambda"]))
    for rel, keymap in ((A1MASS, {"mass_eps_0.01": 0.01, "mass_eps_0.02": 0.02, "mass_eps_0.05": 0.05,
                                  "mass_eps_0.1": 0.1, "mass_eps_0.2": 0.2, "mass_eps_0.5": 0.5}),
                        ("outputs/analysis/a1_retrieval_monitor.json",
                         {"mass_0.01": 0.01, "mass_0.05": 0.05})):
        if not os.path.exists(os.path.join(REPO, rel)):
            continue
        d = load(rel)
        rows = d["rows"] if "rows" in d else [r for rs in d.get("runs", {}).values() for r in rs]
        for r in rows:
            for k, e in keymap.items():
                if k in r:
                    add(rel, e, r[k], str(r.get("family", r.get("run", "row"))))
    lb = load("outputs/analysis/a1_lower_bound_constants.json")["margin_mass_frozen"]
    for k, e in (("mass_eps_0.01", 0.01), ("mass_eps_0.02", 0.02), ("mass_eps_0.05", 0.05), ("mass_eps_0.1", 0.1)):
        add("outputs/analysis/a1_lower_bound_constants.json", e, lb[k], "margin_mass_frozen")

    by_eps = {}
    for a in arms:
        by_eps.setdefault(a["eps"], []).append(a["value"])
    out = {"n_arms_scanned": len(arms), "archives": sorted({a["archive"] for a in arms}), "by_eps": {}}
    for e in sorted(by_eps):
        vals = by_eps[e]
        out["by_eps"]["%g" % e] = {"n": len(vals), "min": min(vals), "max": max(vals),
                                   "n_below_1": sum(1 for v in vals if v < 1.0),
                                   "n_exactly_1": sum(1 for v in vals if v == 1.0)}
    out["claim_check"] = {
        "M(0.05)_min_over_all_arms": min(by_eps.get(0.05, [0])),
        "M(0.05)_at_least_0.97_everywhere": min(by_eps.get(0.05, [0])) >= 0.97,
        "M(0.05)_at_least_0.98_everywhere": min(by_eps.get(0.05, [0])) >= 0.98,
        "M(0.10)_equals_1_everywhere": all(v == 1.0 for v in by_eps.get(0.1, [])),
    }
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    control = control_block()
    adapted = adapted_block()
    tau = tau_block()
    a1 = a1_reference_block()
    ds = dataset_block()
    state = manuscript_state()
    survey = saturation_survey()

    payload = {
        "artifact": "A23 margin-quality certificate - negative-control evidence summary",
        "purpose": ("Evidence and provenance for the sentence(s) stating that the margin-mass certificate is informative "
                    "where it was validated and saturates (uninformative) on the generic-CLIP A23 control, with no "
                    "advantage claimed from it."),
        "generated_by": "tools/_p1585_a23_margin_negative_control.py",
        "certificate_definition": ("mass(eps) = mean(1[margin <= 2 eps]) with margin = s_i(y_i) - max_{c != y_i} s_i(c); "
                                   "mass is therefore the empirical CDF of the top-1 margin evaluated at 2 eps."),
        "control_generic_clip": control,
        "adapted_marine_encoders": adapted,
        "order_preservation_counterpart": tau,
        "informative_reference_a1": a1,
        "saturation_across_all_archived_arms": survey,
        "datasets": ds,
        "manuscript_state": state,
        "verdict": {
            "saturation_is_expected_consequence": True,
            "saturation_is_a_genuine_failure_at_the_tested_operating_point": True,
            "failure_of_the_definition": False,
            "why": ("M(eps) is a CDF evaluated at 2 eps, so it saturates by construction once 2 eps exceeds the bulk of "
                    "the margin distribution. In CLIP score units that bulk lies below ~0.02 in every archived domain: "
                    "on the A1 ImageNet-5k reference the frozen model has margin median 0.0063 and reaches M(0.05) = "
                    "0.9998 / M(0.1) = 1.0 at 59.1% top-1, and the A23 adapted encoders (21.8% / 24.1% top-1) also have "
                    "M(0.1) = 1.0. Within the control, M(0.05) and M(0.1) are identically 1.0 in all 14 configurations, "
                    "which makes the archived correlation NaN and the threshold classifier degenerate to chance "
                    "(BA 0.50); that is a real loss of usefulness at that operating point."),
            "low_frozen_accuracy_causal_claim_supported": False,
            "low_frozen_accuracy_caveat": ("The claim 'saturation happens because frozen accuracy is too low' is not "
                                           "supported by the archives: the 59.1%-accuracy ImageNet-5k reference "
                                           "saturates identically at eps >= 0.05, and the adapted marine encoders at "
                                           "21.8-24.1% top-1 are not saturated at eps = 0.02. Frozen accuracy in the "
                                           "control is 21.57% (marine_optical) and 22.04% (acoustic_sonar) on 7 classes, "
                                           "i.e. above the 14.29% chance level, which is why the manuscript's current "
                                           "wording ('the frozen accuracy is too low for small margins to separate "
                                           "rows') should be replaced by the eps-grid explanation."),
            "informative_operating_point": ("eps = 0.01 (never evaluated in the A23 control, whose grid starts at 0.02): "
                                            "A1 ImageNet-5k gives M(0.01) = 0.681 frozen and Pearson -0.9956 between "
                                            "M(0.01) and top-1 across 17 configurations, and 0.6772-0.7200 across the "
                                            "10 prompt templates of the clip32 arm."),
            "notes_paraphrase_check": ("The project notes' phrase 'frozen accuracy only 20-27%' is a paraphrase of the "
                                       "near-frozen band, not a single archived field: the archived lambda = 0 values are "
                                       "21.5743% (marine_optical) and 22.0415% (acoustic_sonar); the full lambda grids "
                                       "span 19.8251-23.6152% and 2.5238-27.5379% respectively. The 'M approx 1' part of "
                                       "the notes is exact for eps >= 0.05 (constant 1.0 in all 14 configurations) and "
                                       "approximate at eps = 0.02 (0.9825-1.0)."),
            "holds_on": ("generic CLIP ViT-B/32 (openai/clip-vit-base-patch32) on fathomnet8 and NKSID; near-saturated "
                         "and weakly correlated on BioCLIP-base and OceanCLIP over the 67-class marine subset; "
                         "saturated at eps = 0.05 in every arm of every archive that records a margin mass "
                         "(M(0.05) >= 0.976 in 108 arms, M(0.10) = 1.0 in 66 arms, across the control, both adapted "
                         "encoders, the UATD and water-tank OOD probes, the A1 ImageNet-5k and marine-retrieval "
                         "monitors); not saturated at eps = 0.01 on the A1 ImageNet-5k references."),
            "advantage_claimed": False,
        },
        "conclusion": ("The margin-quality certificate M(eps) does not transfer as a portable scalar to the A23 control "
                       "domains at the eps grid that was tested: on generic CLIP ViT-B/32 (fathomnet8 tree, 343 images, "
                       "7 classes; NKSID class directories, 1783 images, 7 classes) M(0.05) and M(0.1) equal 1.0 in all "
                       "14 surgery configurations, so the archived correlation with top-1 is undefined (NaN) and the "
                       "fitted threshold degenerates to chance (BA 0.50 in both directions), while the adapted encoders "
                       "(BioCLIP, OceanCLIP; 1608 images, 67 classes) show only weak within-family correlations "
                       "(r = -0.346 / -0.564 at eps = 0.05) and a threshold fitted on one encoder fails on the other "
                       "(BA 0.125-0.50). This saturation is an expected consequence of evaluating a margin CDF at a "
                       "fixed coarse eps: in CLIP score units the margin bulk lies below ~0.02 in every archived "
                       "domain, including the higher-accuracy ImageNet-5k reference (M(0.05) = 0.9998 at 59.1% top-1, "
                       "M(0.1) = 1.0). It is therefore a failure of the tested operating point, not of the "
                       "certificate's definition, and it must not be explained by low frozen accuracy alone, because "
                       "the high-accuracy reference saturates identically. No advantage is claimed from the "
                       "certificate anywhere in the A23 manuscript; the informative regime (eps = 0.01, where M(0.01) "
                       "tracks top-1 at r = -0.996 on ImageNet-5k) has not been evaluated on the A23 domains."),
        "provenance_gaps": [
            "The control archive stores no per-domain image or class counts; n = 343 (fathomnet8) is recovered from the "
            "accuracy fractions (74/343 = 21.5743...%) and n = 1783 (NKSID) from the loader's own glob over 7 class "
            "directories. The script docstring's '8 classes' is not what the loader collected (7 subdirectories in both "
            "trees).",
            "The control's two domains are the raw data trees, not the manuscript's canonical protocols: fathomnet8 is "
            "7 classes / 343 images (the paper's shipboard FathomNet subset is 6 concepts / 144 frames, and its marine "
            "reference domain is the 67-class rare-species subset with 1608 images), and the NKSID arm is 7 classes / "
            "1783 imbalanced images (floats 951 of 1783) against the paper's balanced 8-class / 650-image sonar "
            "protocol. The NKSID tree holds 834 further loose img_*.jpg files at its root that the loader skipped.",
            "The archive key 'M(0.01)' in a23_certificate_control.json is a duplicate of mass_0.05 (script lines "
            "123-125); the control never measured M(0.01).",
            "The control's threshold-transfer labels are a per-domain median split (script lines 128-133), so BA = 0.50 "
            "there reflects a degenerate constant predictor, not a validated transfer failure.",
        ],
    }

    if a.apply:
        with io.open(OUT, "w", encoding="utf-8", newline="") as fh:
            fh.write(json.dumps(payload, indent=1, ensure_ascii=False))
        print("  wrote", os.path.relpath(OUT, REPO))
    print("  control pooled:", json.dumps(control["pooled"]))
    print("  control correlation archived:", json.dumps(control["correlation_archived"]))
    print("  adapted r_M005:", {k: v["r_M005_archived"] for k, v in adapted["models"].items()})
    print("  A1 r(mass_eps_0.01, top1):", a1["correlation_with_top1_archived"]["mass_eps_0.01"])
    print("  working-copy certificate lines:", state["working_copy"]["lines_with_certificate_text"])
    print("  frozen submitted certificate lines:", state["frozen_submitted_26_0663"]["lines_with_certificate"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())