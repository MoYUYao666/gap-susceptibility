import json, os, glob
ROOT = r"D:\Realdesktop\Wan\Important\New"
def L(p):
    with open(os.path.join(ROOT, p), "r", encoding="utf-8") as f: return json.load(f)

def show(obj, maxdepth=3, pre="", dep=0, maxlist=20):
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
            print(f"{pre}{json.dumps(obj)[:700]}")

for fn in ["outputs/vlm_instruction_dynamics.json","outputs/vlm_vision_instruction_dynamics.json",
           "outputs/ocean_replica.json","outputs/a1_theory_verify.json","outputs/a1_baseline_metrics.json",
           "outputs/master_results.json"]:
    print("="*100); print(fn)
    try: show(L(fn))
    except Exception as e: print("ERR", repr(e))
