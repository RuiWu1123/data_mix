#!/usr/bin/env bash
#SBATCH --job-name=mix-h002
#SBATCH --partition=devel
#SBATCH --time=00:30:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --output=/work1/ruixiangtang/rw761/data_mix_artifacts/slurm/h002-%j.out
#SBATCH --error=/work1/ruixiangtang/rw761/data_mix_artifacts/slurm/h002-%j.err

set -euo pipefail

cd /work1/ruixiangtang/rw761/awesome-pretraining/data_mix
export OPENBLAS_NUM_THREADS=2
export OMP_NUM_THREADS=2
/work1/ruixiangtang/rw761/data_mix_venv/bin/python scripts/test_h002.py \
  --data vendor/ml_scalefit/data/dmsl_llm_slimpajama.csv \
  --output /work1/ruixiangtang/rw761/data_mix_artifacts/H002/result.json
