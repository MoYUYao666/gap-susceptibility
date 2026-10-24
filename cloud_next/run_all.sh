#!/bin/bash
# Resumable phase runner for the cloud round. Every job skips its work if the output already validates, so an
# interrupted phase can simply be re-run. Nothing here starts or stops the instance.
#
#   bash cloud_next/run_all.sh phase1|phase2|phase3|phase4|all
set -uo pipefail

BASE="${BASE:-/root/autodl-tmp/p3work}"
PY="${PY:-python}"
LOGS="$BASE/cloud_next/logs"
mkdir -p "$LOGS"
cd "$BASE"

export HF_HOME="${HF_HOME:-/root/autodl-tmp/hf}"
export MODELSCOPE_CACHE="${MODELSCOPE_CACHE:-/root/autodl-tmp/ms_cache}"
export PYTHONIOENCODING=utf-8
export PYTORCH_ALLOC_CONF=expandable_segments:True

run() {                      # run <logname> <command...>
  local name="$1"; shift
  local log="$LOGS/$name.log"
  echo "== $name -> $log"
  "$@" >"$log" 2>&1
  local rc=$?
  tail -n 4 "$log"
  [ $rc -ne 0 ] && echo "   !! $name exit $rc (see $log)"
  return $rc
}

skip_if_done() {             # skip_if_done <json path>
  [ -s "$1" ] && echo "   skip (exists): $1" && return 0 || return 1
}

# ---------------------------------------------------------------------------
# Phase 1 - decoder objective x scale ladder (the decisive experiment)
# ---------------------------------------------------------------------------
phase1() {
  echo "== PHASE 1: decoder objective x scale ladder (protocol=match) =="
  # decisive first: LLaVA-1.5-7B under BOTH objectives, seed 42
  for obj in contrastive generative; do
    skip_if_done "outputs/analysis/decoder_attribution_llava15-7b_${obj}_seed42.json" && continue
    run "p1_llava15-7b_${obj}_s42" \
      $PY tools/_p1612_objective_control_multimodel.py --model llava15-7b --objective $obj \
      --seed 42 --protocol match --apply
  done
  # ladder rungs: the 2B control re-run at the matched protocol, then scale up on the generative arm
  for obj in contrastive generative; do
    skip_if_done "outputs/analysis/decoder_attribution_qwen2vl-2b_${obj}_seed42.json" && continue
    run "p1_qwen2vl-2b_${obj}_s42" \
      $PY tools/_p1612_objective_control_multimodel.py --model qwen2vl-2b --objective $obj \
      --seed 42 --protocol match --apply
  done
  skip_if_done "outputs/analysis/decoder_attribution_qwen25vl-3b_generative_seed42.json" || \
    run "p1_qwen25vl-3b_generative_s42" \
      $PY tools/_p1612_objective_control_multimodel.py --model qwen25vl-3b --objective generative \
      --seed 42 --protocol match --apply
  skip_if_done "outputs/analysis/decoder_attribution_qwen25vl-7b_generative_seed42.json" || \
    run "p1_qwen25vl-7b_generative_s42" \
      $PY tools/_p1612_objective_control_multimodel.py --model qwen25vl-7b --objective generative \
      --seed 42 --protocol match --apply
  # extra seeds only after the seed-42 grid is complete
  if [ "${EXTRA_SEEDS:-0}" = "1" ]; then
    for s in 7 123; do
      for obj in contrastive generative; do
        skip_if_done "outputs/analysis/decoder_attribution_llava15-7b_${obj}_seed${s}.json" && continue
        run "p1_llava15-7b_${obj}_s${s}" \
          $PY tools/_p1612_objective_control_multimodel.py --model llava15-7b --objective $obj \
          --seed $s --protocol match --apply
      done
    done
  fi
  $PY cloud_next/verify_cloud_artifacts.py --phase phase1 --apply
}

# ---------------------------------------------------------------------------
# Phase 2 - P3 environment-stack seeds (torch 2.6 stack: r5/r6 x seeds 7,123,999)
# ---------------------------------------------------------------------------
phase2() {
  echo "== PHASE 2: P3 env-stack seeds =="
  run "p2_env_seeds" bash cloud_next/p3_env_seeds.sh --job env-seeds
  run "p2_env_seeds_agg" $PY tools/_p1613_p3_cloud_runner.py --job env-seeds --aggregate
  $PY cloud_next/verify_cloud_artifacts.py --phase phase2 --apply
}

# ---------------------------------------------------------------------------
# Phase 3 - P3 VQA on the full 451-question test set (inference only)
# ---------------------------------------------------------------------------
phase3() {
  echo "== PHASE 3: P3 VQA full test set =="
  run "p3_vqa_full" $PY tools/_p1613_p3_cloud_runner.py --job vqa-full --apply
  run "p3_vqa_agg" $PY tools/_p1613_p3_cloud_runner.py --job vqa-full --aggregate
  $PY cloud_next/verify_cloud_artifacts.py --phase phase3 --apply
}

# ---------------------------------------------------------------------------
# Phase 4 - A23 multi-encoder transfer
# ---------------------------------------------------------------------------
phase4() {
  echo "== PHASE 4: A23 multi-encoder transfer =="
  run "p4_a23_encoders" bash cloud_next/a23_encoders.sh
  $PY cloud_next/verify_cloud_artifacts.py --phase phase4 --apply
}

case "${1:-all}" in
  phase1) phase1 ;;
  phase2) phase2 ;;
  phase3) phase3 ;;
  phase4) phase4 ;;
  all)    phase1; phase2; phase3; phase4 ;;
  *)      echo "usage: $0 phase1|phase2|phase3|phase4|all"; exit 2 ;;
esac

echo
echo "== overall gate =="
$PY cloud_next/verify_cloud_artifacts.py --apply
echo "If the gate above says PASS, retrieve the artifacts and re-run it locally; only then stop the instance."