#!/usr/bin/env bash
#SBATCH --job-name=mix-h007
#SBATCH --partition=devel
#SBATCH --time=00:10:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --output=/work1/ruixiangtang/rw761/data_mix_artifacts/slurm/h007-%j.out
#SBATCH --error=/work1/ruixiangtang/rw761/data_mix_artifacts/slurm/h007-%j.err

set -euo pipefail

cd /work1/ruixiangtang/rw761/awesome-pretraining/data_mix
/work1/ruixiangtang/rw761/data_mix_venv/bin/python scripts/test_h007.py \
  --repo vendor/explaining_dmsl \
  --paper-text /work1/ruixiangtang/rw761/data_mix_artifacts/paper_text/explaining_dmsl_2606.08167.txt \
  --output /work1/ruixiangtang/rw761/data_mix_artifacts/H007/result.json
