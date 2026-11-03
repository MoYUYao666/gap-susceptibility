"""确认 imagenet_zs 实验的数据集身份：测 frozen CLIP ViT-B/32 在 CIFAR-100 的 zero-shot top-1。
对比论文 60.72%（声称 CIFAR-100）。如果 ≈66-68%（CLIP 参考值）则不是 CIFAR-100。"""
import os
os.environ.setdefault('HF_ENDPOINT', 'https://hf-mirror.com')
os.environ.setdefault('HF_HUB_OFFLINE', '1')  # 模型已缓存，离线加载避免超时
import torch
from transformers import CLIPModel, CLIPProcessor
import torchvision.datasets as dsets
from torch.utils.data import DataLoader

MODEL = 'openai/clip-vit-base-patch32'
LOCAL = './models/clip-vit-base-patch32'  # 本地下载的路径（可选）

def has_weights(path):
    if not os.path.isdir(path):
        return False
    return any(f.endswith(('.safetensors', '.bin')) for f in os.listdir(path))

if has_weights(LOCAL):
    print('加载本地 CLIP:', LOCAL, flush=True)
    model = CLIPModel.from_pretrained(LOCAL).cuda().eval()
    processor = CLIPProcessor.from_pretrained(LOCAL)
else:
    print('下载/加载 CLIP ViT-B/32（在线，~330MB，耐心等待）...', flush=True)
    model = CLIPModel.from_pretrained(MODEL).cuda().eval()
    processor = CLIPProcessor.from_pretrained(MODEL)

print('加载 CIFAR-100 ...', flush=True)
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
print('论文声称值: 60.72%%')
if abs(100 * correct / total - 60.72) < 3:
    print('=> 与 60.72 匹配 → 数据集确为 CIFAR-100')
else:
    print('=> 与 60.72 不匹配 → 60.72 不是 CIFAR-100，可能为 ImageNet（需进一步验证）')
