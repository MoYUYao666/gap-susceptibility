# -*- coding: utf-8 -*-
"""Summarize Flickr30k/POPE benchmark results for P3 v2."""
import collections, io, json, math, os, re, string
import numpy as np
REPO=os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
AN=os.path.join(REPO,"outputs","analysis")
def norm(s):
 s=str(s).lower().strip(); s=re.sub(r"[%s]"%re.escape(string.punctuation)," ",s); return " ".join(s.split())
def f1(r,h):
 rt=collections.Counter(norm(r).split()); ht=collections.Counter(norm(h).split()); c=sum((rt&ht).values())
 if c==0: return 0.0
 p=c/max(sum(ht.values()),1); rec=c/max(sum(rt.values()),1); return 2*p*rec/max(p+rec,1e-12)
def yesno(s):
 n=norm(s); m=re.search(r"\b(yes|no)\b",n); return m.group(1) if m else ("yes" if n.startswith("yes") else "no")
def load(task,arm):
 p=os.path.join(AN,f"p3_v2_benchmark_{task}_{arm}.json")
 if not os.path.exists(p): return None
 return json.load(io.open(p,encoding="utf-8"))
def boot(a,b,rng,n=20000):
 d=np.asarray(a)-np.asarray(b); idx=rng.integers(0,len(d),(n,len(d))); m=d[idx].mean(axis=1)
 return float(np.quantile(m,.025)),float(np.quantile(m,.975)),float(d.mean())
def main():
 rng=np.random.default_rng(20261112); out={}
 for task in ["flickr30k","coco5k","pope","marinelife","inat","dtd","scienceqa","mmbench"]:
  arms={a:load(task,a) for a in ["base","5","6"]}
  if any(v is None for v in arms.values()): print("missing",task); continue
  out[task]={}
  for a,d in arms.items():
   if task in ("flickr30k","coco5k"):
    out[task][a]={"n":len(d["refs"]),"token_f1":d["token_f1"],"bleu4":d["bleu4"]}
   else:
    out[task][a]={"n":len(d["refs"]),"accuracy":d["accuracy"]}
  if task in ("flickr30k","coco5k"):
   fs={a:[f1(r,h) for r,h in zip(arms["base"]["refs"],arms[a]["hypotheses"])] for a in arms}
   for a in ["5","6"]:
    lo,hi,delta=boot(fs[a],fs["base"],rng); out[task][f"{a}_minus_base"]={"token_f1_delta":delta,"ci95":[lo,hi]}
  else:
   def pred_label(task,s):
    n=norm(s)
    if task=="pope": return yesno(s)
    m=re.search(r"\b([abcde])\b",n); return m.group(1) if m else ""
   ps={a:[pred_label(task,h) for h in arms[a]["hypotheses"]] for a in arms}
   rs=[(yesno(r) if task=="pope" else norm(r)) for r in arms["base"]["refs"]]
   for a in ["5","6"]:
    x=[1.0 if p==r else 0.0 for p,r in zip(ps[a],rs)]; y=[1.0 if p==r else 0.0 for p,r in zip(ps["base"],rs)]
    lo,hi,delta=boot(x,y,rng); out[task][f"{a}_minus_base"]={"accuracy_delta":delta,"ci95":[lo,hi]}
 p=os.path.join(AN,"p3_v2_benchmark_summary.json"); io.open(p,"w",encoding="utf-8",newline="").write(json.dumps(out,indent=1)+"\n")
 print(json.dumps(out,indent=1))
if __name__=="__main__": main()
