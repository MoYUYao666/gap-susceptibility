
import os, sys, json, hashlib
os.chdir(r"""D:\Realdesktop\Wan\Important\New""")
sys.path.insert(0, r"""D:\Realdesktop\Wan\Important\New""")
import torch
from src.dataset import create_dataloaders

loader, val_loader, _ = create_dataloaders(
    dataset_name="flickr30k", data_dir=".", batch_size=128, max_samples=5000)

b = next(iter(loader))
caps = b["caption"]
imgs = b["image"]
print(json.dumps({
    "batch_size": int(imgs.shape[0]),
    "n_captions": len(caps),
    "caption_head": [str(c)[:60] for c in caps[:5]],
    "caption_unique": len(set(str(c) for c in caps)),
    "caption_hash": hashlib.md5("|".join(str(c) for c in caps).encode()).hexdigest()[:16],
    "image_shape": list(imgs.shape),
    "image_sum": round(float(imgs.sum()), 4),
    "image_hash": hashlib.md5(imgs.numpy().tobytes()).hexdigest()[:16],
    "val_batches": len(val_loader),
    "val_batch_size": int(next(iter(val_loader))["image"].shape[0]),
}, indent=1))
