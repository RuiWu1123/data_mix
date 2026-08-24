#!/usr/bin/env bash
#SBATCH --job-name=mix-h009-artifacts
#SBATCH --partition=devel
#SBATCH --time=00:10:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --output=/work1/ruixiangtang/rw761/data_mix_artifacts/slurm/h009-artifacts-%j.out
#SBATCH --error=/work1/ruixiangtang/rw761/data_mix_artifacts/slurm/h009-artifacts-%j.err

set -euo pipefail

cd /work1/ruixiangtang/rw761/awesome-pretraining/data_mix
/work1/ruixiangtang/rw761/data_mix_venv/bin/python scripts/audit_h009_artifacts.py \
  --data /work1/ruixiangtang/rw761/data_mix_public/olmix_rq2 \
  --paper-text /work1/ruixiangtang/rw761/data_mix_artifacts/paper_text/olmix_2602.12237.txt \
  --output /work1/ruixiangtang/rw761/data_mix_artifacts/H009/availability.json
