"""A1 enhancement experiment 2a: retrain text_only_r8 / both_r8 (LoRA), saving weights every epoch.
Configuration matches the original imagenet_zs run: Flickr30k captions 0..1999, batch 64, 10 epochs,
lr 1e-4, AdamW wd 0.01, cosine, seed 42, LoRA rank 8 alpha 16.
Weights saved to outputs/a1_retrain/{mode}/epoch{N}.pt (lora_state_dict + training curves).
"""
import os, sys, json, argparse, time
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import torch
import torch.nn.functional as F
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingLR
from torch.utils.data import DataLoader
from tqdm import tqdm
from transformers import CLIPModel
from src.dataset import Flickr30kDataset, _collate_fn
from src.lora import apply_lora_to_model

parser = argparse.ArgumentParser()
parser.add_argument('--mode', type=str, choices=['text_only', 'both'], required=True)
parser.add_argument('--seed', type=int, default=42)
args = parser.parse_args()

SAVE = 'outputs/a1_retrain/%s' % args.mode
os.makedirs(SAVE, exist_ok=True)
torch.manual_seed(args.seed)
import numpy as np, random
np.random.seed(args.seed); random.seed(args.seed)

ds_all = Flickr30kDataset('flickr30k', split='train', max_samples=None, pre_tokenize=True)
train_ds = torch.utils.data.Subset(ds_all, range(0, 2000))
val_ds = torch.utils.data.Subset(ds_all, range(2000, 3000))
train_loader = DataLoader(train_ds, batch_size=64, shuffle=True, num_workers=0, collate_fn=_collate_fn)
val_loader = DataLoader(val_ds, batch_size=64, shuffle=False, num_workers=0, collate_fn=_collate_fn)

model = CLIPModel.from_pretrained('openai/clip-vit-base-patch32', local_files_only=True)
model, lora_layers, _ = apply_lora_to_model(
    model, rank=8, alpha=16.0,
    apply_to_vision=(args.mode == 'both'), apply_to_text=True)
model = model.cuda()
trainable = [p for n, p in model.named_parameters() if p.requires_grad]
opt = AdamW(trainable, lr=1e-4, weight_decay=0.01)
sched = CosineAnnealingLR(opt, T_max=10 * len(train_loader))

step = 0
for epoch in range(1, 11):
    model.train()
    for batch in tqdm(train_loader, desc='%s ep%d' % (args.mode, epoch), leave=False):
        opt.zero_grad(set_to_none=True)
        out = model(pixel_values=batch['image'].cuda(),
                    input_ids=batch['input_ids'].cuda(),
                    attention_mask=batch['attention_mask'].cuda(), return_loss=False)
        ie = F.normalize(out.image_embeds, dim=-1)
        te = F.normalize(out.text_embeds, dim=-1)
        logits = model.logit_scale.exp() * ie @ te.T
        lab = torch.arange(ie.shape[0], device='cuda')
        loss = (F.cross_entropy(logits, lab) + F.cross_entropy(logits.T, lab)) / 2
        loss.backward()
        opt.step(); sched.step()
        step += 1
    sd = {k: {'A': v.lora_A.data.clone().cpu(), 'B': v.lora_B.data.clone().cpu()}
          for k, v in lora_layers.items()}
    torch.save({'epoch': epoch, 'lora_state_dict': sd}, os.path.join(SAVE, 'epoch%d.pt' % epoch))
    print('%s epoch %d saved (step %d)' % (args.mode, epoch, step), flush=True)
print('RETRAIN DONE', args.mode, flush=True)
