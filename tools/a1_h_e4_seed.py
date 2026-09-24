"""A1 revision E4 -- checkpoints fine-tuned on data other than Flickr30k (answers R1.6).

Reviewer R1.6: all five archived checkpoints were fine-tuned on Flickr30k, so checkpoints trained
on other datasets are needed. This script (a) fine-tunes the archived LoRA configuration on
datasets other than Flickr30k and (b) evaluates every checkpoint it can reach -- new ones and the
archived Flickr30k ones -- with one single evaluator, so the cross-dataset comparison is
internally consistent.

Archived configuration (from tools/train_class_aligned.py + outputs/imagenet_zs/*/results.json):
    LoRA on both towers, rank 8, alpha 16, ONLY parameters whose name contains 'lora_' are
    trainable (strict LoRA test -- see the comment in train_class_aligned.py: collecting by
    requires_grad() silently full-finetunes the base because LayerNorm/Embedding stay trainable);
    AdamW lr 1e-4, weight decay 0.01, cosine schedule; batch 64; 10 epochs; 2000 train pairs
    (320 steps, exactly the archived runs); CLIP symmetric contrastive loss.
The Flickr30k reference runs draw rows 0..1999 of the train split. New datasets draw `--pairs`
samples uniformly at random (seeded) from their own train split, because their row order is
class-sorted; unique-image counts are recorded in the JSON for honesty about the difference.

Evaluation protocol (identical to tools/clip_a1_tau_trajectory.py, which produced the published
checkpoint tau values 0.791 / 0.750):
    frozen top-5 class sets (frozen scores) vs the checkpoint's own text-vs-image ranks on the
    fixed 5000-image ImageNet sample (RandomState(42)); tau = mean Kendall coefficient.
    top-1: checkpoint image embeddings arg-max against the checkpoint's own class text embeddings,
    reported on the 5000-image sample and on the full 50,000-image validation set.
    CG: centroid gap of the checkpoint on Flickr30k rows 2000..3000.
Both class-list conventions are reported (legacy1001 = the published tau tables, clean1000 = the
1000 real ImageNet classes) because the parquet shards carry a trailing placeholder class 'none'.

Usage:
    python tools/a1_rr_e4_train.py --dataset coco    --out outputs/a1_rr_e4_coco.json
    python tools/a1_rr_e4_train.py --dataset food101 --out outputs/a1_rr_e4_food101.json
    python tools/a1_rr_e4_train.py --dataset dtd     --out outputs/a1_rr_e4_dtd.json
    python tools/a1_rr_e4_train.py --eval-spec <spec.json> --out outputs/a1_rr_e4_eval.json
"""
import os
import sys
import json
import glob
import time
import random
import hashlib
import argparse

os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image
from scipy import stats
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingLR
from torch.utils.data import Dataset, DataLoader
from transformers import CLIPModel, CLIPProcessor, CLIPTokenizerFast
from datasets import Dataset as HFDataset

from src.dataset import Flickr30kDataset, COCODataset, get_clip_transform, _collate_fn
from src.lora import apply_lora_to_model

TEMPLATE = 'a photo of a {}'
N_TAU = 5000
PLACEHOLDER_IDX = 1000
CKPT_DIR = 'outputs/a1_rr_ckpt'
MODEL_ID = 'openai/clip-vit-base-patch32'


# ============================================================ data
class PilPairDataset(Dataset):
    """(image path or PIL, caption) pairs with the standard CLIP train-time transform."""

    def __init__(self, items):
        self.items = items
        self.transform = get_clip_transform(224, is_train=True)

    def __len__(self):
        return len(self.items)

    def __getitem__(self, i):
        src, caption = self.items[i]
        if isinstance(src, Image.Image):
            im = src.convert('RGB')
        else:                                   # str or pathlib.Path
            try:
                im = Image.open(src).convert('RGB')
            except Exception:
                im = Image.new('RGB', (224, 224))
        return {'image': self.transform(im), 'caption': caption}


def collate_pairs(batch, tok):
    images = torch.stack([b['image'] for b in batch])
    caps = [b['caption'] for b in batch]
    t = tok(caps, padding='max_length', truncation=True, max_length=77, return_tensors='pt')
    return {'image': images, 'input_ids': t['input_ids'], 'attention_mask': t['attention_mask'],
            'caption': caps}


def _tv_paths(ds):
    """File paths of a torchvision image dataset, if exposed (avoids holding 2000 PILs)."""
    for attr in ('_image_files', 'imgs'):
        v = getattr(ds, attr, None)
        if v is not None and len(v) == len(ds):
            return [x[0] if isinstance(x, (tuple, list)) else x for x in v]
    return None


def build_train_pairs(dataset, pairs, seed, ckpt_dir=None):
    """Returns (PilPairDataset, meta). Deterministic given (dataset, pairs, seed)."""
    rng = np.random.RandomState(seed)
    if dataset == 'coco':
        ds = COCODataset('coco', split='train')
        n = len(ds.samples)
        sel = sorted(rng.choice(n, min(pairs, n), replace=False).tolist())
        items = [(os.path.join(ds.image_dir, ds.samples[i]['image']), ds.samples[i]['caption'])
                 for i in sel]
        uniq = len({s[0] for s in items})
        meta = {'source': 'coco/train2014 + annotations/captions_train2014.json (src.dataset.COCODataset)',
                'split': 'train', 'n_pairs_total': n,
                'sampling': 'uniform without replacement over (image, caption) rows, seed %d' % seed,
                'caption_construction': 'real COCO captions'}
    elif dataset == 'flickr30k_ref':
        ds = Flickr30kDataset('flickr30k', split='train', max_samples=None, pre_tokenize=False)
        items = [(os.path.join(ds.image_dir, ds.samples[i]['image']), ds.samples[i]['caption'])
                 for i in range(min(pairs, len(ds.samples)))]
        uniq = len({s[0] for s in items})
        meta = {'source': 'flickr30k/, rows 0..%d (reference reproduction of the archived run)'
                          % (min(pairs, len(ds.samples)) - 1),
                'split': 'train', 'n_pairs_total': len(ds.samples),
                'sampling': 'first rows, exactly as the archived Flickr30k runs',
                'caption_construction': 'real Flickr30k captions'}
    elif dataset in ('food101', 'dtd'):
        import torchvision.datasets as tvds
        cls = {'food101': tvds.Food101, 'dtd': tvds.DTD}[dataset]
        ds = cls(root='data', split='train', download=False)
        n = len(ds)
        sel = sorted(rng.choice(n, min(pairs, n), replace=False).tolist())
        names = list(ds.classes)
        paths = _tv_paths(ds)
        items = []
        for i in sel:
            if paths is not None:
                items.append((paths[i], TEMPLATE.format(names[ds[i][1]].replace('_', ' '))))
            else:
                img, y = ds[i]
                items.append((img, TEMPLATE.format(names[y].replace('_', ' '))))
        uniq = len({s[0] for s in items}) if paths is not None else len(items)
        meta = {'source': '%s train split via torchvision (root="data")' % dataset, 'split': 'train',
                'n_pairs_total': n, 'n_classes': len(names),
                'sampling': 'uniform without replacement over images, seed %d' % seed,
                'caption_construction': "'a photo of a {class name}' (class-name protocol)"}
    else:
        raise ValueError('unknown dataset %r' % dataset)
    meta.update({'dataset': dataset, 'n_pairs_used': len(items), 'n_unique_images': uniq,
                 'ckpt_dir': ckpt_dir})
    return PilPairDataset(items), meta


# ============================================================ evaluation
def imagenet_names(ds_in):
    names = [n.split(',')[0].strip().replace('_', ' ') for n in ds_in.features['label'].names]
    assert len(names) in (1000, 1001), 'unexpected class list length %d' % len(names)
    legacy = names
    clean = [n for i, n in enumerate(names) if i != PLACEHOLDER_IDX]
    return legacy, clean


def kendall_topk(base_np, cur_np, topk):
    taus = []
    for i in range(len(base_np)):
        r1 = base_np[i][topk[i]]
        r2 = cur_np[i][topk[i]]
        if np.std(r1) < 1e-12 or np.std(r2) < 1e-12:
            continue
        t, _ = stats.kendalltau(r1, r2)
        if np.isfinite(t):
            taus.append(t)
    if not taus:
        return None
    return float(np.mean(taus))


@torch.no_grad()
def encode_images(model, processor, pil_list, batch=64):
    feats = []
    for i in range(0, len(pil_list), batch):
        inp = processor(images=pil_list[i:i + batch], return_tensors='pt').to('cuda')
        vout = model.vision_model(**inp)
        vpooled = vout[1] if isinstance(vout, tuple) else vout.pooler_output
        feats.append(F.normalize(model.visual_projection(vpooled), dim=-1))
    return torch.cat(feats)


@torch.no_grad()
def text_feats(model, processor, texts):
    ti = processor(text=texts, return_tensors='pt', padding=True).to('cuda')
    tout = model.text_model(**ti)
    pooled = tout[1] if isinstance(tout, tuple) else tout.pooler_output
    return F.normalize(model.text_projection(pooled), dim=-1)


@torch.no_grad()
def eval_50k(model, processor, text_sets):
    """Full 50,000-image ImageNet zero-shot top-1, one pass over the shards.

    text_sets: dict name -> list of texts; the checkpoint's own text tower encodes each set.
    Returns dict name -> top-1 (%).
    """
    tfs = {nm: text_feats(model, processor, texts) for nm, texts in text_sets.items()}
    correct = {nm: 0 for nm in text_sets}
    total = 0
    for shard in sorted(glob.glob('data/imagenet_hf/*.parquet')):
        d = HFDataset.from_parquet(shard)
        for i in range(0, len(d), 64):
            b = d[i:i + 64]
            inp = processor(images=b['image'], return_tensors='pt').to('cuda')
            vout = model.vision_model(**inp)
            vpooled = vout[1] if isinstance(vout, tuple) else vout.pooler_output
            ie = F.normalize(model.visual_projection(vpooled), dim=-1)
            labs = np.array(b['label'])
            for nm, tf in tfs.items():
                pred = (ie @ tf.T).argmax(1).cpu().numpy()
                correct[nm] += int((pred == labs).sum())
            total += len(labs)
    return {nm: float(c / total * 100) for nm, c in correct.items()}


def load_lora_checkpoint(model, lora_layers, path):
    ck = torch.load(path, map_location='cpu', weights_only=False)
    sd = ck['lora_state_dict'] if isinstance(ck, dict) and 'lora_state_dict' in ck else ck
    missing = set(sd) - set(lora_layers)
    extra = set(lora_layers) - set(sd)
    if missing or extra:
        raise ValueError('checkpoint/model LoRA key mismatch: %d unknown keys, %d unfilled keys '
                         '(first unknown=%s). Check --vision/--text flags.'
                         % (len(missing), len(extra), sorted(missing)[:2]))
    with torch.no_grad():
        for k, w in sd.items():
            lora_layers[k].lora_A.data.copy_(w['A'].to(lora_layers[k].lora_A.dtype))
            lora_layers[k].lora_B.data.copy_(w['B'].to(lora_layers[k].lora_B.dtype))
    return model


def build_lora(vision, text):
    m, layers, _ = apply_lora_to_model(
        CLIPModel.from_pretrained(MODEL_ID, local_files_only=True),
        rank=8, alpha=16.0, apply_to_vision=vision, apply_to_text=text)
    return m, layers


# ============================================================ main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dataset', default='coco',
                    choices=['coco', 'food101', 'dtd', 'flickr30k_ref'])
    ap.add_argument('--pairs', type=int, default=2000)
    ap.add_argument('--epochs', type=int, default=10)
    ap.add_argument('--seed', type=int, default=42)
    ap.add_argument('--batch', type=int, default=64)
    ap.add_argument('--lr', type=float, default=1e-4)
    ap.add_argument('--wd', type=float, default=0.01)
    ap.add_argument('--no-50k', action='store_true')
    ap.add_argument('--eval-spec', default=None,
                    help='JSON list of {tag, ckpt, vision, text, trained_on} to evaluate in one process')
    ap.add_argument('--seed-json', default=None,
                    help='re-run ONLY the evaluation of a completed run, rewriting its JSON in the '
                         'training-mode schema (uses that JSON\'s checkpoint + protocol)')
    ap.add_argument('--out', default=None)
    args = ap.parse_args()

    t0 = time.time()
    torch.manual_seed(args.seed)
    np.random.seed(args.seed)
    random.seed(args.seed)

    parq = sorted(glob.glob('data/imagenet_hf/*.parquet'))
    hsh = hashlib.sha1()
    for p in parq:
        hsh.update(os.path.basename(p).encode())
        hsh.update(str(os.path.getsize(p)).encode())
    shard_sig = hsh.hexdigest()[:16]

    processor = CLIPProcessor.from_pretrained(MODEL_ID, local_files_only=True)
    ds_in = HFDataset.from_parquet(parq)
    legacy_names, clean_names = imagenet_names(ds_in)
    print('class lists: legacy=%d clean=%d' % (len(legacy_names), len(clean_names)), flush=True)

    # ---- fixed evaluation sample ----
    rng = np.random.RandomState(42)
    idx = rng.choice(len(ds_in), N_TAU, replace=False)
    sub = ds_in.select(list(idx))
    labels = torch.tensor(sub['label'])
    lab_np = labels.numpy()
    sub_imgs = list(sub['image'])

    ds_f = Flickr30kDataset('flickr30k', split='train', max_samples=None, pre_tokenize=True)
    val_ds = torch.utils.data.Subset(ds_f, range(2000, 3000))
    val_loader = DataLoader(val_ds, batch_size=64, shuffle=False, num_workers=0,
                            collate_fn=_collate_fn)

    # ---- global frozen references, computed once for every checkpoint ----
    print('building frozen references ...', flush=True)
    fm = CLIPModel.from_pretrained(MODEL_ID, local_files_only=True).cuda().eval()
    fbase = encode_images(fm, processor, sub_imgs)
    G = {'base_np': {}, 'legacy_names': legacy_names, 'clean_names': clean_names}
    for conv_name, names in (('legacy1001', legacy_names), ('clean1000', clean_names)):
        ftf = text_feats(fm, processor, [TEMPLATE.format(c) for c in names])
        G['base_np'][conv_name] = (fbase @ ftf.T).float().cpu().numpy()
    fi_f, ft_f = [], []
    with torch.no_grad():
        for batch in val_loader:
            o = fm(pixel_values=batch['image'].cuda(), input_ids=batch['input_ids'].cuda(),
                   attention_mask=batch['attention_mask'].cuda(), return_loss=False)
            fi_f.append(F.normalize(o.image_embeds, dim=-1))
            ft_f.append(F.normalize(o.text_embeds, dim=-1))
    frozen_cg = (torch.cat(fi_f).mean(0) - torch.cat(ft_f).mean(0)).norm().item()
    frozen = {'tag': 'frozen', 'CG_flickr_val': round(frozen_cg, 6), 'image_only': {}}
    for conv_name in ('legacy1001', 'clean1000'):
        S = G['base_np'][conv_name]
        frozen['image_only'][conv_name] = {
            'top1_5k': round(float((S.argmax(1) == lab_np).mean() * 100), 4),
            'tau_by_k': {str(k): (None if k == 1 else 1.0) for k in (1, 3, 5, 10, 20)}}
    del fm, fbase
    torch.cuda.empty_cache()
    print('frozen CG=%.6f top1_5k=%s (%.1fs)'
          % (frozen_cg, {c: frozen['image_only'][c]['top1_5k'] for c in frozen['image_only']},
             time.time() - t0), flush=True)

    def eval_checkpoint(model, tag, do_50k=True):
        """Single evaluator for every checkpoint (frozen / archived / new)."""
        model = model.cuda().eval()
        base = encode_images(model, processor, sub_imgs)
        out = {'tag': tag, 'image_only': {}}
        for conv_name, names in (('legacy1001', legacy_names), ('clean1000', clean_names)):
            tf = text_feats(model, processor, [TEMPLATE.format(c) for c in names])
            S = (base @ tf.T).float().cpu().numpy()
            top1_5k = float((S.argmax(1) == lab_np).mean() * 100)
            taus = {}
            for k in (1, 3, 5, 10, 20):
                if k == 1:
                    taus['1'] = None
                    continue
                topk = np.argsort(-G['base_np'][conv_name], axis=1)[:, :k]
                t = kendall_topk(G['base_np'][conv_name], S, topk)
                taus[str(k)] = None if t is None else round(t, 6)
            out['image_only'][conv_name] = {'top1_5k': round(top1_5k, 4), 'tau_by_k': taus}
            print('   [%s] %s: top1_5k=%.2f tau5=%s' % (tag, conv_name, top1_5k, taus['5']),
                  flush=True)
        # CG of this checkpoint on the Flickr30k validation subset
        fi, ft = [], []
        with torch.no_grad():
            for batch in val_loader:
                o = model(pixel_values=batch['image'].cuda(),
                          input_ids=batch['input_ids'].cuda(),
                          attention_mask=batch['attention_mask'].cuda(), return_loss=False)
                fi.append(F.normalize(o.image_embeds, dim=-1))
                ft.append(F.normalize(o.text_embeds, dim=-1))
        out['CG_flickr_val'] = round((torch.cat(fi).mean(0) - torch.cat(ft).mean(0)).norm().item(), 6)
        if do_50k:
            t50 = eval_50k(model, processor, {
                'legacy1001': [TEMPLATE.format(c) for c in legacy_names],
                'clean1000': [TEMPLATE.format(c) for c in clean_names]})
            out['top1_50k_legacy1001'] = round(t50['legacy1001'], 4)
            out['top1_50k_clean1000'] = round(t50['clean1000'], 4)
        del base
        torch.cuda.empty_cache()
        return out

    # =============================================== evaluation-recovery mode
    # Used when a training run completed (its checkpoints are on disk) but the evaluation step was
    # lost -- e.g. a CUDA illegal-memory-access crash or a machine reboot. The output JSON has
    # EXACTLY the training-mode schema, so downstream readers need no special case; the recovery is
    # recorded in meta.recovered_evaluation. Sampler order is restored from the dataset meta.
    if args.seed_json:
        src = json.load(open(args.seed_json, encoding='utf-8'))
        sm = src['meta']
        dataset, seed = sm['dataset'], sm['seed']
        if args.dataset != dataset or args.seed != seed:
            raise SystemExit('--dataset/--seed (%s/%s) disagree with %s (%s/%s)'
                             % (args.dataset, args.seed, args.seed_json, dataset, seed))
        _, ds_meta = build_train_pairs(dataset, sm['data']['n_pairs_used'], seed,
                                       ckpt_dir=sm['data'].get('ckpt_dir'))
        ckpt_path = sm['checkpoint']
        if not os.path.exists(ckpt_path):
            raise SystemExit('checkpoint %s does not exist' % ckpt_path)
        m2, layers2 = build_lora(True, True)
        m2 = load_lora_checkpoint(m2, layers2, ckpt_path)
        res = eval_checkpoint(m2, '%s_r8_both' % dataset, do_50k=not args.no_50k)
        payload = {
            'meta': dict(sm, **{
                'seed_json_source': args.seed_json,
                'recovered_evaluation': {
                    'reason': 'the training run completed and wrote its epoch checkpoints, but the '
                              'evaluation step was lost (process killed / machine rebooted)',
                    'script': 'tools/a1_h_e4_seed.py --seed-json',
                    'rewritten_from': sm.get('script'),
                    'note': 'protocol identical to the original run: same evaluator, same frozen '
                            'references, same 5000-image sample, same 50k pass; only the JSON is '
                            'rewritten'}}),
            'frozen': src['frozen'], 'history': src['history'], 'result': res,
        }
        out_path = args.out or args.seed_json
        json.dump(payload, open(out_path, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
        print('\n%s (recovered): tau5=%s | top1_5k=%s | CG=%.4f | top1_50k=%s'
              % (dataset,
                 {c: res['image_only'][c]['tau_by_k']['5'] for c in res['image_only']},
                 {c: res['image_only'][c]['top1_5k'] for c in res['image_only']},
                 res['CG_flickr_val'],
                 {k: v for k, v in res.items() if k.startswith('top1_50k')}), flush=True)
        print('ALL DONE -> %s (%.1fs)' % (out_path, time.time() - t0), flush=True)
        return

    # =============================================== eval-only mode
    if args.eval_spec:
        spec = json.load(open(args.eval_spec, encoding='utf-8'))
        out_path = args.out or 'outputs/a1_rr_e4_eval.json'
        payload = {'meta': {'script': 'tools/a1_rr_e4_train.py --eval-spec',
                            'protocol': 'tools/clip_a1_tau_trajectory.py evaluator; shared frozen refs',
                            'model': MODEL_ID, 'shard_sig': shard_sig, 'n_tau_images': N_TAU,
                            'placeholder_class_index': PLACEHOLDER_IDX},
                   'frozen': frozen, 'checkpoints': []}
        for entry in spec:
            print('\n== eval %s (%s) ==' % (entry['tag'], entry['ckpt']), flush=True)
            try:
                m, layers = build_lora(bool(entry.get('vision', True)), bool(entry.get('text', True)))
                m = load_lora_checkpoint(m, layers, entry['ckpt'])
                r = eval_checkpoint(m, entry['tag'], do_50k=not args.no_50k)
                r['ckpt'] = entry['ckpt']
                r['lora'] = {'vision': bool(entry.get('vision', True)),
                             'text': bool(entry.get('text', True)), 'rank': 8, 'alpha': 16.0}
                r['trained_on'] = entry.get('trained_on', 'unknown')
                r['ok'] = True
                del m, layers
                torch.cuda.empty_cache()
            except Exception as e:
                import traceback
                r = {'tag': entry['tag'], 'ckpt': entry['ckpt'], 'ok': False,
                     'trained_on': entry.get('trained_on', 'unknown'),
                     'error': '%s: %s' % (type(e).__name__, str(e)[:400]),
                     'traceback_tail': traceback.format_exc()[-600:]}
                print('   EVAL FAILED: %s' % r['error'], flush=True)
                torch.cuda.empty_cache()
            payload['checkpoints'].append(r)
            json.dump(payload, open(out_path, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
        payload['meta']['runtime_s'] = round(time.time() - t0, 1)
        json.dump(payload, open(out_path, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
        print('\nALL DONE -> %s (%.1fs)' % (out_path, time.time() - t0), flush=True)
        return

    # =============================================== train mode
    # NOTE (a1_h): checkpoint directory is seed-aware so that the pre-existing
    # outputs/a1_rr_ckpt/<dataset>/epoch*.pt files (seed 42) are NEVER overwritten.
    seed_dir = os.path.join(CKPT_DIR, 'seed%d' % args.seed, args.dataset)
    os.makedirs(seed_dir, exist_ok=True)
    train_ds, ds_meta = build_train_pairs(args.dataset, args.pairs, args.seed, ckpt_dir=seed_dir)
    print('train pairs: %s' % ds_meta, flush=True)
    tok = CLIPTokenizerFast.from_pretrained(MODEL_ID, local_files_only=True)
    train_loader = DataLoader(train_ds, batch_size=args.batch, shuffle=True, num_workers=0,
                              collate_fn=lambda b: collate_pairs(b, tok))

    model, lora_layers = build_lora(True, True)
    model = model.cuda()
    trainable = [p for n, p in model.named_parameters() if p.requires_grad and 'lora_' in n]
    n_trainable = sum(p.numel() for p in trainable)
    total_params = sum(p.numel() for p in model.parameters())
    n_lora_named = sum(p.numel() for n, p in model.named_parameters() if 'lora_' in n)
    print('trainable LoRA params: %d (all lora_ params: %d) / %d total'
          % (n_trainable, n_lora_named, total_params), flush=True)
    opt = AdamW(trainable, lr=args.lr, weight_decay=args.wd)
    sched = CosineAnnealingLR(opt, T_max=args.epochs * len(train_loader))

    history = []
    for epoch in range(1, args.epochs + 1):
        model.train()
        tot, nb = 0.0, 0
        for batch in train_loader:
            opt.zero_grad(set_to_none=True)
            o = model(pixel_values=batch['image'].cuda(), input_ids=batch['input_ids'].cuda(),
                      attention_mask=batch['attention_mask'].cuda(), return_loss=False)
            ie = F.normalize(o.image_embeds, dim=-1)
            te = F.normalize(o.text_embeds, dim=-1)
            logits = model.logit_scale.exp() * ie @ te.T
            lab = torch.arange(ie.shape[0], device='cuda')
            loss = (F.cross_entropy(logits, lab) + F.cross_entropy(logits.T, lab)) / 2
            loss.backward()
            opt.step()
            sched.step()
            tot += loss.item()
            nb += 1
        sd = {k: {'A': v.lora_A.data.clone().cpu(), 'B': v.lora_B.data.clone().cpu()}
              for k, v in lora_layers.items()}
        torch.save({'epoch': epoch, 'lora_state_dict': sd, 'config': vars(args)},
                   os.path.join(seed_dir, 'epoch%d.pt' % epoch))
        history.append({'epoch': epoch, 'train_loss': tot / nb})
        print('  [%s] epoch %d/%d loss=%.4f (%.1fs)'
              % (args.dataset, epoch, args.epochs, tot / nb, time.time() - t0), flush=True)

    ckpt_path = os.path.join(seed_dir, 'epoch%d.pt' % args.epochs)
    m2, layers2 = build_lora(True, True)
    m2 = load_lora_checkpoint(m2, layers2, ckpt_path)
    res = eval_checkpoint(m2, '%s_r8_both' % args.dataset, do_50k=not args.no_50k)

    payload = {
        'meta': {
            'script': 'tools/a1_h_e4_seed.py',
            'experiment': 'A1 hardening item 2 -- seed spread for the non-Flickr30k LoRA checkpoints',
            'derived_from': 'tools/a1_rr_e4_train.py (verbatim trainer/evaluator; the ONLY change '
                            'is that checkpoints are written to outputs/a1_rr_ckpt/seed<seed>/'
                            '<dataset>/ so the pre-existing seed-42 checkpoints are preserved)',
            'model': MODEL_ID, 'dataset': args.dataset, 'epochs': args.epochs, 'seed': args.seed,
            'batch': args.batch, 'lr': args.lr, 'weight_decay': args.wd,
            'lora': {'rank': 8, 'alpha': 16.0, 'vision': True, 'text': True,
                     'trainable_selection': "named_parameters() with requires_grad and 'lora_' in name"},
            'n_trainable_lora_params': n_trainable, 'n_total_params': total_params,
            'n_steps': args.epochs * len(train_loader), 'data': ds_meta,
            'eval_protocol': 'tools/clip_a1_tau_trajectory.py evaluator; frozen top-5 sets; '
                             'checkpoint scores image x text with its OWN text tower',
            'checkpoint': ckpt_path, 'shard_sig': shard_sig, 'n_tau_images': N_TAU,
            'placeholder_class_index': PLACEHOLDER_IDX,
            'runtime_s': round(time.time() - t0, 1),
        },
        'frozen': frozen, 'history': history, 'result': res,
    }
    out_path = args.out or ('outputs/a1_rr_e4_%s.json' % args.dataset)
    json.dump(payload, open(out_path, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('\n%s: tau5=%s | top1_5k=%s | CG=%.4f | top1_50k=%s'
          % (args.dataset,
             {c: res['image_only'][c]['tau_by_k']['5'] for c in res['image_only']},
             {c: res['image_only'][c]['top1_5k'] for c in res['image_only']},
             res['CG_flickr_val'],
             {k: v for k, v in res.items() if k.startswith('top1_50k')}), flush=True)
    print('ALL DONE -> %s (%.1fs)' % (out_path, time.time() - t0), flush=True)


if __name__ == '__main__':
    main()
