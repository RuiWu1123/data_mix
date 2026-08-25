#!/usr/bin/env python3
"""Validate the final ONEDIAL-V2 Act II evidence bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


EXPECTED_PROTOCOL_SHA256 = "e7cca5e5c0e8ef7405af03f8ff9bd458c33f0bcf6a9f3278ddad65e7565f414b"
EXPECTED_MARKDOWN_SHA256 = "c936d9196cfd5f078c233fc58e2c1b022f47149306503715eae879eabc247dd1"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--q1-audit", type=Path, required=True)
    parser.add_argument("--dependencies", type=Path, required=True)
    parser.add_argument("--amendment-check", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    protocol_path = args.root / "protocol_onedial.json"
    markdown_path = args.root / "PROTOCOL_ONEDIAL.md"
    ledger = (args.root / "EXPERIMENTS.md").read_text(encoding="utf-8")
    result_markdown = (args.root / "RESULT.md").read_text(encoding="utf-8")
    blocked_markdown = (args.root / "BLOCKED.md").read_text(encoding="utf-8")
    audit = json.loads(args.q1_audit.read_text(encoding="utf-8"))
    dependencies = json.loads(args.dependencies.read_text(encoding="utf-8"))
    amendment = json.loads(args.amendment_check.read_text(encoding="utf-8"))
    errors: list[str] = []

    protocol_hash = digest(protocol_path)
    markdown_hash = digest(markdown_path)
    if protocol_hash != EXPECTED_PROTOCOL_SHA256:
        errors.append("frozen ONEDIAL-V2 protocol JSON changed")
    if markdown_hash != EXPECTED_MARKDOWN_SHA256:
        errors.append("frozen ONEDIAL-V2 protocol Markdown changed")
    if amendment.get("passed") is not True:
        errors.append("V1-to-V2 amendment proof failed")
    if amendment.get("protected_json_sections_all_unchanged") is not True:
        errors.append("protected JSON sections changed in V2")
    if audit.get("protocol_defect") is not True:
        errors.append("Q1 Holm-resolution defect is not established")
    if audit.get("impossible_design_count") != 3:
        errors.append("Q1 impossible-design count is not three")
    if audit.get("synthetic_outcomes_read") is not False:
        errors.append("Q1 synthetic-outcome quarantine failed")
    if audit.get("real_outcomes_read") is not False:
        errors.append("Q1 real-outcome quarantine failed")
    if dependencies.get("overall_verdict") != "PARTIAL":
        errors.append("overall verdict is not PARTIAL")
    if dependencies.get("question_count") != 5:
        errors.append("dependency result does not contain five questions")
    if dependencies.get("selected_coordinate_pipeline_count") != 0:
        errors.append("a coordinate pipeline was selected despite Q1 stop")
    if dependencies.get("real_outcome_table_count_read") != 0:
        errors.append("real outcomes were read after Q1 stop")
    if dependencies.get("submitted_downstream_test_job_count") != 0:
        errors.append("downstream test jobs were submitted after Q1 stop")

    for index in range(1, 6):
        identifier = f"Q{index}"
        question = dependencies.get("questions", {}).get(identifier, {})
        if question.get("verdict") != "inconclusive":
            errors.append(f"{identifier} does not have an inconclusive verdict")
        if f"ONEDIAL-V2-{identifier} INCONCLUSIVE" not in ledger:
            errors.append(f"{identifier} V2 result entry is absent")
        if f"| V2-{identifier} |" not in result_markdown:
            errors.append(f"{identifier} is absent from the V2 RESULT table")
    for identifier in ("Q2", "Q3", "Q4", "Q5"):
        if dependencies["questions"][identifier].get("dependency_state") != "inconclusive_by_Q1":
            errors.append(f"{identifier} dependency branch is wrong")

    if "## ONEDIAL-V2 Act II Verdict - PARTIAL" not in result_markdown:
        errors.append("RESULT does not declare the V2 PARTIAL verdict")
    if "B-009 ONEDIAL-V2 Q1 Holm resolution defect" not in blocked_markdown:
        errors.append("Q1 Holm defect is absent from BLOCKED")

    payload = {
        "id": "ONEDIAL-V2-FINAL-CHECK",
        "passed": not errors,
        "errors": errors,
        "overall_verdict": dependencies.get("overall_verdict"),
        "question_count": dependencies.get("question_count"),
        "inconclusive_question_count": sum(
            question.get("verdict") == "inconclusive"
            for question in dependencies.get("questions", {}).values()
        ),
        "q1_impossible_design_count": audit.get("impossible_design_count"),
        "blocked_downstream_question_count": dependencies.get("blocked_downstream_question_count"),
        "selected_coordinate_pipeline_count": dependencies.get("selected_coordinate_pipeline_count"),
        "synthetic_outcome_realization_count_read": dependencies.get(
            "synthetic_outcome_realization_count_read"
        ),
        "real_outcome_table_count_read": dependencies.get("real_outcome_table_count_read"),
        "submitted_downstream_test_job_count": dependencies.get(
            "submitted_downstream_test_job_count"
        ),
        "protocol_sha256": protocol_hash,
        "protocol_markdown_sha256": markdown_hash,
        "inputs": [
            str(protocol_path),
            str(markdown_path),
            str(args.root / "EXPERIMENTS.md"),
            str(args.root / "RESULT.md"),
            str(args.root / "BLOCKED.md"),
            str(args.q1_audit),
            str(args.dependencies),
            str(args.amendment_check),
        ],
        "command": (
            "python scripts/check_onedial_v2_final.py "
            f"--root {args.root} --q1-audit {args.q1_audit} "
            f"--dependencies {args.dependencies} --amendment-check {args.amendment_check} "
            f"--output {args.output}"
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
