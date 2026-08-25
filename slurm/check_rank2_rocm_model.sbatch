#!/usr/bin/env bash
#SBATCH --job-name=twodial-rocm-check
#SBATCH --partition=mi2101x
#SBATCH --time=00:10:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --output=/work1/ruixiangtang/rw761/data_mix_artifacts/slurm/twodial-rocm-check-%j.out
#SBATCH --error=/work1/ruixiangtang/rw761/data_mix_artifacts/slurm/twodial-rocm-check-%j.err

set -euo pipefail
module purge
cd /work1/ruixiangtang/rw761/awesome-pretraining/data_mix
PYTHONPATH=/work1/ruixiangtang/rw761/rank2_regmix_rocm/model_training \
  /work1/ruixiangtang/rw761/rank2_rocm_venv/bin/python scripts/check_rank2_rocm_model.py \
  --patch patches/regmix_rocm.patch \
  --output artifacts/rank2_rocm_model_check.json
