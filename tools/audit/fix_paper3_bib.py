# Paper 3 bib fixes — "others" authors / entries not found (2026-08-12)
import re

base = 'paper3/paper_ieee/'
bib = open(base + 'references.bib', encoding='utf-8').read()

# 1. shaplora2025: real authors Zhao/Yao/Song/Zhu, CPAL 2026
bib = bib.replace(
    '@article{shaplora2025,\n  title={ShapLoRA: Allocation of Low-rank Adaption on Large Language Models via Shapley Value Inspired Importance Estimation},\n  author={others},\n  journal={arXiv:2601.17921},\n  year={2025}\n}',
    '@inproceedings{shaplora2025,\n  title={ShapLoRA: Allocation of Low-rank Adaption on Large Language Models via Shapley Value Inspired Importance Estimation},\n  author={Zhao, Yi and Yao, Qinghua and Song, Xinyuan and Zhu, Wei},\n  booktitle={CPAL},\n  year={2026}\n}')

# 2. f3ocus2025: real authors Saha et al. CVPR 2025
bib = bib.replace(
    '@article{f3ocus2025,\n  title={F$^3$OCUS: Federated Finetuning of Vision-Language Models with Optimal Client Layer Selection},\n  author={others},\n  journal={CVPR},\n  year={2025}\n}',
    '@inproceedings{f3ocus2025,\n  title={F$^3$OCUS: Federated Finetuning of Vision-Language Foundation Models with Optimal Client Layer Updating Strategy},\n  author={Saha, Pramit and Wagner, Felix and Mishra, Divyanshu and Peng, Can and Thakur, Anshul and Clifton, David A. and Kamnitsas, Konstantinos and Noble, J. Alison},\n  booktitle={CVPR},\n  year={2025}\n}')

# 3. loraconvex2025: title corrected + real authors (Kim/Kim/Ryu, ICML 2025)
bib = bib.replace(
    '@article{loraconvex2025,\n  title={LoRA Training: Convergence to Global Minima vs Spurious Local Minima},\n  author={others},\n  journal={arXiv:2502.09376},\n  year={2025}\n}',
    '@inproceedings{loraconvex2025,\n  title={LoRA Training Provably Converges to a Low-Rank Global Minimum or It Fails Loudly (But it Probably Won\'t Fail)},\n  author={Kim, Junsu and Kim, Jaeyeon and Ryu, Ernest K.},\n  booktitle={ICML},\n  year={2025}\n}')

# 4. stable2025neurips: authors untraceable → delete entry
bib = re.sub(r'@inproceedings\{stable2025neurips,[^@]*?\n\}\n\n', '', bib, flags=re.S)

# 5. bayesianadalora2025: paper not found → delete entry
bib = re.sub(r'@article\{bayesianadalora2025,[^@]*?\n\}\n\n', '', bib, flags=re.S)

open(base + 'references.bib', 'w', encoding='utf-8').write(bib)
keys = set(re.findall(r'@\w+\{([^,]+),', bib))
print('bib entries:', len(keys))
print('deleted: stable2025neurips =', 'stable2025neurips' not in keys, '| bayesianadalora2025 =', 'bayesianadalora2025' not in keys)
print('others left:', bib.count('author={others}'))
