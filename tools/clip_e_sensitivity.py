"""合并稿提升#1: 跨 E 敏感性——Γ 排序是否依赖对齐能量 E 的选取。
CLIP ViT-B/32 冻结; K=4 块(vision trunk / visual_projection / text model / text_projection);
E 变体: E1=DG* 均方对距, E2=GD(质心+标准差), E3=负平均余弦;
u=InfoNCE 任务梯度(同批); Γ_k=<∇_kE, ∇_kL>; 报告 3 种 E 下的块排序 + Kendall W(一致性)。
输出: outputs/e_sensitivity.json
"""
import os, sys, json, io, collections
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image
from transformers import CLIPModel, CLIPProcessor
from datasets import load_dataset

MDIR = 'models/clip-vit-base-patch32'
SUB = 'outputs/ocean_subset.json'
OUT = 'outputs/e_sensitivity.json'
TEMPLATE = 'a photo of a {}'


def block_grads(m, grad_map, imgs_enc, txt_enc, loss_fn):
    """loss_fn(scaled_cos) -> loss; 返回每块梯度对 (gE, gL)。"""
    pass  # 简化: 直接在 main 中做


def main():
    ds_ = json.load(open(SUB, encoding='utf-8'))
    classes = ds_['classes']
    idx = ds_['subset_idx']
    dd = load_dataset('parquet', data_files=sorted(
        os.path.join('data/rare-species/data', f) for f in os.listdir('data/rare-species/data')),
        split='train')
    imgs = []
    for j in idx[:160]:
        b = dd[j]['file_name']
        imgs.append(Image.open(io.BytesIO(b['bytes'])).convert('RGB')
                    if isinstance(b, dict) and b.get('bytes') else b.convert('RGB'))
    m = CLIPModel.from_pretrained(MDIR, local_files_only=True).cuda().eval()
    p = CLIPProcessor.from_pretrained(MDIR, local_files_only=True)

    # 冻结全模型但保留要求的参数梯度路径(块粒度投影)
    for prm in m.parameters():
        prm.requires_grad = True
    blocks = {'vision_trunk': None, 'visual_projection': None,
              'text_model': None, 'text_projection': None}
    # 参数映射
    par = dict(m.named_parameters())
    blk_of = {}
    for name, prm in par.items():
        if name.startswith('vision_model'):
            blk_of[name] = 'vision_trunk'
        elif name.startswith('visual_projection'):
            blk_of[name] = 'visual_projection'
        elif name.startswith('text_model'):
            blk_of[name] = 'text_model'
        elif name.startswith('text_projection'):
            blk_of[name] = 'text_projection'
        else:
            blk_of[name] = 'wlogscale'

    def grads_by_block():
        g = collections.defaultdict(lambda: torch.zeros((), device='cuda'))
        for name, prm in par.items():
            if prm.grad is None or blk_of[name] == 'wlogscale':
                continue
            g[blk_of[name]] = g[blk_of[name]] + (prm.grad.reshape(-1) ** 2).sum()
        return {k: torch.sqrt(v).item() for k, v in g.items()}

    ti = p(text=[TEMPLATE.format(c) for c in classes], return_tensors='pt', padding=True).to('cuda')
    with torch.no_grad():
        t_out = m.text_model(**ti)
        tp = t_out[1] if isinstance(t_out, tuple) else t_out.pooler_output
        tf = F.normalize(m.text_projection(tp), dim=-1)
    res = {}
    acc_block = {k: [] for k in blocks}
    acc_block['wlogscale'] = []
    nb = 3
    for bi in range(nb):
        xs = torch.stack([p(images=imgs[j])['pixel_values'][0]
                          for j in range(bi * 48, bi * 48 + 48)]).to('cuda')
        with torch.no_grad():
            v_out = m.vision_model(**{'pixel_values': xs})
            vp = v_out[1] if isinstance(v_out, tuple) else v_out.pooler_output
            vf = F.normalize(m.visual_projection(vp), dim=-1)

        def e1(zI, zT):
            d = zI[:, None, :] - zT[None, :, :]
            return (d ** 2).mean()

        def e2(zI, zT):
            mu = (zI.mean(0) - zT.mean(0)).norm()
            sd = (zI.std(0) - zT.std(0)).norm()
            return mu + sd

        def e3(zI, zT):
            return -(zI @ zT.T).mean()

        # 任务梯度(InfoNCE): 48 图配对 48 个抽样类文本(无放回, 同批内对齐)
        sel = np.random.RandomState(bi).choice(len(classes), 48, replace=False)
        tids = p(text=[TEMPLATE.format(classes[kk]) for kk in sel], return_tensors='pt',
                 padding=True)['input_ids'].to('cuda')

        def task():
            out = m(pixel_values=xs, input_ids=tids)
            if_ = F.normalize(out.image_embeds, dim=-1)
            tf_ = F.normalize(out.text_embeds, dim=-1)
            logits = if_ @ tf_.T * m.logit_scale.exp()
            lab = torch.arange(len(xs), device='cuda')
            return (F.cross_entropy(logits, lab) + F.cross_entropy(logits.T, lab)) / 2

        for name, efn in [('E1_DGstar', e1), ('E2_GD', e2), ('E3_negcos', e3)]:
            # 双通道: 重算两个梯度并逐参数点积(单批, 两次 backward)
            m.zero_grad()
            with torch.enable_grad():
                v_out = m.vision_model(**{'pixel_values': xs})
                vp = v_out[1] if isinstance(v_out, tuple) else v_out.pooler_output
                vf2 = F.normalize(m.visual_projection(vp), dim=-1)
                val = efn(vf2, tf.detach())
            val.backward()
            gE2 = {nm: (prm.grad.detach().clone() if prm.grad is not None else None)
                   for nm, prm in par.items()}
            m.zero_grad()
            val2 = task()
            val2.backward()
            gdot = collections.defaultdict(lambda: 0.0)
            for nm, prm in par.items():
                if prm.grad is None or gE2.get(nm) is None or blk_of[nm] == 'wlogscale':
                    continue
                b = blk_of[nm]
                gdot[b] += float((prm.grad.detach() * gE2[nm]).sum())
            m.zero_grad()
            res.setdefault(name, collections.defaultdict(list))
            for b in dict(blocks):
                res[name][b].append(gdot[b])
            res[name]['_Evalue'].append(float(val.item()))
    out = {}
    for name, d in res.items():
        out[name] = {b: (round(float(np.mean(v)), 2) if isinstance(v, list) and v else None)
                     for b, v in d.items() if b != '_Evalue'}
        out[name]['_Evalue'] = round(float(np.mean(d['_Evalue'])), 3)
    # Kendall W: 各 E 下块序一致性
    from scipy import stats
    orderings = {}
    for name, d in out.items():
        keys = [b for b in d if not b.startswith('_')]
        vals = np.array([d[k] for k in keys])
        orderings[name] = [k for k in keys]
        orderings[name] = [keys[i] for i in np.argsort(-vals)]
    # 配对 Spearman/Kendall 相关系数
    ks = list(out.keys())
    cons = {}
    for i in range(len(ks)):
        for j in range(i + 1, len(ks)):
            a = out[ks[i]]; b = out[ks[j]]
            keys = [k for k in a if not k.startswith('_')]
            rho, p = stats.spearmanr([a[k] for k in keys], [b[k] for k in keys])
            cons['%s_vs_%s' % (ks[i], ks[j])] = {'spearman': round(float(rho), 3), 'p': round(float(p), 4)}
    json.dump({'blocks': list(blocks), 'orderings': orderings, 'kendall_consistency': cons, 'gamma': out},
              open(OUT, 'w', encoding='utf-8'), indent=1)
    print('orderings:', orderings, flush=True)
    print('consistency:', cons, flush=True)
    print('DONE ->', OUT, flush=True)


if __name__ == '__main__':
    main()
