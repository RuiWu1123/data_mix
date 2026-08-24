#!/usr/bin/env python3
"""Audit the evaluation masks used by the released DMSL Table 2 code."""

from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path

import numpy as np
import pandas as pd


def lines_with(path: Path, needles: tuple[str, ...]) -> list[dict[str, object]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    return [
        {"line": index, "text": line.strip()}
        for index, line in enumerate(lines, start=1)
        if any(needle in line for needle in needles)
    ]


def numeric_comparisons(path: Path) -> list[dict[str, object]]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    findings = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Compare):
            continue
        rendered = ast.unparse(node)
        if "h_" not in rendered and "h_train" not in rendered and "h_set" not in rendered:
            continue
        constants = [
            item.value
            for item in ast.walk(node)
            if isinstance(item, ast.Constant) and isinstance(item.value, (int, float))
        ]
        findings.append({"line": node.lineno, "expression": rendered, "constants": constants})
    return findings


def one_pass(args: argparse.Namespace) -> dict[str, object]:
    eq1_driver = args.repo / "fitting_17domains_eq1.py"
    eq3_driver = args.repo / "fitting_17domains_eq3.py"
    law1 = args.repo / "utils/fitting_algos/law1.py"
    law2 = args.repo / "utils/fitting_algos/law2init.py"
    ratios_path = args.repo / "data/test_mixture_1B.csv"
    paper = args.paper_text

    ratios_frame = pd.read_csv(ratios_path)
    weights = ratios_frame.drop(columns=["index"]).apply(pd.to_numeric, errors="coerce").to_numpy(float)
    finite = np.isfinite(weights)
    nonzero = finite & (weights > 0)
    hypothetical_omitted = nonzero & (weights < 0.1)

    eq1_comparisons = numeric_comparisons(law1)
    eq3_comparisons = numeric_comparisons(law2)
    eq1_has_point_one = any(0.1 in item["constants"] for item in eq1_comparisons)
    eq3_has_point_one = any(0.1 in item["constants"] for item in eq3_comparisons)
    eq1_scores_all_cells = any(
        "L_pred_matrix - l" in item["text"]
        for item in lines_with(law1, ("L_pred_matrix - l",))
    )
    eq3_scores_positive_cells = any(
        item["expression"] == "h_set > 0" for item in eq3_comparisons
    )
    table2_scope = lines_with(paper, ("Table 2: Comparison", "64 1B-parameter models"))

    published_mask_exists = eq1_has_point_one or eq3_has_point_one
    return {
        "driver_trace": {
            "eq1": lines_with(eq1_driver, ("law1(",)),
            "eq3": lines_with(eq3_driver, ("law2(",)),
        },
        "mask_trace": {
            "eq1_comparisons": eq1_comparisons,
            "eq1_scores_all_cells": eq1_scores_all_cells,
            "eq3_comparisons": eq3_comparisons,
            "eq3_scores_positive_cells": eq3_scores_positive_cells,
            "published_h_ge_0_1_mask_exists": published_mask_exists,
        },
        "paper_scope_lines": table2_scope,
        "released_ratio_rows": int(weights.shape[0]),
        "released_weight_cells": int(finite.sum()),
        "released_nonzero_weight_cells": int(nonzero.sum()),
        "hypothetical_h_ge_0_1_omitted_cells": int(hypothetical_omitted.sum()),
        "hypothetical_omitted_fraction_of_nonzero": float(
            hypothetical_omitted.sum() / max(nonzero.sum(), 1)
        ),
        "verdict": "falsified" if not published_mask_exists else "continue_full_reproduction",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--paper-text", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    repeats = [one_pass(args) for _ in range(3)]
    exact_repeat_agreement = all(item == repeats[0] for item in repeats[1:])
    result = dict(repeats[0])
    result.update(
        {
            "id": "H007",
            "repeat_count": 3,
            "exact_repeat_agreement": exact_repeat_agreement,
            "sigma": 0.0,
            "effect_sigma": "infinite" if result["verdict"] == "falsified" else 0.0,
            "inputs": [str(args.repo), str(args.paper_text)],
            "command": (
                f"python scripts/test_h007.py --repo {args.repo} "
                f"--paper-text {args.paper_text} --output {args.output}"
            ),
        }
    )
    if not exact_repeat_agreement:
        result["verdict"] = "inconclusive"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
