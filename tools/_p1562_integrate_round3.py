# -*- coding: utf-8 -*-
r"""Integrate cloud round 3: VQA 1793-full (S28), Dolly instruction family (S40), Qwen2-VL third family (S41)."""
import glob
import io
import json
import os
import shutil
import statistics as st

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = os.path.join(REPO, "paper3", "paper_ieee")
SUPP = os.path.join(BASE, "supplementary", "supplementary.tex")
AN = os.path.join(REPO, "outputs", "analysis")
EXP = os.path.join(REPO, "paper3", "scripts", "outputs", "experiments")
MANIFEST = os.path.join(REPO, "docs", "provenance_manifest.json")
bs = chr(92)

# --- copy artifacts ---
for k in ("base", "5", "6"):
    src = os.path.join(REPO, "cloud_round3", "outputs", "analysis", "p3_vqa_downstream_%s.json" % k)
    if os.path.exists(src):
        shutil.copy2(src, os.path.join(AN, "cloud_vqa1793_%s.json" % k))
dolly = []
for r in (4, 5, 6, 7):
    for s in (42, 123):
        for f in glob.glob(os.path.join(REPO, "cloud_round3", "paper3", "scripts", "outputs",
                                        "experiments", "verify_r%d_s%d_lr5e-05_nw_float1_adamw_e3_bcuniform.json" % (r, s))):
            dst = os.path.join(EXP, "cloud_dolly_verify_r%d_s%d.json" % (r, s))
            shutil.copy2(f, dst)
            dolly.append((r, s, json.load(io.open(dst, encoding="utf-8"))["delta_E"]))
print("dolly:", dolly)

# --- S28 rebuild ---
vqa = {k: json.load(io.open(os.path.join(AN, "cloud_vqa1793_%s.json" % k), encoding="utf-8")) for k in ("base", "5", "6")}
rows28 = "\n".join("%s & %d & %.4f & %.4f %s" % (
    ("base" if k == "base" else "r=%s (per-step)" % k), v["meta"]["n_eval"], v["accuracy"], v["token_f1"], bs * 2)
    for k, v in vqa.items())
s28 = (r"""\section{VQA-RAD downstream check}
\label{app:vqa}

The LLaVA adapters are fine-tuned on the full VQA-RAD training split (1434 training pairs per epoch, three epochs,
4302 optimizer steps) and evaluated on 300 held-out questions; answers are compared by exact match and token F1,
with the base model as control. Table~\ref{tab:vqa} reports the results.
\begin{table*}[h]
\centering
\footnotesize
\begin{tabular}{@{}lrrr@{}}
\toprule
arm & $n$ & accuracy & token F1 \\
\midrule
""" + rows28 + r"""
\bottomrule
\end{tabular}
\caption{VQA-RAD downstream check at scale (real images, 300 held-out questions). Both ranks improve over the base
model, but there is no rank ordering consistent with the alignment-energy picture, so the task check is reported as a
small downstream gain rather than evidence for an allocation advantage. Archive:
\texttt{outputs/analysis/cloud\_vqa1793\_*.json}.}
\label{tab:vqa}
\end{table*}""")

# --- S40 Dolly ---
rows40 = []
for r in (4, 5, 6, 7):
    vals = [d for rr, s, d in dolly if rr == r]
    rows40.append("%d & %d & %+.1f & [%+.1f, %+.1f] %s" % (r, len(vals), st.mean(vals), min(vals), max(vals), bs * 2))
s40 = (r"""\section{Instruction-family replication on Dolly-15k}
\label{app:dolly}

The blank-image protocol is repeated on a different instruction family, Dolly-15k (r=4--7, two seeds each).
\begin{table*}[h]
\centering
\footnotesize
\begin{tabular}{@{}lrrr@{}}
\toprule
rank & $n$ & mean $\Delta E$ & range \\
\midrule
""" + "\n".join(rows40) + r"""
\bottomrule
\end{tabular}
\caption{Dolly-15k instruction-family replication: $r=4$ and $r=5$ stay negative while $r=6$ and $r=7$ turn positive,
i.e. the crossing pattern repeats on a different instruction corpus. Archive:
\texttt{paper3/scripts/outputs/experiments/cloud\_dolly\_verify\_r*\_s*.json}.}
\label{tab:dolly}
\end{table*}""")

# --- S41 third family ---
q = {r: json.load(io.open(os.path.join(AN, "cloud_qwen_cf_uniform_rank%d_seed42_qwen2vl.json" % r), encoding="utf-8"))
     for r in (5, 6)}
rows41 = "\n".join("%d & %+.1f & %s %s" % (r, q[r]["delta_E"], q[r]["E"], bs * 2) for r in (5, 6))
s41 = (r"""\section{Third checkpoint family: Qwen2-VL-2B}
\label{app:thirdfamily}

LLaVA-OneVision-0.5B could not be evaluated with the current transformer stack (its released 1.5-processor config
does not load under transformers 5.16), so the third-family control uses Qwen2-VL-2B, a different checkpoint family
from both LLaVA-1.5 and Qwen2.5-VL, under the same blank-image protocol.
\begin{table*}[h]
\centering
\footnotesize
\begin{tabular}{@{}lrr@{}}
\toprule
rank & $\Delta E$ & trajectory \\
\midrule
""" + rows41 + r"""
\bottomrule
\end{tabular}
\caption{Qwen2-VL-2B third-family control: both ranks decrease the alignment energy (no sign change), consistent with
the newer-family controls and again bounding the crossing claim to LLaVA-1.5. Archive:
\texttt{outputs/analysis/cloud\_qwen\_cf\_uniform\_rank*\_seed42\_qwen2vl.json}.}
\label{tab:thirdfamily}
\end{table*}""")

t = io.open(SUPP, encoding="utf-8").read()


def replace_section(t, title, new_block):
    head = "\\section{" + title + "}"
    start = t.find(head)
    assert start >= 0, title
    nxt = t.find("\\section{", start + len(head))
    end = nxt if nxt >= 0 else t.find("\\bibliographystyle", start)
    return t[:start] + new_block + "\n" + t[end:]


t = replace_section(t, "VQA-RAD downstream check", s28)
if "app:dolly" not in t:
    t = t.replace("\\bibliographystyle{IEEEtran}", s40 + "\n\n" + s41 + "\n\n\\bibliographystyle{IEEEtran}", 1)
# S17 rows
idx = t.find("\\label{tab:claims}")
j = t.find("\\bottomrule", idx)
add = ("crossing pattern on a second instruction family & supported for Dolly-15k & r4/r5 negative, r6/r7 "
       "positive (S40) \\\\\nthird checkpoint family & no sign change on Qwen2-VL-2B & reported, bounds the claim "
       "(S41) \\\\\n")
t = t[:j] + add + t[j:]
io.open(SUPP, "w", encoding="utf-8", newline="").write(t)
print("S28/S40/S41 written")

mf = json.load(io.open(MANIFEST, encoding="utf-8"))
floats = mf["manuscripts"]["P3"]["floats"]
have = {f["label"] for f in floats}
for label, script, archive in (
        ("tab:dolly", "paper3/scripts/run_training.py", "outputs/analysis/cloud_dolly_verify_r5_s42.json"),
        ("tab:thirdfamily", "paper3/scripts/run_training_qwen.py",
         "outputs/analysis/cloud_qwen_cf_uniform_rank5_seed42_qwen2vl.json")):
    if label not in have:
        floats.append({"label": label, "kind": "table", "script": script, "archive": archive,
                       "status": "verified", "note": "cloud round 3"})
for f in floats:
    if f["label"] == "tab:vqa":
        f["archive"] = "outputs/analysis/cloud_vqa1793_5.json"
json.dump(mf, io.open(MANIFEST, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print("manifest floats:", len(floats))
