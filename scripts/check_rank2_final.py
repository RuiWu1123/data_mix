#!/usr/bin/env python3
"""Validate the final TWODIAL-E2E-V1 R1-R3 bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--r1", type=Path, required=True)
    parser.add_argument("--r1-check", type=Path, required=True)
    parser.add_argument("--r2", type=Path, required=True)
    parser.add_argument("--r2-check", type=Path, required=True)
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    protocol = json.loads(args.protocol.read_text(encoding="utf-8"))
    r1 = json.loads(args.r1.read_text(encoding="utf-8"))
    r1_check = json.loads(args.r1_check.read_text(encoding="utf-8"))
    r2 = json.loads(args.r2.read_text(encoding="utf-8"))
    r2_check = json.loads(args.r2_check.read_text(encoding="utf-8"))
    ledger = args.ledger.read_text(encoding="utf-8")
    result = args.result.read_text(encoding="utf-8")
    checks: dict[str, bool] = {}
    checks["protocol"] = protocol["protocol_id"] == "TWODIAL-E2E-V1"
    checks["r1_audited"] = r1_check["passed"] and r1_check["independent_verdict"] == r1["verdict"]
    checks["r2_audited"] = r2_check["passed"] and r2_check["independent_verdict"] == r2["verdict"]
    checks["completion_gate"] = r2["completed_jobs"] >= protocol["R2"]["minimum_completed_job_count"]
    checks["all_arms_reported"] = set(r2["arm_completed_counts"]) == set(protocol["R2"]["arms"])
    checks["r1_plot"] = Path(r1["plot"]).is_file()
    checks["r2_plot"] = r2["plot"] is not None and Path(r2["plot"]).is_file()
    checks["r2_csv"] = Path(r2["csv"]).is_file()
    checks["ledger_r1"] = "TWODIAL-E2E-V1 R1 RANK SELECTION" in ledger
    checks["ledger_r2"] = "TWODIAL-E2E-V1 R2 GPU" in ledger
    checks["result_table"] = "| Arm | Seed |" in result
    checks["result_r1"] = "Held-out error vs rank" in result
    checks["result_r2"] = "GPU duel" in result
    checks["upgrade"] = "Minimum upgrade" in result
    match = re.search(r"<!-- RANK2_CONCLUSION_START -->(.*?)<!-- RANK2_CONCLUSION_END -->", result, re.S)
    conclusion_words = len(match.group(1).split()) if match else 10**9
    checks["conclusion_present"] = match is not None
    checks["conclusion_word_limit"] = conclusion_words <= 200
    failures = sorted(name for name, passed in checks.items() if not passed)
    payload = {
        "id": "TWODIAL-E2E-V1-FINAL-CHECK",
        "passed": not failures,
        "checks_passed": sum(checks.values()),
        "checks_total": len(checks),
        "failures": failures,
        "r1_verdict": r1["verdict"],
        "r2_verdict": r2["verdict"],
        "completed_gpu_jobs": r2["completed_jobs"],
        "conclusion_words": conclusion_words,
        "protocol_sha256": sha256(args.protocol),
        "r1_sha256": sha256(args.r1),
        "r2_sha256": sha256(args.r2),
        "result_sha256": sha256(args.result),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
