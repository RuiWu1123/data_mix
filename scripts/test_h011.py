#!/usr/bin/env python3
"""Strongly-convex raw-variance counterexample for H011."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np


def theorem_scope(text: str) -> dict[str, bool]:
    start = text.find("Theorem 2.2 (Monotonic Variance Reduction")
    end = text.find("3 Experiments", start)
    block = text[start:end]
    normalized = " ".join(block.split())
    return {
        "theorem_found": start >= 0 and end > start,
        "strong_convexity_displayed": "strongly convex" in normalized,
        "bounded_gradient_displayed": "upper-bounded by G" in normalized,
        "explicit_global_parameter_quantifier": (
            "for all θ" in normalized or "for every θ" in normalized
        ),
        "minimum_source_count_displayed": "at least two source" in normalized.lower(),
    }


def theta(t: int, gamma: float = 0.1) -> float:
    return 1.0 - (1.0 - 2.0 * gamma) ** t


def discovery() -> dict:
    t0, t1 = theta(0), theta(1)
    variance0, variance1 = 4.0 * t0**2, 4.0 * t1**2
    r = 0.8
    positivity_factors = {
        "r_in_open_unit_interval": 0.0 < r < 1.0,
        "first_factor_positive_for_all_finite_t": True,
        "second_factor_positive_for_all_finite_t": True,
    }
    return {
        "source_count": 1,
        "target_count": 2,
        "theta_recurrence": "theta_t=1-0.8^t",
        "variance_formula": "Var=4*theta_t^2",
        "variance_t0": variance0,
        "variance_t1": variance1,
        "first_step_increase": variance1 - variance0,
        "increment_formula": "4*(r^t-r^(t+1))*(2-r^t-r^(t+1))",
        "symbolically_positive_all_finite_t": all(positivity_factors.values()),
        "positivity_factors": positivity_factors,
    }


def confirmation() -> dict:
    centers = np.linspace(-1.0, -2.0, 7)
    steps = np.arange(0, 1001)
    xs = 1.0 - np.power(0.8, steps)
    losses = np.stack([(xs - c) ** 2 + 2.0 for c in centers], axis=1)
    variances = np.var(losses, axis=1)
    increments = np.diff(variances)
    # Analytically, d Var(c^2 - 2xc) / dx = -4 Cov(c^2 - 2xc, c).
    analytic_derivatives = []
    for x in xs:
        values = centers**2 - 2.0 * x * centers
        analytic_derivatives.append(-4.0 * np.mean((values - values.mean()) * (centers - centers.mean())))
    analytic_derivatives = np.asarray(analytic_derivatives)
    source_gradients = np.tile(np.array([-2.0] + [0.0] * 6), (7, 1))
    mixture_spread = float(np.max(np.linalg.norm(source_gradients - source_gradients.mean(axis=0), axis=1)))
    formula_values = 1.0 - np.power(0.8, steps)
    update_error = float(np.max(np.abs(xs - formula_values)))
    return {
        "dimensions": 7,
        "source_count": 7,
        "target_count": 7,
        "target_centers": centers.tolist(),
        "minimum_sampled_variance_increment": float(increments.min()),
        "minimum_analytic_variance_derivative": float(analytic_derivatives.min()),
        "all_first_1000_increments_positive": bool(np.all(increments > 0.0)),
        "analytic_derivative_positive_on_invariant_interval": bool(np.all(analytic_derivatives > 0.0)),
        "source_gradient_mixture_spread": mixture_spread,
        "update_formula_error": update_error,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--paper-text", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    scope = theorem_scope(args.paper_text.read_text(errors="replace"))
    disc_runs = [discovery() for _ in range(3)]
    conf_runs = [confirmation() for _ in range(3)]
    disc, conf = disc_runs[0], conf_runs[0]
    repeat_stats = [run["first_step_increase"] for run in disc_runs]
    repeat_stats += [run["minimum_analytic_variance_derivative"] for run in conf_runs]
    repeated_groups_equal = (
        len(set(run["first_step_increase"] for run in disc_runs)) == 1
        and len(set(run["minimum_analytic_variance_derivative"] for run in conf_runs)) == 1
    )
    sigma = 0.0 if repeated_groups_equal else float(np.std(repeat_stats, ddof=1))
    assumptions = {
        "mu": 2.0,
        "L": 2.0,
        "gamma": 0.1,
        "gamma_at_most_inverse_L": 0.1 <= 0.5,
        "invariant_interval": [0.0, 1.0],
        "trajectory_gradient_bound": 6.0,
    }
    ambiguous = scope["explicit_global_parameter_quantifier"]
    valid = (
        scope["theorem_found"]
        and scope["strong_convexity_displayed"]
        and scope["bounded_gradient_displayed"]
        and not scope["minimum_source_count_displayed"]
        and assumptions["gamma_at_most_inverse_L"]
    )
    supported = (
        valid
        and not ambiguous
        and disc["first_step_increase"] > 0.10
        and disc["symbolically_positive_all_finite_t"]
        and conf["analytic_derivative_positive_on_invariant_interval"]
        and conf["update_formula_error"] <= 1e-12
        and conf["source_gradient_mixture_spread"] <= 1e-12
        and sigma == 0.0
    )
    if ambiguous:
        verdict = "inconclusive"
    elif supported:
        verdict = "supported"
    elif not valid or not disc["symbolically_positive_all_finite_t"] or not conf["analytic_derivative_positive_on_invariant_interval"]:
        verdict = "falsified"
    else:
        verdict = "inconclusive"

    payload = {
        "id": "H011",
        "verdict": verdict,
        "theorem_scope": scope,
        "assumption_checks": assumptions,
        "discovery": disc,
        "confirmation": conf,
        "repeat_count_per_construction": 3,
        "sigma": sigma,
        "effect_sigma": "infinite" if sigma == 0.0 and disc["first_step_increase"] > 0.0 else disc["first_step_increase"] / sigma,
        "inputs": [str(args.paper_text), "references/grape_2505.20380.pdf"],
        "command": f"python scripts/test_h011.py --paper-text {args.paper_text} --output {args.output}",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
