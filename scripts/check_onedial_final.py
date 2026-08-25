#!/usr/bin/env python3
"""Validate the final One-Dial Act II evidence bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


EXPECTED_PROTOCOL_SHA256 = "43a05296625f725b091b7e0a8a2003987e23b7879cc0ac019a2f4581f11bf494"
EXPECTED_PROTOCOL_MARKDOWN_SHA256 = "10ec812d2feebdb33a336a819c62fcdc550e6bb2ddeb221ebbecc59d98a34659"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--q1-audit", type=Path, required=True)
    parser.add_argument("--dependencies", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    protocol_path = args.root / "protocol_onedial.json"
    protocol_markdown_path = args.root / "PROTOCOL_ONEDIAL.md"
    ledger = (args.root / "EXPERIMENTS.md").read_text(encoding="utf-8")
    result_markdown = (args.root / "RESULT.md").read_text(encoding="utf-8")
    blocked_markdown = (args.root / "BLOCKED.md").read_text(encoding="utf-8")
    audit = json.loads(args.q1_audit.read_text(encoding="utf-8"))
    dependencies = json.loads(args.dependencies.read_text(encoding="utf-8"))
    errors: list[str] = []

    protocol_hash = sha256(protocol_path)
    protocol_markdown_hash = sha256(protocol_markdown_path)
    if protocol_hash != EXPECTED_PROTOCOL_SHA256:
        errors.append("frozen protocol JSON changed after Act I")
    if protocol_markdown_hash != EXPECTED_PROTOCOL_MARKDOWN_SHA256:
        errors.append("frozen protocol Markdown changed after Act I")
    if audit.get("protocol_defect") is not True:
        errors.append("Q1 protocol defect is not established")
    if audit.get("outcome_data_read") is not False:
        errors.append("Q1 outcome quarantine failed")
    if dependencies.get("overall_verdict") != "PARTIAL":
        errors.append("overall verdict is not PARTIAL")
    if dependencies.get("question_count") != 5:
        errors.append("dependency result does not contain five questions")
    if dependencies.get("real_outcome_table_count_read") != 0:
        errors.append("real outcomes were read after Q1 stopped")
    if dependencies.get("submitted_downstream_test_job_count") != 0:
        errors.append("downstream jobs were submitted after Q1 stopped")

    for index in range(1, 6):
        identifier = f"Q{index}"
        question = dependencies.get("questions", {}).get(identifier, {})
        if question.get("verdict") != "inconclusive":
            errors.append(f"{identifier} does not have an inconclusive verdict")
        if f"ONEDIAL-{identifier} PREREGISTRATION" not in ledger:
            errors.append(f"{identifier} preregistration is absent")
        if f"ONEDIAL-{identifier} INCONCLUSIVE" not in ledger:
            errors.append(f"{identifier} result entry is absent")
        if f"| {identifier} |" not in result_markdown:
            errors.append(f"{identifier} is absent from RESULT table")
    for identifier in ("Q2", "Q3", "Q4", "Q5"):
        if dependencies["questions"][identifier].get("dependency_state") != "inconclusive_by_Q1":
            errors.append(f"{identifier} dependency branch is wrong")

    if "## One-Dial Act II Verdict - PARTIAL" not in result_markdown:
        errors.append("RESULT does not declare the One-Dial PARTIAL verdict")
    if "B-008 One-Dial Q1 interior-DGP protocol defect" not in blocked_markdown:
        errors.append("Q1 protocol defect is absent from BLOCKED")

    payload = {
        "id": "ONEDIAL-FINAL-CHECK",
        "passed": not errors,
        "errors": errors,
        "overall_verdict": dependencies.get("overall_verdict"),
        "question_count": dependencies.get("question_count"),
        "inconclusive_question_count": sum(
            question.get("verdict") == "inconclusive"
            for question in dependencies.get("questions", {}).values()
        ),
        "blocked_downstream_question_count": dependencies.get("blocked_downstream_question_count"),
        "real_outcome_table_count_read": dependencies.get("real_outcome_table_count_read"),
        "submitted_downstream_test_job_count": dependencies.get("submitted_downstream_test_job_count"),
        "protocol_sha256": protocol_hash,
        "protocol_markdown_sha256": protocol_markdown_hash,
        "inputs": [
            str(protocol_path),
            str(protocol_markdown_path),
            str(args.root / "EXPERIMENTS.md"),
            str(args.root / "RESULT.md"),
            str(args.root / "BLOCKED.md"),
            str(args.q1_audit),
            str(args.dependencies),
        ],
        "command": (
            "python scripts/check_onedial_final.py "
            f"--root {args.root} --q1-audit {args.q1_audit} "
            f"--dependencies {args.dependencies} --output {args.output}"
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
