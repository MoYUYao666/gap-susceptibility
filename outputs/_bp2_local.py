
import os, sys, json, hashlib
os.chdir(r"""D:\Realdesktop\Wan\Important\New""")
sys.path.insert(0, r"""D:\Realdesktop\Wan\Important\New""")
import torch
from src.dataset import create_dataloaders

loader, val_loader, _ = create_dataloaders(
    dataset_name="flickr30k", data_dir=".", batch_size=128, max_samples=5000)
b = next(iter(loader))
caps = [str(c) for c in b["caption"]]
imgs = b["image"]
ids = b["input_ids"]
out = {
    "n": int(imgs.shape[0]),
    "n_unique_caps": len(set(caps)),
    "cap_head": caps[:3],
    "cap_md5": hashlib.md5("|".join(caps).encode()).hexdigest()[:16],
    "img_md5": hashlib.md5(imgs.numpy().tobytes()).hexdigest()[:16],
    "img_sum": round(float(imgs.sum()), 3),
    "ids_md5": hashlib.md5(ids.numpy().tobytes()).hexdigest()[:16],
    "ids_row0": ids[0].tolist()[:12],
    "ids_row1": ids[1].tolist()[:12],
    "ids_unique_rows": len(set(tuple(r.tolist()) for r in ids)),
    "val_n": int(next(iter(val_loader))["image"].shape[0]),
}
print(json.dumps(out, indent=1))
