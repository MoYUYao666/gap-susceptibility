"""Build the per-paper ownership map for outputs/ and quantify why moving the
files is unsafe. Read-only: writes only outputs_README draft text to stdout."""
import collections
import pathlib
import re

ROOT = pathlib.Path(r"D:\Realdesktop\Wan\Important\New")
OUT = ROOT / "outputs"

# ---- how many path references are built dynamically, which a literal
# ---- rename could never catch
SKIP = {"data", "models", "coco", "flickr30k", ".git", ".worktrees", "envs",
        "outputs", "备选", ".codegraph"}
dyn = 0
dyn_files = set()
for p in ROOT.rglob("*.py"):
    if set(p.relative_to(ROOT).parts) & SKIP:
        continue
    txt = p.read_text(encoding="utf-8", errors="ignore")
    n = len(re.findall(r"""join\(\s*['"]outputs['"]""", txt))
    n += len(re.findall(r"""(?:Path|ROOT|BASE|HERE)\s*/\s*['"]outputs['"]""", txt))
    if n:
        dyn += n
        dyn_files.add(p.name)
print(f"dynamic path constructions (os.path.join / Path-div): {dyn} in {len(dyn_files)} scripts")
print()

# ---- ownership by naming convention
GROUPS = [
    ("A1 — paper_a1/ (Neurocomputing NEUCOM-D-26-20952)",
     [r"^a1_class_aligned$", r"^a1_retrain$", r"^a1_rr_ckpt$", r"^a1_"]),
    ("A23 — paper_a2/ (IEEE JOE 26-0663, marine + sonar)",
     [r"^ocean_", r"^sonar_", r"^uatd_", r"^riku_", r"^watertank_", r"^ml16k_",
      r"^dynamics_fathomnet", r"^clip_ocean"]),
    ("P3 — paper3/paper_ieee/ (TNNLS, rejected) — LLaVA / Qwen",
     [r"^llava_", r"^qwen_cf_", r"^gamma_cost_", r"^gamma_llava", r"^vlm_",
      r"^c1_qwen", r"^c2c4_", r"^c3_", r"^e_family_selection",
      r"^allocation_policy_sim", r"^phase_stats_recompute",
      r"^device_reproducibility", r"^qwen"]),
    ("P1 — paper/ (Pattern Recognition PR-D-26-10149) and its merges ap3",
     [r"^clip_", r"^tier_a_", r"^e_sensitivity", r"^direction_",
      r"^perimage_operator", r"^mechanism_summary", r"^threshold_calibration",
      r"^strict_freeze$", r"^noise_", r"^adapter_layered", r"^layered_ft",
      r"^vitl_layered", r"^gsnr_", r"^effective_rank_tracking",
      r"^text_fine_grid", r"^bh_fdr", r"^clustered_bootstrap_dg"]),
    ("共享/早期（多篇共用或迁移前遗留）",
     [r"^theory$", r"^analysis$", r"^logs$", r"^paper_figures$", r"^tmp$",
      r"^blip2$", r"^coco$", r"^phase1$", r"^siglip$", r"^vitl$",
      r"^cross_method$", r"^route_[cde]$", r"^imagenet_zs", r"^flickr30k",
      r"^master_results", r"^domain_matrix", r"^dynamics_matrix",
      r"^dynamics_seed", r"^bioclip_", r"^zeroshot_extra", r"^imagenet1k_",
      r"^dtd_food101", r"^tinyimagenet", r"^gpu_info", r"^_"]),
]

items = sorted(p.name for p in OUT.iterdir())
assigned = {}
for name in items:
    for label, pats in GROUPS:
        if any(re.search(p, name) for p in pats):
            assigned[name] = label
            break
    else:
        assigned[name] = None

un = [n for n, v in assigned.items() if v is None]
print("=" * 78)
for label, _ in GROUPS:
    sel = [n for n, v in assigned.items() if v == label]
    nd = sum(1 for n in sel if (OUT / n).is_dir())
    print(f"{label}")
    print(f"    {len(sel)} 项（{nd} 目录）")
    for n in sorted(sel)[:10]:
        print(f"      - {n}")
    if len(sel) > 10:
        print(f"      ... 另有 {len(sel)-10} 项")
    print()

if un:
    print("未归类:", un)
