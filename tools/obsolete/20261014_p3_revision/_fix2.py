import json
p = 'outputs/bioclip_lora_instruction.json'
d = json.load(open(p, encoding='utf-8'))
d['meta']['note'] = ('contrastive training identical to full-FT replica; LoRA (r16/a32) applied to '
                     'both towers (matching c_fc/c_proj/out_proj layers); dual-tower PEFT variant')
json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('meta fixed')
