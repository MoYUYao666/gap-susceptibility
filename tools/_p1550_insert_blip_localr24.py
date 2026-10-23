# -*- coding: utf-8 -*-
r"""Insert BLIP source (second non-CLIP source) and the local/cloud r=24 curvature split.

    python tools/_p1550_insert_blip_localr24.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = os.path.join(REPO, "paper3", "paper_ieee")
SUPP = os.path.join(BASE, "supplementary", "supplementary.tex")
AN = os.path.join(REPO, "outputs", "analysis")
EXP = os.path.join(REPO, "paper3", "scripts", "outputs", "experiments")


def jl(p):
    return json.load(io.open(p, encoding="utf-8"))


def shares(path):
    d = jl(path)
    sh = [0.5 * 5e-5 * x["ghg_full"]["0.001"] / x["g2"] for x in d["runs"]]
    return sum(sh) / len(sh)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    loc = {r: shares(os.path.join(AN, f"p3_hessian_probe_r{r}.json")) for r in (8, 12, 16, 24)}
    clo = {24: shares(os.path.join(AN, "cloud_p3_hessian_probe_r24.json")),
           64: shares(os.path.join(AN, "cloud_p3_hessian_probe_r64.json"))}
    blip = jl(os.path.join(AN, "p3_blip_gamma.json"))
    arm = None
    for f in os.listdir(EXP):
        if f.startswith("verify_r1_s42_bcexplicit_v1_s1_m3_d11"):
            arm = jl(os.path.join(EXP, f))["delta_E"]
    print("local shares", loc, "cloud", clo, "blip alloc", blip["allocation"], "arm", arm)
    if not a.apply:
        return 0
    t = io.open(SUPP, encoding="utf-8").read()
    # S34 table
    i = t.find("\\label{app:highrank}")
    m = t.find("\\midrule", i)
    b = t.find("\\bottomrule", m)
    rows = "\n".join("%d & %s & %s \\\\" % (
        r,
        ("%+.4f" % loc[r]) if r in loc else "--",
        ("%+.4f" % clo[r]) if r in clo else "--") for r in (8, 12, 16, 24, 64))
    header_old = "rank & second-order share at $\\eta$ & share at $10^{-3}$ probe \\\\"
    header_new = "rank & local share at $\\eta$ & cloud share at $\\eta$ \\\\"
    seg_start = t.rfind("\\begin{tabular}", i - 400, i)
    seg_end = t.find("\\end{tabular}", i)
    seg = t[seg_start:seg_end]
    seg = seg.replace(header_old, header_new)
    t = t[:seg_start] + seg + t[seg_end:]
    t = t[: m + len("\\midrule")] + "\n" + rows + "\n" + t[b:]
    old_cap = ("\\caption{Curvature across rank. The second-order share stays negative through $r=16$ and turns positive at\n"
               "$r=24$/$r=64$ (cloud RTX 4080 SUPER), so the sign change is localized between $r=16$ and $r=24$; at the\n"
               "operating learning rate the share stays below $0.5\\%$. Archives:\n"
               "\\texttt{outputs/analysis/p3\\_hessian\\_probe\\_r8/12/16.json}, \\texttt{cloud\\_p3\\_hessian\\_probe\\_r24/64.json}.}")
    new_cap = ("\\caption{Curvature across rank on the local stack (torch 2.9/CUDA 13.0) and on the cloud stack\n"
               "(torch 2.12/CUDA 13.0). Locally the second-order share stays negative through $r=24$; on the cloud stack\n"
               "it turns positive at $r=24$, so the sign of the curvature term at high rank is itself environment-sensitive,\n"
               "matching the energy-sign sensitivity in S29. At the operating learning rate the share stays below $0.6\\%$.\n"
               "Archives: \\texttt{outputs/analysis/p3\\_hessian\\_probe\\_r8/12/16/24.json},\n"
               "\\texttt{cloud\\_p3\\_hessian\\_probe\\_r24/64.json}.}")
    if old_cap in t:
        t = t.replace(old_cap, new_cap, 1)
    else:
        print("S34 caption pattern not found")
    # S32 table: add BLIP row after the SigLIP row
    if "BLIP (captioning)" not in t and arm is not None:
        old = "SigLIP & %d & %d & %d & %d & %s \\\\" % (
            jl(os.path.join(AN, "p3_siglip_gamma.json"))["allocation"]["vision"],
            jl(os.path.join(AN, "p3_siglip_gamma.json"))["allocation"]["text_shallow"],
            jl(os.path.join(AN, "p3_siglip_gamma.json"))["allocation"]["text_mid"],
            jl(os.path.join(AN, "p3_siglip_gamma.json"))["allocation"]["text_deep"],
            "$%+.1f$" % jl(os.path.join(EXP, "verify_r1_s42_bcexplicit_v2_s7_m5_d2.json"))["delta_E"])
        if old in t:
            add = ("\nBLIP (captioning) & %d & %d & %d & %d & $%+.1f$ \\\\" % (
                blip["allocation"]["vision"], blip["allocation"]["text_shallow"],
                blip["allocation"]["text_mid"], blip["allocation"]["text_deep"], arm))
            t = t.replace(old, old + add, 1)
        else:
            print("SigLIP row pattern not found")
    old_cap2 = "\\texttt{outputs/analysis/p3\\_siglip\\_gamma.json}, \\texttt{verify\\_r1\\_s42\\_bcexplicit\\_v2\\_s7\\_m5\\_d2.json}.}"
    new_cap2 = ("\\texttt{outputs/analysis/p3\\_siglip\\_gamma.json}, \\texttt{outputs/analysis/p3\\_blip\\_gamma.json},\n"
                "\\texttt{verify\\_r1\\_s42\\_bcexplicit\\_v2\\_s7\\_m5\\_d2.json}, \\texttt{...\\_v1\\_s1\\_m3\\_d11.json}.}")
    if old_cap2 in t:
        t = t.replace(old_cap2, new_cap2, 1)
    # S17 curvature row
    old_row = ("curvature sign stable across ranks & \\emph{not} supported & negative at $r=5/6$, positive at "
               "$r=24/64$ (S34) \\\\")
    new_row = ("curvature sign stable across ranks & \\emph{not} supported & negative locally through $r=24$; "
               "$r=24$ sign differs on the cloud stack (S34) \\\\")
    if old_row in t:
        t = t.replace(old_row, new_row, 1)
    else:
        print("S17 curvature row not found")
    io.open(SUPP, "w", encoding="utf-8", newline="").write(t)
    print("supplement updated")
    mf = jl(os.path.join(REPO, "docs", "provenance_manifest.json"))
    floats = mf["manuscripts"]["P3"]["floats"]
    for f in floats:
        if f["label"] == "tab:highrank":
            f["archive"] = "outputs/analysis/p3_hessian_probe_r24.json"
    if not any(f["label"] == "tab:blipsource" for f in floats):
        floats.append({"label": "tab:blipsource", "kind": "table", "script": "tools/_p1549_blip_gamma.py",
                       "archive": "outputs/analysis/p3_blip_gamma.json", "status": "verified",
                       "note": "BLIP source allocation row inside tab:siglip"})
    io.open(os.path.join(REPO, "docs", "provenance_manifest.json"), "w", encoding="utf-8").write(
        json.dumps(mf, indent=1, ensure_ascii=False))
    print("manifest updated; P3 floats:", len(floats))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
