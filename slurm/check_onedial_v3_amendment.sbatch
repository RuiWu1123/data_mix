#!/usr/bin/env bash
#SBATCH --job-name=onedial-v3-amend
#SBATCH --partition=devel
#SBATCH --time=00:05:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --output=/work1/ruixiangtang/rw761/data_mix_artifacts/slurm/onedial-v3-amend-%j.out
#SBATCH --error=/work1/ruixiangtang/rw761/data_mix_artifacts/slurm/onedial-v3-amend-%j.err

set -euo pipefail

cd /work1/ruixiangtang/rw761/awesome-pretraining/data_mix
/work1/ruixiangtang/rw761/data_mix_venv/bin/python scripts/check_onedial_v3_amendment.py \
  --root /work1/ruixiangtang/rw761/awesome-pretraining/data_mix \
  --base-ref 53055b8 \
  --output artifacts/onedial_v3_amendment_check.json \
  --diff-output artifacts/onedial_v2_to_v3.diff
