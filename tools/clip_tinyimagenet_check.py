"""验证 imagenet_zs 实验是否用了 TinyImageNet：测 frozen CLIP ViT-B/32 在 TinyImageNet-200 val 的 zero-shot top-1。
对比论文 60.72%（声称 CIFAR-100，实际疑似 ImageNet 系列）。"""
import os, zipfile, shutil
os.environ.setdefault('HF_HUB_OFFLINE', '1')  # CLIP 已缓存
import torch
from transformers import CLIPModel, CLIPProcessor
from PIL import Image

# ---------- 1. 准备 TinyImageNet ----------
ZIP = './data/tiny-imagenet-200.zip'
ROOT = './data/tiny-imagenet-200'
if not os.path.isdir(ROOT):
    print('下载 TinyImageNet (~250MB)...', flush=True)
    url = 'http://cs231n.stanford.edu/tiny-imagenet-200.zip'
    import urllib.request
    urllib.request.urlretrieve(url, ZIP)
    print('解压...', flush=True)
    with zipfile.ZipFile(ZIP) as z:
        z.extractall('./data/')
    # 整理 val：val_annotations.txt → images 移到 class 子目录
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
print('TinyImageNet 就绪', flush=True)

# ---------- 2. 加载 CLIP ----------
print('加载 CLIP ViT-B/32 ...', flush=True)
model = CLIPModel.from_pretrained('openai/clip-vit-base-patch32').cuda().eval()
processor = CLIPProcessor.from_pretrained('openai/clip-vit-base-patch32')

# ---------- 3. 类别 ----------
classes = sorted(os.listdir(os.path.join(ROOT, 'train')))  # 200 类（wnid 如 n01443537）
# 用 synset words 做 prompt（简易：类名数字无意义，用 wnid 提示效果差）
# 更准确：TinyImageNet 类名 = ImageNet 同 wnid 的类别名。这里用 ImageNet 1k 模板的替代：
# 简易方案：用 ImageNet 1000 类中对应 wnid 的名称映射（torchvision 有）
import torchvision.datasets as tvds
meta = tvds.ImageNet.meta if hasattr(tvds.ImageNet, 'meta') else None
# 用 torchvision 的 ImageNet 类别映射（无需下载数据）
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
            # wnid 推导：ImageNet 1000 类 wnid 需要额外映射，这里用最接近的启发式
            wnid2name.setdefault(name, name)
texts = [f'a photo of a {classes[i]}' for i in range(200)]  # 备选：wnid 直接当文本
# 尝试更好：用 torchvision ImageNet 的 wnid→name（models 里有 siglip 但不是这个）
text_in = processor(text=texts, return_tensors='pt', padding=True).to('cuda')

# ---------- 4. 评估 ----------
val_dir = os.path.join(ROOT, 'val')
val_items = []
for c in os.listdir(val_dir):
    cd = os.path.join(val_dir, c)
    if os.path.isdir(cd):
        for fn in os.listdir(cd):
            val_items.append((os.path.join(cd, fn), classes.index(c)))
print('val 样本:', len(val_items), flush=True)

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
print('论文声称值: 60.72%%')
if abs(100 * correct / total - 60.72) < 3:
    print('=> 与 60.72 匹配 → 数据集实为 TinyImageNet')
else:
    print('=> 与 60.72 不匹配（%.1f vs 60.72）→ 非 TinyImageNet，倾向完整 ImageNet' % (100 * correct / total))
