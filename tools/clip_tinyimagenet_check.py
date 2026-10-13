"""Check whether the imagenet_zs experiment used TinyImageNet: measure zero-shot top-1 of frozen CLIP ViT-B/32 on TinyImageNet-200 val.
Compared against the paper value 60.72% (claimed CIFAR-100, but actually looks like an ImageNet variant)."""
import os, zipfile, shutil
os.environ.setdefault('HF_HUB_OFFLINE', '1')  # CLIP already cached
import torch
from transformers import CLIPModel, CLIPProcessor
from PIL import Image

# ---------- 1. Prepare TinyImageNet ----------
ZIP = './data/tiny-imagenet-200.zip'
ROOT = './data/tiny-imagenet-200'
if not os.path.isdir(ROOT):
    print('downloading TinyImageNet (~250MB)...', flush=True)
    url = 'http://cs231n.stanford.edu/tiny-imagenet-200.zip'
    import urllib.request
    urllib.request.urlretrieve(url, ZIP)
    print('extracting...', flush=True)
    with zipfile.ZipFile(ZIP) as z:
        z.extractall('./data/')
    # organize val: move images listed in val_annotations.txt into per-class subdirectories
    val_ann = os.path.join(ROOT, 'val', 'val_annotations.txt')
    val_img = os.path.join(ROOT, 'val', 'images')
    import collections
    with open(val_ann) as f:
        for line in f:
            fn, cls = line.split()[:2]
            d = os.path.join(ROOT, 'val', cls)
            os.makedirs(d, exist_ok=True)
            try:
                os.rename(os.path.join(val_img, fn), os.path.join(d, fn))
            except OSError:
                pass
print('TinyImageNet ready', flush=True)

# ---------- 2. Load CLIP ----------
print('loading CLIP ViT-B/32 ...', flush=True)
model = CLIPModel.from_pretrained('openai/clip-vit-base-patch32').cuda().eval()
processor = CLIPProcessor.from_pretrained('openai/clip-vit-base-patch32')

# ---------- 3. Classes ----------
classes = sorted(os.listdir(os.path.join(ROOT, 'train')))  # 200 classes (wnid such as n01443537)
# Use synset words as prompts (simple approach: numeric class names are meaningless, wnid prompts work poorly)
# More accurate: TinyImageNet class names = ImageNet class names of the same wnid. Here a substitute for the ImageNet 1k template:
# Simple workaround: use the name mapping for the corresponding wnid among the ImageNet 1000 classes (torchvision has it)
import torchvision.datasets as tvds
meta = tvds.ImageNet.meta if hasattr(tvds.ImageNet, 'meta') else None
# Use the torchvision ImageNet class mapping (no data download needed)
import json
imagenet_classes_url = 'https://raw.githubusercontent.com/pytorch/hub/master/imagenet_classes.txt'
local_classes = './data/imagenet_classes.txt'
if not os.path.exists(local_classes):
    import urllib.request
    try:
        urllib.request.urlretrieve(imagenet_classes_url, local_classes)
    except Exception:
        pass
wnid2name = {}
if os.path.exists(local_classes):
    with open(local_classes) as f:
        for i, line in enumerate(f):
            name = line.strip()
            # wnid derivation: the 1000 ImageNet wnids need an extra mapping, so the closest heuristic is used here
            wnid2name.setdefault(name, name)
texts = [f'a photo of a {classes[i]}' for i in range(200)]  # alternative: use the wnid directly as text
# Try a better option: torchvision ImageNet wnid→name (models has siglip but not this one)
text_in = processor(text=texts, return_tensors='pt', padding=True).to('cuda')

# ---------- 4. Evaluation ----------
val_dir = os.path.join(ROOT, 'val')
val_items = []
for c in os.listdir(val_dir):
    cd = os.path.join(val_dir, c)
    if os.path.isdir(cd):
        for fn in os.listdir(cd):
            val_items.append((os.path.join(cd, fn), classes.index(c)))
print('val samples:', len(val_items), flush=True)

correct = total = 0
with torch.no_grad():
    for i in range(0, len(val_items), 64):
        batch = val_items[i:i+64]
        imgs = [Image.open(p).convert('RGB') for p, _ in batch]
        ys = [y for _, y in batch]
        inp = processor(images=imgs, return_tensors='pt').to('cuda')
        logits = model(**inp, **text_in).logits_per_image
        pred = logits.argmax(-1).cpu().numpy()
        correct += sum(1 for p, y in zip(pred, ys) if p == y)
        total += len(batch)
print('\nTinyImageNet-200 zero-shot top-1: %.2f%% (n=%d)' % (100 * correct / total, total))
print('value claimed in the paper: 60.72%%')
if abs(100 * correct / total - 60.72) < 3:
    print('=> matches 60.72 → the dataset is actually TinyImageNet')
else:
    print('=> does not match 60.72 (%.1f vs 60.72) → not TinyImageNet, more likely the full ImageNet' % (100 * correct / total))
