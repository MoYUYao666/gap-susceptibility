# Sync the key fixes in main_springer.tex into the older main.tex (to prevent misuse)
edits = [
    (r'across 58 LoRA configurations', r'across all tested LoRA configurations'),
    (r'$R^2 > 0.96$ across 58 LoRA configurations', r'mean $R^2 > 0.96$ across all tested LoRA configurations'),
    (r'sharply distinguishes PEFT from full fine-tuning ($\beta_{\text{full}}=0.643$, $4.7\times$ larger)',
     r'remains stable under full fine-tuning with matched training settings ($\beta_{\text{full}}=0.159$)'),
    (r'$\beta_{\text{full}}=0.643$, $4.7\times$ larger', r'$\beta_{\text{full}}=0.159$'),
    (r'Full fine-tuning    & $0.643 \pm 0.224$', r'Full fine-tuning    & $0.159 \pm 0.024$'),
    (r'$>0.86$ & $4.7\times$ PEFT', r'$>0.97$ & comparable'),
    (r'Full FT    & $-0.003$ & 0.643 & 0.864', r'Full FT    & $-0.040$ & 0.159 & 0.987'),
    (r'287 experiments', r'278 experiments'),
    (r'224 experiments', r'162 experiments'),
    (r'340 experiments', r'278 experiments'),
    (r'CV}=11\%', r'CV}=29\%'),
]
src = open('main.tex', encoding='utf-8').read()
n = 0
for old, new in edits:
    if old in src:
        src = src.replace(old, new); n += 1
open('main.tex', 'w', encoding='utf-8').write(src)
print('main.tex: synced %d places' % n)
