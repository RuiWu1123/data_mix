#!/usr/bin/env bash
#SBATCH --job-name=twodial-r2
#SBATCH --time=04:00:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --output=/work1/ruixiangtang/rw761/data_mix_artifacts/slurm/twodial-r2-%A_%a.out
#SBATCH --error=/work1/ruixiangtang/rw761/data_mix_artifacts/slurm/twodial-r2-%A_%a.err

set -euo pipefail
readonly REPO=/work1/ruixiangtang/rw761/awesome-pretraining/data_mix
readonly VENV=/work1/ruixiangtang/rw761/rank2_rocm_venv
readonly REGMIX=/work1/ruixiangtang/rw761/rank2_regmix_rocm
readonly PACKED=/work1/ruixiangtang/rw761/rank2_regmix_packed
readonly RESULT_ROOT=/work1/ruixiangtang/rw761/data_mix_artifacts/TWODIAL/R2

module --ignore_cache load rocm/6.3.1
mapfile -t CONFIGS < <(find "${REPO}/configs/rank2_r2" -maxdepth 1 -type f -name '*.yaml' | sort)
if [[ "${#CONFIGS[@]}" -ne 12 ]]; then
  echo "expected 12 configs, found ${#CONFIGS[@]}" >&2
  exit 1
fi
readonly CONFIG="${CONFIGS[${SLURM_ARRAY_TASK_ID}]}"
readonly RUN_ID="$(basename "${CONFIG}" .yaml)"
mkdir -p "${RESULT_ROOT}/${RUN_ID}"

cd "${REGMIX}/model_training"
"${VENV}/bin/python" pretrain/tinyllama.py \
  --devices 1 \
  --train_data_dir "${PACKED}" \
  --val_data_dir "${PACKED}" \
  --data_yaml_file "${CONFIG}" \
  --precision bf16-mixed \
  --out_name "${RUN_ID}" \
  --resume false \
  --result_json "${RESULT_ROOT}/${RUN_ID}/result.json"
