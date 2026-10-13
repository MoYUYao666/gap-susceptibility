# Paper 1 fixes — findings of the three-model audit (2026-08-12)
import re

def patch(path, pairs):
    src = open(path, encoding='utf-8').read()
    for old, new in pairs:
        if old in src:
            src = src.replace(old, new)
            print('OK  ', path.split('/')[-1], '|', old[:50])
        else:
            print('MISS', path.split('/')[-1], '|', old[:50])
    open(path, 'w', encoding='utf-8').write(src)

base = 'paper/'

# ============ experiments.tex ============
patch(base + 'sections/experiments.tex', [
    # ANOVA mislabeling recomputed (conclusion reversed) + Welch updated
    (r"Welch's $t$-test comparing all PEFT methods against full fine-tuning yields $t = -25.33$, $p = 9.8 \times 10^{-34}$, confirming extreme statistical significance. One-way ANOVA across PEFT methods: $F = 2.17$, $p = 0.146$ (not significant), suggesting that the choice among PEFT methods matters less than the choice of \textit{where} to apply them.",
     r"Welch's $t$-test comparing all PEFT methods against full fine-tuning yields $t = -22.96$, $p = 3.5 \times 10^{-31}$, confirming extreme statistical significance. One-way ANOVA across PEFT methods (LoRA vs.\ Adapter, using the correctly matched Adapter group): $F = 13.37$, $p = 5 \times 10^{-4}$, indicating that the PEFT method choice also matters: Adapter attains substantially larger gap reduction on average (mean CG$\Delta = -0.100$ vs.\ $-0.004$ for LoRA), at the cost of lower retrieval accuracy."),
    # Table 4 Adapter row (correct values)
    (r'Adapter & $-$0.047 & 0.623 & $d$=64, text-only \\',
     r'Adapter & $-$0.100 & 0.173 & $d$=64, text-only \\'),
    # Table 1: BLIP R@1
    (r'BLIP-1 & 7 & \textbf{$-$0.476} & 0.171 \\',
     r'BLIP-1 & 7 & \textbf{$-$0.476} & 0.175 \\'),
    # Table 1: SigLIP R@1
    (r'SigLIP & 5 & $+$0.058 & 0.485 \\',
     r'SigLIP & 5 & $+$0.058 & 0.479 \\'),
])

# ============ discussion.tex ============
patch(base + 'sections/discussion.tex', [
    # sole exception → one of a few (consistent with the introduction)
    (r'across LoRA, Adapter, BLIP-1, and ViT-L, with COCO as the sole marginal exception (Table~\ref{tab:cross_val})',
     r'across LoRA, Adapter, BLIP-1, and ViT-L, with a few marginal exceptions (COCO both-position, SigLIP both-position, and Adapter vision-only; Table~\ref{tab:cross_val})'),
])

# ============ main_nn.tex ============
patch(base + 'main_nn.tex', [
    # abstract text-only claim qualified (SigLIP is a counterexample)
    (r'We find that text-only fine-tuning overwhelmingly preserves cross-modal alignment better than joint modality fine-tuning across LoRA, Adapter, BLIP-1, and SigLIP configurations.',
     r'We find that text-only fine-tuning preserves cross-modal alignment better than joint modality fine-tuning across LoRA, Adapter, BLIP-1, and ViT-L configurations (with a few marginal exceptions, e.g., SigLIP both-position).'),
])

# ============ supplementary.tex: siglip frozen ============
src = open(base + 'sections/supplementary.tex', encoding='utf-8').read()
if 'siglip\\_frozen & --- & --- & 0.000 & 0.000' in src:
    src = src.replace('siglip\\_frozen & --- & --- & 0.000 & 0.000', 'siglip\\_frozen & --- & --- & 0.000 & 0.075')
    open(base + 'sections/supplementary.tex', 'w', encoding='utf-8').write(src)
    print('OK  supplementary.tex | siglip_frozen R@1')
else:
    print('MISS supplementary.tex | siglip_frozen R@1')

# ============ bib: duplicate IMoD DOI ============
bib = open(base + 'references.bib', encoding='utf-8').read()
if '10.48550/arXiv.2508.00230' in bib:
    # remove the DOI of IMoD (that DOI belongs to KRAdapter)
    m = re.search(r'@\w+\{zhang2026imod,([^@]*?)\n\}', bib, re.S)
    if m:
        body = m.group(1)
        new_body = re.sub(r'\n\s*doi\s*=\s*\{[^}]*\}', '', body)
        bib = bib.replace(body, new_body)
        open(base + 'references.bib', 'w', encoding='utf-8').write(bib)
        print('OK  references.bib | IMoD DOI removed')
else:
    print('MISS references.bib | IMoD DOI')

# ============ orphan abstract.tex update ============
abstract_new = '''\\documentclass[11pt]{article}
\\usepackage[margin=1in]{geometry}
\\usepackage{times}
\\begin{document}

\\textbf{NOTE: This file is superseded by the inline abstract in main\_nn.tex. Retained for reference only.}

\\end{document}
'''
open(base + 'abstract.tex', 'w', encoding='utf-8').write(abstract_new)
print('OK  abstract.tex | orphan file marked obsolete')

print('\nPaper 1 fixes finished')
