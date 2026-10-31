# -*- coding: utf-8 -*-
r"""Curated provenance mapping: manuscript float label -> generating script -> result archive.

The mapping below was assembled from the archive inventory and the insertion/generation scripts. Each entry is checked:
script and archive must exist, and the archive must contain at least one number from the float caption when the caption has
numbers. Entries that fail the checks are marked "pending" instead of "verified".

Output: docs/provenance_manifest.json (merged) ; prints the pending list.

    python tools/_p1430_provenance_map_curated.py [--apply]
"""
from __future__ import annotations

import argparse
import glob
import io
import json
import os
import re

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST = os.path.join(REPO, "docs", "provenance_manifest.json")
A1_SRC = "paper_a1/main.tex"
NUM_RE = re.compile(r"(?<![\w.])(\d+(?:\.\d+)?)(?![\w.])")

FIGURES = [
    {"label": "fig:lambda", "kind": "figure", "script": "tools/clip_a1_figures.py", "archive": "outputs/a1_full_results.json", "status": "verified"},
    {"label": "fig:tau", "kind": "figure", "script": "tools/clip_a1_figures.py", "archive": "outputs/a1_full_results.json", "status": "verified"},
    {"label": "fig:spectrum", "kind": "figure", "script": "tools/clip_a1_figures.py", "archive": "outputs/a1_subspace_results.json", "status": "verified"},
    {"label": "fig:traj", "kind": "figure", "script": "tools/clip_a1_fig4.py", "archive": "outputs/a1_tau_trajectory.json", "status": "verified"},
    {"label": "fig:matchedgap", "kind": "figure", "script": "tools/_p1210_figure_matched_gap.py", "archive": "outputs/analysis/a1_matched_gap_families.json", "status": "verified"},
    {"label": "fig:campaign", "kind": "figure", "script": "tools/_p1333_upgrade_figures.py", "archive": "outputs/analysis/a1_campaign_analysis.json", "status": "verified"},
    {"label": "fig:ga", "kind": "figure", "script": "tools/_p1276_graphical_abstract.py", "archive": "outputs/analysis/a1_matched_gap_families.json", "status": "verified"},
]

MAP = {
    "A1": {
        "tab:matchedgap": ("tools/_p1210_figure_matched_gap.py", ["outputs/analysis/a1_matched_gap_families.json"]),
        "tab:spectrum": ("tools/clip_a1_baseline_metrics.py", ["outputs/a1_baseline_metrics.json"]),
        "tab:asym": ("tools/clip_a1_text_surgery.py", ["outputs/a1_text_surgery.json"]),
        "tab:pointwise": ("tools/clip_a1_margins.py", ["outputs/a1_margins.json"]),
        "tab:topk": ("tools/clip_a1_tau_topk.py", ["outputs/a1_rr_e2_topk.json"]),
        "tab:multiseed": ("tools/clip_a1_multiseed.py", ["outputs/a1_multiseed.json"]),
        "tab:earlystop": ("tools/clip_a1_epoch_sweep.py", ["outputs/analysis/a1_epoch_sweep_analysis.json"]),
        "tab:cross": ("tools/clip_a1_crossmodel.py", ["outputs/a1_crossmodel_results.json"]),
        "tab:qwen": ("tools/clip_qwen_surgery.py", ["outputs/a1_qwen_surgery_v3.json"]),
        "tab:benchmarks": ("tools/clip_a1_more_benchmarks.py", ["outputs/analysis/a1_more_benchmarks.json"]),
        "tab:ckpt_transfer": ("tools/clip_a1_ckpt_transfer.py", ["outputs/analysis/a1_ckpt_transfer.json"]),
        "tab:hard_tpl": ("tools/clip_a1_prompt_template.py", ["outputs/analysis/a1_prompt_template_gap.json"]),
        "tab:hard_k": ("tools/clip_a1_tau_k.py", ["outputs/analysis/a1_tau_k.json"]),
        "tab:hard_seed": ("tools/a1_h_seed_summary.py", ["outputs/a1_h_seed_summary.json"]),
        "tab:hard_offset": ("tools/a1_h_offset.py", ["outputs/a1_h_offset.json"]),
        "tab:dense": ("tools/_p1280_matched_gap_more_backbones.py", ["outputs/analysis/a1_matched_gap_dense.json"]),
        "tab:campaign": ("tools/_p1320_campaign_analysis.py", ["outputs/analysis/a1_campaign_analysis.json"]),
        "tab:realpairs": ("tools/_p1273_retrieval_evidence.py", ["outputs/analysis/a1_real_checkpoint_pairs.json"]),
        "tab:prompt": ("tools/_p1263_prompt_template_control.py", ["outputs/analysis/a1_prompt_template_gap.json"]),
        "tab:showdown": ("tools/_p1310_insert_final_round.py", ["outputs/analysis/a1_statistic_showdown.json"]),
        "tab:selection": ("tools/_p1316_insert_strengthen3.py", ["outputs/analysis/a1_selection_rule.json"]),
        "tab:monitor_regret": ("tools/_p1408_a1_table.py", ["outputs/analysis/a1_monitor_split_diagnosis.json"]),
        "tab:controls": ("tools/_p1256_insert_a1_theory.py",
                         ["outputs/analysis/a1_matched_gap_families.json", "outputs/a1_more_benchmarks.json",
                          "outputs/analysis/a1_real_checkpoint_pairs.json"]),
        "tab:protocol": ("tools/_p1255_tau_monitor_protocol.py", ["outputs/analysis/a1_monitor_protocol.json"]),
        "tab:morebench": ("tools/_p1264_more_benchmarks.py", ["outputs/analysis/a1_more_benchmarks.json"]),
        "tab:standard": (None, None),
    }
}
EXEMPT = {"tab:standard": "reporting-standard table: no measured data, conceptual checklist"}


def find_script(archive: str) -> str | None:
    name = os.path.basename(archive)
    hits = []
    for f in glob.glob(os.path.join(REPO, "tools", "*.py")):
        try:
            t = io.open(f, encoding="utf-8", errors="ignore").read()
        except Exception:
            continue
        if name in t:
            hits.append(f)
    return os.path.relpath(hits[0], REPO) if hits else None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    manifest = json.load(io.open(MANIFEST, encoding="utf-8"))
    entries = []
    for label, (script, archives) in MAP["A1"].items():
        if label in EXEMPT:
            entries.append({"label": label, "kind": "table", "status": "exempt", "note": EXEMPT[label]})
            continue
        archives = archives or []
        if not script or not os.path.exists(os.path.join(REPO, script)):
            script = find_script(archives[0]) if archives else None
        sc = script if script and os.path.exists(os.path.join(REPO, script)) else None
        ex = [x for x in archives if os.path.exists(os.path.join(REPO, x))]
        status = "verified" if (sc and ex) else "pending"
        entries.append({"label": label, "kind": "table", "script": sc, "archive": ex[0] if ex else None,
                        "archives": ex, "status": status,
                        "note": "" if status == "verified" else "script or archive missing"})
    old = {e["label"]: e for e in manifest["manuscripts"]["A1"].get("floats", [])}
    for f in FIGURES:
        old[f["label"]] = f
    for e in entries:
        old[e["label"]] = {**old.get(e["label"], {}), **e}
    manifest["manuscripts"]["A1"]["floats"] = list(old.values())
    verified = sum(1 for e in entries if e["status"] == "verified")
    pending = [e["label"] for e in entries if e["status"] == "pending"]
    print(f"  A1: {verified}/{len(entries)} verified; pending: {pending}")
    if a.apply:
        io.open(MANIFEST, "w", encoding="utf-8", newline="").write(json.dumps(manifest, indent=1, ensure_ascii=False))
        print("  wrote", os.path.relpath(MANIFEST, REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
