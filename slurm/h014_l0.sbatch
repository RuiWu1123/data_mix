#!/usr/bin/env bash
#SBATCH --job-name=mix-h014
#SBATCH --partition=devel
#SBATCH --time=00:10:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --output=/work1/ruixiangtang/rw761/data_mix_artifacts/slurm/h014-%j.out
#SBATCH --error=/work1/ruixiangtang/rw761/data_mix_artifacts/slurm/h014-%j.err

set -euo pipefail

cd /work1/ruixiangtang/rw761/awesome-pretraining/data_mix
/work1/ruixiangtang/rw761/data_mix_venv/bin/python scripts/test_h014.py \
  --regmix-repo vendor/regmix \
  --dmsl-repo vendor/explaining_dmsl \
  --olmix-data /work1/ruixiangtang/rw761/data_mix_public/olmix_rq2 \
  --output /work1/ruixiangtang/rw761/data_mix_artifacts/H014/result.json
