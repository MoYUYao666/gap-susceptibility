# -*- coding: utf-8 -*-
"""Build the held-out caption/instruction table from p3_v2_heldout_*.json."""
import collections, io, json, math, os, re, string
import numpy as np
REPO=os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
AN=os.path.join(REPO,"outputs","analysis")
def norm(s):
 s=str(s).lower().strip(); s=re.sub(r"[%s]"%re.escape(string.punctuation)," ",s); return " ".join(s.split())
def f1_pair(r,h):
 rt=collections.Counter(norm(r).split()); ht=collections.Counter(norm(h).split()); c=sum((rt&ht).values())
 if c==0: return 0.0
 p=c/max(sum(ht.values()),1); rec=c/max(sum(rt.values()),1); return 2*p*rec/max(p+rec,1e-12)
def boot_ci(a,b,rng,n=20000):
 d=np.asarray(a)-np.asarray(b); idx=rng.integers(0,len(d),(n,len(d))); m=d[idx].mean(axis=1)
 return float(np.quantile(m,.025)),float(np.quantile(m,.975)),float(d.mean())
def main():
 rng=np.random.default_rng(20261112); out={}
 for task in ["caption","instruction"]:
  arms={}
  for arm in ["base","5","6"]:
   p=os.path.join(AN,f"p3_v2_heldout_{task}_{arm}.json")
   if not os.path.exists(p): raise SystemExit(f"missing {p}")
   arms[arm]=json.load(io.open(p,encoding="utf-8"))
  base=arms["base"]; refs=base["refs"]
  out[task]={}
  for arm,d in arms.items():
   f1=[f1_pair(r,h) for r,h in zip(refs,d["hypotheses"])]
   out[task][arm]={"n":len(f1),"token_f1":float(np.mean(f1)),"bleu4":float(d["bleu4"]),
                   "exact_match":float(d["exact_match"]),"f1s":f1}
  for arm in ["5","6"]:
   a=out[task][arm]["f1s"]; b=out[task]["base"]["f1s"]
   lo,hi,delta=boot_ci(a,b,rng)
   out[task][f"{arm}_minus_base"]={"token_f1_delta":delta,"ci95":[lo,hi]}
 p=os.path.join(AN,"p3_v2_heldout_summary.json")
 io.open(p,"w",encoding="utf-8",newline="").write(json.dumps(out,indent=1)+"\n")
 for task in out:
  print("\n",task)
  for arm in ["base","5","6"]:
   print(arm,out[task][arm]["n"],"F1",round(out[task][arm]["token_f1"],4),"BLEU4",round(out[task][arm]["bleu4"],4))
  for arm in ["5","6"]:
   print(arm+"-base",out[task][f"{arm}_minus_base"])
if __name__=="__main__": main()
