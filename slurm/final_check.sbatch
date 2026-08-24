#!/usr/bin/env bash
#SBATCH --job-name=mix-final-check
#SBATCH --partition=devel
#SBATCH --time=00:10:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --output=/work1/ruixiangtang/rw761/data_mix_artifacts/slurm/final-check-%j.out
#SBATCH --error=/work1/ruixiangtang/rw761/data_mix_artifacts/slurm/final-check-%j.err

set -euo pipefail
cd /work1/ruixiangtang/rw761/awesome-pretraining/data_mix
/work1/ruixiangtang/rw761/data_mix_venv/bin/python scripts/check_final.py \
  --root /work1/ruixiangtang/rw761/awesome-pretraining/data_mix \
  --summary /work1/ruixiangtang/rw761/awesome-pretraining/data_mix/artifacts/final_summary.json \
  --output /work1/ruixiangtang/rw761/awesome-pretraining/data_mix/artifacts/final_check.json
