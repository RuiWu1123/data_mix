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
    reviews = payload.get("reviews", payload.get("candidates"))
    if reviews is None:
        raise ValueError("review payload has neither 'reviews' nor 'candidates'")
    results = []
    for item in reviews:
        nearest = item.get("nearest_prior_work", item.get("closest_works", []))
        if len(nearest) < 3:
            raise ValueError(f"{item['id']}: fewer than three prior works")
        if len(item["strongest_objections"]) < 3:
            raise ValueError(f"{item['id']}: fewer than three objections")
        score_payload = item["scores"]
        raw_payload = score_payload.get("raw", score_payload)
        raw = {name: int(raw_payload[name]) for name in DIMENSIONS}
        if "calibrated" in score_payload:
            calibrated = {name: int(score_payload["calibrated"][name]) for name in DIMENSIONS}
        else:
            calibrated = dict(raw)
            calibrated["novelty"] = min(10, raw["novelty"] + args.novelty_offset)
        overlap_payload = item.get("substantial_overlap_veto", {})
        overlap = item.get("substantial_overlap", overlap_payload.get("veto", False))
        fatal = item.get("unresolved_fatal_objection")
        if fatal is None:
            fatal = bool(item.get("unresolved_fatal_objections", []))
        passed = (
            not overlap
            and not fatal
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
