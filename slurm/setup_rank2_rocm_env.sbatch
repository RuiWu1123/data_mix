#!/usr/bin/env bash
#SBATCH --job-name=twodial-env
#SBATCH --partition=devel
#SBATCH --time=00:30:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --output=/work1/ruixiangtang/rw761/data_mix_artifacts/slurm/twodial-env-%j.out
#SBATCH --error=/work1/ruixiangtang/rw761/data_mix_artifacts/slurm/twodial-env-%j.err

set -euo pipefail
readonly VENV=/work1/ruixiangtang/rw761/rank2_rocm_venv
readonly REPO=/work1/ruixiangtang/rw761/awesome-pretraining/data_mix

if [[ ! -x "${VENV}/bin/python" ]]; then
  /usr/bin/python3.9 -m venv "${VENV}"
fi
"${VENV}/bin/python" -m pip install --upgrade pip
"${VENV}/bin/python" -m pip install -r "${REPO}/requirements_rank2_rocm.txt"
"${VENV}/bin/python" - <<'PY'
import json
from pathlib import Path

import torch

payload = {
    "python": __import__("sys").version,
    "torch": torch.__version__,
    "torch_hip": torch.version.hip,
    "torch_cuda_available_on_loginless_cpu_job": torch.cuda.is_available(),
}
path = Path("/work1/ruixiangtang/rw761/data_mix_artifacts/rank2_rocm_env.json")
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(payload, sort_keys=True))
PY
