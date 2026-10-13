"""Confirm the dataset identity of the imagenet_zs experiment: measure frozen CLIP ViT-B/32 zero-shot top-1 on CIFAR-100.
Compare with the paper's 60.72% (claimed to be CIFAR-100). If it is ≈66-68% (CLIP reference value), then it is not CIFAR-100."""
import os
os.environ.setdefault('HF_ENDPOINT', 'https://hf-mirror.com')
os.environ.setdefault('HF_HUB_OFFLINE', '1')  # model already cached, load offline to avoid timeouts
import torch
from transformers import CLIPModel, CLIPProcessor
import torchvision.datasets as dsets
from torch.utils.data import DataLoader

MODEL = 'openai/clip-vit-base-patch32'
LOCAL = './models/clip-vit-base-patch32'  # locally downloaded path (optional)

def has_weights(path):
    if not os.path.isdir(path):
        return False
    return any(f.endswith(('.safetensors', '.bin')) for f in os.listdir(path))

if has_weights(LOCAL):
    print('Loading local CLIP:', LOCAL, flush=True)
    model = CLIPModel.from_pretrained(LOCAL).cuda().eval()
    processor = CLIPProcessor.from_pretrained(LOCAL)
else:
    print('Downloading/loading CLIP ViT-B/32 (online, ~330MB, please be patient)...', flush=True)
    model = CLIPModel.from_pretrained(MODEL).cuda().eval()
    processor = CLIPProcessor.from_pretrained(MODEL)

print('Loading CIFAR-100 ...', flush=True)
ds = dsets.CIFAR100('./data', train=False, download=True)
labels = ds.classes
texts = [f'a photo of a {c.replace("_", " ")}' for c in labels]
text_in = processor(text=texts, return_tensors='pt', padding=True).to('cuda')

correct = total = 0
with torch.no_grad():
    for i in range(0, len(ds), 128):
        batch = [ds[j] for j in range(i, min(i + 128, len(ds)))]
        imgs = [x[0] for x in batch]
        ys = [x[1] for x in batch]
        inp = processor(images=imgs, return_tensors='pt').to('cuda')
        logits = model(**inp, **text_in).logits_per_image
        pred = logits.argmax(-1).cpu()
        correct += (pred.numpy() == ys).sum()
        total += len(batch)
        if total % 2500 == 0:
            print('  ... %d/%d' % (total, len(ds)), flush=True)
print('\nCIFAR-100 zero-shot top-1: %.2f%% (n=%d)' % (100 * correct / total, total))
print('Paper claimed value: 60.72%%')
if abs(100 * correct / total - 60.72) < 3:
    print('=> Matches 60.72 -> the dataset is indeed CIFAR-100')
else:
    print('=> Does not match 60.72 -> 60.72 is not CIFAR-100, possibly ImageNet (further verification needed)')
