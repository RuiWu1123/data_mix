#!/usr/bin/env python3
"""Resolve frozen One-Dial dependency branches without reading outcome tables."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--q1-audit", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    protocol = json.loads(args.protocol.read_text(encoding="utf-8"))
    audit = json.loads(args.q1_audit.read_text(encoding="utf-8"))
    if not audit.get("protocol_defect"):
        raise SystemExit("Q1 audit does not establish the registered protocol-defect branch")
    if audit.get("outcome_data_read") is not False:
        raise SystemExit("Q1 audit outcome quarantine is not intact")

    execution_order = protocol["execution_order"]
    if execution_order != ["Q1", "Q2", "Q3", "Q4", "Q5"]:
        raise SystemExit("unexpected execution order")
    if "inconclusive" not in protocol["questions"]["Q1"]:
        raise SystemExit("Q1 has no registered inconclusive branch")

    questions = {
        "Q1": {"verdict": "inconclusive", "dependency_state": "protocol_defect"},
        **{
            identifier: {
                "verdict": "inconclusive",
                "dependency_state": "inconclusive_by_Q1",
            }
            for identifier in execution_order[1:]
        },
    }
    payload = {
        "id": "ONEDIAL-DEPENDENCY-RESOLUTION",
        "questions": questions,
        "question_count": len(questions),
        "blocked_downstream_question_count": len(execution_order) - 1,
        "selected_coordinate_pipeline_count": 0,
        "real_outcome_table_count_read": 0,
        "submitted_downstream_test_job_count": 0,
        "overall_verdict": "PARTIAL",
        "overall_rule": protocol["overall_verdict"]["PARTIAL"],
        "inputs": [str(args.protocol), str(args.q1_audit)],
        "command": (
            "python scripts/resolve_onedial_dependencies.py "
            f"--protocol {args.protocol} --q1-audit {args.q1_audit} --output {args.output}"
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
