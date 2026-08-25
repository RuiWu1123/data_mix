#!/usr/bin/env python3
"""Statically validate the frozen One-Dial Act I preregistration."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


QUESTION_IDS = tuple(f"Q{index}" for index in range(1, 6))


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fail_if(condition: bool, message: str, errors: list[str]) -> None:
    if condition:
        errors.append(message)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--markdown", type=Path, required=True)
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    protocol = json.loads(args.protocol.read_text(encoding="utf-8"))
    markdown = args.markdown.read_text(encoding="utf-8")
    ledger = args.ledger.read_text(encoding="utf-8")
    errors: list[str] = []

    fail_if(protocol.get("protocol_id") != "ONEDIAL-V3", "wrong protocol id", errors)
    compute = protocol.get("compute", {})
    fail_if(compute.get("level") != "L0", "compute level is not L0", errors)
    fail_if(compute.get("gpu_count") != 0, "GPU count is not zero", errors)
    fail_if(compute.get("gpu_node_hours") != 0, "GPU node-hours are not zero", errors)
    fail_if(not compute.get("slurm_batch_only"), "Slurm-only flag is false", errors)

    randomness = protocol.get("randomness", {})
    fail_if(randomness.get("bootstrap_layers") != 1, "bootstrap is not single-layer", errors)
    fail_if(randomness.get("nested_bootstrap") is not False, "nested bootstrap is enabled", errors)
    fail_if(randomness.get("bootstrap_replicates", 0) < 1000, "too few bootstraps", errors)
    fail_if(randomness.get("permutation_replicates") != 4999, "permutation count is not 4999", errors)
    estimator = protocol.get("common_estimator", {})
    fail_if("Holm" not in estimator.get("significant_residual_dimension", ""), "Holm dimension rule missing", errors)
    fail_if("first 4" not in estimator.get("significant_residual_dimension", ""), "Holm family is not the first four directions", errors)
    fail_if("12.5" not in estimator.get("significant_residual_dimension", ""), "Holm resolution margin missing", errors)
    fail_if("no result of a bootstrap replicate is bootstrapped again" not in estimator.get("bootstrap_alignment", ""), "single-layer bootstrap implementation missing", errors)

    questions = protocol.get("questions", {})
    fail_if(tuple(questions) != QUESTION_IDS, "questions are not exactly Q1-Q5 in order", errors)
    for identifier in QUESTION_IDS:
        question = questions.get(identifier, {})
        for field in ("title", "discovery", "confirmation", "support", "falsify", "inconclusive"):
            fail_if(field not in question, f"{identifier}: missing {field}", errors)
        fail_if(question.get("discovery") == question.get("confirmation"), f"{identifier}: discovery equals confirmation", errors)
        fail_if(f"## {identifier}" not in markdown, f"{identifier}: markdown section missing", errors)
        fail_if(f"## ONEDIAL-{identifier} PREREGISTRATION" not in ledger, f"{identifier}: ledger preregistration missing", errors)

    q1 = questions.get("Q1", {})
    fail_if(q1.get("confirmation", {}).get("replicates_per_scenario", 0) <= q1.get("discovery", {}).get("replicates_per_scenario", 0), "Q1 confirmation is not larger", errors)
    fail_if(len(q1.get("truth", {}).get("scenarios", [])) != 5, "Q1 does not have five truth scenarios", errors)
    fail_if("structural_zero_rank1" not in q1.get("truth", {}).get("scenarios", []), "Q1 zero null missing", errors)
    fail_if("structural_zero_rank2" not in q1.get("truth", {}).get("scenarios", []), "Q1 zero signal missing", errors)
    fail_if("Q2 permutation" not in q1.get("detector", ""), "Q1 detector differs from Q2", errors)
    interior_generator = q1.get("truth", {}).get("interior_weight_generator", {})
    fail_if(interior_generator.get("distribution") != "symmetric_dirichlet", "Q1 interior distribution mismatch", errors)
    fail_if(interior_generator.get("alpha") != 1.0, "Q1 interior alpha mismatch", errors)
    fail_if(interior_generator.get("alpha_vector") != "ones(m)", "Q1 interior alpha vector mismatch", errors)
    fail_if("finite weight-row count n_m" not in interior_generator.get("row_count", ""), "Q1 interior row matching missing", errors)
    fail_if("fresh independent n_m-by-m matrix" not in interior_generator.get("draw_scope", ""), "Q1 interior independence missing", errors)
    fail_if("ONEDIAL-V2:Q1-interior-weights:" not in interior_generator.get("seed_rule", ""), "Q1 interior seed rule mismatch", errors)
    fail_if("unmodified design" not in q1.get("truth", {}).get("structural_zero_generator", ""), "Q1 structural-zero design changed", errors)

    q2_support = questions.get("Q2", {}).get("support", {})
    fail_if(q2_support.get("significant_residual_dimension_min") != 1, "Q2 lower dimension is not one", errors)
    fail_if(q2_support.get("significant_residual_dimension_max") != 3, "Q2 upper dimension is not three", errors)
    fail_if("agent_added_exact_one" not in questions.get("Q2", {}), "Q2 exact-one audit missing", errors)

    q3 = questions.get("Q3", {})
    fail_if(len(q3.get("exact_task_bridge", [])) != 8, "Q3 exact bridge size is not eight", errors)
    fail_if(len(q3.get("macro_target_bridge", {}).get("names", [])) != 5, "Q3 macro bridge size is not five", errors)
    fail_if("correct_prob_per_char" not in q3.get("data_transforms", {}).get("datadecide_tasks", ""), "Q3 task metric is not frozen", errors)

    q4 = questions.get("Q4", {})
    fail_if(q4.get("validation_objectives", {}).get("total") != 512, "Q4 objective count is not 512", errors)
    fail_if(q4.get("support", {}).get("shuffle_p_max", 1) > 0.01, "Q4 shuffle threshold is too weak", errors)
    fail_if("shuffle_control" not in q4, "Q4 shuffle control missing", errors)

    q5 = questions.get("Q5", {})
    fail_if(q5.get("discovery", {}).get("onedial_budget") != 26, "Q5 discovery budget mismatch", errors)
    fail_if(q5.get("confirmation", {}).get("onedial_budget") != 50, "Q5 confirmation budget mismatch", errors)
    fail_if("agent_added_attribution_control" not in q5, "Q5 attribution control missing", errors)

    for label in ("SURVIVED", "PARTIAL", "KILLED"):
        fail_if(label not in protocol.get("overall_verdict", {}), f"overall verdict {label} missing", errors)
    feasibility = protocol.get("act1_static_feasibility_audit", {})
    fail_if(feasibility.get("required_before_freeze") is not True, "Act I feasibility audit is not mandatory", errors)
    fail_if(len(feasibility.get("constraint_pair_categories", [])) != 3, "Act I feasibility categories are incomplete", errors)
    feasibility_path = args.root / feasibility.get("artifact", "missing")
    if not feasibility_path.is_file():
        errors.append("Act I feasibility artifact is missing")
        feasibility_result = {}
    else:
        feasibility_result = json.loads(feasibility_path.read_text(encoding="utf-8"))
        fail_if(feasibility_result.get("passed") is not True, "Act I feasibility audit failed", errors)
        fail_if(feasibility_result.get("failed_constraint_count") != 0, "Act I feasibility audit has failed pairs", errors)
        fail_if(feasibility_result.get("constraint_category_count") != 3, "Act I feasibility result omitted a category", errors)
    fail_if(markdown.count("[agent-added]") < 5, "fewer than five agent-added checks", errors)
    fail_if("Second-act execution status: NOT AUTHORIZED" not in markdown, "execution pause marker missing", errors)

    result_paths = [args.root / "artifacts" / "onedial" / f"{identifier}_result.json" for identifier in QUESTION_IDS]
    preexisting_results = [str(path) for path in result_paths if path.exists()]
    fail_if(bool(preexisting_results), "One-Dial outcome artifacts exist before Act II", errors)

    payload = {
        "protocol_id": protocol.get("protocol_id"),
        "passed": not errors,
        "errors": errors,
        "question_count": len(questions),
        "agent_added_check_count": markdown.count("[agent-added]"),
        "bootstrap_layers": randomness.get("bootstrap_layers"),
        "nested_bootstrap": randomness.get("nested_bootstrap"),
        "gpu_count": compute.get("gpu_count"),
        "preexisting_outcome_artifact_count": len(preexisting_results),
        "feasibility_constraint_pair_count": feasibility_result.get("constraint_pair_count"),
        "feasibility_failed_constraint_count": feasibility_result.get("failed_constraint_count"),
        "feasibility_constraint_category_count": feasibility_result.get("constraint_category_count"),
        "protocol_sha256": digest(args.protocol),
        "markdown_sha256": digest(args.markdown),
        "ledger_sha256": digest(args.ledger),
        "inputs": [str(args.protocol), str(args.markdown), str(args.ledger), str(feasibility_path)],
        "command": (
            f"python scripts/check_onedial_protocol.py --root {args.root} "
            f"--protocol {args.protocol} --markdown {args.markdown} "
            f"--ledger {args.ledger} --output {args.output}"
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
