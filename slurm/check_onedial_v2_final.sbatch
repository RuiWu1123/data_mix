#!/usr/bin/env bash
#SBATCH --job-name=onedial-v2-final
#SBATCH --partition=devel
#SBATCH --time=00:05:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --output=/work1/ruixiangtang/rw761/data_mix_artifacts/slurm/onedial-v2-final-%j.out
#SBATCH --error=/work1/ruixiangtang/rw761/data_mix_artifacts/slurm/onedial-v2-final-%j.err

set -euo pipefail

cd /work1/ruixiangtang/rw761/awesome-pretraining/data_mix
/work1/ruixiangtang/rw761/data_mix_venv/bin/python scripts/check_onedial_v2_final.py \
  --root /work1/ruixiangtang/rw761/awesome-pretraining/data_mix \
  --q1-audit /work1/ruixiangtang/rw761/data_mix_artifacts/ONEDIAL_V2/Q1/holm_resolution_audit.json \
  --dependencies /work1/ruixiangtang/rw761/data_mix_artifacts/ONEDIAL_V2/dependency_resolution.json \
  --amendment-check /work1/ruixiangtang/rw761/awesome-pretraining/data_mix/artifacts/onedial_v2_amendment_check.json \
  --output /work1/ruixiangtang/rw761/data_mix_artifacts/ONEDIAL_V2/final_check.json
