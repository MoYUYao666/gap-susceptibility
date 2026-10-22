import torch
from transformers import AutoProcessor, BitsAndBytesConfig, LlavaForConditionalGeneration

P = '/root/autodl-tmp/p3work/models/llava-hf'
q = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_compute_dtype=torch.float16, bnb_4bit_use_double_quant=True)
m = LlavaForConditionalGeneration.from_pretrained(P, quantization_config=q, device_map='auto')
p = AutoProcessor.from_pretrained(P)
print('LOADED', round(torch.cuda.memory_allocated() / 1e9, 2), 'GB', p.tokenizer.convert_tokens_to_ids('<image>'))
