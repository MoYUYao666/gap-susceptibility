"""视觉条件指令微调轨迹(VLM 全通道)——A2 最后一格。
Qwen2-VL-2B-Instruct + LoRA(LLM 层), 训练 = 帧(ML16K)+ QA 指令 chat template;
监控 = 67 类双模板文本嵌入(与纯文本版同一协议)。图 max_pixels=78400(280×280)。
labels: 简式 LM 目标(未 mask 用户段), 论文如实标注。
输出: outputs/vlm_vision_instruction_dynamics.json
"""
import os, sys, json, glob
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image
from scipy import stats
from transformers import Qwen2VLForConditionalGeneration, AutoProcessor, AutoTokenizer
from peft import LoraConfig, get_peft_model

MDIR = 'models/Qwen2-VL-2B-Instruct'
SUB = 'outputs/ocean_subset.json'
ROOT = 'data/marinelife16k/data/selected_frames'
OUT = 'outputs/vlm_vision_instruction_dynamics.json'
SEED = 42
EPOCHS = 10
LR = 1e-4
BATCH = 1
GRAD_ACC = 4


def set_seed(s):
    np.random.seed(s)
    torch.manual_seed(s)
    torch.cuda.manual_seed_all(s)


def build_pairs(root):
    pairs = []
    for qf in sorted(glob.glob(os.path.join(root, '*', '*', 'qa.jsonl'))):
        vdir = os.path.dirname(qf)
        frames = sorted(glob.glob(os.path.join(vdir, '*.jpg')))
        if not frames:
            continue
        with open(qf, encoding='utf-8') as f:
            for li, line in enumerate(f):
                line = line.strip()
                if not line:
                    continue
                try:
                    d = json.loads(line)
                except Exception:
                    continue
                q, a = d.get('question', ''), d.get('answer_text', '')
                if q and a:
                    pairs.append((frames[li % len(frames)], q, a))
    return pairs


def class_texts():
    sub = json.load(open(SUB, encoding='utf-8'))
    return sub['classes']


def embed(m, tok, texts):
    out = []
    with torch.no_grad(), torch.autocast('cuda', dtype=torch.bfloat16):
        for i in range(0, len(texts), 16):
            ids = tok(texts[i:i + 16], return_tensors='pt', padding=True,
                      truncation=True, max_length=32).to('cuda')
            res = m.model(**ids, output_hidden_states=True)
            h = res.hidden_states[-1]
            seq = ids['attention_mask'].sum(1) - 1
            last = h[torch.arange(len(seq), device='cuda'), seq]
            out.append(F.normalize(last.float(), dim=-1))
    return torch.cat(out)


def protocol(m, tok, textsA, textsB):
    EA, EB = embed(m, tok, textsA), embed(m, tok, textsB)
    gap = (EA.mean(0) - EB.mean(0))
    gnorm = gap.norm().item()
    dH = gap / gnorm
    m_c = (dH.cpu().numpy() @ EB.cpu().numpy().T)
    S0 = (EA @ EB.T).cpu().numpy()
    topk5 = np.argsort(-S0, axis=1)[:, :5]
    res = {'sigma_m': round(float(np.std(m_c)), 4),
           'mean_cos': round(float((EA @ EB.T).mean()), 4)}
    rows = []
    for l in [-1.0, -0.5, 0.0, 0.5, 1.0, 2.0]:
        with torch.no_grad():
            sh = F.normalize(EA + l * gnorm * dH, dim=-1)
        S = (sh @ EB.T).cpu().numpy()
        taus, preds = [], []
        for i in range(len(S)):
            k5 = topk5[i]
            s5 = S0[i][k5]
            d_pairs = s5[:, None] - s5[None, :]
            dm = -(m_c[k5][:, None] - m_c[k5][None, :])
            up = np.triu(np.ones((5, 5)), k=1).astype(bool)
            inv = (l * gnorm * dm[up] > d_pairs[up]).sum()
            preds.append(1.0 - 2 * inv / 10.0)
            r1, r2 = S0[i][k5], S[i][k5]
            if np.std(r1) < 1e-12 or np.std(r2) < 1e-12:
                continue
            t, _ = stats.kendalltau(r1, r2)
            if np.isfinite(t):
                taus.append(t)
        rows.append({'lambda': l, 'tau_meas': round(float(np.mean(taus)), 4),
                     'tau_pred': round(float(np.mean(preds)), 4)})
    with torch.no_grad():
        EB2 = F.normalize(EB - 1.0 * gnorm * dH, dim=-1)
    S2 = (EA @ EB2.T).cpu().numpy()
    taus2 = []
    for i in range(len(S0)):
        r1, r2 = S0[i][topk5[i]], S2[i][topk5[i]]
        if np.std(r1) < 1e-12 or np.std(r2) < 1e-12:
            continue
        t, _ = stats.kendalltau(r1, r2)
        if np.isfinite(t):
            taus2.append(t)
    rows.append({'lambda': 'text1.0', 'tau_meas': round(float(np.mean(taus2)), 4)})
    res['rows'] = rows
    res['tau_l1'] = [r['tau_meas'] for r in rows if r['lambda'] == 1.0][0]
    res['tau_text1'] = [r['tau_meas'] for r in rows if r['lambda'] == 'text1.0'][0]
    return res


def main():
    set_seed(SEED)
    cls = class_texts()
    textsA = ['a photo of a ' + c for c in cls]
    textsB = ['a detailed photo of a ' + c for c in cls]
    pairs = build_pairs(ROOT)
    print('vis-pairs=%d classes=%d' % (len(pairs), len(cls)), flush=True)

    m = Qwen2VLForConditionalGeneration.from_pretrained(
        MDIR, torch_dtype=torch.bfloat16, device_map='cuda')
    proc = AutoProcessor.from_pretrained(MDIR, trust_remote_code=True)
    tok = AutoTokenizer.from_pretrained(MDIR, trust_remote_code=True)
    m.model.config.use_cache = False
    m = get_peft_model(m, LoraConfig(
        r=16, lora_alpha=32, lora_dropout=0.05, bias='none',
        target_modules=['q_proj', 'k_proj', 'v_proj', 'o_proj',
                        'gate_proj', 'up_proj', 'down_proj']))
    m.train()
    opt = torch.optim.AdamW([p for p in m.parameters() if p.requires_grad], lr=LR, weight_decay=0.01)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=EPOCHS)

    # 模板预缓存 + 小图缓存(预处理瓶颈消除)
    from PIL import Image
    print('pre-caching templates + small frames...', flush=True)
    cache_dir = 'data/marinelife16k/_small'
    os.makedirs(cache_dir, exist_ok=True)
    cache_paths = []
    tpls = []
    for k, (fp, q, a) in enumerate(pairs):
        ck = os.path.join(cache_dir, '%05d.jpg' % k)
        if not os.path.exists(ck):
            im = Image.open(fp).convert('RGB')
            im.thumbnail((360, 360))
            im.save(ck, quality=88)
        cache_paths.append(ck)
        msg = [{'role': 'user', 'content': [{'type': 'image'},
                                            {'type': 'text', 'text': 'Question: ' + q}]},
               {'role': 'assistant', 'content': [{'type': 'text', 'text': ' ' + a}]}]
        tpls.append(proc.apply_chat_template(msg, add_generation_prompt=False, tokenize=False))
    print('cache done', flush=True)

    m.eval()
    base = protocol(m, tok, textsA, textsB)
    res = {'meta': {'model': 'Qwen2-VL-2B-Instruct + LoRA (vision-conditioned instruction tuning)',
                    'n_pairs': len(pairs), 'epochs': EPOCHS, 'lr': LR,
                    'note': 'full budget (10 epochs x full 3440 pairs); no gradient checkpointing '
                            '(0.44s/step, 6GB); simplified LM objective (user segment not masked); '
                            'max_pixels 19600; templates + frames pre-cached'}}
    print('frozen:', {k: v for k, v in base.items() if k != 'rows'}, flush=True)
    json.dump({'meta': res['meta'], 'frozen': base}, open(OUT, 'w', encoding='utf-8'), indent=1)

    n = len(pairs)
    traj = []
    for ep in range(EPOCHS):
        perm = np.random.RandomState(SEED + ep).permutation(n)
        m.train()
        tot, cnt = 0.0, 0
        opt.zero_grad()
        for i in range(0, n, 1):
            j = int(perm[i])
            try:
                inputs = proc(text=tpls[j], images=[Image.open(cache_paths[j])], return_tensors='pt',
                              min_pixels=3136, max_pixels=19600)
                inputs = {k: v.to('cuda') for k, v in inputs.items()}
                labels = inputs['input_ids'].clone()
                labels[labels == tok.pad_token_id] = -100
                with torch.autocast('cuda', dtype=torch.bfloat16):
                    out = m(**inputs, labels=labels)
                    loss = out.loss / GRAD_ACC
                loss.backward()
                cnt += 1
                if cnt % GRAD_ACC == 0:
                    opt.step()
                    opt.zero_grad()
                tot += out.loss.item()
            except Exception as e:
                print('  batch err', str(e)[:80], flush=True)
                continue
            del inputs, out, loss
        sched.step()
        m.eval()
        st = protocol(m, tok, textsA, textsB)
        st = {'epoch': ep + 1, 'loss': round(tot / max(cnt, 1), 4),
              **{k: v for k, v in st.items() if k != 'rows'}}
        traj.append(st)
        print('  ep%d loss=%.4f tau_l1=%.4f sigma_m=%.4f mean_cos=%.4f' %
              (ep + 1, st['loss'], st['tau_l1'], st['sigma_m'], st['mean_cos']), flush=True)
        json.dump({'meta': res['meta'], 'frozen': base, 'traj': traj},
                  open(OUT, 'w', encoding='utf-8'), indent=1)
    print('DONE ->', OUT, flush=True)


if __name__ == '__main__':
    main()
