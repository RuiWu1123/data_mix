#!/usr/bin/env bash
#SBATCH --job-name=twodial-final-check
#SBATCH --partition=devel
#SBATCH --time=00:30:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --output=/work1/ruixiangtang/rw761/data_mix_artifacts/slurm/twodial-final-check-%j.out
#SBATCH --error=/work1/ruixiangtang/rw761/data_mix_artifacts/slurm/twodial-final-check-%j.err

set -euo pipefail
cd /work1/ruixiangtang/rw761/awesome-pretraining/data_mix
/work1/ruixiangtang/rw761/data_mix_venv/bin/python scripts/check_rank2_final.py \
  --protocol rank2_protocol.json \
  --r1 artifacts/rank2_r1_result.json \
  --r1-check artifacts/rank2_r1_check.json \
  --r2 artifacts/rank2_r2_result.json \
  --r2-check artifacts/rank2_r2_check.json \
  --ledger EXPERIMENTS.md \
  --result RESULT.md \
  --output artifacts/rank2_final_check.json
