#!/usr/bin/env python3
"""Audit whether Q1's frozen permutation count can resolve its Holm tests."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    protocol = json.loads(args.protocol.read_text(encoding="utf-8"))
    permutations = int(protocol["randomness"]["permutation_replicates"])
    familywise_alpha = 0.01
    minimum_p = 1.0 / (permutations + 1)
    q1 = protocol["questions"]["Q1"]
    phases = {
        "discovery": q1["discovery"]["olmix_designs"],
        "confirmation": q1["confirmation"]["olmix_designs"],
    }
    designs: dict[str, dict[str, object]] = {}
    for phase, domain_counts in phases.items():
        for domains in domain_counts:
            residual_family_size = int(domains) - 1
            first_holm_threshold = familywise_alpha / residual_family_size
            minimum_permutations = math.ceil(residual_family_size / familywise_alpha) - 1
            resolvable = minimum_p <= first_holm_threshold
            designs[f"{phase}/m{domains}"] = {
                "domain_count": int(domains),
                "residual_family_size": residual_family_size,
                "minimum_attainable_permutation_p": minimum_p,
                "first_holm_threshold": first_holm_threshold,
                "first_residual_rejection_resolvable": resolvable,
                "minimum_permutation_replicates_for_resolution": minimum_permutations,
                "registered_permutation_shortfall": max(0, minimum_permutations - permutations),
                "maximum_possible_significant_residual_dimension": (
                    residual_family_size if resolvable else 0
                ),
            }

    impossible_designs = [
        name
        for name, result in designs.items()
        if not result["first_residual_rejection_resolvable"]
    ]
    discovery_impossible = any(name.startswith("discovery/") for name in impossible_designs)
    confirmation_impossible = any(name.startswith("confirmation/") for name in impossible_designs)
    protocol_defect = discovery_impossible or confirmation_impossible
    payload = {
        "id": "ONEDIAL-V2-Q1-HOLM-RESOLUTION-AUDIT",
        "protocol_id": protocol["protocol_id"],
        "registered_permutation_replicates": permutations,
        "permutation_p_denominator": permutations + 1,
        "minimum_attainable_permutation_p": minimum_p,
        "familywise_alpha": familywise_alpha,
        "designs": designs,
        "impossible_designs": impossible_designs,
        "impossible_design_count": len(impossible_designs),
        "discovery_contains_impossible_design": discovery_impossible,
        "confirmation_contains_impossible_design": confirmation_impossible,
        "q1_all_designs_required": True,
        "q1_rank2_detection_rate_min": q1["support"]["rank2_detection_rate_min"],
        "q1_rank2_detection_rate_upper_bound_at_impossible_designs": 0.0,
        "protocol_defect": protocol_defect,
        "synthetic_outcomes_read": False,
        "real_outcomes_read": False,
        "inputs": [str(args.protocol)],
        "command": (
            "python scripts/audit_onedial_q1_holm_resolution.py "
            f"--protocol {args.protocol} --output {args.output}"
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
