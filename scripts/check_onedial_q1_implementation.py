#!/usr/bin/env python3
"""Static and numerical implementation audit for ONEDIAL-V3 Q1."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from onedial_core import (
    holm_rejections,
    interior_weight_seed,
    leading_significant_dimension,
    mixture_coordinates,
    prepare_design,
    protocol_seed,
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    protocol = json.loads(args.protocol.read_text(encoding="utf-8"))
    checks: dict[str, bool] = {}
    checks["protocol_id_v3"] = protocol.get("protocol_id") == "ONEDIAL-V3"
    checks["permutations_4999"] = protocol["randomness"]["permutation_replicates"] == 4999
    detector = protocol["common_estimator"]["significant_residual_dimension"]
    checks["holm_family_four"] = "first 4" in detector and "exactly these first 4" in detector

    seed_label = "implementation-audit"
    direct_seed = int.from_bytes(
        hashlib.sha256(("ONEDIAL-V1:" + seed_label).encode("utf-8")).digest()[:8], "little"
    )
    checks["global_seed_serialization"] = protocol_seed(seed_label) == direct_seed
    interior_label = (
        "ONEDIAL-V2:Q1-interior-weights:"
        "Q1-discovery:m=6:scenario=interior_rank2:replicate=17"
    )
    direct_interior_seed = int.from_bytes(
        hashlib.sha256(interior_label.encode("utf-8")).digest()[:8], "little"
    )
    checks["interior_seed_serialization"] = (
        interior_weight_seed("Q1-discovery", 6, "interior_rank2", 17) == direct_interior_seed
    )

    weights = np.asarray(
        [
            [0.0, 0.2, 0.8],
            [0.1, 0.0, 0.9],
            [0.3, 0.7, 0.0],
            [1.0 / 3.0, 1.0 / 3.0, 1.0 / 3.0],
        ]
    )
    ilr = mixture_coordinates(weights, "A", delta=1e-6)
    hellinger = mixture_coordinates(weights, "B")
    checks["coordinate_shapes"] = ilr.shape == (4, 2) and hellinger.shape == (4, 2)
    checks["coordinates_finite"] = bool(np.all(np.isfinite(ilr)) and np.all(np.isfinite(hellinger)))
    checks["hellinger_uniform_origin"] = bool(np.linalg.norm(hellinger[-1]) < 1e-12)

    rng = np.random.default_rng(protocol_seed("implementation-audit-design"))
    x = rng.normal(size=(48, 5))
    folds = np.arange(48) % 2
    cache = prepare_design(x, folds)
    checks["global_design_rank"] = bool(np.linalg.matrix_rank(cache.x - cache.global_x_mean) == 5)
    checks["fold0_training_rank"] = bool(
        np.linalg.matrix_rank(cache.x[cache.train_indices[0]] - cache.train_x_means[0]) == 5
    )
    checks["fold1_training_rank"] = bool(
        np.linalg.matrix_rank(cache.x[cache.train_indices[1]] - cache.train_x_means[1]) == 5
    )

    p_two = np.asarray([0.0030, 0.0002, 0.8, 0.9])
    p_leading_gap = np.asarray([0.0034, 0.0002, 0.8, 0.9])
    checks["holm_stepdown_rejects_two"] = holm_rejections(p_two).tolist() == [True, True, False, False]
    checks["leading_dimension_two"] = leading_significant_dimension(p_two) == 2
    checks["leading_dimension_stops_at_gap"] = leading_significant_dimension(p_leading_gap) == 0
    lower = np.asarray([0.05, 0.06, 0.07, 0.08])
    upper = np.asarray([0.9, 0.9, 0.9, 0.9])
    checks["early_stop_null_envelope_agrees"] = (
        leading_significant_dimension(lower) == leading_significant_dimension(upper) == 0
    )

    errors = [name for name, passed in checks.items() if not passed]
    payload = {
        "id": "ONEDIAL-V3-Q1-IMPLEMENTATION-AUDIT",
        "passed": not errors,
        "check_count": len(checks),
        "error_count": len(errors),
        "errors": errors,
        "checks": checks,
        "protocol_sha256": sha256(args.protocol),
        "synthetic_outcomes_read": False,
        "real_outcomes_read": False,
        "inputs": [str(args.protocol), "scripts/onedial_core.py"],
        "command": (
            "python scripts/check_onedial_q1_implementation.py "
            f"--protocol {args.protocol} --output {args.output}"
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
