#!/usr/bin/env bash
#SBATCH --job-name=twodial-r1-check
#SBATCH --partition=devel
#SBATCH --time=00:30:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --output=/work1/ruixiangtang/rw761/data_mix_artifacts/slurm/twodial-r1-check-%j.out
#SBATCH --error=/work1/ruixiangtang/rw761/data_mix_artifacts/slurm/twodial-r1-check-%j.err

set -euo pipefail
cd /work1/ruixiangtang/rw761/awesome-pretraining/data_mix
/work1/ruixiangtang/rw761/data_mix_venv/bin/python scripts/check_rank2_r1.py \
  --protocol rank2_protocol.json \
  --result artifacts/rank2_r1_result.json \
  --arms artifacts/rank2_r2_arms.json \
  --datadecide vendor/datadecide/perplexity_metrics_by_group.csv \
  --regmix vendor/regmix/data \
  --output artifacts/rank2_r1_check.json
