"""Portable numerical functions extracted from the recorded producer."""
import numpy as np
from scipy.stats import pearsonr, spearmanr


def stable_retrieval(img, txt):
    scores = np.einsum('ik,jk->ij', img, txt, optimize=False)
    diagonal = np.diag(scores)
    ranks = {'i2t': (scores > diagonal[:, None]).sum(1) + 1, 't2i': (scores > diagonal[None, :]).sum(0) + 1}
    return {f'R{k}_{direction}': float(100 * np.mean(rank <= k)) for direction, rank in ranks.items() for k in (1, 5)}
