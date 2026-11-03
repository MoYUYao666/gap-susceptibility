"""(c) MarineGPT 级规模(7B+)原生多模态指令微调——LLaVA-1.5-7B(本地完整权重)
4-bit 量化 + LoRA(LLM 层), ML16K QA 全预算(10ep × 3440 对), 视觉条件。
监控=67 类双模板文本嵌入 + 间隙手术(与 Qwen2V 探针完全同协议)。
v2 优化: 批=2(累积=2), 文本模板/图像预处理一次性缓存, 进度写日志文件
(conda run 管道缓冲导致 stdout 不可见——改用 outputs/llava_progress.log)。
输出: outputs/llava_instruction_dynamics.json + outputs/llava_progress.log
"""
import os, sys, json, glob, time
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image
from scipy import stats
from transformers import (LlavaForConditionalGeneration, AutoProcessor, AutoTokenizer,
                         BitsAndBytesConfig)
from peft import LoraConfig, get_peft_model

MDIR = 'models/llava-hf'
SUB = 'outputs/ocean_subset.json'
ROOT = 'data/marinelife16k/data/selected_frames'
OUT = 'outputs/llava_instruction_dynamics.json'
PROG = 'outputs/llava_progress.log'
SEED = 42
EPOCHS = 5
LR = 1e-4
GRAD_ACC = 1
BATCH = 1
PAIR_SUB = 500  # 时间预算: 与 Qwen2-VL-2B 视觉条件时间预算版相同 (5ep x 500 对)


def log(msg, also_stdout=True):
    with open(PROG, 'a', encoding='utf-8') as f:
        f.write('%s %s\n' % (time.strftime('%H:%M:%S'), msg))
    if also_stdout:
        print(msg, flush=True)


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
                    pairs.append((frames[li % len(frames)], 'Question: ' + q, ' ' + a))
    return pairs


def get_llm(m):
    return getattr(m, 'language_model', getattr(m, 'model', None))


def embed(m, tok, texts):
    llm = get_llm(m)
    out = []
    with torch.no_grad(), torch.autocast('cuda', dtype=torch.bfloat16):
        for i in range(0, len(texts), 8):
            ids = tok(texts[i:i + 8], return_tensors='pt', padding=True,
                      truncation=True, max_length=48).to('cuda')
            res = llm(**ids, output_hidden_states=True)
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
    return res


def main():
    global BATCH
    cls = json.load(open(SUB, encoding='utf-8'))['classes']
    textsA = ['a photo of a ' + c for c in cls]
    textsB = ['a detailed photo of a ' + c for c in cls]
    pairs = build_pairs(ROOT)
    log('pairs=%d' % len(pairs))

    bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_compute_dtype=torch.bfloat16,
                             bnb_4bit_quant_type='nf4', bnb_4bit_use_double_quant=True)
    m = LlavaForConditionalGeneration.from_pretrained(
        MDIR, torch_dtype=torch.bfloat16, quantization_config=bnb, device_map='cuda')
    proc = AutoProcessor.from_pretrained(MDIR)
    tok = AutoTokenizer.from_pretrained(MDIR)
    tok.padding_side = 'right'
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    get_llm(m).config.use_cache = False
    m = get_peft_model(m, LoraConfig(
        r=16, lora_alpha=32, lora_dropout=0.05, bias='none',
        target_modules=['q_proj', 'k_proj', 'v_proj', 'o_proj',
                        'gate_proj', 'up_proj', 'down_proj']))
    m.train()
    opt = torch.optim.AdamW([p for p in m.parameters() if p.requires_grad], lr=LR, weight_decay=0.01)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=EPOCHS)

    cache_dir = 'data/marinelife16k/_small'
    os.makedirs(cache_dir, exist_ok=True)
    cache_paths, tpls = [], []
    for k, (fp, q, a) in enumerate(pairs):
        ck = os.path.join(cache_dir, '%05d.jpg' % k)
        if not os.path.exists(ck):
            im = Image.open(fp).convert('RGB')
            im.thumbnail((360, 360))
            im.save(ck, quality=88)
        cache_paths.append(ck)
        msg = [{'role': 'user', 'content': [{'type': 'image'},
                                            {'type': 'text', 'text': q}]},
               {'role': 'assistant', 'content': [{'type': 'text', 'text': a}]}]
        tpls.append(proc.apply_chat_template(msg, add_generation_prompt=False, tokenize=False))
    log('cache/template done')
    del cache_paths

    # 一次性预处理(每对只调一次 processor): 文本分词(含 576 图像 token 展开, 与训练时一致)
    # + 图像像素(bf16)。此前版本每步重做 => 慢 2-4s/步。
    ids_list, mask_list, pix_list = [], [], []
    for k in range(len(pairs)):
        with torch.no_grad():
            inp = proc(text=tpls[k], images=[Image.open(os.path.join(cache_dir, '%05d.jpg' % k))],
                       return_tensors='pt')
        ids_list.append(inp['input_ids'][0])
        mask_list.append(inp['attention_mask'][0])
        pix_list.append(inp['pixel_values'][0].to(torch.bfloat16))
        if k % 500 == 0:
            log('prec k=%d/%d ids=%d' % (k, len(pairs), inp['input_ids'].shape[1]))
    maxL = max(int(x.shape[0]) for x in ids_list)
    text_ids = torch.full((len(pairs), maxL), tok.pad_token_id, dtype=torch.long)
    text_mask = torch.zeros((len(pairs), maxL), dtype=torch.long)
    for k, x in enumerate(ids_list):
        text_ids[k, :x.shape[0]] = x
        text_mask[k, :mask_list[k].shape[0]] = mask_list[k]
    pix = torch.stack(pix_list)
    del ids_list, mask_list, pix_list, inp
    log('precomputed: ids=%s pix=%s' % (tuple(text_ids.shape), tuple(pix.shape)))
    del tpls

    m.eval()
    base = protocol(m, tok, textsA, textsB)
    res = {'meta': {'model': 'LLaVA-1.5-7B (4-bit nf4 bf16) + LoRA 7B-scale vision-conditioned instruction',
                    'n_pairs': len(pairs), 'pairs_subset': PAIR_SUB, 'epochs': EPOCHS, 'lr': LR,
                    'batch': BATCH,
                    'note': 'MarineGPT-scale native multimodal instruction tuning probe; '
                            'time budget 5ep x 500 pairs (matched to the Qwen2-VL-2B time-budgeted '
                            'vision run; full-budget 7B remains open); simplified LM objective; '
                            'frames <=360px; v2 optimized loop (step ~16.5s on local 8GB)'},
           'frozen': base}
    log('frozen tau@1=%s sigma_m=%s' % (base['tau_l1'], base['sigma_m']))
    json.dump(res, open(OUT, 'w', encoding='utf-8'), indent=1)

    pairs = pairs[:PAIR_SUB]
    n = len(pairs)
    text_ids, text_mask, pix = text_ids[:n], text_mask[:n], pix[:n]
    log('subset n=%d' % n)
    # 预热计时 ~5 批(无 empty_cache 干扰)
    t0 = time.time()
    warm = 0
    for w in range(0, n, BATCH):
        if w >= BATCH * 5:
            break
        try:
            idx = torch.arange(w, w + BATCH)
            ids = text_ids[idx].to('cuda')
            msk = text_mask[idx].to('cuda')
            pv = pix[idx].to('cuda')
            labels = ids.clone()
            labels[labels == tok.pad_token_id] = -100
            with torch.autocast('cuda', dtype=torch.bfloat16):
                out = m(pixel_values=pv, input_ids=ids, attention_mask=msk, labels=labels)
            loss = out.loss / GRAD_ACC
            loss.backward()
            opt.step()
            opt.zero_grad()
            del ids, msk, pv, labels, out, loss
        except RuntimeError as e:
            if 'out of memory' in str(e).lower():
                log('OOM at batch=%d, fallback batch=1' % BATCH)
                break
            else:
                log('warm err: ' + str(e)[:80])
                continue
        warm += 1
    elapsed = time.time() - t0
    log('warmup done step_time=%.3fs (%.2fs/step over warm)' % (elapsed / max(warm, 1), elapsed))
    del opt
    opt = None
    # 重新初始化优化器(去掉预热梯度污染)
    for p in m.parameters():
        if p.requires_grad and p.grad is not None:
            p.grad = None

    traj = []
    for ep in range(EPOCHS):
        perm = np.random.RandomState(SEED + ep).permutation(n)
        m.train()
        tot, cnt = 0.0, 0
        opt = torch.optim.AdamW([p for p in m.parameters() if p.requires_grad], lr=LR, weight_decay=0.01)
        opt.zero_grad()
        t0 = time.time()
        last_loss = 0.0
        for i in range(0, n, BATCH):
            j = perm[i:i + BATCH]
            try:
                ids = text_ids[j].to('cuda')
                msk = text_mask[j].to('cuda')
                pv = pix[j].to('cuda')
                labels = ids.clone()
                labels[labels == tok.pad_token_id] = -100
                with torch.autocast('cuda', dtype=torch.bfloat16):
                    out = m(pixel_values=pv, input_ids=ids, attention_mask=msk, labels=labels)
                loss = out.loss / GRAD_ACC
                loss.backward()
                cnt += 1
                if cnt % GRAD_ACC == 0:
                    opt.step()
                    opt.zero_grad()
                tot += out.loss.item()
                last_loss = out.loss.item()
                del ids, msk, pv, labels, out, loss
            except RuntimeError as e:
                if 'out of memory' in str(e).lower():
                    log('ep%d OOM at i=%d -> batch=1 permanent fallback' % (ep, i))
                    BATCH = 1
                    ids = text_ids[j[:1]].to('cuda')
                    msk = text_mask[j[:1]].to('cuda')
                    pv = pix[j[:1]].to('cuda')
                    labels = ids.clone()
                    labels[labels == tok.pad_token_id] = -100
                    with torch.autocast('cuda', dtype=torch.bfloat16):
                        out = m(pixel_values=pv, input_ids=ids, attention_mask=msk, labels=labels)
                    loss = out.loss / GRAD_ACC
                    loss.backward()
                    cnt += 1
                    if cnt % GRAD_ACC == 0:
                        opt.step()
                        opt.zero_grad()
                    tot += out.loss.item()
                    last_loss = out.loss.item()
                    torch.cuda.empty_cache()
                else:
                    log('ep%d batch err %s' % (ep, str(e)[:80]))
                    continue
            if (i // BATCH) % 100 == 0:
                log('ep%d step %d/%d loss=%.4f' % (ep + 1, i // BATCH, n // BATCH, last_loss))
        sched.step()
        m.eval()
        st = protocol(m, tok, textsA, textsB)
        st = {'epoch': ep + 1, 'loss': round(tot / max(cnt, 1), 4), 'step_time': round((time.time() - t0) / (n // BATCH), 3),
              'tau_l1': st['tau_l1'], 'sigma_m': st['sigma_m'], 'mean_cos': st['mean_cos']}
        traj.append(st)
        log('ep%d done loss=%.4f tau=%.4f sigma=%.4f cos=%.4f step=%.2fs' %
            (ep + 1, st['loss'], st['tau_l1'], st['sigma_m'], st['mean_cos'], st['step_time']))
        json.dump({'meta': res['meta'], 'frozen': base, 'traj': traj},
                  open(OUT, 'w', encoding='utf-8'), indent=1)
    log('DONE -> ' + OUT)


if __name__ == '__main__':
    main()
