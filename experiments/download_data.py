"""自动下载数据集 — 用 HuggingFace datasets 库。支持跳过已完成。"""
import os, json, glob
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
from datasets import load_dataset
from tqdm import tqdm

# ==== Flickr30k ====
if len(glob.glob("flickr30k/flickr30k-images/*.jpg")) > 1000:
    print("Flickr30k: already downloaded — skip")
else:
    print("Downloading Flickr30k...")
    os.makedirs("flickr30k/flickr30k-images", exist_ok=True)
    ds = load_dataset("nlphuji/flickr30k", split="test", trust_remote_code=True)
    for i, item in enumerate(tqdm(ds, desc="flickr30k")):
        item['image'].save(f"flickr30k/flickr30k-images/{i}.jpg")
    anns = []
    for i, item in enumerate(ds):
        captions = item.get('caption', []) or item.get('sentences', []) or []
        if isinstance(captions, str): captions = [captions]
        if isinstance(captions, dict): captions = [captions.get('raw', str(captions))]
        anns.append({"image_id": i, "caption": captions, "id": i})
    with open("flickr30k/flickr30k.json", "w") as f: json.dump(anns, f)
    print(f"Flickr30k done: {i+1} images")

# ==== COCO ====
for split in ["train", "val"]:
    if len(glob.glob(f"coco/{split}2014/*.jpg")) > 1000:
        print(f"COCO {split}: already downloaded — skip")
        continue
    print(f"Downloading COCO {split}...")
    os.makedirs(f"coco/{split}2014", exist_ok=True)
    os.makedirs("coco/annotations", exist_ok=True)
    ds = load_dataset("HuggingFaceM4/COCO", split=f"{split}2014", trust_remote_code=True)
    anns = {"images": [], "annotations": []}
    for i, item in enumerate(tqdm(ds, desc=f"coco {split}")):
        item['image'].save(f"coco/{split}2014/COCO_{split}2014_{i:012d}.jpg")
        sents = item.get('sentences', item.get('caption', []))
        if isinstance(sents, str): sents = [sents]
        for s in sents:
            anns["annotations"].append({
                "image_id": i, "caption": s if isinstance(s, str) else str(s)
            })
    with open(f"coco/annotations/captions_{split}2014.json", "w") as f: json.dump(anns, f)
print("All done!")
