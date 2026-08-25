#!/usr/bin/env bash
#SBATCH --job-name=twodial-r2-collect
#SBATCH --partition=devel
#SBATCH --time=00:30:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --output=/work1/ruixiangtang/rw761/data_mix_artifacts/slurm/twodial-r2-collect-%j.out
#SBATCH --error=/work1/ruixiangtang/rw761/data_mix_artifacts/slurm/twodial-r2-collect-%j.err

set -euo pipefail
cd /work1/ruixiangtang/rw761/awesome-pretraining/data_mix
: "${RANK2_JOB_IDS:?RANK2_JOB_IDS must list all R2 array job IDs}"
/work1/ruixiangtang/rw761/data_mix_venv/bin/python scripts/collect_rank2_r2.py \
  --protocol rank2_protocol.json \
  --arms artifacts/rank2_r2_arms.json \
  --manifest artifacts/rank2_r2_config_manifest.json \
  --result-root /work1/ruixiangtang/rw761/data_mix_artifacts/TWODIAL/R2 \
  --job-ids "${RANK2_JOB_IDS}" \
  --output artifacts/rank2_r2_result.json \
  --csv artifacts/rank2_r2_jobs.csv \
  --plot artifacts/rank2_r2_effects.png
