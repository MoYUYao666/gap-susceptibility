"""Tier A 总驱动: 一次性串行执行全部需要 GPU 的步骤(GPU 严格单进程)。

顺序(按价值/小时排序):
  1) LLaVA 训练电池 (tools/ap3_tier_a_battery.py) — A5 策略多种子 → A4 种子族 → A2 梯度门控
     → A6 不对称投影器 → A7 alpha → A8 10-epoch 亚临界
  2) A1 跨 PEFT 参数化 Γ 排序 (tools/clip_peft_gamma_ordering.py, CLIP, 分钟级)
  3) A3 跨批 Γ + 分层 bootstrap (tools/llava_gamma_batch_ci.py)

用法: python tools/ap3_tier_a_runall.py [--skip-battery] [--skip-clip] [--skip-batches]
日志: paper3/scripts/logs/tier_a/master_*.log; 汇总: outputs/tier_a_runall_status.json
"""
import argparse
import json
import os
import subprocess
import sys
import time

PY = r'D:\Anaconda\envs\pytorch\python.exe'
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGDIR = os.path.join(ROOT, 'paper3', 'scripts', 'logs', 'tier_a')
STATUS = os.path.join(ROOT, 'outputs', 'tier_a_runall_status.json')


def run_step(name, argv, timeout=None):
    os.makedirs(LOGDIR, exist_ok=True)
    logp = os.path.join(LOGDIR, 'master_%s.log' % name)
    print('=== [%s] %s' % (name, ' '.join(argv)), flush=True)
    t0 = time.time()
    with open(logp, 'w', encoding='utf-8', errors='ignore') as lf:
        rc = subprocess.run(argv, cwd=ROOT, stdout=lf, stderr=subprocess.STDOUT,
                            env={**os.environ, 'PYTHONUNBUFFERED': '1',
                                 'KMP_DUPLICATE_LIB_OK': 'TRUE', 'HF_HUB_DISABLE_PROGRESS_BARS': '1'},
                            timeout=timeout).returncode
    dt = time.time() - t0
    print('=== [%s] rc=%s in %.1f min (log %s)' % (name, rc, dt / 60, logp), flush=True)
    return {'step': name, 'rc': rc, 'minutes': round(dt / 60, 1), 'log': logp}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--skip-battery', action='store_true')
    ap.add_argument('--skip-clip', action='store_true')
    ap.add_argument('--skip-batches', action='store_true')
    a = ap.parse_args()
    steps = []
    if not a.skip_battery:
        steps.append(('battery', [sys.executable, os.path.join(ROOT, 'tools', 'ap3_tier_a_battery.py')]))
    if not a.skip_clip:
        steps.append(('a1_clip_peft_gamma', [PY, os.path.join(ROOT, 'tools', 'clip_peft_gamma_ordering.py')]))
    if not a.skip_batches:
        steps.append(('a3_llava_gamma_batches', [PY, os.path.join(ROOT, 'tools', 'llava_gamma_batch_ci.py')]))
    status = {'started': time.strftime('%Y-%m-%d %H:%M:%S'), 'steps': []}
    for name, argv in steps:
        try:
            status['steps'].append(run_step(name, argv))
        except Exception as e:  # noqa: BLE001
            status['steps'].append({'step': name, 'error': repr(e)})
        with open(STATUS, 'w', encoding='utf-8') as f:
            json.dump(status, f, indent=1)
    status['finished'] = time.strftime('%Y-%m-%d %H:%M:%S')
    json.dump(status, open(STATUS, 'w', encoding='utf-8'), indent=1)
    print('ALL GPU STEPS DONE', flush=True)


if __name__ == '__main__':
    main()
