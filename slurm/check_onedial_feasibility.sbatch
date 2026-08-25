#!/usr/bin/env bash
#SBATCH --job-name=onedial-feasible
#SBATCH --partition=devel
#SBATCH --time=00:05:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --output=/work1/ruixiangtang/rw761/data_mix_artifacts/slurm/onedial-feasible-%j.out
#SBATCH --error=/work1/ruixiangtang/rw761/data_mix_artifacts/slurm/onedial-feasible-%j.err

set -euo pipefail

cd /work1/ruixiangtang/rw761/awesome-pretraining/data_mix
/work1/ruixiangtang/rw761/data_mix_venv/bin/python scripts/check_onedial_feasibility.py \
  --protocol protocol_onedial.json \
  --olmix-data /work1/ruixiangtang/rw761/data_mix_public/olmix_rq2 \
  --output artifacts/onedial_v3_feasibility_check.json
