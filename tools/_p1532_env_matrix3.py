# -*- coding: utf-8 -*-
r"""Three-environment matrix (A3): rewrite S29 with the local torch 2.9/cu130, cloud torch 2.12/cu130 and local
torch 2.4/cu121 results.

    python tools/_p1532_env_matrix3.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = os.path.join(REPO, "paper3", "paper_ieee")
SUPP = os.path.join(BASE, "supplementary", "supplementary.tex")
DISC = os.path.join(BASE, "sections", "discussion.tex")
MANIFEST = os.path.join(REPO, "docs", "provenance_manifest.json")
AN = os.path.join(REPO, "outputs", "analysis")
EXP = os.path.join(REPO, "paper3", "scripts", "outputs", "experiments")


def jl(p):
    return json.load(io.open(p, encoding="utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    env1 = jl(os.path.join(AN, "p3_rerun_protocol.json"))["runs"]
    env2 = {r: jl(os.path.join(EXP, f"cloud_verify_r{r}_s42.json")) for r in (5, 6)}
    env3 = {5: jl(os.path.join(EXP, "verify_r5_s42_lr5e-05_nw_float1_adamw_e3_bcuniform_a10.json")),
            6: jl(os.path.join(EXP, "verify_r6_s42_lr5e-05_nw_float1_adamw_e3_bcuniform_a12.json"))}
    matrix = {
        "env1_local_torch29_cu130": {"gpu": "RTX 4060 Laptop", "torch": "2.9.1+cu130", "cuda": "13.0",
                                     "runs": {r: {"E": env1[f"r{r}_s42"]["E"], "delta_E": env1[f"r{r}_s42"]["delta_E"]}
                                              for r in (5, 6)}},
        "env2_cloud_torch212_cu130": {"gpu": "RTX 4080 SUPER", "torch": "2.12.1+cu130", "cuda": "13.0",
                                      "runs": {r: {"E": env2[r]["E"], "delta_E": env2[r]["delta_E"]} for r in (5, 6)}},
        "env3_local_torch24_cu121": {"gpu": "RTX 4060 Laptop", "torch": "2.4.1+cu121", "cuda": "12.1",
                                     "runs": {r: {"E": env3[r]["E"], "delta_E": env3[r]["delta_E"]} for r in (5, 6)}},
    }
    json.dump(matrix, io.open(os.path.join(AN, "p3_env_matrix3.json"), "w", encoding="utf-8"), indent=1)
    rows = []
    for name, env in matrix.items():
        for r in (5, 6):
            d = env["runs"][r]
            rows.append("%s & %s & %s & %d & %.1f & %+.1f \\\\" % (env["gpu"], env["torch"], env["cuda"], r,
                                                                   d["E"][0], d["delta_E"]))
    rows = "\n".join(rows)
    print(rows)
    if not a.apply:
        return 0
    t = io.open(SUPP, encoding="utf-8").read()
    i = t.find("\\label{app:envcloud}")
    m = t.find("\\midrule", i)
    b = t.find("\\bottomrule", m)
    t = t[: m + len("\\midrule")] + "\n" + rows + "\n" + t[b:]
    old_cap = ("\\caption{Cross-environment reproducibility of the $r=5$/$r=6$ crossing (seed 42, blank-image protocol). The sign\n"
               "pattern is preserved (negative at $r=5$, positive at $r=6$) and the $E_0$ shifts by $0.1\\%$; magnitudes differ by\n"
               "about $2\\times$, which is the environment-sensitivity the paper reports. Archives:\n"
               "\\texttt{outputs/analysis/p3\\_rerun\\_protocol.json} and \\texttt{cloud\\_verify\\_r*\\_s42.json}.}")
    new_cap = ("\\caption{Cross-environment reproducibility of the $r=5$/$r=6$ crossing (seed 42, blank-image protocol). The\n"
               "positive sign at $r=6$ is stable in all three environments; the sign at $r=5$ flips in the torch 2.4/CUDA 12.1\n"
               "environment ($+41.0$ against $-10.5$ and $-33.5$ in the two cu130 environments), so the crossing is\n"
               "environment-sensitive and the $r=5$ sign is not a cross-environment constant. Archive:\n"
               "\\texttt{outputs/analysis/p3\\_env\\_matrix3.json}.}")
    if old_cap in t:
        t = t.replace(old_cap, new_cap, 1)
    old_row = ("sign pattern preserved across environments & supported & RTX 4060/4080, torch 2.9/2.12 (S29) \\\\")
    new_row = ("crossing stable across torch/CUDA versions & \\emph{not} supported & $r=6$ positive everywhere; $r=5$ "
               "sign flips in torch 2.4/cu121 (S29) \\\\")
    if old_row in t:
        t = t.replace(old_row, new_row, 1)
    io.open(SUPP, "w", encoding="utf-8", newline="").write(t)
    print("S29 rewritten (3 environments)")
    d = io.open(DISC, encoding="utf-8").read()
    old_lim = ("(6) The\nphase-table values are environment-sensitive: a legacy batch from an earlier environment\n"
               "differs in sign at $r\\in[5,8]$, so all reported LLaVA values come from the\n"
               "current-environment E2 and supplementary batches (verified by local re-runs), and the\n"
               "ordering evidence ($p = 2^{-5}$) is computed within that environment; cross-environment\n"
               "reproducibility of $r_c$ is an open question rather than an established constant.")
    new_lim = ("(6) The\nphase-table values are environment-sensitive: a legacy batch from an earlier environment\n"
               "differs in sign at $r\\in[5,8]$; a three-environment matrix (torch 2.9/CUDA 13.0, torch 2.12/CUDA 13.0,\n"
               "torch 2.4/CUDA 12.1) keeps the $r=6$ sign positive but flips the $r=5$ sign in the oldest stack\n"
               "(Section~S29), so $r_c$ is an environment-conditioned quantity rather than a universal constant.")
    if old_lim in d:
        d = d.replace(old_lim, new_lim, 1)
        io.open(DISC, "w", encoding="utf-8", newline="").write(d)
        print("discussion limitation updated")
    mf = jl(MANIFEST)
    for f in mf["manuscripts"]["P3"]["floats"]:
        if f["label"] == "tab:envcloud":
            f["archive"] = "outputs/analysis/p3_env_matrix3.json"
    io.open(MANIFEST, "w", encoding="utf-8", newline="").write(json.dumps(mf, indent=1, ensure_ascii=False))
    print("manifest updated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
