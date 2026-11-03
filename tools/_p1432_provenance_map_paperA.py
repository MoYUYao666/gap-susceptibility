# -*- coding: utf-8 -*-
r"""Curated provenance mapping for Paper A (30 floats).

    python tools/_p1432_provenance_map_paperA.py [--apply]
"""
from __future__ import annotations

import argparse
import glob
import io
import json
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST = os.path.join(REPO, "docs", "provenance_manifest.json")

MAP = {
    "fig:overview": ("tools/_pa_rebuild_figs_rest.py", ["outputs/flickr30k/rq2_both/gap_history.json"]),
    "fig:ode": ("tools/_pa_rebuild_figs_rest.py", ["outputs/theory/beta_pilot/beta_pilot_both_r8/seed42/beta_results.json"]),
    "fig:corr": ("tools/_pa_fig2_corr.py", ["outputs/analysis/dg_r1_reproducible.json"]),
    "fig:falsification": ("tools/_pa_rebuild_figs_rest.py", ["outputs/analysis/k_remeasured_both.json"]),
    "fig:ablation": ("tools/_pa_rebuild_figs_rest.py", ["outputs/flickr30k/alpha_16/gap_history.json"]),
    "fig:crossmethod": ("tools/_pa_rebuild_figs_rest.py", ["outputs/theory/adapter/adapter_all_results.json"]),
    "fig:ers": ("tools/_pa_rebuild_figs_rest.py", ["outputs/analysis/k_remeasured_both.json"]),
    "fig:weight_svd": ("tools/_pa_fig8_rebuild.py", ["outputs/analysis/strict_control_summary.json"]),
    "fig:noise_sensitivity": ("tools/_pa_fig9_noise_rebuild.py", ["outputs/noise_fixed_aug.json"]),
    "fig:layered_ft": ("tools/_pa_rebuild_fig10.py", ["outputs/layered_ft_results.json"]),
    "fig:zeroshot": ("tools/_pa_rebuild_fig12.py", ["outputs/zeroshot_extra.json"]),
    "fig:adapter_layered": ("tools/_pa_fix_fig14_title.py", ["outputs/adapter_layered_results.json"]),
    "fig:budget": ("tools/_pa_split_appendix_figs.py", ["outputs/analysis/strict_control_summary.json"]),
    "fig:vision_untouched": ("tools/_pa_fig8c.py", ["outputs/analysis/strict_control_summary.json"]),
    "fig:sigma0_control": ("tools/_pa_split_appendix_figs.py", ["outputs/noise_fixed_aug.json"]),
    "fig:ratio": ("tools/_pa_split_appendix_figs.py", ["outputs/noise_fixed_aug.json"]),
    "fig:stratified": ("tools/_p860_fig_stratified.py", ["outputs/analysis/dg_r1_reproducible.json"]),
    "fig:site_schematic": (None, None),
    "tab:position": (None, ["outputs/analysis/tab_position_provenance.json"]),
    "tab:position_strict": (None, ["outputs/analysis/strict_table_provenance.json"]),
    "tab:family": (None, ["outputs/analysis/ode_ledger.json"]),
    "tab:corr": (None, ["outputs/analysis/dg_r1_reproducible.json"]),
    "tab:beta_pilot": (None, ["outputs/theory/beta_pilot/beta_pilot_results.json"]),
    "tab:phase2": (None, ["outputs/analysis/ode_ledger.json"]),
    "tab:diagnostics": (None, ["outputs/analysis/ode_ledger.json"]),
    "tab:generalization": (None, ["outputs/analysis/ode_ledger.json"]),
    "tab:grad_side": (None, ["outputs/analysis/k_remeasured_both.json"]),
    "tab:config_groups": (None, ["outputs/analysis/strict_control_summary.json"]),
    "tab:odefit": ("tools/_p1440_paperA_ode_residuals.py", ["outputs/analysis/paperA_ode_residuals.json"]),
    "tab:vlm": (None, ["outputs/vlm_clean_summary.json", "outputs/vlm_clean_cloud/frozen_baseline.json"]),
    "tab:llava": (None, ["outputs/canonical_caption_metric.json"]),
}
EXEMPT = {"fig:site_schematic": "mechanism schematic (not measured data); generator tools/_p1333_upgrade_figures.py"}


def find_script(archive: str) -> str | None:
    name = os.path.basename(archive)
    for f in sorted(glob.glob(os.path.join(REPO, "tools", "*.py"))):
        try:
            t = io.open(f, encoding="utf-8", errors="ignore").read()
        except Exception:
            continue
        if name in t:
            return os.path.relpath(f, REPO)
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    manifest = json.load(io.open(MANIFEST, encoding="utf-8"))
    floats = []
    for label, (script, archives) in MAP.items():
        if label in EXEMPT:
            floats.append({"label": label, "kind": "figure", "status": "exempt", "note": EXEMPT[label],
                           "script": "tools/_p1333_upgrade_figures.py"})
            continue
        archives = [x for x in (archives or []) if os.path.exists(os.path.join(REPO, x))]
        if not script:
            script = find_script(archives[0]) if archives else None
        sc = script if script and os.path.exists(os.path.join(REPO, script)) else None
        status = "verified" if (sc and archives) else "pending"
        floats.append({"label": label, "kind": "table" if label.startswith("tab:") else "figure",
                       "script": sc, "archive": archives[0] if archives else None, "archives": archives,
                       "status": status, "note": "" if status == "verified" else "script or archive missing"})
    manifest["manuscripts"]["paperA"]["floats"] = floats
    verified = sum(1 for e in floats if e["status"] == "verified")
    pending = [e["label"] for e in floats if e["status"] == "pending"]
    print(f"  paperA: {verified}/{len(floats)} verified; pending: {pending}")
    if a.apply:
        io.open(MANIFEST, "w", encoding="utf-8", newline="").write(json.dumps(manifest, indent=1, ensure_ascii=False))
        print("  wrote", os.path.relpath(MANIFEST, REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
