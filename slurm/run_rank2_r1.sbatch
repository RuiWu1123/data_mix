#!/usr/bin/env bash
#SBATCH --job-name=twodial-r1
#SBATCH --partition=devel
#SBATCH --time=00:30:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --output=/work1/ruixiangtang/rw761/data_mix_artifacts/slurm/twodial-r1-%j.out
#SBATCH --error=/work1/ruixiangtang/rw761/data_mix_artifacts/slurm/twodial-r1-%j.err

set -euo pipefail
cd /work1/ruixiangtang/rw761/awesome-pretraining/data_mix
export OPENBLAS_NUM_THREADS=16
export OMP_NUM_THREADS=16
/work1/ruixiangtang/rw761/data_mix_venv/bin/python scripts/run_rank2_r1.py \
  --protocol rank2_protocol.json \
  --olmix /work1/ruixiangtang/rw761/data_mix_public/olmix_rq2 \
  --regmix vendor/regmix/data \
  --datadecide vendor/datadecide/perplexity_metrics_by_group.csv \
  --output artifacts/rank2_r1_result.json \
  --arms-output artifacts/rank2_r2_arms.json \
  --plot artifacts/rank2_r1_curve.png
