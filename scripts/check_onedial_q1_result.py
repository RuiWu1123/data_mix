#!/usr/bin/env python3
"""Independently validate the ONEDIAL-V3 Q1 discovery result."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from onedial_core import leading_significant_dimension


PIPELINES = ("A", "B")
SCENARIOS = (
    "interior_rank1",
    "interior_rank2",
    "interior_rank5",
    "structural_zero_rank1",
    "structural_zero_rank2",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--shards", type=Path, required=True)
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--confirmation-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    protocol = json.loads(args.protocol.read_text(encoding="utf-8"))
    result = json.loads(args.result.read_text(encoding="utf-8"))
    q1 = protocol["questions"]["Q1"]
    protocol_hash = sha256(args.protocol)
    expected_replicates = q1["discovery"]["replicates_per_scenario"]
    designs = q1["discovery"]["olmix_designs"]
    errors: list[str] = []
    cell_summaries: dict[str, dict[str, object]] = {}
    record_count = 0
    early_stop_count = 0
    full_permutation_count = 0

    for pipeline in PIPELINES:
        for domains in designs:
            for scenario in SCENARIOS:
                key = f"{pipeline}/m{domains}/{scenario}"
                files = sorted((args.shards / pipeline / f"m{domains}" / scenario).glob("*.json"))
                records = []
                for path in files:
                    shard = json.loads(path.read_text(encoding="utf-8"))
                    if shard.get("protocol_sha256") != protocol_hash:
                        errors.append(f"{path}: protocol hash mismatch")
                    if (shard.get("phase"), shard.get("pipeline"), shard.get("domains"), shard.get("scenario")) != (
                        "discovery", pipeline, domains, scenario
                    ):
                        errors.append(f"{path}: identity mismatch")
                    records.extend(shard.get("records", []))
                replicate_ids = sorted(record.get("replicate") for record in records)
                if replicate_ids != list(range(expected_replicates)):
                    errors.append(f"{key}: replicate coverage mismatch")
                dimensions = []
                for record in records:
                    record_count += 1
                    processed = record["permutations_processed"]
                    dimension = record["significant_dimension"]
                    dimensions.append(dimension)
                    if record["stopped_early"]:
                        early_stop_count += 1
                        lower_dimension = leading_significant_dimension(record["p_value_lower_bounds"])
                        upper_dimension = leading_significant_dimension(record["p_value_upper_bounds"])
                        if lower_dimension != upper_dimension or dimension != lower_dimension:
                            errors.append(f"{key}/{record['replicate']}: invalid early-stop envelope")
                        if record["p_values"] is not None or processed >= 4999:
                            errors.append(f"{key}/{record['replicate']}: invalid early-stop metadata")
                    else:
                        full_permutation_count += 1
                        expected_p = [(1 + count) / 5000 for count in record["permutation_exceedance_counts"]]
                        if record["p_values"] != expected_p or processed != 4999:
                            errors.append(f"{key}/{record['replicate']}: invalid exact p-value metadata")
                        if dimension != leading_significant_dimension(expected_p):
                            errors.append(f"{key}/{record['replicate']}: Holm dimension mismatch")
                aggregate_cell = result.get("cells", {}).get(key)
                if aggregate_cell is None:
                    errors.append(f"{key}: missing aggregate cell")
                    continue
                expected_counts = {str(value): dimensions.count(value) for value in range(5)}
                if aggregate_cell.get("dimension_counts") != expected_counts:
                    errors.append(f"{key}: aggregate dimension counts mismatch")
                cell_summaries[key] = {
                    "record_count": len(records),
                    "passed": aggregate_cell.get("passed"),
                    "dimension_counts": expected_counts,
                }

    expected_cells = len(PIPELINES) * len(designs) * len(SCENARIOS)
    expected_records = expected_cells * expected_replicates
    if set(result.get("cells", {})) != set(cell_summaries):
        errors.append("aggregate cell key set mismatch")
    if result.get("protocol_sha256") != protocol_hash:
        errors.append("aggregate protocol hash mismatch")
    if result.get("phase") != "discovery":
        errors.append("aggregate phase mismatch")
    recomputed_pipeline_pass = {
        pipeline: all(
            summary["passed"] for key, summary in cell_summaries.items() if key.startswith(pipeline + "/")
        )
        for pipeline in PIPELINES
    }
    if result.get("pipeline_pass") != recomputed_pipeline_pass:
        errors.append("pipeline pass map mismatch")
    selected = "A" if recomputed_pipeline_pass["A"] else "B" if recomputed_pipeline_pass["B"] else None
    if result.get("selected_pipeline") != selected:
        errors.append("selected pipeline mismatch")
    expected_phase_verdict = "selected" if selected else "inconclusive"
    if result.get("phase_verdict") != expected_phase_verdict:
        errors.append("phase verdict mismatch")
    confirmation_files = list(args.confirmation_root.rglob("*.json")) if args.confirmation_root.exists() else []
    if confirmation_files:
        errors.append("confirmation artifacts exist before a discovery selection")
    if record_count != expected_records:
        errors.append("total record count mismatch")

    payload = {
        "id": "ONEDIAL-V3-Q1-RESULT-CHECK",
        "passed": not errors,
        "error_count": len(errors),
        "errors": errors,
        "protocol_sha256": protocol_hash,
        "cell_count": len(cell_summaries),
        "expected_cell_count": expected_cells,
        "synthetic_record_count": record_count,
        "expected_synthetic_record_count": expected_records,
        "early_stopped_record_count": early_stop_count,
        "full_permutation_record_count": full_permutation_count,
        "pipeline_pass": recomputed_pipeline_pass,
        "selected_pipeline": selected,
        "phase_verdict": expected_phase_verdict,
        "confirmation_artifact_count": len(confirmation_files),
        "real_outcome_table_count_read": 0,
        "inputs": [str(args.protocol), str(args.shards), str(args.result)],
        "command": (
            "python scripts/check_onedial_q1_result.py "
            f"--protocol {args.protocol} --shards {args.shards} --result {args.result} "
            f"--confirmation-root {args.confirmation_root} --output {args.output}"
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
