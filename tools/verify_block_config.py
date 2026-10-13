"""Verify that the exp rank_pattern is injected correctly (fast, no training)."""
import os, re, collections
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
import torch
from transformers import LlavaForConditionalGeneration, BitsAndBytesConfig
from peft import LoraConfig, get_peft_model, TaskType
from peft.utils import get_peft_model_state_dict

bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_compute_dtype=torch.float16,
                         bnb_4bit_quant_type='nf4', bnb_4bit_use_double_quant=True)
m = LlavaForConditionalGeneration.from_pretrained('models/llava-hf', torch_dtype=torch.bfloat16,
                                                  quantization_config=bnb, device_map='auto')
_pat = {r".*language_model\.layers\.([0-9])\..*": 6,
        r".*language_model\.layers\.(1[0-9]|2[0-3])\..*": 1,
        r".*language_model\.layers\.(2[4-9]|3[01])\..*": 5,
        r".*vision_tower.*": 1}
cfg = LoraConfig(r=1, lora_alpha=16, rank_pattern=_pat,
                 target_modules=['q_proj', 'k_proj', 'v_proj', 'o_proj'],
                 lora_dropout=0.1, bias='none', task_type=TaskType.CAUSAL_LM)
mm = get_peft_model(m, cfg)
sd = get_peft_model_state_dict(mm)
ranks = collections.Counter()
for k, t in sd.items():
    if 'lora_A' in k:
        li = re.search(r'layers\.(\d+)', k)
        key = ('vis' if 'vision_tower' in k else ('L' + li.group(1) if li else 'other'), 'v' if '.v_proj' in k or 'v_proj.' in k else '?')
        ranks[key[0]] = ranks[key[0]] or t.shape[0]
print('rank by location (lora_A first dim):', dict(ranks))
tot = sum(t.numel() for t in sd.values()) / 1e6
print('total trainable %.2fM' % tot)
