#!/usr/bin/env python3
"""Prove that ONEDIAL-V2 changes only the approved Q1 interior generator."""

from __future__ import annotations

import argparse
import copy
import difflib
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any


EXPECTED_JSON_DIFF_PATHS = {
    "/protocol_id",
    "/questions/Q1/truth/interior_weight_generator",
}
Q1_MARKDOWN_SECTION = "Q1 - Synthetic calibration with true zeros"


def canonical_hash(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    return hashlib.sha256(encoded).hexdigest()


def text_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def git_text(root: Path, ref: str, relative_path: str) -> str:
    return subprocess.run(
        ["git", "show", f"{ref}:{relative_path}"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout


def difference_paths(old: Any, new: Any, path: str = "") -> set[str]:
    if isinstance(old, dict) and isinstance(new, dict):
        differences: set[str] = set()
        for key in sorted(old.keys() | new.keys()):
            child = f"{path}/{key}"
            if key not in old or key not in new:
                differences.add(child)
            else:
                differences |= difference_paths(old[key], new[key], child)
        return differences
    if isinstance(old, list) and isinstance(new, list):
        if old == new:
            return set()
        differences = set()
        for index in range(max(len(old), len(new))):
            child = f"{path}/{index}"
            if index >= len(old) or index >= len(new):
                differences.add(child)
            else:
                differences |= difference_paths(old[index], new[index], child)
        return differences
    return set() if old == new else {path}


def markdown_sections(text: str) -> tuple[str, dict[str, str]]:
    preamble: list[str] = []
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for line in text.splitlines(keepends=True):
        if line.startswith("## "):
            current = line[3:].strip()
            sections[current] = [line]
        elif current is None:
            preamble.append(line)
        else:
            sections[current].append(line)
    return "".join(preamble), {name: "".join(lines) for name, lines in sections.items()}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--base-ref", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--diff-output", type=Path, required=True)
    args = parser.parse_args()

    old_json_text = git_text(args.root, args.base_ref, "protocol_onedial.json")
    old_markdown = git_text(args.root, args.base_ref, "PROTOCOL_ONEDIAL.md")
    new_json_text = (args.root / "protocol_onedial.json").read_text(encoding="utf-8")
    new_markdown = (args.root / "PROTOCOL_ONEDIAL.md").read_text(encoding="utf-8")
    old = json.loads(old_json_text)
    new = json.loads(new_json_text)
    errors: list[str] = []

    json_differences = difference_paths(old, new)
    if json_differences != EXPECTED_JSON_DIFF_PATHS:
        errors.append(f"unexpected JSON diff paths: {sorted(json_differences)}")
    if old.get("protocol_id") != "ONEDIAL-V1" or new.get("protocol_id") != "ONEDIAL-V2":
        errors.append("protocol identity transition is not ONEDIAL-V1 to ONEDIAL-V2")

    generator = new.get("questions", {}).get("Q1", {}).get("truth", {}).get(
        "interior_weight_generator", {}
    )
    expected_generator = {
        "distribution": "symmetric_dirichlet",
        "alpha": 1.0,
        "alpha_vector": "ones(m)",
        "domain_count": "m from the corresponding Olmix swarm",
        "row_count": "finite weight-row count n_m from the corresponding unmodified Olmix ratios table",
        "draw_scope": "fresh independent n_m-by-m matrix for each phase, m, interior scenario, and zero-based synthetic replicate; never used by structural-zero scenarios",
        "rng": "numpy.random.Generator(numpy.random.PCG64(seed)).dirichlet(ones(m), size=n_m)",
        "seed_rule": "little-endian uint64 from the first 8 bytes of SHA256('ONEDIAL-V2:Q1-interior-weights:' + phase_seed_namespace + ':m=' + decimal(m) + ':scenario=' + scenario + ':replicate=' + decimal(zero_based_replicate_index))",
    }
    if generator != expected_generator:
        errors.append("Q1 interior generator does not equal the approved frozen definition")
    old_structural = old["questions"]["Q1"]["truth"].get("structural_zero_generator")
    new_structural = new["questions"]["Q1"]["truth"].get("structural_zero_generator")
    if old_structural != new_structural:
        errors.append("Q1 structural-zero generator changed")

    json_hashes: dict[str, dict[str, Any]] = {}
    top_level_sections = (
        "stage",
        "claim",
        "scope",
        "compute",
        "randomness",
        "common_estimator",
        "inputs",
        "execution_order",
        "overall_verdict",
        "mutation_policy",
        "commands",
    )
    for name in top_level_sections:
        old_hash = canonical_hash(old[name])
        new_hash = canonical_hash(new[name])
        json_hashes[f"top_level/{name}"] = {
            "v1": old_hash,
            "v2": new_hash,
            "unchanged": old_hash == new_hash,
        }
    for identifier in ("Q2", "Q3", "Q4", "Q5"):
        old_hash = canonical_hash(old["questions"][identifier])
        new_hash = canonical_hash(new["questions"][identifier])
        json_hashes[f"questions/{identifier}"] = {
            "v1": old_hash,
            "v2": new_hash,
            "unchanged": old_hash == new_hash,
        }
    q1_without_amendment = copy.deepcopy(new["questions"]["Q1"])
    q1_without_amendment["truth"].pop("interior_weight_generator", None)
    old_hash = canonical_hash(old["questions"]["Q1"])
    new_hash = canonical_hash(q1_without_amendment)
    json_hashes["questions/Q1_without_interior_generator"] = {
        "v1": old_hash,
        "v2": new_hash,
        "unchanged": old_hash == new_hash,
    }
    if not all(item["unchanged"] for item in json_hashes.values()):
        errors.append("at least one protected JSON section changed")

    old_preamble, old_sections = markdown_sections(old_markdown)
    new_preamble, new_sections = markdown_sections(new_markdown)
    if set(old_sections) != set(new_sections):
        errors.append("Markdown section set changed")
    protected_markdown_hashes: dict[str, dict[str, Any]] = {}
    for name in sorted(set(old_sections) & set(new_sections)):
        if name == Q1_MARKDOWN_SECTION:
            continue
        old_hash = text_hash(old_sections[name])
        new_hash = text_hash(new_sections[name])
        protected_markdown_hashes[name] = {
            "v1": old_hash,
            "v2": new_hash,
            "unchanged": old_hash == new_hash,
        }
    if not all(item["unchanged"] for item in protected_markdown_hashes.values()):
        errors.append("at least one protected Markdown section changed")
    if "ONEDIAL-V1" not in old_preamble or "ONEDIAL-V2" not in new_preamble:
        errors.append("Markdown preamble does not record the V1 to V2 transition")

    diff_lines = [
        *difflib.unified_diff(
            old_json_text.splitlines(keepends=True),
            new_json_text.splitlines(keepends=True),
            fromfile="ONEDIAL-V1/protocol_onedial.json",
            tofile="ONEDIAL-V2/protocol_onedial.json",
        ),
        "\n",
        *difflib.unified_diff(
            old_markdown.splitlines(keepends=True),
            new_markdown.splitlines(keepends=True),
            fromfile="ONEDIAL-V1/PROTOCOL_ONEDIAL.md",
            tofile="ONEDIAL-V2/PROTOCOL_ONEDIAL.md",
        ),
    ]
    diff_text = "".join(diff_lines)
    added_lines = sum(line.startswith("+") and not line.startswith("+++") for line in diff_lines)
    removed_lines = sum(line.startswith("-") and not line.startswith("---") for line in diff_lines)

    payload = {
        "id": "ONEDIAL-V2-AMENDMENT-CHECK",
        "passed": not errors,
        "errors": errors,
        "base_ref": args.base_ref,
        "json_difference_paths": sorted(json_differences),
        "expected_json_difference_paths": sorted(EXPECTED_JSON_DIFF_PATHS),
        "protected_json_section_count": len(json_hashes),
        "protected_json_sections_all_unchanged": all(
            item["unchanged"] for item in json_hashes.values()
        ),
        "protected_json_section_hashes": json_hashes,
        "protected_markdown_section_count": len(protected_markdown_hashes),
        "protected_markdown_sections_all_unchanged": all(
            item["unchanged"] for item in protected_markdown_hashes.values()
        ),
        "protected_markdown_section_hashes": protected_markdown_hashes,
        "q1_structural_zero_generator_unchanged": old_structural == new_structural,
        "diff_added_line_count": added_lines,
        "diff_removed_line_count": removed_lines,
        "diff_sha256": text_hash(diff_text),
        "v1_protocol_sha256": text_hash(old_json_text),
        "v2_protocol_sha256": text_hash(new_json_text),
        "v1_markdown_sha256": text_hash(old_markdown),
        "v2_markdown_sha256": text_hash(new_markdown),
        "inputs": [
            f"git:{args.base_ref}:protocol_onedial.json",
            f"git:{args.base_ref}:PROTOCOL_ONEDIAL.md",
            str(args.root / "protocol_onedial.json"),
            str(args.root / "PROTOCOL_ONEDIAL.md"),
        ],
        "command": (
            "python scripts/check_onedial_v2_amendment.py "
            f"--root {args.root} --base-ref {args.base_ref} --output {args.output} "
            f"--diff-output {args.diff_output}"
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.diff_output.parent.mkdir(parents=True, exist_ok=True)
    args.diff_output.write_text(diff_text, encoding="utf-8")
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
