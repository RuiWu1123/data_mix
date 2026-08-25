#!/usr/bin/env bash
#SBATCH --job-name=onedial-deps
#SBATCH --partition=devel
#SBATCH --time=00:05:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --output=/work1/ruixiangtang/rw761/data_mix_artifacts/slurm/onedial-deps-%j.out
#SBATCH --error=/work1/ruixiangtang/rw761/data_mix_artifacts/slurm/onedial-deps-%j.err

set -euo pipefail

cd /work1/ruixiangtang/rw761/awesome-pretraining/data_mix
/work1/ruixiangtang/rw761/data_mix_venv/bin/python scripts/resolve_onedial_dependencies.py \
  --protocol protocol_onedial.json \
  --q1-audit /work1/ruixiangtang/rw761/data_mix_artifacts/ONEDIAL/Q1/design_audit.json \
  --output /work1/ruixiangtang/rw761/data_mix_artifacts/ONEDIAL/dependency_resolution.json
