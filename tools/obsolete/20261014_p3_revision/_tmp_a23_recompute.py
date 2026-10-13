# -*- coding: utf-8 -*-
"""Recompute every derived quantity claimed in the paper_a2 tables."""
import json, os, statistics as st
ROOT = r"D:\Realdesktop\Wan\Important\New"
def L(p): return json.load(open(os.path.join(ROOT, p), encoding="utf-8"))

def ms(vals, ddof=0):
    m = sum(vals)/len(vals)
    var = sum((v-m)**2 for v in vals)/ (len(vals)-ddof) if len(vals) > ddof else float('nan')
    return m, var**0.5

def chk(label, got, paper, tol=0.0006):
    ok = abs(got-paper) <= tol
    print(f"{'OK ' if ok else 'XX '} {label:<62} computed={got:<12.6g} paper={paper}")

print("="*100); print("TAB sonar-peft  (sonar_peft.json = seed42 ; sonar_peft_ms.json = s1,s99)")
lb = [L("outputs/sonar_peft.json")["lora_both"], L("outputs/sonar_peft_ms.json")["lora_both__s1"], L("outputs/sonar_peft_ms.json")["lora_both__s99"]]
ff = [L("outputs/sonar_peft.json")["fullft"], L("outputs/sonar_peft_ms.json")["fullft__s1"], L("outputs/sonar_peft_ms.json")["fullft__s99"]]
for nm, grp, papers in [("LoRA-both top1", lb, ("100.0", 0.0)),
                        ("LoRA-both R1",   lb, ("1.000", 0.0)),
                        ("LoRA-both tau",  lb, ("0.575", 0.062)),
                        ("FullFT top1",    ff, ("72.8", 36.2)),
                        ("FullFT tau",     ff, ("0.881", 0.015))]:
    key = "top1_0" if "top1" in nm else ("R1" if "R1" in nm else "tau_l1")
    vals = [g[key] for g in grp]
    for ddof in (0, 1):
        m, s = ms(vals, ddof)
        print(f"   {nm:<16} values={[round(v,4) for v in vals]} ddof={ddof}: mean={m:.4f} sd={s:.4f}")
    print(f"   paper: {papers}")

print("="*100); print("TAB dynamics (dynamics_matrix/dynamics_seed/ocean_tautraj)")
dm = L("outputs/dynamics_matrix.json"); ds = L("outputs/dynamics_seed.json"); ot = L("outputs/ocean_tautraj.json")
marine = {"s0": ds["bio_marine_s0"], "s1": ds["bio_marine_s1"], "s42": ot["marine"]}
sonar  = {"s42": dm["clip_sonar"], "s0": ds["clip_sonar_s0"], "s99": ds["clip_sonar_s99"], "s1": ds["clip_sonar_s1"]}
def traj_stats(grp, key, ep):
    return [g[ep-1][key] for g in grp.values()]
for label, grp, eps, papervals in [
        ("BioCLIP+Marine tau@1", marine, 1, (0.178, 0.008)),
        ("BioCLIP+Marine tau@10", marine, 10, (0.184, 0.010)),
        ("CLIP+Sonar tau@1", sonar, 1, (0.436, 0.200)),
        ("CLIP+Sonar tau@10", sonar, 10, (0.278, 0.140))]:
    vals = traj_stats(grp, "tau", eps)
    print(f"  {label}: seeds={sorted(grp)} values={[round(v,4) for v in vals]}")
    for ddof in (0,1):
        m,s = ms(vals, ddof); print(f"     ddof={ddof}: mean={m:.4f} sd={s:.4f}")
    print(f"     paper: {papervals}")
print("  -- sigma_m rows (only s0,s1 exist for BioCLIP+Marine) --")
for ep in (1, 10):
    vals = [marine[k][ep-1]["sigma_m"] for k in ("s0","s1")]
    m,s = ms(vals, 0); m1,s1 = ms(vals, 1)
    print(f"     BioCLIP+Marine sigma_m@{ep}: s0={vals[0]} s1={vals[1]} 2-seed mean={m:.4f} sd(ddof0)={s:.4f} sd(ddof1)={s1:.4f}")
print("  -- CLIP+Sonar sigma_m / top-1 --")
for ep, key in ((1,"sigma_m"), (10,"sigma_m"), (10,"top1")):
    vals = [sonar[k][ep-1][key] for k in ("s42","s0","s1")]
    print(f"     {key}@{ep}: values={vals}")
    for ddof in (0,1):
        m,s = ms(vals, ddof); print(f"        ddof={ddof}: mean={m:.4f} sd={s:.4f}")
print("     paper: sigma_m@1 0.0094+-0.009 ; sigma_m@10 0.0050+-0.001 ; top1@10 98.5+-1.5")
print("  -- 50ep row --")
e50 = ds["clip_sonar_50ep"]
print("     ep1 tau/sig:", e50[0]["tau"], e50[0]["sigma_m"], "| ep10:", e50[9]["tau"], e50[9]["sigma_m"], "| ep50:", e50[49]["tau"], e50[49]["sigma_m"], "top1:", e50[49]["top1"])
print("     paper: tau@1 0.276, tau@10 0.155, sig@1 0.0104, sig@10 0.0046, top1@10 100.0*")

print("="*100); print("TAB peft (ocean_peft_ms.json)")
pm = L("outputs/ocean_peft_ms.json")
groups = {}
for k, v in pm.items():
    model, meth, seed = k.split("__")
    groups.setdefault((model, meth), []).append(v)
paper_peft = {("bioclip","lora_text"): (0.114,0.004,22.95,0.20),
              ("bioclip","fullft"): (0.340,0.054,8.33,1.32),
              ("oceanclip","lora_text"): (0.348,0.004,23.36,0.13),
              ("oceanclip","lora_both"): (0.620,0.005,22.22,0.36),
              ("oceanclip","bitfit"): (0.178,0.002,23.51,0.05),
              ("oceanclip","fullft"): (0.587,0.015,20.52,0.71)}
for key, grp in groups.items():
    r1 = [g["flickr_R1"] for g in grp]; mt = [g["marine_top1"] for g in grp]
    for ddof in (0,1):
        m,s = ms(r1,ddof); m2,s2 = ms(mt,ddof)
        print(f"  {key} ddof={ddof}: R1={m:.4f}+-{s:.4f}  marine_top1={m2:.4f}+-{s2:.4f}")
    print(f"     paper: R1={paper_peft[key][0]}+-{paper_peft[key][1]}  top1={paper_peft[key][2]}+-{paper_peft[key][3]}")
print("  -- retentions (paper values) --")
base = {"OceanCLIP": 24.192, "BioCLIP": 21.704}
for key, grp in groups.items():
    m,_ = ms([g["marine_top1"] for g in grp])
    b = base["BioCLIP"] if key[0]=="bioclip" else base["OceanCLIP"]
    print(f"     {key}: {m:.4f}/{b} - 1 = {100*(m/b-1):+.2f}%")
print("     paper: +5.8 / -61.6 / -3.4 / -8.1 / -2.8 / -15.2")

print("="*100); print("TAB portrait / disc ratios")
def r(a,b): return a/b
print("  flatten disc: bio 0.0233/0.0064 =", round(r(0.0233,0.0064),3), " clip 0.0203/0.0092 =", round(r(0.0203,0.0092),3),
      " sat 0.0233/0.0078 =", round(r(0.0233,0.0078),3))
print("  sonar: 0.0239/0.0063 =", round(r(0.0239,0.0063),3), " 0.0247/0.0136 =", round(r(0.0247,0.0136),3),
      " 0.0247/0.0222 =", round(r(0.0247,0.0222),3), " marine-domain-diff vs terr 0.0239/0.0216 =", round(r(0.0239,0.0216),3))
print("  watertank 0.0287/0.0067 =", round(r(0.0287,0.0067),3), " below terr 0.0309/0.0067 =", round(r(0.0309,0.0067),3),
      " riku 0.0286/0.0213 =", round(r(0.0286,0.0213),3), " uatd 0.0176/0.0175 =", round(r(0.0176,0.0175),3))
print("  fauna 0.0595/0.0067 =", round(r(0.0595,0.0067),2), " inat 0.0611/0.0050 =", round(r(0.0611,0.0050),2))
print("="*100); print("TAB ml16k chance: 1/427 =", round(100/427,4), "%")
print("  replica 27.645/chance:", round(27.645/(100/427),1), " 11.657/0.872 =", round(11.657/0.872,1))
