#!/usr/bin/env python3
"""Literal-theorem stationary counterexample for H006."""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np


@dataclass
class Dual:
    value: float
    derivative: np.ndarray

    def __mul__(self, other):
        if isinstance(other, Dual):
            return Dual(self.value * other.value, self.derivative * other.value + other.derivative * self.value)
        return Dual(self.value * other, self.derivative * other)

    __rmul__ = __mul__

    def __sub__(self, other):
        if isinstance(other, Dual):
            return Dual(self.value - other.value, self.derivative - other.derivative)
        return Dual(self.value - other, self.derivative)

    def __rsub__(self, other):
        return Dual(other - self.value, -self.derivative)


def dual_exp(x: Dual) -> Dual:
    value = math.exp(x.value)
    return Dual(value, value * x.derivative)


def dual_target(theta: list[Dual]) -> Dual:
    squared = theta[0] * theta[0]
    return 1.0 - dual_exp(-1.0 * squared)


def assumptions_from_text(text: str) -> dict[str, bool]:
    theorem_start = text.find("Theorem 2.1 (Convergence of GRAPE)")
    theorem_end = text.find("Furthermore, Theorem 2.2", theorem_start)
    theorem = text[theorem_start:theorem_end]
    return {
        "theorem_found": theorem_start >= 0 and theorem_end > theorem_start,
        "l_smooth": "L-smooth" in theorem,
        "bounded_stochastic_gradients": "upper-bounded by G" in theorem,
        "learning_rate_bound": "γ" in theorem and "L" in theorem,
        "positive_regularizers": "µ" in theorem and "chosen such that" in theorem,
        "strong_convexity_not_displayed": "strongly convex" not in theorem,
    }


def construction(dimensions: int) -> dict:
    theta = np.zeros(dimensions)
    theta[0] = 1.0
    basis = np.eye(dimensions)
    dual_theta = [Dual(float(theta[i]), basis[i]) for i in range(dimensions)]
    target = dual_target(dual_theta)
    source_gradients = np.zeros((dimensions, dimensions))
    update = source_gradients.mean(axis=0)
    gap = target.value
    analytic_gradient = np.zeros(dimensions)
    analytic_gradient[0] = 2.0 * math.exp(-1.0)
    ad_error = float(np.linalg.norm(target.derivative - analytic_gradient))
    return {
        "dimensions": dimensions,
        "target_at_initialization": target.value,
        "target_optimum": 0.0,
        "optimality_gap": gap,
        "source_gradient_norm": float(np.linalg.norm(source_gradients)),
        "update_norm": float(np.linalg.norm(update)),
        "automatic_differentiation_error": ad_error,
        "gap_threshold_met": bool(gap > 0.50),
        "update_threshold_met": bool(np.linalg.norm(update) <= 1e-12),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--paper-text", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    assumptions = assumptions_from_text(args.paper_text.read_text(errors="replace"))
    discovery_runs = [construction(1) for _ in range(3)]
    confirmation_runs = [construction(7) for _ in range(3)]
    discovery = discovery_runs[0]
    confirmation = confirmation_runs[0]
    sigma = float(np.std([r["optimality_gap"] for r in discovery_runs + confirmation_runs], ddof=1))
    smoothness = {
        "global_gradient_bound": math.sqrt(2.0 / math.e),
        "global_smoothness_bound": 2.0,
        "learning_rate": 0.25,
        "learning_rate_upper_bound": 0.5,
        "mu_alpha": 1.0,
        "mu_z": 1.0,
    }
    valid = all(assumptions.values()) and smoothness["learning_rate"] <= smoothness["learning_rate_upper_bound"]
    supported = (
        valid
        and discovery["gap_threshold_met"]
        and confirmation["gap_threshold_met"]
        and discovery["update_threshold_met"]
        and confirmation["update_threshold_met"]
        and discovery["automatic_differentiation_error"] <= 1e-12
        and confirmation["automatic_differentiation_error"] <= 1e-12
        and sigma == 0.0
    )
    if supported:
        verdict = "supported"
    elif not valid or not discovery["update_threshold_met"] or not confirmation["update_threshold_met"]:
        verdict = "falsified"
    else:
        verdict = "inconclusive"

    payload = {
        "id": "H006",
        "verdict": verdict,
        "displayed_assumptions": assumptions,
        "smoothness_checks": smoothness,
        "discovery": discovery,
        "confirmation": confirmation,
        "repeat_count_per_construction": 3,
        "sigma": sigma,
        "effect_sigma": "infinite" if sigma == 0.0 and discovery["optimality_gap"] > 0.0 else discovery["optimality_gap"] / sigma,
        "scope": "literal displayed Theorem 2.1 only",
        "inputs": [str(args.paper_text), "references/grape_2505.20380.pdf"],
        "command": f"python scripts/test_h006.py --paper-text {args.paper_text} --output {args.output}",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
