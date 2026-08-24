#!/usr/bin/env python3
"""Extract page-delimited PDF text for auditable literature review."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pdfplumber


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def extract(pdf_path: Path, output_dir: Path) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    pages: list[str] = []
    with pdfplumber.open(pdf_path) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            text = page.extract_text(x_tolerance=1, y_tolerance=3) or ""
            pages.append(f"[[PAGE {page_number}]]\n{text}")

    output_path = output_dir / f"{pdf_path.stem}.txt"
    output_path.write_text("\n\n".join(pages) + "\n", encoding="utf-8")
    return {
        "input": str(pdf_path),
        "output": str(output_path),
        "pages": len(pages),
        "sha256": sha256(pdf_path),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("pdfs", nargs="+", type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    records = [extract(path, args.output_dir) for path in args.pdfs]
    print(json.dumps(records, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
