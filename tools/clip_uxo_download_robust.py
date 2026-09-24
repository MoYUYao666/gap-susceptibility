"""稳健续传:显式 Range(bytes=S-) 追加,仅 206 才写,进度写日志。
保证主文件单调增长(不依赖 curl -C - 的隐式行为)。
"""
import os, subprocess, time, sys

URL = ('https://zenodo.org/records/13778485/files/'
       'data_export_recordings.7z?download=1')
TOTAL = 16658054765
OUT = 'data/ctx_uxo/recordings.7z'
PROG = 'data/ctx_uxo/dl_progress.log'
TMP = 'data/ctx_uxo/_chunk.tmp'
CHUNK = 67108864  # 64 MiB

def log(msg):
    with open(PROG, 'a', encoding='utf-8') as f:
        f.write('%s %s\n' % (time.strftime('%H:%M:%S'), msg))

last = -1
for it in range(3000):
    s = os.path.getsize(OUT) if os.path.exists(OUT) else 0
    if s >= TOTAL:
        log('DONE size=%d' % s)
        print('DONE', flush=True)
        sys.exit(0)
    if s != last:
        log('size=%d (%.1f%%)' % (s, 100.0 * s / TOTAL))
        last = s
    # 显式 Range 请求小分块(服务端对大 Range 返回 504;64MB 分块稳定 206)
    hi = min(TOTAL - 1, s + CHUNK - 1)
    r = subprocess.run(
        ['curl.exe', '-sS', '-L', '--max-time', '900', '--speed-time', '60',
         '--speed-limit', '4096', '-r', '%d-%d' % (s, hi), '-o', TMP,
         '-w', '%{http_code}', URL],
        capture_output=True, text=True)
    code = (r.stdout or '').strip()[-3:]
    tsize = os.path.getsize(TMP) if os.path.exists(TMP) else 0
    ok = code == '206' and tsize == hi - s + 1
    if ok:
        with open(OUT, 'ab') as f:
            with open(TMP, 'rb') as g:
                while True:
                    b = g.read(1 << 20)
                    if not b:
                        break
                    f.write(b)
        os.remove(TMP)
        log('append ok +%d (code=%s)' % (tsize, code))
    else:
        log('wait code=%s chunk=%d (expected +%d)' % (code, tsize, hi - s + 1))
        if os.path.exists(TMP):
            os.remove(TMP)
        time.sleep(20)
log('LOOP_CAP')
print('LOOP_CAP', flush=True)
sys.exit(3)
