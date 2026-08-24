#!/bin/bash
#SBATCH --job-name=mix-l0-env
#SBATCH --partition=devel
#SBATCH --time=00:30:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --output=/work1/ruixiangtang/rw761/data_mix_artifacts/slurm/setup_l0_env-%j.out
#SBATCH --error=/work1/ruixiangtang/rw761/data_mix_artifacts/slurm/setup_l0_env-%j.err

set -euo pipefail

ENV_DIR=/work1/ruixiangtang/rw761/data_mix_venv
python -m venv "$ENV_DIR"
"$ENV_DIR/bin/python" -m pip install --upgrade pip
"$ENV_DIR/bin/python" -m pip install numpy pandas scipy scikit-learn
"$ENV_DIR/bin/python" -c "import numpy, pandas, scipy, sklearn; print(numpy.__version__, pandas.__version__, scipy.__version__, sklearn.__version__)"
