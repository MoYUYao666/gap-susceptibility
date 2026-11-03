"""补强 ⑨: iNaturalist 野生照片来源复验（跨来源稳健性）。
用 ocean_subset_fauna.json 的海洋学名, 经 iNat API 检索 taxon id → 拉观察照片（野生, 真实名标签,
CC 许可公开数据）→ 按我们的协议（d̂=类文本质心差, λ 手术, margins 分析）在 iNat 子集上复验。
输出: data/inat_wild/{species}/*.jpg + outputs/ocean_inat_wild.json
"""
import os, sys, json, time
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import torch
import torch.nn.functional as F
import requests
from PIL import Image
from scipy import stats
import open_clip

TEMPLATE = 'a photo of a {}'
API = 'https://api.inaturalist.org/v1'
TOP_N = 50
PER_SPECIES = 15        # 每物种最多取图
MIN_PER_CLASS = 8
MAX_PER_CLASS = 12
IMG_DIR = 'data/inat_wild'
OUT = 'outputs/ocean_inat_wild.json'


def get(url, params=None, tries=2):
    for _ in range(tries):
        try:
            r = requests.get(url, params=params, timeout=40)
            if r.status_code == 200:
                return r.json()
            print('  HTTP', r.status_code, url[:80], flush=True)
        except Exception as e:
            print('  net err', str(e)[:100], flush=True)
        time.sleep(2)
    return None


def find_taxon(name):
    d = get(API + '/taxa', {'q': name, 'rank': 'species', 'per_page': 5})
    if not d:
        return None
    for t in d.get('results', []):
        if (t.get('name') or '').lower() == name.lower():
            return t.get('id')
    return None


def fetch_photos(taxon_id, want=PER_SPECIES):
    urls = []
    d = get(API + '/observations', {'taxon_id': taxon_id, 'per_page': want, 'order_by': 'id',
                                    'sort_order': 'asc', 'photo': True, 'quality_grade': 'research'})
    if not d:
        return urls
    for o in d.get('results', []):
        for ph in (o.get('photos') or [])[:1]:
            u = ph.get('url')
            if u:
                if '/square.jpg' in u:
                    u = u.replace('/square.jpg', '/medium.jpg')
                elif '/small.jpg' in u:
                    u = u.replace('/small.jpg', '/medium.jpg')
                urls.append(u)
        if len(urls) >= want:
            break
    return urls


def load_subset_info():
    sub = json.load(open('outputs/ocean_subset_fauna.json', encoding='utf-8'))
    counts = sub['class_counts']
    classes = sorted(counts, key=lambda c: (-counts[c], c))[:TOP_N]
    return classes


def download(species, urls):
    d = os.path.join(IMG_DIR, species.replace(' ', '_'))
    os.makedirs(d, exist_ok=True)
    got = 0
    for i, u in enumerate(urls):
        fp = os.path.join(d, '%02d.jpg' % i)
        if os.path.exists(fp):
            got += 1
            continue
        try:
            r = requests.get(u, timeout=30)
            if r.status_code == 200 and len(r.content) > 5000:
                open(fp, 'wb').write(r.content)
                got += 1
        except Exception:
            pass
        time.sleep(0.3)
    return got


def encode_imgs(m, pre, imgs, batch=32):
    feats = []
    with torch.no_grad():
        for i in range(0, len(imgs), batch):
            xs = torch.stack([pre(im) for im in imgs[i:i + batch]]).to('cuda')
            feats.append(F.normalize(m.encode_image(xs), dim=-1))
    return torch.cat(feats)


def analyze(tf, base, labels, m_c, gnorm, dH):
    import importlib.util
    spec = importlib.util.spec_from_file_location('ocm', 'tools/clip_ocean_margins.py')
    ocm = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ocm)
    return ocm.analyze(tf, base, labels, m_c, gnorm, dH)


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else 'all'
    classes = load_subset_info()
    print('目标物种(按图数 top%d): %d 模式=%s' % (TOP_N, len(classes), mode), flush=True)
    per_sp = {}
    if mode in ('all', 'collect'):
        tok_save = {}
        for c in classes:
            tid = find_taxon(c)
            if tid is None:
                print('  %-40s 未找到 taxon' % c, flush=True)
                continue
            urls = fetch_photos(tid)
            got = download(c, urls)
            per_sp[c] = got
            print('  %-40s taxon=%s photos=%d/%d' % (c, tid, got, len(urls)), flush=True)
        json.dump(per_sp, open(os.path.join(IMG_DIR, 'per_species.json'), 'w', encoding='utf-8'), indent=1)
    else:
        per_sp = json.load(open(os.path.join(IMG_DIR, 'per_species.json'), encoding='utf-8'))
    # 构建子集（≥8 图）
    keep = {c: sorted(f for f in os.listdir(os.path.join(IMG_DIR, c.replace(' ', '_')))
                      if f.endswith('.jpg'))[:MAX_PER_CLASS]
            for c, g in per_sp.items() if g >= MIN_PER_CLASS}
    if not keep:
        print('NONE with >=8 images; relax and retry?', flush=True)
        return
    classes2 = sorted(keep)
    imgs, labels = [], []
    for ci, c in enumerate(classes2):
        d = os.path.join(IMG_DIR, c.replace(' ', '_'))
        for f in keep[c]:
            imgs.append(Image.open(os.path.join(d, f)).convert('RGB'))
            labels.append(ci)
    labels = np.array(labels)
    print('子集: %d 类 / %d 图' % (len(classes2), len(imgs)), flush=True)
    res = {'n_species': len(classes2), 'n_images': len(imgs), 'per_species': per_sp}
    tok = open_clip.get_tokenizer('ViT-B-16')
    for tag in ['bioclip', 'oceanclip']:
        m, pre = ocm_load(tag)
        texts = [TEMPLATE.format(c) for c in classes2]
        with torch.no_grad():
            tf = F.normalize(m.encode_text(tok(texts).to('cuda')), dim=-1)
        base = encode_imgs(m, pre, imgs)
        gap = tf.mean(0) - base.mean(0)
        gnorm = gap.norm().item()
        dH = gap / gnorm
        m_c = (dH @ tf.T).cpu().numpy()
        r = analyze(tf, base, labels, m_c, gnorm, dH)
        res[tag] = {'gap_norm': r['gap_norm'], 'sigma_m': r['sigma_m'], 'mean_m': r['mean_m'],
                    'tau_pred_1': r['predicted_tau_exact']['1.0'], 'tau_meas_1': r['measured']['1.0']['tau'],
                    'top1_0': r['measured']['0.0']['top1'], 'top1_1': r['measured']['1.0']['top1']}
        print('%s: gap=%.4f sigma_m=%.4f tau_pred=%.4f tau_meas=%.4f top1 %.2f→%.2f' %
              (tag, gnorm, res[tag]['sigma_m'], res[tag]['tau_pred_1'], res[tag]['tau_meas_1'],
               res[tag]['top1_0'], res[tag]['top1_1']), flush=True)
        json.dump(res, open(OUT, 'w', encoding='utf-8'), indent=1)
        del m
        torch.cuda.empty_cache()
    print('DONE ->', OUT, flush=True)


def ocm_load(tag):
    import importlib.util
    spec = importlib.util.spec_from_file_location('ocm', 'tools/clip_ocean_margins.py')
    ocm = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ocm)
    return ocm.load_openclip(tag)


if __name__ == '__main__':
    main()
