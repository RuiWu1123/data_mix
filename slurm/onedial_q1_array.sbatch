#!/usr/bin/env bash
#SBATCH --job-name=onedial-q1
#SBATCH --partition=devel
#SBATCH --time=00:30:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=6G
#SBATCH --output=/work1/ruixiangtang/rw761/data_mix_artifacts/slurm/onedial-q1-%A_%a.out
#SBATCH --error=/work1/ruixiangtang/rw761/data_mix_artifacts/slurm/onedial-q1-%A_%a.err

set -euo pipefail

cd /work1/ruixiangtang/rw761/awesome-pretraining/data_mix
export OPENBLAS_NUM_THREADS=2
export OMP_NUM_THREADS=2
: "${ONEDIAL_PHASE:?ONEDIAL_PHASE is required}"
: "${ONEDIAL_PIPELINES:?ONEDIAL_PIPELINES is required}"
: "${ONEDIAL_OUTPUT_ROOT:?ONEDIAL_OUTPUT_ROOT is required}"

/work1/ruixiangtang/rw761/data_mix_venv/bin/python scripts/run_onedial_q1.py dispatch \
  --protocol protocol_onedial.json \
  --data /work1/ruixiangtang/rw761/data_mix_public/olmix_rq2 \
  --phase "$ONEDIAL_PHASE" \
  --pipelines "$ONEDIAL_PIPELINES" \
  --task-id "$SLURM_ARRAY_TASK_ID" \
  --shard-size "${ONEDIAL_SHARD_SIZE:-20}" \
  --permutation-batch-size "${ONEDIAL_PERMUTATION_BATCH_SIZE:-128}" \
  --output-root "$ONEDIAL_OUTPUT_ROOT"
