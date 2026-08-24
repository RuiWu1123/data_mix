#!/usr/bin/env python3
"""Validate the final autonomous data-mixing evidence bundle."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


REQUIRED_DOCUMENTS = (
    "PLAN.md",
    "ASSUMPTIONS.md",
    "EXPERIMENTS.md",
    "PROPOSALS.md",
    "RESULT.md",
    "BLOCKED.md",
)
ALLOWED_VERDICTS = {"supported", "falsified", "inconclusive"}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    summary = json.loads(args.summary.read_text(encoding="utf-8"))
    ledger = (args.root / "EXPERIMENTS.md").read_text(encoding="utf-8")
    result_markdown = (args.root / "RESULT.md").read_text(encoding="utf-8")
    errors: list[str] = []

    missing_documents = [name for name in REQUIRED_DOCUMENTS if not (args.root / name).is_file()]
    if missing_documents:
        errors.append(f"missing required documents: {missing_documents}")

    records = summary["records"]
    protocol = json.loads((args.root / "protocol.json").read_text(encoding="utf-8"))
    if not summary["quotas"]["passed"]:
        errors.append("structured completion quotas failed")
    if len(records) < protocol["minimum_completed_hypotheses"]:
        errors.append("too few completed hypotheses")
    if summary["literature_addition_count"] > summary["literature_addition_cap"]:
        errors.append("literature expansion cap exceeded")

    supported_ids = []
    closed_ids = []
    for record in records:
        identifier = record["id"]
        verdict = record["verdict"]
        line_status = record.get("line_status", "active")
        evidence = Path(record["evidence"])
        if verdict not in ALLOWED_VERDICTS:
            errors.append(f"{identifier}: invalid verdict {verdict}")
        if not evidence.is_file():
            errors.append(f"{identifier}: missing result evidence {evidence}")
        if f"## {identifier} v1" not in ledger or "PREREGISTERED" not in ledger:
            errors.append(f"{identifier}: preregistration not found in ledger")
        if identifier not in result_markdown:
            errors.append(f"{identifier}: absent from final verdict table")
        if verdict == "supported":
            supported_ids.append(identifier)
            if record["supported_effect_sigma"] == "not_applicable":
                errors.append(f"{identifier}: supported effect is missing")
            if line_status == "closed":
                closed_ids.append(identifier)
                if record["next_minimum_upgrade"] is not None:
                    errors.append(f"{identifier}: closed line retains an upgrade")
                if f"CLOSED FINDING — {identifier}" not in result_markdown:
                    errors.append(f"{identifier}: closed-finding marker is missing")
            else:
                if record["next_minimum_upgrade"] is None:
                    errors.append(f"{identifier}: next minimum upgrade is missing")
                if f"CANDIDATE FINDING — {identifier}" not in result_markdown:
                    errors.append(f"{identifier}: candidate-finding marker is missing")

    payload = {
        "passed": not errors,
        "errors": errors,
        "required_document_count": len(REQUIRED_DOCUMENTS),
        "completed_record_count": len(records),
        "supported_ids": supported_ids,
        "supported_count": len(supported_ids),
        "closed_ids": closed_ids,
        "closed_count": len(closed_ids),
        "literature_addition_count": summary["literature_addition_count"],
        "literature_addition_cap": summary["literature_addition_cap"],
        "quota_snapshot": summary["quotas"],
        "inputs": [
            str(args.summary),
            "protocol.json",
            *REQUIRED_DOCUMENTS,
            *[record["evidence"] for record in records],
        ],
        "command": (
            f"python scripts/check_final.py --root {args.root} "
            f"--summary {args.summary} --output {args.output}"
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
