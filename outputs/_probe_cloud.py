
import os, sys, json, glob
import torch, torch.nn.functional as F
os.chdir(r"""/root/autodl-tmp/work""")
sys.path.insert(0, r"""/root/autodl-tmp/work""")
from transformers import CLIPModel, CLIPProcessor
from PIL import Image

MD = r"""/root/autodl-tmp/work/models/clip-vit-base-patch32"""
m = CLIPModel.from_pretrained(MD, local_files_only=True)
p = CLIPProcessor.from_pretrained(MD, local_files_only=True)
m.eval()

# Fixed input: first 4 images + fixed texts (independent of the dataset split)
imgs = sorted(glob.glob("flickr30k/flickr30k-images/*.jpg"))[:4]
texts = ["a photo of a dog", "two men in a yard", "a child in a pink dress",
         "a dog running on grass"]
ims = [Image.open(x).convert("RGB") for x in imgs]

with torch.no_grad():
    inp = p(text=texts, images=ims, return_tensors="pt", padding=True)
    out = m(**inp)

I = out.image_embeds
T = out.text_embeds
In = F.normalize(I, p=2, dim=-1)
Tn = F.normalize(T, p=2, dim=-1)

res = {
    "n_images": len(ims),
    "image_embeds_norm_mean": float(I.norm(dim=-1).mean()),
    "image_embeds_norm_std": float(I.norm(dim=-1).std()),
    "text_embeds_norm_mean": float(T.norm(dim=-1).mean()),
    "image_embeds_dim": int(I.shape[-1]),
    "image_embeds_first5": [round(float(x), 6) for x in I[0, :5]],
    "image_embeds_hash": round(float(I.sum()), 4),
    "cos_ii_mean": float((In @ In.T).mean()),
    "dist_it_mean": float(((In - Tn) ** 2).sum(-1).mean()),
    "cg_norm": float((In.mean(0) - Tn.mean(0)).norm()),
    "cg_raw": float((I.mean(0) - T.mean(0)).norm()),
}
print(json.dumps(res, indent=1))
open("_embed_probe.json", "w").write(json.dumps(res))
