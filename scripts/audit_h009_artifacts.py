#!/usr/bin/env python3
"""Audit whether released Olmix RQ2 artifacts can confirm H009 at 1B scale."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


def matching_lines(path: Path, needles: tuple[str, ...]) -> list[dict[str, object]]:
    return [
        {"line": number, "text": line.strip()}
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1)
        if any(needle in line for needle in needles)
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--paper-text", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    tables = {}
    all_names = []
    for domains in (6, 12, 18, 24):
        ratios_path = args.data / f"m{domains}_ratios.csv"
        metrics_path = args.data / f"m{domains}_metrics.csv"
        ratios = pd.read_csv(ratios_path)
        metrics = pd.read_csv(metrics_path)
        names = metrics["name"].astype(str) if "name" in metrics else pd.Series([], dtype=str)
        all_names.extend(names.tolist())
        ratio_domains = [column for column in ratios if column not in {"run", "name", "index", "Unnamed: 0"}]
        metric_columns = [column for column in metrics if column not in {"run", "name", "index", "Unnamed: 0"}]
        tables[str(domains)] = {
            "ratio_rows": len(ratios),
            "metric_rows": len(metrics),
            "domain_columns": len(ratio_domains),
            "metric_columns": len(metric_columns),
            "names_containing_30m": int(names.str.lower().str.contains("30m").sum()),
            "names_containing_1b": int(names.str.lower().str.contains("1b").sum()),
        }
    lowered = [name.lower() for name in all_names]
    result = {
        "id": "H009",
        "tables": tables,
        "released_run_name_count": len(all_names),
        "released_names_containing_30m": sum("30m" in name for name in lowered),
        "released_names_containing_1b": sum("1b" in name for name in lowered),
        "has_row_level_30m_discovery": len(all_names) > 0 and all("30m" in name for name in lowered),
        "has_row_level_1b_confirmation": any("1b" in name for name in lowered),
        "paper_scope_lines": matching_lines(
            args.paper_text,
            (
                "We used 30M proxy models for",
                "at the 1B scale (Figure 18)",
                "For the results in Figure 4 and Figure 18",
                "m = 6, 24",
            ),
        ),
        "line_status": "ready" if any("1b" in name for name in lowered) else "blocked_missing_1b_row_level_results",
        "inputs": [str(args.data), str(args.paper_text)],
        "command": (
            f"python scripts/audit_h009_artifacts.py --data {args.data} "
            f"--paper-text {args.paper_text} --output {args.output}"
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
