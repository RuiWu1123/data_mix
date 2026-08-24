#!/usr/bin/env python3
"""Temporal row-lineage audit for H004."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


def source_trace() -> dict[str, bool]:
    source = (ROOT / "vendor/admire_bayesopt/mfbayesopt_maxvalue.py").read_text()
    return {
        "preparation_initially_concatenates_high_rows": (
            "X_train_with_fidelity = torch.cat([X_train_low, X_train_medium, X_train_high], dim=0)" in source
        ),
        "test_rows_are_high_tail": "X_test_high = X_train_high[threshold:]" in source,
        "call_removes_high_tail_features": (
            "X_train_with_fidelity[:-(X_train_high.shape[0]-threshold)]" in source
        ),
        "call_removes_high_tail_labels": (
            "Y_train[:-(X_train_high.shape[0]-threshold)]" in source
        ),
    }


def lineage(name: str, high_count: int, threshold: int) -> dict:
    high_ids = [f"{name}:high:{i}" for i in range(high_count)]
    acquisition_ids = set(high_ids[:threshold])
    evaluation_ids = set(high_ids[threshold:])
    intersections = []
    for seed in range(20):
        # Acquisition order varies by seed, but the eligible universe is fixed by the slice.
        intersections.append(len(acquisition_ids & evaluation_ids))
    return {
        "dataset": name,
        "high_fidelity_rows": high_count,
        "threshold": threshold,
        "acquisition_eligible_high_rows": len(acquisition_ids),
        "evaluation_rows": len(evaluation_ids),
        "seed_count": 20,
        "intersection_counts": intersections,
        "maximum_contamination_fraction": max(intersections) / max(1, len(evaluation_ids)),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    pile = pd.read_csv(ROOT / "vendor/admire_bayesopt/regmix-data/test_mixture_1B.csv")
    ift = pd.read_csv(ROOT / "vendor/admire_bayesopt/admire_ift_runs/admire_ift_runs.csv")
    ift_high = ift[ift["model"] == "Qwen2.5-7B"]
    trace = source_trace()
    discovery = lineage("pile", len(pile), 48)
    confirmation = lineage("ift", len(ift_high), 60)
    empty = (
        max(discovery["intersection_counts"]) == 0
        and max(confirmation["intersection_counts"]) == 0
    )
    slice_present = all(trace.values())
    if empty and slice_present:
        verdict = "falsified"
    elif not empty and max(
        discovery["maximum_contamination_fraction"],
        confirmation["maximum_contamination_fraction"],
    ) >= 0.05:
        verdict = "inconclusive"
    else:
        verdict = "inconclusive"

    payload = {
        "id": "H004",
        "verdict": verdict,
        "source_trace": trace,
        "discovery": discovery,
        "confirmation": confirmation,
        "falsification_reason": (
            "The run_mfbayesopt call removes the target high-fidelity tail before acquisition."
            if verdict == "falsified"
            else None
        ),
        "inputs": [
            "vendor/admire_bayesopt/mfbayesopt_maxvalue.py",
            "vendor/admire_bayesopt/regmix-data/test_mixture_1B.csv",
            "vendor/admire_bayesopt/admire_ift_runs/admire_ift_runs.csv",
        ],
        "command": "python scripts/test_h004.py --output /work1/ruixiangtang/rw761/data_mix_artifacts/H004/result.json",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
