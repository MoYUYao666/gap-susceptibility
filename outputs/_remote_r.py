
import os, json, glob, subprocess
W = "/root/autodl-tmp/work"
os.chdir(W)

print("=== all results.json ===")
files = sorted(glob.glob("outputs/**/results.json", recursive=True))
print("  %d total" % len(files))
for f in files:
    try:
        d = json.load(open(f))
        cg0 = d.get("initial_gap", {}).get("centroid_gap")
        cg1 = d.get("final_gap", {}).get("centroid_gap")
        dlt = (cg1 - cg0) if (cg0 is not None and cg1 is not None) else None
        print("  %-56s CGΔ=%s" % (f[:56], ("%+.4f" % dlt) if dlt is not None else "?"))
    except Exception as e:
        print("  %-56s ERR %s" % (f[:56], str(e)[:60]))

print("\n=== Γ_m log (last 20 lines) ===")
p = "outputs_cloud_driver.log"
if os.path.exists(p):
    lines = open(p).read().splitlines()
    i = next((k for k, l in enumerate(lines) if "Γ_m" in l or "gamma" in l.lower()), max(0, len(lines)-25))
    for ln in lines[max(0, i-25):]:
        print("  " + ln[:150])

print("\n=== does gamma_clip.json exist ===")
print("  ", os.path.exists("outputs/analysis/gamma_clip.json"))
