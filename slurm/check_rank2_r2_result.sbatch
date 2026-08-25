#!/usr/bin/env bash
#SBATCH --job-name=twodial-r2-result-check
#SBATCH --partition=devel
#SBATCH --time=00:30:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --output=/work1/ruixiangtang/rw761/data_mix_artifacts/slurm/twodial-r2-result-check-%j.out
#SBATCH --error=/work1/ruixiangtang/rw761/data_mix_artifacts/slurm/twodial-r2-result-check-%j.err

set -euo pipefail
cd /work1/ruixiangtang/rw761/awesome-pretraining/data_mix
/work1/ruixiangtang/rw761/data_mix_venv/bin/python scripts/check_rank2_r2_result.py \
  --protocol rank2_protocol.json \
  --arms artifacts/rank2_r2_arms.json \
  --result artifacts/rank2_r2_result.json \
  --csv artifacts/rank2_r2_jobs.csv \
  --output artifacts/rank2_r2_check.json
