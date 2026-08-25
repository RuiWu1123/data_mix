#!/usr/bin/env bash
#SBATCH --job-name=twodial-pack
#SBATCH --partition=mi2101x
#SBATCH --time=12:00:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --output=/work1/ruixiangtang/rw761/data_mix_artifacts/slurm/twodial-pack-%j.out
#SBATCH --error=/work1/ruixiangtang/rw761/data_mix_artifacts/slurm/twodial-pack-%j.err

set -euo pipefail
readonly REPO=/work1/ruixiangtang/rw761/awesome-pretraining/data_mix
readonly VENV=/work1/ruixiangtang/rw761/rank2_rocm_venv
readonly RAW=/work1/ruixiangtang/rw761/rank2_regmix_raw
readonly PACKED=/work1/ruixiangtang/rw761/rank2_regmix_packed
readonly REGMIX=/work1/ruixiangtang/rw761/rank2_regmix_rocm

if [[ ! -d "${REGMIX}/.git" ]]; then
  cp -a "${REPO}/vendor/regmix" "${REGMIX}"
fi
if git -C "${REGMIX}" apply --check "${REPO}/patches/regmix_rocm.patch"; then
  git -C "${REGMIX}" apply --whitespace=nowarn "${REPO}/patches/regmix_rocm.patch"
elif ! git -C "${REGMIX}" apply --check --reverse "${REPO}/patches/regmix_rocm.patch"; then
  echo "RegMix work copy is neither pristine nor exactly patched" >&2
  exit 1
fi
test "$(git -C "${REGMIX}" rev-parse HEAD)" = "dd9d1c3b2d7c1756b1a90f0ad7603068e9856cc6"

cd "${REGMIX}/model_training/preprocess"
"${VENV}/bin/python" prepare_file_domain.py \
  --source_path "${RAW}" \
  --tokenizer_path tokenizer/gptneox \
  --destination_path "${PACKED}" \
  --short_name the_pile \
  --split train \
  --chunk_size 524544
"${VENV}/bin/python" prepare_file_domain.py \
  --source_path "${RAW}" \
  --tokenizer_path tokenizer/gptneox \
  --destination_path "${PACKED}" \
  --short_name the_pile \
  --split valid \
  --chunk_size 131136

cd "${REPO}"
"${VENV}/bin/python" scripts/audit_rank2_packed_data.py \
  --arms artifacts/rank2_r2_arms.json \
  --packed "${PACKED}" \
  --output artifacts/rank2_packed_data_audit.json
