import json, collections
import numpy as np

d = json.load(open('outputs/ocean_peft_ms.json', encoding='utf-8'))
g = collections.defaultdict(list)
order = [('bioclip', 'lora_text'), ('bioclip', 'fullft'),
         ('oceanclip', 'lora_text'), ('oceanclip', 'lora_both'),
         ('oceanclip', 'bitfit'), ('oceanclip', 'fullft')]
print('config                R@1 (mean +/- sd)      marine top1 (mean +/- sd)   top1 rel to frozen')
base = {'bioclip': 21.70, 'oceanclip': 24.19}
for k, v in d.items():
    tag, method, seed = k.split('__')
    g[(tag, method)].append(v)
for tag, method in order:
    rows = g[(tag, method)]
    r1 = np.array([r['flickr_R1'] for r in rows])
    t1 = np.array([r['marine_top1'] for r in rows])
    rel = 100 * (t1.mean() - base[tag]) / base[tag]
    print('%-18s %.4f +/- %.4f    %.2f +/- %.2f        %+.1f%%' %
          ('%s %s' % (tag, method), r1.mean(), r1.std(), t1.mean(), t1.std(), rel))
