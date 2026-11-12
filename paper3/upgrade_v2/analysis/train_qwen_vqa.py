# -*- coding: utf-8 -*-
"""Train a small Qwen2-VL-2B VQA-RAD adapter for cross-architecture public-benchmark checks."""
import argparse, glob, io, json, os, sys, time
import numpy as np, pandas as pd, torch
from PIL import Image

REPO=os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
MODEL=os.path.join(REPO,"models","Qwen2-VL-2B-Instruct")
TRAIN=os.path.join(REPO,"paper3","data","train-vqarad.parquet")
IMAGES=os.path.join(REPO,"data","vqa_rad","images")

def main():
 ap=argparse.ArgumentParser(); ap.add_argument("--rank",type=int,required=True); ap.add_argument("--seed",type=int,default=42)
 ap.add_argument("--epochs",type=int,default=2); ap.add_argument("--num-samples",type=int,default=100)
 ap.add_argument("--out-dir",required=True); args=ap.parse_args(); os.environ["KMP_DUPLICATE_LIB_OK"]="TRUE"; os.environ["HF_HUB_OFFLINE"]="1"
 from transformers import Qwen2VLForConditionalGeneration, AutoProcessor, BitsAndBytesConfig
 from peft import LoraConfig, get_peft_model
 q=BitsAndBytesConfig(load_in_4bit=True,bnb_4bit_compute_dtype=torch.float16,bnb_4bit_use_double_quant=True)
 model=Qwen2VLForConditionalGeneration.from_pretrained(MODEL,quantization_config=q,device_map="auto")
 proc=AutoProcessor.from_pretrained(MODEL)
 cfg=LoraConfig(r=args.rank,lora_alpha=2*args.rank,lora_dropout=0.05,target_modules=["q_proj","k_proj","v_proj","o_proj"],task_type="CAUSAL_LM")
 model=get_peft_model(model,cfg); model.train()
 if hasattr(model,"gradient_checkpointing_enable"): model.gradient_checkpointing_enable()
 df=pd.read_parquet(TRAIN).head(args.num_samples)
 opt=torch.optim.AdamW([p for p in model.parameters() if p.requires_grad],lr=1e-4)
 t0=time.time(); losses=[]
 for ep in range(args.epochs):
  for i,row in df.iterrows():
   img=Image.open(os.path.join(IMAGES,str(row["image"]))).convert("RGB")
   msgs=[{"role":"user","content":[{"type":"image"},{"type":"text","text":str(row["instruction"])}]},{"role":"assistant","content":[{"type":"text","text":str(row["output"])}]}]
   text=proc.apply_chat_template(msgs,add_generation_prompt=False)
   inp=proc(text=[text],images=[img],return_tensors="pt")
   inp={k:(v.to(model.device) if hasattr(v,"to") else v) for k,v in inp.items()}
   inp["labels"]=inp["input_ids"].clone()
   out=model(**inp); loss=out.loss
   if not torch.isfinite(loss): continue
   loss.backward(); torch.nn.utils.clip_grad_norm_([p for p in model.parameters() if p.requires_grad],1.0)
   opt.step(); opt.zero_grad(); losses.append(float(loss.item()))
   if (i+1)%10==0: print("ep",ep,"step",i+1,"loss",round(float(np.mean(losses[-10:])),4),flush=True)
 os.makedirs(args.out_dir,exist_ok=True); model.save_pretrained(args.out_dir)
 proc.save_pretrained(args.out_dir)
 meta={"rank":args.rank,"seed":args.seed,"epochs":args.epochs,"num_samples":len(df),"model":MODEL,
       "train_data":TRAIN,"elapsed_min":round((time.time()-t0)/60,2),"last_loss":float(np.mean(losses[-10:])) if losses else None}
 io.open(os.path.join(args.out_dir,"train_meta.json"),"w",encoding="utf-8",newline="").write(json.dumps(meta,indent=1)+"\n")
 print("saved",args.out_dir,meta,flush=True)
if __name__=="__main__": main()
