#!/usr/bin/env python3
"""Build the traceable TWODIAL-E2E-V1 R3 reporting tables."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--r1", type=Path, required=True)
    parser.add_argument("--r2", type=Path, required=True)
    parser.add_argument("--r2-check", type=Path, required=True)
    parser.add_argument("--csv", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    r1 = json.loads(args.r1.read_text(encoding="utf-8"))
    r2 = json.loads(args.r2.read_text(encoding="utf-8"))
    r2_check = json.loads(args.r2_check.read_text(encoding="utf-8"))
    frame = pd.read_csv(args.csv)
    complete = frame[frame["status"] == "complete"].copy()
    task_names = [column.removeprefix("bpb/") for column in complete.columns if column.startswith("bpb/")]
    complete["mean_bpb"] = complete[[f"bpb/{task}" for task in task_names]].mean(axis=1)
    run_columns = ["arm", "seed", "optimizer_steps", "training_tokens", "aggregate_standardized_loss", "mean_bpb"]
    arm_means = {}
    for arm, group in complete.groupby("arm", sort=True):
        arm_means[str(arm)] = {
            "aggregate_standardized_loss": float(group["aggregate_standardized_loss"].mean()),
            "mean_bpb": float(group["mean_bpb"].mean()),
            "task_mean_bpb": {
                task: float(group[f"bpb/{task}"].mean())
                for task in task_names
            },
        }
    successful_hours = sum(
        float(job["gpu_node_hours"])
        for job in r2["jobs"]
        if job["state"] == "COMPLETED"
    )
    failed_hours = sum(
        float(job["gpu_node_hours"])
        for job in r2["jobs"]
        if job["state"] == "FAILED"
    )
    payload = {
        "id": "TWODIAL-E2E-V1-R3-SUMMARY",
        "r1": {
            "verdict": r1["verdict"],
            "selected_rank": r1["selected_rank_for_r2"],
            "datadecide_seed_noise_floor": r1["datadecide_seed_noise_floor"],
            "source_curves": r1["source_summaries"],
        },
        "r2": {
            "verdict": r2["verdict"],
            "completed_jobs": r2["completed_jobs"],
            "arm_completed_counts": r2["arm_completed_counts"],
            "runs": complete[run_columns].sort_values(["arm", "seed"]).to_dict(orient="records"),
            "arm_means": arm_means,
            "contrasts": r2["contrasts"],
            "direction": r2["direction"],
            "power_rule_triggered": r2["power_rule_triggered"],
            "accounting": {
                "successful_gpu_node_hours": successful_hours,
                "failed_gpu_node_hours": failed_hours,
                "total_gpu_node_hours": r2["gpu_node_hours"],
                "successful_job_records": sum(job["state"] == "COMPLETED" for job in r2["jobs"]),
                "failed_job_records": sum(job["state"] == "FAILED" for job in r2["jobs"]),
            },
        },
        "independent_check": r2_check,
        "input_sha256": {
            str(args.r1): sha256(args.r1),
            str(args.r2): sha256(args.r2),
            str(args.r2_check): sha256(args.r2_check),
            str(args.csv): sha256(args.csv),
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
