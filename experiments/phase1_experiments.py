"""Phase 1: Adapter + Prefix Tuning comparison experiments — resumable"""
import os, json, time, sys
os.environ["HF_HUB_OFFLINE"] = "1"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pathlib import Path
from src.config import ExperimentConfig, AdapterConfig, PrefixConfig, LoRAConfig, TrainConfig
from src.trainer import GapAwareTrainer
from src.dataset import create_dataloaders

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "phase1"
MASTER_FILE = PROJECT_ROOT / "outputs" / "master_results.json"
DATA = "flickr30k"
BS, EPOCHS, SAMPLES = 128, 10, 5000


def load_master():
    """Load master_results.json"""
    if MASTER_FILE.exists():
        with open(MASTER_FILE, 'r') as f:
            return json.load(f)
    return {"experiments": {}}


def is_experiment_done(exp_name: str, master: dict) -> bool:
    """Check whether an experiment is already done (cg_delta present = complete)"""
    exps = master.get("experiments", {})
    for key, exp in exps.items():
        if exp.get("experiment") == exp_name and exp.get("cg_delta") is not None:
            return True
        if key.endswith(f"/{exp_name}") and exp.get("cg_delta") is not None:
            return True
    return False


def sync_master():
    """Call sync_results.py to update master_results.json"""
    import subprocess
    sync_script = PROJECT_ROOT / "analysis" / "sync_results.py"
    result = subprocess.run(
        [sys.executable, str(sync_script)],
        capture_output=True, text=True, cwd=str(PROJECT_ROOT),
    )
    if result.returncode != 0:
        print(f"⚠️ sync_results failed: {result.stderr[:200]}")
    return load_master()


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    experiments = [
        # === Adapter dim sweep (text_only) ===
        ("adapter_d4_text",  "adapter", AdapterConfig(bottleneck_dim=4,  apply_to_vision=False, apply_to_text=True), None),
        ("adapter_d8_text",  "adapter", AdapterConfig(bottleneck_dim=8,  apply_to_vision=False, apply_to_text=True), None),
        ("adapter_d16_text", "adapter", AdapterConfig(bottleneck_dim=16, apply_to_vision=False, apply_to_text=True), None),
        ("adapter_d32_text", "adapter", AdapterConfig(bottleneck_dim=32, apply_to_vision=False, apply_to_text=True), None),
        ("adapter_d64_text", "adapter", AdapterConfig(bottleneck_dim=64, apply_to_vision=False, apply_to_text=True), None),

        # === Adapter position sweep ===
        ("adapter_d16_both", "adapter", AdapterConfig(bottleneck_dim=16, apply_to_vision=True, apply_to_text=True), None),
        ("adapter_d16_vis",  "adapter", AdapterConfig(bottleneck_dim=16, apply_to_vision=True, apply_to_text=False), None),

        # === Prefix length sweep (text_only) ===
        ("prefix_l4_text",  "prefix", None, PrefixConfig(prefix_length=4,  apply_to_vision=False, apply_to_text=True)),
        ("prefix_l8_text",  "prefix", None, PrefixConfig(prefix_length=8,  apply_to_vision=False, apply_to_text=True)),
        ("prefix_l16_text", "prefix", None, PrefixConfig(prefix_length=16, apply_to_vision=False, apply_to_text=True)),
        ("prefix_l32_text", "prefix", None, PrefixConfig(prefix_length=32, apply_to_vision=False, apply_to_text=True)),
        ("prefix_l64_text", "prefix", None, PrefixConfig(prefix_length=64, apply_to_vision=False, apply_to_text=True)),

        # === Prefix position sweep ===
        ("prefix_l16_both", "prefix", None, PrefixConfig(prefix_length=16, apply_to_vision=True, apply_to_text=True)),
        ("prefix_l16_vis",  "prefix", None, PrefixConfig(prefix_length=16, apply_to_vision=True, apply_to_text=False)),
    ]

    # load master for duplicate checking
    master = load_master()

    total = len(experiments)
    completed = 0
    for idx, (name, method, adapter_cfg, prefix_cfg) in enumerate(experiments):
        save_dir = OUTPUT_DIR / name
        res_file = save_dir / "results.json"

        # double check: master_results.json or the local results.json
        if is_experiment_done(name, master) or (res_file.exists() and _has_cg_delta(res_file)):
            print(f"⏭ [{idx+1}/{total}] {name} — already done, skipping")
            completed += 1
            continue

        print(f"\n{'='*50}\n🔬 [{idx+1}/{total}] {name} (method={method})")
        t0 = time.time()
        config = ExperimentConfig(
            name=name, peft_method=method, adapter=adapter_cfg, prefix=prefix_cfg,
            train=TrainConfig(batch_size=BS, num_epochs=EPOCHS, max_samples=SAMPLES, save_dir=str(save_dir)),
        )
        tl, vl, _ = create_dataloaders(DATA, ".", batch_size=BS, max_samples=SAMPLES)
        trainer = GapAwareTrainer(config)
        result = trainer.train(tl, vl)
        save_dir.mkdir(parents=True, exist_ok=True)
        with open(res_file, 'w') as f:
            json.dump(result, f, indent=2)

        elapsed = time.time() - t0
        cg_init = result.get("initial_gap", {}).get("centroid_gap", 0)
        cg_final = result.get("final_gap", {}).get("centroid_gap", 0)
        delta = cg_final - cg_init if cg_init and cg_final else None
        r1 = result.get("final_task_metrics", {}).get("R@1", "N/A")
        print(f"   ✅ CG Δ={delta:+.4f}, R@1={r1}, {elapsed/60:.0f}min")

        # update master after each completed experiment
        master = sync_master()

    print(f"\n🎉 Phase 1 done ({completed} skipped, {total - completed} newly run)")


def _has_cg_delta(res_file: Path) -> bool:
    """Check whether the local results.json has a valid cg_delta"""
    try:
        with open(res_file) as f:
            data = json.load(f)
        init_gap = data.get("initial_gap") or {}
        final_gap = data.get("final_gap") or {}
        return (init_gap.get("centroid_gap") is not None and
                final_gap.get("centroid_gap") is not None)
    except Exception:
        return False


if __name__ == "__main__":
    main()
