# -*- coding: utf-8 -*-
"""P3 v2 conceptual and PACT figures."""
import json, io, os
import matplotlib as mpl
mpl.use("Agg")
mpl.rcParams.update({"font.family":"serif","font.serif":["Times New Roman","Times","STIXGeneral"],
 "mathtext.fontset":"stix","pdf.fonttype":42,"ps.fonttype":42,"axes.unicode_minus":False,
 "font.size":8,"axes.labelsize":8})
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

REPO=os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
FIG=os.path.join(REPO,"paper3","upgrade_v2","figures")

def pact_heatmap():
    d=json.load(io.open(os.path.join(REPO,"outputs","analysis","p3_pact_pilot.json"),encoding="utf-8"))
    labels=sorted({r["protocol_a"] for r in d["pairs"]} | {r["protocol_b"] for r in d["pairs"]})
    idx={v:i for i,v in enumerate(labels)}; n=len(labels); m=np.eye(n)
    for r in d["pairs"]:
        i,j=idx[r["protocol_a"]],idx[r["protocol_b"]]; m[i,j]=m[j,i]=r["kendall_tau"]
    fig,ax=plt.subplots(figsize=(3.6,3.1))
    im=ax.imshow(m,vmin=-1,vmax=1,cmap="RdBu_r")
    ax.set_xticks(range(n)); ax.set_yticks(range(n))
    ax.set_xticklabels([x.replace("/draw="," / d") for x in labels],rotation=35,ha="right",fontsize=7)
    ax.set_yticklabels([x.replace("/draw="," / d") for x in labels],fontsize=7)
    for i in range(n):
        for j in range(n):
            ax.text(j,i,"%.2f"%m[i,j],ha="center",va="center",fontsize=6.5,
                    color="white" if abs(m[i,j])>0.75 else "black")
    cb=fig.colorbar(im,ax=ax,fraction=0.046,pad=0.04); cb.ax.tick_params(labelsize=7)
    ax.set_title("PACT pilot: pairwise Kendall $\\tau$",fontsize=8.5)
    fig.tight_layout(pad=0.15)
    fig.savefig(os.path.join(FIG,"fig2_pact_pilot.pdf"),bbox_inches="tight",pad_inches=0.02)
    fig.savefig(os.path.join(FIG,"fig2_pact_pilot.png"),dpi=300,bbox_inches="tight",pad_inches=0.02)
    plt.close(fig)

if __name__=="__main__":
    pact_heatmap(); print("figure written",FIG)
