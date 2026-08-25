#!/usr/bin/env bash
#SBATCH --job-name=onedial-final
#SBATCH --partition=devel
#SBATCH --time=00:05:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --output=/work1/ruixiangtang/rw761/data_mix_artifacts/slurm/onedial-final-%j.out
#SBATCH --error=/work1/ruixiangtang/rw761/data_mix_artifacts/slurm/onedial-final-%j.err

set -euo pipefail

cd /work1/ruixiangtang/rw761/awesome-pretraining/data_mix
/work1/ruixiangtang/rw761/data_mix_venv/bin/python scripts/check_onedial_final.py \
  --root /work1/ruixiangtang/rw761/awesome-pretraining/data_mix \
  --q1-audit /work1/ruixiangtang/rw761/data_mix_artifacts/ONEDIAL/Q1/design_audit.json \
  --dependencies /work1/ruixiangtang/rw761/data_mix_artifacts/ONEDIAL/dependency_resolution.json \
  --output /work1/ruixiangtang/rw761/data_mix_artifacts/ONEDIAL/final_check.json
