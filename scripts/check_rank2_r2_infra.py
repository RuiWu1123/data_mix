#!/usr/bin/env python3
"""Validate R2 environment, upstream patch, packed data, and all configs."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

import torch
import yaml


UPSTREAM = "dd9d1c3b2d7c1756b1a90f0ad7603068e9856cc6"


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
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--packed-audit", type=Path, required=True)
    parser.add_argument("--regmix-worktree", type=Path, required=True)
    parser.add_argument("--result-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    protocol = json.loads(args.protocol.read_text(encoding="utf-8"))
    arms = json.loads(args.arms.read_text(encoding="utf-8"))
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    packed = json.loads(args.packed_audit.read_text(encoding="utf-8"))
    training = protocol["R2"]["training_stack"]
    checks: dict[str, bool] = {}
    checks["torch_rocm"] = torch.__version__ == "2.7.1+rocm6.3" and torch.version.hip is not None
    head = subprocess.run(
        ["git", "-C", str(args.regmix_worktree), "rev-parse", "HEAD"],
        check=True,
        text=True,
        capture_output=True,
    ).stdout.strip()
    changed = subprocess.run(
        ["git", "-C", str(args.regmix_worktree), "diff", "--name-only"],
        check=True,
        text=True,
        capture_output=True,
    ).stdout.splitlines()
    checks["upstream_commit"] = head == UPSTREAM == training["repository_commit"]
    checks["patch_file_scope"] = sorted(changed) == sorted(
        [
            "model_training/lit_gpt/__init__.py",
            "model_training/lit_gpt/config.py",
            "model_training/lit_gpt/model.py",
            "model_training/pretrain/tinyllama.py",
        ]
    )
    config_text = (args.regmix_worktree / "model_training/lit_gpt/config.py").read_text(encoding="utf-8")
    tiny_1m_block = config_text.split('name="tinyllama_1M"', 1)[1].split("),", 1)[0]
    model_text = (args.regmix_worktree / "model_training/lit_gpt/model.py").read_text(encoding="utf-8")
    train_text = (args.regmix_worktree / "model_training/pretrain/tinyllama.py").read_text(encoding="utf-8")
    model_code = "\n".join(line for line in model_text.splitlines() if not line.lstrip().startswith("#"))
    train_code = "\n".join(line for line in train_text.splitlines() if not line.lstrip().startswith("#"))
    checks["fused_scope_absent"] = (
        '_norm_class="FusedRMSNorm"' not in tiny_1m_block
        and "return torch.nn.RMSNorm" in config_text
        and "from xformers.ops import SwiGLU" not in model_code
        and "apply_rotary_emb_func(q" not in model_code
        and "FusedCrossEntropyLoss()" not in train_code
    )
    checks["packed_audit"] = packed["passed"] and packed["required_train_prefixes"] == 17
    checks["validation_prefixes"] = packed["required_valid_prefixes"] == 13
    checks["config_count"] = manifest["config_count"] == 12 and len(manifest["records"]) == 12
    checks["manifest_hashes"] = manifest["protocol_sha256"] == sha256(args.protocol) and manifest[
        "arms_sha256"
    ] == sha256(args.arms)
    config_checks = []
    for record in manifest["records"]:
        path = Path(record["path"])
        config = yaml.safe_load(path.read_text(encoding="utf-8"))
        config_checks.append(
            sha256(path) == record["sha256"]
            and config["model_name"] == "tinyllama_1M"
            and config["global_batch_size"] == 512
            and config["micro_batch_size"] == 16
            and config["max_step"] == 954
            and config["warmup_steps"] == 100
            and config["eval_iters"] == 50
            and config["eval_step_interval"] == 954
            and config["save_step_interval"] == 954
            and len(config["train"]) == 17
            and len(config["valid"]) == 13
            and abs(sum(config["train"].values()) - record["raw_weight_sum"]) <= 1e-12
            and record["training_tokens"] == 1000341504
        )
    checks["all_configs"] = all(config_checks)
    preexisting = list(args.result_root.glob("*/result.json")) if args.result_root.exists() else []
    checks["no_preexisting_results"] = len(preexisting) == 0
    failures = sorted(name for name, passed in checks.items() if not passed)
    payload = {
        "id": "TWODIAL-E2E-V1-R2-INFRA-CHECK",
        "passed": not failures,
        "checks_passed": sum(checks.values()),
        "checks_total": len(checks),
        "failures": failures,
        "checks": checks,
        "torch": torch.__version__,
        "torch_hip": torch.version.hip,
        "upstream_commit": head,
        "patched_files": changed,
        "config_count": len(config_checks),
        "preexisting_results": len(preexisting),
        "packed_total_files": packed["total_files"],
        "packed_total_tokens": packed["total_tokens"],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
