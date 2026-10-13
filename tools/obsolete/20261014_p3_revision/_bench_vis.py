import os, time, glob, json
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
import numpy as np
import torch
from PIL import Image
from transformers import Qwen2VLForConditionalGeneration, AutoProcessor, AutoTokenizer
from peft import LoraConfig, get_peft_model

MDIR = 'models/Qwen2-VL-2B-Instruct'
ROOT = 'data/marinelife16k/data/selected_frames'
pairs = []
for qf in sorted(glob.glob(os.path.join(ROOT, '*', '*', 'qa.jsonl')))[:40]:
    vdir = os.path.dirname(qf)
    frames = sorted(glob.glob(os.path.join(vdir, '*.jpg')))
    if not frames:
        continue
    with open(qf, encoding='utf-8') as f:
        for li, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            q, a = d.get('question', ''), d.get('answer_text', '')
            if q and a:
                pairs.append((frames[li % len(frames)], q, a))
pairs = pairs[:12]
print('pairs:', len(pairs))

proc = AutoProcessor.from_pretrained(MDIR, trust_remote_code=True)
tok = AutoTokenizer.from_pretrained(MDIR, trust_remote_code=True)

tpls = []
for fp, q, a in pairs:
    msg = [{'role': 'user', 'content': [{'type': 'image'}, {'type': 'text', 'text': 'Question: ' + q}]},
           {'role': 'assistant', 'content': [{'type': 'text', 'text': ' ' + a}]}]
    tpls.append(proc.apply_chat_template(msg, add_generation_prompt=False, tokenize=False))

for name, cp, mp in [('CPon_19600', True, 19600), ('CPoff_19600', False, 19600),
                     ('CPoff_7840', False, 7840)]:
    torch.cuda.empty_cache()
    m = Qwen2VLForConditionalGeneration.from_pretrained(
        MDIR, torch_dtype=torch.bfloat16, device_map='cuda')
    m.model.config.use_cache = False
    if cp:
        m.model.gradient_checkpointing_enable()
    m = get_peft_model(m, LoraConfig(
        r=16, lora_alpha=32, lora_dropout=0.05, bias='none',
        target_modules=['q_proj', 'k_proj', 'v_proj', 'o_proj',
                        'gate_proj', 'up_proj', 'down_proj']))
    m.train()
    opt = torch.optim.AdamW([p for p in m.parameters() if p.requires_grad], lr=1e-4)
    # 预热数据
    inputs = proc(text=tpls[0], images=[Image.open(pairs[0][0]).convert('RGB')],
                  return_tensors='pt', min_pixels=3136, max_pixels=mp)
    t0 = time.time()
    for k in range(6):
        j = k % len(pairs)
        inputs = proc(text=tpls[j], images=[Image.open(pairs[j][0]).convert('RGB')],
                      return_tensors='pt', min_pixels=3136, max_pixels=mp)
        inputs = {kk: vv.cuda() for kk, vv in inputs.items()}
        labels = inputs['input_ids'].clone()
        labels[labels == tok.pad_token_id] = -100
        opt.zero_grad()
        with torch.autocast('cuda', dtype=torch.bfloat16):
            out = m(**inputs, labels=labels)
            loss = out.loss
        loss.backward()
        opt.step()
    dt = (time.time() - t0) / 6
    print('%s: %.2fs/step  mem=%.0fMiB' % (name, dt, torch.cuda.max_memory_allocated() / 1e6), flush=True)
    del m, opt
    torch.cuda.empty_cache()
print('BENCH DONE')
