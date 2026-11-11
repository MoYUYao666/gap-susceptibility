# -*- coding: utf-8 -*-
"""Empirical test of a simple spectral competition bound on frozen class features."""
from __future__ import annotations
import glob, io, json, os
import numpy as np
from scipy.stats import spearmanr

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FEAT = os.path.join(REPO, "outputs", "a4", "features")
OUT = os.path.join(REPO, "outputs", "a4", "a4_spectral_bound_2026-11-10.json")


def sp(a, b):
    a=np.asarray(a,float); b=np.asarray(b,float); m=np.isfinite(a)&np.isfinite(b)
    if m.sum()<3 or np.std(a[m])==0 or np.std(b[m])==0: return None
    return float(spearmanr(a[m],b[m]).correlation)


def main():
    cells=[]
    for f in sorted(glob.glob(os.path.join(FEAT,"*.npz"))):
        base=os.path.basename(f)[:-4]
        enc,ds=base.split("__",1)
        if ds not in ("dtd","inat","nksid"): continue
        z=np.load(f,allow_pickle=True); img=z["img"].astype(float); txt=z["txt"].astype(float); y=z["labels"]
        if img.ndim!=2 or txt.ndim!=2: continue
        # normalize
        img=img/np.maximum(np.linalg.norm(img,axis=1,keepdims=True),1e-12)
        txt=txt/np.maximum(np.linalg.norm(txt,axis=1,keepdims=True),1e-12)
        s=img@txt.T; n,C=s.shape
        pos=s[np.arange(n),y]; s2=s.copy(); s2[np.arange(n),y]=-1e9; neg=s2.max(1)
        margin=pos-neg
        # text covariance and spectral quantities
        tc=txt-txt.mean(0); cov=(tc.T@tc)/max(1,len(tc)-1)
        lam=np.clip(np.linalg.eigvalsh(cov),1e-12,None); p=lam/lam.sum()
        er=float(np.exp(-(p*np.log(p)).sum())); lmax=float(lam[-1])
        # average q^T Sigma q over image queries
        qvar=float(np.mean(np.einsum("ij,jk,ik->i",img,cov,img)))
        bound=float(np.sqrt(2*qvar*np.log(max(2,C-1))))
        cells.append({"cell":base,"encoder":enc,"dataset":ds,"n":n,"n_classes":C,
                      "eff_rank":er,"lambda_max":lmax,"query_var":qvar,
                      "mean_margin":float(margin.mean()),"mean_negative":float(neg.mean()),
                      "bound":bound,"mean_top1":float((s.argmax(1)==y).mean()*100)})
    out={"n_cells":len(cells),"cells":cells}
    out["rho_effrank_margin"]=sp([c["eff_rank"] for c in cells],[c["mean_margin"] for c in cells])
    out["rho_effrank_top1"]=sp([c["eff_rank"] for c in cells],[c["mean_top1"] for c in cells])
    out["rho_bound_negative"]=sp([c["bound"] for c in cells],[c["mean_negative"] for c in cells])
    out["rho_lmax_negative"]=sp([c["lambda_max"] for c in cells],[c["mean_negative"] for c in cells])
    json.dump(out,io.open(OUT,"w",encoding="utf-8"),indent=1)
    lines=["# A4 spectral competition bound: empirical check (2026-11-10)","",
           "Frozen class cells: %d."%len(cells),"",
           "- rho(effective rank, mean top-1 margin) = %s"%out["rho_effrank_margin"],
           "- rho(effective rank, top-1 accuracy) = %s"%out["rho_effrank_top1"],
           "- rho(bound, mean top negative score) = %s"%out["rho_bound_negative"],
           "- rho(lambda_max, mean top negative score) = %s"%out["rho_lmax_negative"],"",
           "| cell | n | classes | eff. rank | lambda_max | mean margin | mean neg | bound | top-1 |",
           "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for c in cells:
        lines.append("| %s | %d | %d | %.1f | %.3f | %.3f | %.3f | %.3f | %.1f |"%(c["cell"],c["n"],c["n_classes"],c["eff_rank"],c["lambda_max"],c["mean_margin"],c["mean_negative"],c["bound"],c["mean_top1"]))
    io.open(os.path.join(REPO,"outputs","a4","A4_SPECTRAL_BOUND_2026-11-10.md"),"w",encoding="utf-8",newline="").write("\n".join(lines)+"\n")
    print("wrote",OUT)
    print("\n".join(lines[:12]))


if __name__=="__main__":
    main()
