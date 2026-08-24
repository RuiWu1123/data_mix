#!/usr/bin/env bash
#SBATCH --job-name=extract-review-priors
#SBATCH --partition=devel
#SBATCH --time=00:15:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --output=/work1/ruixiangtang/rw761/data_mix_artifacts/slurm/extract-review-priors-%j.out
#SBATCH --error=/work1/ruixiangtang/rw761/data_mix_artifacts/slurm/extract-review-priors-%j.err

set -euo pipefail
cd /work1/ruixiangtang/rw761/awesome-pretraining/data_mix
python scripts/extract_pdf_text.py \
  references/vector_dimension_reduction_1801.07922.pdf \
  references/shared_active_subspace_2401.02735.pdf \
  references/sequential_active_subspaces_1907.11572.pdf \
  --output-dir /work1/ruixiangtang/rw761/data_mix_artifacts/paper_text
python scripts/reference_inventory.py \
  --references references \
  --vendor vendor \
  --output artifacts/reference_inventory.json
