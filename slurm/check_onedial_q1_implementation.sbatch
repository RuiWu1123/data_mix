#!/usr/bin/env bash
#SBATCH --job-name=onedial-q1-impl
#SBATCH --partition=devel
#SBATCH --time=00:30:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=1G
#SBATCH --output=/work1/ruixiangtang/rw761/data_mix_artifacts/slurm/onedial-q1-impl-%j.out
#SBATCH --error=/work1/ruixiangtang/rw761/data_mix_artifacts/slurm/onedial-q1-impl-%j.err

set -euo pipefail

cd /work1/ruixiangtang/rw761/awesome-pretraining/data_mix
/work1/ruixiangtang/rw761/data_mix_venv/bin/python scripts/check_onedial_q1_implementation.py \
  --protocol protocol_onedial.json \
  --output artifacts/onedial_v3_q1_implementation_check.json
