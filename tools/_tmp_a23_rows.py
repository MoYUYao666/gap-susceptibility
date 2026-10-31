import json, os, sys
ROOT = r"D:\Realdesktop\Wan\Important\New"
def L(p):
    with open(os.path.join(ROOT, p), "r", encoding="utf-8") as f:
        return json.load(f)

# dump full row lists
for fn in ["outputs/degradation_matrix.json","outputs/direction_subspace.json",
           "outputs/perimage_operator.json","outputs/direction_operator.json",
           "outputs/domain_matrix.json"]:
    d = L(fn)
    print("="*100); print(fn)
    def emit(tag, o):
        if isinstance(o, dict):
            if "rows" in o and isinstance(o["rows"], list):
                hdr = {k:v for k,v in o.items() if k != "rows"}
                print(f"  [{tag}] {json.dumps(hdr)}")
                for r in o["rows"]:
                    print("       ", json.dumps(r))
            else:
                for k,v in o.items(): emit(tag+"."+k, v)
        elif isinstance(o, list):
            for i,r in enumerate(o):
                print(f"  [{tag}][{i}] {json.dumps(r)}")
    for k,v in d.items():
        emit(k, v)
