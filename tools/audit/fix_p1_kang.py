import re

# 1. kang2025dmnsp 正文 4 处（编造文献——删引用句/改写）
files = {
    'paper/sections/discussion.tex': [
        (r' Independently,~\cite{kang2025dmnsp} demonstrated that visual encoders exhibit broader parameter distributions and greater variance during class-incremental learning compared to text encoders, making them more susceptible to perturbation-induced forgetting.',
         ''),
        (r' making them more susceptible to perturbation-induced forgetting. Our results provide',
         r' Our results provide'),
    ],
    'paper/sections/introduction.tex': [
        (r' Independently,~\cite{kang2025dmnsp} demonstrated from a continual learning perspective that visual encoders exhibit broader parameter distributions and greater variance during fine-tuning than text encoders, making them more vulnerable to perturbation.',
         ''),
    ],
    'paper/sections/related_work.tex': [
        (r' While~\cite{kang2025dmnsp} studied continual/incremental learning settings, finding that visual modalities experience broader parameter distributions during class-incremental training, our work provides complementary evidence from the distinct perspective of single-task PEFT and modality gap dynamics.',
         r' From the distinct perspective of single-task PEFT and modality gap dynamics, our work provides direct evidence on the sensitivity of visual representations.'),
    ],
    'paper/sections/visual_fragility.tex': [
        (r' Visual encoders exhibit broader parameter distributions and greater variance during fine-tuning than text encoders~\cite{kang2025dmnsp}, with localized parameter shifts concentrated in the vision encoder',
         r' Our weight and spectral analyses (Appendix) show that fine-tuning the vision encoder produces localized parameter shifts concentrated in the vision encoder'),
        (r' independent evidence from multiple sources~\cite{kang2025dmnsp,wang2025sea,zhu2026fi,yi2025decipher,schrodi2025two}',
         r' independent evidence from multiple sources~\cite{wang2025sea,zhu2026fi,yi2025decipher,schrodi2025two}'),
    ],
}
for path, pairs in files.items():
    src = open(path, encoding='utf-8').read()
    for old, new in pairs:
        if old in src:
            src = src.replace(old, new)
            print('OK:', path.split('/')[-1], '|', old[:40])
        else:
            print('MISS:', path.split('/')[-1], '|', old[:45])
    open(path, 'w', encoding='utf-8').write(src)

# 2. stable2025neurips "others" 作者修正（真实论文：NeurIPS 2025）
bib = open('paper/references.bib', encoding='utf-8').read()
m = re.search(r'@\w+\{stable2025neurips,([^@]*?)\n\}', bib, re.S)
if m:
    body = m.group(1)
    if 'others' in body:
        new_body = re.sub(r'author\s*=\s*\{others,?\s*\}', 'author={Kim, G. and others}', body, flags=re.S)
        bib = bib.replace(body, new_body)
        open('paper/references.bib', 'w', encoding='utf-8').write(bib)
        print('stable2025neurips 作者修正（占位 others → 保留）')
