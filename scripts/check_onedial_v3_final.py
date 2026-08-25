#!/usr/bin/env python3
"""Validate the final ONEDIAL-V3 Act II evidence bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


EXPECTED_PROTOCOL_SHA256 = "b8dc548618f38a74b00ca8027a7ca519ffa4e6fa0ecfdb7bee84a3d7a1b08791"
EXPECTED_PROTOCOL_MARKDOWN_SHA256 = "5ce9b2d0a6cbfe1d29ab78b124ac0497c322da3f6ba802d45417f2cba7d9a8bc"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--q1-result", type=Path, required=True)
    parser.add_argument("--q1-check", type=Path, required=True)
    parser.add_argument("--dependencies", type=Path, required=True)
    parser.add_argument("--confirmation-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    protocol_path = args.root / "protocol_onedial.json"
    protocol_markdown_path = args.root / "PROTOCOL_ONEDIAL.md"
    ledger = (args.root / "EXPERIMENTS.md").read_text(encoding="utf-8")
    result_markdown = (args.root / "RESULT.md").read_text(encoding="utf-8")
    q1_result = json.loads(args.q1_result.read_text(encoding="utf-8"))
    q1_check = json.loads(args.q1_check.read_text(encoding="utf-8"))
    dependencies = json.loads(args.dependencies.read_text(encoding="utf-8"))
    errors: list[str] = []

    protocol_hash = sha256(protocol_path)
    protocol_markdown_hash = sha256(protocol_markdown_path)
    if protocol_hash != EXPECTED_PROTOCOL_SHA256:
        errors.append("frozen V3 protocol JSON changed after Act I")
    if protocol_markdown_hash != EXPECTED_PROTOCOL_MARKDOWN_SHA256:
        errors.append("frozen V3 protocol Markdown changed after Act I")
    if not q1_check.get("passed") or q1_check.get("error_count") != 0:
        errors.append("Q1 result check did not pass cleanly")
    if q1_check.get("cell_count") != 20 or q1_check.get("synthetic_record_count") != 4000:
        errors.append("Q1 cell or record count is wrong")
    if q1_check.get("early_stopped_record_count") + q1_check.get("full_permutation_record_count") != 4000:
        errors.append("Q1 permutation execution accounting is incomplete")
    if q1_result.get("pipeline_pass") != {"A": False, "B": False}:
        errors.append("Q1 pipeline pass map is wrong")
    if q1_result.get("selected_pipeline") is not None or q1_result.get("phase_verdict") != "inconclusive":
        errors.append("Q1 selector or phase verdict is wrong")
    expected_q1_metrics = {
        "A/m6/interior_rank2": (0.04, 0.433393536937634),
        "A/m12/interior_rank2": (0.0, 0.2349996645103392),
        "B/m6/interior_rank2": (0.04, 0.4368551768695305),
        "B/m12/interior_rank2": (0.005, 0.21279398132653693),
    }
    for key, (rate, cosine) in expected_q1_metrics.items():
        cell = q1_result.get("cells", {}).get(key, {})
        if cell.get("rate") != rate or cell.get("h_cosine_median") != cosine:
            errors.append(f"{key} result changed")

    if dependencies.get("protocol_id") != "ONEDIAL-V3":
        errors.append("dependency artifact has wrong protocol ID")
    if dependencies.get("overall_verdict") != "PARTIAL":
        errors.append("overall verdict is not PARTIAL")
    if dependencies.get("question_count") != 5:
        errors.append("dependency result does not contain five questions")
    if dependencies.get("selected_coordinate_pipeline_count") != 0:
        errors.append("dependency result selected a coordinate pipeline")
    if dependencies.get("confirmation_synthetic_record_count_read") != 0:
        errors.append("Q1 confirmation was read")
    if dependencies.get("real_outcome_table_count_read") != 0:
        errors.append("real outcomes were read after Q1 stopped")
    if dependencies.get("submitted_downstream_test_job_count") != 0:
        errors.append("downstream scientific jobs were submitted after Q1 stopped")
    confirmation_files = list(args.confirmation_root.rglob("*.json")) if args.confirmation_root.exists() else []
    if confirmation_files:
        errors.append("Q1 confirmation artifacts exist")

    ledger_markers = [
        "## ONEDIAL-V3-Q1 INCONCLUSIVE",
        "## ONEDIAL-V3-Q2 INCONCLUSIVE_BY_Q1",
        "## ONEDIAL-V3-Q3 INCONCLUSIVE_BY_Q1",
        "## ONEDIAL-V3-Q4 INCONCLUSIVE_BY_Q1",
        "## ONEDIAL-V3-Q5 INCONCLUSIVE_BY_Q1",
    ]
    ledger_positions = [ledger.find(marker) for marker in ledger_markers]
    if any(position < 0 for position in ledger_positions):
        errors.append("one or more V3 ledger entries are absent")
    elif ledger_positions != sorted(ledger_positions) or len(set(ledger_positions)) != 5:
        errors.append("V3 ledger entries are out of Q1-to-Q5 order")
    for index in range(1, 6):
        identifier = f"Q{index}"
        question = dependencies.get("questions", {}).get(identifier, {})
        if question.get("verdict") != "inconclusive":
            errors.append(f"{identifier} does not have an inconclusive verdict")
        if index > 1 and question.get("dependency_state") != "inconclusive_by_Q1":
            errors.append(f"{identifier} dependency branch is wrong")
        if f"| V3-{identifier} |" not in result_markdown:
            errors.append(f"V3-{identifier} is absent from RESULT table")
    if "## ONEDIAL-V3 Act II Verdict - PARTIAL" not in result_markdown:
        errors.append("RESULT does not declare the V3 PARTIAL verdict")

    payload = {
        "id": "ONEDIAL-V3-FINAL-CHECK",
        "passed": not errors,
        "error_count": len(errors),
        "errors": errors,
        "overall_verdict": dependencies.get("overall_verdict"),
        "question_count": dependencies.get("question_count"),
        "inconclusive_question_count": sum(
            question.get("verdict") == "inconclusive"
            for question in dependencies.get("questions", {}).values()
        ),
        "blocked_downstream_question_count": dependencies.get("blocked_downstream_question_count"),
        "q1_cell_count": q1_check.get("cell_count"),
        "q1_synthetic_record_count": q1_check.get("synthetic_record_count"),
        "q1_early_stopped_record_count": q1_check.get("early_stopped_record_count"),
        "q1_full_permutation_record_count": q1_check.get("full_permutation_record_count"),
        "selected_coordinate_pipeline_count": dependencies.get("selected_coordinate_pipeline_count"),
        "confirmation_artifact_count": len(confirmation_files),
        "real_outcome_table_count_read": dependencies.get("real_outcome_table_count_read"),
        "submitted_downstream_test_job_count": dependencies.get("submitted_downstream_test_job_count"),
        "gpu_count": 0,
        "gpu_node_hours": 0,
        "protocol_sha256": protocol_hash,
        "protocol_markdown_sha256": protocol_markdown_hash,
        "ledger_question_positions": ledger_positions,
        "inputs": [
            str(protocol_path),
            str(protocol_markdown_path),
            str(args.root / "EXPERIMENTS.md"),
            str(args.root / "RESULT.md"),
            str(args.q1_result),
            str(args.q1_check),
            str(args.dependencies),
        ],
        "command": (
            "python scripts/check_onedial_v3_final.py "
            f"--root {args.root} --q1-result {args.q1_result} --q1-check {args.q1_check} "
            f"--dependencies {args.dependencies} --confirmation-root {args.confirmation_root} "
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
