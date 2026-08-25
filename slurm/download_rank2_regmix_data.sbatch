#!/usr/bin/env bash
#SBATCH --job-name=twodial-data
#SBATCH --partition=mi2101x
#SBATCH --time=04:00:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --output=/work1/ruixiangtang/rw761/data_mix_artifacts/slurm/twodial-data-%j.out
#SBATCH --error=/work1/ruixiangtang/rw761/data_mix_artifacts/slurm/twodial-data-%j.err

set -euo pipefail
readonly VENV=/work1/ruixiangtang/rw761/rank2_rocm_venv
readonly DEST=/work1/ruixiangtang/rw761/rank2_regmix_raw
export HF_HOME=/work1/ruixiangtang/rw761/hf-cache
export HF_HUB_DISABLE_XET=1

"${VENV}/bin/python" - <<'PY'
from huggingface_hub import snapshot_download

print(snapshot_download(
    repo_id="sail/regmix-data-sample",
    repo_type="dataset",
    revision="b5b301999278f59beccb75b55c81e6e551165327",
    local_dir="/work1/ruixiangtang/rw761/rank2_regmix_raw",
    max_workers=8,
))
PY
