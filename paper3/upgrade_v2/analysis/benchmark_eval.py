# -*- coding: utf-8 -*-
"""Standard benchmark evaluation for P3 v2: Flickr30k/COCO captions, POPE and MarineLife-16k VQA."""
import argparse, ast, collections, io, json, math, os, re, string, sys, time, zipfile
import numpy as np
import pandas as pd
import torch
from PIL import Image

REPO=os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
AN=os.path.join(REPO,"outputs","analysis")
MODEL=os.path.join(REPO,"models","llava-hf")
FLICKR_CSV=os.path.join(REPO,"data","a4_raw","flickr30k","flickr_annotations_30k.csv")
FLICKR_ZIP=os.path.join(REPO,"data","a4_raw","flickr30k","flickr30k-images.zip")
COCO_CSV=os.path.join(REPO,"data","a4_raw","coco5k","test_5k_mscoco_2014.csv")
COCO_DIR=os.path.join(REPO,"data","a4","coco5k","images_mscoco_2014_5k_test")
POPE_PARQUET=os.path.join(REPO,"paper3","data","test-pope-random.parquet")
MARINE_ROOT=os.path.join(REPO,"data","marinelife16k","data","selected_frames")
INAT_ROOT=os.path.join(REPO,"data","inat_wild")
DTD_ROOT=os.path.join(REPO,"data","dtd","dtd","images")
SCIENCEQA=os.path.join(REPO,"data","benchmarks","scienceqa","test.parquet")
MMBENCH=os.path.join(REPO,"data","benchmarks","mmbench","dev.parquet")
CAP_ADAPTERS=os.path.join(REPO,"outputs","p3_caption_adapters")
VQA_ADAPTERS=os.path.join(REPO,"outputs","p3_vqa_adapters")

def norm(s):
 s=str(s).lower().strip(); s=re.sub(r"[%s]"%re.escape(string.punctuation)," ",s); return " ".join(s.split())
def token_f1(refs,hyps):
 vals=[]
 for r,h in zip(refs,hyps):
  rt=collections.Counter(norm(r).split()); ht=collections.Counter(norm(h).split()); c=sum((rt&ht).values())
  if c==0: vals.append(0.0); continue
  p=c/max(sum(ht.values()),1); rec=c/max(sum(rt.values()),1); vals.append(2*p*rec/max(p+rec,1e-12))
 return float(np.mean(vals))
def bleu4(refs,hyps):
 prec=[]
 for n in range(1,5):
  num=den=0
  for r,h in zip(refs,hyps):
   rt=norm(r).split(); ht=norm(h).split()
   rc=collections.Counter(tuple(rt[i:i+n]) for i in range(len(rt)-n+1))
   hc=collections.Counter(tuple(ht[i:i+n]) for i in range(len(ht)-n+1))
   num += sum(min(c,rc[g]) for g,c in hc.items()); den += max(len(ht)-n+1,0)
  prec.append(num/den if den else 0.0)
 if min(prec)<=0: return 0.0
 return float(math.exp(sum(math.log(p) for p in prec)/4.0))
def load_adapter(task,arm):
 from transformers import AutoProcessor, BitsAndBytesConfig, LlavaForConditionalGeneration
 from peft import PeftModel
 q=BitsAndBytesConfig(load_in_4bit=True,bnb_4bit_compute_dtype=torch.float16,bnb_4bit_use_double_quant=True)
 proc=AutoProcessor.from_pretrained(MODEL)
 base=LlavaForConditionalGeneration.from_pretrained(MODEL,quantization_config=q,device_map="auto")
 model=base; adir=None
 if arm!="base":
  root=CAP_ADAPTERS if task in ("flickr30k","coco5k") else VQA_ADAPTERS
  adir=os.path.join(root,"r"+str(arm))
  if not os.path.exists(os.path.join(adir,"adapter_config.json")): raise FileNotFoundError(adir)
  model=PeftModel.from_pretrained(base,adir,is_trainable=False)
 model.eval(); return proc,model,adir
def flickr_rows(n):
 df=pd.read_csv(FLICKR_CSV); df=df[df["split"]=="test"].sort_values("filename")
 zf=zipfile.ZipFile(FLICKR_ZIP); rows=[]
 for _,r in df.iterrows():
  fn=str(r["filename"]); caps=ast.literal_eval(r["raw"]); name=next((x for x in zf.namelist() if x.endswith("/"+fn) or x==fn),None)
  if name: rows.append((io.BytesIO(zf.read(name)),"Describe the image.",caps[0] if caps else ""))
  if len(rows)>=n: break
 return rows
def coco_rows(n):
 df=pd.read_csv(COCO_CSV).drop_duplicates("filename"); rows=[]
 for _,r in df.iterrows():
  img=os.path.join(COCO_DIR,str(r["filename"]))
  if os.path.exists(img): rows.append((img,"Describe the image.",str(r["raw"])))
  if len(rows)>=n: break
 return rows
def pope_rows(n):
 df=pd.read_parquet(POPE_PARQUET); rows=[]
 for _,r in df.iterrows():
  src=str(r["image_source"]); img=os.path.join(COCO_DIR,src+".jpg")
  if os.path.exists(img): rows.append((img,str(r["instruction"]),str(r["output"])))
  if len(rows)>=n: break
 return rows
def marine_rows(n):
 rows=[]
 for qf in sorted(__import__("glob").glob(os.path.join(MARINE_ROOT,"*","*","qa.jsonl"))):
  frame=os.path.join(os.path.dirname(qf),"frame1.jpg")
  if not os.path.exists(frame): continue
  for line in io.open(qf,encoding="utf-8"):
   q=json.loads(line); opts="\n".join("%s. %s"%(o["label"],o["text"]) for o in q["options"])
   prompt=q["question"]+"\n"+opts+"\nAnswer with the option letter only."
   rows.append((frame,prompt,str(q["answer"])))
   if len(rows)>=n: return rows
 return rows

def _choice_rows(root,n,label_from_path,instruction):
    import glob, random
    files=[]; labels=[]
    for p in sorted(glob.glob(os.path.join(root,"**","*.jpg"),recursive=True)):
        lab=label_from_path(p)
        if lab: files.append(p); labels.append(lab)
    if not files: return []
    rng=random.Random(42); order=list(range(len(files))); rng.shuffle(order)
    all_labs=sorted(set(labels)); rows=[]
    for idx in order[:n]:
        correct=labels[idx]; pool=[x for x in all_labs if x!=correct]; rng.shuffle(pool)
        cands=[correct]+pool[:4]; rng.shuffle(cands); letter="ABCDE"[cands.index(correct)]
        opts="\n".join("%s. %s"%("ABCDE"[i],c.replace("_"," ")) for i,c in enumerate(cands))
        rows.append((files[idx],instruction+"\n"+opts+"\nAnswer with the option letter only.",letter))
    return rows

def inat_rows(n):
    return _choice_rows(INAT_ROOT,n,lambda p: os.path.basename(os.path.dirname(p)).replace("_"," "),"Which species is shown in the image?")

def dtd_rows(n):
    return _choice_rows(DTD_ROOT,n,lambda p: os.path.basename(os.path.dirname(p)).replace("_"," "),"Which texture class is shown in the image?")


def scienceqa_rows(n):
    df=pd.read_parquet(SCIENCEQA); rows=[]
    for _,r in df.iterrows():
        if r["image"] is None: continue
        ch=list(r["choices"]); ans=int(r["answer"])
        if not (0<=ans<len(ch)): continue
        opts="\n".join("%s. %s"%("ABCD"[i],str(c)) for i,c in enumerate(ch[:4]))
        prompt=str(r["question"])+"\n"+opts+"\nAnswer with the option letter only."
        rows.append((r["image"],prompt,"ABCD"[ans]))
        if len(rows)>=n: break
    return rows

def mmbench_rows(n):
    df=pd.read_parquet(MMBENCH); rows=[]
    for _,r in df.iterrows():
        opts=[]
        for L in "ABCD":
            if L in df.columns and pd.notna(r[L]): opts.append((L,str(r[L])))
        if len(opts)<2: continue
        ans=str(r["answer"]).strip().upper()[:1]
        prompt=str(r["question"])+"\n"+"\n".join("%s. %s"%(L,v) for L,v in opts)+"\nAnswer with the option letter only."
        rows.append((r["image"],prompt,ans))
        if len(rows)>=n: break
    return rows

def _open_img(src):
    if isinstance(src, dict):
        if src.get("bytes") is not None: return Image.open(io.BytesIO(src["bytes"])).convert("RGB")
        if src.get("path"): return Image.open(src["path"]).convert("RGB")
    if isinstance(src, (bytes, bytearray)): return Image.open(io.BytesIO(src)).convert("RGB")
    return Image.open(src).convert("RGB")

def main():
 ap=argparse.ArgumentParser(); ap.add_argument("--task",choices=["flickr30k","coco5k","pope","marinelife","inat","dtd","scienceqa","mmbench"],required=True); ap.add_argument("--arm",default="base"); ap.add_argument("--n",type=int,default=100)
 args=ap.parse_args(); os.environ["KMP_DUPLICATE_LIB_OK"]="TRUE"; os.environ["HF_HUB_OFFLINE"]="1"
 if args.task=="flickr30k": rows=flickr_rows(args.n)
 elif args.task=="coco5k": rows=coco_rows(args.n)
 elif args.task=="pope": rows=pope_rows(args.n)
 elif args.task=="marinelife": rows=marine_rows(args.n)
 elif args.task=="inat": rows=inat_rows(args.n)
 elif args.task=="dtd": rows=dtd_rows(args.n)
 elif args.task=="scienceqa": rows=scienceqa_rows(args.n)
 else: rows=mmbench_rows(args.n)
 proc,model,adir=load_adapter(args.task,args.arm)
 refs=[]; hyps=[]; t0=time.time()
 for img_src,prompt,ref in rows:
  img=_open_img(img_src)
  conv=[{"role":"user","content":[{"type":"image"},{"type":"text","text":prompt}]}]
  p=proc.apply_chat_template(conv,add_generation_prompt=True)
  inp=proc(text=p,images=img,return_tensors="pt").to(model.device)
  with torch.inference_mode(): out=model.generate(**inp,max_new_tokens=64,do_sample=False)
  gen=proc.tokenizer.decode(out[0][inp["input_ids"].shape[1]:],skip_special_tokens=True).strip()
  refs.append(ref); hyps.append(gen)
  if len(hyps)%10==0: print(args.task,args.arm,len(hyps),flush=True)
 out={"meta":{"task":args.task,"arm":args.arm,"n":len(hyps),"model":MODEL,"adapter":adir,"seed":42,
              "source":FLICKR_CSV if args.task=="flickr30k" else (COCO_CSV if args.task=="coco5k" else (POPE_PARQUET if args.task=="pope" else (MARINE_ROOT if args.task=="marinelife" else (INAT_ROOT if args.task=="inat" else (DTD_ROOT if args.task=="dtd" else (SCIENCEQA if args.task=="scienceqa" else MMBENCH)))))),
              "protocol":"held-out test split; archived adapters; zero-shot evaluation","elapsed_min":round((time.time()-t0)/60,2)},
      "refs":refs,"hypotheses":hyps}
 if args.task in ("flickr30k","coco5k"):
  out["token_f1"]=token_f1(refs,hyps); out["bleu4"]=bleu4(refs,hyps); out["exact_match"]=float(np.mean([norm(a)==norm(b) for a,b in zip(refs,hyps)]))
 else:
  def answer_label(s):
   n=norm(s)
   if args.task=="pope": m=re.search(r"\b(yes|no)\b",n); return m.group(1) if m else "no"
   m=re.search(r"\b([abcd])\b",n); return m.group(1) if m else ""
  pred=[answer_label(h) for h in hyps]; out["pred"]=pred
  out["accuracy"]=float(np.mean([p==str(r).lower() for p,r in zip(pred,refs)])); out["n"]=len(hyps)
  out["confusion"]=collections.Counter(zip(refs,pred)).most_common(10)
 p=os.path.join(AN,f"p3_v2_benchmark_{args.task}_{args.arm}.json"); io.open(p,"w",encoding="utf-8",newline="").write(json.dumps(out,indent=1)+"\n")
 print("wrote",os.path.relpath(p,REPO),out.get("token_f1"),out.get("accuracy"),flush=True)
if __name__=="__main__": main()
