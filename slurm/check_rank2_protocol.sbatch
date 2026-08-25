#!/usr/bin/env bash
#SBATCH --job-name=twodial-protocol
#SBATCH --partition=devel
#SBATCH --time=00:30:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --output=/work1/ruixiangtang/rw761/data_mix_artifacts/slurm/twodial-protocol-%j.out
#SBATCH --error=/work1/ruixiangtang/rw761/data_mix_artifacts/slurm/twodial-protocol-%j.err

set -euo pipefail
cd /work1/ruixiangtang/rw761/awesome-pretraining/data_mix
/work1/ruixiangtang/rw761/data_mix_venv/bin/python scripts/check_rank2_protocol.py \
  --protocol rank2_protocol.json \
  --markdown RANK2_PROTOCOL.md \
  --output artifacts/rank2_protocol_check.json
