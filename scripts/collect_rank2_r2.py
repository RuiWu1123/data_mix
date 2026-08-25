#!/usr/bin/env python3
"""Collect TWODIAL-E2E-V1 R2 jobs and apply the frozen scientific verdict."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import subprocess
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def paired(left: dict[int, float], right: dict[int, float]) -> dict[str, object]:
    seeds = sorted(set(left) & set(right))
    values = np.asarray([left[seed] - right[seed] for seed in seeds], dtype=float)
    mean = float(values.mean()) if len(values) else math.nan
    sigma = float(values.std(ddof=1)) if len(values) >= 2 else math.nan
    effect = mean / sigma if sigma > 0.0 else math.copysign(math.inf, mean) if mean else 0.0
    if len(values) >= 2 and sigma > 0.0:
        half = float(stats.t.ppf(0.975, len(values) - 1) * sigma / math.sqrt(len(values)))
        interval = [mean - half, mean + half]
        interval_sigma = [value / sigma for value in interval]
    else:
        interval = [math.nan, math.nan]
        interval_sigma = [math.nan, math.nan]
    return {
        "shared_seeds": seeds,
        "n": len(seeds),
        "differences": values.tolist(),
        "mean": mean,
        "paired_sigma": sigma,
        "effect_sigma": effect,
        "ci95": interval,
        "ci95_sigma": interval_sigma,
    }


def slurm_records(job_ids: list[str], configs: list[dict[str, object]]) -> list[dict[str, object]]:
    if not job_ids:
        return []
    command = [
        "sacct",
        "-j",
        ",".join(job_ids),
        "--format=JobID,State,ElapsedRaw,ExitCode,NodeList,AllocTRES",
        "-n",
        "-P",
    ]
    output = subprocess.run(command, check=True, text=True, capture_output=True).stdout
    records = []
    for line in output.splitlines():
        fields = line.split("|")
        match = re.fullmatch(r"(\d+)_(\d+)", fields[0])
        if match is None:
            continue
        index = int(match.group(2))
        if index >= len(configs):
            continue
        records.append(
            {
                "job_id": fields[0],
                "array_job_id": match.group(1),
                "array_index": index,
                "arm": configs[index]["arm"],
                "seed": configs[index]["seed"],
                "state": fields[1],
                "elapsed_seconds": int(fields[2]),
                "exit_code": fields[3],
                "node": fields[4],
                "alloc_tres": fields[5],
                "gpu_node_hours": int(fields[2]) / 3600.0,
            }
        )
    return records


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--arms", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--result-root", type=Path, required=True)
    parser.add_argument("--job-ids", default="")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--csv", type=Path, required=True)
    parser.add_argument("--plot", type=Path, required=True)
    args = parser.parse_args()
    protocol = json.loads(args.protocol.read_text(encoding="utf-8"))
    arms = json.loads(args.arms.read_text(encoding="utf-8"))
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    task_names = arms["tasks"]
    records = sorted(manifest["records"], key=lambda item: item["path"])
    rows = []
    result_hashes = {}
    for record in records:
        arm = str(record["arm"])
        seed = int(record["seed"])
        path = args.result_root / f"{arm}_seed{seed}" / "result.json"
        row: dict[str, object] = {"arm": arm, "seed": seed, "result_path": str(path)}
        if not path.is_file():
            row["status"] = "missing"
            rows.append(row)
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        losses = payload.get("validation_cross_entropy", {})
        complete = (
            payload.get("optimizer_steps") == 954
            and payload.get("training_tokens") == 1000341504
            and set(losses) == set(task_names)
            and all(math.isfinite(float(losses[task])) for task in task_names)
        )
        row["status"] = "complete" if complete else "missing"
        row["optimizer_steps"] = payload.get("optimizer_steps")
        row["training_tokens"] = payload.get("training_tokens")
        if complete:
            for task in task_names:
                ce = float(losses[task])
                row[f"ce/{task}"] = ce
                row[f"bpb/{task}"] = ce / math.log(2.0)
            result_hashes[str(path)] = sha256(path)
        rows.append(row)
    frame = pd.DataFrame(rows)
    complete = frame[frame["status"] == "complete"].copy()
    completed_count = len(complete)
    arm_counts = complete.groupby("arm").size().to_dict() if completed_count else {}
    task_scale = {}
    if completed_count >= 2:
        for task in task_names:
            values = complete[f"ce/{task}"].to_numpy(float)
            task_scale[task] = {"mean": float(values.mean()), "sd": float(values.std(ddof=1))}
            complete[f"z/{task}"] = (values - task_scale[task]["mean"]) / task_scale[task]["sd"]
        complete["aggregate_standardized_loss"] = complete[[f"z/{task}" for task in task_names]].mean(axis=1)
        for index in complete.index:
            frame.loc[index, "aggregate_standardized_loss"] = complete.loc[index, "aggregate_standardized_loss"]

    by_arm: dict[str, dict[int, float]] = {}
    if completed_count:
        for arm, group in complete.groupby("arm"):
            by_arm[arm] = dict(zip(group["seed"].astype(int), group["aggregate_standardized_loss"].astype(float)))
    required_arms = set(arms["arms"])
    enough = (
        completed_count >= protocol["R2"]["minimum_completed_job_count"]
        and required_arms.issubset(by_arm)
        and all(len(by_arm[arm]) >= 2 for arm in required_arms)
    )
    contrasts: dict[str, object] = {}
    direction: dict[str, object] = {}
    verdict = "incomplete"
    power_rule_triggered = False
    if enough:
        contrasts["selected_minus_full"] = paired(by_arm["rank_selected"], by_arm["full_nonparametric"])
        contrasts["official_minus_selected"] = paired(by_arm["official_regmix"], by_arm["rank_selected"])
        selected_tasks = complete[complete["arm"] == "rank_selected"].set_index("seed")
        probe_tasks = complete[complete["arm"] == "h_probe"].set_index("seed")
        shared = sorted(set(selected_tasks.index) & set(probe_tasks.index))
        observed = np.asarray(
            [
                (probe_tasks.loc[shared, f"ce/{task}"] - selected_tasks.loc[shared, f"ce/{task}"]).mean()
                / task_scale[task]["sd"]
                for task in task_names
            ],
            dtype=float,
        )
        predicted = np.asarray(arms["predicted_probe_minus_selected_standardized_task_effect"], dtype=float)
        cosine = float(np.dot(observed, predicted) / (np.linalg.norm(observed) * np.linalg.norm(predicted)))
        sign_agreement = int(np.sum(np.sign(observed) == np.sign(predicted)))
        code_math = [task_names.index("github"), task_names.index("dm_mathematics")]
        common = [task_names.index("pile_cc"), task_names.index("wikipedia_en")]
        per_seed_effects = {}
        for seed in shared:
            per_seed_effects[seed] = np.asarray(
                [
                    (probe_tasks.loc[seed, f"ce/{task}"] - selected_tasks.loc[seed, f"ce/{task}"])
                    / task_scale[task]["sd"]
                    for task in task_names
                ]
            )
        code_values = {seed: float(value[code_math].mean()) for seed, value in per_seed_effects.items()}
        common_values = {seed: float(value[common].mean()) for seed, value in per_seed_effects.items()}
        zero = {seed: 0.0 for seed in shared}
        code_stats = paired(code_values, zero)
        common_stats = paired(common_values, zero)
        direction = {
            "shared_seeds": shared,
            "predicted_standardized_effect": predicted.tolist(),
            "observed_standardized_effect": observed.tolist(),
            "cosine": cosine,
            "sign_agreement": sign_agreement,
            "task_count": len(task_names),
            "code_math_probe_minus_selected": code_stats,
            "pilecc_wikipedia_probe_minus_selected": common_stats,
        }
        selected_full = contrasts["selected_minus_full"]["effect_sigma"]
        official_selected = contrasts["official_minus_selected"]["effect_sigma"]
        opposite = code_stats["mean"] * common_stats["mean"] < 0.0
        supported = (
            selected_full <= 0.5
            and official_selected >= 1.0
            and cosine >= 0.70
            and sign_agreement >= 10
            and opposite
            and abs(code_stats["effect_sigma"]) >= 1.0
            and abs(common_stats["effect_sigma"]) >= 1.0
        )
        falsified = selected_full > 1.0 or cosine < 0.0 or sign_agreement <= 6
        verdict = "supported" if supported else "falsified" if falsified else "inconclusive"
        ci_sigma = contrasts["selected_minus_full"]["ci95_sigma"]
        direction_unresolved = not supported and not falsified
        power_rule_triggered = (
            abs(selected_full) < 0.5
            and all(math.isfinite(value) for value in ci_sigma)
            and max(abs(value) for value in ci_sigma) < 0.5
            and direction_unresolved
        )

    job_ids = [value for value in args.job_ids.split(",") if value]
    jobs = slurm_records(job_ids, records)
    frame.to_csv(args.csv, index=False)
    if completed_count:
        fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))
        order = ["rank_selected", "full_nonparametric", "official_regmix", "h_probe"]
        for index, arm in enumerate(order):
            values = complete.loc[complete["arm"] == arm, "aggregate_standardized_loss"].to_numpy(float)
            axes[0].scatter(np.full(len(values), index), values, color="#0072B2", alpha=0.8)
            if len(values):
                axes[0].plot(index, values.mean(), marker="D", color="#D55E00")
        axes[0].set_xticks(range(len(order)), ["rank-selected", "ExtraTrees", "official", "h probe"], rotation=20)
        axes[0].set_ylabel("Mean task-standardized validation CE")
        axes[0].grid(axis="y", alpha=0.2)
        if direction:
            axes[1].scatter(direction["predicted_standardized_effect"], direction["observed_standardized_effect"], color="#009E73")
            for task, x_value, y_value in zip(task_names, direction["predicted_standardized_effect"], direction["observed_standardized_effect"]):
                axes[1].annotate(task, (x_value, y_value), fontsize=7)
            axes[1].axhline(0.0, color="#555555", linewidth=0.8)
            axes[1].axvline(0.0, color="#555555", linewidth=0.8)
        axes[1].set_xlabel("Frozen predicted probe-selected effect")
        axes[1].set_ylabel("Observed probe-selected effect")
        axes[1].grid(alpha=0.2)
        fig.tight_layout()
        args.plot.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(args.plot, dpi=180)
        plt.close(fig)
    payload = {
        "id": "TWODIAL-E2E-V1-R2",
        "verdict": verdict,
        "completed_jobs": completed_count,
        "target_jobs": protocol["R2"]["target_job_count"],
        "minimum_completed_jobs": protocol["R2"]["minimum_completed_job_count"],
        "arm_completed_counts": arm_counts,
        "task_standardization": task_scale,
        "contrasts": contrasts,
        "direction": direction,
        "power_rule_triggered": power_rule_triggered,
        "jobs": jobs,
        "gpu_node_hours": sum(record["gpu_node_hours"] for record in jobs),
        "result_hashes": result_hashes,
        "protocol_sha256": sha256(args.protocol),
        "arms_sha256": sha256(args.arms),
        "manifest_sha256": sha256(args.manifest),
        "csv": str(args.csv),
        "plot": str(args.plot) if args.plot.is_file() else None,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
