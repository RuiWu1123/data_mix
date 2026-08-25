#!/usr/bin/env bash
#SBATCH --job-name=onedial-q1-audit
#SBATCH --partition=devel
#SBATCH --time=00:05:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --output=/work1/ruixiangtang/rw761/data_mix_artifacts/slurm/onedial-q1-audit-%j.out
#SBATCH --error=/work1/ruixiangtang/rw761/data_mix_artifacts/slurm/onedial-q1-audit-%j.err

set -euo pipefail

cd /work1/ruixiangtang/rw761/awesome-pretraining/data_mix
export OPENBLAS_NUM_THREADS=1
export OMP_NUM_THREADS=1
/work1/ruixiangtang/rw761/data_mix_venv/bin/python scripts/audit_onedial_q1_design.py \
  --data /work1/ruixiangtang/rw761/data_mix_public/olmix_rq2 \
  --protocol protocol_onedial.json \
  --output /work1/ruixiangtang/rw761/data_mix_artifacts/ONEDIAL/Q1/design_audit.json
