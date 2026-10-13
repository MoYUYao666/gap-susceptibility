"""TinyImageNet-200 zero-shot validation. Compare against the paper's 60.72% (already calibrated to ImageNet (zero-shot)).
Authoritative source of the class names: data/classes.py or data/tiny_imagenet_classes.py (classes.py from the zh-plus/tiny-imagenet repo,
whose i2d dict contains all ImageNet synsets). On the first run, the 200 tiny class names are extracted and saved to data/tiny_wnid_names.json.

⚠️ Order-sensitive: datasets/pyarrow must be imported before torch (importing both in the same process segfaults /
with an access violation in pyarrow.dataset)."""
import os, sys, json, ast
os.environ.setdefault('HF_ENDPOINT', 'https://hf-mirror.com')
os.environ['HF_HUB_OFFLINE'] = '1'

# ---------- 1. load TinyImageNet valid first (arrow offline cache) ----------
from datasets import Dataset
arrow = r'C:\Users\hongr\.cache\huggingface\datasets\zh-plus___tiny-imagenet\default\0.0.0\5a77092c28e51558c5586e9c5eb71a7e17a5e43f\tiny-imagenet-valid.arrow'
ds = Dataset.from_file(arrow)
print('[1/3] TinyImageNet valid loaded, number of samples:', len(ds), flush=True)

# ---------- 2. class names (authoritative source classes.py) ----------
HERE = os.path.dirname(os.path.abspath(__file__))
CPY = os.path.join(HERE, 'data', 'tiny_imagenet_classes.py')
if not os.path.exists(CPY):
    CPY = os.path.join(HERE, 'data', 'classes.py')  # filename written to disk by hf_hub_download local_dir='data'
NAMES_JSON = os.path.join(HERE, 'data', 'tiny_wnid_names.json')
WNIDS_JSON = os.path.join(HERE, 'data', 'tiny_wnids.json')

if os.path.exists(NAMES_JSON):
    WNID_NAMES = json.load(open(NAMES_JSON, encoding='utf-8'))
else:
    if not os.path.exists(CPY):
        sys.exit(
            'missing %s\n'
            'please download the authoritative class-name file first (hf-mirror domestic mirror):\n'
            '  HF_ENDPOINT=https://hf-mirror.com python -c "from huggingface_hub import hf_hub_download; '
            "hf_hub_download('zh-plus/tiny-imagenet', 'classes.py', local_dir='data'); print('done')" % CPY)
    i2d = ast.literal_eval(ast.parse(open(CPY, encoding='utf-8').read()).body[0].value)  # first-line assignment = the i2d dict
    wnids = json.load(open(WNIDS_JSON, encoding='utf-8'))
    assert len(wnids) == 200, 'tiny_wnids.json should contain 200 wnids'
    missing = [w for w in wnids if w not in i2d]
    assert not missing, 'classes.py is missing class names: %s' % missing[:10]
    WNID_NAMES = [i2d[w].split(',')[0].strip() for w in wnids]  # primary name (before the comma), class_ids.txt style
    json.dump(WNID_NAMES, open(NAMES_JSON, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    print('extracted %d class names -> %s' % (len(WNID_NAMES), NAMES_JSON), flush=True)

assert len(WNID_NAMES) == 200, 'the class-name list must have 200 entries, got %d' % len(WNID_NAMES)
print('number of class names:', len(WNID_NAMES), flush=True)

# ---------- 3. then load CLIP (after datasets, to avoid DLL conflicts) ----------
print('[2/3] loading CLIP ViT-B/32 (offline cache)...', flush=True)
import torch
from transformers import CLIPModel, CLIPProcessor
model = CLIPModel.from_pretrained('openai/clip-vit-base-patch32', local_files_only=True).cuda().eval()
processor = CLIPProcessor.from_pretrained('openai/clip-vit-base-patch32', local_files_only=True)

print('[3/3] evaluating 10000 images (real class-name prompts, same multi-template averaging as the paper)...', flush=True)
templates = ['a photo of a {}', 'a photo of the {}', 'a photo of a {} in a photo']
all_texts = [t.format(c.replace('_', ' ')) for c in WNID_NAMES for t in templates]
text_in = processor(text=all_texts, return_tensors='pt', padding=True).to('cuda')
with torch.no_grad():
    text_feats = model.get_text_features(**text_in)
    text_feats = text_feats / text_feats.norm(dim=-1, keepdim=True)
    # average over the 3 templates of each class
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
print('value claimed in the paper: 60.72%%')
if abs(acc - 60.72) < 4:
    print('=> matches 60.72 (±4pp) → the dataset really is TinyImageNet')
else:
    print('=> does not match 60.72 (%.1f vs 60.72) → not TinyImageNet, more likely the full ImageNet-1K' % acc)
