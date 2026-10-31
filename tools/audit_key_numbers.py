"""核查合并稿关键数字来源: 相位表 / 机制章 / 反事实 / Qwen。"""
import json
import glob
import os

def show(f, depth=2, limit=30):
    try:
        d = json.load(open(f, encoding='utf-8'))
    except Exception as e:
        print(f, 'ERR', e)
        return
    print('=====', f)
    s = json.dumps(d)[:0]
    def walk(o, path='', lvl=0):
        if lvl > depth:
            return
        if isinstance(o, dict):
            for k, v in list(o.items())[:limit]:
                if isinstance(v, (int, float, str)):
                    print('  ' * lvl, path + '/' + str(k), '=', v)
                else:
                    walk(v, path + '/' + str(k), lvl + 1)
        elif isinstance(o, list):
            print('  ' * lvl, path, '[list', len(o), ']')
    walk(d)

# 相位表候选源
for pat in ['paper3/scripts/outputs/experiments/E2*.json',
            'paper3/scripts/outputs/experiments/all_results.json',
            'paper3/scripts/outputs/experiments/*qwen*results*.json',
            'paper3/scripts/outputs/experiments/*phase*.json',
            'outputs/*phase*.json']:
    for f in glob.glob(pat)[:3]:
        show(f, depth=2, limit=14)
