from __future__ import annotations
from pathlib import Path
import os
import argparse
import io
import json
import re
from pathlib import Path
import numpy as np
import pandas as pd
import torch
from PIL import Image
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from transformers import AutoProcessor, BitsAndBytesConfig, Qwen2VLForConditionalGeneration
ROOT = Path(os.environ.get('GS_WORKSPACE', Path(__file__).resolve().parents[3]))
MODEL = ROOT / 'models/Qwen2-VL-2B-Instruct'
DATA_ROOT = Path(os.environ.get('GS_VQA_DATA', ROOT / 'data/vqa'))

def load_rows(n, dataset):
    p = sorted((DATA_ROOT / dataset / 'data').glob('train-*.parquet' if dataset != 'chartqa' else 'test-*.parquet'))[0]
    d = pd.read_parquet(p).head(n)
    rows = []
    for _, r in d.iterrows():
        im = Image.open(io.BytesIO(r['image']['bytes'])).convert('RGB')
        im.thumbnail((448, 448))
        if dataset == 'vqav2':
            ans = [str(r['multiple_choice_answer']).lower().strip()]
        elif dataset == 'chartqa':
            ans = [str(r['answer']).lower().strip()]
        else:
            ans = [str(a).lower().strip() for a in r['answers']]
        rows.append({'image': im, 'question': str(r['question']), 'answers': ans})
    return rows

def norm(s):
    s = s.lower().strip()
    s = re.sub('[^a-z0-9 ]+', ' ', s)
    return re.sub('\\s+', ' ', s).strip()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--rank', type=int, default=8)
    ap.add_argument('--seed', type=int, default=45)
    ap.add_argument('--train', type=int, default=80)
    ap.add_argument('--test', type=int, default=12)
    ap.add_argument('--epochs', type=int, default=3)
    ap.add_argument('--tower', default='both')
    ap.add_argument('--dataset', default='textvqa')
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        ap.error("Training requires --apply and a fresh --outdir")
    torch.manual_seed(a.seed)
    OUT = Path(a.outdir)
    OUT.mkdir(parents=True, exist_ok=True)
    output_name = f"qwen2vl__{a.dataset}__r{a.rank}__s{a.seed}__{a.tower}.json"
    if (OUT / output_name).exists():
        raise FileExistsError("Output already exists; choose a fresh --outdir")
    bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type='nf4', bnb_4bit_compute_dtype=torch.bfloat16)
    model = Qwen2VLForConditionalGeneration.from_pretrained(str(MODEL), quantization_config=bnb, device_map={'': 0}, torch_dtype=torch.bfloat16, local_files_only=True)
    processor = AutoProcessor.from_pretrained(str(MODEL), local_files_only=True)
    model = prepare_model_for_kbit_training(model)
    cfg = LoraConfig(r=a.rank, lora_alpha=2 * a.rank, lora_dropout=0.05, bias='none', target_modules=['q_proj', 'k_proj', 'v_proj'])
    model = get_peft_model(model, cfg)
    model.train()
    train_rows = load_rows(a.train, a.dataset)
    test_rows = load_rows(a.train + a.test, a.dataset)[a.train:]
    opt = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=0.0002)
    recs = []
    for ep in range(1, a.epochs + 1):
        losses = []
        for r in train_rows:
            msgs = [{'role': 'user', 'content': [{'type': 'image'}, {'type': 'text', 'text': r['question']}]}]
            prompt = processor.apply_chat_template(msgs, add_generation_prompt=True, tokenize=False)
            full = prompt + r['answers'][0] + '<|im_end|>'
            inp = processor(text=[full], images=[r['image']], return_tensors='pt').to(0)
            prompt_inp = processor(text=[prompt], images=[r['image']], return_tensors='pt').to(0)
            labels = inp['input_ids'].clone()
            labels[:, :prompt_inp['input_ids'].shape[1]] = -100
            out = model(**inp, labels=labels)
            out.loss.backward()
            torch.nn.utils.clip_grad_norm_([p for p in model.parameters() if p.requires_grad], 1.0)
            opt.step()
            opt.zero_grad(set_to_none=True)
            losses.append(float(out.loss.item()))
        model.eval()
        correct = 0
        for r in test_rows:
            msgs = [{'role': 'user', 'content': [{'type': 'image'}, {'type': 'text', 'text': r['question']}]}]
            prompt = processor.apply_chat_template(msgs, add_generation_prompt=True, tokenize=False)
            inp = processor(text=[prompt], images=[r['image']], return_tensors='pt').to(0)
            with torch.no_grad():
                gen = model.generate(**inp, max_new_tokens=8, do_sample=False)
            pred = norm(processor.batch_decode(gen[:, inp['input_ids'].shape[1]:], skip_special_tokens=True)[0])
            correct += int(any((pred == norm(x) for x in r['answers'])))
        model.train()
        rec = {'epoch': ep, 'train_loss': float(np.mean(losses)), 'em': correct / len(test_rows)}
        recs.append(rec)
        print('DONE', a.rank, a.seed, ep, rec, flush=True)
        key = f'qwen2vl__{a.dataset}__r{a.rank}__s{a.seed}__{a.tower}'
        (OUT / f'{key}.json').write_text(json.dumps({'run': vars(a), 'epochs': recs}, indent=2) + '\n', encoding='utf-8')
if __name__ == '__main__':
    main()
