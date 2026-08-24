#!/usr/bin/env python3
"""Preflight the frozen ActiveSubspaceMix retrospective intervention."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


EVALUATION_FRACTION = 0.20
SWARM_SEEDS = 1_000


def evaluation_member(dataset: str, row_id: str) -> bool:
    digest = hashlib.sha256(f"H014:evaluation:{dataset}:{row_id}".encode("utf-8")).digest()
    value = int.from_bytes(digest[:8], "big") / 2**64
    return value < EVALUATION_FRACTION


def audit_table(dataset: str, frame: pd.DataFrame, weight_cols: list[str], id_col: str) -> dict[str, object]:
    numeric = frame[weight_cols].apply(pd.to_numeric, errors="coerce").to_numpy(float)
    finite = np.all(np.isfinite(numeric), axis=1)
    numeric = numeric[finite]
    row_ids = frame.loc[finite, id_col].astype(str).tolist()
    evaluation = np.array([evaluation_member(dataset, row_id) for row_id in row_ids], dtype=bool)
    train = ~evaluation
    rounded = np.round(numeric, decimals=12)
    unique_all = len(np.unique(rounded, axis=0))
    unique_train = len(np.unique(rounded[train], axis=0))
    domains = len(weight_cols)
    budgets = [2 * domains, 3 * domains, 4 * domains]
    pilot_rows = budgets[0] // 2
    affine_parameters = domains
    return {
        "dataset": dataset,
        "domains_K": domains,
        "rows": len(numeric),
        "unique_coordinate_rows": unique_all,
        "evaluation_rows": int(evaluation.sum()),
        "training_rows": int(train.sum()),
        "unique_training_coordinate_rows": unique_train,
        "budgets": budgets,
        "max_budget_4K": budgets[-1],
        "max_budget_available": unique_train >= budgets[-1],
        "B_2K_pilot_rows": pilot_rows,
        "ilr_affine_parameters_including_intercept": affine_parameters,
        "pilot_residual_degrees_of_freedom": pilot_rows - affine_parameters,
        "pilot_has_positive_residual_dof": pilot_rows - affine_parameters > 0,
        "duplicate_fraction": 1.0 - unique_all / max(len(numeric), 1),
    }


def load_regmix(repo: Path) -> list[dict[str, object]]:
    outputs = []
    for scale in ("1m", "60m", "1B"):
        frame = pd.read_csv(repo / f"data/test_mixture_{scale}.csv")
        weights = [column for column in frame if column.startswith("train_the_pile_")]
        outputs.append(audit_table(f"RegMix-{scale}", frame, weights, "index"))
    return outputs


def load_dmsl(repo: Path) -> tuple[list[dict[str, object]], dict[str, object]]:
    frame = pd.read_csv(repo / "data/dmsl_llm_slimpajama.csv")
    weights = [column for column in frame if column.startswith("weight_")]
    model_sizes = sorted(frame["model_size"].dropna().unique())
    split_at = len(model_sizes) // 2
    lower = set(model_sizes[:split_at])
    outputs = []
    for (model_size, n_tokens), block in frame.groupby(["model_size", "n_tokens"], sort=True):
        block = block.reset_index().rename(columns={"index": "row_id"})
        split = "discovery" if model_size in lower else "confirmation"
        label = f"DMSL-{split}-N{model_size:g}-D{n_tokens:g}"
        outputs.append(audit_table(label, block, weights, "row_id"))
    return outputs, {
        "lower_model_sizes": [float(value) for value in model_sizes[:split_at]],
        "upper_model_sizes": [float(value) for value in model_sizes[split_at:]],
    }


def load_olmix(data: Path) -> dict[str, object]:
    frame = pd.read_csv(data / "m24_ratios.csv")
    skip = {"run", "name", "index", "Unnamed: 0"}
    weights = [column for column in frame if column not in skip]
    id_col = "run" if "run" in frame else "index"
    return audit_table("Olmix-m24", frame, weights, id_col)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--regmix-repo", type=Path, required=True)
    parser.add_argument("--dmsl-repo", type=Path, required=True)
    parser.add_argument("--olmix-data", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    regmix = load_regmix(args.regmix_repo)
    dmsl, dmsl_split = load_dmsl(args.dmsl_repo)
    olmix = load_olmix(args.olmix_data)
    tables = regmix + dmsl + [olmix]
    insufficient = [item["dataset"] for item in tables if not item["max_budget_available"]]
    saturated = [item["dataset"] for item in tables if not item["pilot_has_positive_residual_dof"]]
    valid = not insufficient and not saturated
    result = {
        "id": "H014",
        "verdict": "inconclusive",
        "evaluation_fraction": EVALUATION_FRACTION,
        "requested_swarm_seed_count": SWARM_SEEDS,
        "performance_trials_executed": 0,
        "validity": {
            "all_4K_budgets_available": not insufficient,
            "all_B_2K_pilots_have_positive_residual_dof": not saturated,
            "insufficient_public_tables": insufficient,
            "saturated_pilot_tables": saturated,
            "decision": (
                "run frozen regret benchmark" if valid else "stop before labels: retrospective support is unidentified"
            ),
        },
        "tables": tables,
        "dmsl_split": dmsl_split,
        "inputs": [str(args.regmix_repo), str(args.dmsl_repo), str(args.olmix_data)],
        "command": (
            f"python scripts/test_h014.py --regmix-repo {args.regmix_repo} "
            f"--dmsl-repo {args.dmsl_repo} --olmix-data {args.olmix_data} --output {args.output}"
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
