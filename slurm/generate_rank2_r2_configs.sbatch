#!/usr/bin/env bash
#SBATCH --job-name=twodial-configs
#SBATCH --partition=devel
#SBATCH --time=00:30:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --output=/work1/ruixiangtang/rw761/data_mix_artifacts/slurm/twodial-configs-%j.out
#SBATCH --error=/work1/ruixiangtang/rw761/data_mix_artifacts/slurm/twodial-configs-%j.err

set -euo pipefail
cd /work1/ruixiangtang/rw761/awesome-pretraining/data_mix
/work1/ruixiangtang/rw761/data_mix_venv/bin/python scripts/generate_rank2_r2_configs.py \
  --protocol rank2_protocol.json \
  --arms artifacts/rank2_r2_arms.json \
  --output-dir configs/rank2_r2 \
  --manifest artifacts/rank2_r2_config_manifest.json
