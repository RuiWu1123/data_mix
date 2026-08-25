#!/usr/bin/env bash
#SBATCH --job-name=onedial-q1-check
#SBATCH --partition=devel
#SBATCH --time=00:30:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --output=/work1/ruixiangtang/rw761/data_mix_artifacts/slurm/onedial-q1-check-%j.out
#SBATCH --error=/work1/ruixiangtang/rw761/data_mix_artifacts/slurm/onedial-q1-check-%j.err

set -euo pipefail

cd /work1/ruixiangtang/rw761/awesome-pretraining/data_mix
/work1/ruixiangtang/rw761/data_mix_venv/bin/python scripts/check_onedial_q1_result.py \
  --protocol protocol_onedial.json \
  --shards /work1/ruixiangtang/rw761/data_mix_artifacts/ONEDIAL_V3/Q1/discovery/shards \
  --result /work1/ruixiangtang/rw761/data_mix_artifacts/ONEDIAL_V3/Q1/discovery/result.json \
  --confirmation-root /work1/ruixiangtang/rw761/data_mix_artifacts/ONEDIAL_V3/Q1/confirmation \
  --output artifacts/onedial_v3_q1_result_check.json
