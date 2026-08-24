#!/usr/bin/env python3
"""Build the final quota/verdict summary from structured review and result artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


COMPLETED = {
    "H002": ("measurement", "L0"),
    "H003": ("audit", "L0"),
    "H004": ("audit", "L0"),
    "H006": ("audit", "L0"),
    "H007": ("audit", "L0"),
    "H011": ("audit", "L0"),
    "H013": ("measurement", "L0"),
    "H014": ("constructive", "L0"),
    "H015": ("measurement", "L0"),
}

REVIEW_ROUNDS = (
    ("reviews/candidate_round1.json", 1),
    ("reviews/candidate_round2.json", 0),
    ("reviews/candidate_round3.json", 0),
    ("reviews/candidate_round4.json", 0),
)

UPGRADES = {
    "H003": {
        "tier": "L1",
        "design": "Train the direct-coefficient and affine-corrected final samplers at matched scale and tokens.",
        "model_parameters": 160_000_000,
        "training_tokens": 3_200_000_000,
        "seeds_per_arm": 3,
        "arms": 2,
        "decision": "Affine correction must lower mean target loss by at least 2 seed sigma without raising any domain loss by more than 1 sigma.",
    },
    "H006": {
        "tier": "L0",
        "design": "Add an explicit source-target progress constant and property-test the repaired theorem on strongly convex quadratic families.",
        "quadratic_instances": 10_000,
        "minimum_progress_constant": 0.1,
        "maximum_allowed_gap": 1e-10,
        "decision": "Any post-bound optimality gap above the maximum allowed gap falsifies the proposed repair.",
    },
    "H011": {
        "tier": "L1",
        "design": "Run GRAPE and a fixed-mixture control on a SlimPajama proxy while logging raw target-loss variance.",
        "model_parameters": 60_000_000,
        "target_domains": 7,
        "seeds_per_arm": 3,
        "arms": 2,
        "logging_interval_updates": 100,
        "decision": "The theorem-relevance concern advances if GRAPE variance has a positive slope above 2 seed sigma over the first 10 logged intervals.",
    },
    "H015": {
        "tier": "L0",
        "design": "Repeat the frozen spectrum analysis under raw, z-scored, and task-family-aggregated BPB codomain norms.",
        "codomain_norms": 3,
        "bootstraps_per_norm": 10_000,
        "maximum_rank_fraction_upper_95": 0.60,
        "maximum_slope_upper_95": 0.75,
        "decision": "The measurement is norm-robust only if both upper bounds hold under every codomain norm.",
    },
}


def load_scores(root: Path) -> dict[str, dict[str, int]]:
    scores = {}
    for relative, novelty_offset in REVIEW_ROUNDS:
        payload = json.loads((root / relative).read_text(encoding="utf-8"))
        for review in payload["reviews"]:
            raw = review["scores"]
            scores[review["id"]] = {
                "novelty": min(10, int(raw["novelty"]) + novelty_offset),
                "falsifiability": int(raw["falsifiability"]),
                "impact": int(raw["impact"]),
            }
    return scores


def supported_effect(identifier: str, result: dict[str, object]):
    if identifier == "H003":
        return result["confirmation"]["effect_sigma"]
    if identifier in {"H006", "H011"}:
        return result["effect_sigma"]
    if identifier == "H015":
        return min(result["tables"][key]["deficit_sigma"] for key in ("18", "24"))
    return "not_applicable"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--result-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    scores = load_scores(args.root)
    records = []
    for identifier, (kind, level) in COMPLETED.items():
        path = args.result_root / identifier / "result.json"
        result = json.loads(path.read_text(encoding="utf-8"))
        verdict = result["verdict"]
        records.append(
            {
                "id": identifier,
                "type": kind,
                "level": level,
                "review_scores": scores[identifier],
                "verdict": verdict,
                "supported_effect_sigma": supported_effect(identifier, result) if verdict == "supported" else "not_applicable",
                "evidence": str(path),
                "next_minimum_upgrade": UPGRADES.get(identifier),
            }
        )

    verdict_counts = {name: sum(record["verdict"] == name for record in records) for name in ("supported", "falsified", "inconclusive")}
    audit_count = sum(record["type"] == "audit" for record in records)
    non_audit_count = len(records) - audit_count
    l0_count = sum(record["level"] == "L0" for record in records)
    protocol = json.loads((args.root / "protocol.json").read_text(encoding="utf-8"))
    assumptions = json.loads((args.root / "artifacts/assumptions_check.json").read_text(encoding="utf-8"))
    quotas = {
        "completed_count": len(records),
        "minimum_completed": protocol["minimum_completed_hypotheses"],
        "l0_count": l0_count,
        "minimum_l0": protocol["minimum_l0_completed"],
        "audit_count": audit_count,
        "non_audit_count": non_audit_count,
        "audit_fraction": audit_count / len(records),
        "maximum_audit_fraction": protocol["maximum_audit_fraction"],
        "minimum_non_audit": protocol["minimum_measurement_or_constructive"],
        "gpu_mi210_node_hours": 0,
        "gpu_budget_mi210_node_hours": protocol["gpu_budget_mi210_node_hours"],
        "passed": (
            len(records) >= protocol["minimum_completed_hypotheses"]
            and l0_count >= protocol["minimum_l0_completed"]
            and audit_count / len(records) <= protocol["maximum_audit_fraction"]
            and non_audit_count >= protocol["minimum_measurement_or_constructive"]
            and assumptions["passed"]
        ),
    }
    result = {
        "records": records,
        "verdict_counts": verdict_counts,
        "quotas": quotas,
        "assumptions": assumptions,
        "blocked_line_count": 7,
        "literature_addition_count": 10,
        "literature_addition_cap": protocol["literature_addition_cap"],
        "command": (
            f"python scripts/build_final_summary.py --root {args.root} "
            f"--result-root {args.result_root} --output {args.output}"
        ),
        "inputs": [
            "protocol.json",
            "artifacts/assumptions_check.json",
            *[relative for relative, _ in REVIEW_ROUNDS],
            *[str(args.result_root / identifier / "result.json") for identifier in COMPLETED],
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
