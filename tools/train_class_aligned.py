"""A1 #6：类别对齐正则 LoRA 训练（补齐版，2026-08-16 起跑）。

L = L_clip + λ_reg · (1 − cos(x_i, c_{ŷ_i}))
  - ŷ_i：冻结 CLIP 在 ImageNet 类上的伪标签（训练前一次性预计算，按数据集索引取用）；
  - c：ImageNet 类质心（冻结模型在 5k 验证样本上算，EMA γ=0.01 微调，初始化即冻结质心）；
  - 训练配置与 a1_retrain 一致（Flickr30k 0..1999、batch 64、10 epoch、lr 1e-4、
    AdamW wd 0.01、cosine、LoRA both r8 α16）；
  - 每 epoch 记录 τ（ImageNet 5k，冻结 top-5 集 vs 当前模型排序）与训练损失；
  - 训练结束跑 50k 单模板零样本 top-1（对照 A1 的 both-LoRA 59.67）。

用法：
  conda run -n pytorch python tools/train_class_aligned.py --lambda-reg 0.1 --seed 42
扫描（后台）：
  for lr in 0 0.05 0.1 0.25 0.5; do conda run -n pytorch python tools/train_class_aligned.py --lambda-reg $lr --seed 42; done
输出：outputs/a1_class_aligned/lr{λ}/seed{seed}/results.json + per-epoch 权重。
"""
import os
import sys
import glob
import json
import random
import hashlib
import argparse

os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import torch
import torch.nn.functional as F
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingLR
from torch.utils.data import DataLoader, Dataset
from scipy import stats
from tqdm import tqdm
from transformers import CLIPModel, CLIPProcessor
from datasets import Dataset as HFDataset

from src.dataset import Flickr30kDataset, _collate_fn as _base_collate
from src.lora import apply_lora_to_model

TEMPLATE = 'a photo of a {}'
N_TAU = 5000
SAVE_ROOT = 'outputs/a1_class_aligned'


def imagenet_class_names(ds_in):
    """真实的 1000 个 ImageNet 类名（逗号截断）。

    2026-09-14 重下的 HF 分片其 ClassLabel 为 1001 项：末尾多一个占位类 'none'，
    若直接拿 names 建文本集会多出一个垃圾类，使 50k top-1 与 08-17 的 1000 类
    结果不可比（实测：当前数据真实标签 0..999，占位类无样本）。此处一律剔除。
    """
    names = list(ds_in.features['label'].names)
    if len(names) == 1001 and names[-1] == 'none':
        names = names[:1000]
    assert len(names) == 1000, '未预期的类别数: %d' % len(names)
    return [n.split(',')[0].strip().replace('_', ' ') for n in names]


def data_fingerprint():
    """记录本次评测所用的分片与冻结参照版本，便于日后核对数字出自哪份数据。"""
    parq = sorted(glob.glob('data/imagenet_hf/*.parquet'))
    h = hashlib.sha1()
    for p in parq:
        h.update(os.path.basename(p).encode())
        h.update(str(os.path.getsize(p)).encode())
    ref = os.path.join(SAVE_ROOT, 'frozen_refs.pt')
    return {'parquet_files': len(parq), 'parquet_sig': h.hexdigest()[:16],
            'refs_mtime': (int(os.path.getmtime(ref)) if os.path.exists(ref) else None),
            'class_names': 1000}


class IdxSubset(Dataset):
    """带数据集索引的子集（伪标签按索引取用）。"""

    def __init__(self, base, start, end):
        self.base, self.start, self.end = base, start, end

    def __len__(self):
        return self.end - self.start

    def __getitem__(self, i):
        item = dict(self.base[self.start + i])
        item['idx'] = self.start + i
        return item


def collate_idx(batch):
    idxs = torch.tensor([item.pop('idx') for item in batch])
    out = _base_collate(batch)
    out['idx'] = idxs
    return out


def build_frozen_refs():
    """冻结模型一次性产出：类质心、文本特征、5k 冻结分数/top-5、Flickr 伪标签。
    结果缓存到 outputs/a1_class_aligned/frozen_refs.pt，扫描多个 λ 时复用。"""
    cache_path = os.path.join(SAVE_ROOT, 'frozen_refs.pt')
    if os.path.exists(cache_path):
        ck = torch.load(cache_path, weights_only=False)
        print('frozen refs loaded from cache', flush=True)
        return ck['tf'], ck['cents'], ck['S0'], ck['topk5'], ck['y_pseudo'], ck['sub_indices']

    parq = sorted(glob.glob('data/imagenet_hf/*.parquet'))
    assert parq, 'no parquet shards'
    ds_in = HFDataset.from_parquet(parq)
    names = imagenet_class_names(ds_in)
    texts = [TEMPLATE.format(c) for c in names]
    rng = np.random.RandomState(42)
    idx = rng.choice(len(ds_in), N_TAU, replace=False)
    sub_indices = idx.tolist()
    sub = ds_in.select(list(idx))
    labels = torch.tensor(sub['label'])

    model = CLIPModel.from_pretrained('openai/clip-vit-base-patch32',
                                      local_files_only=True).cuda().eval()
    processor = CLIPProcessor.from_pretrained('openai/clip-vit-base-patch32',
                                              local_files_only=True)
    with torch.no_grad():
        ti = processor(text=texts, return_tensors='pt', padding=True).to('cuda')
        tout = model.text_model(**ti)
        pooled = tout[1] if isinstance(tout, tuple) else tout.pooler_output
        tf = F.normalize(model.text_projection(pooled), dim=-1)
        imgs = []
        for i in range(0, N_TAU, 64):
            b = sub[i:i + 64]
            inp = processor(images=b['image'], return_tensors='pt').to('cuda')
            vout = model.vision_model(**inp)
            vpooled = vout[1] if isinstance(vout, tuple) else vout.pooler_output
            imgs.append(F.normalize(model.visual_projection(vpooled), dim=-1))
            if (i // 64) % 20 == 0:
                print('frozen 5k %d/%d' % (i + len(b), N_TAU), flush=True)
        base = torch.cat(imgs)
    cls_ids = sorted(set(labels.tolist()))
    # 质心表必须按【类 ID】索引：训练时用 c_ema[y] 取值（y 为伪标签的类 ID）。
    # 旧实现是 torch.stack([... for c in cls_ids])，行序为 cls_ids 位置而非类 ID，
    # 只要缺失的类不在末尾，其后所有类的质心就整体错位（2026-09-14 定位）。
    # 缺失类用该类名的文本嵌入兜底，避免出现零向量使 loss 恒定。
    cents = tf.clone().float()
    missing = [i for i in range(len(names)) if i not in set(cls_ids)]
    for c in cls_ids:
        cents[c] = F.normalize(base[labels == c].mean(0), dim=-1)
    if missing:
        print('  注意: 5k 子集缺 %d 个类，质心用其类名文本嵌入兜底: %s'
              % (len(missing), missing[:10]), flush=True)
    S0 = (base @ tf.T).float().cpu().numpy()
    topk5 = np.argsort(-S0, axis=1)[:, :5]

    # Flickr30k 训练集伪标签（按索引）
    ds_all = Flickr30kDataset('flickr30k', split='train', max_samples=None,
                              pre_tokenize=True)
    lab_loader = DataLoader(IdxSubset(ds_all, 0, 2000), batch_size=64, shuffle=False,
                            num_workers=0, collate_fn=collate_idx)
    y_pseudo = torch.zeros(2000, dtype=torch.long)
    with torch.no_grad():
        for batch in tqdm(lab_loader, desc='frozen pseudo-labels', leave=False):
            out = model(pixel_values=batch['image'].cuda(),
                        input_ids=batch['input_ids'].cuda(),
                        attention_mask=batch['attention_mask'].cuda(), return_loss=False)
            ie = F.normalize(out.image_embeds, dim=-1)
            y_pseudo[batch['idx']] = (ie @ tf.T).argmax(1).cpu()
    print('pseudo-labels done; frozen refs built', flush=True)
    torch.save({'tf': tf.cpu(), 'cents': cents.cpu(), 'S0': S0, 'topk5': topk5,
                'y_pseudo': y_pseudo, 'sub_indices': sub_indices}, cache_path)
    print('frozen refs cached to', cache_path, flush=True)
    return tf, cents, S0, topk5, y_pseudo, sub_indices


def compute_tau(model, processor, sub, tf, S0, topk5):
    """当前模型在 5k 样本上的 τ（冻结 top-5 集 vs 当前排序）。"""
    with torch.no_grad():
        imgs = []
        for i in range(0, N_TAU, 64):
            b = sub[i:i + 64]
            inp = processor(images=b['image'], return_tensors='pt').to('cuda')
            vout = model.vision_model(**inp)
            vpooled = vout[1] if isinstance(vout, tuple) else vout.pooler_output
            imgs.append(F.normalize(model.visual_projection(vpooled), dim=-1))
        cur = torch.cat(imgs)
    Sc = (cur @ tf.T).float().cpu().numpy()
    taus = []
    for i in range(N_TAU):
        k5 = topk5[i]
        r1, r2 = S0[i][k5], Sc[i][k5]
        if np.std(r1) < 1e-12 or np.std(r2) < 1e-12:
            continue
        t, _ = stats.kendalltau(r1, r2)
        if np.isfinite(t):
            taus.append(t)
    return float(np.mean(taus))


def eval_50k(model, processor, texts):
    """50k 单模板零样本 top-1（整验证集，14 分片）。"""
    parq = sorted(glob.glob('data/imagenet_hf/*.parquet'))
    ds_in = HFDataset.from_parquet(parq)
    with torch.no_grad():
        ti = processor(text=texts, return_tensors='pt', padding=True).to('cuda')
        tout = model.text_model(**ti)
        pooled = tout[1] if isinstance(tout, tuple) else tout.pooler_output
        tf = F.normalize(model.text_projection(pooled), dim=-1)
        correct = 0
        total = 0
        for shard in parq:
            d = HFDataset.from_parquet(shard)
            for i in range(0, len(d), 64):
                b = d[i:i + 64]
                inp = processor(images=b['image'], return_tensors='pt').to('cuda')
                vout = model.vision_model(**inp)
                vpooled = vout[1] if isinstance(vout, tuple) else vout.pooler_output
                ie = F.normalize(model.visual_projection(vpooled), dim=-1)
                pred = (ie @ tf.T).argmax(1).cpu().numpy()
                labs_b = np.array(b['label'])          # 与 b 的 image 数量天然对齐
                correct += (pred == labs_b).sum()
                total += len(labs_b)
    return float(correct / total * 100)


def eval_val_loss(model, ds_all):
    """Flickr30k 2000..3000 的 CLIP 对比损失（早停对照）。调用前请自行 model.eval()。"""
    val_ds = torch.utils.data.Subset(ds_all, range(2000, 3000))
    val_loader = DataLoader(val_ds, batch_size=64, shuffle=False,
                            num_workers=0, collate_fn=_base_collate)
    tot, n = 0.0, 0
    with torch.no_grad():
        for batch in val_loader:
            out = model(pixel_values=batch['image'].cuda(),
                        input_ids=batch['input_ids'].cuda(),
                        attention_mask=batch['attention_mask'].cuda(), return_loss=False)
            ie = F.normalize(out.image_embeds, dim=-1)
            te = F.normalize(out.text_embeds, dim=-1)
            logits = model.logit_scale.exp() * ie @ te.T
            lab = torch.arange(ie.shape[0], device='cuda')
            loss = (F.cross_entropy(logits, lab) + F.cross_entropy(logits.T, lab)) / 2
            tot += loss.item() * ie.shape[0]
            n += ie.shape[0]
    return tot / n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--lambda-reg', type=float, default=0.1)
    ap.add_argument('--seed', type=int, default=42)
    ap.add_argument('--epochs', type=int, default=10)
    ap.add_argument('--ema-gamma', type=float, default=0.01)
    ap.add_argument('--no-ema', action='store_true',
                    help='变体：固定冻结质心（不做 EMA 微调）')
    ap.add_argument('--no-eval-50k', action='store_true', help='冒烟用：跳过 50k 评测')
    ap.add_argument('--tau-every-epoch', action='store_true',
                    help='逐 epoch 算 τ（默认关闭；权重每 epoch 都存，需要时用 --eval-only 补）')
    ap.add_argument('--eval-only', action='store_true',
                    help='加载已存 epoch{epochs}.pt，只跑最终 τ + 50k 评测（训练已完成时用）')
    ap.add_argument('--epoch', type=int, default=None,
                    help='eval-only 时加载的 epoch（默认=--epochs；用于逐 epoch 轨迹）')
    args = ap.parse_args()

    torch.manual_seed(args.seed)
    np.random.seed(args.seed)
    random.seed(args.seed)

    mode_tag = '_noema' if args.no_ema else ''
    save_dir = os.path.join(SAVE_ROOT, 'lr%s%s' % (args.lambda_reg, mode_tag),
                            'seed%d' % args.seed)
    os.makedirs(save_dir, exist_ok=True)

    # ---- 冻结参照 ----
    tf, cents, S0, topk5, y_pseudo, sub_indices = build_frozen_refs()
    tf = tf.cuda()
    processor = CLIPProcessor.from_pretrained('openai/clip-vit-base-patch32',
                                              local_files_only=True)
    parq = sorted(glob.glob('data/imagenet_hf/*.parquet'))
    ds_in = HFDataset.from_parquet(parq)
    names = imagenet_class_names(ds_in)
    texts = [TEMPLATE.format(c) for c in names]
    sub = ds_in.select(sub_indices)
    torch.cuda.empty_cache()

    # ---- 训练 ----
    ds_all = Flickr30kDataset('flickr30k', split='train', max_samples=None,
                              pre_tokenize=True)
    train_loader = DataLoader(IdxSubset(ds_all, 0, 2000), batch_size=64, shuffle=True,
                              num_workers=0, collate_fn=collate_idx)

    model = CLIPModel.from_pretrained('openai/clip-vit-base-patch32', local_files_only=True)
    model, lora_layers, _ = apply_lora_to_model(model, rank=8, alpha=16.0,
                                                apply_to_vision=True, apply_to_text=True)
    model = model.cuda()

    if args.eval_only:
        ep = args.epoch if args.epoch is not None else args.epochs
        ck = torch.load(os.path.join(save_dir, 'epoch%d.pt' % ep),
                        weights_only=False)
        sd = ck['lora_state_dict']
        for k, v in lora_layers.items():
            v.lora_A.data.copy_(sd[k]['A'].to(v.lora_A.device, v.lora_A.dtype))
            v.lora_B.data.copy_(sd[k]['B'].to(v.lora_B.device, v.lora_B.dtype))
        model.eval()
        tau_final = compute_tau(model, processor, sub, tf, S0, topk5)
        top1_50k = None if args.no_eval_50k else eval_50k(model, processor, texts)
        val_loss = eval_val_loss(model, ds_all)
        out = {'lambda_reg': args.lambda_reg, 'seed': args.seed,
               'history': [], 'eval_only': True, 'eval_epoch': ep,
               'tau_final': tau_final, 'top1_50k': top1_50k, 'val_loss': val_loss,
               'fingerprint': data_fingerprint()}
        with open(os.path.join(save_dir, 'eval_epoch%d.json' % ep), 'w', encoding='utf-8') as f:
            json.dump(out, f, indent=1, ensure_ascii=False)
        print('eval-only lr%.2g ep%d: tau=%.4f top1_50k=%.2f val_loss=%.4f' %
              (args.lambda_reg, ep, tau_final, top1_50k, val_loss), flush=True)
        return

    # 只训练 LoRA 参数：apply_lora_to_model 只替换 Linear 层，Embedding/LayerNorm
    # 仍 requires_grad=True——若按 requires_grad 收参，基座会被直接更新，导致
    # "进程内模型（LoRA+部分全参）≠ 存档模型（纯 LoRA）"的假崩塌（已诊断定位）。
    trainable = [p for n, p in model.named_parameters() if p.requires_grad and 'lora_' in n]
    opt = AdamW(trainable, lr=1e-4, weight_decay=0.01)
    sched = CosineAnnealingLR(opt, T_max=args.epochs * len(train_loader))

    c_ema = cents.cuda().clone()          # EMA 质心，初始化 = 冻结质心

    history = []
    step = 0
    for epoch in range(1, args.epochs + 1):
        model.train()
        tot_loss, tot_clip, tot_align = 0.0, 0.0, 0.0
        n_b = 0
        for batch in tqdm(train_loader, desc='lr%.2g ep%d' % (args.lambda_reg, epoch),
                          leave=False):
            opt.zero_grad(set_to_none=True)
            out = model(pixel_values=batch['image'].cuda(),
                        input_ids=batch['input_ids'].cuda(),
                        attention_mask=batch['attention_mask'].cuda(), return_loss=False)
            ie = F.normalize(out.image_embeds, dim=-1)
            te = F.normalize(out.text_embeds, dim=-1)
            logits = model.logit_scale.exp() * ie @ te.T
            lab = torch.arange(ie.shape[0], device='cuda')
            loss_clip = (F.cross_entropy(logits, lab) + F.cross_entropy(logits.T, lab)) / 2
            # 类别对齐正则（伪标签 → EMA 质心，detach）
            y = y_pseudo[batch['idx']].cuda()
            cc = F.normalize(c_ema[y], dim=-1).detach()
            loss_align = (1.0 - (ie * cc).sum(-1)).mean()
            loss = loss_clip + args.lambda_reg * loss_align
            loss.backward()
            opt.step()
            sched.step()
            # EMA 更新（当前嵌入）；--no-ema 变体保持冻结质心
            if not args.no_ema:
                with torch.no_grad():
                    for cls in y.unique():
                        m = (y == cls)
                        mu = F.normalize(ie[m].mean(0), dim=-1)
                        c_ema[cls] = F.normalize((1 - args.ema_gamma) * c_ema[cls]
                                                 + args.ema_gamma * mu, dim=-1)
            tot_loss += loss.item()
            tot_clip += loss_clip.item()
            tot_align += loss_align.item()
            n_b += 1
            step += 1
        # epoch 尾：τ（默认关闭——逐 epoch 权重都会存盘，需要时用 --eval-only 精确补测，
        # 免得每次训练多花 ~7 分钟）
        hist = {'epoch': epoch, 'train_loss': tot_loss / n_b,
                'clip_loss': tot_clip / n_b, 'align_loss': tot_align / n_b}
        if args.tau_every_epoch:
            model.eval()
            hist['tau'] = compute_tau(model, processor, sub, tf, S0, topk5)
        history.append(hist)
        sd = {k: {'A': v.lora_A.data.clone().cpu(), 'B': v.lora_B.data.clone().cpu()}
              for k, v in lora_layers.items()}
        torch.save({'epoch': epoch, 'lora_state_dict': sd},
                   os.path.join(save_dir, 'epoch%d.pt' % epoch))
        print('lr%.2g ep%d: loss=%.4f clip=%.4f align=%.4f%s' %
              (args.lambda_reg, epoch, hist['train_loss'], hist['clip_loss'],
               hist['align_loss'],
               (' tau=%.4f' % hist['tau']) if 'tau' in hist else ''), flush=True)

    # ---- 50k 零样本 + 端点 val loss ----
    model.eval()
    top1_50k = None
    if not args.no_eval_50k:
        top1_50k = eval_50k(model, processor, texts)
        print('lr%.2g 50k top1=%.2f' % (args.lambda_reg, top1_50k), flush=True)
    val_loss = eval_val_loss(model, ds_all)
    print('lr%.2g 端点 val_loss=%.4f' % (args.lambda_reg, val_loss), flush=True)

    out = {'lambda_reg': args.lambda_reg, 'seed': args.seed, 'history': history,
           'top1_50k': top1_50k, 'val_loss': val_loss,
           'tau_final': history[-1].get('tau') if history else None,
           'ema': not args.no_ema, 'fingerprint': data_fingerprint()}
    with open(os.path.join(save_dir, 'results.json'), 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
    print('saved', os.path.join(save_dir, 'results.json'), flush=True)


if __name__ == '__main__':
    main()
