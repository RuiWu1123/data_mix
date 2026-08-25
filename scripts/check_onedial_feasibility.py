#!/usr/bin/env python3
"""Enumerate and validate every registered ONEDIAL Act I reachability pair."""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any


META_COLUMNS = {"", "run", "name", "index", "Unnamed: 0"}
EXPECTED_CATEGORIES = {
    "p_reachability",
    "rank_or_count_reachability",
    "quantile_resolution",
}


def walk(value: Any, path: str = ""):
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}/{key}"
            yield child_path, child
            yield from walk(child, child_path)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            child_path = f"{path}/{index}"
            yield child_path, child
            yield from walk(child, child_path)


def finite_weight_rows(path: Path) -> tuple[int, int]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        domain_columns = [column for column in reader.fieldnames or [] if column not in META_COLUMNS]
        count = 0
        for row in reader:
            try:
                values = [float(row[column]) for column in domain_columns]
            except (TypeError, ValueError):
                continue
            if all(math.isfinite(value) for value in values):
                count += 1
    return count, len(domain_columns)


def pair(
    identifier: str,
    category: str,
    available: float,
    required: float,
    relation: str,
    source: str,
) -> dict[str, object]:
    if relation == ">=":
        passed = available >= required
    elif relation == "<=":
        passed = available <= required
    elif relation == "==":
        passed = available == required
    else:
        raise ValueError(f"unknown relation {relation}")
    return {
        "id": identifier,
        "category": category,
        "available": available,
        "required": required,
        "relation": relation,
        "passed": passed,
        "source": source,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--olmix-data", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    protocol = json.loads(args.protocol.read_text(encoding="utf-8"))
    obligation = protocol.get("act1_static_feasibility_audit", {})
    errors: list[str] = []
    constraints: list[dict[str, object]] = []

    permutations = int(protocol["randomness"]["permutation_replicates"])
    minimum_p = 1.0 / (permutations + 1)
    holm_family = 4
    holm_alpha = 0.01
    for index in range(holm_family):
        threshold = holm_alpha / (holm_family - index)
        record = pair(
            f"holm_direction_{index + 1}",
            "p_reachability",
            minimum_p,
            threshold,
            "<=",
            "/common_estimator/significant_residual_dimension",
        )
        record["resolution_margin"] = threshold / minimum_p
        constraints.append(record)

    registered_p_paths: list[str] = []
    for path, value in walk(protocol):
        if path.endswith("_p_max") and isinstance(value, (int, float)):
            registered_p_paths.append(path)
            record = pair(
                f"registered_p_gate:{path}",
                "p_reachability",
                minimum_p,
                float(value),
                "<=",
                path,
            )
            record["resolution_margin"] = float(value) / minimum_p
            constraints.append(record)

    row_counts: dict[int, int] = {}
    domain_column_counts: dict[int, int] = {}
    for domains in protocol["inputs"]["olmix"]["domain_counts"]:
        path = args.olmix_data / f"m{domains}_ratios.csv"
        rows, columns = finite_weight_rows(path)
        row_counts[int(domains)] = rows
        domain_column_counts[int(domains)] = columns
        constraints.append(
            pair(
                f"olmix_m{domains}_rows_vs_affine_rank",
                "rank_or_count_reachability",
                rows,
                int(domains),
                ">=",
                str(path),
            )
        )
        constraints.append(
            pair(
                f"olmix_m{domains}_rows_vs_two_fold_affine_capacity",
                "rank_or_count_reachability",
                rows,
                2 * int(domains),
                ">=",
                f"{path}; /common_estimator/crossfit_folds",
            )
        )
        constraints.append(
            pair(
                f"olmix_m{domains}_domain_columns",
                "rank_or_count_reachability",
                columns,
                int(domains),
                "==",
                str(path),
            )
        )

    q1 = protocol["questions"]["Q1"]
    maximum_truth_rank = len(q1["truth"]["singular_values"])
    for phase in ("discovery", "confirmation"):
        for domains in q1[phase]["olmix_designs"]:
            constraints.append(
                pair(
                    f"q1_{phase}_m{domains}_coordinate_rank_vs_truth_rank",
                    "rank_or_count_reachability",
                    int(domains) - 1,
                    maximum_truth_rank,
                    ">=",
                    f"/questions/Q1/{phase}/olmix_designs; /questions/Q1/truth/singular_values",
                )
            )
    constraints.append(
        pair(
            "holm_family_vs_registered_dimension_decision_space",
            "rank_or_count_reachability",
            holm_family,
            int(protocol["questions"]["Q2"]["support"]["significant_residual_dimension_max"]) + 1,
            ">=",
            "/common_estimator/significant_residual_dimension; /questions/Q2/support/significant_residual_dimension_max",
        )
    )

    q3 = protocol["questions"]["Q3"]
    constraints.extend(
        [
            pair(
                "q3_exact_bridge_size",
                "rank_or_count_reachability",
                len(q3["exact_task_bridge"]),
                int(q3["support"]["exact_task_count"]),
                "==",
                "/questions/Q3/exact_task_bridge",
            ),
            pair(
                "q3_macro_bridge_size",
                "rank_or_count_reachability",
                len(q3["macro_target_bridge"]["names"]),
                int(q3["support"]["macro_target_count"]),
                "==",
                "/questions/Q3/macro_target_bridge/names",
            ),
            pair(
                "q3_exact_sign_agreement_attainable",
                "rank_or_count_reachability",
                int(q3["support"]["exact_task_count"]),
                int(q3["support"]["exact_task_sign_agreement_min"]),
                ">=",
                "/questions/Q3/support",
            ),
            pair(
                "q3_macro_sign_agreement_attainable",
                "rank_or_count_reachability",
                int(q3["support"]["macro_target_count"]),
                int(q3["support"]["macro_sign_agreement_min"]),
                ">=",
                "/questions/Q3/support",
            ),
        ]
    )

    q4 = protocol["questions"]["Q4"]
    objectives = q4["validation_objectives"]
    spline = q4["curve"]
    spline_parameter_count = int(spline["degree"]) + 1 + int(spline["interior_knots"])
    constraints.extend(
        [
            pair(
                "q4_objective_components_sum",
                "rank_or_count_reachability",
                int(objectives["one_hot"]) + int(objectives["dirichlet"]),
                int(objectives["total"]),
                "==",
                "/questions/Q4/validation_objectives",
            ),
            pair(
                "q4_two_objective_halves",
                "rank_or_count_reachability",
                int(objectives["total"]),
                2 * int(objectives["minimum_targets_per_half"]),
                ">=",
                "/questions/Q4/validation_objectives",
            ),
            pair(
                "q4_half_size_vs_spline_parameter_count",
                "rank_or_count_reachability",
                int(objectives["minimum_targets_per_half"]),
                spline_parameter_count,
                ">=",
                "/questions/Q4/validation_objectives; /questions/Q4/curve",
            ),
        ]
    )

    q5 = protocol["questions"]["Q5"]
    for phase in ("discovery", "confirmation"):
        stage = q5[phase]
        domains = int(stage["selection_target_design"])
        rows = row_counts[domains]
        for budget_name in ("onedial_budget", "three_x_budget"):
            constraints.append(
                pair(
                    f"q5_{phase}_{budget_name}_vs_affine_rank",
                    "rank_or_count_reachability",
                    int(stage[budget_name]),
                    domains,
                    ">=",
                    f"/questions/Q5/{phase}/{budget_name}",
                )
            )
        constraints.append(
            pair(
                f"q5_{phase}_nonpilot_candidates",
                "rank_or_count_reachability",
                rows - int(stage["onedial_budget"]),
                int(q5["support"]["minimum_nonpilot_candidates"]),
                ">=",
                f"/questions/Q5/{phase}; {args.olmix_data}/m{domains}_ratios.csv",
            )
        )

    bootstrap_replicates = int(protocol["randomness"]["bootstrap_replicates"])
    quantile_paths: list[str] = []
    for path, value in walk(protocol):
        if not isinstance(value, (int, float)):
            continue
        final_key = path.rsplit("/", 1)[-1]
        if "bootstrap_lower95" in final_key or "bootstrap_upper95" in final_key:
            quantile_paths.append(path)
            constraints.append(
                pair(
                    f"bootstrap_95_resolution:{path}",
                    "quantile_resolution",
                    1.0 / bootstrap_replicates,
                    0.025,
                    "<=",
                    f"/randomness/bootstrap_replicates; {path}",
                )
            )

    for phase in ("discovery", "confirmation"):
        simulations = int(q1[phase]["replicates_per_scenario"])
        for path, value in walk(q1["support"], "/questions/Q1/support"):
            if not isinstance(value, (int, float)):
                continue
            final_key = path.rsplit("/", 1)[-1]
            if "wilson_" in final_key:
                quantile_paths.append(f"{phase}:{path}")
                constraints.append(
                    pair(
                        f"q1_{phase}_wilson95_resolution:{path}",
                        "quantile_resolution",
                        1.0 / simulations,
                        0.025,
                        "<=",
                        f"/questions/Q1/{phase}/replicates_per_scenario; {path}",
                    )
                )
            if "q05" in final_key:
                quantile_paths.append(f"{phase}:{path}")
                constraints.append(
                    pair(
                        f"q1_{phase}_q05_resolution:{path}",
                        "quantile_resolution",
                        1.0 / simulations,
                        0.05,
                        "<=",
                        f"/questions/Q1/{phase}/replicates_per_scenario; {path}",
                    )
                )

    q99_path = "/questions/Q4/support/margin_over_shuffle_q99_min"
    quantile_paths.append(q99_path)
    constraints.append(
        pair(
            "q4_shuffle_q99_resolution",
            "quantile_resolution",
            1.0 / permutations,
            0.01,
            "<=",
            f"/randomness/permutation_replicates; {q99_path}",
        )
    )

    categories = {str(item["category"]) for item in constraints}
    if categories != EXPECTED_CATEGORIES:
        errors.append(f"constraint categories differ: {sorted(categories)}")
    if set(obligation.get("constraint_pair_categories", [])) != EXPECTED_CATEGORIES:
        errors.append("protocol obligation does not require every audit category")
    if obligation.get("required_before_freeze") is not True:
        errors.append("Act I feasibility audit is not mandatory")
    failed = [str(item["id"]) for item in constraints if not item["passed"]]
    if failed:
        errors.append(f"unreachable constraints: {failed}")

    category_counts = {
        category: sum(item["category"] == category for item in constraints)
        for category in sorted(EXPECTED_CATEGORIES)
    }
    payload = {
        "id": "ONEDIAL-V3-ACT1-FEASIBILITY-CHECK",
        "protocol_id": protocol.get("protocol_id"),
        "passed": not errors,
        "errors": errors,
        "constraint_pair_count": len(constraints),
        "constraint_category_count": len(categories),
        "constraint_category_counts": category_counts,
        "failed_constraint_count": len(failed),
        "failed_constraint_ids": failed,
        "minimum_attainable_permutation_p": minimum_p,
        "holm_first_threshold": holm_alpha / holm_family,
        "holm_first_threshold_resolution_margin": (holm_alpha / holm_family) / minimum_p,
        "registered_p_threshold_paths": sorted(registered_p_paths),
        "registered_quantile_paths": sorted(quantile_paths),
        "olmix_finite_row_counts": {str(key): value for key, value in row_counts.items()},
        "olmix_domain_column_counts": {
            str(key): value for key, value in domain_column_counts.items()
        },
        "constraints": constraints,
        "outcome_columns_read": False,
        "inputs": [
            str(args.protocol),
            *[
                str(args.olmix_data / f"m{domains}_ratios.csv")
                for domains in protocol["inputs"]["olmix"]["domain_counts"]
            ],
        ],
        "command": (
            "python scripts/check_onedial_feasibility.py "
            f"--protocol {args.protocol} --olmix-data {args.olmix_data} --output {args.output}"
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
