#!/usr/bin/env python3
"""Validate structured adversarial reviews and apply calibration."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


DIMENSIONS = ("novelty", "falsifiability", "impact")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("review", type=Path)
    parser.add_argument("--threshold", type=int, default=7)
    parser.add_argument("--novelty-offset", type=int, default=0)
    args = parser.parse_args()

    payload = json.loads(args.review.read_text(encoding="utf-8"))
    results = []
    for item in payload["reviews"]:
        if len(item["nearest_prior_work"]) < 3:
            raise ValueError(f"{item['id']}: fewer than three prior works")
        if len(item["strongest_objections"]) < 3:
            raise ValueError(f"{item['id']}: fewer than three objections")
        raw = {name: int(item["scores"][name]) for name in DIMENSIONS}
        calibrated = dict(raw)
        calibrated["novelty"] = min(10, raw["novelty"] + args.novelty_offset)
        passed = (
            not item.get("substantial_overlap", False)
            and not item.get("unresolved_fatal_objection", False)
            and all(value >= args.threshold for value in calibrated.values())
        )
        results.append(
            {
                "calibrated_scores": calibrated,
                "id": item["id"],
                "passed": passed,
                "raw_scores": raw,
            }
        )
    print(json.dumps({"results": results}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
