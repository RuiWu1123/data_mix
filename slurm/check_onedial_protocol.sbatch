#!/usr/bin/env bash
#SBATCH --job-name=onedial-protocol-check
#SBATCH --partition=devel
#SBATCH --time=00:10:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --output=/work1/ruixiangtang/rw761/data_mix_artifacts/slurm/onedial-protocol-check-%j.out
#SBATCH --error=/work1/ruixiangtang/rw761/data_mix_artifacts/slurm/onedial-protocol-check-%j.err

set -euo pipefail
cd /work1/ruixiangtang/rw761/awesome-pretraining/data_mix
/work1/ruixiangtang/rw761/data_mix_venv/bin/python scripts/check_onedial_protocol.py \
  --root /work1/ruixiangtang/rw761/awesome-pretraining/data_mix \
  --protocol /work1/ruixiangtang/rw761/awesome-pretraining/data_mix/protocol_onedial.json \
  --markdown /work1/ruixiangtang/rw761/awesome-pretraining/data_mix/PROTOCOL_ONEDIAL.md \
  --ledger /work1/ruixiangtang/rw761/awesome-pretraining/data_mix/EXPERIMENTS.md \
  --output /work1/ruixiangtang/rw761/awesome-pretraining/data_mix/artifacts/onedial_protocol_check.json
