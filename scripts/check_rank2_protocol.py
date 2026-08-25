#!/usr/bin/env python3
"""Static validation for TWODIAL-E2E-V1."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--markdown", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    protocol = json.loads(args.protocol.read_text(encoding="utf-8"))
    checks: dict[str, bool] = {}
    checks["protocol_id"] = protocol.get("protocol_id") == "TWODIAL-E2E-V1"
    checks["formula_unique"] = protocol.get("claim") == (
        "loss(w,t) = c_t + g(w) * a_t + h(w) * b_t + noise, where g and h are two shared "
        "linear directions in mixture coordinates and a_t and b_t are task scalars"
    )
    checks["unattended"] = protocol["execution"] == {
        "unattended": True,
        "order": ["R1", "R2", "R3"],
        "r1_wall_clock_limit_hours": 2,
        "ledger_append_only": True,
        "slurm_only": True,
    }
    checks["five_folds"] = protocol["randomness"]["cross_validation_folds"] == 5
    checks["paired_seeds"] = protocol["randomness"]["r2_paired_seeds"] == [3406, 3407, 3408]
    checks["hellinger"] = protocol["coordinates"]["name"] == "zero-safe Hellinger"
    r1 = protocol["R1"]
    checks["nonparametric_baseline"] = (
        r1["estimators"]["nonparametric"]
        == "ExtraTreesRegressor with 500 trees, min_samples_leaf=2, max_features=1.0, deterministic protocol seed"
    )
    checks["r1_thresholds"] = r1["thresholds_in_datadecide_sigma"] == {
        "rank2_minus_best_baseline_max": 0.5,
        "rank1_minus_rank2_min": 1.0,
        "rank2_minus_rank3_max": 0.5,
    }
    r2 = protocol["R2"]
    train = r2["training_stack"]
    checks["upstream_pin"] = train["repository_commit"] == "dd9d1c3b2d7c1756b1a90f0ad7603068e9856cc6"
    checks["four_arms"] = r2["arm_count"] == len(r2["arms"]) == 4
    checks["three_seeds"] = r2["seeds_per_arm"] == len(protocol["randomness"]["r2_paired_seeds"]) == 3
    checks["job_counts"] = r2["target_job_count"] == 12 and r2["minimum_completed_job_count"] == 10
    checks["token_arithmetic"] = (
        train["sequence_length"] * train["global_batch_sequences"] * train["optimizer_steps"]
        == train["tokens_per_job"]
        == 1000341504
    )
    checks["one_gpu"] = train["gpu_per_job"] == 1 and train["walltime_hours"] == 4
    checks["thirteen_tasks"] = r2["evaluation"]["task_count"] == len(r2["evaluation"]["tasks"]) == 13
    checks["fifty_eval_batches"] = r2["evaluation"]["validation_batches_per_task"] == 50
    checks["three_attempts"] = r2["retry"]["maximum_attempts_per_arm_seed"] == 3
    checks["r3_requirements"] = len(protocol["R3"]["required"]) == 6
    markdown = args.markdown.read_text(encoding="utf-8")
    checks["markdown_protocol_id"] = "TWODIAL-E2E-V1" in markdown
    checks["markdown_traceability"] = markdown.count("scripts/check_rank2_protocol.py") >= 8
    errors = [name for name, passed in checks.items() if not passed]
    payload = {
        "id": "TWODIAL-E2E-V1-PROTOCOL-CHECK",
        "passed": not errors,
        "check_count": len(checks),
        "error_count": len(errors),
        "errors": errors,
        "checks": checks,
        "protocol_sha256": sha256(args.protocol),
        "markdown_sha256": sha256(args.markdown),
        "outcome_data_read": False,
        "gpu_jobs_submitted": 0,
        "inputs": [str(args.protocol), str(args.markdown)],
        "command": (
            "python scripts/check_rank2_protocol.py "
            f"--protocol {args.protocol} --markdown {args.markdown} --output {args.output}"
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
