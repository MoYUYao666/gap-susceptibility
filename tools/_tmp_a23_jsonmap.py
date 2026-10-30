import json, os, sys, glob

ROOT = r"D:\Realdesktop\Wan\Important\New"

def walk(o, prefix="", depth=0, maxdepth=3, out=None, maxkeys=40):
    if out is None: out = []
    if depth > maxdepth: return out
    if isinstance(o, dict):
        for i, (k, v) in enumerate(o.items()):
            if i >= maxkeys:
                out.append(f"{prefix}... (+{len(o)-maxkeys} more keys)")
                break
            t = type(v).__name__
            if isinstance(v, (dict, list)):
                n = len(v)
                out.append(f"{prefix}{k}/ [{t} n={n}]")
                if depth < maxdepth:
                    walk(v, prefix + "  ", depth+1, maxdepth, out, maxkeys)
            else:
                out.append(f"{prefix}{k} = {v!r}")
    elif isinstance(o, list):
        if len(o) > 0 and isinstance(o[0], (dict, list)):
            out.append(f"{prefix}[0]/ [{type(o[0]).__name__}]  (list n={len(o)})")
            walk(o[0], prefix + "  ", depth+1, maxdepth, out, maxkeys)
        else:
            out.append(f"{prefix}(list n={len(o)}) sample={o[:6]}")
    return out

def main():
    targets = sys.argv[1:]
    for t in targets:
        p = t if os.path.isabs(t) else os.path.join(ROOT, t)
        print("=" * 100)
        print("FILE:", os.path.relpath(p, ROOT), "  size:", os.path.getsize(p))
        try:
            with open(p, "r", encoding="utf-8") as f:
                d = json.load(f)
        except Exception as e:
            print("  ERROR:", e); continue
        for line in walk(d):
            print("  " + line)

main()
