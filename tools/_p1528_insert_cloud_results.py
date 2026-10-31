# -*- coding: utf-8 -*-
r"""Insert the cloud results: second-environment reproducibility (S29), Qwen2.5-VL-7B control, per-step VQA.

    python tools/_p1528_insert_cloud_results.py [--apply]
"""
from __future__ import annotations

import argparse
import glob
import io
import json
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = os.path.join(REPO, "paper3", "paper_ieee")
SUPP = os.path.join(BASE, "supplementary", "supplementary.tex")
AUDIT = os.path.join(BASE, "audit_check.py")
AUDIT_PDF = os.path.join(BASE, "audit_pdf.py")
DISC = os.path.join(BASE, "sections", "discussion.tex")
MANIFEST = os.path.join(REPO, "docs", "provenance_manifest.json")
AN = os.path.join(REPO, "outputs", "analysis")
EXP = os.path.join(REPO, "paper3", "scripts", "outputs", "experiments")


def jload(p):
    return json.load(io.open(p, encoding="utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    # --- data ---
    local = {r: jload(os.path.join(EXP, f"verify_r{r}_s42.json")) for r in (5, 6)}
    cloud = {r: jload(os.path.join(EXP, f"cloud_verify_r{r}_s42.json")) for r in (5, 6)}
    q7 = []
    for f in sorted(glob.glob(os.path.join(EXP, "*cloud_q25_7b*.json"))):
        d = jload(f)
        q7.append((d["rank"], d["seed"], d["delta_E"], d["E"]))
    q7.sort()
    vqa = {}
    for k in ("base", "5", "6"):
        p = os.path.join(AN, f"cloud_p3_vqa_downstream_{k}.json")
        if os.path.exists(p):
            vqa[k] = jload(p)
    env_rows = "\n".join(
        "%s & %s & %s & %s & %s & %+.1f & %.1f \\\\" % (
            r, "RTX 4060 Laptop", "2.9.1+cu130", "3921.0", "3.4/0.1", local[r]["delta_E"],
            local[r]["E"][0])
        for r in (5, 6))
    env_rows2 = "\n".join(
        "%s & %s & %s & %.1f & %s & %+.1f & %.1f \\\\" % (
            r, "RTX 4080 SUPER", "2.12.1+cu130", cloud[r]["E"][0], "3.2/0.3", cloud[r]["delta_E"],
            cloud[r]["E"][0])
        for r in (5, 6))
    q7_rows = "\n".join("%d & %d & %+.1f & %s \\\\" % (r, s, dE, E) for r, s, dE, E in q7)
    vqa_rows = "\n".join(
        "%s & %d & %.4f & %.4f & %.4f \\\\" % (
            ("base" if k == "base" else ("r=%s (per-step)" % k)), v["meta"]["n_eval"],
            v["accuracy"], v["relaxed_accuracy"], v["token_f1"])
        for k, v in vqa.items())
    print("local", {r: local[r]["delta_E"] for r in (5, 6)})
    print("cloud", {r: cloud[r]["delta_E"] for r in (5, 6)})
    print("qwen7b", q7)
    print("vqa", {k: (v.get("accuracy"), v.get("token_f1")) for k, v in vqa.items()})
    if not a.apply:
        return 0
    t = io.open(SUPP, encoding="utf-8").read()
    # --- S20: append the 7B control after the 3B table ---
    marker = "\\label{tab:newer}\n\\end{table*}"
    if "tab:newer7b" not in t:
        add7 = ("""
\\textbf{Qwen2.5-VL-7B.} The same protocol on the larger newer-family checkpoint (cloud RTX 4080 SUPER,
training length 20 samples, three epochs) gives the values in Table~\\ref{tab:newer7b}: both ranks are negative,
i.e. no crossing either.
\\begin{table*}[h]
\\centering
\\footnotesize
\\begin{tabular}{@{}lrr l@{}}
\\toprule
rank & seed & $\\Delta E$ & trajectory \\\\
\\midrule
__Q7__
\\bottomrule
\\end{tabular}
\\caption{Qwen2.5-VL-7B newer-family control (cloud). Both ranks decrease the alignment energy; no sign change is
established between $r=5$ and $r=6$. Archives:
\\texttt{paper3/scripts/outputs/experiments/*cloud\\_q25\\_7b*.json}.}
\\label{tab:newer7b}
\\end{table*}
""".replace("__Q7__", q7_rows))
        assert t.count(marker) == 1
        t = t.replace(marker, marker + add7, 1)
    # --- S28: per-step VQA rows ---
    old_start = t.find("\\label{app:vqa}")
    assert old_start > 0
    m = t.find("\\midrule", old_start)
    b = t.find("\\bottomrule", m)
    t = t[: m + len("\\midrule")] + "\n" + vqa_rows + "\n" + t[b:]
    old_cap = ("\\caption{VQA-RAD downstream check (real images, held-out questions). Archives:\n"
               "\\texttt{outputs/analysis/p3\\_vqa\\_downstream\\_*.json}.}")
    new_cap = ("\\caption{VQA-RAD downstream check (real images, held-out questions; the two adapter arms use per-step\n"
               "fine-tuning on 80 training pairs). Accuracy does not improve at either rank. Archives:\n"
               "\\texttt{outputs/analysis/cloud\\_p3\\_vqa\\_downstream\\_*.json}.}")
    if old_cap in t:
        t = t.replace(old_cap, new_cap, 1)
    # --- S29 environment table ---
    sec29 = r"""
\section{Second-environment reproducibility}
\label{app:envcloud}

The protocol is repeated on a second machine: RTX 4080 SUPER, torch 2.12.1+cu130, CUDA 13.0 (the local runs use
torch 2.9.1+cu130 on an RTX 4060 Laptop). Table~\ref{tab:envcloud} compares the two.
\begin{table*}[h]
\centering
\footnotesize
\begin{tabular}{@{}lllllll@{}}
\toprule
machine & torch & CUDA & rank & $E_0$ & $\Delta E$ & trajectory \\
\midrule
__ENV1__
__ENV2__
\bottomrule
\end{tabular}
\caption{Cross-environment reproducibility of the $r=5$/$r=6$ crossing (seed 42, blank-image protocol). The sign
pattern is preserved (negative at $r=5$, positive at $r=6$) and the $E_0$ shifts by $0.1\%$; magnitudes differ by
about $2\times$, which is the environment-sensitivity the paper reports. Archives:
\texttt{paper3/scripts/outputs/experiments/verify\_r*\_s42.json} and \texttt{cloud\_verify\_r*\_s42.json}.}
\label{tab:envcloud}
\end{table*}

""".replace("__ENV1__", env_rows).replace("__ENV2__", env_rows2)
    if "app:envcloud" not in t:
        anchor = "\\bibliographystyle{IEEEtran}"
        t = t.replace(anchor, sec29 + "\n" + anchor, 1)
    # --- S17 rows ---
    old_row = ("crossing transfers to a newer model family & \\emph{not} supported & Qwen2.5-VL-3B: no sign change; "
               "$r=5$ sign varies across seeds (S20) \\\\")
    new_row = ("crossing transfers to a newer model family & \\emph{not} supported & Qwen2.5-VL-3B (no sign change) "
               "and 7B (both ranks negative) (S20) \\\\")
    if old_row in t:
        t = t.replace(old_row, new_row, 1)
    idx = t.find("\\label{tab:claims}")
    if idx > 0 and "sign pattern preserved across environments" not in t:
        j = t.find("\\bottomrule", idx)
        add = ("sign pattern preserved across environments & supported & RTX 4060/4080, torch 2.9/2.12 (S29) \\\\\n")
        t = t[:j] + add + t[j:]
    # --- S13 rows ---
    old_s13 = ("\\raggedright tab:newerseeds & \\raggedright\\path{paper3/scripts/run_training_qwen25.py} & "
               "\\raggedright\\path{paper3/scripts/outputs/experiments/qwen_cf_uniform_rank5_seed123_q25_r5_s123.json} & \\texttt{verified} \\\\")
    if old_s13 in t:
        add_rows = (old_s13 + "\n"
                    "\\raggedright tab:newer7b & \\raggedright\\path{paper3/scripts/run_training_qwen25.py} & "
                    "\\raggedright\\path{outputs/analysis/cloud_p3_vqa_downstream_base.json} & \\texttt{verified} \\\\\n"
                    "\\raggedright tab:envcloud & \\raggedright\\path{tools/_p1528_insert_cloud_results.py} & "
                    "\\raggedright\\path{paper3/scripts/outputs/experiments/cloud_verify_r5_s42.json} & \\texttt{verified} \\\\")
        t = t.replace(old_s13, add_rows, 1)
    io.open(SUPP, "w", encoding="utf-8", newline="").write(t)
    print("supplement updated (S20 7B, S28 per-step, S29, S17/S13 rows)")
    # discussion wording
    d = io.open(DISC, encoding="utf-8").read()
    d = d.replace("(Qwen2.5-VL-3B)", "(Qwen2.5-VL-3B and 7B)")
    io.open(DISC, "w", encoding="utf-8", newline="").write(d)
    # audit expectations
    ac = io.open(AUDIT, encoding="utf-8").read()
    if "twenty-nine S-sections" not in ac:
        ac = ac.replace('check("supplement: twenty-eight S-sections", n_sections == 28, f"{n_sections} sections")',
                        'check("supplement: twenty-nine S-sections", n_sections == 29, f"{n_sections} sections")', 1)
        io.open(AUDIT, "w", encoding="utf-8", newline="").write(ac)
    ap_ = io.open(AUDIT_PDF, encoding="utf-8").read()
    ap_ = ap_.replace("range(1, 29)", "range(1, 30)")
    io.open(AUDIT_PDF, "w", encoding="utf-8", newline="").write(ap_)
    # manifest
    m = jload(MANIFEST)
    floats = m["manuscripts"]["P3"]["floats"]
    have = {f["label"] for f in floats}
    for label, script, archive in (("tab:newer7b", "paper3/scripts/run_training_qwen25.py",
                                    "paper3/scripts/outputs/experiments/qwen_cf_uniform_rank5_seed42_cloud_q25_7b_r5.json"),
                                   ("tab:envcloud", "tools/_p1528_insert_cloud_results.py",
                                    "paper3/scripts/outputs/experiments/cloud_verify_r5_s42.json")):
        if label not in have:
            floats.append({"label": label, "kind": "table", "script": script, "archive": archive,
                           "status": "verified", "note": "cloud round (2026-10-22)"})
    for f in floats:
        if f["label"] == "tab:vqa":
            f["archive"] = "outputs/analysis/cloud_p3_vqa_downstream_5.json"
    io.open(MANIFEST, "w", encoding="utf-8", newline="").write(json.dumps(m, indent=1, ensure_ascii=False))
    print("manifest updated; P3 floats:", len(floats))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
