#!/usr/bin/env python3
"""Test codomain-norm robustness of the H015 Olmix affine spectrum."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.linalg import helmert


BOOTSTRAPS = 10_000
DOMAIN_COUNTS = (6, 12, 18, 24)
NORMS = ("raw_bpb", "task_standardized", "equal_family_quadratic")
ZERO_REPLACEMENT = 1e-6
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
    return weights[finite], responses[finite], domain_cols, id_col


def task_family(task: str) -> str:
    if task.startswith("minerva_math_"):
        return "math"
    if task.startswith("codex_humaneval") or task.startswith("mbpp:") or task.startswith("mt_mbpp_"):
        return "code"
    return "qa"


def response_transform(
    responses: np.ndarray,
    norm: str,
    families: np.ndarray,
    family_sizes: dict[str, int],
):
    centered = responses - responses.mean(axis=0, keepdims=True)
    scales = np.ones(responses.shape[1], dtype=float)
    if norm != "raw_bpb":
        scales = responses.std(axis=0, ddof=1)
        if np.any(scales < 1e-8):
            raise ValueError("task standard deviation below 1e-8")
        centered = centered / scales
    if norm == "equal_family_quadratic":
        centered = centered / np.sqrt(
            np.asarray([family_sizes[family] for family in families], dtype=float)
        )
    return centered, scales


def fit_operator(
    weights: np.ndarray,
    responses: np.ndarray,
    norm: str,
    families: np.ndarray,
    family_sizes: dict[str, int],
    indices: np.ndarray | None = None,
):
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
    y, scales = response_transform(responses, norm, families, family_sizes)
    coefficient, _, design_rank, design_singular = np.linalg.lstsq(x, y, rcond=None)
    _, singular, vh = np.linalg.svd(coefficient.T, full_matrices=False)
    stable_rank = float(np.square(singular).sum() / max(singular[0] ** 2, np.finfo(float).tiny))
    condition = (
        float(design_singular[0] / design_singular[-1])
        if design_singular[-1] > 0
        else "infinite"
    )
    return {
        "condition_number": condition,
        "design_rank": int(design_rank),
        "rank_two_basis": vh[:2].T,
        "response_scales": scales,
        "singular_values": singular,
        "stable_rank": stable_rank,
        "stable_rank_fraction": stable_rank / x.shape[1],
        "zero_replacements": replacements,
    }


def squared_canonical_overlap(left: np.ndarray, right: np.ndarray) -> float:
    correlations = np.linalg.svd(left.T @ right, compute_uv=False)
    return float(np.mean(np.square(correlations)))


def family_aggregate_description(
    weights: np.ndarray,
    responses: np.ndarray,
    families: np.ndarray,
    family_sizes: dict[str, int],
):
    standardized, _ = response_transform(
        responses, "task_standardized", families, family_sizes
    )
    aggregate = np.column_stack(
        [standardized[:, families == family].mean(axis=1) for family in ("math", "code", "qa")]
    )
    aggregate_families = np.asarray(["math", "code", "qa"])
    aggregate_sizes = {family: 1 for family in aggregate_families}
    fit = fit_operator(
        weights,
        aggregate,
        "raw_bpb",
        aggregate_families,
        aggregate_sizes,
    )
    return {
        "output_count": 3,
        "stable_rank": fit["stable_rank"],
        "singular_values": fit["singular_values"].tolist(),
        "decision_use": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    loaded, metric_cols = load_tables(args.data)
    families = np.asarray([task_family(column) for column in metric_cols])
    family_sizes = {
        family: int(np.sum(families == family)) for family in ("math", "code", "qa")
    }
    scope_valid = len(metric_cols) >= 100 and min(family_sizes.values()) >= 7
    tables = {}
    bootstrap_ranks = {norm: [] for norm in NORMS}
    design_valid = True

    for domains in DOMAIN_COUNTS:
        weights, responses, domain_cols, id_col = prepare(*loaded[domains], metric_cols)
        point = {
            norm: fit_operator(weights, responses, norm, families, family_sizes)
            for norm in NORMS
        }
        design_valid = design_valid and all(
            fit["design_rank"] == domains - 1 for fit in point.values()
        )
        rng = np.random.default_rng(seed(f"H016:m{domains}"))
        ranks = {norm: np.empty(BOOTSTRAPS) for norm in NORMS}
        overlaps = {
            norm: np.empty(BOOTSTRAPS) for norm in NORMS if norm != "raw_bpb"
        }
        for bootstrap in range(BOOTSTRAPS):
            indices = rng.integers(0, len(weights), size=len(weights))
            fitted = {
                norm: fit_operator(
                    weights, responses, norm, families, family_sizes, indices
                )
                for norm in NORMS
            }
            for norm in NORMS:
                ranks[norm][bootstrap] = fitted[norm]["stable_rank"]
            for norm in overlaps:
                overlaps[norm][bootstrap] = squared_canonical_overlap(
                    fitted["raw_bpb"]["rank_two_basis"], fitted[norm]["rank_two_basis"]
                )

        norm_results = {}
        for norm in NORMS:
            rank_fractions = ranks[norm] / (domains - 1)
            median_fraction = float(np.median(rank_fractions))
            upper_fraction = float(np.quantile(rank_fractions, 0.95))
            fraction_sigma = float(np.std(rank_fractions, ddof=1))
            deficit_sigma = (
                (1.0 - median_fraction) / fraction_sigma if fraction_sigma > 0 else "infinite"
            )
            conditions = {
                "median_fraction_at_most_0_50": median_fraction <= 0.50,
                "upper_95_fraction_at_most_0_60": upper_fraction <= 0.60,
                "nominal_deficit_above_2_sigma": deficit_sigma == "infinite"
                or deficit_sigma > 2.0,
            }
            overlap_result = None
            if norm != "raw_bpb":
                point_overlap = squared_canonical_overlap(
                    point["raw_bpb"]["rank_two_basis"], point[norm]["rank_two_basis"]
                )
                lower_overlap = float(np.quantile(overlaps[norm], 0.05))
                overlap_conditions = {
                    "point_at_least_0_80": point_overlap >= 0.80,
                    "bootstrap_lower_05_at_least_0_60": lower_overlap >= 0.60,
                }
                conditions.update(overlap_conditions)
                overlap_result = {
                    "point": point_overlap,
                    "bootstrap_lower_05": lower_overlap,
                    "bootstrap_median": float(np.median(overlaps[norm])),
                    "bootstrap_sigma": float(np.std(overlaps[norm], ddof=1)),
                    "conditions": overlap_conditions,
                }
            norm_results[norm] = {
                "point": {
                    key: value.tolist() if isinstance(value, np.ndarray) else value
                    for key, value in point[norm].items()
                    if key != "rank_two_basis"
                },
                "bootstrap_median_rank_fraction": median_fraction,
                "bootstrap_upper_95_rank_fraction": upper_fraction,
                "bootstrap_rank_fraction_sigma": fraction_sigma,
                "deficit_sigma": deficit_sigma,
                "overlap_with_raw_rank_two": overlap_result,
                "conditions": conditions,
                "supported": all(conditions.values()),
            }
            bootstrap_ranks[norm].append(ranks[norm])

        tables[str(domains)] = {
            "domain_columns": domain_cols,
            "id_column": id_col,
            "rows": int(len(weights)),
            "norms": norm_results,
            "family_aggregate_descriptive": family_aggregate_description(
                weights, responses, families, family_sizes
            ),
        }

    x = np.log(np.asarray(DOMAIN_COUNTS, dtype=float) - 1.0)
    centered_x = x - x.mean()
    slopes = {}
    for norm in NORMS:
        rank_matrix = np.vstack(bootstrap_ranks[norm])
        bootstrap_slopes = centered_x @ np.log(rank_matrix) / np.square(centered_x).sum()
        point_ranks = np.asarray(
            [tables[str(domains)]["norms"][norm]["point"]["stable_rank"] for domains in DOMAIN_COUNTS]
        )
        point_slope = float(centered_x @ np.log(point_ranks) / np.square(centered_x).sum())
        upper_slope = float(np.quantile(bootstrap_slopes, 0.95))
        conditions = {
            "point_at_most_0_50": point_slope <= 0.50,
            "bootstrap_upper_95_at_most_0_75": upper_slope <= 0.75,
        }
        slopes[norm] = {
            "point": point_slope,
            "bootstrap_median": float(np.median(bootstrap_slopes)),
            "bootstrap_upper_95": upper_slope,
            "bootstrap_sigma": float(np.std(bootstrap_slopes, ddof=1)),
            "conditions": conditions,
            "supported": all(conditions.values()),
        }

    discovery_supported = all(
        tables[str(domains)]["norms"][norm]["supported"]
        for domains in (6, 12)
        for norm in NORMS
    )
    confirmation_supported = all(
        tables[str(domains)]["norms"][norm]["supported"]
        for domains in (18, 24)
        for norm in NORMS
    )
    scope_valid = scope_valid and design_valid
    if not scope_valid:
        verdict = "inconclusive"
    elif discovery_supported and confirmation_supported and all(
        item["supported"] for item in slopes.values()
    ):
        verdict = "supported"
    else:
        verdict = "falsified"

    result = {
        "id": "H016",
        "type": "measurement",
        "verdict": verdict,
        "estimator_scope": "three frozen diagonal codomain metrics on fixed released tasks; no deduplication or intrinsic-dimension claim",
        "bootstrap_count": BOOTSTRAPS,
        "zero_replacement": ZERO_REPLACEMENT,
        "common_finite_task_count": len(metric_cols),
        "common_finite_task_columns": metric_cols,
        "task_family_counts": family_sizes,
        "task_families": dict(zip(metric_cols, families.tolist())),
        "design_full_rank_every_m": design_valid,
        "scope_valid": scope_valid,
        "discovery": {"domain_counts": [6, 12], "supported": discovery_supported},
        "confirmation": {"domain_counts": [18, 24], "supported": confirmation_supported},
        "tables": tables,
        "slopes": slopes,
        "inputs": [
            str(args.data / f"m{domains}_{kind}")
            for domains in DOMAIN_COUNTS
            for kind in ("ratios.csv", "metrics.csv")
        ],
        "command": f"python scripts/test_h016.py --data {args.data} --output {args.output}",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
