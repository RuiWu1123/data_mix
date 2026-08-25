#!/usr/bin/env bash
#SBATCH --job-name=onedial-q1-aggregate
#SBATCH --partition=devel
#SBATCH --time=00:30:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --output=/work1/ruixiangtang/rw761/data_mix_artifacts/slurm/onedial-q1-aggregate-%j.out
#SBATCH --error=/work1/ruixiangtang/rw761/data_mix_artifacts/slurm/onedial-q1-aggregate-%j.err

set -euo pipefail

cd /work1/ruixiangtang/rw761/awesome-pretraining/data_mix
: "${ONEDIAL_PHASE:?ONEDIAL_PHASE is required}"
: "${ONEDIAL_INPUT_ROOT:?ONEDIAL_INPUT_ROOT is required}"
: "${ONEDIAL_OUTPUT:?ONEDIAL_OUTPUT is required}"

PIPELINE_ARGS=()
if [[ -n "${ONEDIAL_PIPELINE:-}" ]]; then
  PIPELINE_ARGS=(--pipeline "$ONEDIAL_PIPELINE")
fi

/work1/ruixiangtang/rw761/data_mix_venv/bin/python scripts/run_onedial_q1.py aggregate \
  --protocol protocol_onedial.json \
  --phase "$ONEDIAL_PHASE" \
  "${PIPELINE_ARGS[@]}" \
  --input-root "$ONEDIAL_INPUT_ROOT" \
  --output "$ONEDIAL_OUTPUT"
