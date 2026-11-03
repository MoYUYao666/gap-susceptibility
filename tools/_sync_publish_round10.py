"""把工作区中已变更/新增的发布物同步到 .worktrees/ap3-publish (origin/main)。

只同步文本/结果类文件: paper_ap3 的 tex/bib/spl/figures/pdf、outputs 的 json、
paper3/scripts/outputs 的 json、tools 的 py、docs 的 md、根目录若干文本文件。
输出: 新增/修改/未变计数 + 明细, 供提交前 review。
"""
import hashlib
import os

WT = '.worktrees/ap3-n10'
SKIP_DIRS = {'.git', '.worktrees', 'envs', '_fnpy', '__pycache__', 'node_modules'}

# (相对路径, 允许的扩展名; None = 目录内按扩展名过滤)
TARGETS = [
    ('outputs', ('.json',)),
    ('paper3/scripts/outputs', ('.json',)),
    ('tools', ('.py', '.json')),
    ('docs', ('.md',)),
]
ROOT_FILES = ['HANDOFF.md', 'README.md', 'requirements.txt', '.gitignore', 'AGENTS.md']


def md5(path):
    h = hashlib.md5()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def iter_targets():
    for base, exts in TARGETS:
        for dirpath, dirs, files in os.walk(base):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            for fn in files:
                if fn.lower().endswith(exts):
                    yield os.path.join(dirpath, fn)
    for fn in ROOT_FILES:
        if os.path.exists(fn):
            yield fn


new, chg, same, size = [], [], 0, 0
for src in iter_targets():
    dst = os.path.join(WT, src)
    if not os.path.exists(dst):
        new.append(src)
        size += os.path.getsize(src)
    elif md5(src) != md5(dst):
        chg.append(src)
        size += os.path.getsize(src)
    else:
        same += 1

print('unchanged: %d' % same)
print('new: %d, changed: %d, to copy: %.1f KB' % (len(new), len(chg), size / 1024))
for k, rows in (('NEW', sorted(new)), ('CHG', sorted(chg))):
    for r in rows:
        print('  %s %s' % (k, r))

if not new and not chg:
    raise SystemExit(0)

for src in new + chg:
    dst = os.path.join(WT, src)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with open(src, 'rb') as f, open(dst, 'wb') as g:
        g.write(f.read())
print('copied %d files' % (len(new) + len(chg)))
