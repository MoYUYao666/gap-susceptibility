# Paper 3 fixes — findings from the three-model audit (2026-08-12)
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

base = 'paper3/paper_ieee/'

# ============ experiments.tex ============
patch(base + 'sections/experiments.tex', [
    # phase caption: make the source attribution accurate
    (r'population std over 3 seeds (LLaVA $r{=}4,16,32,64$; $r{=}5,6,7,8$ from the dense sweep; Qwen-VL: 45/45 runs valid, 0 NaN).',
     r'population std over 3 seeds (LLaVA values from the E2 and supplementary sweep batches; Qwen-VL: 45/45 runs valid, 0 NaN).'),
    # make the 6/6 claim reference accurate ("3-seed sweep" → "phase table")
    (r'$\Delta E(r{=}5)$ holds in all six independent configurations (3-seed',
     r'$\Delta E(r{=}5)$ holds in all six independent configurations (phase table,'),
    # correct the NaN rank annotation
    (r'mean is $+491$, driven by runs exceeding $+1000$; two of fifteen runs produce NaN collapse at $r=64$---a failure mode',
     r'mean is $+491$, driven by runs exceeding $+1000$; two of fifteen runs produce NaN collapse (one at $r{=}32$, one at $r{=}64$)---a failure mode'),
    # cross-reference: IV-C → IV-B (statistical tests are in the Phase Transition section)
    (r'(6/6 configurations in total, including the multi-seed sweep and'
     r'\nShareGPT; two-sided binomial $p = 0.031$, see the statistical test in'
     r'\nSection~IV-C).',
     r'(6/6 configurations in total, including the phase table and'
     r'\nShareGPT; two-sided binomial $p = 0.031$, see the statistical test in'
     r'\nSection~IV-B).'),
    # cross-reference: Appendix~A → Appendix~D (the Γ table)
    (r'(Appendix~A) confirm this directly: all $|\Gamma_k|$ grow monotonically',
     r'(Appendix~D) confirm this directly: all $|\Gamma_k|$ grow monotonically'),
])

# ============ theory.tex ============
patch(base + 'sections/theory.tex', [
    # cross-reference: Section~VI → V
    (r'Corollary~4 and Section~VI.',
     r'Corollary~4 and Section~V.'),
    # Appendix~A → D (raw magnitudes in the scale invariance paragraph)
    (r'recovered with temperature $\beta/s$. The raw magnitudes in Appendix~A',
     r'recovered with temperature $\beta/s$. The raw magnitudes in Appendix~D'),
    # Section~IV-F → IV-E (counterfactual)
    (r'counterfactual experiments (Section~IV-F).',
     r'counterfactual experiments (Section~IV-E).'),
])

# ============ references.bib ============
bib = open(base + 'references.bib', encoding='utf-8').read()
# double-blind: real-name self-citation → Anonymous
bib = bib.replace('  author={Wan, Hongrui},', '  author={Anonymous},')
print('bib self-citation anonymization: 2 places' if bib.count('author={Anonymous},') == 2 else 'bib self-citation anonymization: %d places' % bib.count('author={Anonymous},'))
# remove orphan fields (two blocks with no @entry header)
bib = bib.replace('''  journal={arXiv:2404.02948},
  year={2024}
}

''', '')
bib = bib.replace('''  journal={ICML},
  year={2024}
}

@article{wu2025language,''', '@article{wu2025language,')
open(base + 'references.bib', 'w', encoding='utf-8').write(bib)

print('\nPaper 3 fix pass complete')
