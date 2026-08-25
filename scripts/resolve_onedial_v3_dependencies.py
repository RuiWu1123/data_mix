#!/usr/bin/env python3
"""Resolve ONEDIAL-V3 downstream branches after Q1 discovery."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--q1-result", type=Path, required=True)
    parser.add_argument("--q1-check", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    protocol = json.loads(args.protocol.read_text(encoding="utf-8"))
    q1_result = json.loads(args.q1_result.read_text(encoding="utf-8"))
    q1_check = json.loads(args.q1_check.read_text(encoding="utf-8"))
    if protocol.get("protocol_id") != "ONEDIAL-V3":
        raise SystemExit("dependency resolver requires ONEDIAL-V3")
    if not q1_check.get("passed") or q1_check.get("phase_verdict") != "inconclusive":
        raise SystemExit("Q1 result check does not establish an inconclusive discovery")
    if q1_result.get("selected_pipeline") is not None:
        raise SystemExit("a selected pipeline requires confirmation rather than the death branch")
    if q1_check.get("confirmation_artifact_count") != 0:
        raise SystemExit("confirmation quarantine is not intact")
    if q1_check.get("real_outcome_table_count_read") != 0:
        raise SystemExit("real-outcome quarantine is not intact")
    execution_order = protocol["execution_order"]
    if execution_order != ["Q1", "Q2", "Q3", "Q4", "Q5"]:
        raise SystemExit("unexpected execution order")

    questions = {
        "Q1": {"verdict": "inconclusive", "dependency_state": "no_discovery_pipeline_passed"},
        **{
            identifier: {"verdict": "inconclusive", "dependency_state": "inconclusive_by_Q1"}
            for identifier in execution_order[1:]
        },
    }
    payload = {
        "id": "ONEDIAL-V3-DEPENDENCY-RESOLUTION",
        "protocol_id": protocol["protocol_id"],
        "questions": questions,
        "question_count": len(questions),
        "blocked_downstream_question_count": len(execution_order) - 1,
        "q1_synthetic_record_count": q1_check["synthetic_record_count"],
        "selected_coordinate_pipeline_count": 0,
        "confirmation_synthetic_record_count_read": 0,
        "real_outcome_table_count_read": 0,
        "submitted_downstream_test_job_count": 0,
        "overall_verdict": "PARTIAL",
        "overall_rule": protocol["overall_verdict"]["PARTIAL"],
        "inputs": [str(args.protocol), str(args.q1_result), str(args.q1_check)],
        "command": (
            "python scripts/resolve_onedial_v3_dependencies.py "
            f"--protocol {args.protocol} --q1-result {args.q1_result} "
            f"--q1-check {args.q1_check} --output {args.output}"
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
