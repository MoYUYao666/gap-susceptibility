import json, os
ROOT = r"D:\Realdesktop\Wan\Important\New"
def L(p):
    with open(os.path.join(ROOT, p), "r", encoding="utf-8") as f: return json.load(f)

def show(fn, maxdepth=4, pre="", dep=0, obj=None):
    if obj is None: obj = L(fn)
    if dep > maxdepth: return
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, (dict, list)):
                print(f"{pre}{k}/  [{type(v).__name__} {len(v)}]")
                show(fn, maxdepth, pre + "   ", dep + 1, v)
            else:
                print(f"{pre}{k} = {v!r}")
    elif isinstance(obj, list):
        if obj and isinstance(obj[0], dict):
            for i, r in enumerate(obj[:60]):
                print(f"{pre}[{i}] {json.dumps(r)}")
        else:
            print(f"{pre}{json.dumps(obj)[:400]}")

for fn in ["outputs/ocean_spectrum.json","outputs/ocean_degradation.json","outputs/ocean_tautraj.json",
           "outputs/text_fine_grid.json","outputs/sonar_spectrum.json","outputs/ocean_subset_fauna.json",
           "outputs/ocean_inat_wild.json","outputs/ocean_multitemplate.json","outputs/ocean_multiseed.json",
           "outputs/ocean_gap_surgery.json","outputs/mechanism_summary.json"]:
    print("="*100); print(fn); show(fn)
