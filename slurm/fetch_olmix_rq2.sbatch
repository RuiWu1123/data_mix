#!/usr/bin/env bash
#SBATCH --job-name=fetch-olmix-rq2
#SBATCH --partition=devel
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=1G
#SBATCH --time=00:15:00
#SBATCH --output=/work1/ruixiangtang/rw761/data_mix_artifacts/slurm/fetch-olmix-rq2-%j.out

set -euo pipefail
bash scripts/fetch_olmix_rq2.sh
