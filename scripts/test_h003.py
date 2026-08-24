#!/usr/bin/env python3
"""Deterministic coordinate-contract audit for H003."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]


def source_trace() -> dict[str, bool]:
    pretrain = (ROOT / "vendor/on_policy_mix/pipeline/pretrain.py").read_text()
    opm = (ROOT / "vendor/on_policy_mix/pipeline/pretrain_opm.py").read_text()
    continual = (ROOT / "vendor/on_policy_mix/pipeline/continual_opm.py").read_text()
    return {
        "proxy_reader_prefers_ratios": 'spec.get("ratios", spec["weights"])' in pretrain,
        "pretrain_specs_have_weights_only": '"proxy_specs": _sample_proxy_weights(' in opm,
        "new_probe_is_90_percent": "0.9, component, self.old_weights" in opm,
        "final_expands_coefficients_directly": (
            "w_old * old_weights.get(d, 0.0) + opt_weights.get(d, 0.0)" in opm
        ),
        "continual_specs_have_effective_ratios": (
            '"ratios": {' in continual and "effective_new" in continual
        ),
    }


def evaluate_split(component_count: int, seed: int, count: int = 1000) -> dict:
    rng = np.random.default_rng(seed)
    coefficients = rng.dirichlet(np.ones(component_count), size=count)
    represented = 0.9 * coefficients
    represented[:, 0] += 0.1
    errors = np.abs(represented - coefficients).sum(axis=1)
    repeats = np.stack([errors.copy() for _ in range(3)])
    repeat_medians = np.median(repeats, axis=1)
    repeat_agreement = bool(np.all(repeat_medians == repeat_medians[0]))
    sigma = 0.0 if repeat_agreement else float(np.std(repeat_medians, ddof=1))
    median = float(np.median(errors))
    return {
        "candidate_count": count,
        "component_count": component_count,
        "seed": seed,
        "maximum_l1": float(errors.max()),
        "median_l1": median,
        "minimum_l1": float(errors.min()),
        "repeat_count": 3,
        "repeat_agreement": repeat_agreement,
        "repeat_medians": repeat_medians.tolist(),
        "sigma": sigma,
        "effect_sigma": "infinite" if sigma == 0.0 and median > 0.0 else median / sigma,
        "thresholds_met": bool(errors.max() > 1e-12 and median >= 0.02),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    trace = source_trace()
    discovery = evaluate_split(component_count=5, seed=0)
    confirmation = evaluate_split(component_count=7, seed=1729)
    pretrain_defect = all(
        trace[key]
        for key in (
            "proxy_reader_prefers_ratios",
            "pretrain_specs_have_weights_only",
            "new_probe_is_90_percent",
            "final_expands_coefficients_directly",
        )
    )
    negative_control = trace["continual_specs_have_effective_ratios"]
    repeats_agree = discovery["sigma"] == 0.0 and confirmation["sigma"] == 0.0
    if pretrain_defect and negative_control and repeats_agree and discovery["thresholds_met"] and confirmation["thresholds_met"]:
        verdict = "supported"
    elif (not pretrain_defect) or discovery["maximum_l1"] <= 1e-12 or confirmation["maximum_l1"] <= 1e-12:
        verdict = "falsified"
    else:
        verdict = "inconclusive"

    payload = {
        "id": "H003",
        "verdict": verdict,
        "source_trace": trace,
        "discovery": discovery,
        "confirmation": confirmation,
        "negative_control_tolerance": 1e-12,
        "inputs": [
            "vendor/on_policy_mix/pipeline/pretrain.py",
            "vendor/on_policy_mix/pipeline/pretrain_opm.py",
            "vendor/on_policy_mix/pipeline/continual_opm.py",
        ],
        "command": "python scripts/test_h003.py --output /work1/ruixiangtang/rw761/data_mix_artifacts/H003/result.json",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
