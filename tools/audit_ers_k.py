"""Check the source data for ERS slope k=0.043 vs k=0.088."""
import json
import glob
import re

# 1) effective_rank_tracking.json content summary
f = 'outputs/effective_rank_tracking.json'
try:
    d = json.load(open(f, encoding='utf-8'))
    s = json.dumps(d)
    print('=== effective_rank_tracking.json keys:', list(d)[:12])
    for m in re.finditer(r'"[^"]{0,30}(slope|k_|k")[^"]{0,30}"\s*:\s*[-0-9.eE]+', s):
        print('   ', m.group(0))
    for m in re.finditer(r'0\.0(43|88)[0-9]*', s):
        i = m.start()
        print('   ctx:', s[max(0, i - 90):i + 40].replace('\n', ' '))
except Exception as e:
    print(f, 'NA', e)

# 2) repo-wide scan for slope/k values
print('\n=== repo-wide slope/k ≈ 0.04 or 0.088 ===')
for fp in glob.glob('outputs/**/*.json', recursive=True):
    try:
        t = open(fp, encoding='utf-8', errors='ignore').read()
    except Exception:
        continue
    for m in re.finditer(r'"(slope|k|k_slope)"\s*:\s*(0\.0\d+)', t):
        v = float(m.group(2))
        if abs(v - 0.043) < 0.004 or abs(v - 0.088) < 0.006:
            print('  ', fp, m.group(0))
