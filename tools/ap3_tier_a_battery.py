"""Tier A local experiment battery: run all LLaVA training/intervention runs serially (single GPU process), idempotent and resumable.

Usage:
  python tools/ap3_tier_a_battery.py            # run every unfinished run
  python tools/ap3_tier_a_battery.py --stage A4 # run one stage only
  python tools/ap3_tier_a_battery.py --force    # ignore existing JSON, rerun everything
  python tools/ap3_tier_a_battery.py --list     # only list the run manifest

Per run: paper3/scripts/run_training.py <args>, stdout/stderr saved to paper3/scripts/logs/tier_a/<name>.log
After all runs finish, print a <name> -> delta_E summary table.
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
    """Keep consistent with the _tag logic of run_training.py (used for the idempotency check)."""
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
        # the reference protocol fixes 3 epochs (run_training.py's --epochs defaults to 1, so it must be passed explicitly)
        a = {'epochs': 3, **a}
        runs.append({'stage': stage, 'name': name, 'args': a})

    # --- A5: multi-seed allocation policies + two new policies + a control arm with a consistent vision convention ---
    # uniformv1: all LLM layers r4, vision r1 —— same convention as each policy (vision r1), removing the vision-rank confound
    for s in (42, 123, 456):
        add('A5', f'A5_uniformv1_s{s}', dict(rank=4, seed=s, block_config='uniformv1'))
    for s in (123, 456):
        add('A5', f'A5_uniform_s{s}', dict(rank=4, seed=s))
        add('A5', f'A5_exp_s{s}', dict(rank=8, seed=s, block_config='exp'))
        add('A5', f'A5_greedy_s{s}', dict(rank=8, seed=s, block_config='greedy'))
    for s in (42, 123):
        add('A5', f'A5_expnorm_s{s}', dict(rank=8, seed=s, block_config='expnorm'))
        add('A5', f'A5_deepavoid_s{s}', dict(rank=8, seed=s, block_config='deepavoid'))
    # --- A4: enlarge the independent seed family (~34 min each) ---
    for r in (5, 6):
        for s in (7, 17, 27, 37, 47):
            add('A4', f'A4_r{r}_s{s}', dict(rank=r, seed=s))
    # --- A2: gradient pathway masking (image/text × r5/r6, seed 42) ---
    for r in (5, 6):
        for gm in ('image', 'text'):
            add('A2', f'A2_r{r}_{gm}_s42', dict(rank=r, seed=42, grad_mask=gm))
    # --- A6: projector/LLM asymmetric ranks ---
    for s in (42,):
        add('A6', f'A6_projonly_r4_s{s}', dict(rank=4, seed=s, attn_targets='none', proj_rank=4))
        add('A6', f'A6_projhi_r16_llmlo_r2_s{s}', dict(rank=2, seed=s, proj_rank=16))
        add('A6', f'A6_projlo_r2_llmhi_r16_s{s}', dict(rank=16, seed=s, proj_rank=2))
    # --- A7: three-axis sensitivity (α / attention target modules / batch size), each perturbation relative to the reference protocol ---
    # note: batch=4 OOMs on this 8GB box (CUDA out of memory, 7B backward pass of 4×576 image tokens),
    #     so the batch-size axis uses batch=2 instead (still contrasting with the reference batch=1); the OOM itself is recorded as device-constraint evidence.
    for r in (5, 6):
        add('A7', f'A7_r{r}_a32', dict(rank=r, lora_alpha=32))
        add('A7', f'A7_r{r}_q', dict(rank=r, attn_targets='q'))
        add('A7', f'A7_r{r}_b2', dict(rank=r, batch_size=2))
    # --- A8: additional 10-epoch subcritical trajectory (r4, contrasting with the existing r5/r6 for monotonicity/rebound) ---
    add('A8', 'A8_r4_e10', dict(rank=4, epochs=10))
    return runs


def out_path(a):
    return os.path.join(EXP, 'verify_r%d_s%d%s.json' % (a['rank'], a['seed'], tag_for(a)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--stage', default=None)
    ap.add_argument('--force', action='store_true')
    ap.add_argument('--list', action='store_true')
    ap.add_argument('--only', default=None, help='only run runs whose name contains this substring')
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
