import json, os
ROOT = r"D:\Realdesktop\Wan\Important\New"
def L(p):
    with open(os.path.join(ROOT, p), "r", encoding="utf-8") as f: return json.load(f)

def show(obj, maxdepth=3, pre="", dep=0, maxlist=60):
    if dep > maxdepth: return
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, (dict, list)):
                print(f"{pre}{k}/  [{type(v).__name__} {len(v)}]")
                show(v, maxdepth, pre + "   ", dep + 1, maxlist)
            else:
                print(f"{pre}{k} = {v!r}")
    elif isinstance(obj, list):
        if obj and isinstance(obj[0], dict):
            for i, r in enumerate(obj[:maxlist]): print(f"{pre}[{i}] {json.dumps(r)}")
        else:
            print(f"{pre}{json.dumps(obj)[:600]}")

for fn in ["outputs/dynamics_matrix.json","outputs/dynamics_seed.json","outputs/dynamics_fathomnet.json",
           "outputs/bioclip_lora_instruction.json","outputs/bioclip_joint_training.json"]:
    print("="*100); print(fn)
    try: show(L(fn))
    except Exception as e: print("ERR", e)
print("="*100); print("threshold_calibration.json (keys only)")
d = L("outputs/threshold_calibration.json")
def keys(o, pre="", dep=0):
    if dep > 3: return
    if isinstance(o, dict):
        for k, v in o.items():
            if isinstance(v, (dict, list)):
                print(f"{pre}{k}/ [{type(v).__name__} {len(v)}]")
                keys(v, pre+"  ", dep+1)
            else:
                print(f"{pre}{k} = {v!r}")
    elif isinstance(o, list):
        print(f"{pre}[list {len(o)}] first={json.dumps(o[0])[:300] if o else None}")
keys(d)
