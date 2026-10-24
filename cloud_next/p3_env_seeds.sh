#!/bin/sh
# P3 cloud round: environment-stack seeds (S29/S37) and full 451-question VQA (S28).
#
# Entry point for the GPU instance.  It exports the offline/HF cache variables, runs the two jobs in
# order with setsid-style background logging into cloud_next/logs/, then runs the two aggregation
# steps and prints the exact list of files to retrieve.  Every step is resumable: the runner skips a
# run whose output already exists and validates, so re-running this script after an interruption
# costs at most the run that was in flight.
#
# Nothing is started automatically, no cloud instance is required to prepare the bundle, and no
# particular AutoDL port is assumed anywhere (the retrieval commands below carry <PORT>/<HOST>
# placeholders for the operator to fill in).
#
# Usage on the instance:
#     bash cloud_next/p3_env_seeds.sh                       # both jobs, then both aggregations
#     bash cloud_next/p3_env_seeds.sh --job env-seeds       # job 1 and its aggregation only
#     bash cloud_next/p3_env_seeds.sh --job vqa-full        # job 2 and its aggregation only
#     bash cloud_next/p3_env_seeds.sh --dry-run             # print every command, run/write nothing
#
# cloud_next/run_all.sh calls this script as "p3_env_seeds.sh --job env-seeds", so --job is honoured
# exactly as given there.
#
# Environment overrides:
#     P3_BASE=/root/autodl-tmp/p3work   repository checkout on the instance
#     P3_DATA=/root/autodl-tmp          data disk that holds the caches (50 GB, not the root disk)
#     PY=/root/miniconda3/bin/python    interpreter of the torch 2.6.0+cu124 environment
#     P3_LIMIT=2                        run at most N pending training runs in this invocation
#     P3_ALLOW_NETWORK=1                do not force offline mode for the HF libraries
set -u

# ------------------------------------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------------------------------------
P3_BASE="${P3_BASE:-/root/autodl-tmp/p3work}"
P3_DATA="${P3_DATA:-/root/autodl-tmp}"
PY="${PY:-python}"
P3_LOGDIR="${P3_LOGDIR:-$P3_BASE/cloud_next/logs}"
P3_RUNNER="tools/_p1613_p3_cloud_runner.py"
P3_LIMIT="${P3_LIMIT:-}"
STAMP="$(date +%Y%m%d-%H%M%S)"
DRY=""
JOB="both"
while [ $# -gt 0 ]; do
    case "$1" in
        --dry-run) DRY="--dry-run" ;;
        --job) shift; JOB="${1:-both}" ;;
        --job=*) JOB="${1#--job=}" ;;
        *) echo "NOTE: ignoring unrecognised argument '$1'" ;;
    esac
    shift
done
case "$JOB" in
    env-seeds) DO_JOB1=1; DO_JOB2=0 ;;
    vqa-full) DO_JOB1=0; DO_JOB2=1 ;;
    both) DO_JOB1=1; DO_JOB2=1 ;;
    *) echo "ERROR: --job must be env-seeds, vqa-full or both (got '$JOB')"; exit 2 ;;
esac

echo "=============================================================================="
echo "P3 cloud round: env-stack seeds + full 451-question VQA"
echo "  repository : $P3_BASE"
echo "  data disk  : $P3_DATA"
echo "  python     : $PY"
echo "  logs       : $P3_LOGDIR"
echo "  job        : $JOB"
echo "  mode       : ${DRY:-run}"
echo "=============================================================================="

# ------------------------------------------------------------------------------------------------
# Preconditions
# ------------------------------------------------------------------------------------------------
[ -d "$P3_BASE" ] || { echo "ERROR: $P3_BASE does not exist"; exit 2; }
cd "$P3_BASE" || { echo "ERROR: cannot enter $P3_BASE"; exit 2; }
[ -f "$P3_RUNNER" ] || { echo "ERROR: $P3_RUNNER not found; is this the p3work checkout?"; exit 2; }

missing=""
[ -f paper3/scripts/run_training.py ] || missing="$missing paper3/scripts/run_training.py"
[ -f tools/_p1516_p3_vqa_downstream.py ] || missing="$missing tools/_p1516_p3_vqa_downstream.py"
[ -f tools/_p1595_p3_rank_separation.py ] || missing="$missing tools/_p1595_p3_rank_separation.py"
[ -f paper3/test-vqarad.parquet ] || missing="$missing paper3/test-vqarad.parquet"
[ -d models/llava-hf ] || missing="$missing models/llava-hf"
[ -d data/vqa_rad/images ] || missing="$missing data/vqa_rad/images"
if [ -n "$missing" ]; then
    echo "ERROR: missing inputs:$missing"
    echo "       Download models and datasets on the instance first (never upload weights), see"
    echo "       cloud_next/README.md: bash cloud_next/env_setup.sh"
    exit 2
fi

# ------------------------------------------------------------------------------------------------
# Environment: caches on the data disk, mirror endpoints, offline runtime
# ------------------------------------------------------------------------------------------------
export HF_ENDPOINT="${HF_ENDPOINT:-https://hf-mirror.com}"
export HF_HOME="${HF_HOME:-$P3_DATA/hf}"
export MODELSCOPE_CACHE="${MODELSCOPE_CACHE:-$P3_DATA/modelscope}"
export HF_HUB_DISABLE_XET="${HF_HUB_DISABLE_XET:-1}"
export TORCH_HOME="${TORCH_HOME:-$P3_DATA/torch}"
export PIP_INDEX_URL="${PIP_INDEX_URL:-https://pypi.tuna.tsinghua.edu.cn/simple}"
export PIP_CACHE_DIR="${PIP_CACHE_DIR:-$P3_DATA/pipcache}"
export PYTHONIOENCODING="${PYTHONIOENCODING:-utf-8}"
export KMP_DUPLICATE_LIB_OK="${KMP_DUPLICATE_LIB_OK:-TRUE}"
if [ "${P3_ALLOW_NETWORK:-0}" != "1" ]; then
    # Models and data are already on disk; refusing to reach out keeps a slow mirror from stalling
    # the round, and turns a missing cache into an immediate, readable error.
    export HF_HUB_OFFLINE=1
    export TRANSFORMERS_OFFLINE=1
fi

mkdir -p "$P3_LOGDIR" outputs/analysis || { echo "ERROR: cannot create $P3_LOGDIR"; exit 2; }
echo "HF_HOME=$HF_HOME  MODELSCOPE_CACHE=$MODELSCOPE_CACHE  HF_ENDPOINT=$HF_ENDPOINT"
echo "HF_HUB_OFFLINE=${HF_HUB_OFFLINE:-0}  TRANSFORMERS_OFFLINE=${TRANSFORMERS_OFFLINE:-0}"

# The archived stack suffix _torch26 means torch 2.6.x with CUDA 12.4; the runner refuses to run
# when the installed torch does not match, so record the stack here before anything is trained.
"$PY" - <<'PY'
import torch
print("torch=%s cuda=%s gpu=%s" % (torch.__version__, torch.version.cuda,
                                   torch.cuda.get_device_name(0) if torch.cuda.is_available()
                                   else "no cuda device"))
PY

# ------------------------------------------------------------------------------------------------
# Background launcher: setsid-style detachment, log per job, exit status propagated
# ------------------------------------------------------------------------------------------------
if setsid --wait true >/dev/null 2>&1; then
    bg() { setsid --wait "$@"; }          # detached session; the subshell still reports the status
else
    bg() { "$@"; }                        # fallback for a setsid without --wait
    echo "NOTE: setsid --wait is unavailable; jobs still run in the background with logging"
fi

BG_PID=""
launch() {
    # launch <name> <command...>; starts the job in the background and sets BG_PID.
    # It must not run inside a command substitution: the job has to stay a child of this shell so
    # that wait can collect its exit status.
    name="$1"
    shift
    log="$P3_LOGDIR/$name.$STAMP.log"
    bg "$@" >"$log" 2>&1 </dev/null &
    BG_PID=$!
    echo "$BG_PID" >"$P3_LOGDIR/$name.$STAMP.pid"
    echo "  started $name -> $log (pid $BG_PID)"
}

run_job() {
    # run_job <name> <command...>; waits for the job and records its exit status
    name="$1"
    shift
    launch "$name" "$@"
    wait "$BG_PID"
    rc=$?
    echo "$rc" >"$P3_LOGDIR/$name.$STAMP.rc"
    echo "  finished $name with exit $rc"
    return "$rc"
}

RUN_ARGS=""
STRICT="--strict"
if [ -n "$DRY" ]; then
    # A dry run must not report an acceptance failure for work that has not been done yet.
    RUN_ARGS="--dry-run"
    STRICT=""
fi
[ -n "$P3_LIMIT" ] && RUN_ARGS="$RUN_ARGS --limit $P3_LIMIT"

# ------------------------------------------------------------------------------------------------
# Job 1: environment-stack seeds (six runs, one subprocess each)
# ------------------------------------------------------------------------------------------------
JOB1=0
JOB2=0
JOB3=0
JOB4=0

if [ "$DO_JOB1" = "1" ]; then
    echo
    echo "--- job 1/4: env-seeds (torch 2.6/cu124, ranks 5 and 6, seeds 7/123/999) ---"
    # shellcheck disable=SC2086
    run_job env_seeds "$PY" "$P3_RUNNER" --job env-seeds $RUN_ARGS
    JOB1=$?
fi

# ------------------------------------------------------------------------------------------------
# Job 2: VQA on the full 451-question test set (three arms, one subprocess each)
# ------------------------------------------------------------------------------------------------
if [ "$DO_JOB2" = "1" ]; then
    echo
    echo "--- job 2/4: vqa-full (base, r=5, r=6 on all 451 test questions) ---"
    run_job vqa_full "$PY" "$P3_RUNNER" --job vqa-full $RUN_ARGS
    JOB2=$?
fi

# ------------------------------------------------------------------------------------------------
# Aggregation steps (deterministic; they always re-run so the archives match the final state)
# ------------------------------------------------------------------------------------------------
if [ "$DO_JOB1" = "1" ]; then
    echo
    echo "--- job 3/4: aggregate env-seeds -> outputs/analysis/p3_env_stack_seeds.json ---"
    # shellcheck disable=SC2086
    run_job agg_env "$PY" "$P3_RUNNER" --job env-seeds --aggregate $STRICT $RUN_ARGS
    JOB3=$?
fi

if [ "$DO_JOB2" = "1" ]; then
    echo
    echo "--- job 4/4: aggregate vqa-full -> outputs/analysis/p3_vqa_full_equivalence.json ---"
    # shellcheck disable=SC2086
    run_job agg_vqa "$PY" "$P3_RUNNER" --job vqa-full --aggregate $STRICT $RUN_ARGS
    JOB4=$?
fi

# ------------------------------------------------------------------------------------------------
# What must come back from the instance
# ------------------------------------------------------------------------------------------------
echo
echo "=============================================================================="
echo "Files to retrieve (exact list; instance root: $P3_BASE)"
echo "=============================================================================="
if [ "$DO_JOB1" = "1" ]; then
    echo "-- six new environment-stack archives --"
    for r in 5 6; do
        a=$((2 * r))
        for s in 7 123 999; do
            echo "paper3/scripts/outputs/experiments/verify_r${r}_s${s}_lr5e-05_nw_float1_adamw_e3_bcuniform_a${a}_torch26.json"
        done
    done
    echo "-- env-stack analysis archive and its provenance sidecar --"
    echo "outputs/analysis/p3_env_stack_seeds.json"
    echo "outputs/analysis/p3_env_seeds_runlog.json"
fi
if [ "$DO_JOB2" = "1" ]; then
    echo "-- three VQA archives and the equivalence analysis --"
    echo "outputs/analysis/cloud_vqa_full451_base.json"
    echo "outputs/analysis/cloud_vqa_full451_5.json"
    echo "outputs/analysis/cloud_vqa_full451_6.json"
    echo "outputs/analysis/p3_vqa_full_equivalence.json"
    echo "-- optional, only if the adapters should be re-usable without retraining (24 MB and 29 MB) --"
    echo "outputs/p3_vqa_adapters/r5_step/"
    echo "outputs/p3_vqa_adapters/r6_step/"
fi
echo "-- provenance sidecar --"
echo "cloud_next/logs/*.log   (this round's console logs, including the stack probe above)"
echo
echo "Retrieve from the laptop, filling in the current instance's port and host (no port is"
echo "assumed by this script):"
echo "  PORT=<PORT>; HOST=<HOST>"
echo "  scp -P \$PORT root@\$HOST:$P3_BASE/paper3/scripts/outputs/experiments/verify_r[56]_s*_torch26.json \\"
echo "      paper3/scripts/outputs/experiments/"
echo "  scp -P \$PORT root@\$HOST:$P3_BASE/outputs/analysis/cloud_vqa_full451_*.json outputs/analysis/"
echo "  scp -P \$PORT root@\$HOST:$P3_BASE/outputs/analysis/p3_env_stack_seeds.json \\"
echo "      root@\$HOST:$P3_BASE/outputs/analysis/p3_vqa_full_equivalence.json \\"
echo "      root@\$HOST:$P3_BASE/outputs/analysis/p3_env_seeds_runlog.json outputs/analysis/"
echo "  scp -P \$PORT -r root@\$HOST:$P3_BASE/cloud_next/logs/ cloud_next/logs/"
echo "  python cloud_next/verify_cloud_artifacts.py --apply   # re-run the gate locally"
echo
echo "Do NOT stop the instance before the archives are back and the gate passes locally."
echo "Shutdown order required by this repository: confirm outputs -> verify -> retrieve ->"
echo "  sync && ( shutdown -h now || poweroff || /usr/bin/shutdown -h now )"

# ------------------------------------------------------------------------------------------------
# Summary
# ------------------------------------------------------------------------------------------------
echo
echo "=============================================================================="
echo "Summary: env_seeds=$JOB1 vqa_full=$JOB2 agg_env=$JOB3 agg_vqa=$JOB4"
echo "  exit 3 from an aggregation means an acceptance criterion is unmet (see the log)."
echo "  logs: $P3_LOGDIR/*.$STAMP.log"
echo "=============================================================================="
rc=0
[ "$JOB1" -ne 0 ] && rc=1
[ "$JOB2" -ne 0 ] && rc=1
[ "$JOB3" -ne 0 ] && rc=1
[ "$JOB4" -ne 0 ] && rc=1
exit "$rc"