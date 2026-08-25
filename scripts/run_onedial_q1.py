#!/usr/bin/env python3
"""Run and aggregate the frozen ONEDIAL-V3 Q1 synthetic calibration."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.linalg import helmert

from onedial_core import (
    META_COLUMNS,
    interior_weight_seed,
    mixture_coordinates,
    permutation_dimension_test,
    prepare_design,
    protocol_seed,
    sha_fold,
)


SCENARIOS = (
    "interior_rank1",
    "interior_rank2",
    "interior_rank5",
    "structural_zero_rank1",
    "structural_zero_rank2",
)
RANKS = {
    "interior_rank1": 1,
    "interior_rank2": 2,
    "interior_rank5": 5,
    "structural_zero_rank1": 1,
    "structural_zero_rank2": 2,
}


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_protocol(path: Path) -> dict[str, object]:
    protocol = json.loads(path.read_text(encoding="utf-8"))
    if protocol.get("protocol_id") != "ONEDIAL-V3":
        raise ValueError("Q1 execution requires the frozen ONEDIAL-V3 protocol")
    q1 = protocol["questions"]["Q1"]
    if protocol["randomness"]["permutation_replicates"] != 4999:
        raise ValueError("unexpected permutation count")
    if q1["truth"]["scenarios"] != list(SCENARIOS):
        raise ValueError("unexpected Q1 scenario list")
    return protocol


def load_ratios(path: Path) -> tuple[np.ndarray, list[str]]:
    table = pd.read_csv(path)
    domains = [column for column in table.columns if column not in META_COLUMNS]
    weights = table[domains].apply(pd.to_numeric, errors="coerce").to_numpy(float)
    finite = np.all(np.isfinite(weights), axis=1)
    table = table.loc[finite].reset_index(drop=True)
    weights = weights[finite]
    row_ids = []
    for row_index, row in table.iterrows():
        immutable = row["run"] if "run" in table and pd.notna(row["run"]) else row.get("index", row_index)
        row_ids.append(str(immutable))
    return weights, row_ids


def orthonormal_columns(rng: np.random.Generator, rows: int, columns: int) -> np.ndarray:
    matrix = rng.normal(size=(rows, columns))
    q, r = np.linalg.qr(matrix, mode="reduced")
    signs = np.where(np.diag(r) < 0.0, -1.0, 1.0)
    return q * signs[None, :]


def generate_replicate(
    protocol: dict[str, object],
    data: Path,
    phase: str,
    domains: int,
    scenario: str,
    replicate: int,
    pipeline: str,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    q1 = protocol["questions"]["Q1"]
    truth = q1["truth"]
    namespace = q1[phase]["seed_namespace"]
    public_weights, public_row_ids = load_ratios(data / f"m{domains}_ratios.csv")
    rows = len(public_weights)
    if scenario.startswith("interior_"):
        weight_rng = np.random.Generator(
            np.random.PCG64(interior_weight_seed(namespace, domains, scenario, replicate))
        )
        weights = weight_rng.dirichlet(np.ones(domains), size=rows)
        truth_x = np.log(weights) @ helmert(domains, full=False).T
        row_ids = [f"interior-{row}" for row in range(rows)]
    else:
        weights = public_weights
        truth_x = mixture_coordinates(weights, "B")
        row_ids = public_row_ids

    fit_x = mixture_coordinates(weights, pipeline)
    fold_prefix = f"Q1:{namespace}:m={domains}:scenario={scenario}:replicate={replicate}"
    folds = np.asarray([sha_fold(f"{fold_prefix}:row={row_id}") for row_id in row_ids], dtype=int)
    rank = RANKS[scenario]
    direction_rng = np.random.default_rng(
        protocol_seed(f"Q1:{namespace}:m={domains}:scenario={scenario}:replicate={replicate}:operator")
    )
    coordinate_loading = orthonormal_columns(direction_rng, truth_x.shape[1], rank)
    task_loading = orthonormal_columns(direction_rng, int(truth["task_count"]), rank)
    singular = np.asarray(truth["singular_values"][:rank], dtype=float)
    centered_truth_x = truth_x - truth_x.mean(axis=0, keepdims=True)
    signal = centered_truth_x @ coordinate_loading @ np.diag(singular) @ task_loading.T
    noise_rng = np.random.default_rng(
        protocol_seed(f"Q1:{namespace}:m={domains}:scenario={scenario}:replicate={replicate}:noise")
    )
    response = signal + noise_rng.normal(
        scale=float(truth["noise_sigma"]), size=(rows, int(truth["task_count"]))
    )
    return fit_x, folds, response, task_loading


def run_shard(args: argparse.Namespace) -> None:
    protocol = load_protocol(args.protocol)
    q1 = protocol["questions"]["Q1"]
    registered_designs = q1[args.phase]["olmix_designs"]
    registered_replicates = int(q1[args.phase]["replicates_per_scenario"])
    if args.domains not in registered_designs or args.scenario not in SCENARIOS:
        raise ValueError("shard is outside the registered phase design")
    if args.start < 0 or args.count < 1 or args.start + args.count > registered_replicates:
        raise ValueError("shard replicate interval is outside the registered phase")
    records = []
    for replicate in range(args.start, args.start + args.count):
        fit_x, folds, response, true_task_loading = generate_replicate(
            protocol, args.data, args.phase, args.domains, args.scenario, replicate, args.pipeline
        )
        cache = prepare_design(fit_x, folds)
        permutation_rng = np.random.default_rng(
            protocol_seed(
                f"Q1:{q1[args.phase]['seed_namespace']}:m={args.domains}:scenario={args.scenario}:"
                f"replicate={replicate}:pipeline={args.pipeline}:permutations"
            )
        )
        test = permutation_dimension_test(
            cache,
            response,
            permutation_rng,
            permutations=int(protocol["randomness"]["permutation_replicates"]),
            family_size=4,
            alpha=0.01,
            batch_size=args.permutation_batch_size,
        )
        recovered_h = np.asarray(test.pop("h_task_loading"), dtype=float)
        cosine = None
        if RANKS[args.scenario] == 2:
            true_h = true_task_loading[:, 1]
            denominator = np.linalg.norm(recovered_h) * np.linalg.norm(true_h)
            cosine = float(abs(recovered_h @ true_h) / denominator) if denominator > 0.0 else 0.0
        records.append({"replicate": replicate, "h_cosine": cosine, **test})
        print(
            json.dumps(
                {
                    "replicate": replicate,
                    "dimension": test["significant_dimension"],
                    "permutations_processed": test["permutations_processed"],
                    "cosine": cosine,
                },
                sort_keys=True,
            ),
            flush=True,
        )
    payload = {
        "id": "ONEDIAL-V3-Q1-SHARD",
        "protocol_sha256": file_sha256(args.protocol),
        "phase": args.phase,
        "pipeline": args.pipeline,
        "domains": args.domains,
        "scenario": args.scenario,
        "start": args.start,
        "count": args.count,
        "permutation_batch_size": args.permutation_batch_size,
        "records": records,
        "inputs": [str(args.protocol), str(args.data / f"m{args.domains}_ratios.csv")],
        "command": " ".join(os.sys.argv),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def wilson(successes: int, total: int) -> tuple[float, float]:
    z = 1.959963984540054
    proportion = successes / total
    denominator = 1.0 + z * z / total
    center = (proportion + z * z / (2.0 * total)) / denominator
    half = z * math.sqrt(proportion * (1.0 - proportion) / total + z * z / (4.0 * total**2)) / denominator
    return center - half, center + half


def summarize_cell(records: list[dict[str, object]], scenario: str) -> dict[str, object]:
    total = len(records)
    dimensions = np.asarray([record["significant_dimension"] for record in records], dtype=int)
    permutations_processed = np.asarray([record["permutations_processed"] for record in records], dtype=int)
    summary: dict[str, object] = {
        "replicate_count": total,
        "mean_permutations_processed": float(permutations_processed.mean()),
        "full_permutation_fraction": float(np.mean(permutations_processed == 4999)),
        "dimension_counts": {str(value): int(np.sum(dimensions == value)) for value in range(5)},
    }
    if scenario.endswith("rank1"):
        successes = int(np.sum(dimensions >= 1))
        lower, upper = wilson(successes, total)
        summary.update({
            "metric": "false_positive_dimension_ge_1",
            "success_count": successes,
            "rate": successes / total,
            "wilson_lower95": lower,
            "wilson_upper95": upper,
        })
    elif scenario.endswith("rank2"):
        successes = int(np.sum(dimensions >= 1))
        lower, upper = wilson(successes, total)
        cosines = np.asarray([record["h_cosine"] for record in records], dtype=float)
        summary.update({
            "metric": "detect_residual_dimension_ge_1",
            "success_count": successes,
            "rate": successes / total,
            "wilson_lower95": lower,
            "wilson_upper95": upper,
            "h_cosine_median": float(np.median(cosines)),
            "h_cosine_q05": float(np.quantile(cosines, 0.05)),
        })
    elif scenario == "interior_rank5":
        successes = int(np.sum(dimensions > 3))
        lower, upper = wilson(successes, total)
        summary.update({
            "metric": "detect_residual_dimension_gt_3",
            "success_count": successes,
            "rate": successes / total,
            "wilson_lower95": lower,
            "wilson_upper95": upper,
        })
    return summary


def cell_passes(summary: dict[str, object], support: dict[str, object]) -> tuple[bool, dict[str, bool]]:
    metric = summary["metric"]
    if metric == "false_positive_dimension_ge_1":
        checks = {
            "rate_max": summary["rate"] <= support["null_false_positive_rate_max"],
            "wilson_upper95_max": summary["wilson_upper95"] <= support["null_false_positive_wilson_upper95_max"],
        }
    elif metric == "detect_residual_dimension_ge_1":
        checks = {
            "rate_min": summary["rate"] >= support["rank2_detection_rate_min"],
            "wilson_lower95_min": summary["wilson_lower95"] >= support["rank2_detection_wilson_lower95_min"],
            "h_cosine_median_min": summary["h_cosine_median"] >= support["rank2_h_cosine_median_min"],
            "h_cosine_q05_min": summary["h_cosine_q05"] >= support["rank2_h_cosine_q05_min"],
        }
    elif metric == "detect_residual_dimension_gt_3":
        checks = {
            "rate_min": summary["rate"] >= support["rank5_gt3_detection_rate_min"],
            "wilson_lower95_min": summary["wilson_lower95"] >= support["rank5_gt3_detection_wilson_lower95_min"],
        }
    else:
        raise ValueError(f"unknown metric: {metric}")
    return all(checks.values()), checks


def aggregate(args: argparse.Namespace) -> None:
    protocol = load_protocol(args.protocol)
    q1 = protocol["questions"]["Q1"]
    designs = q1[args.phase]["olmix_designs"]
    expected_replicates = int(q1[args.phase]["replicates_per_scenario"])
    pipelines = [args.pipeline] if args.pipeline else ["A", "B"]
    cells = {}
    for pipeline in pipelines:
        for domains in designs:
            for scenario in SCENARIOS:
                directory = args.input_root / pipeline / f"m{domains}" / scenario
                files = sorted(directory.glob("*.json"))
                records = []
                for path in files:
                    shard = json.loads(path.read_text(encoding="utf-8"))
                    if shard["protocol_sha256"] != file_sha256(args.protocol):
                        raise ValueError(f"protocol hash mismatch in {path}")
                    expected_identity = (args.phase, pipeline, domains, scenario)
                    actual_identity = (
                        shard["phase"], shard["pipeline"], shard["domains"], shard["scenario"]
                    )
                    if actual_identity != expected_identity:
                        raise ValueError(f"shard identity mismatch in {path}")
                    records.extend(shard["records"])
                replicate_ids = sorted(int(record["replicate"]) for record in records)
                if replicate_ids != list(range(expected_replicates)):
                    raise ValueError(
                        f"incomplete or overlapping shards for {pipeline}/m{domains}/{scenario}: "
                        f"found {len(replicate_ids)}, expected {expected_replicates}"
                    )
                summary = summarize_cell(records, scenario)
                passed, checks = cell_passes(summary, q1["support"])
                summary["checks"] = checks
                summary["passed"] = passed
                cells[f"{pipeline}/m{domains}/{scenario}"] = summary
    pipeline_pass = {
        pipeline: all(value["passed"] for key, value in cells.items() if key.startswith(pipeline + "/"))
        for pipeline in pipelines
    }
    selected_pipeline = None
    if args.phase == "discovery":
        if pipeline_pass.get("A", False):
            selected_pipeline = "A"
        elif pipeline_pass.get("B", False):
            selected_pipeline = "B"
        phase_verdict = "selected" if selected_pipeline else "inconclusive"
    else:
        if len(pipelines) != 1:
            raise ValueError("confirmation aggregation requires exactly one frozen pipeline")
        phase_verdict = "supported" if pipeline_pass[pipelines[0]] else "falsified"
        selected_pipeline = pipelines[0]
    payload = {
        "id": f"ONEDIAL-V3-Q1-{args.phase.upper()}",
        "protocol_sha256": file_sha256(args.protocol),
        "phase": args.phase,
        "pipelines": pipelines,
        "pipeline_pass": pipeline_pass,
        "selected_pipeline": selected_pipeline,
        "phase_verdict": phase_verdict,
        "cells": cells,
        "inputs": [str(args.protocol), str(args.input_root)],
        "command": " ".join(os.sys.argv),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))


def dispatch(args: argparse.Namespace) -> None:
    protocol = load_protocol(args.protocol)
    q1 = protocol["questions"]["Q1"]
    designs = list(q1[args.phase]["olmix_designs"])
    replicates = int(q1[args.phase]["replicates_per_scenario"])
    pipelines = args.pipelines.split("+")
    if args.phase == "discovery" and pipelines != ["A", "B"]:
        raise ValueError("discovery dispatch must evaluate A,B in that order")
    if args.phase == "confirmation" and len(pipelines) != 1:
        raise ValueError("confirmation dispatch requires one selected pipeline")
    if replicates % args.shard_size != 0:
        raise ValueError("registered replicate count must divide evenly by shard size")
    shards_per_cell = replicates // args.shard_size
    cells = [(pipeline, domains, scenario) for pipeline in pipelines for domains in designs for scenario in SCENARIOS]
    expected_tasks = len(cells) * shards_per_cell
    if not 0 <= args.task_id < expected_tasks:
        raise ValueError(f"task ID must be in [0,{expected_tasks - 1}]")
    cell_index, shard_index = divmod(args.task_id, shards_per_cell)
    pipeline, domains, scenario = cells[cell_index]
    start = shard_index * args.shard_size
    output = args.output_root / pipeline / f"m{domains}" / scenario / f"{start:04d}.json"
    shard_args = argparse.Namespace(
        protocol=args.protocol,
        data=args.data,
        phase=args.phase,
        pipeline=pipeline,
        domains=domains,
        scenario=scenario,
        start=start,
        count=args.shard_size,
        permutation_batch_size=args.permutation_batch_size,
        output=output,
    )
    run_shard(shard_args)


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser()
    subparsers = root.add_subparsers(dest="mode", required=True)
    shard = subparsers.add_parser("shard")
    shard.add_argument("--protocol", type=Path, required=True)
    shard.add_argument("--data", type=Path, required=True)
    shard.add_argument("--phase", choices=("discovery", "confirmation"), required=True)
    shard.add_argument("--pipeline", choices=("A", "B"), required=True)
    shard.add_argument("--domains", type=int, required=True)
    shard.add_argument("--scenario", choices=SCENARIOS, required=True)
    shard.add_argument("--start", type=int, required=True)
    shard.add_argument("--count", type=int, required=True)
    shard.add_argument("--permutation-batch-size", type=int, default=128)
    shard.add_argument("--output", type=Path, required=True)
    shard.set_defaults(function=run_shard)
    aggregate_parser = subparsers.add_parser("aggregate")
    aggregate_parser.add_argument("--protocol", type=Path, required=True)
    aggregate_parser.add_argument("--phase", choices=("discovery", "confirmation"), required=True)
    aggregate_parser.add_argument("--pipeline", choices=("A", "B"))
    aggregate_parser.add_argument("--input-root", type=Path, required=True)
    aggregate_parser.add_argument("--output", type=Path, required=True)
    aggregate_parser.set_defaults(function=aggregate)
    dispatch_parser = subparsers.add_parser("dispatch")
    dispatch_parser.add_argument("--protocol", type=Path, required=True)
    dispatch_parser.add_argument("--data", type=Path, required=True)
    dispatch_parser.add_argument("--phase", choices=("discovery", "confirmation"), required=True)
    dispatch_parser.add_argument("--pipelines", required=True)
    dispatch_parser.add_argument("--task-id", type=int, required=True)
    dispatch_parser.add_argument("--shard-size", type=int, default=20)
    dispatch_parser.add_argument("--permutation-batch-size", type=int, default=128)
    dispatch_parser.add_argument("--output-root", type=Path, required=True)
    dispatch_parser.set_defaults(function=dispatch)
    return root


if __name__ == "__main__":
    arguments = parser().parse_args()
    arguments.function(arguments)
