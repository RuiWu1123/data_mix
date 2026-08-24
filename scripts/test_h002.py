#!/usr/bin/env python3
"""Bootstrap identification of an Apple additive-law mixture optimum."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import least_squares, minimize
from scipy.spatial.distance import pdist


BOOTSTRAPS = 1_000
MULTISTARTS = 20
MIXTURE_FLOOR = 1e-6
VALIDITY_TOL = 1e-6


def predict_and_jacobian(params: np.ndarray, weights: np.ndarray, model_size: np.ndarray, tokens: np.ndarray):
    n_model = model_size / 1e6
    d_tokens = tokens / 1e9
    bias, bias_tokens, pow_tokens, bias_size, pow_size = params[:5]
    coefficients = params[5:12]
    powers = params[12:19]
    weight_power = weights**powers
    mixture_sum = np.maximum(weight_power @ coefficients, np.finfo(float).tiny)
    prediction = (
        bias
        + 1.0 / mixture_sum
        + bias_tokens * d_tokens ** (-pow_tokens)
        + bias_size * n_model ** (-pow_size)
    )
    jacobian = np.empty((len(weights), 19), dtype=float)
    jacobian[:, 0] = 1.0
    jacobian[:, 1] = d_tokens ** (-pow_tokens)
    jacobian[:, 2] = -bias_tokens * np.log(d_tokens) * d_tokens ** (-pow_tokens)
    jacobian[:, 3] = n_model ** (-pow_size)
    jacobian[:, 4] = -bias_size * np.log(n_model) * n_model ** (-pow_size)
    jacobian[:, 5:12] = -weight_power / mixture_sum[:, None] ** 2
    jacobian[:, 12:19] = (
        -weight_power * coefficients * np.log(weights) / mixture_sum[:, None] ** 2
    )
    return prediction, jacobian


def fit_law(
    weights: np.ndarray,
    model_size: np.ndarray,
    tokens: np.ndarray,
    target: np.ndarray,
    starts: list[np.ndarray],
    row_weights: np.ndarray | None = None,
    max_nfev: int = 400,
) -> dict[str, object]:
    lower = np.array([0, 0, 0, 0, 0] + [1e-8] * 7 + [-2] * 7, dtype=float)
    upper = np.array([5, 15, 2, 15, 2] + [6] * 7 + [2] * 7, dtype=float)
    scale = np.ones(len(target)) if row_weights is None else np.sqrt(row_weights)

    def residual(params: np.ndarray) -> np.ndarray:
        prediction, _ = predict_and_jacobian(params, weights, model_size, tokens)
        return (prediction - target) * scale

    def jacobian(params: np.ndarray) -> np.ndarray:
        _, jac = predict_and_jacobian(params, weights, model_size, tokens)
        return jac * scale[:, None]

    results = []
    for start in starts:
        fitted = least_squares(
            residual,
            np.clip(start, lower + 1e-10, upper - 1e-10),
            jac=jacobian,
            bounds=(lower, upper),
            loss="huber",
            f_scale=1e-3,
            xtol=1e-9,
            ftol=1e-9,
            gtol=1e-9,
            max_nfev=max_nfev,
        )
        results.append(fitted)
    finite = [item for item in results if np.isfinite(item.cost)]
    best = min(finite, key=lambda item: item.cost)
    return {
        "params": best.x,
        "cost": float(best.cost),
        "success": bool(best.success),
        "nfev": int(best.nfev),
        "start_cost_min": float(min(item.cost for item in finite)),
        "start_cost_max": float(max(item.cost for item in finite)),
        "finite_start_count": len(finite),
    }


def parameter_starts(seed: int) -> list[np.ndarray]:
    lower = np.array([0, 0, 0, 0, 0] + [1e-8] * 7 + [-2] * 7, dtype=float)
    upper = np.array([5, 15, 2, 15, 2] + [6] * 7 + [2] * 7, dtype=float)
    rng = np.random.default_rng(seed)
    starts = [(lower + upper) / 2]
    starts.extend(rng.uniform(lower, upper) for _ in range(MULTISTARTS - 1))
    return starts


def mixture_value_gradient(params: np.ndarray, mixture: np.ndarray, model_size: float, tokens: float):
    bias, bias_tokens, pow_tokens, bias_size, pow_size = params[:5]
    coefficients = params[5:12]
    powers = params[12:19]
    terms = coefficients * mixture**powers
    mixture_sum = max(float(terms.sum()), np.finfo(float).tiny)
    value = (
        bias
        + 1.0 / mixture_sum
        + bias_tokens * (tokens / 1e9) ** (-pow_tokens)
        + bias_size * (model_size / 1e6) ** (-pow_size)
    )
    gradient = -(coefficients * powers * mixture ** (powers - 1)) / mixture_sum**2
    return float(value), gradient


def kkt_residual(mixture: np.ndarray, gradient: np.ndarray) -> float:
    free = mixture > MIXTURE_FLOOR + 1e-5
    if not np.any(free):
        return float("inf")
    common = float(np.mean(gradient[free]))
    free_residual = float(np.max(np.abs(gradient[free] - common)))
    lower_residual = float(np.max(np.maximum(common - gradient[~free], 0))) if np.any(~free) else 0.0
    feasibility = max(abs(float(mixture.sum()) - 1.0), max(0.0, MIXTURE_FLOOR - float(mixture.min())))
    return max(free_residual, lower_residual, feasibility)


def optimize_mixture(params: np.ndarray, model_size: float, tokens: float, seed: int) -> dict[str, object]:
    rng = np.random.default_rng(seed)
    starts = [np.full(7, 1 / 7)]
    starts.extend(rng.dirichlet(np.ones(7)) for _ in range(MULTISTARTS - 1))
    bounds = [(MIXTURE_FLOOR, 1.0)] * 7
    constraint = {"type": "eq", "fun": lambda value: float(value.sum() - 1.0), "jac": lambda value: np.ones(7)}
    solutions = []
    for start in starts:
        start = MIXTURE_FLOOR + (1 - 7 * MIXTURE_FLOOR) * start

        def objective(value: np.ndarray) -> float:
            return mixture_value_gradient(params, value, model_size, tokens)[0]

        def gradient(value: np.ndarray) -> np.ndarray:
            return mixture_value_gradient(params, value, model_size, tokens)[1]

        result = minimize(
            objective,
            start,
            jac=gradient,
            method="SLSQP",
            bounds=bounds,
            constraints=constraint,
            options={"ftol": 1e-12, "maxiter": 1000},
        )
        if result.success and np.isfinite(result.fun):
            solutions.append(result)
    if not solutions:
        return {"valid": False, "reason": "no successful simplex start"}
    best = min(solutions, key=lambda item: item.fun)
    values = np.array([item.fun for item in solutions])
    _, gradient = mixture_value_gradient(params, best.x, model_size, tokens)
    residual = kkt_residual(best.x, gradient)
    spread = float(values.max() - values.min())
    return {
        "valid": len(solutions) == MULTISTARTS and spread <= VALIDITY_TOL and residual <= VALIDITY_TOL,
        "mixture": best.x,
        "objective": float(best.fun),
        "successful_starts": len(solutions),
        "objective_spread": spread,
        "kkt_simplex_residual": residual,
    }


def deterministic_seed(label: str) -> int:
    return int.from_bytes(hashlib.sha256(label.encode("utf-8")).digest()[:8], "little")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    frame = pd.read_csv(args.data, comment="#")
    domains = ["arxiv", "book", "c4", "github", "commoncrawl", "stackexchange", "wikipedia"]
    weight_cols = [f"weight_{domain}" for domain in domains]
    frame = frame[frame["n_tokens"] > 4e9].dropna(subset=weight_cols + ["openhermes_loss"])
    model_sizes = sorted(frame["model_size"].unique())
    split_at = len(model_sizes) // 2
    lower_sizes = set(model_sizes[:split_at])
    lower_frame = frame[frame["model_size"].isin(lower_sizes)].reset_index(drop=True)
    upper_frame = frame[~frame["model_size"].isin(lower_sizes)].reset_index(drop=True)
    target_model_size = float(upper_frame["model_size"].max())
    target_tokens = float(upper_frame["n_tokens"].max())

    lower_w = lower_frame[weight_cols].to_numpy(float)
    lower_n = lower_frame["model_size"].to_numpy(float)
    lower_d = lower_frame["n_tokens"].to_numpy(float)
    lower_y = lower_frame["openhermes_loss"].to_numpy(float)
    rounded_weights = np.round(lower_w, 12)
    unique_mixtures, block_inverse = np.unique(rounded_weights, axis=0, return_inverse=True)

    full_starts = parameter_starts(deterministic_seed("H002:lower-full"))
    lower_fit = fit_law(lower_w, lower_n, lower_d, lower_y, full_starts)
    bootstrap_optima = np.empty((BOOTSTRAPS, 7))
    optimizer_spreads = np.empty(BOOTSTRAPS)
    kkt_residuals = np.empty(BOOTSTRAPS)
    fit_successes = 0
    valid_optimizers = 0
    rng = np.random.default_rng(deterministic_seed("H002:mixture-block-bootstrap"))
    for bootstrap in range(BOOTSTRAPS):
        sampled = rng.integers(0, len(unique_mixtures), size=len(unique_mixtures))
        counts = np.bincount(sampled, minlength=len(unique_mixtures))
        row_weights = counts[block_inverse].astype(float)
        bootstrap_fit = fit_law(
            lower_w,
            lower_n,
            lower_d,
            lower_y,
            [lower_fit["params"]],
            row_weights=row_weights,
            max_nfev=80,
        )
        fit_successes += int(bootstrap_fit["success"])
        optimized = optimize_mixture(
            bootstrap_fit["params"], target_model_size, target_tokens, deterministic_seed(f"H002:mix:{bootstrap}")
        )
        if optimized.get("valid"):
            valid_optimizers += 1
        if "mixture" not in optimized:
            bootstrap_optima[bootstrap] = np.nan
            optimizer_spreads[bootstrap] = np.inf
            kkt_residuals[bootstrap] = np.inf
        else:
            bootstrap_optima[bootstrap] = optimized["mixture"]
            optimizer_spreads[bootstrap] = optimized["objective_spread"]
            kkt_residuals[bootstrap] = optimized["kkt_simplex_residual"]

    generation_complete = np.all(np.isfinite(bootstrap_optima))
    upper_w = upper_frame[weight_cols].to_numpy(float)
    upper_n = upper_frame["model_size"].to_numpy(float)
    upper_d = upper_frame["n_tokens"].to_numpy(float)
    upper_y = upper_frame["openhermes_loss"].to_numpy(float)
    upper_fit = fit_law(
        upper_w,
        upper_n,
        upper_d,
        upper_y,
        parameter_starts(deterministic_seed("H002:upper-common-evaluator")),
    )
    upper_prediction, _ = predict_and_jacobian(upper_fit["params"], upper_w, upper_n, upper_d)
    evaluator_sigma = float(np.std(upper_prediction - upper_y, ddof=19))

    if generation_complete:
        evaluator_losses = np.array(
            [mixture_value_gradient(upper_fit["params"], mixture, target_model_size, target_tokens)[0] for mixture in bootstrap_optima]
        )
        pairwise_l1_median = float(np.median(pdist(bootstrap_optima, metric="cityblock")))
        coordinate_lower = np.quantile(bootstrap_optima, 0.025, axis=0)
        coordinate_upper = np.quantile(bootstrap_optima, 0.975, axis=0)
        coordinate_widths = coordinate_upper - coordinate_lower
        pairwise_loss_difference_median = float(np.median(pdist(evaluator_losses[:, None], metric="cityblock")))
    else:
        evaluator_losses = np.full(BOOTSTRAPS, np.nan)
        pairwise_l1_median = float("nan")
        coordinate_lower = np.full(7, np.nan)
        coordinate_upper = np.full(7, np.nan)
        coordinate_widths = np.full(7, np.nan)
        pairwise_loss_difference_median = float("nan")

    validity = {
        "bootstrap_parameter_fit_success_count": fit_successes,
        "bootstrap_optimizer_valid_count": valid_optimizers,
        "all_bootstraps_generated": bool(generation_complete),
        "maximum_optimizer_objective_spread": float(np.max(optimizer_spreads)),
        "maximum_kkt_simplex_residual": float(np.max(kkt_residuals)),
        "objective_spread_at_most_1e_6": bool(np.max(optimizer_spreads) <= VALIDITY_TOL),
        "kkt_simplex_residual_at_most_1e_6": bool(np.max(kkt_residuals) <= VALIDITY_TOL),
    }
    validity_passed = (
        fit_successes == BOOTSTRAPS
        and valid_optimizers == BOOTSTRAPS
        and generation_complete
        and validity["objective_spread_at_most_1e_6"]
        and validity["kkt_simplex_residual_at_most_1e_6"]
    )
    conditions = {
        "median_pairwise_L1_above_0_10": pairwise_l1_median > 0.10,
        "some_coordinate_95_width_above_0_10": float(np.nanmax(coordinate_widths)) > 0.10,
        "common_evaluator_difference_at_most_2_sigma": pairwise_loss_difference_median <= 2 * evaluator_sigma,
    }
    verdict = "inconclusive" if not validity_passed else ("supported" if all(conditions.values()) else "falsified")
    result = {
        "id": "H002",
        "verdict": verdict,
        "type": "measurement",
        "bootstrap_count": BOOTSTRAPS,
        "optimizer_multistarts_per_bootstrap": MULTISTARTS,
        "validity_tolerance": VALIDITY_TOL,
        "target_response": "openhermes_loss",
        "model_sizes": [float(value) for value in model_sizes],
        "lower_generation_model_sizes": [float(value) for value in model_sizes[:split_at]],
        "upper_confirmation_model_sizes": [float(value) for value in model_sizes[split_at:]],
        "target_model_size": target_model_size,
        "target_tokens": target_tokens,
        "lower_rows": len(lower_frame),
        "upper_rows": len(upper_frame),
        "mixture_block_count": len(unique_mixtures),
        "lower_full_fit": {key: value for key, value in lower_fit.items() if key != "params"},
        "upper_common_evaluator_fit": {key: value for key, value in upper_fit.items() if key != "params"},
        "validity": validity,
        "validity_passed": validity_passed,
        "measurements": {
            "median_pairwise_optimum_L1": pairwise_l1_median,
            "coordinate_95_lower": coordinate_lower.tolist(),
            "coordinate_95_upper": coordinate_upper.tolist(),
            "coordinate_95_widths": coordinate_widths.tolist(),
            "maximum_coordinate_95_width": float(np.nanmax(coordinate_widths)),
            "common_evaluator_loss_difference_median": pairwise_loss_difference_median,
            "common_evaluator_residual_sigma": evaluator_sigma,
            "loss_difference_sigma_units": pairwise_loss_difference_median / evaluator_sigma if evaluator_sigma > 0 else "infinite",
        },
        "conditions": conditions,
        "inputs": [str(args.data)],
        "command": f"python scripts/test_h002.py --data {args.data} --output {args.output}",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
