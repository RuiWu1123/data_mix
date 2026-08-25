#!/usr/bin/env python3
"""Audit whether the frozen Q1 interior synthetic designs are executable."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


DOMAIN_COUNTS = (6, 12, 18, 24)
META_COLUMNS = {"run", "name", "index", "Unnamed: 0"}


def audit_table(path: Path, domains: int) -> dict[str, object]:
    table = pd.read_csv(path)
    domain_columns = [column for column in table.columns if column not in META_COLUMNS]
    weights = table[domain_columns].apply(pd.to_numeric, errors="coerce").to_numpy(float)
    finite_rows = np.all(np.isfinite(weights), axis=1)
    finite_weights = weights[finite_rows]
    positive_rows = np.all(finite_weights > 0.0, axis=1)
    zero_cells = finite_weights == 0.0
    positive_support = finite_weights[positive_rows]
    centered_rank = 0
    if len(positive_support) > 0:
        closed = positive_support / positive_support.sum(axis=1, keepdims=True)
        logs = np.log(closed)
        centered_rank = int(np.linalg.matrix_rank(logs - logs.mean(axis=0, keepdims=True)))
    return {
        "path": str(path),
        "declared_domain_count": domains,
        "domain_column_count": len(domain_columns),
        "row_count": int(len(table)),
        "finite_row_count": int(finite_rows.sum()),
        "strictly_positive_row_count": int(positive_rows.sum()),
        "rows_with_at_least_one_exact_zero": int(np.any(zero_cells, axis=1).sum()),
        "exact_zero_cell_count": int(zero_cells.sum()),
        "strictly_positive_centered_log_rank": centered_rank,
        "required_coordinate_rank": domains - 1,
        "interior_design_full_rank": centered_rank == domains - 1,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    protocol = json.loads(args.protocol.read_text(encoding="utf-8"))
    dgp = protocol["questions"]["Q1"]["truth"]
    tables = {
        str(domains): audit_table(args.data / f"m{domains}_ratios.csv", domains)
        for domains in DOMAIN_COUNTS
    }
    interior_scenarios = [name for name in dgp["scenarios"] if name.startswith("interior_")]
    interior_generator_registered = "interior_generator" in dgp
    executable_from_strictly_positive_public_rows = all(
        table["interior_design_full_rank"] for table in tables.values()
    )
    protocol_defect = bool(
        interior_scenarios
        and not interior_generator_registered
        and not executable_from_strictly_positive_public_rows
    )
    result = {
        "id": "Q1-DESIGN-AUDIT",
        "outcome_data_read": False,
        "interior_scenario_count": len(interior_scenarios),
        "interior_generator_registered": interior_generator_registered,
        "structural_zero_generator_registered": "structural_zero_generator" in dgp,
        "executable_from_strictly_positive_public_rows": executable_from_strictly_positive_public_rows,
        "protocol_defect": protocol_defect,
        "tables": tables,
        "inputs": [
            str(args.protocol),
            *[str(args.data / f"m{domains}_ratios.csv") for domains in DOMAIN_COUNTS],
        ],
        "command": (
            "python scripts/audit_onedial_q1_design.py "
            f"--data {args.data} --protocol {args.protocol} --output {args.output}"
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
