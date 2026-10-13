"""Diagnostic: naming/group attribution of Llava decoder-style blocks (fast, no backward pass)."""
import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
from transformers import LlavaForConditionalGeneration, BitsAndBytesConfig
import torch

MDIR = 'models/llava-hf'
bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_compute_dtype=torch.bfloat16,
                         bnb_4bit_quant_type='nf4', bnb_4bit_use_double_quant=True)
m = LlavaForConditionalGeneration.from_pretrained(MDIR, torch_dtype=torch.bfloat16,
                                                  quantization_config=bnb, device_map='cuda')
par = dict(m.named_parameters())
print('total params:', len(par))
from collections import Counter
c = Counter()
for n, p in par.items():
    if n.startswith('vision_tower'):
        c['vision_tower'] += 1
    elif n.startswith('multi_modal_projector'):
        c['projector'] += 1
    elif '.layers.' in n:
        c['llm_layers'] += 1
    else:
        c['llm_other'] += 1
print(c)
# param numel per block
from collections import defaultdict
sz = defaultdict(float)
for n, p in par.items():
    if n.startswith('vision_tower'):
        k = 'vision_tower'
    elif n.startswith('multi_modal_projector'):
        k = 'projector'
    elif '.layers.' in n:
        k = 'llm_layers'
    else:
        k = 'llm_other'
    sz[k] += p.numel() / 1e6
print({k: round(v, 1) for k, v in sz.items()})
print('other param names:', [n for n, p in par.items() if not n.startswith('vision_tower') and not n.startswith('multi_modal_projector') and '.layers.' not in n])
print('layer-group prefixes:')
cnt = Counter()
for n, p in par.items():
    if '.layers.' in n:
        if n.startswith('model.layers.'):
            cnt['VISION_TRANSFORMER model.layers'] += 1
        elif n.startswith('model.language_model.model.layers.'):
            cnt['LLM language_model.model.layers'] += 1
        else:
            cnt['OTHER_layers'] += 1
print(cnt)
print('sample layer names:')
for n, p in par.items():
    if '.layers.' in n:
        print('  ', n)
        break
print('vis layer names:')
for n, p in par.items():
    if n.startswith('model.vision_tower'):
        print('  ', n)
        break
print('attr check:', [a for a in dir(m) if 'vision' in a.lower()][:6])
print('model attr:', type(getattr(m, 'model', None)).__name__ if hasattr(m, 'model') else 'NA')
print('model.mm attr:', [a for a in dir(m.model) if 'vision' in a.lower() or 'proj' in a.lower()][:8] if hasattr(m, 'model') else 'NA')
print('vision params in m.vision_named:', sum(1 for _ in m.vision_tower.named_parameters()) if hasattr(m, 'vision_tower') else 'NA')
print('proj params in m.named:', sum(1 for n, _ in m.multi_modal_projector.named_parameters()) if hasattr(m, 'multi_modal_projector') else 'NA')
# number of layers
layers = m.language_model.model.layers
print('num llm layers:', len(layers))
# projector module names
for n, mod in m.multi_modal_projector.named_modules():
    print('proj module:', n)
