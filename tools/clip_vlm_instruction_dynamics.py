"""指令微调型(VLM LLM 组件)轨迹——A 的最后一格。
模型: Qwen2-VL-2B-Instruct (本地 models/Qwen2-VL-2B-Instruct), 仅语言模型 + LoRA(r=16, α=32)。
数据: MarineLife-16K QA (3,440 对) → 指令格式 "Question: {q}\\nAnswer: {a}" (q 段 labels=-100)。
监控: 67 类 fish-67 双模板嵌入 — A="a photo of a {c}"(查询/"图像"侧), B="a detailed photo of a {c}"(类侧);
      手术沿 g=μA−μB 方向; τ(冻结 top-5, 预测 vs 实测), σ_m, 类嵌入几何(Ω=类间平均余弦)。
输出: outputs/vlm_instruction_dynamics.json
"""
import os, sys, json, glob
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import torch
import torch.nn.functional as F
from scipy import stats
from transformers import Qwen2VLForConditionalGeneration, AutoTokenizer
from peft import LoraConfig, get_peft_model

MDIR = 'models/Qwen2-VL-2B-Instruct'
SUB = 'outputs/ocean_subset.json'
ROOT = 'data/marinelife16k/data/selected_frames'
OUT = 'outputs/vlm_instruction_dynamics.json'
SEED = 42
EPOCHS = 10
LR = 1e-4
BATCH = 4


def set_seed(s):
    np.random.seed(s)
    torch.manual_seed(s)
    torch.cuda.manual_seed_all(s)


def build_pairs(root):
    pairs = []
    for qf in sorted(glob.glob(os.path.join(root, '*', '*', 'qa.jsonl'))):
        with open(qf, encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    d = json.loads(line)
                except Exception:
                    continue
                q, a = d.get('question', ''), d.get('answer_text', '')
                if q and a:
                    pairs.append(('Question: ' + q + '\nAnswer: ', ' ' + a))
    return pairs


def class_texts():
    sub = json.load(open(SUB, encoding='utf-8'))
    return sub['classes']


def embed(m, tok, texts):
    """文本嵌入 = 语言模型最后层 hidden state 末 token, L2 归一化。"""
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
    # 文本侧 λ=1
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
    print('pairs=%d classes=%d' % (len(pairs), len(cls)), flush=True)

    m = Qwen2VLForConditionalGeneration.from_pretrained(
        MDIR, torch_dtype=torch.bfloat16, device_map='cuda')
    tok = AutoTokenizer.from_pretrained(MDIR, trust_remote_code=True)
    m.model.config.use_cache = False
    m.model.gradient_checkpointing_enable()
    m = get_peft_model(m, LoraConfig(
        r=16, lora_alpha=32, lora_dropout=0.05, bias='none',
        target_modules=['q_proj', 'k_proj', 'v_proj', 'o_proj',
                        'gate_proj', 'up_proj', 'down_proj']))
    m.train()
    opt = torch.optim.AdamW([p for p in m.parameters() if p.requires_grad], lr=LR, weight_decay=0.01)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=EPOCHS)

    # 冻结基线
    m.eval()
    base = protocol(m, tok, textsA, textsB)
    res = {'meta': {'model': 'Qwen2-VL-2B-Instruct + LoRA (text-only instruction tuning)',
                    'n_pairs': len(pairs), 'epochs': EPOCHS, 'lr': LR},
           'frozen': base}
    print('frozen:', {k: v for k, v in base.items() if k != 'rows'}, flush=True)
    json.dump(res, open(OUT, 'w', encoding='utf-8'), indent=1)

    n = len(pairs)
    traj = []
    for ep in range(EPOCHS):
        perm = np.random.RandomState(SEED + ep).permutation(n)
        m.train()
        tot, cnt = 0.0, 0
        for i in range(0, n, BATCH):
            sel = perm[i:i + BATCH]
            all_ids, all_lab = [], []
            for j in sel:
                q, a = pairs[j]
                qt = tok(q, add_special_tokens=False)['input_ids']
                at = tok(a, add_special_tokens=True)['input_ids']
                all_ids.append(qt + at)
                all_lab.append([-100] * len(qt) + at)
            mx = max(len(x) for x in all_ids)
            ids = torch.tensor([x + [tok.pad_token_id] * (mx - len(x)) for x in all_ids]).to('cuda')
            lab = torch.tensor([x + [-100] * (mx - len(x)) for x in all_lab]).to('cuda')
            att = (ids != tok.pad_token_id).long()
            opt.zero_grad()
            with torch.autocast('cuda', dtype=torch.bfloat16):
                out = m.model(input_ids=ids, attention_mask=att, labels=lab)
                loss = out.loss
            loss.backward()
            opt.step()
            tot += loss.item(); cnt += 1
            del ids, lab, att, out, loss
        sched.step()
        m.eval()
        st = protocol(m, tok, textsA, textsB)
        st = {'epoch': ep + 1, 'loss': round(tot / cnt, 4), **{k: v for k, v in st.items() if k != 'rows'}}
        traj.append(st)
        print('  ep%d loss=%.4f tau_l1=%.4f sigma_m=%.4f mean_cos=%.4f' %
              (ep + 1, st['loss'], st['tau_l1'], st['sigma_m'], st['mean_cos']), flush=True)
        json.dump({'frozen': res['frozen'], 'traj': traj,
                   'meta': res['meta']}, open(OUT, 'w', encoding='utf-8'), indent=1)
    print('DONE ->', OUT, flush=True)


if __name__ == '__main__':
    main()
