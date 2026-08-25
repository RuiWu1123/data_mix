#!/usr/bin/env python3
"""Generate frozen RegMix training YAMLs for TWODIAL-E2E-V1 R2."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path

import yaml


SEEDS = (3406, 3407, 3408)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--arms", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    protocol = json.loads(args.protocol.read_text(encoding="utf-8"))
    arms = json.loads(args.arms.read_text(encoding="utf-8"))
    training = protocol["R2"]["training_stack"]
    expected_optimizer = (
        "AdamW, learning_rate=0.0004, min_lr=0.00001, betas=[0.9,0.95], "
        "weight_decay=0.1, grad_clip=1.0"
    )
    if training["optimizer"] != expected_optimizer:
        raise ValueError("frozen optimizer string changed")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    records = []
    for arm, weights in arms["arms"].items():
        train = dict(zip(arms["domains"], weights))
        valid = {f"valid_the_pile_{task}": 1.0 for task in arms["tasks"]}
        for seed in SEEDS:
            payload = {
                "train": train,
                "valid": valid,
                "data_seed": seed,
                "model_name": training["model"],
                "total_devices": 1,
                "num_of_devices": 1,
                "num_of_nodes": 1,
                "global_batch_size": training["global_batch_sequences"],
                "micro_batch_size": training["device_batch_sequences"],
                "max_step": training["optimizer_steps"],
                "warmup_steps": training["warmup_steps"],
                "log_step_interval": 10,
                "eval_iters": protocol["R2"]["evaluation"]["validation_batches_per_task"],
                "save_step_interval": training["optimizer_steps"],
                "eval_step_interval": training["optimizer_steps"],
                "only_save_model": True,
                "learning_rate": 0.0004,
                "min_lr": 0.00001,
                "decay_lr": True,
                "weight_decay": 0.1,
                "beta1": 0.9,
                "beta2": 0.95,
                "grad_clip": 1.0,
            }
            path = args.output_dir / f"{arm}_seed{seed}.yaml"
            path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
            records.append(
                {
                    "arm": arm,
                    "seed": seed,
                    "path": str(path),
                    "sha256": sha256(path),
                    "raw_weight_sum": sum(weights),
                    "effective_weight_sum_after_official_sampler_normalization": 1.0,
                    "training_tokens": training["tokens_per_job"],
                    "validation_domains": len(valid),
                }
            )
    manifest = {
        "id": "TWODIAL-E2E-V1-R2-CONFIGS",
        "config_count": len(records),
        "arm_count": len(arms["arms"]),
        "seeds_per_arm": len(SEEDS),
        "records": records,
        "protocol_sha256": sha256(args.protocol),
        "arms_sha256": sha256(args.arms),
        "command": " ".join(os.sys.argv),
    }
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
