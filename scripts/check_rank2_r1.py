#!/usr/bin/env python3
"""Independently validate frozen TWODIAL-E2E-V1 R1 artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from pathlib import Path

import numpy as np
import pandas as pd
import yaml


MODEL_PARAMS = {
    "4M": 3744832,
    "6M": 6010464,
    "8M": 8538240,
    "10M": 9900432,
    "14M": 14380224,
    "16M": 16004560,
    "20M": 19101888,
    "60M": 57078144,
    "90M": 97946640,
    "150M": 151898880,
    "300M": 319980544,
    "530M": 530074944,
    "750M": 681297408,
    "1B": 1176832000,
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def close(left: float, right: float, tolerance: float = 1e-11) -> bool:
    return math.isclose(float(left), float(right), rel_tol=tolerance, abs_tol=tolerance)


def parse_group(value: str) -> tuple[str, str, int]:
    match = re.fullmatch(r"(.+)-([^-]+)-(5xC)(?:-([0-9]+))?", value)
    if match is None or match.group(2) not in MODEL_PARAMS:
        raise ValueError(value)
    raw_seed = int(match.group(4)) if match.group(4) else 6198
    return match.group(1), match.group(2), 6198 if raw_seed == 2 else raw_seed


def recompute_noise(path: Path) -> tuple[float, dict[str, int]]:
    frame = pd.read_csv(path)
    tasks = [column for column in frame if column.startswith("eval/")]
    parsed = [parse_group(str(value)) for value in frame["group"]]
    frame["recipe"] = [value[0] for value in parsed]
    frame["model"] = [value[1] for value in parsed]
    frame["seed"] = [value[2] for value in parsed]
    maximum = frame.groupby(["recipe", "model", "seed"])["step"].transform("max")
    final = frame.loc[frame["step"] == maximum].copy()
    values = np.log(final[tasks].apply(pd.to_numeric, errors="coerce").to_numpy(float))
    final[tasks] = values
    final = final.loc[np.all(np.isfinite(values), axis=1)].copy()
    eligible = final.groupby(["recipe", "model"], sort=True).filter(
        lambda group: group["seed"].nunique() >= 2
    )
    scale = eligible.groupby(["recipe", "model"])[tasks].mean().std(axis=0, ddof=1)
    observations: list[float] = []
    for _, group in eligible.groupby(["recipe", "model"], sort=True):
        standardized = group[tasks].std(axis=0, ddof=1) / math.sqrt(group["seed"].nunique()) / scale
        observations.extend(standardized[np.isfinite(standardized)].tolist())
    return float(np.median(observations)), {
        "raw_rows": len(frame),
        "final_rows": len(final),
        "eligible_seed_rows": len(eligible),
        "observations": len(observations),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--arms", type=Path, required=True)
    parser.add_argument("--datadecide", type=Path, required=True)
    parser.add_argument("--regmix", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    protocol = json.loads(args.protocol.read_text(encoding="utf-8"))
    result = json.loads(args.result.read_text(encoding="utf-8"))
    arms = json.loads(args.arms.read_text(encoding="utf-8"))
    checks: dict[str, bool] = {}
    checks["protocol_id"] = protocol["protocol_id"] == "TWODIAL-E2E-V1"
    expected_protocol_hash = sha256(args.protocol)
    checks["result_protocol_hash"] = result["protocol_sha256"] == expected_protocol_hash
    checks["arms_protocol_hash"] = arms["protocol_sha256"] == expected_protocol_hash
    checks["input_hashes"] = all(
        Path(path).is_file() and sha256(Path(path)) == digest
        for path, digest in result["input_sha256"].items()
    )

    sigma, noise_audit = recompute_noise(args.datadecide)
    checks["noise_floor"] = close(sigma, result["datadecide_seed_noise_floor"])
    checks["noise_counts"] = (
        noise_audit["raw_rows"] == result["datadecide_audit"]["raw_rows"]
        and noise_audit["final_rows"] == result["datadecide_audit"]["final_rows"]
        and noise_audit["eligible_seed_rows"] == result["datadecide_audit"]["eligible_seed_rows"]
        and noise_audit["observations"]
        == result["datadecide_audit"]["noise_standard_error_observations"]
    )

    summaries: dict[str, dict[str, float]] = {}
    for source, prefix in (("olmix", "olmix_"), ("regmix", "regmix_"), ("datadecide", "datadecide")):
        tables = [value for key, value in result["tables"].items() if key.startswith(prefix)]
        summaries[source] = {
            estimator: float(np.median([table["rmse"][estimator] for table in tables]))
            for estimator in tables[0]["rmse"]
        }
        checks[f"{source}_summary"] = all(
            close(value, result["source_summaries"][source][estimator])
            for estimator, value in summaries[source].items()
        )
        for table in tables:
            test_rows = sum(item["test_rows"] for item in table["folds"])
            checks[f"fold_coverage_{table['name']}"] = test_rows == table["rows"] and all(
                item["train_rows"] + item["test_rows"] == table["rows"] for item in table["folds"]
            )

    vote_counts = {"rank2": 0, "rank1": 0}
    for source, summary in summaries.items():
        baseline = min(summary["full_linear"], summary["extra_trees"])
        rank2_pass = (
            (summary["rank2"] - baseline) / sigma <= 0.5
            and (summary["rank1"] - summary["rank2"]) / sigma >= 1.0
            and (summary["rank2"] - summary["rank3"]) / sigma <= 0.5
        )
        rank1_pass = (summary["rank1"] - baseline) / sigma <= 0.5
        vote_counts["rank2"] += int(rank2_pass)
        vote_counts["rank1"] += int(rank1_pass)
        checks[f"{source}_votes"] = (
            rank2_pass == result["source_votes"][source]["rank2_pass"]
            and rank1_pass == result["source_votes"][source]["rank1_pass"]
        )
    expected_verdict = (
        "rank2-sufficient"
        if vote_counts["rank2"] >= 2
        else "rank1-sufficient"
        if vote_counts["rank1"] >= 2
        else "rank3+-sufficient"
    )
    checks["verdict"] = result["verdict"] == expected_verdict == arms["r1_verdict"]
    checks["selected_rank"] = arms["selected_rank"] == result["selected_rank_for_r2"]

    mixture = pd.read_csv(args.regmix / "test_mixture_1m.csv")
    domains = arms["domains"]
    for arm in ("rank_selected", "full_nonparametric", "h_probe"):
        row = arms["candidate_row_indices"][arm]
        expected = mixture.loc[mixture["index"] == row, domains].iloc[0].to_numpy(float)
        checks[f"arm_row_{arm}"] = np.allclose(expected, arms["arms"][arm], atol=1e-12, rtol=1e-12)
    official = yaml.safe_load(Path(arms["official_config"]).read_text(encoding="utf-8"))["train"]
    expected_official = np.asarray([official[domain] for domain in domains], dtype=float)
    expected_official /= expected_official.sum()
    checks["arm_official"] = np.allclose(expected_official, arms["arms"]["official_regmix"])
    checks["arm_count"] = len(arms["arms"]) == 4
    checks["arm_closure"] = all(abs(sum(weight) - 1.0) <= 0.002 for weight in arms["arms"].values())
    checks["task_effect_count"] = len(arms["tasks"]) == len(
        arms["predicted_probe_minus_selected_standardized_task_effect"]
    ) == 13
    checks["probe_distance"] = arms["rank_selected_vs_probe_l1"] >= 0.20

    failures = sorted(name for name, passed in checks.items() if not passed)
    payload = {
        "id": "TWODIAL-E2E-V1-R1-CHECK",
        "passed": not failures,
        "checks_passed": sum(checks.values()),
        "checks_total": len(checks),
        "failures": failures,
        "checks": checks,
        "independent_noise_floor": sigma,
        "independent_noise_audit": noise_audit,
        "independent_vote_counts": vote_counts,
        "independent_verdict": expected_verdict,
        "result_sha256": sha256(args.result),
        "arms_sha256": sha256(args.arms),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
