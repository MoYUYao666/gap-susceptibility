"""Tier A1: Γ 块排序在四种参数化下的一致性 + 耦合偏差量化（论文局限 3 的直接测量）。

背景: 表示定理的证明假设重参数化落在正交子群内; LoRA/Adapter/BitFit 都是非正交的。
本脚本在冻结 CLIP ViT-B/32 上, 对同一对齐能量 E 与同一任务梯度 u, 分别在
  (a) full  : 全参数梯度,
  (b) lora  : 注意力投影的 LoRA 子空间 (r=8, q/k/v/out, 两个编码器),
  (c) adapter: 注意力输出后的 bottleneck 适配器 (64),
  (d) bitfit: 仅偏置,
四种可训练子空间内计算 Γ_k = Σ_{θ∈block} ⟨∇_θE, ∇_θL⟩, 报告:
  1) 各参数化下的块排序 (E ∈ {DG*, GD, negcos} × 3 批);
  2) 与 full 的逐块耦合偏差 ε_k = |Γ^peft_k − Γ^full_k| / |Γ^full_k|;
  3) 参数化两两之间的块排序 Spearman 相关。
输出: outputs/clip_peft_gamma_ordering.json
"""
import os
import sys
import json
import io
import math
import collections

os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from PIL import Image
from transformers import CLIPModel, CLIPProcessor
from datasets import load_dataset

MDIR = 'models/clip-vit-base-patch32'
SUB = 'outputs/ocean_subset.json'
OUT = 'outputs/clip_peft_gamma_ordering.json'
TEMPLATE = 'a photo of a {}'
N_BATCH = 3
BS = 48
LORA_R = 8
ADAPTER_BOTTLENECK = 64


# ---------------- PEFT 模块(手工实现, 便于按前缀分块) ----------------
class LoRALinear(nn.Module):
    """W x + scale * B (A x); 仅 A/B 可训练(基座冻结)。

    注: 标准 LoRA 把 B 初始化为 0 → 在初始化点 A 的梯度恒为 0, 耦合只有半个子空间
    且量级远小于全参数化(维度/尺度伪影)。为做**参数化几何**层面的对比, 这里把 B 以
    小尺度随机初始化, 使两个因子在初始化点都携带梯度(尺度与 kaiming(A) 匹配)。
    """

    def __init__(self, base: nn.Linear, r: int = LORA_R, alpha: int = 16, b_scale: float = 1e-2):
        super().__init__()
        self.base = base
        self.r = r
        self.scale = alpha / r
        self.lora_A = nn.Parameter(torch.empty(r, base.in_features))
        self.lora_B = nn.Parameter(torch.empty(base.out_features, r))
        nn.init.kaiming_uniform_(self.lora_A, a=math.sqrt(5))
        nn.init.normal_(self.lora_B, std=b_scale)

    def forward(self, x):
        return self.base(x) + self.scale * (x @ self.lora_A.t() @ self.lora_B.t())


class AdapterAttn(nn.Module):
    """注意力输出后接 bottleneck 残差适配器 h <- h + W_up relu(W_down h)。"""

    def __init__(self, attn: nn.Module, dim: int, bottleneck: int = ADAPTER_BOTTLENECK,
                 up_scale: float = 1e-2):
        super().__init__()
        self.attn = attn
        self.down = nn.Linear(dim, bottleneck)
        self.up = nn.Linear(bottleneck, dim)
        nn.init.normal_(self.up.weight, std=up_scale)
        nn.init.zeros_(self.up.bias)

    def forward(self, *a, **k):
        out = self.attn(*a, **k)
        if isinstance(out, tuple):
            h, rest = out[0], out[1:]
            return (h + self.up(F.relu(self.down(h))),) + tuple(rest)
        return out + self.up(F.relu(self.down(out)))


def add_lora(model, targets=('q_proj', 'k_proj', 'v_proj', 'out_proj')):
    """把两个编码器内的注意力投影替换为 LoRA 包装(基座 requires_grad=False)。"""
    n = 0
    for name, module in list(model.named_modules()):
        for child_name, child in list(module.named_children()):
            if child_name in targets and isinstance(child, nn.Linear):
                setattr(module, child_name, LoRALinear(child))
                n += 1
    for p in model.parameters():
        p.requires_grad = False
    for name, p in model.named_parameters():
        if 'lora_A' in name or 'lora_B' in name:
            p.requires_grad = True
    return n


def add_adapters(model, bottleneck=ADAPTER_BOTTLENECK):
    n = 0
    for enc in (model.vision_model, model.text_model):
        for layer in enc.encoder.layers:
            dim = layer.self_attn.out_proj.in_features
            layer.self_attn = AdapterAttn(layer.self_attn, dim, bottleneck)
            n += 1
    for p in model.parameters():
        p.requires_grad = False
    for name, p in model.named_parameters():
        if name.endswith('down.weight') or name.endswith('down.bias') \
                or name.endswith('up.weight') or name.endswith('up.bias'):
            p.requires_grad = True
    return n


def add_bitfit(model):
    for p in model.parameters():
        p.requires_grad = False
    n = 0
    for name, p in model.named_parameters():
        if name.endswith('bias'):
            p.requires_grad = True
            n += 1
    return n


BLOCKS = ['vision_trunk', 'visual_projection', 'text_model', 'text_projection']


def block_of(name):
    if name.startswith('vision_model'):
        return 'vision_trunk'
    if name.startswith('visual_projection'):
        return 'visual_projection'
    if name.startswith('text_model'):
        return 'text_model'
    if name.startswith('text_projection'):
        return 'text_projection'
    return None


def main():
    ds_ = json.load(open(SUB, encoding='utf-8'))
    classes = ds_['classes']
    idx = ds_['subset_idx']
    files = sorted(os.path.join('data/rare-species/data', f) for f in os.listdir('data/rare-species/data'))
    dd = load_dataset('parquet', data_files=files, split='train')
    imgs = []
    for j in idx[:BS * N_BATCH]:
        b = dd[j]['file_name']
        imgs.append(Image.open(io.BytesIO(b['bytes'])).convert('RGB')
                    if isinstance(b, dict) and b.get('bytes') else b.convert('RGB'))
    print('images:', len(imgs), flush=True)

    proc = CLIPProcessor.from_pretrained(MDIR, local_files_only=True)

    def e1(zI, zT):  # DG*
        return ((zI[:, None, :] - zT[None, :, :]) ** 2).mean()

    def e2(zI, zT):  # GD: 质心 + 标准差
        return (zI.mean(0) - zT.mean(0)).norm() + (zI.std(0) - zT.std(0)).norm()

    def e3(zI, zT):  # 负平均余弦
        return -(zI @ zT.t()).mean()

    EFNS = [('DGstar', e1), ('GD', e2), ('negcos', e3)]

    def measure(mode):
        """返回 (gamma[E][block] 均值, 每块可训练参数数) —— 每种模式独立加载模型。"""
        m = CLIPModel.from_pretrained(MDIR, local_files_only=True)
        if mode == 'lora':
            nmod = add_lora(m)
            ntr = sum(p.numel() for p in m.parameters() if p.requires_grad)
        elif mode == 'adapter':
            nmod = add_adapters(m)
            ntr = sum(p.numel() for p in m.parameters() if p.requires_grad)
        elif mode == 'bitfit':
            nmod = add_bitfit(m)
            ntr = sum(p.numel() for p in m.parameters() if p.requires_grad)
        else:
            for p in m.parameters():
                p.requires_grad = True
            nmod, ntr = 0, sum(p.numel() for p in m.parameters())
        m = m.cuda().eval()
        par = [(n, p) for n, p in m.named_parameters() if p.requires_grad]
        blk_sizes = collections.Counter()
        for n, p in par:
            b = block_of(n)
            if b:
                blk_sizes[b] += p.numel()
        print(f'[{mode}] modules wrapped={nmod} trainable={ntr/1e6:.3f}M', flush=True)

        # 文本特征(冻结, 与 e_sensitivity_v2 一致)
        ti = proc(text=[TEMPLATE.format(c) for c in classes], return_tensors='pt', padding=True).to('cuda')
        with torch.no_grad():
            t_out = m.text_model(**ti)
            tp = t_out[1] if isinstance(t_out, tuple) else t_out.pooler_output
            tf = F.normalize(m.text_projection(tp), dim=-1)

        acc = {name: collections.defaultdict(list) for name, _ in EFNS}
        for bi in range(N_BATCH):
            xs = torch.stack([proc(images=imgs[j])['pixel_values'][0]
                              for j in range(bi * BS, bi * BS + BS)]).to('cuda')
            sel = np.random.RandomState(bi).choice(len(classes), BS, replace=False)
            tids = proc(text=[TEMPLATE.format(classes[k]) for k in sel], return_tensors='pt',
                        padding=True)['input_ids'].to('cuda')

            def task():
                out = m(pixel_values=xs, input_ids=tids)
                if_ = F.normalize(out.image_embeds, dim=-1)
                tf_ = F.normalize(out.text_embeds, dim=-1)
                logits = if_ @ tf_.t() * m.logit_scale.exp()
                lab = torch.arange(len(xs), device='cuda')
                return (F.cross_entropy(logits, lab) + F.cross_entropy(logits.t(), lab)) / 2

            for name, efn in EFNS:
                m.zero_grad()
                with torch.enable_grad():
                    # E 必须同时依赖两个模态: 文本分支也要在 enable_grad 下前向
                    # (否则 ∂E/∂θ ≡ 0 于所有文本侧参数, 文本块的 Γ 恒为 0 —— 设计缺陷)
                    t_out2 = m.text_model(**ti)
                    tp2 = t_out2[1] if isinstance(t_out2, tuple) else t_out2.pooler_output
                    tf2 = F.normalize(m.text_projection(tp2), dim=-1)
                    v_out = m.vision_model(pixel_values=xs)
                    vp = v_out[1] if isinstance(v_out, tuple) else v_out.pooler_output
                    vf = F.normalize(m.visual_projection(vp), dim=-1)
                    val = efn(vf, tf2)
                val.backward()
                gE = {n: (p.grad.detach().clone() if p.grad is not None else None) for n, p in par}
                m.zero_grad()
                task().backward()
                gdot = collections.defaultdict(float)
                for n, p in par:
                    if p.grad is None or gE.get(n) is None:
                        continue
                    b = block_of(n)
                    if b is None:
                        continue
                    gdot[b] += float((p.grad.detach() * gE[n]).sum())
                m.zero_grad()
                for b in BLOCKS:
                    acc[name][b].append(gdot[b])
            del xs, tids
            torch.cuda.empty_cache()
        out = {name: {b: float(np.mean(acc[name][b])) for b in BLOCKS} for name, _ in EFNS}
        del m
        torch.cuda.empty_cache()
        return out, dict(blk_sizes), ntr

    res, sizes, ntrain = {}, {}, {}
    for mode in ['full', 'lora', 'adapter', 'bitfit']:
        g, bs, nt = measure(mode)
        res[mode] = g
        sizes[mode] = bs
        ntrain[mode] = nt

    # 排序 + 两两 Spearman（同时给出"逐参数归一化"的耦合, 消除维度/尺度伪影）
    from scipy import stats
    norm = {}
    for mode in res:
        norm[mode] = {}
        for E in res[mode]:
            norm[mode][E] = {b: (res[mode][E][b] / max(sizes[mode].get(b, 1), 1)) for b in BLOCKS}
    orderings = {mode: {E: [b for b in sorted(BLOCKS, key=lambda x: -abs(norm[mode][E][x]))]
                        for E in res[mode]} for mode in res}
    spear = {}
    modes = list(res.keys())
    for i in range(len(modes)):
        for j in range(i + 1, len(modes)):
            for E in res[modes[i]]:
                a = [norm[modes[i]][E][b] for b in BLOCKS]
                b_ = [norm[modes[j]][E][b] for b in BLOCKS]
                rho, p = stats.spearmanr(a, b_)
                spear[f'{modes[i]}_vs_{modes[j]}|{E}'] = {'spearman': round(float(rho), 3),
                                                          'p': round(float(p), 4)}
    # 耦合偏差(归一化后) ε_k = |Γ^peft - Γ^full| / |Γ^full|
    dev = {}
    for mode in ['lora', 'adapter', 'bitfit']:
        dev[mode] = {}
        for b in BLOCKS:
            rel = [abs(norm[mode][E][b] - norm['full'][E][b]) / max(abs(norm['full'][E][b]), 1e-12)
                   for E in res['full']]
            dev[mode][b] = round(float(np.median(rel)), 4)
        allrel = [dev[mode][b] for b in BLOCKS]
        dev[mode]['_median'] = round(float(np.median(allrel)), 4)
        dev[mode]['_max'] = round(float(np.max(allrel)), 4)
    # 排序一致性汇总: 每个 E 下 full 与三 PEFT 的排序是否完全相同
    same = {E: all(orderings[m][E] == orderings['full'][E] for m in ['lora', 'adapter', 'bitfit'])
            for E in res['full']}
    json.dump({'blocks': BLOCKS, 'gamma': res, 'gamma_per_param': norm,
               'block_trainable_params': sizes,
               'trainable_total': ntrain, 'orderings': orderings, 'spearman': spear,
               'coupling_deviation_median_rel': dev, 'identical_order_to_full': same,
               'config': {'lora_r': LORA_R, 'adapter_bottleneck': ADAPTER_BOTTLENECK,
                          'batches': N_BATCH, 'batch_size': BS, 'E': [n for n, _ in EFNS],
                          'note': 'LoRA B 与 adapter up 采用非零小尺度随机初始化, 使两因子在初始化点均携带梯度'}},
              open(OUT, 'w', encoding='utf-8'), indent=1)
    print('orderings:', json.dumps(orderings, indent=1), flush=True)
    print('identical_order_to_full:', same, flush=True)
    print('DONE ->', OUT, flush=True)


if __name__ == '__main__':
    main()
