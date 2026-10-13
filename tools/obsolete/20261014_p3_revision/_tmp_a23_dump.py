import json, os, sys

ROOT = r"D:\Realdesktop\Wan\Important\New"

def L(p):
    with open(os.path.join(ROOT, p), "r", encoding="utf-8") as f:
        return json.load(f)

def pr(name, d, indent=0):
    print(" " * indent + f"{name}: {json.dumps(d, ensure_ascii=False)}")

if __name__ == "__main__":
    which = sys.argv[1]
    if which == "sonar":
        for fn in ["outputs/sonar_protocol_full.json", "outputs/sonar_protocol.json"]:
            d = L(fn)
            print("=" * 90); print(fn)
            for model, blk in d.items():
                if model == "meta":
                    pr("meta", blk); continue
                print(f"  -- {model}: gap_norm={blk.get('gap_norm')} sigma_m={blk.get('sigma_m')} mean_m={blk.get('mean_m')} top1_0={blk.get('top1_0')}")
                for r in blk.get("rows", []):
                    print("      ", json.dumps(r))
    elif which == "keys":
        # print top-level key tree for a list of files
        files = json.load(open(os.path.join(ROOT, "tools/_tmp_a23_files.json")))
        for fn in files:
            p = os.path.join(ROOT, fn)
            if not os.path.exists(p):
                print("MISSING", fn); continue
            d = L(fn)
            print("=" * 90); print(fn)
            def rec(o, pre="", dep=0):
                if dep > 2: return
                if isinstance(o, dict):
                    for k, v in list(o.items())[:60]:
                        if isinstance(v, dict):
                            print(f"  {pre}{k}/ [dict {len(v)}] keys={list(v.keys())[:14]}")
                            rec(v, pre + "  ", dep + 1)
                        elif isinstance(v, list):
                            s = v[0] if v else None
                            print(f"  {pre}{k} [list {len(v)}] first={json.dumps(s)[:220] if s is not None else None}")
                        else:
                            print(f"  {pre}{k} = {v!r}")
                elif isinstance(o, list):
                    print(f"  {pre}[list {len(o)}] first={json.dumps(o[0])[:220] if o else None}")
            rec(d)
