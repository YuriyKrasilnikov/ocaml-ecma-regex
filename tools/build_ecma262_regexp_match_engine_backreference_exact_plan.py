#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path

from ecma262_tooling import (
    bool_text,
    copy_requirement_metadata,
    read_tsv,
    require_columns,
    safe_id,
    select_expected_source_rows,
    suffix_number,
    validate_expected_fields,
    validate_unique_ids,
)


DETAIL_NAME = "ecma262-regexp-match-engine-backreference-exact-plan.tsv"
SUMMARY_NAME = "ecma262-regexp-match-engine-backreference-exact-plan.summary"
TARGET_TEST_ARTIFACT = "test/test_ecma262_match_engine_backreference_exact_plan.ml"

OBSERVATIONS_BY_SUFFIX = {
    66: "decimal_backreference_atom",
    67: "decimal_capturing_group_number",
    68: "decimal_group_count_assert",
    69: "decimal_backreference_matcher_return",
    94: "named_backreference_atom",
    95: "named_matching_group_specifiers",
    96: "named_paren_indices_list",
    97: "named_group_specifier_iteration",
    98: "named_count_left_capturing_parens",
    99: "named_paren_index_append",
    100: "named_backreference_matcher_return",
}


def expected_source(row: dict[str, str]) -> dict[str, str]:
    number = suffix_number(row["requirement_id"])
    if 66 <= number <= 69:
        return {
            "atom_subfamily": "decimal_backreference_atom_escape",
            "atom_semantic_route": "capture_backreference_runtime_model",
            "expected_behavior": "requires_capture_backreference_model",
            "plan_state": "deferred_requires_capture_backreference_model",
            "observability_status": "requires_capture_backreference_model",
        }
    if 94 <= number <= 100:
        return {
            "atom_subfamily": "named_backreference_atom_escape",
            "atom_semantic_route": "named_capture_backreference_runtime_model",
            "expected_behavior": "requires_named_backreference_model",
            "plan_state": "deferred_requires_named_backreference_model",
            "observability_status": "requires_named_backreference_model",
        }
    raise SystemExit(
        f"backreference exact source row {row['requirement_id']} has unsupported suffix"
    )


def validate_source_row(row: dict[str, str]) -> None:
    requirement_id = row["requirement_id"]
    expected = {
        "mapping_family": "match_engine_atoms",
        "executable_layer": "match_engine",
        "coverage_credit": "none_match_engine_atoms_exact_deferred",
        **expected_source(row),
    }
    validate_expected_fields(
        row,
        expected,
        context="backreference exact source row",
    )
    if suffix_number(requirement_id) not in OBSERVATIONS_BY_SUFFIX:
        raise SystemExit(
            f"backreference exact source row {requirement_id} has unsupported suffix"
        )
    if not Path(row["source_file"]).is_file():
        raise SystemExit(
            f"backreference exact source row {requirement_id} source is missing: "
            f"{row['source_file']}"
        )


def selected_source_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    expected_ids = {
        f"ecma262-22.2.2.7-{number:04d}" for number in OBSERVATIONS_BY_SUFFIX
    }
    return select_expected_source_rows(
        rows,
        include_row=lambda row: row["plan_state"]
        in {
            "deferred_requires_capture_backreference_model",
            "deferred_requires_named_backreference_model",
        },
        expected_ids=expected_ids,
        validate_row=validate_source_row,
        duplicate_message=lambda requirement_id: (
            f"duplicate backreference source row for {requirement_id}"
        ),
        missing_prefix="backreference exact source rows missing from atom plan: ",
        extra_prefix=(
            "backreference exact source rows outside expected CompileAtom range: "
        ),
    )


def plan_case(row: dict[str, str]) -> dict[str, str]:
    number = suffix_number(row["requirement_id"])
    if 66 <= number <= 69:
        return {
            "backreference_subfamily": "decimal_backreference_atom_escape",
            "backreference_semantic_route": "capture_backreference_runtime_model",
            "pattern": "(a)\\1",
            "flags": "u",
            "input_text": "aa",
            "expected_search_result": "true",
        }
    return {
        "backreference_subfamily": "named_backreference_atom_escape",
        "backreference_semantic_route": "named_capture_backreference_runtime_model",
        "pattern": "(?<x>a)\\k<x>",
        "flags": "",
        "input_text": "aa",
        "expected_search_result": "true",
    }


def plan_row(row: dict[str, str]) -> dict[str, str]:
    requirement_id = row["requirement_id"]
    observation = OBSERVATIONS_BY_SUFFIX[suffix_number(requirement_id)]
    exact_case_id = (
        f"match-engine-backreference-exact:{requirement_id}:"
        f"{safe_id(observation)}"
    )
    return {
        "plan_id": f"match-engine-backreference-exact-plan:{requirement_id}",
        "source_atom_plan_id": row["plan_id"],
        **copy_requirement_metadata(row, include_local_id=True),
        "mapping_family": "match_engine_atoms",
        "executable_layer": "match_engine",
        **plan_case(row),
        "exact_case_family": observation,
        "exact_case_id": exact_case_id,
        "expected_observation": observation,
        "expected_observed": "true",
        "expected_behavior": "backreference_model_observable",
        "coverage_credit": "none_match_engine_backreference_exact_planned",
        "plan_state": "planned_not_executable",
        "target_test_artifact": TARGET_TEST_ARTIFACT,
        "exact_case_obligation": row["requirement_text"],
        "observability_status": "backreference_model_observable",
        "observability_reason": (
            "Ecma_regex_core exposes a test-only backreference matcher model "
            "observation while public Ecma_regex.search verifies runtime behavior"
        ),
        "next_action": "materialize_match_engine_backreference_exact_case",
        "plan_reason": (
            "backreference exact case upgrades a previously deferred "
            "CompileAtom backreference row into executable internal "
            "matcher-model evidence; ledger credit is assigned only after the "
            "exactness audit consumes this plan"
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache", default="cache")
    parser.add_argument(
        "--atoms-plan",
        default="cache/ecma262-regexp-match-engine-atoms-exact-plan.tsv",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    cache = Path(args.cache)
    atoms_plan = Path(args.atoms_plan)
    detail = cache / DETAIL_NAME
    summary = cache / SUMMARY_NAME

    if not atoms_plan.is_file():
        raise SystemExit(
            f"missing match-engine atoms exact plan at {atoms_plan}; "
            "run tools/build_ecma262_regexp_match_engine_atoms_exact_plan.py first"
        )

    atoms_fields, atoms_rows = read_tsv(atoms_plan)
    require_columns(
        atoms_plan,
        atoms_fields,
        {
            "plan_id",
            "requirement_id",
            "clause_id",
            "clause_title",
            "source_file",
            "section_anchor",
            "requirement_kind",
            "requirement_local_id",
            "requirement_text",
            "mapping_family",
            "executable_layer",
            "atom_subfamily",
            "atom_semantic_route",
            "expected_behavior",
            "coverage_credit",
            "plan_state",
            "observability_status",
        },
    )
    rows = [plan_row(row) for row in selected_source_rows(atoms_rows)]
    validate_unique_ids(rows)

    fieldnames = [
        "plan_id",
        "source_atom_plan_id",
        "requirement_id",
        "clause_id",
        "clause_title",
        "source_file",
        "section_anchor",
        "requirement_kind",
        "requirement_local_id",
        "requirement_text",
        "mapping_family",
        "executable_layer",
        "backreference_subfamily",
        "backreference_semantic_route",
        "exact_case_family",
        "exact_case_id",
        "pattern",
        "flags",
        "input_text",
        "expected_search_result",
        "expected_observation",
        "expected_observed",
        "expected_behavior",
        "coverage_credit",
        "plan_state",
        "target_test_artifact",
        "exact_case_obligation",
        "observability_status",
        "observability_reason",
        "next_action",
        "plan_reason",
    ]

    state_counts = Counter(row["plan_state"] for row in rows)
    observation_counts = Counter(row["expected_observation"] for row in rows)
    subfamily_counts = Counter(row["backreference_subfamily"] for row in rows)
    route_counts = Counter(row["backreference_semantic_route"] for row in rows)
    search_counts = Counter(row["expected_search_result"] for row in rows)
    summary_lines = [
        "ecma262_snapshot\t2026\n",
        f"input_atoms_plan\t{atoms_plan}\n",
        f"match_engine_backreference_exact_plan_rows\t{len(rows)}\n",
        f"planned_executable_rows\t{state_counts.get('planned_not_executable', 0)}\n",
        f"backreference_subfamily_decimal_backreference_atom_escape\t{subfamily_counts.get('decimal_backreference_atom_escape', 0)}\n",
        f"backreference_subfamily_named_backreference_atom_escape\t{subfamily_counts.get('named_backreference_atom_escape', 0)}\n",
        f"backreference_route_capture_backreference_runtime_model\t{route_counts.get('capture_backreference_runtime_model', 0)}\n",
        f"backreference_route_named_capture_backreference_runtime_model\t{route_counts.get('named_capture_backreference_runtime_model', 0)}\n",
        f"target_test_artifact\t{TARGET_TEST_ARTIFACT}\n",
        f"planned_detail_output\t{detail}\n",
        f"planned_summary_output\t{summary}\n",
        f"dry_run\t{bool_text(args.dry_run)}\n",
    ]
    for name, count in sorted(state_counts.items()):
        summary_lines.append(f"plan_state_{name}\t{count}\n")
    for name, count in sorted(search_counts.items()):
        summary_lines.append(f"expected_search_result_{name}\t{count}\n")
    for name, count in sorted(observation_counts.items()):
        summary_lines.append(f"expected_observation_{name}\t{count}\n")

    if args.dry_run:
        print("".join(summary_lines), end="")
        return

    cache.mkdir(parents=True, exist_ok=True)
    with detail.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)
    summary.write_text("".join(summary_lines), encoding="utf-8")


if __name__ == "__main__":
    main()
