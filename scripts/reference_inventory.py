#!/usr/bin/env python3
"""Inventory reviewed PDFs and pinned vendor repositories."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

import pdfplumber


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git(path: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(path), *args], text=True
    ).strip()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--references", type=Path, default=Path("references"))
    parser.add_argument("--vendor", type=Path, default=Path("vendor"))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    papers = []
    for path in sorted(args.references.glob("*.pdf")):
        with pdfplumber.open(path) as pdf:
            papers.append(
                {
                    "path": str(path),
                    "pages": len(pdf.pages),
                    "sha256": sha256(path),
                }
            )

    repositories = []
    for path in sorted(item for item in args.vendor.iterdir() if item.is_dir()):
        repositories.append(
            {
                "path": str(path),
                "remote": git(path, "remote", "get-url", "origin"),
                "commit": git(path, "rev-parse", "HEAD"),
            }
        )

    payload = {"papers": papers, "repositories": repositories}
    rendered = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")


if __name__ == "__main__":
    main()
