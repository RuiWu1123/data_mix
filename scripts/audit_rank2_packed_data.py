#!/usr/bin/env python3
"""Audit RegMix packed data produced for TWODIAL-E2E-V1."""

from __future__ import annotations

import argparse
import json
import struct
from pathlib import Path


HEADER_MAGIC = b"LITPKDS"
HEADER_SIZE = 24


def read_header(path: Path) -> dict[str, int | str]:
    with path.open("rb") as stream:
        magic = stream.read(len(HEADER_MAGIC))
        version = struct.unpack("<Q", stream.read(8))[0]
        dtype_code = struct.unpack("<B", stream.read(1))[0]
        chunk_size = struct.unpack("<Q", stream.read(8))[0]
    if magic != HEADER_MAGIC or version != 1:
        raise ValueError(f"invalid packed header: {path}")
    return {
        "path": str(path),
        "version": version,
        "dtype_code": dtype_code,
        "chunk_tokens": chunk_size,
        "bytes": path.stat().st_size,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--arms", type=Path, required=True)
    parser.add_argument("--packed", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    arms = json.loads(args.arms.read_text(encoding="utf-8"))
    train_prefixes = arms["domains"]
    valid_prefixes = [f"valid_the_pile_{task}" for task in arms["tasks"]]
    inventory: dict[str, dict[str, object]] = {}
    errors: list[str] = []
    for split, prefixes, expected_chunk in (
        ("train", train_prefixes, 2049 * 256),
        ("valid", valid_prefixes, 131136),
    ):
        for prefix in prefixes:
            paths = sorted(args.packed.glob(f"{prefix}-*"))
            if not paths:
                errors.append(f"missing {prefix}")
                continue
            headers = [read_header(path) for path in paths]
            if any(header["chunk_tokens"] != expected_chunk for header in headers):
                errors.append(f"wrong chunk size {prefix}")
            if any(header["dtype_code"] != 8 for header in headers):
                errors.append(f"wrong dtype {prefix}")
            inventory[prefix] = {
                "split": split,
                "files": len(paths),
                "bytes": sum(int(header["bytes"]) for header in headers),
                "tokens": sum(int(header["chunk_tokens"]) for header in headers),
                "first_header": headers[0],
            }
    payload = {
        "id": "TWODIAL-E2E-V1-PACKED-DATA",
        "passed": not errors,
        "errors": errors,
        "required_train_prefixes": len(train_prefixes),
        "required_valid_prefixes": len(valid_prefixes),
        "present_prefixes": len(inventory),
        "total_files": sum(int(item["files"]) for item in inventory.values()),
        "total_bytes": sum(int(item["bytes"]) for item in inventory.values()),
        "total_tokens": sum(int(item["tokens"]) for item in inventory.values()),
        "inventory": inventory,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
