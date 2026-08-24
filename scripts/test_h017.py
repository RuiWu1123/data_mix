#!/usr/bin/env python3
"""Test whether rank two suffices for cross-fitted Olmix affine prediction."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.linalg import helmert


BOOTSTRAPS = 10_000
CV_REPEATS = 20
OUTER_FOLDS = 5
INNER_FOLDS = 4
HAAR_DRAWS = 64
DOMAIN_COUNTS = (6, 12, 18, 24)
ZERO_REPLACEMENT = 1e-6
CONDITION_LIMIT = 10_000.0
META = {"run", "name", "index", "Unnamed: 0"}


def seed(label: str) -> int:
    return int.from_bytes(hashlib.sha256(label.encode("utf-8")).digest()[:8], "little")


def load_tables(data: Path):
    loaded = {}
    common_metrics = None
    for domains in DOMAIN_COUNTS:
        ratios = pd.read_csv(data / f"m{domains}_ratios.csv")
        metrics = pd.read_csv(data / f"m{domains}_metrics.csv")
        metric_cols = {column for column in metrics if column not in META}
        common_metrics = metric_cols if common_metrics is None else common_metrics & metric_cols
        loaded[domains] = (ratios, metrics)
    finite_common = [
        column
        for column in sorted(common_metrics or set())
        if all(
            pd.to_numeric(loaded[domains][1][column], errors="coerce").notna().all()
            for domains in DOMAIN_COUNTS
        )
    ]
    return loaded, finite_common


def prepare(ratios: pd.DataFrame, metrics: pd.DataFrame, metric_cols: list[str]):
    id_col = "run" if "run" in ratios and "run" in metrics else "index"
    domain_cols = [column for column in ratios if column not in META]
    joined = ratios[[id_col] + domain_cols].merge(
        metrics[[id_col] + metric_cols], on=id_col, how="inner"
    )
    weights = joined[domain_cols].apply(pd.to_numeric, errors="coerce").to_numpy(float)
    responses = joined[metric_cols].apply(pd.to_numeric, errors="coerce").to_numpy(float)
    finite = np.all(np.isfinite(weights), axis=1) & np.all(np.isfinite(responses), axis=1)
    identifiers = joined.loc[finite, id_col].astype(str).to_numpy()
    weights = weights[finite]
    weights[weights <= 0] = ZERO_REPLACEMENT
    weights /= weights.sum(axis=1, keepdims=True)
    basis = helmert(weights.shape[1], full=False).T
    x = np.log(weights) @ basis
    return x, responses[finite], identifiers, domain_cols, id_col


def balanced_folds(identifiers: np.ndarray, label: str, folds: int) -> np.ndarray:
    keys = np.asarray(
        [hashlib.sha256(f"{label}:{identifier}".encode("utf-8")).digest() for identifier in identifiers],
        dtype="S32",
    )
    order = np.argsort(keys, kind="stable")
    assignments = np.empty(len(identifiers), dtype=int)
    assignments[order] = np.arange(len(identifiers)) % folds
    return assignments


def training_transform(x_train: np.ndarray, y_train: np.ndarray):
    x_mean = x_train.mean(axis=0)
    y_mean = y_train.mean(axis=0)
    y_scale = y_train.std(axis=0, ddof=1)
    if np.any(y_scale < 1e-8):
        raise ValueError("task training standard deviation below 1e-8")
    xc = x_train - x_mean
    yz = (y_train - y_mean) / y_scale
    singular = np.linalg.svd(xc, compute_uv=False)
    rank = int(np.linalg.matrix_rank(xc))
    condition = float(singular[0] / singular[-1]) if singular[-1] > 0 else float("inf")
    return xc, yz, x_mean, y_mean, y_scale, rank, condition


def reduced_rank_predict(
    x_train: np.ndarray,
    y_train: np.ndarray,
    x_validation: np.ndarray,
    rank: int,
):
    xc, yz, x_mean, y_mean, y_scale, design_rank, condition = training_transform(
        x_train, y_train
    )
    coefficient = np.linalg.lstsq(xc, yz, rcond=None)[0]
    fitted = xc @ coefficient
    u, singular, vh = np.linalg.svd(fitted, full_matrices=False)
    retained = min(rank, len(singular))
    fitted_rank = (u[:, :retained] * singular[:retained]) @ vh[:retained]
    rank_coefficient = np.linalg.lstsq(xc, fitted_rank, rcond=None)[0]
    predicted_z = (x_validation - x_mean) @ rank_coefficient
    predicted_raw = predicted_z * y_scale + y_mean
    return predicted_raw, {
        "condition": condition,
        "design_rank": design_rank,
        "predictor_dimensions": int(xc.shape[1]),
        "task_scale": y_scale,
    }


def random_rank_two_predictions(
    x_train: np.ndarray,
    y_train: np.ndarray,
    x_validation: np.ndarray,
    label: str,
):
    xc, yz, x_mean, y_mean, y_scale, design_rank, condition = training_transform(
        x_train, y_train
    )
    _, singular, vh = np.linalg.svd(xc, full_matrices=False)
    whitener = vh.T @ np.diag(np.sqrt(max(len(x_train) - 1, 1)) / singular)
    z_train = xc @ whitener
    z_validation = (x_validation - x_mean) @ whitener
    predictions = np.empty((HAAR_DRAWS, len(x_validation), y_train.shape[1]))
    for draw in range(HAAR_DRAWS):
        rng = np.random.default_rng(seed(f"{label}:haar:{draw}"))
        q, _ = np.linalg.qr(rng.normal(size=(x_train.shape[1], 2)))
        coefficient = np.linalg.lstsq(z_train @ q, yz, rcond=None)[0]
        predicted_z = z_validation @ q @ coefficient
        predictions[draw] = predicted_z * y_scale + y_mean
    return predictions, {
        "condition": condition,
        "design_rank": design_rank,
        "predictor_dimensions": int(xc.shape[1]),
        "whitened_gram_max_abs_error": float(
            np.max(np.abs((z_train.T @ z_train) / max(len(x_train) - 1, 1) - np.eye(xc.shape[1])))
        ),
    }


def select_rank_nested(
    x: np.ndarray,
    y: np.ndarray,
    identifiers: np.ndarray,
    label: str,
):
    folds = balanced_folds(identifiers, label, INNER_FOLDS)
    max_rank = x.shape[1]
    squared_error = np.zeros(max_rank)
    cell_count = np.zeros(max_rank, dtype=int)
    conditions = []
    ranks = []
    for fold in range(INNER_FOLDS):
        validation = folds == fold
        training = ~validation
        for rank in range(1, max_rank + 1):
            prediction, diagnostics = reduced_rank_predict(
                x[training], y[training], x[validation], rank
            )
            standardized_residual = (
                y[validation] - prediction
            ) / diagnostics["task_scale"]
            squared_error[rank - 1] += float(np.square(standardized_residual).sum())
            cell_count[rank - 1] += standardized_residual.size
            if rank == 1:
                conditions.append(diagnostics["condition"])
                ranks.append(diagnostics["design_rank"])
    mean_mse = squared_error / cell_count
    best = float(mean_mse.min())
    selected = int(np.flatnonzero(mean_mse <= best + 1e-12)[0] + 1)
    return selected, mean_mse, conditions, ranks


def table_test(x: np.ndarray, y: np.ndarray, identifiers: np.ndarray, domains: int):
    rows, tasks = y.shape
    rank_two_prediction_sum = np.zeros((rows, tasks))
    selected_prediction_sum = np.zeros((rows, tasks))
    full_prediction_sum = np.zeros((rows, tasks))
    haar_prediction_sum = np.zeros((HAAR_DRAWS, rows, tasks))
    evaluation_scale_sum = np.zeros((rows, tasks))
    selected_ranks = []
    conditions = []
    design_ranks = []
    whiten_errors = []

    for repeat in range(CV_REPEATS):
        outer = balanced_folds(identifiers, f"H017:m{domains}:repeat{repeat}:outer", OUTER_FOLDS)
        for fold in range(OUTER_FOLDS):
            validation = outer == fold
            training = ~validation
            selected, _, inner_conditions, inner_ranks = select_rank_nested(
                x[training],
                y[training],
                identifiers[training],
                f"H017:m{domains}:repeat{repeat}:outer{fold}:inner",
            )
            selected_ranks.append(selected)
            conditions.extend(inner_conditions)
            design_ranks.extend(inner_ranks)
            rank_two_prediction, rank_two_diagnostics = reduced_rank_predict(
                x[training], y[training], x[validation], 2
            )
            selected_prediction, selected_diagnostics = reduced_rank_predict(
                x[training], y[training], x[validation], selected
            )
            full_prediction, _ = reduced_rank_predict(
                x[training], y[training], x[validation], x.shape[1]
            )
            haar_predictions, haar_diagnostics = random_rank_two_predictions(
                x[training],
                y[training],
                x[validation],
                f"H017:m{domains}:repeat{repeat}:outer{fold}",
            )
            task_scale = rank_two_diagnostics["task_scale"]
            rank_two_prediction_sum[validation] += rank_two_prediction
            selected_prediction_sum[validation] += selected_prediction
            full_prediction_sum[validation] += full_prediction
            haar_prediction_sum[:, validation] += haar_predictions
            evaluation_scale_sum[validation] += task_scale
            conditions.extend(
                [rank_two_diagnostics["condition"], selected_diagnostics["condition"]]
            )
            design_ranks.extend(
                [rank_two_diagnostics["design_rank"], selected_diagnostics["design_rank"]]
            )
            whiten_errors.append(haar_diagnostics["whitened_gram_max_abs_error"])

    evaluation_scale = evaluation_scale_sum / CV_REPEATS
    rank_two_residual = (y - rank_two_prediction_sum / CV_REPEATS) / evaluation_scale
    selected_residual = (y - selected_prediction_sum / CV_REPEATS) / evaluation_scale
    full_residual = (y - full_prediction_sum / CV_REPEATS) / evaluation_scale
    haar_residual = (
        y[None, :, :] - haar_prediction_sum / CV_REPEATS
    ) / evaluation_scale[None, :, :]

    def rmse(residual: np.ndarray) -> float:
        return float(np.sqrt(np.mean(np.square(residual))))

    point_rank_two = rmse(rank_two_residual)
    point_selected = rmse(selected_residual)
    point_full = rmse(full_residual)
    point_haar_draws = np.sqrt(np.mean(np.square(haar_residual), axis=(1, 2)))
    point_haar = float(np.median(point_haar_draws))
    point_noninferiority = point_rank_two - point_selected
    point_haar_gain = point_haar - point_rank_two

    rng = np.random.default_rng(seed(f"H017:m{domains}:bootstrap"))
    noninferiority = np.empty(BOOTSTRAPS)
    haar_gain = np.empty(BOOTSTRAPS)
    for bootstrap in range(BOOTSTRAPS):
        indices = rng.integers(0, rows, size=rows)
        rank_two_rmse = rmse(rank_two_residual[indices])
        selected_rmse = rmse(selected_residual[indices])
        haar_draw_rmse = np.sqrt(
            np.mean(np.square(haar_residual[:, indices]), axis=(1, 2))
        )
        noninferiority[bootstrap] = rank_two_rmse - selected_rmse
        haar_gain[bootstrap] = float(np.median(haar_draw_rmse)) - rank_two_rmse

    noninferiority_upper = float(np.quantile(noninferiority, 0.95))
    haar_gain_lower = float(np.quantile(haar_gain, 0.05))
    haar_gain_sigma = float(np.std(haar_gain, ddof=1))
    haar_gain_effect_sigma = (
        point_haar_gain / haar_gain_sigma if haar_gain_sigma > 0 else "infinite"
    )
    validity = {
        "all_design_ranks_full": all(rank == x.shape[1] for rank in design_ranks),
        "maximum_condition_at_most_10000": max(conditions) <= CONDITION_LIMIT,
        "all_task_scales_valid": True,
    }
    conditions_result = {
        "point_noninferiority_at_most_0_01": point_noninferiority <= 0.01,
        "upper_95_noninferiority_at_most_0_01": noninferiority_upper <= 0.01,
        "point_haar_gain_at_least_0_02": point_haar_gain >= 0.02,
        "lower_05_haar_gain_at_least_0_02": haar_gain_lower >= 0.02,
        "haar_gain_above_2_sigma": haar_gain_effect_sigma == "infinite"
        or haar_gain_effect_sigma > 2.0,
    }
    return {
        "rows": rows,
        "tasks": tasks,
        "predictor_dimensions": int(x.shape[1]),
        "cv_repeats": CV_REPEATS,
        "outer_folds": OUTER_FOLDS,
        "inner_folds": INNER_FOLDS,
        "haar_draws": HAAR_DRAWS,
        "selected_rank_histogram": {
            str(rank): count for rank, count in sorted(Counter(selected_ranks).items())
        },
        "selected_rank_median": float(np.median(selected_ranks)),
        "selected_rank_upper_95": float(np.quantile(selected_ranks, 0.95)),
        "point_rmse": {
            "rank_two": point_rank_two,
            "nested_selected": point_selected,
            "full_ols": point_full,
            "median_haar_rank_two": point_haar,
        },
        "rank_two_minus_selected": {
            "point": point_noninferiority,
            "bootstrap_upper_95": noninferiority_upper,
            "bootstrap_sigma": float(np.std(noninferiority, ddof=1)),
        },
        "median_haar_minus_rank_two": {
            "point": point_haar_gain,
            "bootstrap_lower_05": haar_gain_lower,
            "bootstrap_sigma": haar_gain_sigma,
            "effect_sigma": haar_gain_effect_sigma,
        },
        "maximum_condition_number": float(max(conditions)),
        "maximum_whitened_gram_abs_error": float(max(whiten_errors)),
        "validity": validity,
        "conditions": conditions_result,
        "valid": all(validity.values()),
        "supported": all(validity.values()) and all(conditions_result.values()),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    loaded, metric_cols = load_tables(args.data)
    tables = {}
    for domains in DOMAIN_COUNTS:
        x, y, identifiers, domain_cols, id_col = prepare(*loaded[domains], metric_cols)
        result = table_test(x, y, identifiers, domains)
        result["domain_columns"] = domain_cols
        result["id_column"] = id_col
        tables[str(domains)] = result

    scope_valid = len(metric_cols) >= 100 and all(item["valid"] for item in tables.values())
    discovery_supported = all(tables[str(domains)]["supported"] for domains in (6, 12))
    confirmation_supported = all(tables[str(domains)]["supported"] for domains in (18, 24))
    if not scope_valid:
        verdict = "inconclusive"
    elif discovery_supported and confirmation_supported:
        verdict = "supported"
    else:
        verdict = "falsified"

    result = {
        "id": "H017",
        "version": 2,
        "type": "measurement",
        "verdict": verdict,
        "estimator_scope": "prediction-loss-optimal affine RRR for unseen mixture rows and fixed released tasks",
        "common_finite_task_count": len(metric_cols),
        "common_finite_task_columns": metric_cols,
        "bootstrap_count": BOOTSTRAPS,
        "cv_repeats": CV_REPEATS,
        "outer_folds": OUTER_FOLDS,
        "inner_folds": INNER_FOLDS,
        "haar_draws_per_outer_fold": HAAR_DRAWS,
        "scope_valid": scope_valid,
        "discovery": {"domain_counts": [6, 12], "supported": discovery_supported},
        "confirmation": {"domain_counts": [18, 24], "supported": confirmation_supported},
        "tables": tables,
        "inputs": [
            str(args.data / f"m{domains}_{kind}")
            for domains in DOMAIN_COUNTS
            for kind in ("ratios.csv", "metrics.csv")
        ],
        "command": f"python scripts/test_h017.py --data {args.data} --output {args.output}",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
