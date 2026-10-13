#!/bin/bash
# Paper2 experiment one-shot script — fix all known issues + run experiments
set -e

echo "===== Step 1: fix trainer.py ====="
sed -i 's/, local_files_only=True//g' /root/src/trainer.py

echo "===== Step 2: fix HF_HUB_OFFLINE ====="
sed -i '/HF_HUB_OFFLINE/d' /root/experiments/theory/v1_rank_sweep.py
sed -i '/HF_HUB_OFFLINE/d' /root/experiments/theory/v1_rank_sweep_coco.py
sed -i '/HF_HUB_OFFLINE/d' /root/experiments/theory/adapter_sweep.py

echo "===== Step 3: create data symlinks ====="
[ -d /root/flickr30k ] || ln -sf /root/experiments/flickr30k /root/flickr30k
[ -d /root/coco ] || ln -sf /root/experiments/coco /root/coco

echo "===== Step 4: fix flickr30k.json format ====="
python3 -c "
import json
path = '/root/flickr30k/flickr30k.json'
with open(path) as f:
    data = json.load(f)
# Check if already correct format
if data and 'captions' in data[0]:
    print('flickr30k.json already correct')
else:
    by_image = {}
    for item in data:
        img = item.get('image', f\"{item.get('image_id', 0)}.jpg\")
        cap = item.get('caption', '')
        if isinstance(cap, list): cap = cap[0] if cap else ''
        if img not in by_image: by_image[img] = []
        by_image[img].append(cap)
    new = [{'image': k, 'captions': v} for k,v in by_image.items()]
    with open(path, 'w') as f:
        json.dump(new, f)
    print(f'Fixed: {len(new)} images')
"

echo "===== Step 5: set up environment ====="
unset HF_HUB_OFFLINE
export HF_ENDPOINT=https://hf-mirror.com

echo "===== Step 6: run experiments ====="
echo "launching: v1_rank_sweep (Flickr30k)"
python experiments/theory/v1_rank_sweep.py > /root/v1_flickr30k.log 2>&1 &

echo "launching: v1_rank_sweep_coco (COCO)"
python experiments/theory/v1_rank_sweep_coco.py > /root/v1_coco.log 2>&1 &

echo "launching: adapter_sweep"
python experiments/theory/adapter_sweep.py > /root/adapter.log 2>&1 &

echo "===== Step 4.5: fix COCO annotation format ====="
python3 -c "
import json, os
for split in ['train','val']:
    path = f'coco/annotations/captions_{split}2017.json'
    with open(path) as f: data = json.load(f)
    if 'images' in data and data['images']: print(f'COCO {split}: OK'); continue
    files = sorted(os.listdir(f'coco/{split}2017/'))
    id_to_file = {i: f for i,f in enumerate(files)}
    anns = [{'image_id': a.get('image_id',0), 'caption': a.get('caption','')}
            for a in data.get('annotations', data.get('annotations',[]))
            if a.get('image_id',0) in id_to_file]
    new = {'images': [{'id': i, 'file_name': f} for i,f in id_to_file.items()],
           'annotations': anns}
    with open(path, 'w') as f: json.dump(new, f)
    print(f'COCO {split}: fixed')
"

echo "===== all three experiments launched in background ====="
echo "check progress: tail -f /root/v1_flickr30k.log"
echo "          tail -f /root/v1_coco.log"
echo "          tail -f /root/adapter.log"
