#!/usr/bin/env python3
"""Run frozen TWODIAL-E2E-V1 R1 and construct the R2 arms."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yaml
from scipy.linalg import helmert
from sklearn.ensemble import ExtraTreesRegressor


META = {"run", "name", "index", "Unnamed: 0"}
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
REGMIX_VALID_PREFIXES = {
    "metric/the_pile_arxiv_val_loss": "arxiv",
    "metric/the_pile_freelaw_val_loss": "freelaw",
    "metric/the_pile_pubmed_central_val_loss": "pubmed_central",
    "metric/the_pile_wikipedia_en_val_loss": "wikipedia_en",
    "metric/the_pile_dm_mathematics_val_loss": "dm_mathematics",
    "metric/the_pile_github_val_loss": "github",
    "metric/the_pile_stackexchange_val_loss": "stackexchange",
    "metric/the_pile_gutenberg_pg_19_val_loss": "gutenberg_pg_19",
    "metric/the_pile_pile_cc_val_loss": "pile_cc",
    "metric/the_pile_ubuntu_irc_val_loss": "ubuntu_irc",
    "metric/the_pile_hackernews_val_loss": "hackernews",
    "metric/the_pile_pubmed_abstracts_val_loss": "pubmed_abstracts",
    "metric/the_pile_uspto_backgrounds_val_loss": "uspto_backgrounds",
}


def seed(label: str) -> int:
    digest = hashlib.sha256(("TWODIAL-E2E-V1:" + label).encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "little")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fold(label: str, folds: int = 5) -> int:
    return hashlib.sha256(label.encode("utf-8")).digest()[0] % folds


def hellinger(weights: np.ndarray) -> np.ndarray:
    weights = np.asarray(weights, dtype=float)
    if np.any(~np.isfinite(weights)) or np.any(weights < 0.0):
        raise ValueError("mixture weights must be finite and nonnegative")
    row_sum = weights.sum(axis=1, keepdims=True)
    if np.any(row_sum <= 0.0):
        raise ValueError("mixture row has nonpositive mass")
    closed = weights / row_sum
    return np.sqrt(closed) @ helmert(closed.shape[1], full=False).T


def fit_rrr(x: np.ndarray, y: np.ndarray, rank: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    design = np.column_stack([np.ones(len(x)), x])
    coefficient = np.linalg.lstsq(design, y, rcond=None)[0]
    intercept = coefficient[0]
    slope = coefficient[1:]
    u, singular, vt = np.linalg.svd(slope, full_matrices=False)
    kept = min(rank, len(singular))
    reduced = (u[:, :kept] * singular[:kept]) @ vt[:kept]
    return intercept, reduced, singular


def cross_validate(
    name: str,
    x: np.ndarray,
    y: np.ndarray,
    row_ids: list[str],
    ranks: tuple[int, ...] = (1, 2, 3, 4, 5, 6),
) -> dict[str, object]:
    assigned = np.asarray([fold(f"R1:{name}:{row_id}") for row_id in row_ids], dtype=int)
    squared_errors: dict[str, list[np.ndarray]] = {f"rank{rank}": [] for rank in ranks}
    squared_errors["full_linear"] = []
    squared_errors["extra_trees"] = []
    fold_rows = []
    for heldout_fold in range(5):
        train = assigned != heldout_fold
        test = assigned == heldout_fold
        if train.sum() <= x.shape[1] + 1 or test.sum() == 0:
            raise ValueError(f"{name} fold {heldout_fold} lacks rows for its design")
        mean = y[train].mean(axis=0)
        scale = y[train].std(axis=0, ddof=1)
        if np.any(~np.isfinite(scale)) or np.any(scale <= 1e-8):
            raise ValueError(f"{name} fold {heldout_fold} has an invalid task scale")
        train_y = (y[train] - mean) / scale
        test_y = (y[test] - mean) / scale
        design = np.column_stack([np.ones(train.sum()), x[train]])
        full_coefficient = np.linalg.lstsq(design, train_y, rcond=None)[0]
        full_prediction = np.column_stack([np.ones(test.sum()), x[test]]) @ full_coefficient
        squared_errors["full_linear"].append(np.square(test_y - full_prediction))
        for rank in ranks:
            intercept, slope, _ = fit_rrr(x[train], train_y, rank)
            prediction = intercept + x[test] @ slope
            squared_errors[f"rank{rank}"].append(np.square(test_y - prediction))
        forest = ExtraTreesRegressor(
            n_estimators=500,
            min_samples_leaf=2,
            max_features=1.0,
            random_state=seed(f"R1:{name}:fold={heldout_fold}:extra-trees") % (2**32 - 1),
            n_jobs=-1,
        )
        forest.fit(x[train], train_y)
        forest_prediction = forest.predict(x[test])
        squared_errors["extra_trees"].append(np.square(test_y - forest_prediction))
        fold_rows.append({"fold": heldout_fold, "train_rows": int(train.sum()), "test_rows": int(test.sum())})
    rmse = {
        estimator: float(np.sqrt(np.concatenate(errors, axis=0).mean()))
        for estimator, errors in squared_errors.items()
    }
    return {
        "name": name,
        "rows": int(len(x)),
        "features": int(x.shape[1]),
        "tasks": int(y.shape[1]),
        "folds": fold_rows,
        "rmse": rmse,
    }


def load_olmix(data: Path) -> list[tuple[str, np.ndarray, np.ndarray, list[str], list[str]]]:
    tables = []
    for domains in (6, 12, 18, 24):
        ratios = pd.read_csv(data / f"m{domains}_ratios.csv")
        metrics = pd.read_csv(data / f"m{domains}_metrics.csv")
        id_column = "run" if "run" in ratios and "run" in metrics else "index"
        domain_columns = [column for column in ratios.columns if column not in META]
        task_columns = [column for column in metrics.columns if column not in META]
        joined = ratios[[id_column] + domain_columns].merge(
            metrics[[id_column] + task_columns], on=id_column, how="inner"
        )
        weight = joined[domain_columns].apply(pd.to_numeric, errors="coerce").to_numpy(float)
        response = joined[task_columns].apply(pd.to_numeric, errors="coerce").to_numpy(float)
        finite_tasks = np.all(np.isfinite(response), axis=0)
        response = response[:, finite_tasks]
        task_columns = list(np.asarray(task_columns)[finite_tasks])
        finite_rows = np.all(np.isfinite(weight), axis=1) & np.all(np.isfinite(response), axis=1)
        tables.append(
            (
                f"olmix_m{domains}",
                hellinger(weight[finite_rows]),
                response[finite_rows],
                joined.loc[finite_rows, id_column].astype(str).tolist(),
                task_columns,
            )
        )
    return tables


def load_regmix(data: Path) -> list[tuple[str, np.ndarray, np.ndarray, list[str], list[str]]]:
    specifications = [
        ("regmix_train_1m", "train_mixture_1m.csv", "train_pile_loss_1m.csv"),
        ("regmix_test_1m", "test_mixture_1m.csv", "test_pile_loss_1m.csv"),
        ("regmix_test_60m", "test_mixture_60m.csv", "test_pile_loss_60m.csv"),
        ("regmix_test_1b", "test_mixture_1B.csv", "test_pile_loss_1B.csv"),
    ]
    tables = []
    for name, mixture_name, loss_name in specifications:
        mixture = pd.read_csv(data / mixture_name)
        loss = pd.read_csv(data / loss_name)
        domain_columns = [column for column in mixture.columns if column != "index"]
        task_columns = [column for column in loss.columns if column != "index"]
        joined = mixture.merge(loss, on="index", how="inner")
        weights = joined[domain_columns].apply(pd.to_numeric, errors="coerce").to_numpy(float)
        response = joined[task_columns].apply(pd.to_numeric, errors="coerce").to_numpy(float)
        finite = np.all(np.isfinite(weights), axis=1) & np.all(np.isfinite(response), axis=1)
        tables.append(
            (
                name,
                hellinger(weights[finite]),
                response[finite],
                joined.loc[finite, "index"].astype(str).tolist(),
                task_columns,
            )
        )
    return tables


def parse_datadecide_group(value: str) -> tuple[str, str, str, int]:
    seeded = re.fullmatch(r"(.+)-([^-]+)-(5xC)-([0-9]+)", value)
    unseeded = re.fullmatch(r"(.+)-([^-]+)-(5xC)", value)
    match = seeded or unseeded
    if match is None or match.group(2) not in MODEL_PARAMS:
        raise ValueError(f"cannot parse official DataDecide group: {value}")
    raw_seed = int(match.group(4)) if seeded else 6198
    normalized_seed = 6198 if raw_seed == 2 else raw_seed
    return match.group(1), match.group(2), match.group(3), normalized_seed


def load_datadecide(path: Path) -> tuple[np.ndarray, np.ndarray, list[str], list[str], float, dict[str, object]]:
    frame = pd.read_csv(path)
    task_columns = [column for column in frame.columns if column.startswith("eval/")]
    parsed = [parse_datadecide_group(str(value)) for value in frame["group"]]
    frame = frame.copy()
    frame["recipe"] = [value[0] for value in parsed]
    frame["model"] = [value[1] for value in parsed]
    frame["seed"] = [value[3] for value in parsed]
    frame["params"] = frame["model"].map(MODEL_PARAMS)
    max_step = frame.groupby(["recipe", "model", "seed"])["step"].transform("max")
    final = frame[frame["step"] == max_step].copy()
    for column in task_columns:
        final[column] = np.log(pd.to_numeric(final[column], errors="coerce"))
    finite = np.all(np.isfinite(final[task_columns].to_numpy(float)), axis=1)
    final = final.loc[finite].copy()
    cell_groups = final.groupby(["recipe", "model"], sort=True)
    eligible = cell_groups.filter(lambda group: group["seed"].nunique() >= 2)
    if eligible.empty:
        raise ValueError("DataDecide has no multi-seed final-step cells")
    task_scale = eligible.groupby(["recipe", "model"])[task_columns].mean().std(axis=0, ddof=1)
    standard_errors = []
    for _, group in eligible.groupby(["recipe", "model"], sort=True):
        seeds = group["seed"].nunique()
        scaled_se = group[task_columns].std(axis=0, ddof=1) / np.sqrt(seeds) / task_scale
        standard_errors.extend(scaled_se[np.isfinite(scaled_se)].tolist())
    noise_floor = float(np.median(standard_errors))

    means = eligible.groupby(["recipe", "model"], sort=True)[task_columns].mean().reset_index()
    recipes = sorted(means["recipe"].unique())
    recipe_index = {recipe: index for index, recipe in enumerate(recipes)}
    one_hot = np.zeros((len(means), len(recipes)), dtype=float)
    for row_index, recipe in enumerate(means["recipe"]):
        one_hot[row_index, recipe_index[recipe]] = 1.0
    log_params = np.log(means["model"].map(MODEL_PARAMS).to_numpy(float))
    log_params = (log_params - log_params.mean()) / log_params.std(ddof=1)
    design = np.column_stack([one_hot, one_hot * log_params[:, None]])
    response = means[task_columns].to_numpy(float)
    row_ids = [f"{recipe}:{model}" for recipe, model in zip(means["recipe"], means["model"])]
    audit = {
        "raw_rows": int(len(frame)),
        "final_rows": int(len(final)),
        "eligible_seed_rows": int(len(eligible)),
        "recipe_model_cells": int(len(means)),
        "recipes": len(recipes),
        "models": int(means["model"].nunique()),
        "tasks": len(task_columns),
        "minimum_seeds_per_eligible_cell": int(
            eligible.groupby(["recipe", "model"])["seed"].nunique().min()
        ),
        "noise_standard_error_observations": len(standard_errors),
    }
    return design, response, row_ids, task_columns, noise_floor, audit


def source_summary(tables: dict[str, dict[str, object]], prefix: str) -> dict[str, float]:
    keys = [key for key in tables if key.startswith(prefix)]
    estimators = list(tables[keys[0]]["rmse"])
    return {
        estimator: float(np.median([tables[key]["rmse"][estimator] for key in keys]))
        for estimator in estimators
    }


def source_vote(summary: dict[str, float], sigma: float) -> dict[str, object]:
    best_baseline = min(summary["full_linear"], summary["extra_trees"])
    values = {
        "rank2_minus_best_baseline_sigma": (summary["rank2"] - best_baseline) / sigma,
        "rank1_minus_rank2_sigma": (summary["rank1"] - summary["rank2"]) / sigma,
        "rank2_minus_rank3_sigma": (summary["rank2"] - summary["rank3"]) / sigma,
        "rank1_minus_best_baseline_sigma": (summary["rank1"] - best_baseline) / sigma,
    }
    checks = {
        "rank2_catches_baseline": values["rank2_minus_best_baseline_sigma"] <= 0.5,
        "rank2_beats_rank1": values["rank1_minus_rank2_sigma"] >= 1.0,
        "rank3_marginal": values["rank2_minus_rank3_sigma"] <= 0.5,
    }
    return {
        "best_baseline": "full_linear" if summary["full_linear"] <= summary["extra_trees"] else "extra_trees",
        **values,
        "checks": checks,
        "rank2_pass": all(checks.values()),
        "rank1_pass": values["rank1_minus_best_baseline_sigma"] <= 0.5,
    }


def orient_h(task_columns: list[str], task_loading: np.ndarray) -> tuple[np.ndarray, float]:
    normalized = [REGMIX_VALID_PREFIXES.get(column, column) for column in task_columns]
    positive = [normalized.index(name) for name in ("github", "dm_mathematics")]
    negative = [normalized.index(name) for name in ("pile_cc", "wikipedia_en")]
    contrast = float(task_loading[positive].mean() - task_loading[negative].mean())
    if abs(contrast) <= 1e-12:
        raise ValueError("RegMix h orientation anchor is undefined")
    return (task_loading if contrast > 0.0 else -task_loading), abs(contrast)


def construct_arms(regmix_dir: Path, selected_rank: int) -> dict[str, object]:
    mixture = pd.read_csv(regmix_dir / "train_mixture_1m.csv")
    loss = pd.read_csv(regmix_dir / "train_pile_loss_1m.csv")
    domains = [column for column in mixture.columns if column != "index"]
    tasks = [column for column in loss.columns if column != "index"]
    joined = mixture.merge(loss, on="index", how="inner")
    train_weights = joined[domains].to_numpy(float)
    x = hellinger(train_weights)
    y = joined[tasks].to_numpy(float)
    y_mean = y.mean(axis=0)
    y_scale = y.std(axis=0, ddof=1)
    yz = (y - y_mean) / y_scale
    intercept, selected_slope, singular = fit_rrr(x, yz, selected_rank)

    candidates = pd.read_csv(regmix_dir / "test_mixture_1m.csv")
    candidate_weights = candidates[domains].to_numpy(float)
    candidate_x = hellinger(candidate_weights)
    selected_prediction = intercept + candidate_x @ selected_slope
    selected_index = int(np.argmin(selected_prediction.mean(axis=1)))
    forest = ExtraTreesRegressor(
        n_estimators=500,
        min_samples_leaf=2,
        max_features=1.0,
        random_state=seed("R2:arm:extra-trees") % (2**32 - 1),
        n_jobs=-1,
    )
    forest.fit(x, yz)
    forest_prediction = forest.predict(candidate_x)
    forest_index = int(np.argmin(forest_prediction.mean(axis=1)))

    _, full_rank2_slope, _ = fit_rrr(x, yz, 2)
    u, s, vt = np.linalg.svd(full_rank2_slope, full_matrices=False)
    h_task, anchor = orient_h(tasks, s[1] * vt[1])
    orientation = 1.0 if np.allclose(h_task, s[1] * vt[1]) else -1.0
    h_coordinate = orientation * u[:, 1]
    h_score = (candidate_x - x.mean(axis=0)) @ h_coordinate
    distance = np.abs(candidate_weights - candidate_weights[selected_index]).sum(axis=1)
    eligible = np.flatnonzero((distance >= 0.20) & (distance <= 0.60))
    fallback_used = False
    if len(eligible) == 0:
        eligible = np.flatnonzero(distance >= 0.20)
        fallback_used = True
    if len(eligible) == 0:
        raise ValueError("no released candidate is separated from the selected-rank arm")
    probe_index = int(eligible[np.argmax(h_score[eligible])])

    official_path = regmix_dir.parent / "mixture_config" / "config_1b" / "regmix.yaml"
    official = yaml.safe_load(official_path.read_text(encoding="utf-8"))["train"]
    official_weights = np.asarray([float(official[domain]) for domain in domains])
    official_weights /= official_weights.sum()
    rank2_intercept, rank2_slope, _ = fit_rrr(x, yz, 2)
    probe_effect = (
        rank2_intercept + candidate_x[probe_index] @ rank2_slope
        - (rank2_intercept + candidate_x[selected_index] @ rank2_slope)
    )
    arms = {
        "rank_selected": candidate_weights[selected_index].tolist(),
        "full_nonparametric": candidate_weights[forest_index].tolist(),
        "official_regmix": official_weights.tolist(),
        "h_probe": candidate_weights[probe_index].tolist(),
    }
    return {
        "domains": domains,
        "tasks": [REGMIX_VALID_PREFIXES[column] for column in tasks],
        "selected_rank": selected_rank,
        "candidate_row_indices": {
            "rank_selected": int(candidates.iloc[selected_index]["index"]),
            "full_nonparametric": int(candidates.iloc[forest_index]["index"]),
            "h_probe": int(candidates.iloc[probe_index]["index"]),
        },
        "arms": arms,
        "arm_weight_sums": {name: float(sum(weights)) for name, weights in arms.items()},
        "rank_selected_vs_full_l1": float(
            np.abs(candidate_weights[selected_index] - candidate_weights[forest_index]).sum()
        ),
        "rank_selected_vs_probe_l1": float(distance[probe_index]),
        "probe_fallback_used": fallback_used,
        "h_orientation_anchor": anchor,
        "rank2_singular_values": singular.tolist(),
        "predicted_probe_minus_selected_standardized_task_effect": probe_effect.tolist(),
        "predicted_probe_minus_selected_sign": np.sign(probe_effect).astype(int).tolist(),
        "official_config": str(official_path),
    }


def plot_curve(source_summaries: dict[str, dict[str, float]], sigma: float, output: Path) -> None:
    ranks = np.arange(1, 7)
    colors = {"olmix": "#0072B2", "regmix": "#D55E00", "datadecide": "#009E73"}
    fig, axis = plt.subplots(figsize=(8.4, 5.2))
    for source, summary in source_summaries.items():
        curve = [summary[f"rank{rank}"] for rank in ranks]
        axis.plot(ranks, curve, marker="o", linewidth=2, label=f"{source} reduced rank", color=colors[source])
        baseline = min(summary["full_linear"], summary["extra_trees"])
        axis.axhline(baseline, linestyle="--", linewidth=1, color=colors[source], alpha=0.65)
    axis.plot([], [], linestyle="--", color="#444444", label="best full/ExtraTrees baseline")
    axis.text(6.05, sigma, f"DataDecide seed SE = {sigma:.4f}", va="center", fontsize=9)
    axis.set_xlabel("Slope-operator rank")
    axis.set_ylabel("Held-out task-standardized RMSE")
    axis.set_xticks(ranks)
    axis.grid(alpha=0.2)
    axis.legend(frameon=False, fontsize=9)
    fig.tight_layout()
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=180)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--olmix", type=Path, required=True)
    parser.add_argument("--regmix", type=Path, required=True)
    parser.add_argument("--datadecide", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--arms-output", type=Path, required=True)
    parser.add_argument("--plot", type=Path, required=True)
    args = parser.parse_args()
    protocol = json.loads(args.protocol.read_text(encoding="utf-8"))
    if protocol.get("protocol_id") != "TWODIAL-E2E-V1":
        raise SystemExit("R1 requires TWODIAL-E2E-V1")

    table_results: dict[str, dict[str, object]] = {}
    input_paths = [args.protocol]
    for name, x, y, row_ids, _ in load_olmix(args.olmix):
        table_results[name] = cross_validate(name, x, y, row_ids)
        domains = name.split("m")[-1]
        input_paths.extend([args.olmix / f"m{domains}_ratios.csv", args.olmix / f"m{domains}_metrics.csv"])
    for name, x, y, row_ids, _ in load_regmix(args.regmix):
        table_results[name] = cross_validate(name, x, y, row_ids)
    input_paths.extend(sorted(args.regmix.glob("*.csv")))
    dd_x, dd_y, dd_ids, _, sigma, dd_audit = load_datadecide(args.datadecide)
    table_results["datadecide"] = cross_validate("datadecide", dd_x, dd_y, dd_ids)
    input_paths.append(args.datadecide)

    summaries = {
        "olmix": source_summary(table_results, "olmix_"),
        "regmix": source_summary(table_results, "regmix_"),
        "datadecide": source_summary(table_results, "datadecide"),
    }
    votes = {source: source_vote(summary, sigma) for source, summary in summaries.items()}
    rank2_votes = sum(vote["rank2_pass"] for vote in votes.values())
    rank1_votes = sum(vote["rank1_pass"] for vote in votes.values())
    if rank2_votes >= 2:
        interpretation = "rank2-sufficient"
        selected_rank = 2
    elif rank1_votes >= 2:
        interpretation = "rank1-sufficient"
        selected_rank = 1
    else:
        interpretation = "rank3+-sufficient"
        selected_rank = 3
    arms = construct_arms(args.regmix, selected_rank)
    plot_curve(summaries, sigma, args.plot)
    payload = {
        "id": "TWODIAL-E2E-V1-R1",
        "verdict": interpretation,
        "selected_rank_for_r2": selected_rank,
        "datadecide_seed_noise_floor": sigma,
        "datadecide_audit": dd_audit,
        "source_rank2_vote_count": rank2_votes,
        "source_rank1_vote_count": rank1_votes,
        "source_votes": votes,
        "source_summaries": summaries,
        "tables": table_results,
        "thresholds_in_datadecide_sigma": protocol["R1"]["thresholds_in_datadecide_sigma"],
        "plot": str(args.plot),
        "protocol_sha256": sha256(args.protocol),
        "inputs": [str(path) for path in input_paths],
        "input_sha256": {str(path): sha256(path) for path in input_paths},
        "command": " ".join(os.sys.argv),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    arms_payload = {
        "id": "TWODIAL-E2E-V1-R2-ARMS",
        "r1_verdict": interpretation,
        **arms,
        "protocol_sha256": sha256(args.protocol),
        "r1_result": str(args.output),
        "inputs": [str(args.regmix / "train_mixture_1m.csv"), str(args.regmix / "train_pile_loss_1m.csv"), str(args.regmix / "test_mixture_1m.csv"), arms["official_config"]],
        "command": " ".join(os.sys.argv),
    }
    args.arms_output.parent.mkdir(parents=True, exist_ok=True)
    args.arms_output.write_text(json.dumps(arms_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"r1": payload, "arms": arms_payload}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
