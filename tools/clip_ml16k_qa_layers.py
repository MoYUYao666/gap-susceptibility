"""A2 extension E5: MarineLife QA stratified retrieval -- videoR1 stratified by QA type (central_object / appearance / environment, etc.).
Models: bioclip / oceanclip (open_clip). Output: outputs/ml16k_qa_layers.json
Run: conda run -n pytorch python tools/clip_ml16k_qa_layers.py
"""
import os, sys, json, glob, collections
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

OUT = 'outputs/ml16k_qa_layers.json'
ROOT = 'data/marinelife16k/data/selected_frames'


def load_qa(root):
    qs = []
    for qf in sorted(glob.glob(os.path.join(root, '*', '*', 'qa.jsonl'))):
        vdir = os.path.dirname(qf)
        vid = os.path.basename(os.path.dirname(vdir)) + '/' + os.path.basename(vdir)
        with open(qf, encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    qa = json.loads(line)
                except Exception:
                    continue
                q = qa.get('question', '')
                a = qa.get('answer_text', '')
                if q and a:
                    qs.append({'vid': vid, 'q': q, 'a': a, 'type': qa.get('type', 'other')})
    return qs


def main():
    qs = load_qa(ROOT)
    frames = []
    for fp in sorted(glob.glob(os.path.join(ROOT, '*', '*', '*.jpg'))):
        frames.append((fp, os.path.basename(os.path.dirname(os.path.dirname(fp))) + '/' +
                       os.path.basename(os.path.dirname(fp))))
    vids = sorted(set(v for _, v in frames))
    res = {'meta': {'n_queries': len(qs), 'n_frames': len(frames), 'n_videos': len(vids),
                    'types': collections.Counter(q['type'] for q in qs)}}
    for tag in ['bioclip', 'oceanclip']:
        m, pre = ocm.load_openclip(tag)
        tok = open_clip.get_tokenizer('ViT-B-16')
        with torch.no_grad():
            fv = []
            ims = [Image.open(fp).convert('RGB') for fp, _ in frames]
            for i in range(0, len(ims), 32):
                xs = torch.stack([pre(im) for im in ims[i:i + 32]]).to('cuda')
                fv.append(F.normalize(m.encode_image(xs), dim=-1))
            fv = torch.cat(fv)
        vid2idx = {v: i for i, v in enumerate(vids)}
        fvi = F.normalize(torch.stack([fv[[i for i, (_, vv) in enumerate(frames) if vv == v]].mean(0)
                                       for v in vids]), dim=-1)
        res[tag] = {}
        for lay in sorted(set(q['type'] for q in qs)):
            sub = [q for q in qs if q['type'] == lay]
            if len(sub) < 20:
                continue
            texts = [q['q'] + ' ' + q['a'] for q in sub]
            with torch.no_grad():
                tf = F.normalize(m.encode_text(tok(texts).to('cuda')), dim=-1)
            sim = tf @ fvi.T
            gt = np.array([vid2idx[q['vid']] for q in sub])
            r1 = float((sim.argmax(1).cpu().numpy() == gt).mean() * 100)
            r5 = float(np.mean([gt[i] in sim[i].topk(5).indices.cpu().numpy() for i in range(len(gt))]) * 100)
            res[tag][lay] = {'n': len(sub), 'videoR1': round(r1, 3), 'videoR5': round(r5, 3)}
            print('%s %-28s n=%d R1=%.2f R5=%.2f' % (tag, lay, len(sub), r1, r5), flush=True)
        del m
        torch.cuda.empty_cache()
    json.dump(res, open(OUT, 'w', encoding='utf-8'), indent=1)
    print('DONE ->', OUT, flush=True)


if __name__ == '__main__':
    main()
