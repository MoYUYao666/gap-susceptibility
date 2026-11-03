"""A2 提升⑥: MarineLife-16K 真实自然文本检索实验（D 升级版: 自然 QA 文本替代 BLIP 生成字幕）。
数据: HF MarineLife-16K/MarineLife-16K（实际发布 = 251 视频组/2012 帧/qa.jsonl; README 声称的 2000 caption 未完整发布）
协议:
  - query = QA 文本（question + answer_text 拼接, 自然句）
  - 图像库 = 全部帧; 视频级检索 = 每视频 8 帧平均嵌入
  - 若干句变体（q_ans / q_only / central_object）对照
  - 模型: openclip / oceanclip / bioclip（与 D 实验同加载器）
输出: outputs/ocean_ml16k_retrieval.json
运行: conda run -n pytorch python tools/clip_ocean_ml16k_retrieval.py
"""
import os, sys, json, glob, collections
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image
import open_clip
import importlib.util

spec = importlib.util.spec_from_file_location('ocm', 'tools/clip_ocean_margins.py')
ocm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ocm)

OUT = 'outputs/ocean_ml16k_retrieval.json'
ROOT = 'data/marinelife16k/data/selected_frames'


def build_queries(root):
    """遍历 qa.jsonl → (vid, q_txt, ans_txt, obj)。vid = site/video 组合(目录名跨 site 重复)。"""
    qlist = []
    for qf in sorted(glob.glob(os.path.join(root, '*', '*', 'qa.jsonl'))):
        vdir = os.path.dirname(qf)
        vid = os.path.basename(os.path.dirname(vdir)) + '/' + os.path.basename(vdir)
        with open(qf, encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    import json as _j
                    qa = _j.loads(line)
                except Exception:
                    continue
                q = qa.get('question', '')
                a = qa.get('answer_text', '')
                obj = qa.get('central_object', '')
                if q and a:
                    qlist.append({'vid': vid, 'q': q, 'a': a, 'obj': obj})
    return qlist


def encode_text_openclip(m, tok, texts, batch=64):
    out = []
    with torch.no_grad():
        for i in range(0, len(texts), batch):
            toks = tok(texts[i:i + batch]).to('cuda')
            out.append(F.normalize(m.encode_text(toks), dim=-1))
    return torch.cat(out)


def encode_img_openclip(m, pre, imgs, batch=32):
    out = []
    with torch.no_grad():
        for i in range(0, len(imgs), batch):
            xs = torch.stack([pre(im) for im in imgs[i:i + batch]]).to('cuda')
            out.append(F.normalize(m.encode_image(xs), dim=-1))
    return torch.cat(out)


def run(tag, m, pre, tok, queries, frames, vids):
    vid2idx = {v: i for i, v in enumerate(vids)}
    # 变体
    variants = {
        'q_ans': [q['q'] + ' ' + q['a'] for q in queries],
        'q_only': [q['q'] for q in queries],
        'obj': [q['obj'] for q in queries if q['obj']],
        'ans': [q['a'] for q in queries],
    }
    res = {}
    with torch.no_grad():
        imgs = [Image.open(fp).convert('RGB') for fp, _ in frames]
        fv = encode_img_openclip(m, pre, imgs)
        fv = F.normalize(fv, dim=-1)
        # 视频级表示
        fvi = []
        for v in vids:
            idx = [i for i, (_, vv) in enumerate(frames) if vv == v]
            fvi.append(fv[idx].mean(0))
        fvi = F.normalize(torch.stack(fvi), dim=-1)
        # 帧级: 视频组标签
        frames_vid = np.array([vid2idx[v] for _, v in frames])
        for vname, texts in variants.items():
            if not texts:
                continue
            tf = encode_text_openclip(m, tok, texts)
            # 视频级检索 (查询→视频平均嵌入)
            sim = tf @ fvi.T
            vid_gt = np.array([vid2idx[q['vid']] for q in queries if (q['obj'] if vname == 'obj' else True)])[:len(texts)]
            r1_v = float((sim.argmax(1).cpu().numpy() == vid_gt).mean() * 100)
            r5_v = float(sum(1 for i, g in enumerate(vid_gt) if g in sim[i].topk(5).indices.cpu().numpy()) / len(vid_gt) * 100)
            # 帧级检索: 命中同视频任何帧
            simf = tf @ fv.T
            q_gt = np.array([vid2idx[q['vid']] for q in queries])[:len(texts)]
            hit = (frames_vid[simf.argmax(1).cpu().numpy()] == q_gt)
            r1_f = float(hit.mean() * 100)
            r5f = np.array([q_gt[i] in frames_vid[simf[i].topk(5).indices.cpu().numpy()] for i in range(len(q_gt))])
            r5_f = float(r5f.mean() * 100)
            res[vname] = {'n': len(texts), 'video_R1': round(r1_v, 3), 'video_R5': round(r5_v, 3),
                          'frame_R1': round(r1_f, 3), 'frame_R5': round(r5_f, 3)}
            print('  %s %-8s n=%d videoR1=%.2f videoR5=%.2f frameR1=%.2f frameR5=%.2f' %
                  (tag, vname, len(texts), r1_v, r5_v, r1_f, r5_f), flush=True)
    return res


def main():
    queries = build_queries(ROOT)
    frames = sorted(glob.glob(os.path.join(ROOT, '*', '*', '*.jpg')))
    frame_meta = []
    for fp in frames:
        frame_meta.append((fp, os.path.basename(os.path.dirname(os.path.dirname(fp))) + '/' + os.path.basename(os.path.dirname(fp))))
    vids = sorted(set(v for _, v in frame_meta))
    print('videos=%d frames=%d queries=%d' % (len(vids), len(frame_meta), len(queries)), flush=True)
    res = {'meta': {'dataset': 'MarineLife-16K (HF; README claims 2000 videos, actual release: %d videos)' % len(vids),
                    'n_frames': len(frame_meta), 'n_queries': len(queries),
                    'note': 'qa.jsonl Q/A only; metadata/attributes_captions.csv absent in release'}}
    for tag in ['bioclip', 'oceanclip']:
        print('== %s ==' % tag, flush=True)
        m, pre = ocm.load_openclip(tag)
        tok = open_clip.get_tokenizer('ViT-B-16')
        res[tag] = run(tag, m, pre, tok, queries, frame_meta, vids)
        json.dump(res, open(OUT, 'w', encoding='utf-8'), indent=1)
        del m
        torch.cuda.empty_cache()
    # openclip 通用对照（复用 models/openclip transformer 无法直接做 open_clip 编码; 用官方 open_clip 权重下载版? 采用本地 CLIP transformer 版作对照）
    print('== openclip_tf ==', flush=True)
    from transformers import CLIPModel, CLIPProcessor
    m = CLIPModel.from_pretrained('models/openclip', local_files_only=True).cuda().eval()
    p = CLIPProcessor.from_pretrained('models/openclip', local_files_only=True)

    def enc_tf(texts):
        ti = p(text=texts, return_tensors='pt', padding=True, truncation=True).to('cuda')
        with torch.no_grad():
            out = m.text_model(**ti)
            pooled = out[1] if isinstance(out, tuple) else out.pooler_output
            return F.normalize(m.text_projection(pooled), dim=-1)

    def enc_vi(imgs):
        out = []
        with torch.no_grad():
            for i in range(0, len(imgs), 32):
                inp = p(images=imgs[i:i + 32], return_tensors='pt').to('cuda')
                vout = m.vision_model(**{k: v for k, v in inp.items() if 'pixel' in k})
                vp = vout[1] if isinstance(vout, tuple) else vout.pooler_output
                out.append(F.normalize(m.visual_projection(vp), dim=-1))
        return torch.cat(out)

    imgs = [Image.open(fp).convert('RGB') for fp, _ in frame_meta]
    fv = enc_vi(imgs)
    vid2idx = {v: i for i, v in enumerate(vids)}
    fvi = F.normalize(torch.stack([fv[[i for i, (_, vv) in enumerate(frame_meta) if vv == v]].mean(0) for v in vids]), dim=-1)
    frames_vid = np.array([vid2idx[v] for _, v in frame_meta])
    res['openclip_tf'] = {}
    for vname, texts in [('q_ans', [q['q'] + ' ' + q['a'] for q in queries]),
                         ('q_only', [q['q'] for q in queries]),
                         ('ans', [q['a'] for q in queries])]:
        tf = enc_tf(texts)
        sim = tf @ fvi.T
        vid_gt = np.array([vid2idx[q['vid']] for q in queries])
        r1_v = float((sim.argmax(1).cpu().numpy() == vid_gt).mean() * 100)
        simf = tf @ fv.T
        q_gt = vid_gt
        hit = (frames_vid[simf.argmax(1).cpu().numpy()] == q_gt)
        r1_f = float(hit.mean() * 100)
        res['openclip_tf'][vname] = {'n': len(texts), 'video_R1': round(r1_v, 3), 'frame_R1': round(r1_f, 3)}
        print('  openclip_tf %-8s n=%d videoR1=%.2f frameR1=%.2f' % (vname, len(texts), r1_v, r1_f), flush=True)
    json.dump(res, open(OUT, 'w', encoding='utf-8'), indent=1)
    print('DONE ->', OUT, flush=True)


if __name__ == '__main__':
    main()
