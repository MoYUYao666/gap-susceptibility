import json, os, glob, sys, re

ROOT = r"D:\Realdesktop\Wan\Important\New"
CACHE = os.path.join(ROOT, "tools", "_tmp_a23_index.json")

def walk(o, path, out):
    if isinstance(o, dict):
        for k, v in o.items():
            walk(v, f"{path}.{k}" if path else str(k), out)
    elif isinstance(o, list):
        for i, v in enumerate(o):
            walk(v, f"{path}[{i}]", out)
    elif isinstance(o, bool):
        pass
    elif isinstance(o, (int, float)):
        out.append((float(o), path))
    elif isinstance(o, str):
        out.append((o, path))

def build():
    idx = {}
    files = sorted(glob.glob(os.path.join(ROOT, "outputs", "*.json")))
    files += sorted(glob.glob(os.path.join(ROOT, "paper3", "scripts", "outputs", "**", "*.json"), recursive=True))
    for p in files:
        rel = os.path.relpath(p, ROOT)
        try:
            d = json.load(open(p, encoding="utf-8"))
        except Exception as e:
            continue
        flat = []
        walk(d, "", flat)
        idx[rel] = flat
    json.dump(idx, open(CACHE, "w", encoding="utf-8"))
    print("files:", len(idx), "leaf values:", sum(len(v) for v in idx.values()))

def load():
    if not os.path.exists(CACHE): build()
    return json.load(open(CACHE, encoding="utf-8"))

def find(target, tol=0.0005, want_str=False):
    idx = load()
    hits = []
    for fn, flat in idx.items():
        for val, path in flat:
            if want_str:
                if isinstance(val, str) and target in val:
                    hits.append((fn, path, val))
            else:
                if isinstance(val, float) and abs(val - target) <= tol:
                    hits.append((fn, path, val))
    return hits

if __name__ == "__main__":
    if sys.argv[1] == "build":
        build()
    else:
        for a in sys.argv[1:]:
            t = float(a)
            tol = float(os.environ.get("TOL", "0.0005"))
            h = find(t, tol)
            print(f"--- {t} (tol {tol}) : {len(h)} hits")
            for fn, path, v in h[:25]:
                print(f"    {fn} :: {path} = {v}")
