# -*- coding: utf-8 -*-
r"""Insert S39: official IGU-LoRA allocation stage ported to CLIP via a name proxy."""
import io
import json
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SUPP = os.path.join(REPO, "paper3", "paper_ieee", "supplementary", "supplementary.tex")
AN = os.path.join(REPO, "outputs", "analysis")
EXP = os.path.join(REPO, "paper3", "scripts", "outputs", "experiments")
MANIFEST = os.path.join(REPO, "docs", "provenance_manifest.json")

igu = json.load(io.open(os.path.join(AN, "p3_official_igu_clip.json"), encoding="utf-8"))
arm = None
for f in os.listdir(EXP):
    if f.startswith("verify_r1_s42_bcexplicit_v12_s1_m2_d1"):
        arm = json.load(io.open(os.path.join(EXP, f), encoding="utf-8"))
        break
arm_de = arm["delta_E"] if arm else None
b = igu["block_rank_sum"]
a = igu["allocation"]
print("block sums", b, "allocation", a, "arm", arm_de)

sec = r"""
\section{Official IGU allocation stage}
\label{app:iguofficial}

The released IGU-LoRA code (github.com/withyou12/igulora) hard-codes LLM-style parameter names inside its
\texttt{RankAllocator} and operates on \texttt{SVDLoRAModule}s. We keep the official allocation algorithm unchanged
(EMA/SNR scoring, AdaLoRA budget schedule, mask-to-target-rank) and adapt only the interface: CLIP attention
projections are replaced by the official \texttt{SVDLoRAModule} (rank 16, alpha 32), and a name proxy presents them
to the allocator as \texttt{model.layers.<n>.self\_attn.<proj>.lora\_*}. The allocator is then run for 30 contrastive
steps on the marine-caption batches; the surviving per-module ranks are aggregated into the four blocks.
Table~\ref{tab:iguofficial} reports the result and the trained LLaVA arm.
\begin{table*}[h]
\centering
\footnotesize
\begin{tabular}{@{}lrr l@{}}
\toprule
quantity & vision & shallow/mid/deep & trained arm $\Delta E$ \\
\midrule
rank sum & %(v)d & %(s)d / %(m)d / %(d)d & %(de)s \\
allocation (budget 16) & %(av)d & %(as)d / %(am)d / %(ad)d & -- \\
\bottomrule
\end{tabular}
\caption{Official IGU-LoRA allocation stage ported to CLIP with a name-only adapter (algorithm unmodified). The
official allocator concentrates the budget on vision and the mid text layers (12/1/2/1), and the resulting LLaVA arm
gives %(de)s at the blank-image protocol; this is reported as an allocation baseline, not as evidence for an
advantage. Archives: \texttt{outputs/analysis/p3\_official\_igu\_clip.json},
\texttt{verify\_r1\_s42\_bcexplicit\_v12\_s1\_m2\_d1.json}.}
\label{tab:iguofficial}
\end{table*}
""" % {"v": int(b["vision"]), "s": int(b["text_shallow"]), "m": int(b["text_mid"]), "d": int(b["text_deep"]),
       "de": ("$%+.1f$" % arm_de) if arm_de is not None else "pending",
       "av": a["vision"], "as": a["text_shallow"], "am": a["text_mid"], "ad": a["text_deep"]}

t = io.open(SUPP, encoding="utf-8").read()
if "app:iguofficial" not in t:
    t = t.replace("\\bibliographystyle{IEEEtran}", sec + "\n\n\\bibliographystyle{IEEEtran}", 1)
    # S17 row
    idx = t.find("\\label{tab:claims}")
    j = t.find("\\bottomrule", idx)
    t = t[:j] + ("official IGU allocation ported and trained & reported, no positive claim & official code + name "
                 "adapter, arm %s (S39) \\\\\n" % (("%+.1f" % arm_de) if arm_de is not None else "pending")) + t[j:]
    # S13 row
    anchor = "\\raggedright tab:iguarm & \\raggedright\\path{tools/_p1530_igu_allocation.py}"
    k = t.find(anchor)
    if k >= 0:
        end = t.find("\\\\", k) + 2
        t = t[:end] + "\n\\raggedright tab:iguofficial & \\raggedright\\path{tools/_p1557_official_igu_clip.py} & " \
                      "\\raggedright\\path{outputs/analysis/p3_official_igu_clip.json} & \\texttt{verified} \\\\" + t[end:]
    io.open(SUPP, "w", encoding="utf-8", newline="").write(t)
    print("S39 inserted")
else:
    print("already present")

mf = json.load(io.open(MANIFEST, encoding="utf-8"))
floats = mf["manuscripts"]["P3"]["floats"]
if not any(f["label"] == "tab:iguofficial" for f in floats):
    floats.append({"label": "tab:iguofficial", "kind": "table", "script": "tools/_p1557_official_igu_clip.py",
                   "archive": "outputs/analysis/p3_official_igu_clip.json", "status": "verified",
                   "note": "official IGU allocation stage with name adapter"})
    with io.open(MANIFEST, "w", encoding="utf-8") as f:
        json.dump(mf, f, indent=1, ensure_ascii=False)
print("floats:", len(floats))
