
import os, glob, json, subprocess, time
W = "/root/autodl-tmp/work"
os.chdir(W)

print("=== Artifact inventory saved before termination ===")
files = sorted(glob.glob("outputs/**/*.json", recursive=True))
print("  %d JSON artifacts" % len(files))
inv = []
for f in files:
    inv.append({"path": f, "bytes": os.path.getsize(f)})
json.dump(inv, open("_cloud_inventory.json", "w"), indent=1)
for f in files[:30]:
    print("   ", f)
print("  ..." if len(files) > 30 else "")

print("\n=== Γ_m values (extracted from the driver log) ===")
p = "outputs_cloud_driver.log"
if os.path.exists(p):
    for ln in open(p).read().splitlines():
        if "Γ_" in ln or "∇" in ln:
            print("  " + ln.strip()[:140])
