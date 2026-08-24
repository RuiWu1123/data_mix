#!/usr/bin/env python3
"""Check structural coverage requirements in ASSUMPTIONS.md."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path


ENTRY = re.compile(r"(?ms)^## (A-[0-9]{3})\b(.*?)(?=^## A-[0-9]{3}\b|\Z)")
FIELD = re.compile(r"(?m)^- ([A-Za-z ]+):\s*(.+)$")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs="?", type=Path, default=Path("ASSUMPTIONS.md"))
    parser.add_argument("--minimum-methods", type=int, default=5)
    parser.add_argument("--maximum-method-share", type=float, default=0.4)
    args = parser.parse_args()

    text = args.path.read_text(encoding="utf-8")
    errors: list[str] = []
    methods: Counter[str] = Counter()
    entries = ENTRY.findall(text)
    required = {
        "Method",
        "Statement",
        "Paper tested",
        "Paper location",
        "Code location",
        "Level",
        "Provenance",
    }

    for assumption_id, body in entries:
        fields = dict(FIELD.findall(body))
        missing = sorted(required - fields.keys())
        if missing:
            errors.append(f"{assumption_id}: missing {', '.join(missing)}")
            continue
        methods[fields["Method"]] += 1
        if fields["Level"] not in {"L0", "L1", "L2"}:
            errors.append(f"{assumption_id}: invalid level {fields['Level']}")
        if not re.search(r"(Section|Appendix|Equation|Table|Figure|§)", fields["Paper location"]):
            errors.append(f"{assumption_id}: paper location is not specific")
        if not re.search(r":\d+", fields["Code location"]):
            errors.append(f"{assumption_id}: code location lacks a line number")

    total = len(entries)
    if len(methods) < args.minimum_methods:
        errors.append(f"method coverage {len(methods)} < {args.minimum_methods}")
    maximum_share = max(methods.values(), default=0) / total if total else 0.0
    if maximum_share > args.maximum_method_share:
        errors.append(
            f"maximum method share {maximum_share:.6f} > {args.maximum_method_share:.6f}"
        )

    result = {
        "assumptions": total,
        "errors": errors,
        "maximum_method_share": maximum_share,
        "method_counts": dict(sorted(methods.items())),
        "methods": len(methods),
        "passed": not errors,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(1 if errors else 0)


if __name__ == "__main__":
    main()
