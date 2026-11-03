"""对 clip_fullft_rerun.py 产出的 full FT 权重做 ImageNet-1K 零样本评测（两协议 × 两 checkpoint）。"""
import os, json
os.environ['HF_HUB_OFFLINE'] = '1'
from glob import glob
from datasets import Dataset
import torch
from transformers import CLIPModel, CLIPProcessor

PARQ = sorted(glob('data/imagenet_hf/*.parquet'))
ds = Dataset.from_parquet(PARQ)
names_full = ds.features['label'].names
names_plain = [n.split(',')[0].strip() for n in names_full]
processor = CLIPProcessor.from_pretrained('openai/clip-vit-base-patch32', local_files_only=True)


@torch.no_grad()
def zs_eval(m, class_names):
    texts = ['a photo of a {}'.format(c.replace('_', ' ')) for c in class_names]
    text_in = processor(text=texts, return_tensors='pt', padding=True).to('cuda')
    tout = m.text_model(**text_in)
    pooled = tout[1] if isinstance(tout, tuple) else tout.pooler_output
    tf = m.text_projection(pooled)
    tf = tf / tf.norm(dim=-1, keepdim=True)
    correct = total = 0
    for i in range(0, len(ds), 64):
        b = ds[i:i + 64]
        inp = processor(images=b['image'], return_tensors='pt').to('cuda')
        vout = m.vision_model(**inp)
        vpooled = vout[1] if isinstance(vout, tuple) else vout.pooler_output
        imf = m.visual_projection(vpooled)
        imf = imf / imf.norm(dim=-1, keepdim=True)
        pred = (imf @ tf.T).argmax(-1).cpu().numpy()
        correct += sum(1 for p, y in zip(pred, b['label']) if p == y)
        total += len(b['label'])
    return 100 * correct / total


out = {}
for ckpt_name in ['model_state_last.pt', 'model_state_best.pt']:
    path = os.path.join('outputs/imagenet_zs_rerun/full_ft', ckpt_name)
    m = CLIPModel.from_pretrained('openai/clip-vit-base-patch32', local_files_only=True)
    m.load_state_dict(torch.load(path, map_location='cpu', weights_only=False))
    m = m.cuda().eval()
    zs_synset = zs_eval(m, names_full)
    zs_plain = zs_eval(m, names_plain)
    print('%s: synset+single=%.2f%%  plain+single=%.2f%%' % (ckpt_name, zs_synset, zs_plain), flush=True)
    out[ckpt_name] = {'synset_single_template': round(zs_synset, 2),
                      'plain_single_template': round(zs_plain, 2)}

out.update({'n_images': len(ds), 'paper_value': 7.38})
json.dump(out, open('outputs/imagenet_zs_rerun/full_ft/zero_shot_eval.json', 'w', encoding='utf-8'),
          ensure_ascii=False, indent=2)
print('saved outputs/imagenet_zs_rerun/full_ft/zero_shot_eval.json')
