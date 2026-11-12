# -*- coding: utf-8 -*-
"""Held-out downstream check for P3 v2: captioning and instruction following.

The previous 4-example checks evaluated the same first rows used to train the adapters. This script uses held-out
examples and reports per-example generations plus token F1 and BLEU-4.
"""
import argparse, collections, hashlib, io, json, math, os, re, string, sys, time
import numpy as np
import pandas as pd
import torch
from PIL import Image

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
MODEL = os.path.join(REPO, "models", "llava-hf")
AN = os.path.join(REPO, "outputs", "analysis")
CAPTION_JSON = os.path.join(REPO, "data", "marine_captions", "captions.json")
CAPTION_IMAGES = os.path.join(REPO, "data", "marine_captions")
INSTR_PARQUET = os.path.join(REPO, "paper3", "data", "train-00000-of-00001-a09b74b3ef9c3b56.parquet")
CAPTION_ADAPTERS = os.path.join(REPO, "outputs", "p3_caption_adapters")
INSTR_ADAPTERS = os.path.join(REPO, "outputs", "p3_instr_adapters")

def norm(s):
    s = str(s).lower().strip()
    s = re.sub(r"[%s]" % re.escape(string.punctuation), " ", s)
    return " ".join(s.split())

def token_f1(refs, hyps):
    vals=[]
    for r,h in zip(refs,hyps):
        rt=collections.Counter(norm(r).split()); ht=collections.Counter(norm(h).split())
        c=sum((rt & ht).values())
        if c==0: vals.append(0.0); continue
        p=c/max(sum(ht.values()),1); rec=c/max(sum(rt.values()),1)
        vals.append(2*p*rec/max(p+rec,1e-12))
    return float(np.mean(vals))

def bleu4(refs, hyps):
    prec=[]
    for n in range(1,5):
        num=den=0
        for r,h in zip(refs,hyps):
            rt=norm(r).split(); ht=norm(h).split()
            rc=collections.Counter(tuple(rt[i:i+n]) for i in range(len(rt)-n+1))
            hc=collections.Counter(tuple(ht[i:i+n]) for i in range(len(ht)-n+1))
            num += sum(min(c,rc[g]) for g,c in hc.items())
            den += max(len(ht)-n+1,0)
        prec.append(num/den if den else 0.0)
    if min(prec)<=0: return 0.0
    return float(math.exp(sum(math.log(p) for p in prec)/4.0))

def load_arm(task, arm):
    from transformers import AutoProcessor, BitsAndBytesConfig, LlavaForConditionalGeneration
    from peft import PeftModel
    quant=BitsAndBytesConfig(load_in_4bit=True,bnb_4bit_compute_dtype=torch.float16,bnb_4bit_use_double_quant=True)
    proc=AutoProcessor.from_pretrained(MODEL)
    base=LlavaForConditionalGeneration.from_pretrained(MODEL,quantization_config=quant,device_map="auto")
    model=base
    adir=None
    if arm != "base":
        root=CAPTION_ADAPTERS if task=="caption" else INSTR_ADAPTERS
        adir=os.path.join(root,"r"+str(arm))
        if not os.path.exists(os.path.join(adir,"adapter_config.json")):
            raise FileNotFoundError(adir)
        model=PeftModel.from_pretrained(base,adir,is_trainable=False)
    model.eval()
    return proc,model,adir

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--task",choices=["caption","instruction"],required=True)
    ap.add_argument("--arm",default="base")
    ap.add_argument("--n",type=int,default=100)
    ap.add_argument("--start",type=int,default=20)
    args=ap.parse_args()
    os.environ["KMP_DUPLICATE_LIB_OK"]="TRUE"; os.environ["HF_HUB_OFFLINE"]="1"
    out_path=os.path.join(AN,f"p3_v2_heldout_{args.task}_{args.arm}.json")
    if args.task=="caption":
        d=json.load(io.open(CAPTION_JSON,encoding="utf-8")); refs_all=d["captions"]
        idx=list(range(args.start,min(args.start+args.n,len(refs_all))))
        rows=[(i, os.path.join(CAPTION_IMAGES,f"{i:04d}.jpg"), "Describe the image.", refs_all[i]) for i in idx]
    else:
        df=pd.read_parquet(INSTR_PARQUET)
        idx=list(range(args.start,min(args.start+args.n,len(df))))
        rows=[(i, None, str(df.iloc[i]["instruction"]) + ((" " + str(df.iloc[i]["input"])) if str(df.iloc[i].get("input","")) else ""), str(df.iloc[i]["output"])) for i in idx]
    proc,model,adir=load_arm(args.task,args.arm)
    hyps=[]; refs=[]; t0=time.time()
    for i,img_path,prompt,ref in rows:
        if img_path is not None:
            img=Image.open(img_path).convert("RGB")
        else:
            img=Image.new("RGB",(336,336),"white")
        conv=[{"role":"user","content":[{"type":"image"},{"type":"text","text":prompt}]}]
        p=proc.apply_chat_template(conv,add_generation_prompt=True)
        inp=proc(text=p,images=img,return_tensors="pt").to(model.device)
        with torch.inference_mode():
            out=model.generate(**inp,max_new_tokens=64,do_sample=False)
        gen=proc.tokenizer.decode(out[0][inp["input_ids"].shape[1]:],skip_special_tokens=True).strip()
        hyps.append(gen); refs.append(ref)
        if len(hyps)%10==0: print(args.task,args.arm,len(hyps),flush=True)
    res={"meta":{"task":args.task,"arm":args.arm,"n":len(hyps),"start":args.start,"model":MODEL,
                 "adapter":adir,"source":CAPTION_JSON if args.task=="caption" else INSTR_PARQUET,
                 "instruction":"held-out examples; adapters were trained on the first 20 examples of the same archive",
                 "seed":42,"elapsed_min":round((time.time()-t0)/60,2)},
         "refs":refs,"hypotheses":hyps,"token_f1":token_f1(refs,hyps),"bleu4":bleu4(refs,hyps),
         "exact_match":float(np.mean([norm(a)==norm(b) for a,b in zip(refs,hyps)]))}
    io.open(out_path,"w",encoding="utf-8",newline="").write(json.dumps(res,indent=1)+"\n")
    print("wrote",os.path.relpath(out_path,REPO),res["token_f1"],res["bleu4"],flush=True)

if __name__=="__main__": main()
