"""Portable numerical functions extracted from the recorded producer."""
import numpy as np
from scipy.stats import pearsonr, spearmanr
import statistics as st


def l2(x):
    n = np.linalg.norm(x, axis=1, keepdims=True)
    return x / np.maximum(n, 1e-12)

def gap_stats(img, txt):
    mu_i, mu_t = (img.mean(0), txt.mean(0))
    cg = float(np.linalg.norm(mu_i - mu_t))
    dg = float(np.sqrt(cg ** 2 + float(np.linalg.norm(img.std(0) - txt.std(0)) ** 2)))
    z = np.concatenate([img - img.mean(0), txt - txt.mean(0)], 0)
    cov = z.T @ z / max(1, len(z) - 1)
    w = np.clip(np.linalg.eigvalsh(cov), 1e-12, None)
    w = w / w.sum()
    return {'CG': cg, 'DG': dg, 'spec_eff_rank': float(np.exp(-(w * np.log(w)).sum())), 'spec_top1_share': float(w[-1])}

def classify(img, txt, labels):
    s = img @ txt.T
    return float((s.argmax(1) == labels).mean() * 100)

def retrieval_one_to_one(img, txt):
    s = img @ txt.T
    n = len(img)
    d = np.diag(s)
    rank_i2t = (s > d[:, None]).sum(1) + 1
    rank_t2i = (s > d[None, :]).sum(0) + 1
    r1_i2t = float((rank_i2t <= 1).mean() * 100)
    r1_t2i = float((rank_t2i <= 1).mean() * 100)
    rank5_i2t = float((rank_i2t <= 5).mean() * 100)
    rank5_t2i = float((rank_t2i <= 5).mean() * 100)
    return {'R1_i2t': r1_i2t, 'R1_t2i': r1_t2i, 'R5_i2t': rank5_i2t, 'R5_t2i': rank5_t2i}

def retrieval_class(img, txt, labels):
    s = img @ txt.T
    n, c = (len(img), len(txt))
    d = s[np.arange(n), labels]
    rank_i2t = (s > d[:, None]).sum(1) + 1
    r1_i2t = float((rank_i2t <= 1).mean() * 100)
    pred = s.argmax(0)
    r1_t2i = float((labels[pred] == np.arange(c)).mean() * 100)
    return {'R1_i2t': r1_i2t, 'R1_t2i': r1_t2i, 'R5_i2t': float((rank_i2t <= 5).mean() * 100)}

def mixed_retrieval(img, txt, labels, kind):
    if kind == 'caption':
        s_img = txt @ img.T
        s_txt = txt @ txt.T
        ok = 0
        for i in range(len(img)):
            scores = np.concatenate([s_img[i], s_txt[i]])
            scores[len(img) + i] = -np.inf
            top = int(scores.argmax())
            ok += int(top == i)
        return {'mixed_R1': 100.0 * ok / len(img)}
    c = len(txt)
    s_img = txt @ img.T
    s_txt = txt @ txt.T
    ok = 0
    for j in range(c):
        scores = np.concatenate([s_img[j], s_txt[j]])
        scores[len(img) + j] = -np.inf
        top = int(scores.argmax())
        if top < len(img) and labels[top] == j:
            ok += 1
    return {'mixed_R1': 100.0 * ok / c}

def transform(img, txt, mode, seed=0):
    img = l2(img.copy())
    txt = l2(txt.copy())
    if mode == 'original':
        return (img, txt)
    if mode == 'mean_center':
        return (l2(img - img.mean(0)), l2(txt - txt.mean(0)))
    if mode == 'gap_project':
        d = img.mean(0) - txt.mean(0)
        d = d / max(np.linalg.norm(d), 1e-12)
    elif mode == 'random_project':
        rng = np.random.RandomState(seed)
        d = rng.normal(size=img.shape[1])
        d /= np.linalg.norm(d)
    else:
        raise ValueError(mode)
    return (l2(img - np.outer(img @ d, d)), l2(txt - np.outer(txt @ d, d)))
