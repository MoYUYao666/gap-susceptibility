# Paper 3 bib 修复 — others 作者/查无条目（2026-08-12）
import re

base = 'paper3/paper_ieee/'
bib = open(base + 'references.bib', encoding='utf-8').read()

# 1. shaplora2025: 真实作者 Zhao/Yao/Song/Zhu，CPAL 2026
bib = bib.replace(
    '@article{shaplora2025,\n  title={ShapLoRA: Allocation of Low-rank Adaption on Large Language Models via Shapley Value Inspired Importance Estimation},\n  author={others},\n  journal={arXiv:2601.17921},\n  year={2025}\n}',
    '@inproceedings{shaplora2025,\n  title={ShapLoRA: Allocation of Low-rank Adaption on Large Language Models via Shapley Value Inspired Importance Estimation},\n  author={Zhao, Yi and Yao, Qinghua and Song, Xinyuan and Zhu, Wei},\n  booktitle={CPAL},\n  year={2026}\n}')

# 2. f3ocus2025: 真实作者 Saha et al. CVPR 2025
bib = bib.replace(
    '@article{f3ocus2025,\n  title={F$^3$OCUS: Federated Finetuning of Vision-Language Models with Optimal Client Layer Selection},\n  author={others},\n  journal={CVPR},\n  year={2025}\n}',
    '@inproceedings{f3ocus2025,\n  title={F$^3$OCUS: Federated Finetuning of Vision-Language Foundation Models with Optimal Client Layer Updating Strategy},\n  author={Saha, Pramit and Wagner, Felix and Mishra, Divyanshu and Peng, Can and Thakur, Anshul and Clifton, David A. and Kamnitsas, Konstantinos and Noble, J. Alison},\n  booktitle={CVPR},\n  year={2025}\n}')

# 3. loraconvex2025: 标题错误修正 + 真实作者（Kim/Kim/Ryu, ICML 2025）
bib = bib.replace(
    '@article{loraconvex2025,\n  title={LoRA Training: Convergence to Global Minima vs Spurious Local Minima},\n  author={others},\n  journal={arXiv:2502.09376},\n  year={2025}\n}',
    '@inproceedings{loraconvex2025,\n  title={LoRA Training Provably Converges to a Low-Rank Global Minimum or It Fails Loudly (But it Probably Won\'t Fail)},\n  author={Kim, Junsu and Kim, Jaeyeon and Ryu, Ernest K.},\n  booktitle={ICML},\n  year={2025}\n}')

# 4. stable2025neurips: 作者查不到 → 删条目
bib = re.sub(r'@inproceedings\{stable2025neurips,[^@]*?\n\}\n\n', '', bib, flags=re.S)

# 5. bayesianadalora2025: 查无此文 → 删条目
bib = re.sub(r'@article\{bayesianadalora2025,[^@]*?\n\}\n\n', '', bib, flags=re.S)

open(base + 'references.bib', 'w', encoding='utf-8').write(bib)
keys = set(re.findall(r'@\w+\{([^,]+),', bib))
print('bib 条目:', len(keys))
print('删除: stable2025neurips =', 'stable2025neurips' not in keys, '| bayesianadalora2025 =', 'bayesianadalora2025' not in keys)
print('others 残留:', bib.count('author={others}'))
