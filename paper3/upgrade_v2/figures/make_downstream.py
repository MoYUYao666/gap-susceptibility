# -*- coding: utf-8 -*-
"""P3 v2 downstream figure: VQA-RAD metrics for base/r5/r6."""
import os
import matplotlib as mpl
mpl.use("Agg")
mpl.rcParams.update({"font.family":"serif","font.serif":["Times New Roman","Times","STIXGeneral"],
 "mathtext.fontset":"stix","pdf.fonttype":42,"ps.fonttype":42,"axes.unicode_minus":False,"font.size":8})
import matplotlib.pyplot as plt
import numpy as np
REPO=os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
FIG=os.path.join(REPO,"paper3","upgrade_v2","figures")
labels=["base","r=5","r=6"]
acc=[0.3304,0.3880,0.3348]
f1=[0.3553,0.4217,0.3983]
x=np.arange(len(labels)); w=0.36
fig,ax=plt.subplots(figsize=(4.2,2.7))
b1=ax.bar(x-w/2,acc,w,label="exact-match accuracy",color="#4C72B0",edgecolor="black",linewidth=0.4)
b2=ax.bar(x+w/2,f1,w,label="token F1",color="#DD8452",edgecolor="black",linewidth=0.4)
for bars in (b1,b2):
    for rect in bars:
        ax.text(rect.get_x()+rect.get_width()/2,rect.get_height()+0.008,"%.3f"%rect.get_height(),
                ha="center",va="bottom",fontsize=6.5)
ax.set_xticks(x); ax.set_xticklabels(labels); ax.set_ylabel("score"); ax.set_ylim(0,0.50)
ax.legend(frameon=False,fontsize=7,loc="upper left")
ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
ax.set_title("VQA-RAD, 451 held-out questions",fontsize=8.5)
fig.tight_layout(pad=0.2)
fig.savefig(os.path.join(FIG,"fig3_downstream.pdf"),bbox_inches="tight",pad_inches=0.02)
fig.savefig(os.path.join(FIG,"fig3_downstream.png"),dpi=300,bbox_inches="tight",pad_inches=0.02)
print("written")
