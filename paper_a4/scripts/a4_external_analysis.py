# -*- coding: utf-8 -*-
"""Summarise external public-checkpoint validation."""
import glob,io,json,os
import numpy as np
from scipy.stats import spearmanr
REPO=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
D=os.path.join(REPO,"outputs","a4","extra","external")
OUT=os.path.join(REPO,"outputs","a4","a4_external_analysis_2026-11-10.json")
def sp(a,b):
 a=np.asarray(a,float);b=np.asarray(b,float);m=np.isfinite(a)&np.isfinite(b)
 if m.sum()<3 or np.std(a[m])==0 or np.std(b[m])==0:return None
 return float(spearmanr(a[m],b[m]).correlation)
cells=[]
for f in sorted(glob.glob(os.path.join(D,"*.json"))):
 if os.path.basename(f)=="summary.json": continue
 d=json.load(open(f,encoding="utf-8")); cells.append(d)
out={"n_cells":len(cells),"cells":[]}
for c in cells:
 b=c["base"]["original"]; e=c["adapted"]["original"]
 row={"adapter":c["adapter"],"dataset":c["dataset"],"kind":c["kind"],
      "base_CG":b["CG"],"adapt_CG":e["CG"],"base_DG":b["DG"],"adapt_DG":e["DG"],"dCG":e["CG"]-b["CG"],"dDG":e["DG"]-b["DG"]}
 for k in ("classification_top1","R1_i2t","R1_t2i","ARI","R5_i2t"):
  if k in b and k in e: row["base_"+k]=b[k]; row["adapt_"+k]=e[k]; row["d_"+k]=e[k]-b[k]
 out["cells"].append(row)
# static correlation across adapted cells (all and held-out excluding DTD in-domain)
for scope,sub in [("all",out["cells"]),("heldout",[r for r in out["cells"] if r["dataset"]!="dtd"])]:
 out["static_"+scope]={}
 target="classification_top1" if sub and "adapt_classification_top1" in sub[0] else "R1_i2t"
 for m in ("adapt_CG","adapt_DG"):
  out["static_"+scope][m+"__"+target]=sp([r[m] for r in sub],[r["adapt_"+target] for r in sub])
 out["static_"+scope]["n"]=len(sub)
 # interventions not stored? adapted conditions exist; compute for later
json.dump(out,io.open(OUT,"w",encoding="utf-8"),indent=1)
lines=["# A4 external public-checkpoint validation (2026-11-10)","",
       "Cells: %d (4 public CLIP B/16 LoRA adapters x 5 datasets)."%len(cells),"",
       "| adapter | dataset | base CG | adapted CG | dCG | base i2t | adapted i2t |",
       "|---|---|---:|---:|---:|---:|---:|"]
for r in out["cells"]:
 lines.append("| %s | %s | %.3f | %.3f | %+.3f | %.1f | %.1f |"%(r["adapter"],r["dataset"],r["base_CG"],r["adapt_CG"],r["dCG"],r.get("base_R1_i2t",float("nan")),r.get("adapt_R1_i2t",float("nan"))))
lines += ["","Static Spearman (adapted):"]
for k,v in out["static_all"].items():
 if isinstance(v,float): lines.append("- all %s = %+.2f"% (k,v))
for k,v in out["static_heldout"].items():
 if isinstance(v,float): lines.append("- heldout %s = %+.2f"% (k,v))
io.open(os.path.join(REPO,"outputs","a4","A4_EXTERNAL_RESULTS_2026-11-10.md"),"w",encoding="utf-8",newline="").write("\n".join(lines)+"\n")
print("\n".join(lines[:25]))
