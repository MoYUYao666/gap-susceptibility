# -*- coding: utf-8 -*-
"""Summarize held-out caption/instruction results with paired bootstrap CIs."""
import argparse, glob, io, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
REPO=os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
AN=os.path.join(REPO,"outputs","analysis")
def load(task,arm):
 p=os.path.join(AN,f"p3_v2_heldout_{task}_{arm}.json")
 if not os.path.exists(p): return None
 return json.load(io.open(p,encoding="utf-8"))
def boot_ci(a,b,rng,n=20000):
 d=np.asarray(a)-np.asarray(b); idx=rng.integers(0,len(d),(n,len(d)))
 m=d[idx].mean(axis=1); return float(np.quantile(m,0.025)),float(np.quantile(m,0.975)),float(d.mean())
def main():
 rng=np.random.default_rng(20261112); out={}
 for task in ["caption","instruction"]:
  arms={a:load(task,a) for a in ["base","5","6"]}
  if any(v is None for v in arms.values()): print("missing",task); continue
  out[task]={}
  for a,d in arms.items():
   out[task][a]={"n":d["meta"]["n"],"token_f1":d["token_f1"],"bleu4":d["bleu4"],"exact_match":d["exact_match"]}
  for a in ["5","6"]:
   out[task][f"{a}_minus_base"]={
    "token_f1":{"delta":out[task][a]["token_f1"]-out[task]["base"]["token_f1"]},
    "bleu4":{"delta":out[task][a]["bleu4"]-out[task]["base"]["bleu4"]}}
   # per-example differences need token_f1 arrays; recompute from refs/hyps using metric functions
   from heldout_downstream import token_f1, bleu4
   refs=arms["base"]["refs"]; 
   # arrays of per-example metric not directly available; use bootstrap over examples by recomputing with same refs/hyps
   def f1s(d):
    return [token_f1([r],[h]) for r,h in zip(d["refs"],d["hypotheses"])]
   def b4s(d):
    return [bleu4([r],[h]) for r,h in zip(d["refs"],d["hypotheses"])]
   out[task][f"{a}_minus_base"]["token_f1"]["ci95"]=boot_ci(f1s(arms[a]),f1s(arms["base"]),rng)[:2]
   out[task][f"{a}_minus_base"]["bleu4"]["ci95"]=boot_ci(b4s(arms[a]),b4s(arms["base"]),rng)[:2]
 p=os.path.join(AN,"p3_v2_heldout_summary.json")
 io.open(p,"w",encoding="utf-8",newline="").write(json.dumps(out,indent=1)+"\n")
 print(json.dumps(out,indent=1))
if __name__=="__main__": main()
