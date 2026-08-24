#!/usr/bin/env python3
"""Apply the conservative review-generation token-pool cutoff."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol", type=Path, default=Path("protocol.json"))
    parser.add_argument("--snapshot", type=Path, required=True)
    args = parser.parse_args()

    protocol = json.loads(args.protocol.read_text(encoding="utf-8"))
    snapshot = json.loads(args.snapshot.read_text(encoding="utf-8"))
    pool_limit = int(
        protocol["token_budget"] * protocol["review_generation_budget_fraction"]
    )
    total_used = int(snapshot["tokens_used"])
    result = {
        "conservative_accounting": "all goal tokens upper-bound review-generation tokens",
        "forced_relative_selection": total_used >= pool_limit,
        "pool_limit": pool_limit,
        "token_budget": protocol["token_budget"],
        "tokens_used": total_used,
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
