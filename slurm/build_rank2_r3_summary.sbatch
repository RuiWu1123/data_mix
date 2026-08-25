#!/usr/bin/env bash
#SBATCH --job-name=twodial-r3-summary
#SBATCH --partition=devel
#SBATCH --time=00:30:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --output=/work1/ruixiangtang/rw761/data_mix_artifacts/slurm/twodial-r3-summary-%j.out
#SBATCH --error=/work1/ruixiangtang/rw761/data_mix_artifacts/slurm/twodial-r3-summary-%j.err

set -euo pipefail
cd /work1/ruixiangtang/rw761/awesome-pretraining/data_mix
/work1/ruixiangtang/rw761/data_mix_venv/bin/python scripts/build_rank2_r3_summary.py \
  --r1 artifacts/rank2_r1_result.json \
  --r2 artifacts/rank2_r2_result.json \
  --r2-check artifacts/rank2_r2_check.json \
  --csv artifacts/rank2_r2_jobs.csv \
  --output artifacts/rank2_r3_summary.json
