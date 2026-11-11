# -*- coding: utf-8 -*-
"""A4: readout and intervention benchmark over the frozen features.

For every (encoder, dataset) feature set compute classification, image-to-text retrieval, text-to-image retrieval,
mixed-modal retrieval, joint clustering ARI (class datasets) and gap statistics, under four conditions:
original, mean-centred, gap-direction-projected, random-direction-projected.
"""
from __future__ import annotations
import glob, io, json, os
import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FEAT = os.path.join(REPO, "outputs", "a4", "features")
CATALOG = os.path.join(REPO, "outputs", "a4", "a4_dataset_catalog.json")
OUT = os.path.join(REPO, "outputs", "a4", "a4_readouts_2026-11-09.json")


def l2(x):
    n = np.linalg.norm(x, axis=1, keepdims=True)
    return x / np.maximum(n, 1e-12)


def gap_stats(img, txt):
    mu_i, mu_t = img.mean(0), txt.mean(0)
    cg = float(np.linalg.norm(mu_i - mu_t))
    dg = float(np.sqrt(cg ** 2 + float(np.linalg.norm(img.std(0) - txt.std(0)) ** 2)))
    # spectral effective rank of the concatenated representation
    z = np.concatenate([img - img.mean(0), txt - txt.mean(0)], 0)
    cov = (z.T @ z) / max(1, len(z) - 1)
    w = np.clip(np.linalg.eigvalsh(cov), 1e-12, None); w = w / w.sum()
    return {"CG": cg, "DG": dg,
            "spec_eff_rank": float(np.exp(-(w * np.log(w)).sum())),
            "spec_top1_share": float(w[-1])}


def classify(img, txt, labels):
    s = img @ txt.T
    return float((s.argmax(1) == labels).mean() * 100)


def retrieval_one_to_one(img, txt):
    s = img @ txt.T
    n = len(img)
    d = np.diag(s)
    rank_i2t = (s > d[:, None]).sum(1) + 1
    rank_t2i = (s.T > d[None, :]).sum(0) + 1
    r1_i2t = float((rank_i2t <= 1).mean() * 100)
    r1_t2i = float((rank_t2i <= 1).mean() * 100)
    rank5_i2t = float((rank_i2t <= 5).mean() * 100)
    rank5_t2i = float((rank_t2i <= 5).mean() * 100)
    return {"R1_i2t": r1_i2t, "R1_t2i": r1_t2i, "R5_i2t": rank5_i2t, "R5_t2i": rank5_t2i}


def retrieval_class(img, txt, labels):
    s = img @ txt.T
    n, c = len(img), len(txt)
    d = s[np.arange(n), labels]
    rank_i2t = (s > d[:, None]).sum(1) + 1
    r1_i2t = float((rank_i2t <= 1).mean() * 100)
    pred = s.argmax(0)
    r1_t2i = float((labels[pred] == np.arange(c)).mean() * 100)
    return {"R1_i2t": r1_i2t, "R1_t2i": r1_t2i,
            "R5_i2t": float((rank_i2t <= 5).mean() * 100)}


def mixed_retrieval(img, txt, labels, kind):
    if kind == "caption":
        # query text i, candidates = images + all texts except the query itself; correct = image i
        s_img = txt @ img.T   # N x N
        s_txt = txt @ txt.T
        ok = 0
        for i in range(len(img)):
            scores = np.concatenate([s_img[i], s_txt[i]])
            scores[len(img) + i] = -np.inf  # do not allow the query text to retrieve itself
            top = int(scores.argmax())
            ok += int(top == i)
        return {"mixed_R1": 100.0 * ok / len(img)}
    # class dataset: class text c, candidates = images + class texts except the query text; correct = any image of class c
    c = len(txt)
    s_img = txt @ img.T   # C x N
    s_txt = txt @ txt.T
    ok = 0
    for j in range(c):
        scores = np.concatenate([s_img[j], s_txt[j]])
        scores[len(img) + j] = -np.inf  # exclude the query text itself
        top = int(scores.argmax())
        if top < len(img) and labels[top] == j:
            ok += 1
    return {"mixed_R1": 100.0 * ok / c}


def ari_cluster(img, txt, labels):
    try:
        from sklearn.cluster import KMeans
        from sklearn.metrics import adjusted_rand_score
        n = len(img)
        k = int(len(set(labels.tolist())))
        pool = np.concatenate([img, txt], 0)
        pool_labels = np.concatenate([labels, np.arange(len(txt))], 0)
        pred = KMeans(n_clusters=k, n_init=5, random_state=0).fit_predict(pool)
        return {"ARI": float(adjusted_rand_score(pool_labels, pred))}
    except Exception as e:
        return {"ARI": None, "ARI_error": str(e)[:80]}


def transform(img, txt, mode, seed=0):
    img = l2(img.copy()); txt = l2(txt.copy())
    if mode == "original":
        return img, txt
    if mode == "mean_center":
        return l2(img - img.mean(0)), l2(txt - txt.mean(0))
    if mode == "gap_project":
        d = img.mean(0) - txt.mean(0); d = d / max(np.linalg.norm(d), 1e-12)
    elif mode == "random_project":
        rng = np.random.RandomState(seed); d = rng.normal(size=img.shape[1]); d /= np.linalg.norm(d)
    else:
        raise ValueError(mode)
    return l2(img - np.outer(img @ d, d)), l2(txt - np.outer(txt @ d, d))


def main():
    cat = json.load(io.open(CATALOG, encoding="utf-8"))
    out = {}
    for f in sorted(glob.glob(os.path.join(FEAT, "*.npz"))):
        enc, ds = os.path.basename(f)[:-4].split("__", 1)
        meta = cat.get(ds, {})
        kind = meta.get("kind", "class")
        z = np.load(f, allow_pickle=True)
        img, txt, labels = z["img"].astype(np.float64), z["txt"].astype(np.float64), z["labels"]
        row = {"kind": kind, "n_images": len(img), "n_texts": len(txt)}
        for mode in ("original", "mean_center", "gap_project", "random_project"):
            a, b = transform(img, txt, mode)
            m = {"gap": gap_stats(a, b)}
            if kind == "class":
                m["classification_top1"] = classify(a, b, labels)
                m.update(retrieval_class(a, b, labels))
                m.update(mixed_retrieval(a, b, labels, kind))
                m.update(ari_cluster(a, b, labels))
            else:
                m.update(retrieval_one_to_one(a, b))
                m.update(mixed_retrieval(a, b, labels, kind))
            row[mode] = m
        out["%s__%s" % (enc, ds)] = row
        print(enc, ds, kind, len(img), flush=True)
    json.dump(out, io.open(OUT, "w", encoding="utf-8"), indent=1)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
