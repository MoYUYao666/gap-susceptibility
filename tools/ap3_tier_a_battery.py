"""Tier A 本地实验电池: 串行执行所有 LLaVA 训练/干预运行(GPU 单进程), 幂等可续跑。

用法:
  python tools/ap3_tier_a_battery.py            # 跑全部未完成的运行
  python tools/ap3_tier_a_battery.py --stage A4 # 只跑某阶段
  python tools/ap3_tier_a_battery.py --force    # 忽略已有 JSON, 全部重跑
  python tools/ap3_tier_a_battery.py --list     # 只列出运行清单

每个运行: paper3/scripts/run_training.py <args>, stdout/stderr 存 paper3/scripts/logs/tier_a/<name>.log
运行完毕后打印 <name> -> delta_E 汇总表。
"""
import argparse
import json
import os
import subprocess
import sys
import time

PY = r'D:\Anaconda\envs\pytorch\python.exe'
SCRIPTS = os.path.join('paper3', 'scripts')
EXP = os.path.join(SCRIPTS, 'outputs', 'experiments')
LOGDIR = os.path.join(SCRIPTS, 'logs', 'tier_a')


def tag_for(a):
    """与 run_training.py 的 _tag 逻辑保持一致(用于幂等检查)。"""
    defaults = dict(lr=5e-5, warmup=False, compute_dtype='float16', opt='adamw', images_dir=None,
                    data_path=None, epochs=3, block_config='uniform', lang_only=False, target_proj=False,
                    grad_mask='none', lora_alpha=None, attn_targets='qkvo', batch_size=1, proj_rank=None,
                    data_offset=0)
    cur = dict(defaults)
    cur.update({k: v for k, v in a.items() if k in defaults and v is not None})
    if all(cur[k] == defaults[k] for k in defaults):
        return ''
    return '_lr%g_%s_%s_%s%s%s_e%d_bc%s%s%s%s%s%s%s%s%s' % (
        cur['lr'], 'w' if cur['warmup'] else 'nw', cur['compute_dtype'][:6], cur['opt'],
        '_imgs' if cur['images_dir'] else '',
        '_cap' if cur['data_path'] and 'caption' in cur['data_path'] else '',
        cur['epochs'], cur['block_config'],
        '_lang' if cur['lang_only'] else '',
        '_proj' if cur['target_proj'] else '',
        '' if cur['grad_mask'] == 'none' else '_gm' + cur['grad_mask'],
        '' if cur['lora_alpha'] is None else '_a%g' % cur['lora_alpha'],
        '' if cur['attn_targets'] == 'qkvo' else '_t' + cur['attn_targets'],
        '' if cur['batch_size'] == 1 else '_b%d' % cur['batch_size'],
        '' if cur['proj_rank'] is None else '_pr%d' % cur['proj_rank'],
        '' if cur['data_offset'] == 0 else '_o%d' % cur['data_offset'])


def build_runs():
    runs = []

    def add(stage, name, a):
        # 参考协议固定 3 epochs(run_training.py 的 --epochs 默认是 1, 必须显式传)
        a = {'epochs': 3, **a}
        runs.append({'stage': stage, 'name': name, 'args': a})

    # --- A5: 分配策略多种子 + 两个新策略 + vision 口径一致的对照臂 ---
    # uniformv1: LLM 全层 r4、vision r1 —— 与各策略(vision r1)同口径, 消除 vision 秩混淆
    for s in (42, 123, 456):
        add('A5', f'A5_uniformv1_s{s}', dict(rank=4, seed=s, block_config='uniformv1'))
    for s in (123, 456):
        add('A5', f'A5_uniform_s{s}', dict(rank=4, seed=s))
        add('A5', f'A5_exp_s{s}', dict(rank=8, seed=s, block_config='exp'))
        add('A5', f'A5_greedy_s{s}', dict(rank=8, seed=s, block_config='greedy'))
    for s in (42, 123):
        add('A5', f'A5_expnorm_s{s}', dict(rank=8, seed=s, block_config='expnorm'))
        add('A5', f'A5_deepavoid_s{s}', dict(rank=8, seed=s, block_config='deepavoid'))
    # --- A4: 扩大独立种子族(每条 ~34 min) ---
    for r in (5, 6):
        for s in (7, 17, 27, 37, 47):
            add('A4', f'A4_r{r}_s{s}', dict(rank=r, seed=s))
    # --- A2: 梯度通路门控(图/文 × r5/r6, seed 42) ---
    for r in (5, 6):
        for gm in ('image', 'text'):
            add('A2', f'A2_r{r}_{gm}_s42', dict(rank=r, seed=42, grad_mask=gm))
    # --- A6: 投影器/LLM 不对称秩 ---
    for s in (42,):
        add('A6', f'A6_projonly_r4_s{s}', dict(rank=4, seed=s, attn_targets='none', proj_rank=4))
        add('A6', f'A6_projhi_r16_llmlo_r2_s{s}', dict(rank=2, seed=s, proj_rank=16))
        add('A6', f'A6_projlo_r2_llmhi_r16_s{s}', dict(rank=16, seed=s, proj_rank=2))
    # --- A7: 三轴灵敏度(α / 注意力目标模块 / 批大小), 每个扰动相对参考协议 ---
    # 注: batch=4 在本机 8GB 上 OOM(CUDA out of memory, 4×576 图像 token 的 7B 反传),
    #     故批大小轴改用 batch=2(仍与参考的 batch=1 形成对照); OOM 本身作为设备约束证据记录。
    for r in (5, 6):
        add('A7', f'A7_r{r}_a32', dict(rank=r, lora_alpha=32))
        add('A7', f'A7_r{r}_q', dict(rank=r, attn_targets='q'))
        add('A7', f'A7_r{r}_b2', dict(rank=r, batch_size=2))
    # --- A8: 补充 10-epoch 亚临界轨迹(r4, 与已有 r5/r6 形成单调/回弹对照) ---
    add('A8', 'A8_r4_e10', dict(rank=4, epochs=10))
    return runs


def out_path(a):
    return os.path.join(EXP, 'verify_r%d_s%d%s.json' % (a['rank'], a['seed'], tag_for(a)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--stage', default=None)
    ap.add_argument('--force', action='store_true')
    ap.add_argument('--list', action='store_true')
    ap.add_argument('--only', default=None, help='只跑名字包含该子串的运行')
    args = ap.parse_args()

    runs = build_runs()
    if args.stage:
        runs = [r for r in runs if r['stage'] == args.stage]
    if args.only:
        runs = [r for r in runs if args.only in r['name']]

    todo = []
    for r in runs:
        a = {'rank': r['args'].get('rank', 8), 'seed': r['args'].get('seed', 42)}
        a.update({k: v for k, v in r['args'].items() if k not in ('rank', 'seed')})
        r['out'] = out_path(a)
        r['done'] = os.path.exists(r['out'])
        if args.list:
            print('%-8s %-34s %-8s %s' % (r['stage'], r['name'], 'DONE' if r['done'] else 'TODO',
                                          os.path.basename(r['out'])))
        elif args.force or not r['done']:
            todo.append(r)
    if args.list:
        print('total=%d todo=%d' % (len(runs), sum(1 for r in runs if not r['done'])))
        return

    os.makedirs(LOGDIR, exist_ok=True)
    print('runs to execute: %d (of %d)' % (len(todo), len(runs)), flush=True)
    results, t0 = [], time.time()
    for i, r in enumerate(todo, 1):
        argv = [PY, 'run_training.py'] + [str(x) for kv in r['args'].items() for x in
                                          (('--' + kv[0].replace('_', '-'), kv[1]) if kv[1] is not True else ('--' + kv[0].replace('_', '-'),))]
        logp = os.path.join(LOGDIR, r['name'] + '.log')
        print('[%d/%d] %s -> %s' % (i, len(todo), r['name'], os.path.basename(r['out'])), flush=True)
        ts = time.time()
        with open(logp, 'w', encoding='utf-8', errors='ignore') as lf:
            rc = subprocess.run(argv, cwd=SCRIPTS, stdout=lf, stderr=subprocess.STDOUT,
                                env={**os.environ, 'PYTHONUNBUFFERED': '1',
                                     'HF_HUB_DISABLE_PROGRESS_BARS': '1'}).returncode
        dt = time.time() - ts
        dE = None
        if os.path.exists(r['out']):
            try:
                dE = json.load(open(r['out'], encoding='utf-8')).get('delta_E')
            except Exception:
                pass
        results.append({'name': r['name'], 'rc': rc, 'sec': round(dt, 1), 'delta_E': dE,
                        'json': os.path.basename(r['out'])})
        print('    rc=%s  %.0fs  delta_E=%s' % (rc, dt, dE), flush=True)
        with open(os.path.join(LOGDIR, 'battery_summary.json'), 'w', encoding='utf-8') as f:
            json.dump({'elapsed_s': round(time.time() - t0, 1), 'results': results}, f, indent=1)
    print('ALL DONE in %.0f min' % ((time.time() - t0) / 60), flush=True)


if __name__ == '__main__':
    main()
