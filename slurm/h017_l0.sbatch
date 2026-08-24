#!/usr/bin/env bash
#SBATCH --job-name=mix-h017
#SBATCH --partition=devel
#SBATCH --time=00:30:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --output=/work1/ruixiangtang/rw761/data_mix_artifacts/slurm/h017-%j.out
#SBATCH --error=/work1/ruixiangtang/rw761/data_mix_artifacts/slurm/h017-%j.err

set -euo pipefail

cd /work1/ruixiangtang/rw761/awesome-pretraining/data_mix
export OPENBLAS_NUM_THREADS=2
export OMP_NUM_THREADS=2
/work1/ruixiangtang/rw761/data_mix_venv/bin/python scripts/test_h017.py \
  --data /work1/ruixiangtang/rw761/data_mix_public/olmix_rq2 \
  --output /work1/ruixiangtang/rw761/data_mix_artifacts/H017/result.json
