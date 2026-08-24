#!/usr/bin/env python3
"""Measure the preregistered affine stable rank of mixture-response tables."""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.linalg import helmert


ZERO_REPLACEMENT = 1e-6
BOOTSTRAPS = 10_000


@dataclass
class Group:
    method: str
    split: str
    label: str
    weights: np.ndarray
    responses: np.ndarray
    response_semantics: str


def stable_seed(label: str) -> int:
    return int.from_bytes(hashlib.sha256(label.encode("utf-8")).digest()[:8], "little")


def align_frames(ratios: pd.DataFrame, metrics: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, str]:
    if "index" in ratios and "index" in metrics:
        common = set(ratios["index"]) & set(metrics["index"])
        if len(common) >= 0.8 * min(len(ratios), len(metrics)):
            joined = ratios.merge(metrics, on="index", suffixes=("_ratio", "_metric"))
            ratio_cols = [column for column in ratios.columns if column != "index"]
            metric_cols = [column for column in metrics.columns if column != "index"]
            return joined[ratio_cols], joined[metric_cols], "index_inner_join"
    n_rows = min(len(ratios), len(metrics))
    return (
        ratios.iloc[:n_rows].drop(columns=["index"], errors="ignore").reset_index(drop=True),
        metrics.iloc[:n_rows].drop(columns=["index"], errors="ignore").reset_index(drop=True),
        "position_after_index_mismatch",
    )


def load_regmix(repo: Path) -> tuple[list[Group], dict[str, object]]:
    groups = []
    alignment = {}
    for scale, split in (("1m", "discovery"), ("60m", "confirmation"), ("1B", "confirmation")):
        ratios = pd.read_csv(repo / f"data/test_mixture_{scale}.csv")
        metrics = pd.read_csv(repo / f"data/test_pile_loss_{scale}.csv")
        ratio_values, metric_values, mode = align_frames(ratios, metrics)
        weight_cols = [column for column in ratio_values if column.startswith("train_the_pile_")]
        loss_cols = [column for column in metric_values if column.endswith("_val_loss")]
        groups.append(
            Group(
                method="RegMix",
                split=split,
                label=scale,
                weights=ratio_values[weight_cols].apply(pd.to_numeric, errors="coerce").to_numpy(float),
                responses=metric_values[loss_cols].apply(pd.to_numeric, errors="coerce").to_numpy(float),
                response_semantics="Pile domain-validation losses",
            )
        )
        alignment[scale] = {
            "mode": mode,
            "rows": len(ratio_values),
            "weight_columns": weight_cols,
            "response_columns": loss_cols,
        }
    return groups, alignment


def load_dmsl(repo: Path) -> tuple[list[Group], dict[str, object]]:
    path = repo / "data/dmsl_llm_slimpajama.csv"
    frame = pd.read_csv(path)
    weight_cols = [column for column in frame if column.startswith("weight_")]
    loss_cols = [column for column in frame if column.endswith("_loss") and column != "openhermes_loss"]
    model_sizes = sorted(frame["model_size"].dropna().unique())
    split_at = len(model_sizes) // 2
    lower = set(model_sizes[:split_at])
    groups = []
    skipped = []
    for (model_size, n_tokens), block in frame.groupby(["model_size", "n_tokens"], sort=True):
        if len(block) < len(weight_cols) + 2:
            skipped.append({"model_size": model_size, "n_tokens": n_tokens, "rows": len(block)})
            continue
        groups.append(
            Group(
                method="DMSL",
                split="discovery" if model_size in lower else "confirmation",
                label=f"N={model_size:g},D={n_tokens:g}",
                weights=block[weight_cols].apply(pd.to_numeric, errors="coerce").to_numpy(float),
                responses=block[loss_cols].apply(pd.to_numeric, errors="coerce").to_numpy(float),
                response_semantics="SlimPajama domain-validation losses",
            )
        )
    meta = {
        "model_sizes": [float(value) for value in model_sizes],
        "lower_half_model_sizes": [float(value) for value in model_sizes[:split_at]],
        "upper_half_model_sizes": [float(value) for value in model_sizes[split_at:]],
        "weight_columns": weight_cols,
        "response_columns": loss_cols,
        "skipped_groups": skipped,
    }
    return groups, meta


def transform_weights(weights: np.ndarray) -> tuple[np.ndarray, int]:
    valid = np.all(np.isfinite(weights), axis=1)
    weights = weights[valid].copy()
    replacements = int((weights <= 0).sum())
    weights[weights <= 0] = ZERO_REPLACEMENT
    weights /= weights.sum(axis=1, keepdims=True)
    basis = helmert(weights.shape[1], full=False).T
    return np.log(weights) @ basis, replacements


def fit_operator(weights: np.ndarray, responses: np.ndarray, indices: np.ndarray | None = None) -> dict[str, object]:
    finite_rows = np.all(np.isfinite(weights), axis=1) & np.all(np.isfinite(responses), axis=1)
    weights = weights[finite_rows]
    responses = responses[finite_rows]
    if indices is not None:
        weights = weights[indices]
        responses = responses[indices]
    x, replacements = transform_weights(weights)
    x -= x.mean(axis=0, keepdims=True)
    y = responses - responses.mean(axis=0, keepdims=True)
    coefficient, _, design_rank, singular_x = np.linalg.lstsq(x, y, rcond=None)
    operator = coefficient.T
    _, singular, vh = np.linalg.svd(operator, full_matrices=False)
    stable_rank = float(np.square(singular).sum() / max(float(singular[0] ** 2), np.finfo(float).tiny))
    active_rank = max(1, min(vh.shape[0], int(np.ceil(stable_rank))))
    condition = float(singular_x[0] / singular_x[-1]) if singular_x[-1] > 0 else "infinite"
    return {
        "active_subspace": vh[:active_rank].T,
        "condition_number": condition,
        "design_rank": int(design_rank),
        "ilr_dimensions": int(x.shape[1]),
        "response_dimensions": int(y.shape[1]),
        "rows": int(x.shape[0]),
        "singular_values": singular,
        "stable_rank": stable_rank,
        "stable_rank_fraction": stable_rank / x.shape[1],
        "zero_replacements": replacements,
    }


def canonical_overlap(left: np.ndarray, right: np.ndarray) -> float:
    denominator = max(1, min(left.shape[1], right.shape[1]))
    return float(np.square(left.T @ right).sum() / denominator)


def summarize_group(group: Group) -> dict[str, object]:
    finite_rows = np.all(np.isfinite(group.weights), axis=1) & np.all(np.isfinite(group.responses), axis=1)
    weights = group.weights[finite_rows]
    responses = group.responses[finite_rows]
    point = fit_operator(weights, responses)
    rng = np.random.default_rng(stable_seed(f"H013:{group.method}:{group.label}"))
    ranks = np.empty(BOOTSTRAPS)
    subspaces = []
    for iteration in range(BOOTSTRAPS):
        indices = rng.integers(0, len(weights), size=len(weights))
        fitted = fit_operator(weights, responses, indices)
        ranks[iteration] = fitted["stable_rank_fraction"]
        subspaces.append(fitted["active_subspace"])
    return {
        "method": group.method,
        "split": group.split,
        "label": group.label,
        "response_semantics": group.response_semantics,
        "point": {
            key: value.tolist() if isinstance(value, np.ndarray) else value
            for key, value in point.items()
            if key != "active_subspace"
        },
        "point_subspace": point["active_subspace"],
        "bootstrap_rank_fraction": ranks,
        "bootstrap_subspaces": subspaces,
    }


def summarize_method(items: list[dict[str, object]]) -> dict[str, object]:
    discovery = [item for item in items if item["split"] == "discovery"]
    confirmation = [item for item in items if item["split"] == "confirmation"]
    if not discovery or not confirmation:
        return {"valid": False, "reason": "missing discovery or confirmation scale"}
    rank_matrix = np.vstack([item["bootstrap_rank_fraction"] for item in items])
    bootstrap_median_rank = np.median(rank_matrix, axis=0)
    point_rank_fractions = [item["point"]["stable_rank_fraction"] for item in items]
    pairs = [(left, right) for left in discovery for right in confirmation]
    point_overlaps = [canonical_overlap(left["point_subspace"], right["point_subspace"]) for left, right in pairs]
    bootstrap_overlaps = np.empty(BOOTSTRAPS)
    for iteration in range(BOOTSTRAPS):
        bootstrap_overlaps[iteration] = np.median(
            [
                canonical_overlap(left["bootstrap_subspaces"][iteration], right["bootstrap_subspaces"][iteration])
                for left, right in pairs
            ]
        )
    median_rank = float(np.median(point_rank_fractions))
    rank_sigma = float(np.std(bootstrap_median_rank, ddof=1))
    nominal_fraction = 1.0
    deficit = nominal_fraction - median_rank
    deficit_sigma = deficit / rank_sigma if rank_sigma > 0 else "infinite"
    summary = {
        "valid": True,
        "scale_count": len(items),
        "discovery_scale_count": len(discovery),
        "confirmation_scale_count": len(confirmation),
        "cross_split_pair_count": len(pairs),
        "median_rank_fraction": median_rank,
        "bootstrap_rank_fraction_upper_95": float(np.quantile(bootstrap_median_rank, 0.95)),
        "rank_fraction_sigma": rank_sigma,
        "rank_deficit": deficit,
        "rank_deficit_sigma": deficit_sigma,
        "median_cross_scale_overlap": float(np.median(point_overlaps)),
        "bootstrap_overlap_lower_05": float(np.quantile(bootstrap_overlaps, 0.05)),
        "conditions": {
            "median_rank_fraction_at_most_0_50": median_rank <= 0.50,
            "upper_95_at_most_0_60": float(np.quantile(bootstrap_median_rank, 0.95)) <= 0.60,
            "cross_scale_overlap_at_least_0_80": float(np.median(point_overlaps)) >= 0.80,
            "rank_deficit_above_2_sigma": deficit_sigma == "infinite" or deficit_sigma > 2.0,
        },
    }
    summary["supported"] = all(summary["conditions"].values())
    return summary


def serializable_group(item: dict[str, object]) -> dict[str, object]:
    return {
        "method": item["method"],
        "split": item["split"],
        "label": item["label"],
        "response_semantics": item["response_semantics"],
        "point": item["point"],
        "bootstrap_rank_fraction_median": float(np.median(item["bootstrap_rank_fraction"])),
        "bootstrap_rank_fraction_upper_95": float(np.quantile(item["bootstrap_rank_fraction"], 0.95)),
        "bootstrap_rank_fraction_sigma": float(np.std(item["bootstrap_rank_fraction"], ddof=1)),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--regmix-repo", type=Path, required=True)
    parser.add_argument("--dmsl-repo", type=Path, required=True)
    parser.add_argument("--olmix-data", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    regmix_groups, regmix_meta = load_regmix(args.regmix_repo)
    dmsl_groups, dmsl_meta = load_dmsl(args.dmsl_repo)
    groups = regmix_groups + dmsl_groups
    fitted = [summarize_group(group) for group in groups]
    method_results = {
        method: summarize_method([item for item in fitted if item["method"] == method])
        for method in ("RegMix", "DMSL")
    }

    olmix_ratios = pd.read_csv(args.olmix_data / "m24_ratios.csv")
    olmix_metrics = pd.read_csv(args.olmix_data / "m24_metrics.csv")
    olmix_record = {
        "compatible_with_domain_validation_loss_codomains": False,
        "reason": "released metric columns are downstream-task BPB, not training-domain validation losses",
        "rows_ratios": len(olmix_ratios),
        "rows_metrics": len(olmix_metrics),
        "domain_columns": len([c for c in olmix_ratios if c not in {"run", "name", "index", "Unnamed: 0"}]),
        "metric_columns": len([c for c in olmix_metrics if c not in {"run", "name", "index", "Unnamed: 0"}]),
    }
    valid_methods = [value for value in method_results.values() if value.get("valid")]
    enough_scope = len(valid_methods) >= 2 and sum(item["scale_count"] for item in valid_methods) >= 3
    if not enough_scope:
        verdict = "inconclusive"
    elif all(item["supported"] for item in valid_methods):
        verdict = "supported"
    else:
        verdict = "falsified"

    result = {
        "id": "H013",
        "verdict": verdict,
        "estimator_name": "centered global OLS stable rank (not average-Jacobian or numerical rank)",
        "zero_replacement": ZERO_REPLACEMENT,
        "bootstrap_count": BOOTSTRAPS,
        "method_count_in_decision": len(valid_methods),
        "enough_scope": enough_scope,
        "method_results": method_results,
        "groups": [serializable_group(item) for item in fitted],
        "regmix_metadata": regmix_meta,
        "dmsl_metadata": dmsl_meta,
        "olmix_exclusion": olmix_record,
        "inputs": [str(args.regmix_repo), str(args.dmsl_repo), str(args.olmix_data)],
        "command": (
            f"python scripts/test_h013.py --regmix-repo {args.regmix_repo} "
            f"--dmsl-repo {args.dmsl_repo} --olmix-data {args.olmix_data} --output {args.output}"
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
