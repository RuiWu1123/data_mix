#!/usr/bin/env python3
"""Prove that ONEDIAL-V3 contains only the authorized V2 amendments."""

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
    "/randomness/permutation_replicates",
    "/common_estimator/significant_residual_dimension",
    "/act1_static_feasibility_audit",
}
ALLOWED_MARKDOWN_CHANGES = {"Claim and estimand", "Frozen common pipeline"}
NEW_MARKDOWN_SECTION = "Permanent Act I feasibility obligation"
VERBATIM_RATIONALE = '覆盖注册判定空间的完备集：维度 1-3 的支持判定与"超过 3"的证伪判定各自只依赖这 4 个指标'


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
    if old.get("protocol_id") != "ONEDIAL-V2" or new.get("protocol_id") != "ONEDIAL-V3":
        errors.append("protocol identity transition is not ONEDIAL-V2 to ONEDIAL-V3")
    if new.get("randomness", {}).get("permutation_replicates") != 4999:
        errors.append("permutation replicate count is not 4999")
    detector = new.get("common_estimator", {}).get("significant_residual_dimension", "")
    for required in ("first 4", "1+4999", "0.0002", "0.0025", "12.5", VERBATIM_RATIONALE):
        if required not in detector:
            errors.append(f"detector is missing required text: {required}")

    expected_obligation = {
        "required_before_freeze": True,
        "constraint_pair_categories": [
            "p_reachability",
            "rank_or_count_reachability",
            "quantile_resolution",
        ],
        "enumeration_rule": "enumerate every minimum-attainable-p versus corrected or registered p threshold, every available-row or count versus required rank or minimum count, and every sample or resample count versus registered quantile-tail resolution",
        "failure_policy": "any failed or unenumerated reachability pair blocks protocol freeze and Act II authorization",
        "script": "scripts/check_onedial_feasibility.py",
        "artifact": "artifacts/onedial_v3_feasibility_check.json",
        "command": "sbatch slurm/check_onedial_feasibility.sbatch",
    }
    if new.get("act1_static_feasibility_audit") != expected_obligation:
        errors.append("permanent Act I feasibility obligation differs from the frozen definition")

    protected_hashes: dict[str, dict[str, Any]] = {}
    for name in (
        "stage",
        "claim",
        "scope",
        "compute",
        "inputs",
        "execution_order",
        "overall_verdict",
        "mutation_policy",
        "commands",
    ):
        old_hash = canonical_hash(old[name])
        new_hash = canonical_hash(new[name])
        protected_hashes[f"top_level/{name}"] = {
            "v2": old_hash,
            "v3": new_hash,
            "unchanged": old_hash == new_hash,
        }
    for identifier in ("Q1", "Q2", "Q3", "Q4", "Q5"):
        old_hash = canonical_hash(old["questions"][identifier])
        new_hash = canonical_hash(new["questions"][identifier])
        protected_hashes[f"questions/{identifier}"] = {
            "v2": old_hash,
            "v3": new_hash,
            "unchanged": old_hash == new_hash,
        }
    old_randomness = copy.deepcopy(old["randomness"])
    new_randomness = copy.deepcopy(new["randomness"])
    old_randomness.pop("permutation_replicates")
    new_randomness.pop("permutation_replicates")
    old_hash = canonical_hash(old_randomness)
    new_hash = canonical_hash(new_randomness)
    protected_hashes["randomness/without_permutation_replicates"] = {
        "v2": old_hash,
        "v3": new_hash,
        "unchanged": old_hash == new_hash,
    }
    old_estimator = copy.deepcopy(old["common_estimator"])
    new_estimator = copy.deepcopy(new["common_estimator"])
    old_estimator.pop("significant_residual_dimension")
    new_estimator.pop("significant_residual_dimension")
    old_hash = canonical_hash(old_estimator)
    new_hash = canonical_hash(new_estimator)
    protected_hashes["common_estimator/without_dimension_detector"] = {
        "v2": old_hash,
        "v3": new_hash,
        "unchanged": old_hash == new_hash,
    }
    if not all(item["unchanged"] for item in protected_hashes.values()):
        errors.append("at least one protected JSON section changed")

    old_preamble, old_sections = markdown_sections(old_markdown)
    new_preamble, new_sections = markdown_sections(new_markdown)
    if set(new_sections) - set(old_sections) != {NEW_MARKDOWN_SECTION}:
        errors.append("unexpected added Markdown sections")
    if set(old_sections) - set(new_sections):
        errors.append("a V2 Markdown section was removed")
    markdown_hashes: dict[str, dict[str, Any]] = {}
    for name in sorted(set(old_sections) & set(new_sections)):
        if name in ALLOWED_MARKDOWN_CHANGES:
            continue
        old_hash = text_hash(old_sections[name])
        new_hash = text_hash(new_sections[name])
        markdown_hashes[name] = {
            "v2": old_hash,
            "v3": new_hash,
            "unchanged": old_hash == new_hash,
        }
    if not all(item["unchanged"] for item in markdown_hashes.values()):
        errors.append("at least one protected Markdown section changed")
    if "ONEDIAL-V2" not in old_preamble or "ONEDIAL-V3" not in new_preamble:
        errors.append("Markdown preamble does not record the V2 to V3 transition")
    if VERBATIM_RATIONALE not in new_sections.get("Frozen common pipeline", ""):
        errors.append("verbatim Holm-family rationale is absent from Markdown")

    diff_lines = [
        *difflib.unified_diff(
            old_json_text.splitlines(keepends=True),
            new_json_text.splitlines(keepends=True),
            fromfile="ONEDIAL-V2/protocol_onedial.json",
            tofile="ONEDIAL-V3/protocol_onedial.json",
        ),
        "\n",
        *difflib.unified_diff(
            old_markdown.splitlines(keepends=True),
            new_markdown.splitlines(keepends=True),
            fromfile="ONEDIAL-V2/PROTOCOL_ONEDIAL.md",
            tofile="ONEDIAL-V3/PROTOCOL_ONEDIAL.md",
        ),
    ]
    diff_text = "".join(diff_lines)
    added_lines = sum(line.startswith("+") and not line.startswith("+++") for line in diff_lines)
    removed_lines = sum(line.startswith("-") and not line.startswith("---") for line in diff_lines)
    payload = {
        "id": "ONEDIAL-V3-AMENDMENT-CHECK",
        "passed": not errors,
        "errors": errors,
        "base_ref": args.base_ref,
        "json_difference_paths": sorted(json_differences),
        "expected_json_difference_paths": sorted(EXPECTED_JSON_DIFF_PATHS),
        "protected_json_section_count": len(protected_hashes),
        "protected_json_sections_all_unchanged": all(
            item["unchanged"] for item in protected_hashes.values()
        ),
        "protected_json_section_hashes": protected_hashes,
        "protected_markdown_section_count": len(markdown_hashes),
        "protected_markdown_sections_all_unchanged": all(
            item["unchanged"] for item in markdown_hashes.values()
        ),
        "protected_markdown_section_hashes": markdown_hashes,
        "diff_added_line_count": added_lines,
        "diff_removed_line_count": removed_lines,
        "diff_sha256": text_hash(diff_text),
        "v2_protocol_sha256": text_hash(old_json_text),
        "v3_protocol_sha256": text_hash(new_json_text),
        "v2_markdown_sha256": text_hash(old_markdown),
        "v3_markdown_sha256": text_hash(new_markdown),
        "inputs": [
            f"git:{args.base_ref}:protocol_onedial.json",
            f"git:{args.base_ref}:PROTOCOL_ONEDIAL.md",
            str(args.root / "protocol_onedial.json"),
            str(args.root / "PROTOCOL_ONEDIAL.md"),
        ],
        "command": (
            "python scripts/check_onedial_v3_amendment.py "
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
