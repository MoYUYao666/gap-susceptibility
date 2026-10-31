"""TinyImageNet-200 zero-shot 验证。对比论文 60.72%（已定标 ImageNet (zero-shot)）。
类名权威来源：data/classes.py 或 data/tiny_imagenet_classes.py（zh-plus/tiny-imagenet 仓库 classes.py，
i2d 字典含全部 ImageNet synset）。首次运行自动提取 200 个 tiny 类名存 data/tiny_wnid_names.json。

⚠️ 顺序敏感：datasets/pyarrow 必须在 torch 之前导入（两者同进程导入会在 pyarrow.dataset
处段错误/access violation）。"""
import os, sys, json, ast
os.environ.setdefault('HF_ENDPOINT', 'https://hf-mirror.com')
os.environ['HF_HUB_OFFLINE'] = '1'

# ---------- 1. 先加载 TinyImageNet valid（arrow 离线缓存）----------
from datasets import Dataset
arrow = r'C:\Users\hongr\.cache\huggingface\datasets\zh-plus___tiny-imagenet\default\0.0.0\5a77092c28e51558c5586e9c5eb71a7e17a5e43f\tiny-imagenet-valid.arrow'
ds = Dataset.from_file(arrow)
print('[1/3] TinyImageNet valid 已加载，样本数:', len(ds), flush=True)

# ---------- 2. 类名（权威来源 classes.py）----------
HERE = os.path.dirname(os.path.abspath(__file__))
CPY = os.path.join(HERE, 'data', 'tiny_imagenet_classes.py')
if not os.path.exists(CPY):
    CPY = os.path.join(HERE, 'data', 'classes.py')  # hf_hub_download local_dir='data' 落盘名
NAMES_JSON = os.path.join(HERE, 'data', 'tiny_wnid_names.json')
WNIDS_JSON = os.path.join(HERE, 'data', 'tiny_wnids.json')

if os.path.exists(NAMES_JSON):
    WNID_NAMES = json.load(open(NAMES_JSON, encoding='utf-8'))
else:
    if not os.path.exists(CPY):
        sys.exit(
            '缺少 %s\n'
            '请先下载权威类名文件（hf-mirror 国内镜像）:\n'
            '  HF_ENDPOINT=https://hf-mirror.com python -c "from huggingface_hub import hf_hub_download; '
            "hf_hub_download('zh-plus/tiny-imagenet', 'classes.py', local_dir='data'); print('done')" % CPY)
    i2d = ast.literal_eval(ast.parse(open(CPY, encoding='utf-8').read()).body[0].value)  # 首行赋值 = i2d 字典
    wnids = json.load(open(WNIDS_JSON, encoding='utf-8'))
    assert len(wnids) == 200, 'tiny_wnids.json 应为 200 个 wnid'
    missing = [w for w in wnids if w not in i2d]
    assert not missing, 'classes.py 缺少类名: %s' % missing[:10]
    WNID_NAMES = [i2d[w].split(',')[0].strip() for w in wnids]  # 主名（逗号前），class_ids.txt 风格
    json.dump(WNID_NAMES, open(NAMES_JSON, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    print('已提取 %d 个类名 -> %s' % (len(WNID_NAMES), NAMES_JSON), flush=True)

assert len(WNID_NAMES) == 200, '类名列表必须 200 个，实际 %d' % len(WNID_NAMES)
print('类名数:', len(WNID_NAMES), flush=True)

# ---------- 3. 再加载 CLIP（datasets 之后，避免 DLL 冲突）----------
print('[2/3] 加载 CLIP ViT-B/32（离线缓存）...', flush=True)
import torch
from transformers import CLIPModel, CLIPProcessor
model = CLIPModel.from_pretrained('openai/clip-vit-base-patch32', local_files_only=True).cuda().eval()
processor = CLIPProcessor.from_pretrained('openai/clip-vit-base-patch32', local_files_only=True)

print('[3/3] 评估 10000 张（真实类名提示，论文同款多模板平均）...', flush=True)
templates = ['a photo of a {}', 'a photo of the {}', 'a photo of a {} in a photo']
all_texts = [t.format(c.replace('_', ' ')) for c in WNID_NAMES for t in templates]
text_in = processor(text=all_texts, return_tensors='pt', padding=True).to('cuda')
with torch.no_grad():
    text_feats = model.get_text_features(**text_in)
    text_feats = text_feats / text_feats.norm(dim=-1, keepdim=True)
    # 每个类 3 个模板平均
    text_feats = text_feats.view(200, len(templates), -1).mean(dim=1)
    text_feats = text_feats / text_feats.norm(dim=-1, keepdim=True)

correct = total = 0
with torch.no_grad():
    for i in range(0, len(ds), 64):
        batch = ds[i:i+64]
        imgs, ys = batch['image'], batch['label']
        inp = processor(images=imgs, return_tensors='pt').to('cuda')
        img_feats = model.get_image_features(**inp)
        img_feats = img_feats / img_feats.norm(dim=-1, keepdim=True)
        sims = img_feats @ text_feats.T
        pred = sims.argmax(-1).cpu().numpy()
        correct += sum(1 for p, y in zip(pred, ys) if p == y)
        total += len(ys)
        if total % 2500 == 0:
            print('  ... %d/%d' % (total, len(ds)), flush=True)

acc = 100 * correct / total
print('\nTinyImageNet-200 zero-shot top-1: %.2f%% (n=%d)' % (acc, total))
print('论文声称值: 60.72%%')
if abs(acc - 60.72) < 4:
    print('=> 与 60.72 匹配（±4pp）→ 数据集实为 TinyImageNet')
else:
    print('=> 与 60.72 不匹配（%.1f vs 60.72）→ 非 TinyImageNet，更倾向完整 ImageNet-1K' % acc)
