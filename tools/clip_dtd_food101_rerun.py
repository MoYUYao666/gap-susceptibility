"""DTD / Food101 zero-shot re-evaluation — torchvision datasets (downloaded from the official source), protocol: single template 'a photo of a {}'.
Evaluates the three checkpoints frozen / text_only_r8 / both_r8; results are written to outputs/dtd_food101_zs_check.json.
"""
import os, json, sys
os.environ['HF_HUB_OFFLINE'] = '1'
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import torch
import torchvision.datasets as tvds
from torch.utils.data import DataLoader
from transformers import CLIPModel, CLIPProcessor
from src.lora import apply_lora_to_model

processor = CLIPProcessor.from_pretrained('openai/clip-vit-base-patch32', local_files_only=True)
TEMPLATES = ['a photo of a {}']


def get_split(ds_name):
    if ds_name == 'Food101':
        return tvds.Food101(root='data', split='test', download=True)
    return tvds.DTD(root='data', split='test', download=True)


def tv_collate(batch):
    """torchvision returns (PIL, label) by default; only labels are stacked, images stay a PIL list"""
    imgs = [b[0] for b in batch]
    ys = torch.tensor([b[1] for b in batch])
    return imgs, ys


@torch.no_grad()
def eval_tv(model, ds, class_names):
    texts = [t.format(c.replace('_', ' ')) for c in class_names for t in TEMPLATES]
    text_in = processor(text=texts, return_tensors='pt', padding=True).to('cuda')
    tout = model.text_model(**text_in)
    pooled = tout[1] if isinstance(tout, tuple) else tout.pooler_output
    tf = model.text_projection(pooled)
    tf = tf / tf.norm(dim=-1, keepdim=True)
    tf = tf.view(len(class_names), len(TEMPLATES), -1).mean(dim=1)
    tf = tf / tf.norm(dim=-1, keepdim=True)
    loader = DataLoader(ds, batch_size=64, shuffle=False, num_workers=0, collate_fn=tv_collate)
    correct = total = 0
    for imgs, ys in loader:
        inp = processor(images=list(imgs), return_tensors='pt').to('cuda')
        vout = model.vision_model(**inp)
        vpooled = vout[1] if isinstance(vout, tuple) else vout.pooler_output
        imf = model.visual_projection(vpooled)
        imf = imf / imf.norm(dim=-1, keepdim=True)
        pred = (imf @ tf.T).argmax(-1).cpu().numpy()
        correct += sum(1 for p, y in zip(pred, ys) if p == y)
        total += len(ys)
        if total % 5000 == 0:
            print('  ... %d/%d' % (total, len(ds)), flush=True)
    return 100 * correct / total


CONFIGS = {
    'frozen': dict(ckpt=None),
    'text_only_r8': dict(ckpt='outputs/imagenet_zs/text_only_r8/best_checkpoint.pt',
                         vision=False, text=True),
    'both_r8': dict(ckpt='outputs/imagenet_zs/both_r8/best_checkpoint.pt',
                    vision=True, text=True),
}

results, meta = {}, {}
for dname in ['DTD', 'Food101']:
    ds = get_split(dname)
    names = ds.classes
    print('%s: %d samples, %d classes' % (dname, len(ds), len(names)), flush=True)
    meta[dname] = {'n': len(ds), 'n_classes': len(names), 'source': 'torchvision %s test split' % dname}
    results[dname] = {}
    for label, cfg in CONFIGS.items():
        m = CLIPModel.from_pretrained('openai/clip-vit-base-patch32', local_files_only=True)
        if cfg.get('ckpt'):
            m, lora_layers, _ = apply_lora_to_model(
                m, rank=8, alpha=16.0,
                apply_to_vision=cfg['vision'], apply_to_text=cfg['text'])
            ckpt = torch.load(cfg['ckpt'], map_location='cpu', weights_only=False)
            sd = ckpt['lora_state_dict']
            with torch.no_grad():
                for k, w in sd.items():
                    lora_layers[k].lora_A.data.copy_(w['A'])
                    lora_layers[k].lora_B.data.copy_(w['B'])
        acc = eval_tv(m.cuda().eval(), ds, names)
        print('  %s %s => %.2f%%' % (dname, label, acc), flush=True)
        results[dname][label] = round(acc, 2)

out = {
    'protocol': {'templates': TEMPLATES, 'note': 'single template, torchvision class names'},
    'meta': meta,
    'results': results,
    'paper_footnote_values': {
        'dtd': {'frozen': 43.27, 'both': 42.53},
        'food101': {'frozen': 80.60, 'both': 79.73},
    },
}
json.dump(out, open('outputs/dtd_food101_zs_check.json', 'w', encoding='utf-8'),
          ensure_ascii=False, indent=2)
print('results saved to outputs/dtd_food101_zs_check.json')
