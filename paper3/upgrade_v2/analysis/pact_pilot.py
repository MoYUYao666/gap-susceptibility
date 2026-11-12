# -*- coding: utf-8 -*-
"""PACT pilot: protocol-aware concordance of Gamma allocations on the reference-batch sweep."""
import io, json, os, itertools
import numpy as np
from scipy.stats import kendalltau

REPO=os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
src=os.path.join(REPO,"outputs","analysis","p3_gamma_batch_sensitivity.json")
d=json.load(io.open(src,encoding="utf-8"))
conds=d["conditions"]
blocks=sorted(conds[0]["ranks"])
rows=[]
for a,b in itertools.combinations(conds,2):
    va=[a["ranks"][k] for k in blocks]; vb=[b["ranks"][k] for k in blocks]
    tau=float(kendalltau(va,vb).correlation)
    rows.append({"protocol_a":"n=%d/draw=%d"%(a["n"],a["draw"]),
                 "protocol_b":"n=%d/draw=%d"%(b["n"],b["draw"]),
                 "kendall_tau":tau})
taus=[r["kendall_tau"] for r in rows]
out={"source":os.path.relpath(src,REPO),"blocks":blocks,"n_protocols":len(conds),
     "pairs":rows,"pact_min":float(min(taus)),"pact_mean":float(np.mean(taus)),
     "pact_max":float(max(taus)),
     "interpretation":"Pilot PACT; only four reference-batch conditions, not the full audit."}
dst=os.path.join(REPO,"outputs","analysis","p3_pact_pilot.json")
io.open(dst,"w",encoding="utf-8",newline="").write(json.dumps(out,indent=1)+"\n")
lines=["# PACT pilot (2026-11-12)","",
       "Source: `%s`"%out["source"],"",
       "Four reference-batch protocols; allocations are the archived Gamma rank vectors.","",
       "| pair | Kendall tau |","|---|---:|"]
for r in rows: lines.append("| %s vs %s | %+.3f |"%(r["protocol_a"],r["protocol_b"],r["kendall_tau"]))
lines += ["", "PACT min = **%+.3f**, mean = **%+.3f**, max = **%+.3f**."%(out["pact_min"],out["pact_mean"],out["pact_max"]),
          "", "This is a pilot, not the full protocol audit; it shows how the metric will be reported."]
io.open(os.path.join(REPO,"docs","P3_PACT_PILOT_2026-11-12.md"),"w",encoding="utf-8",newline="").write("\n".join(lines)+"\n")
print("wrote",dst)
