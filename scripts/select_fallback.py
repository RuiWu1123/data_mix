#!/usr/bin/env python3
"""Select fallback admissions from all remaining reviewed candidates."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--round", action="append", type=Path, required=True)
    parser.add_argument("--novelty-offset", action="append", type=int, required=True)
    parser.add_argument("--already-admitted", nargs="*", default=[])
    parser.add_argument("--count", type=int, default=3)
    args = parser.parse_args()
    if len(args.round) != len(args.novelty_offset):
        raise ValueError("one novelty offset is required per round")

    candidates = []
    for path, offset in zip(args.round, args.novelty_offset):
        payload = json.loads(path.read_text())
        reviews = payload.get("reviews", payload.get("candidates"))
        if reviews is None:
            raise ValueError(f"{path}: neither 'reviews' nor 'candidates'")
        for review in reviews:
            overlap_payload = review.get("substantial_overlap_veto", {})
            overlap = review.get("substantial_overlap", overlap_payload.get("veto", False))
            if overlap:
                continue
            if review["id"] in args.already_admitted:
                continue
            score_payload = review["scores"]
            if "calibrated" in score_payload:
                scores = {name: int(score_payload["calibrated"][name]) for name in ("novelty", "falsifiability", "impact")}
            else:
                raw = score_payload.get("raw", score_payload)
                scores = {
                    "novelty": min(10, int(raw["novelty"]) + offset),
                    "falsifiability": int(raw["falsifiability"]),
                    "impact": int(raw["impact"]),
                }
            candidates.append(
                {
                    "id": review["id"],
                    "scores": scores,
                    "total": sum(scores.values()),
                    "source": str(path),
                }
            )
    ranked = sorted(
        candidates,
        key=lambda item: (
            item["total"],
            item["scores"]["impact"],
            item["scores"]["falsifiability"],
            item["scores"]["novelty"],
            item["id"],
        ),
        reverse=True,
    )
    result = {
        "already_admitted": args.already_admitted,
        "eligible_ranked": ranked,
        "selected": [item["id"] for item in ranked[: args.count]],
        "tie_break": "total, impact, falsifiability, novelty, id descending",
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
