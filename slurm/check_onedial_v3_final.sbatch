#!/usr/bin/env bash
#SBATCH --job-name=onedial-v3-final
#SBATCH --partition=devel
#SBATCH --time=00:30:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --output=/work1/ruixiangtang/rw761/data_mix_artifacts/slurm/onedial-v3-final-%j.out
#SBATCH --error=/work1/ruixiangtang/rw761/data_mix_artifacts/slurm/onedial-v3-final-%j.err

set -euo pipefail

cd /work1/ruixiangtang/rw761/awesome-pretraining/data_mix
/work1/ruixiangtang/rw761/data_mix_venv/bin/python scripts/check_onedial_v3_final.py \
  --root . \
  --q1-result /work1/ruixiangtang/rw761/data_mix_artifacts/ONEDIAL_V3/Q1/discovery/result.json \
  --q1-check artifacts/onedial_v3_q1_result_check.json \
  --dependencies /work1/ruixiangtang/rw761/data_mix_artifacts/ONEDIAL_V3/dependency_resolution.json \
  --confirmation-root /work1/ruixiangtang/rw761/data_mix_artifacts/ONEDIAL_V3/Q1/confirmation \
  --output /work1/ruixiangtang/rw761/data_mix_artifacts/ONEDIAL_V3/final_check.json
