#!/usr/bin/env python3
"""Independently recompute the TWODIAL-E2E-V1 R2 verdict."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def close(left: float, right: float, tolerance: float = 1e-9) -> bool:
    return math.isclose(float(left), float(right), rel_tol=tolerance, abs_tol=tolerance)


def effect(values: list[float]) -> float:
    array = np.asarray(values, dtype=float)
    sigma = float(array.std(ddof=1))
    mean = float(array.mean())
    return mean / sigma if sigma > 0.0 else math.copysign(math.inf, mean) if mean else 0.0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--arms", type=Path, required=True)
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--csv", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    protocol = json.loads(args.protocol.read_text(encoding="utf-8"))
    arms = json.loads(args.arms.read_text(encoding="utf-8"))
    result = json.loads(args.result.read_text(encoding="utf-8"))
    frame = pd.read_csv(args.csv)
    complete = frame[frame["status"] == "complete"].copy()
    tasks = arms["tasks"]
    checks: dict[str, bool] = {}
    checks["protocol_hash"] = result["protocol_sha256"] == sha256(args.protocol)
    checks["arms_hash"] = result["arms_sha256"] == sha256(args.arms)
    checks["completed_count"] = len(complete) == result["completed_jobs"]
    checks["job_gate"] = len(complete) >= protocol["R2"]["minimum_completed_job_count"]
    checks["arm_counts"] = complete.groupby("arm").size().to_dict() == result["arm_completed_counts"]
    scientific_columns = {f"ce/{task}" for task in tasks} | {f"bpb/{task}" for task in tasks}
    checks["scientific_columns"] = scientific_columns.issubset(complete.columns)
    if not checks["job_gate"] or not checks["scientific_columns"]:
        failures = sorted(name for name, passed in checks.items() if not passed)
        payload = {
            "id": "TWODIAL-E2E-V1-R2-CHECK",
            "passed": False,
            "checks_passed": sum(checks.values()),
            "checks_total": len(checks),
            "failures": failures,
            "independent_verdict": "incomplete",
            "completed_jobs": len(complete),
            "result_sha256": sha256(args.result),
            "csv_sha256": sha256(args.csv),
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps(payload, indent=2, sort_keys=True))
        raise SystemExit(1)
    checks["all_tasks_finite"] = all(
        np.all(np.isfinite(complete[f"ce/{task}"].to_numpy(float))) for task in tasks
    )
    checks["bpb_formula"] = all(
        np.allclose(
            complete[f"bpb/{task}"].to_numpy(float),
            complete[f"ce/{task}"].to_numpy(float) / math.log(2.0),
            rtol=1e-12,
            atol=1e-12,
        )
        for task in tasks
    )
    for task in tasks:
        values = complete[f"ce/{task}"].to_numpy(float)
        mean = float(values.mean())
        sd = float(values.std(ddof=1))
        checks[f"scale_{task}"] = close(mean, result["task_standardization"][task]["mean"]) and close(
            sd, result["task_standardization"][task]["sd"]
        )
        complete[f"independent_z/{task}"] = (values - mean) / sd
    complete["independent_score"] = complete[[f"independent_z/{task}" for task in tasks]].mean(axis=1)
    checks["aggregate_scores"] = np.allclose(
        complete["independent_score"], complete["aggregate_standardized_loss"], rtol=1e-10, atol=1e-10
    )
    indexed = complete.set_index(["arm", "seed"])
    shared = sorted(
        set(complete.loc[complete["arm"] == "rank_selected", "seed"].astype(int))
        & set(complete.loc[complete["arm"] == "h_probe", "seed"].astype(int))
    )

    def paired_scores(left: str, right: str) -> list[float]:
        seeds = sorted(
            set(complete.loc[complete["arm"] == left, "seed"].astype(int))
            & set(complete.loc[complete["arm"] == right, "seed"].astype(int))
        )
        return [
            float(indexed.loc[(left, seed), "independent_score"] - indexed.loc[(right, seed), "independent_score"])
            for seed in seeds
        ]

    selected_full = effect(paired_scores("rank_selected", "full_nonparametric"))
    official_selected = effect(paired_scores("official_regmix", "rank_selected"))
    checks["selected_full"] = close(
        selected_full, result["contrasts"]["selected_minus_full"]["effect_sigma"]
    )
    checks["official_selected"] = close(
        official_selected, result["contrasts"]["official_minus_selected"]["effect_sigma"]
    )
    observed = []
    per_seed = {}
    for task in tasks:
        task_values = complete[f"ce/{task}"].to_numpy(float)
        sd = float(task_values.std(ddof=1))
        observed.append(
            float(
                np.mean(
                    [
                        indexed.loc[("h_probe", seed), f"ce/{task}"]
                        - indexed.loc[("rank_selected", seed), f"ce/{task}"]
                        for seed in shared
                    ]
                )
                / sd
            )
        )
    for seed in shared:
        per_seed[seed] = np.asarray(
            [
                (
                    indexed.loc[("h_probe", seed), f"ce/{task}"]
                    - indexed.loc[("rank_selected", seed), f"ce/{task}"]
                )
                / complete[f"ce/{task}"].std(ddof=1)
                for task in tasks
            ]
        )
    observed_array = np.asarray(observed)
    predicted = np.asarray(arms["predicted_probe_minus_selected_standardized_task_effect"])
    cosine = float(np.dot(observed_array, predicted) / (np.linalg.norm(observed_array) * np.linalg.norm(predicted)))
    sign_agreement = int(np.sum(np.sign(observed_array) == np.sign(predicted)))
    checks["observed_vector"] = np.allclose(
        observed_array, result["direction"]["observed_standardized_effect"], rtol=1e-10, atol=1e-10
    )
    checks["cosine"] = close(cosine, result["direction"]["cosine"])
    checks["sign_agreement"] = sign_agreement == result["direction"]["sign_agreement"]
    code_index = [tasks.index("github"), tasks.index("dm_mathematics")]
    common_index = [tasks.index("pile_cc"), tasks.index("wikipedia_en")]
    code_values = [float(per_seed[seed][code_index].mean()) for seed in shared]
    common_values = [float(per_seed[seed][common_index].mean()) for seed in shared]
    code_effect = effect(code_values)
    common_effect = effect(common_values)
    checks["code_math"] = close(
        code_effect, result["direction"]["code_math_probe_minus_selected"]["effect_sigma"]
    )
    checks["common"] = close(
        common_effect, result["direction"]["pilecc_wikipedia_probe_minus_selected"]["effect_sigma"]
    )
    supported = (
        selected_full <= 0.5
        and official_selected >= 1.0
        and cosine >= 0.70
        and sign_agreement >= 10
        and np.mean(code_values) * np.mean(common_values) < 0.0
        and abs(code_effect) >= 1.0
        and abs(common_effect) >= 1.0
    )
    falsified = selected_full > 1.0 or cosine < 0.0 or sign_agreement <= 6
    verdict = "supported" if supported else "falsified" if falsified else "inconclusive"
    checks["verdict"] = verdict == result["verdict"]
    checks["result_hashes"] = all(Path(path).is_file() and sha256(Path(path)) == digest for path, digest in result["result_hashes"].items())
    failures = sorted(name for name, passed in checks.items() if not passed)
    payload = {
        "id": "TWODIAL-E2E-V1-R2-CHECK",
        "passed": not failures,
        "checks_passed": sum(checks.values()),
        "checks_total": len(checks),
        "failures": failures,
        "independent_verdict": verdict,
        "independent_selected_minus_full_sigma": selected_full,
        "independent_official_minus_selected_sigma": official_selected,
        "independent_direction_cosine": cosine,
        "independent_sign_agreement": sign_agreement,
        "independent_code_math_sigma": code_effect,
        "independent_pilecc_wikipedia_sigma": common_effect,
        "result_sha256": sha256(args.result),
        "csv_sha256": sha256(args.csv),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
