import json, os
ROOT = r"D:\Realdesktop\Wan\Important\New"
def L(p):
    with open(os.path.join(ROOT, p), "r", encoding="utf-8") as f: return json.load(f)

def show(obj, maxdepth=3, pre="", dep=0, maxlist=12):
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
            print(f"{pre}{json.dumps(obj)[:500]}")

for fn in ["outputs/ocean_rank1_bound.json","outputs/watertank_protocol.json","outputs/riku_protocol.json",
           "outputs/uatd_protocol.json","outputs/dynamics_matrix.json","outputs/dynamics_seed.json",
           "outputs/dynamics_fathomnet.json","outputs/bioclip_lora_instruction.json",
           "outputs/bioclip_joint_training.json","outputs/threshold_calibration.json"]:
    print("="*100); print(fn); show(L(fn))
