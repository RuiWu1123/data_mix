#!/usr/bin/env python3
"""Frozen numerical primitives for ONEDIAL-V3 Act II."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

import numpy as np
from scipy.linalg import helmert


META_COLUMNS = {"run", "name", "index", "Unnamed: 0"}


def protocol_seed(label: str) -> int:
    digest = hashlib.sha256(("ONEDIAL-V1:" + label).encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "little")


def interior_weight_seed(namespace: str, domains: int, scenario: str, replicate: int) -> int:
    label = (
        "ONEDIAL-V2:Q1-interior-weights:"
        f"{namespace}:m={domains}:scenario={scenario}:replicate={replicate}"
    )
    return int.from_bytes(hashlib.sha256(label.encode("utf-8")).digest()[:8], "little")


def sha_fold(label: str) -> int:
    return hashlib.sha256(label.encode("utf-8")).digest()[0] % 2


def close_weights(weights: np.ndarray) -> np.ndarray:
    weights = np.asarray(weights, dtype=float)
    row_sum = weights.sum(axis=1, keepdims=True)
    if np.any(~np.isfinite(weights)) or np.any(weights < 0.0) or np.any(row_sum <= 0.0):
        raise ValueError("weights must be finite, nonnegative, and have positive row sums")
    return weights / row_sum


def mixture_coordinates(weights: np.ndarray, pipeline: str, delta: float = 1e-6) -> np.ndarray:
    closed = close_weights(weights)
    basis = helmert(closed.shape[1], full=False).T
    if pipeline == "A":
        replaced = np.empty_like(closed)
        for row_index, row in enumerate(closed):
            zeros = row <= 0.0
            zero_count = int(zeros.sum())
            positive_sum = float(row[~zeros].sum())
            if zero_count * delta >= 1.0 or positive_sum <= 0.0:
                raise ValueError("multiplicative zero replacement is undefined")
            replaced[row_index, zeros] = delta
            replaced[row_index, ~zeros] = row[~zeros] * (1.0 - zero_count * delta) / positive_sum
        return np.log(replaced) @ basis
    if pipeline == "B":
        return np.sqrt(closed) @ basis
    raise ValueError(f"unknown coordinate pipeline: {pipeline}")


@dataclass(frozen=True)
class DesignCache:
    x: np.ndarray
    folds: np.ndarray
    train_indices: tuple[np.ndarray, np.ndarray]
    heldout_indices: tuple[np.ndarray, np.ndarray]
    train_x_means: tuple[np.ndarray, np.ndarray]
    train_pinvs: tuple[np.ndarray, np.ndarray]
    global_x_mean: np.ndarray
    global_pinv: np.ndarray


def prepare_design(x: np.ndarray, folds: np.ndarray) -> DesignCache:
    x = np.asarray(x, dtype=float)
    folds = np.asarray(folds, dtype=int)
    if x.ndim != 2 or folds.shape != (x.shape[0],):
        raise ValueError("invalid design or fold shape")
    if np.any(~np.isfinite(x)) or set(np.unique(folds)) != {0, 1}:
        raise ValueError("design must be finite and contain both folds")
    dimension = x.shape[1]
    train_indices = []
    heldout_indices = []
    train_x_means = []
    train_pinvs = []
    for heldout_fold in (0, 1):
        train = np.flatnonzero(folds != heldout_fold)
        heldout = np.flatnonzero(folds == heldout_fold)
        x_mean = x[train].mean(axis=0)
        centered = x[train] - x_mean
        if np.linalg.matrix_rank(centered) != dimension:
            raise ValueError(f"cross-fit training design for fold {heldout_fold} is rank deficient")
        train_indices.append(train)
        heldout_indices.append(heldout)
        train_x_means.append(x_mean)
        train_pinvs.append(np.linalg.pinv(centered))
    global_x_mean = x.mean(axis=0)
    global_centered = x - global_x_mean
    if np.linalg.matrix_rank(global_centered) != dimension:
        raise ValueError("stacked residual design is rank deficient")
    return DesignCache(
        x=x,
        folds=folds,
        train_indices=(train_indices[0], train_indices[1]),
        heldout_indices=(heldout_indices[0], heldout_indices[1]),
        train_x_means=(train_x_means[0], train_x_means[1]),
        train_pinvs=(train_pinvs[0], train_pinvs[1]),
        global_x_mean=global_x_mean,
        global_pinv=np.linalg.pinv(global_centered),
    )


def _as_response_batch(response: np.ndarray) -> tuple[np.ndarray, bool]:
    response = np.asarray(response, dtype=float)
    if response.ndim == 2:
        return response[None, ...], True
    if response.ndim == 3:
        return response, False
    raise ValueError("response must have shape rows-by-tasks or batch-by-rows-by-tasks")


def fit_crossfitted(
    cache: DesignCache,
    response: np.ndarray,
    scale_floor: float = 1e-8,
    return_components: bool = False,
) -> dict[str, np.ndarray]:
    """Peel cross-fitted rank one and fit the residual response operator."""
    y, squeeze = _as_response_batch(response)
    if y.shape[1] != cache.x.shape[0] or np.any(~np.isfinite(y)):
        raise ValueError("response is nonfinite or does not match the design")
    batch, rows, tasks = y.shape
    residual = np.empty((batch, rows, tasks), dtype=float)
    prediction = np.empty_like(residual)
    for fold in (0, 1):
        train = cache.train_indices[fold]
        heldout = cache.heldout_indices[fold]
        train_y = y[:, train, :]
        mean = train_y.mean(axis=1, keepdims=True)
        scale = train_y.std(axis=1, ddof=1, keepdims=True)
        if np.any(~np.isfinite(scale)) or np.any(scale < scale_floor):
            raise ValueError("fit-fold response scale is below the registered floor")
        standardized_train = (train_y - mean) / scale
        coefficient = np.einsum(
            "pn,bnt->bpt", cache.train_pinvs[fold], standardized_train, optimize=True
        )
        gram = np.einsum("bpt,bqt->bpq", coefficient, coefficient, optimize=True)
        _, eigenvectors = np.linalg.eigh(gram)
        leading_coordinate = eigenvectors[:, :, -1]
        leading_task_score = np.einsum(
            "bp,bpt->bt", leading_coordinate, coefficient, optimize=True
        )
        heldout_score = np.einsum(
            "np,bp->bn",
            cache.x[heldout] - cache.train_x_means[fold],
            leading_coordinate,
            optimize=True,
        )
        fold_prediction = heldout_score[:, :, None] * leading_task_score[:, None, :]
        standardized_heldout = (y[:, heldout, :] - mean) / scale
        prediction[:, heldout, :] = fold_prediction
        residual[:, heldout, :] = standardized_heldout - fold_prediction

    centered_residual = residual - residual.mean(axis=1, keepdims=True)
    residual_coefficient = np.einsum(
        "pn,bnt->bpt", cache.global_pinv, centered_residual, optimize=True
    )
    residual_gram = np.einsum(
        "bpt,bqt->bpq", residual_coefficient, residual_coefficient, optimize=True
    )
    eigenvalues, eigenvectors = np.linalg.eigh(residual_gram)
    order = np.arange(residual_gram.shape[1] - 1, -1, -1)
    singular_values = np.sqrt(np.maximum(eigenvalues[:, order], 0.0))
    leading_coordinate = eigenvectors[:, :, -1]
    leading_value = singular_values[:, 0]
    leading_task_loading = np.einsum(
        "bp,bpt->bt", leading_coordinate, residual_coefficient, optimize=True
    )
    nonzero = leading_value > np.finfo(float).tiny
    leading_task_loading[nonzero] /= leading_value[nonzero, None]
    result = {
        "residual_singular_values": singular_values,
        "h_task_loading": leading_task_loading,
    }
    if return_components:
        result["rank1_prediction"] = prediction
        result["crossfit_residual"] = residual
        result["residual_coefficient"] = residual_coefficient
    if squeeze:
        return {key: value[0] for key, value in result.items()}
    return result


def holm_rejections(p_values: np.ndarray, alpha: float = 0.01) -> np.ndarray:
    p_values = np.asarray(p_values, dtype=float)
    order = np.argsort(p_values, kind="stable")
    rejected = np.zeros(len(p_values), dtype=bool)
    for step, index in enumerate(order):
        if p_values[index] <= alpha / (len(p_values) - step):
            rejected[index] = True
        else:
            break
    return rejected


def leading_significant_dimension(p_values: np.ndarray, alpha: float = 0.01) -> int:
    rejected = holm_rejections(p_values, alpha=alpha)
    dimension = 0
    for is_rejected in rejected:
        if not is_rejected:
            break
        dimension += 1
    return dimension


def permuted_residual_batch(residual: np.ndarray, rng: np.random.Generator, batch: int) -> np.ndarray:
    """Independently and uniformly permute rows for every batch item and task."""
    rows, tasks = residual.shape
    keys = rng.random((batch, tasks, rows))
    indices = np.argsort(keys, axis=2)
    source = np.broadcast_to(residual.T, indices.shape)
    return np.take_along_axis(source, indices, axis=2).transpose(0, 2, 1)


def permutation_dimension_test(
    cache: DesignCache,
    response: np.ndarray,
    rng: np.random.Generator,
    permutations: int = 4999,
    family_size: int = 4,
    alpha: float = 0.01,
    batch_size: int = 128,
) -> dict[str, object]:
    observed = fit_crossfitted(cache, response, return_components=True)
    observed_singular = observed["residual_singular_values"][:family_size]
    if len(observed_singular) != family_size:
        raise ValueError("residual operator has fewer than four registered directions")
    counts = np.zeros(family_size, dtype=np.int64)
    processed = 0
    stopped_early = False
    while processed < permutations:
        current = min(batch_size, permutations - processed)
        permuted = permuted_residual_batch(observed["crossfit_residual"], rng, current)
        pseudo_response = observed["rank1_prediction"][None, :, :] + permuted
        null_singular = fit_crossfitted(cache, pseudo_response)["residual_singular_values"]
        counts += np.sum(null_singular[:, :family_size] >= observed_singular[None, :], axis=0)
        processed += current
        if processed < permutations:
            remaining = permutations - processed
            denominator = permutations + 1
            lower = (1.0 + counts) / denominator
            upper = (1.0 + counts + remaining) / denominator
            lower_dimension = leading_significant_dimension(lower, alpha=alpha)
            upper_dimension = leading_significant_dimension(upper, alpha=alpha)
            if lower_dimension == upper_dimension:
                stopped_early = True
                break
    if stopped_early:
        p_lower = (1.0 + counts) / (permutations + 1)
        p_upper = (1.0 + counts + permutations - processed) / (permutations + 1)
        dimension = leading_significant_dimension(p_lower, alpha=alpha)
        p_values = None
    else:
        p_values_array = (1.0 + counts) / (permutations + 1)
        p_lower = p_values_array
        p_upper = p_values_array
        p_values = p_values_array.tolist()
        dimension = leading_significant_dimension(p_values_array, alpha=alpha)
    return {
        "significant_dimension": dimension,
        "observed_singular_values": observed_singular.tolist(),
        "permutation_exceedance_counts": counts.tolist(),
        "permutations_processed": processed,
        "stopped_early": stopped_early,
        "p_values": p_values,
        "p_value_lower_bounds": p_lower.tolist(),
        "p_value_upper_bounds": p_upper.tolist(),
        "h_task_loading": observed["h_task_loading"],
    }
