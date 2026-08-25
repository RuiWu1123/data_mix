#!/usr/bin/env python3
"""Run a no-update GPU forward check on the patched RegMix tinyllama_1M."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import torch

from lit_gpt.config import Config
from lit_gpt.model import GPT


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--patch", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    torch.manual_seed(20260825)
    device = torch.device("cuda")
    config = Config.from_name("tinyllama_1M")
    model = GPT(config).to(device=device, dtype=torch.bfloat16).eval()
    inputs = torch.randint(0, config.vocab_size, (2, 32), device=device)
    with torch.no_grad():
        logits = model(inputs)
    payload = {
        "id": "TWODIAL-E2E-V1-ROCM-FORWARD-CHECK",
        "passed": bool(torch.isfinite(logits).all()),
        "torch": torch.__version__,
        "torch_hip": torch.version.hip,
        "device": torch.cuda.get_device_name(0),
        "model": config.name,
        "parameters": sum(parameter.numel() for parameter in model.parameters()),
        "input_shape": list(inputs.shape),
        "logit_shape": list(logits.shape),
        "logit_dtype": str(logits.dtype),
        "finite_logits": int(torch.isfinite(logits).sum()),
        "total_logits": logits.numel(),
        "patch_sha256": sha256(args.patch),
        "optimizer_updates": 0,
        "training_tokens": 0,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    if not payload["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
