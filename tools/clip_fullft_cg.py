"""Measure Centroid Gap on the retrained full FT weights (compared with frozen on the same Flickr30k val subset).
Usage: python tools/clip_fullft_cg.py --ckpt-dir outputs/imagenet_zs_rerun/full_ft_s123
"""
import os, sys, argparse, json
os.environ['HF_HUB_OFFLINE'] = '1'
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader
from transformers import CLIPModel, CLIPProcessor
from src.dataset import Flickr30kDataset, _collate_fn

parser = argparse.ArgumentParser()
parser.add_argument('--ckpt-dir', type=str, default='outputs/imagenet_zs_rerun/full_ft')
args = parser.parse_args()

ds_all = Flickr30kDataset('flickr30k', split='train', max_samples=None, pre_tokenize=True)
val_ds = torch.utils.data.Subset(ds_all, range(2000, 3000))
loader = DataLoader(val_ds, batch_size=64, shuffle=False, num_workers=0, collate_fn=_collate_fn)
processor = CLIPProcessor.from_pretrained('openai/clip-vit-base-patch32', local_files_only=True)


@torch.no_grad()
def centroid_gap(model):
    ie_all, te_all = [], []
    for batch in loader:
        out = model(pixel_values=batch['image'].cuda(),
                    input_ids=batch['input_ids'].cuda(),
                    attention_mask=batch['attention_mask'].cuda())
        ie_all.append(F.normalize(out.image_embeds, dim=-1))
        te_all.append(F.normalize(out.text_embeds, dim=-1))
    ie = torch.cat(ie_all)
    te = torch.cat(te_all)
    return torch.norm(ie.mean(0) - te.mean(0), p=2).item()


frozen = CLIPModel.from_pretrained('openai/clip-vit-base-patch32', local_files_only=True).cuda().eval()
cg0 = centroid_gap(frozen)
ft = CLIPModel.from_pretrained('openai/clip-vit-base-patch32', local_files_only=True)
ft.load_state_dict(torch.load(os.path.join(args.ckpt_dir, 'model_state_last.pt'),
                             map_location='cpu', weights_only=False))
cg1 = centroid_gap(ft.cuda().eval())
print('%s: frozen CG = %.4f | full-FT CG = %.4f | CGΔ = %+.4f' % (args.ckpt_dir, cg0, cg1, cg1 - cg0))

out = {'frozen_centroid_gap': round(cg0, 4), 'full_ft_centroid_gap': round(cg1, 4),
       'cg_delta': round(cg1 - cg0, 4), 'val_subset': 'flickr30k captions 2000:3000',
       'ckpt_dir': args.ckpt_dir,
       'note': 'original run archived CGΔ=+0.189 (initial 0.8185 → final 1.0072)'}
json.dump(out, open(os.path.join(args.ckpt_dir, 'centroid_gap.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=2)
print('saved', os.path.join(args.ckpt_dir, 'centroid_gap.json'))
