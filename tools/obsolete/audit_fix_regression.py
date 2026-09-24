"""回归验证: 第九轮全部修复项是否已在当前(冻结)文本中生效。"""
import glob
import re

tex = {}
for f in glob.glob('paper_ap3/sections/*.tex') + ['paper_ap3/main.tex', 'paper_ap3/refs.bib']:
    tex[f] = open(f, encoding='utf-8').read()
allt = '\n'.join(tex.values())


def chk(name, cond, detail=''):
    print(('  OK   ' if cond else '  FAIL ') + name + (' | ' + detail if detail else ''))


print('=== 引用类 ===')
chk('cheng2026maab 不再被引用', 'cheng2026maab}' not in allt and 'cheng2026maab,' not in allt)
chk('cheng2026maab 条目已禁用', '@article{cheng2026maab' not in allt)
chk('morelli arXiv=2605.15961', 'arXiv:2605.15961' in tex['paper_ap3/refs.bib'])
chk('xu arXiv=2604.16256', 'arXiv:2604.16256' in tex['paper_ap3/refs.bib'])
chk('gao 无错误 DOI (2501.00984)', '2501.00984' not in allt)
chk('chen2025vlmft 作者已修正', 'Danish, Sufyan' in tex['paper_ap3/refs.bib'])
chk('wang2026ftp 作者已修正', 'Lu, Y. and Salah' in tex['paper_ap3/refs.bib'])
chk('wan2026 占位条目已移除', 'wan2026gap' not in allt and 'wan2026protect' not in allt)
chk('igulora year=2026', re.search(r'igulora2025.*?year=\{2026\}', tex['paper_ap3/refs.bib'], re.S) is not None)
chk('hu2025loralimits 含 Fine-Tuning', 'Fine-Tuning for Transformer-Based' in allt)
chk('yi2025 标题修正', 'of Contrastive Vision-Language Models' in allt)
chk('sharegpt 含 url', 'huggingface.co/datasets/anon8231489123' in allt)
chk('zhu2025connector → IJCAI', 'ijcai.2025/1202' in allt)
chk('li2023blip2 已添加并被引用', 'li2023blip2' in tex['paper_ap3/refs.bib'] and '\\cite{li2023blip2}' in allt)
chk('BLIP-1 已全部改为 BLIP-2', 'BLIP-1' not in allt)
chk('"independent empirical work" 已移除', 'independent empirical work' not in allt)

print('=== 数据类 ===')
chk('秩线性 R²=0.953/slope 173.3', '0.953' in allt and '173.3' in allt)
chk('旧秩线性值已清 (0.961/175.4/0.991)', '0.961' not in allt and '175.4' not in allt and '0.991' not in allt.split('0.991') and '0.991' not in allt)
chk('generalization Flickr 0.984±0.005', '0.984 \\pm 0.005' in allt)
chk('generalization COCO β=0.171', '0.171' in allt)
chk('聚类 bootstrap 复算值', '-0.847' in allt and '98 experiments' in allt)
chk('旧聚类值已清 (-0.819/79 clusters)', '-0.819' not in allt and '79 clusters' not in allt)
chk('零样本 -53.3% 已清', '53.3' not in allt)
chk('56.7 pp 已写入', '56.7' in allt)
chk('+0.079 已清', '0.079' not in allt)
chk('full-FT ±0.007', '0.191 \\pm 0.007' in allt)
chk('0.9 percentage points', '0.9' in allt and 'within $0.9$ percentage' in allt)
chk('Qwen ±117', '+83 \\pm 117' in allt)
chk('Qwen p=6.4e-6', '6.4\\times10^{-6}' in allt)
chk('预算 128 起', 'budget $128$--$152$' in allt)
chk('8-point β grid', '8-point' in allt and '9-point' not in allt)
chk('k=0.088 已清', '0.088' not in allt)
chk('池化范围 +0.60', '+0.60' in allt)
chk('bootstrap 措辞 (vision block strongest)', 'vision block as the strongest coupling' in allt)
chk('跨批 |Γ| 口径', 'ordering basis $|\\Gamma_k|$' in allt)
chk('E0 范围 3931', '3864$--$3931' in allt)
chk('成本统一 $8', '7.5' not in allt)

print('=== 结构类 ===')
chk('4 个浮动体已引用', all(f'\\ref{{{l}}}' in allt for l in ['fig:framework', 'tab:corr', 'tab:beta_pilot', 'fig:ode']))
chk('无硬编码 Section~III', 'III-B' not in allt and 'Section~III' not in allt)
chk('无未定义引用标记', '??' not in allt)
print('=== 摘要 ===')
m = re.search(r'\\begin\{abstract\}(.*?)\\end\{abstract\}', tex['paper_ap3/main.tex'], re.S)
inner = re.sub(r'\$[^$]*\$', ' X ', m.group(1))
words = [w for w in re.sub(r'\\[a-zA-Z]+\*?\{|\\[a-zA-Z]+|[{}]|[\[\]]|\s+', ' ', inner).strip().split(' ') if w]
print('  abstract words =', len(words))
