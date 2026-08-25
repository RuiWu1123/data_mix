#!/usr/bin/env bash
#SBATCH --job-name=twodial-r2-check
#SBATCH --partition=devel
#SBATCH --time=00:30:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --output=/work1/ruixiangtang/rw761/data_mix_artifacts/slurm/twodial-r2-check-%j.out
#SBATCH --error=/work1/ruixiangtang/rw761/data_mix_artifacts/slurm/twodial-r2-check-%j.err

set -euo pipefail
cd /work1/ruixiangtang/rw761/awesome-pretraining/data_mix
/work1/ruixiangtang/rw761/rank2_rocm_venv/bin/python scripts/check_rank2_r2_infra.py \
  --protocol rank2_protocol.json \
  --arms artifacts/rank2_r2_arms.json \
  --manifest artifacts/rank2_r2_config_manifest.json \
  --packed-audit artifacts/rank2_packed_data_audit.json \
  --regmix-worktree /work1/ruixiangtang/rw761/rank2_regmix_rocm \
  --result-root /work1/ruixiangtang/rw761/data_mix_artifacts/TWODIAL/R2 \
  --output artifacts/rank2_r2_infra_check.json
