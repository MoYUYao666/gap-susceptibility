#!/bin/bash
# A23 multi-encoder threshold transfer -- cloud phase 4 entry point (cloud_next/run_all.sh phase4).
#
# What it does, in order:
#   1. pins HF_HOME / MODELSCOPE_CACHE / PIP cache to the DATA disk (the root disk is small),
#   2. fetches only the encoders that are not already in the local Hugging Face cache,
#   3. runs tools/_p1614_a23_multi_encoder_transfer.py --dry-run as a gate (plan + assertions +
#      "every selected encoder has weights on this host"),
#   4. runs --encode  (one cache file per encoder x corpus, resumable: a valid cache is reused),
#   5. runs --analyze (statistics + the ordered-pair transfer table with the paired bootstrap over images),
#   6. re-checks the produced JSON against the acceptance criteria,
#   7. prints the files to retrieve before the instance is stopped.
#
# DOWNLOAD POLICY (repository rule, highest priority): models are fetched ON THE SERVER, never uploaded from
# the laptop. Try the mirror first -- `HF_ENDPOINT=https://hf-mirror.com` with `snapshot_download` -- and
# measure the throughput on this host before trusting it (hosts differ by up to 60x on the same day). If the
# mirror is slow or dead, fall back to ModelScope; on ModelScope verify the repository id first with
# `HubApi().get_model_files('<repo>')` instead of guessing. Slow is not the same as stuck: only 30-60 s of
# zero progress counts as stuck, and "try parallel connections" comes before "switch source".
# The transfer script itself NEVER downloads: it loads with local_files_only=True and fails with the repo id
# to fetch if something is missing.
#
# Usage (from the checkout root on the instance):
#   bash cloud_next/a23_encoders.sh                 # 7 encoders x 3 corpora = 21 units
#   ADAPTED=0 bash cloud_next/a23_encoders.sh       # 5 generic encoders x 3 corpora = 15 units
#   BOOT=5000 bash cloud_next/a23_encoders.sh       # more bootstrap draws
#   UNITS="clip-vit-base-patch32__marine_optical" bash cloud_next/a23_encoders.sh   # one unit only
#
# Environment:
#   BASE      checkout on the instance           (default /root/autodl-tmp/p3work)
#   DISK      data disk holding the caches       (default /root/autodl-tmp)
#   PY        interpreter with torch/open_clip   (default python)
#   BOOT      bootstrap draws over images        (default 2000)
#   ADAPTED   1 = also encode BioCLIP/OceanCLIP  (default 1)
#   FETCH     1 = fetch missing encoders         (default 1; 0 = offline / caches already warm)
set -uo pipefail

BASE="${BASE:-/root/autodl-tmp/p3work}"
DISK="${DISK:-/root/autodl-tmp}"
PY="${PY:-python}"
BOOT="${BOOT:-2000}"
ADAPTED="${ADAPTED:-1}"
FETCH="${FETCH:-1}"
LOGS="$BASE/cloud_next/logs"
JSON_REL="${JSON_REL:-outputs/analysis/a23_multiencoder_transfer.json}"
CACHE_REL="${CACHE_REL:-outputs/analysis/_cache/a23_multiencoder}"
MODELS_ROOT="${MODELS_ROOT:-$BASE/models}"

export HF_ENDPOINT="${HF_ENDPOINT:-https://hf-mirror.com}"     # mirror first (see policy above)
export HF_HOME="$DISK/hf"                                      # weights on the data disk, not the root disk
export MODELSCOPE_CACHE="$DISK/ms_cache"
export HF_HUB_ENABLE_HF_TRANSFER="${HF_HUB_ENABLE_HF_TRANSFER:-1}"
export PIP_INDEX_URL="${PIP_INDEX_URL:-https://pypi.tuna.tsinghua.edu.cn/simple}"
export PIP_CACHE_DIR="$DISK/pipcache"
export PYTHONIOENCODING=utf-8
export PYTORCH_ALLOC_CONF="${PYTORCH_ALLOC_CONF:-expandable_segments:True}"
mkdir -p "$LOGS" "$HF_HOME" "$MODELSCOPE_CACHE" "$PIP_CACHE_DIR"

cd "$BASE" || { echo "!! checkout not found: $BASE (set BASE=...)"; exit 2; }

# ---------------------------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------------------------
run_logged() {                  # run_logged <logname> <command...>  (detached from the ssh session)
  local name="$1"; shift
  local log="$LOGS/$name.log"
  echo "== $name -> $log"
  # setsid keeps the job alive if the ssh session drops; it is Linux-only, so fall back to plain nohup
  # (e.g. when this script is smoke-tested under Git Bash on the laptop).
  if command -v setsid >/dev/null 2>&1; then
    setsid nohup "$@" </dev/null >>"$log" 2>&1 &
  else
    nohup "$@" </dev/null >>"$log" 2>&1 &
  fi
  local pid=$!
  wait "$pid"
  local rc=$?
  tail -n 5 "$log"
  [ $rc -ne 0 ] && echo "   !! $name exit $rc (full log: $log)"
  return $rc
}

probe_repo() {                  # probe_repo <repo> [allow_patterns...] -> prints the cached path or nothing
  "$PY" - "$@" <<'PYEOF'
import sys
try:
    from huggingface_hub import snapshot_download
except Exception:
    sys.exit(1)
repo, patterns = sys.argv[1], sys.argv[2:]
kw = {"allow_patterns": patterns} if patterns else {}
try:
    path = snapshot_download(repo, local_files_only=True, **kw)
except Exception:
    sys.exit(1)
print(path)
PYEOF
}

fetch_hf() {                    # fetch_hf <repo> [allow_patterns...]
  local repo="$1"; shift
  echo "   fetch(hf-mirror): $repo"
  "$PY" - "$repo" "$@" <<'PYEOF'
import sys
from huggingface_hub import snapshot_download
repo, patterns = sys.argv[1], sys.argv[2:]
kw = {"max_workers": 8, "allow_patterns": patterns} if patterns else {"max_workers": 8}
print("     ->", snapshot_download(repo, **kw))
PYEOF
}

fetch_ms() {                    # fetch_ms <repo>   (verify the id on ModelScope before relying on this)
  local repo="$1"
  echo "   fetch(modelscope): $repo"
  "$PY" - "$repo" <<'PYEOF'
import sys
from modelscope import snapshot_download
print("     ->", snapshot_download(sys.argv[1]))
PYEOF
}

fetch_encoder() {               # fetch_encoder <repo> [allow_patterns...]  -- skips a warm cache
  local repo="$1"; shift
  local have
  have="$(probe_repo "$repo" "$@" 2>/dev/null)"
  if [ -n "$have" ]; then
    echo "   ok (cached): $repo -> $have"
    return 0
  fi
  if fetch_hf "$repo" "$@"; then
    return 0
  fi
  echo "   mirror failed or too slow for $repo; falling back to ModelScope"
  if fetch_ms "$repo"; then
    return 0
  fi
  echo "   !! could not fetch $repo -- verify the repository id with HubApi().get_model_files()"
  return 1
}

# ---------------------------------------------------------------------------------------------
# 1. hardware / disk / mirror throughput (12 s per probe; choose by measurement, not by habit)
# ---------------------------------------------------------------------------------------------
echo "== hardware =="
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader 2>/dev/null || echo "   no nvidia-smi"
"$PY" -c "import torch, transformers, open_clip; print('   torch', torch.__version__, 'cuda', torch.cuda.is_available(), '| transformers', transformers.__version__, '| open_clip', open_clip.__version__)" 2>/dev/null || echo "   !! torch/transformers/open_clip not importable with $PY"
echo "== disk =="
df -h "$DISK" | tail -1
echo "== throughput probe (12 s) =="
for url in "https://hf-mirror.com/openai/clip-vit-base-patch32/resolve/main/config.json" \
           "https://pypi.tuna.tsinghua.edu.cn/simple/"; do
  bps=$(curl -sL -m 12 -o /dev/null -w '%{speed_download}' "$url" 2>/dev/null || echo 0)
  awk -v u="$url" -v b="${bps:-0}" 'BEGIN{printf "   %-72s %7.2f MB/s\n", u, b/1048576}'
done

# ---------------------------------------------------------------------------------------------
# 2. encoders (about 4.2 GB generic + 2.9 GB adapted; fetched once, reused afterwards)
# ---------------------------------------------------------------------------------------------
if [ "$FETCH" = "1" ]; then
  echo "== encoders =="
  fetch_encoder "openai/clip-vit-base-patch32"                       # ~600 MB  (transformers CLIP)
  fetch_encoder "google/siglip-base-patch16-224"                     # ~800 MB  (transformers SigLIP)
  fetch_encoder "openai/clip-vit-large-patch14"                      # ~1.7 GB  (transformers CLIP)
  fetch_encoder "facebook/dinov2-base"                               # ~350 MB  (vision tower + probe)
  # RemoteCLIP ships RN50 + ViT-B/32 + ViT-L/14 (2.7 GB); only the ViT-B/32 file is used here.
  fetch_encoder "chendelong/RemoteCLIP" "RemoteCLIP-ViT-B-32.pt" "*.json" "*.md" ".gitattributes"
  if [ "$ADAPTED" = "1" ]; then
    fetch_encoder "imageomics/bioclip"                               # ~600 MB  (BioCLIP base, open_clip format)
    fetch_encoder "zjunlp/OceanCLIP-0.15B"                           # ~2.3 GB  (BioCLIP base + epoch_50.pt)
  fi
else
  echo "== encoders: FETCH=0, using the local caches only =="
fi

# ---------------------------------------------------------------------------------------------
# 3. unit list (encoder x corpus), matching the registry in the script
# ---------------------------------------------------------------------------------------------
CORPORA="marine_optical acoustic_sonar rare_species"
GENERIC="clip-vit-base-patch32 siglip-base-patch16-224 clip-vit-large-patch14 dinov2-base remoteclip"
ADAPTED_ENC="bioclip oceanclip"
UNITS="${UNITS:-}"
if [ -z "$UNITS" ]; then
  for e in $GENERIC; do for c in $CORPORA; do UNITS="$UNITS,$e__$c"; done; done
  if [ "$ADAPTED" = "1" ]; then
    for e in $ADAPTED_ENC; do for c in $CORPORA; do UNITS="$UNITS,$e__$c"; done; done
  fi
  UNITS="${UNITS#,}"
fi
N_UNITS=$(echo "$UNITS" | tr ',' '\n' | grep -c .)
echo "== units: $N_UNITS (expected ordered pairs: $((N_UNITS * N_UNITS))) =="
echo "   $UNITS"

ENC_SEL=""
for u in $(echo "$UNITS" | tr ',' ' '); do ENC_SEL="$ENC_SEL,${u%%__*}"; done
ENC_SEL=$(echo "${ENC_SEL#,}" | tr ',' '\n' | sort -u | paste -sd, -)
ENC_SEL="${ENC_SEL%,}"

# ---------------------------------------------------------------------------------------------
# 4. dry-run gate: plan, assertions, model availability
# ---------------------------------------------------------------------------------------------
echo "== dry-run gate =="
run_logged "p4_a23_dryrun" "$PY" tools/_p1614_a23_multi_encoder_transfer.py --dry-run \
  --data-root "$BASE/data" --models-root "$MODELS_ROOT" --cache-root "$CACHE_REL" \
  --subset-json "$BASE/outputs/ocean_subset.json" --encoders "$ENC_SEL" --include-adapted \
  --units "$UNITS" --boot "$BOOT" --out "$BASE/$JSON_REL"
rc=$?
if [ $rc -ne 0 ]; then
  echo "   !! the dry-run gate failed (missing weights or a plan/JSON mismatch) -- stopping before encoding."
  echo "      fix the fetch step, or re-run with ADAPTED=0 / a smaller UNITS list."
  exit $rc
fi

# ---------------------------------------------------------------------------------------------
# 5. encode  (resumable: valid caches are reused; only missing units are encoded)
# ---------------------------------------------------------------------------------------------
echo "== encode =="
run_logged "p4_a23_encode" "$PY" tools/_p1614_a23_multi_encoder_transfer.py --encode \
  --data-root "$BASE/data" --models-root "$MODELS_ROOT" --cache-root "$CACHE_REL" \
  --subset-json "$BASE/outputs/ocean_subset.json" --encoders "$ENC_SEL" --include-adapted \
  --units "$UNITS" --boot "$BOOT" --out "$BASE/$JSON_REL" --allow-missing-models
rc=$?
if [ $rc -ne 0 ]; then
  echo "   !! encode failed (exit $rc); see $LOGS/p4_a23_encode.log"
  exit $rc
fi

# ---------------------------------------------------------------------------------------------
# 6. analyze  (statistics + transfer table + bootstrap; rebuilds the JSON from the caches)
# ---------------------------------------------------------------------------------------------
echo "== analyze =="
run_logged "p4_a23_analyze" "$PY" tools/_p1614_a23_multi_encoder_transfer.py --analyze \
  --data-root "$BASE/data" --models-root "$MODELS_ROOT" --cache-root "$CACHE_REL" \
  --subset-json "$BASE/outputs/ocean_subset.json" --encoders "$ENC_SEL" --include-adapted \
  --units "$UNITS" --boot "$BOOT" --out "$BASE/$JSON_REL"
rc=$?
if [ $rc -ne 0 ]; then
  echo "   !! analyze failed (exit $rc); see $LOGS/p4_a23_analyze.log"
  exit $rc
fi

# ---------------------------------------------------------------------------------------------
# 7. acceptance criteria
# ---------------------------------------------------------------------------------------------
echo "== acceptance check =="
"$PY" - "$BASE/$JSON_REL" "$BASE/$CACHE_REL" "$N_UNITS" <<'PYEOF'
import io, json, os, sys
json_rel, cache_rel, n_units_expected = sys.argv[1], sys.argv[2], int(sys.argv[3])
fail = []


def check(cond, msg):
    print("   [%s] %s" % ("OK  " if cond else "FAIL", msg))
    if not cond:
        fail.append(msg)


if not os.path.exists(json_rel):
    check(False, "%s exists" % json_rel)
    sys.exit(1)
doc = json.load(io.open(json_rel, encoding="utf-8"))
for key in ("meta", "encoders", "correlations", "transfer", "conclusion", "limits"):
    check(key in doc, "top-level key '%s'" % key)
units = doc["transfer"]["units"]
pairs = doc["transfer"]["pairs"]
check(len(units) == n_units_expected, "units = %d (expected %d)" % (len(units), n_units_expected))
check(len(pairs) == len(units) ** 2, "ordered pairs = %d (expected %d)" % (len(pairs), len(units) ** 2))
check(doc["meta"]["complete_for_selection"], "meta.complete_for_selection is true")
missing_cache = []
for u in units:
    enc, corp = u.split("__", 1)
    if not os.path.exists(os.path.join(cache_rel, "%s__%s.npz" % (enc, corp))):
        missing_cache.append(u)
    block = doc.get("encoders", {}).get(enc, {}).get("corpora", {}).get(corp)
    if block is None:
        fail.append("unit %s has no row block" % u)
    elif len(block.get("rows", [])) != 9:
        fail.append("unit %s has %d family rows (expected 9)" % (u, len(block.get("rows", []))))
check(not missing_cache, "one cache file per unit%s" % ("" if not missing_cache else " -- missing: %s" % missing_cache))
scored = doc["conclusion"]["n_scored_entries_cross_unit"]
self_scored = doc["conclusion"]["n_scored_entries_self_pairs"]
check(scored > 0 or len(units) < 2,
      "scored cross-unit (pair, statistic) entries = %d (self-pair entries: %d)" % (scored, self_scored))
boot_ok = all("delta_vs_chance_ci95" in p["by_statistic"][k]["bootstrap"]
              for p in pairs for k in p["by_statistic"])
check(boot_ok, "every pair x statistic carries the bootstrap interval")
check("survives_paired_bootstrap" in json.dumps(doc["conclusion"]) or
      "n_entries_surviving_bootstrap" in doc["conclusion"],
      "conclusion states whether a pair survived the paired bootstrap")
print("   units=%d pairs=%d scored_entries=%d above_chance=%d survivors=%d"
      % (len(units), len(pairs), scored, doc["conclusion"]["n_entries_above_chance"],
         doc["conclusion"]["n_entries_surviving_bootstrap"]))
print("   conclusion: %s" % doc["conclusion"]["answer"])
print("   %s" % doc["conclusion"]["headline"])
print("   effect on the A23 text: %s" % doc["conclusion"]["effect_on_a23_text"]["action"])
sys.exit(1 if fail else 0)
PYEOF
rc=$?
if [ $rc -ne 0 ]; then
  echo "   !! acceptance check failed -- do NOT stop the instance (see the failed lines above)"
  exit $rc
fi

# ---------------------------------------------------------------------------------------------
# 8. retrieval list (copy these back, re-run the gate locally, only then stop the instance)
# ---------------------------------------------------------------------------------------------
echo
echo "== files to retrieve =="
echo "   $JSON_REL"
ls -l "$CACHE_REL"/*.npz 2>/dev/null | awk '{printf "   %s (%d bytes)\n", $9, $5}'
echo "   cloud_next/logs/p4_a23_{dryrun,encode,analyze}.log"
echo
echo "   from the laptop (port/password of the current instance):"
echo "     scp -P <PORT> root@<HOST>:$BASE/$JSON_REL outputs/analysis/"
echo "     scp -P <PORT> -r root@<HOST>:$BASE/$CACHE_REL/ $CACHE_REL/"
echo "     python cloud_next/verify_cloud_artifacts.py --phase phase4 --apply   # re-run AFTER the copy"
echo
echo "A23_ENCODERS_DONE -- verify, retrieve, then stop the instance (never the other way round)."