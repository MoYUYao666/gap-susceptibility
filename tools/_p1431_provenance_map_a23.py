# -*- coding: utf-8 -*-
r"""Curated provenance mapping for A23 (31 floats).

Archives are the topic-specific JSON files in outputs/; scripts are the figure generators or, for tables, the script that
produces the archive (found by searching tools/ for the archive filename).

    python tools/_p1431_provenance_map_a23.py [--apply]
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
    "fig:tau": ("tools/clip_a2_figures.py", ["outputs/ocean_margins.json", "outputs/sonar_protocol.json"]),
    "fig:lambda": ("tools/clip_a2_figures.py", ["outputs/ocean_gap_surgery.json"]),
    "fig:sonar-tau": ("tools/clip_a2_figures.py", ["outputs/sonar_protocol_full.json"]),
    "tab:sonar-exact": (None, ["outputs/sonar_protocol_full.json"]),
    "tab:sonar-sigma": (None, ["outputs/sonar_protocol_full.json"]),
    "tab:sonar-peft": (None, ["outputs/sonar_peft.json", "outputs/sonar_peft_ms.json"]),
    "fig:sonar-sigma": ("tools/clip_a2_fig7.py", ["outputs/sonar_protocol_full.json"]),
    "fig:sigma": ("tools/clip_a2_figures.py", ["outputs/ocean_margins.json", "outputs/ocean_flickrft_sigma.json"]),
    "tab:spectrum": (None, ["outputs/ocean_spectrum.json"]),
    "tab:portrait": (None, ["outputs/ocean_margins.json"]),
    "tab:disc": (None, ["outputs/ocean_clip2x2.json"]),
    "tab:peft": (None, ["outputs/ocean_peft.json"]),
    "fig:peft": ("tools/clip_a2_figures.py", ["outputs/ocean_peft.json"]),
    "tab:rank1": (None, ["outputs/ocean_rank1_bound.json"]),
    "tab:dir-op": (None, ["outputs/direction_operator.json"]),
    "tab:ml16k": (None, ["outputs/ocean_ml16k_retrieval.json"]),
    "tab:watertank": (None, ["outputs/sonar_protocol_full.json"]),
    "tab:replica": (None, ["outputs/ocean_replica.json"]),
    "tab:monitor": (None, ["outputs/ocean_tautraj.json"]),
    "fig:degrad": ("tools/clip_a2_figures.py", ["outputs/ocean_degradation.json"]),
    "tab:degrad": (None, ["outputs/ocean_degradation.json"]),
    "tab:eng": (None, None),
    "tab:calib": (None, ["outputs/threshold_calibration.json"]),
    "tab:theory-stack": (None, ["outputs/a1_theory_verify.json"]),
    "tab:matrix": (None, ["outputs/domain_matrix.json"]),
    "tab:dynamics": (None, ["outputs/dynamics_matrix.json"]),
    "tab:degmap": (None, ["outputs/degradation_matrix.json"]),
    "tab:subspace": (None, ["outputs/direction_subspace.json"]),
    "tab:perimage": (None, ["outputs/perimage_operator.json"]),
    "tab:qa-layers": (None, ["outputs/ml16k_qa_layers.json"]),
    "tab:classlaw": (None, ["outputs/ocean_sigma_other.json"]),
}
EXEMPT = {"tab:eng": "engineering-procedure table: no measured data, distilled procedure"}


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
            floats.append({"label": label, "kind": "table", "status": "exempt", "note": EXEMPT[label]})
            continue
        archives = [x for x in (archives or []) if os.path.exists(os.path.join(REPO, x))]
        if not script and archives:
            script = find_script(archives[0])
        sc = script if script and os.path.exists(os.path.join(REPO, script)) else None
        if not sc and archives:
            sc = find_script(archives[0])
        status = "verified" if (sc and archives) else "pending"
        floats.append({"label": label, "kind": "table" if label.startswith("tab:") else "figure",
                       "script": sc, "archive": archives[0] if archives else None, "archives": archives,
                       "status": status, "note": "" if status == "verified" else "script or archive missing"})
    manifest["manuscripts"]["A23"]["floats"] = floats
    verified = sum(1 for e in floats if e["status"] == "verified")
    pending = [e["label"] for e in floats if e["status"] == "pending"]
    print(f"  A23: {verified}/{len(floats)} verified; pending: {pending}")
    if a.apply:
        io.open(MANIFEST, "w", encoding="utf-8", newline="").write(json.dumps(manifest, indent=1, ensure_ascii=False))
        print("  wrote", os.path.relpath(MANIFEST, REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
