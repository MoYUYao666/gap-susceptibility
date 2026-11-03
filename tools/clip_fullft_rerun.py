"""Full FT 重训（复现 Paper 1 零样本节 full_ft 行）— 重建配置基于 8/3 存档 results.json：
epoch=10, step=320 → 32 steps/epoch ≈ batch 64 × 2000 样本（max_samples=2000, drop_last=False）。
其余超参取 src/config.py 默认：lr=1e-4, AdamW wd=0.01, cosine, seed=42, grad clip 1.0。
与原脚本的差异：本脚本保存完整模型权重（原 trainer 只存 LoRA，full_ft 权重丢失——本次修复）。
训练后自动评测 ImageNet-1K 零样本（synset+single 与 plain+single 两协议）。
"""
import os, sys, json, time, argparse
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import torch
import torch.nn.functional as F
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingLR
from torch.utils.data import DataLoader
from tqdm import tqdm

from src.dataset import Flickr30kDataset, _collate_fn

parser = argparse.ArgumentParser()
parser.add_argument('--seed', type=int, default=42)
parser.add_argument('--save-dir', type=str, default='outputs/imagenet_zs_rerun/full_ft')
args = parser.parse_args()

SAVE_DIR = args.save_dir
os.makedirs(SAVE_DIR, exist_ok=True)

torch.manual_seed(args.seed)
import numpy as np
np.random.seed(args.seed)
import random
random.seed(args.seed)

# ---------- 数据 ----------
ds_all = Flickr30kDataset('flickr30k', split='train', max_samples=None, pre_tokenize=True)
train_ds = torch.utils.data.Subset(ds_all, range(0, 2000))
val_ds = torch.utils.data.Subset(ds_all, range(2000, 3000))
train_loader = DataLoader(train_ds, batch_size=64, shuffle=True, num_workers=0,
                          collate_fn=_collate_fn)
val_loader = DataLoader(val_ds, batch_size=64, shuffle=False, num_workers=0,
                        collate_fn=_collate_fn)
print('train batches/epoch:', len(train_loader), '| val batches:', len(val_loader), flush=True)

# ---------- 模型 ----------
from transformers import CLIPModel, CLIPProcessor
model = CLIPModel.from_pretrained('openai/clip-vit-base-patch32', local_files_only=True)
processor = CLIPProcessor.from_pretrained('openai/clip-vit-base-patch32', local_files_only=True)
for p in model.parameters():
    p.requires_grad = True
model = model.cuda()
n_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
print('trainable params:', n_params, flush=True)

optimizer = AdamW([p for p in model.parameters() if p.requires_grad], lr=1e-4, weight_decay=0.01)
scheduler = CosineAnnealingLR(optimizer, T_max=10 * len(train_loader))
scaler = torch.amp.GradScaler('cuda')


def infonce_loss(model, batch, train=True):
    images = batch['image'].cuda()
    input_ids = batch['input_ids'].cuda()
    attention_mask = batch['attention_mask'].cuda()
    if train:
        out = model(pixel_values=images, input_ids=input_ids, attention_mask=attention_mask,
                    return_loss=False)
    else:
        with torch.no_grad():
            out = model(pixel_values=images, input_ids=input_ids, attention_mask=attention_mask,
                        return_loss=False)
    ie = F.normalize(out.image_embeds, dim=-1)
    te = F.normalize(out.text_embeds, dim=-1)
    logits = model.logit_scale.exp() * ie @ te.T
    labels = torch.arange(images.shape[0], device='cuda')
    loss = (F.cross_entropy(logits, labels) + F.cross_entropy(logits.T, labels)) / 2.0
    return loss, logits


def retrieval_r1(model, loader):
    model.eval()
    ie_all, te_all = [], []
    for batch in loader:
        with torch.no_grad():
            out = model(pixel_values=batch['image'].cuda(),
                        input_ids=batch['input_ids'].cuda(),
                        attention_mask=batch['attention_mask'].cuda())
        ie_all.append(F.normalize(out.image_embeds, dim=-1))
        te_all.append(F.normalize(out.text_embeds, dim=-1))
    ie = torch.cat(ie_all)
    te = torch.cat(te_all)
    sims = ie @ te.T
    i2t = (sims.argmax(1) == torch.arange(len(sims), device='cuda')).float().mean().item()
    t2i = (sims.argmax(0) == torch.arange(len(sims), device='cuda')).float().mean().item()
    model.train()
    return (i2t + t2i) / 2.0


def val_loss(model, loader):
    model.eval()
    tot, n = 0.0, 0
    for batch in loader:
        loss, _ = infonce_loss(model, batch, train=False)
        tot += loss.item()
        n += 1
    model.train()
    return tot / max(n, 1)


train_losses, val_losses, r1s = [], [], []
best_val = float('inf')
t0 = time.time()
step = 0
for epoch in range(1, 11):
    model.train()
    ep_loss, nb = 0.0, 0
    pbar = tqdm(train_loader, desc='Epoch %d' % epoch, leave=False)
    for batch in pbar:
        optimizer.zero_grad(set_to_none=True)
        with torch.amp.autocast('cuda'):
            loss, _ = infonce_loss(model, batch, train=True)
        scaler.scale(loss).backward()
        scaler.unscale_(optimizer)
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        scaler.step(optimizer)
        scaler.update()
        scheduler.step()
        ep_loss += loss.item()
        nb += 1
        step += 1
        pbar.set_postfix({'loss': '%.4f' % loss.item()})
    tl = ep_loss / max(nb, 1)
    vl = val_loss(model, val_loader)
    r1 = retrieval_r1(model, val_loader)
    train_losses.append(tl)
    val_losses.append(vl)
    r1s.append(r1)
    print('Epoch %d | train %.4f | val %.4f | R@1 %.3f | %.1fs' % (epoch, tl, vl, r1, time.time() - t0),
          flush=True)
    if vl < best_val:
        best_val = vl
        torch.save(model.state_dict(), os.path.join(SAVE_DIR, 'model_state_best.pt'))
torch.save(model.state_dict(), os.path.join(SAVE_DIR, 'model_state_last.pt'))
print('训练完成，总步数', step, flush=True)

# ---------- 零样本评测 ----------
from glob import glob
from datasets import Dataset
PARQ = sorted(glob('data/imagenet_hf/*.parquet'))
ds_zs = Dataset.from_parquet(PARQ)
names_full = ds_zs.features['label'].names
names_plain = [n.split(',')[0].strip() for n in names_full]


@torch.no_grad()
def zs_eval(m, class_names):
    texts = ['a photo of a {}'.format(c.replace('_', ' ')) for c in class_names]
    text_in = processor(text=texts, return_tensors='pt', padding=True).to('cuda')
    tout = m.text_model(**text_in)
    pooled = tout[1] if isinstance(tout, tuple) else tout.pooler_output
    tf = m.text_projection(pooled)
    tf = tf / tf.norm(dim=-1, keepdim=True)
    correct = total = 0
    for i in range(0, len(ds_zs), 64):
        b = ds_zs[i:i + 64]
        inp = processor(images=b['image'], return_tensors='pt').to('cuda')
        vout = m.vision_model(**inp)
        vpooled = vout[1] if isinstance(vout, tuple) else vout.pooler_output
        imf = m.visual_projection(vpooled)
        imf = imf / imf.norm(dim=-1, keepdim=True)
        pred = (imf @ tf.T).argmax(-1).cpu().numpy()
        correct += sum(1 for p, y in zip(pred, b['label']) if p == y)
        total += len(b['label'])
    return 100 * correct / total


model.eval()
zs_synset = zs_eval(model, names_full)
zs_plain = zs_eval(model, names_plain)
print('zero-shot ImageNet-1K: synset+single=%.2f  plain+single=%.2f' % (zs_synset, zs_plain), flush=True)

results = {
    'experiment': 'imagenet_zs_full_ft_rerun_2026-08_seed%d' % args.seed,
    'config': {
        'dataset': 'flickr30k subset (captions 0..1999, batch64 -> 32 steps/epoch)',
        'num_epochs': 10, 'lr': 1e-4, 'weight_decay': 0.01, 'scheduler': 'cosine',
        'seed': args.seed, 'amp': 'fp16', 'grad_clip': 1.0,
        'reconstruction_note': '超参从 8/3 存档 results.json (epoch=10, step=320) 与 src/config.py 默认值重建；原脚本已丢失',
    },
    'final_train_loss': train_losses[-1], 'final_val_loss': val_losses[-1],
    'best_val_loss': best_val, 'final_R1': r1s[-1],
    'train_losses': train_losses, 'val_losses': val_losses, 'r1_history': r1s,
    'n_trainable_params': n_params,
    'zero_shot_imagenet1k': {
        'synset_single_template': round(zs_synset, 2),
        'plain_single_template': round(zs_plain, 2),
        'n_images': len(ds_zs),
    },
    'paper_value': 7.38,
}
json.dump(results, open(os.path.join(SAVE_DIR, 'results.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=2)
print('结果已存', os.path.join(SAVE_DIR, 'results.json'))
