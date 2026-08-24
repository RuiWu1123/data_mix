#!/usr/bin/env python3
"""Measure Olmix RQ2 raw-BPB affine stable-rank scaling."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.linalg import helmert


BOOTSTRAPS = 10_000
ZERO_REPLACEMENT = 1e-6
DOMAIN_COUNTS = (6, 12, 18, 24)
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
    finite_common = []
    for column in sorted(common_metrics or set()):
        if all(pd.to_numeric(loaded[m][1][column], errors="coerce").notna().all() for m in DOMAIN_COUNTS):
            finite_common.append(column)
    return loaded, finite_common


def prepare(ratios: pd.DataFrame, metrics: pd.DataFrame, metric_cols: list[str]):
    id_col = "run" if "run" in ratios and "run" in metrics else "index"
    domain_cols = [column for column in ratios if column not in META]
    joined = ratios[[id_col] + domain_cols].merge(metrics[[id_col] + metric_cols], on=id_col, how="inner")
    weights = joined[domain_cols].apply(pd.to_numeric, errors="coerce").to_numpy(float)
    responses = joined[metric_cols].apply(pd.to_numeric, errors="coerce").to_numpy(float)
    finite = np.all(np.isfinite(weights), axis=1) & np.all(np.isfinite(responses), axis=1)
    return weights[finite], responses[finite], domain_cols, id_col


def fit_operator(weights: np.ndarray, responses: np.ndarray, indices: np.ndarray | None = None):
    if indices is not None:
        weights = weights[indices]
        responses = responses[indices]
    weights = weights.copy()
    replacements = int((weights <= 0).sum())
    weights[weights <= 0] = ZERO_REPLACEMENT
    weights /= weights.sum(axis=1, keepdims=True)
    basis = helmert(weights.shape[1], full=False).T
    x = np.log(weights) @ basis
    x -= x.mean(axis=0, keepdims=True)
    y = responses - responses.mean(axis=0, keepdims=True)
    coefficient, _, design_rank, design_singular = np.linalg.lstsq(x, y, rcond=None)
    response_singular = np.linalg.svd(coefficient.T, compute_uv=False)
    stable_rank = float(
        np.square(response_singular).sum()
        / max(float(response_singular[0] ** 2), np.finfo(float).tiny)
    )
    condition = float(design_singular[0] / design_singular[-1]) if design_singular[-1] > 0 else "infinite"
    return {
        "condition_number": condition,
        "design_rank": int(design_rank),
        "ilr_dimensions": int(x.shape[1]),
        "response_dimensions": int(y.shape[1]),
        "rows": int(x.shape[0]),
        "singular_values": response_singular,
        "stable_rank": stable_rank,
        "stable_rank_fraction": stable_rank / x.shape[1],
        "zero_replacements": replacements,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    loaded, common_metrics = load_tables(args.data)
    table_results = {}
    bootstrap_ranks = []
    design_valid = True
    for domains in DOMAIN_COUNTS:
        weights, responses, domain_cols, id_col = prepare(*loaded[domains], common_metrics)
        point = fit_operator(weights, responses)
        design_valid = design_valid and point["design_rank"] == domains - 1
        rng = np.random.default_rng(seed(f"H015:m{domains}"))
        ranks = np.empty(BOOTSTRAPS)
        for bootstrap in range(BOOTSTRAPS):
            indices = rng.integers(0, len(weights), size=len(weights))
            ranks[bootstrap] = fit_operator(weights, responses, indices)["stable_rank"]
        rank_fractions = ranks / (domains - 1)
        median_fraction = float(np.median(rank_fractions))
        upper_fraction = float(np.quantile(rank_fractions, 0.95))
        fraction_sigma = float(np.std(rank_fractions, ddof=1))
        deficit = 1.0 - median_fraction
        deficit_sigma = deficit / fraction_sigma if fraction_sigma > 0 else "infinite"
        conditions = {
            "median_fraction_at_most_0_50": median_fraction <= 0.50,
            "upper_95_fraction_at_most_0_60": upper_fraction <= 0.60,
            "nominal_deficit_above_2_sigma": deficit_sigma == "infinite" or deficit_sigma > 2.0,
        }
        table_results[str(domains)] = {
            "domain_columns": domain_cols,
            "id_column": id_col,
            "point": {
                key: value.tolist() if isinstance(value, np.ndarray) else value for key, value in point.items()
            },
            "bootstrap_median_stable_rank": float(np.median(ranks)),
            "bootstrap_median_rank_fraction": median_fraction,
            "bootstrap_rank_fraction_upper_95": upper_fraction,
            "bootstrap_rank_fraction_sigma": fraction_sigma,
            "nominal_rank_fraction_deficit": deficit,
            "deficit_sigma": deficit_sigma,
            "conditions": conditions,
            "supported": all(conditions.values()),
        }
        bootstrap_ranks.append(ranks)

    x = np.log(np.asarray(DOMAIN_COUNTS, dtype=float) - 1.0)
    rank_matrix = np.vstack(bootstrap_ranks)
    centered_x = x - x.mean()
    bootstrap_slopes = centered_x @ np.log(rank_matrix) / np.square(centered_x).sum()
    point_ranks = np.array([table_results[str(m)]["point"]["stable_rank"] for m in DOMAIN_COUNTS])
    point_slope = float(centered_x @ np.log(point_ranks) / np.square(centered_x).sum())
    slope_upper = float(np.quantile(bootstrap_slopes, 0.95))
    slope_conditions = {
        "point_slope_at_most_0_50": point_slope <= 0.50,
        "bootstrap_upper_95_at_most_0_75": slope_upper <= 0.75,
    }
    discovery_supported = all(table_results[str(m)]["supported"] for m in (6, 12))
    confirmation_supported = all(table_results[str(m)]["supported"] for m in (18, 24))
    scope_valid = len(common_metrics) >= 100 and design_valid
    if not scope_valid:
        verdict = "inconclusive"
    elif discovery_supported and confirmation_supported and all(slope_conditions.values()):
        verdict = "supported"
    else:
        verdict = "falsified"

    result = {
        "id": "H015",
        "type": "measurement",
        "verdict": verdict,
        "estimator_scope": "raw-BPB centered global-OLS stable rank; no intrinsic-dimension or sample-complexity claim",
        "bootstrap_count": BOOTSTRAPS,
        "zero_replacement": ZERO_REPLACEMENT,
        "common_finite_task_count": len(common_metrics),
        "common_finite_task_columns": common_metrics,
        "design_full_rank_every_m": design_valid,
        "scope_valid": scope_valid,
        "discovery": {"domain_counts": [6, 12], "supported": discovery_supported},
        "confirmation": {"domain_counts": [18, 24], "supported": confirmation_supported},
        "tables": table_results,
        "slope": {
            "point_log_log_slope": point_slope,
            "bootstrap_median": float(np.median(bootstrap_slopes)),
            "bootstrap_upper_95": slope_upper,
            "bootstrap_sigma": float(np.std(bootstrap_slopes, ddof=1)),
            "conditions": slope_conditions,
        },
        "inputs": [str(args.data / f"m{m}_{kind}") for m in DOMAIN_COUNTS for kind in ("ratios.csv", "metrics.csv")],
        "command": f"python scripts/test_h015.py --data {args.data} --output {args.output}",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
