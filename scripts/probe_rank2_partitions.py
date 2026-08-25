#!/usr/bin/env python3
"""Record a fresh Slurm partition snapshot and choose the R2 partition."""

from __future__ import annotations

import argparse
import json
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


PARTITIONS = ("mi2101x", "mi2104x")
REGISTERED_RUNTIME_HOURS = 4.0


def capture(command: list[str]) -> str:
    return subprocess.run(command, check=True, text=True, capture_output=True).stdout


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    snapshots = {}
    for partition in PARTITIONS:
        states = Counter(
            line.strip().lower()
            for line in capture(["sinfo", "-h", "-p", partition, "-o", "%T"]).splitlines()
            if line.strip()
        )
        queue_states = Counter(
            line.strip()
            for line in capture(["squeue", "-h", "-p", partition, "-o", "%t"]).splitlines()
            if line.strip()
        )
        idle = states.get("idle", 0)
        total = sum(states.values())
        pending = queue_states.get("PD", 0)
        estimated_wait = 0.0 if idle > 0 else REGISTERED_RUNTIME_HOURS * pending / max(total, 1)
        snapshots[partition] = {
            "node_states": dict(sorted(states.items())),
            "node_count": total,
            "idle_nodes": idle,
            "queue_states": dict(sorted(queue_states.items())),
            "pending_jobs": pending,
            "estimated_wait_hours": estimated_wait,
            "estimated_completion_hours": estimated_wait + REGISTERED_RUNTIME_HOURS,
            "compatibility": "native MI210 target for torch 2.7.1+rocm6.3",
        }
    selected = min(
        PARTITIONS,
        key=lambda name: (
            snapshots[name]["estimated_completion_hours"],
            -snapshots[name]["idle_nodes"],
            name,
        ),
    )
    payload = {
        "id": "TWODIAL-E2E-V1-R2-PARTITION-PROBE",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "registered_runtime_hours": REGISTERED_RUNTIME_HOURS,
        "partitions": snapshots,
        "selected_partition": selected,
        "selection_rule": "minimum estimated wait plus registered runtime; break ties by more idle nodes then name",
        "commands": [
            "sinfo -h -p <partition> -o %T",
            "squeue -h -p <partition> -o %t",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
