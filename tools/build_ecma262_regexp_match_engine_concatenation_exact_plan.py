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


DETAIL_NAME = "ecma262-regexp-match-engine-concatenation-exact-plan.tsv"
SUMMARY_NAME = "ecma262-regexp-match-engine-concatenation-exact-plan.summary"
TARGET_TEST_ARTIFACT = "test/test_ecma262_match_engine_concatenation_exact_plan.ml"

OBSERVATIONS_BY_SUFFIX = {
    1: "match_sequence_operation",
    2: "match_sequence_forward_branch",
    3: "match_sequence_forward_closure",
    4: "match_sequence_forward_match_state_parameter",
    5: "match_sequence_forward_continuation_parameter",
    7: "match_sequence_forward_nested_match_state_parameter",
    10: "match_sequence_backward_branch",
    11: "match_sequence_backward_closure",
    12: "match_sequence_backward_match_state_parameter",
    13: "match_sequence_backward_continuation_parameter",
    14: "match_sequence_backward_nested_continuation",
    15: "match_sequence_backward_nested_match_state_parameter",
    16: "match_sequence_backward_first_matcher_return",
    17: "match_sequence_backward_second_matcher_return",
}


def validate_source_row(row: dict[str, str]) -> None:
    requirement_id = row["requirement_id"]
    expected = {
        "clause_id": "22.2.2.3.4",
        "mapping_family": "match_engine_concatenation",
        "executable_layer": "match_engine",
        "product_surface": "match_engine",
        "ledger_state": "open_requirement_to_test_mapping_missing",
        "mapping_state": "open_exact_case_selection",
    }
    validate_expected_fields(row, expected, context="MatchSequence source row")
    number = suffix_number(requirement_id)
    if number not in OBSERVATIONS_BY_SUFFIX:
        raise SystemExit(
            f"MatchSequence source row {requirement_id} has unsupported suffix"
        )
    if not Path(row["source_file"]).is_file():
        raise SystemExit(
            f"MatchSequence source row {requirement_id} source is missing: "
            f"{row['source_file']}"
        )


def selected_source_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    expected_ids = {
        f"ecma262-22.2.2.3.4-{number:04d}"
        for number in OBSERVATIONS_BY_SUFFIX
    }
    return select_expected_source_rows(
        rows,
        include_row=lambda row: row["mapping_family"] == "match_engine_concatenation",
        expected_ids=expected_ids,
        validate_row=validate_source_row,
        duplicate_message=lambda requirement_id: (
            f"duplicate MatchSequence source row {requirement_id}"
        ),
        missing_prefix="MatchSequence source rows missing from worklist: ",
        extra_prefix="unexpected MatchSequence source rows in worklist: ",
    )


def behavior_case(number: int) -> dict[str, str]:
    if number >= 10:
        return {
            "pattern": "(?<=ab)c",
            "flags": "",
            "input_text": "abc",
            "expected_search_result": "true",
            "case_route": "backward_lookbehind_sequence_success",
        }
    return {
        "pattern": "ab",
        "flags": "",
        "input_text": "ab",
        "expected_search_result": "true",
        "case_route": "forward_sequence_success",
    }


def plan_row(row: dict[str, str]) -> dict[str, str]:
    requirement_id = row["requirement_id"]
    number = suffix_number(requirement_id)
    observation = OBSERVATIONS_BY_SUFFIX[number]
    exact_case_id = (
        f"match-engine-concatenation-exact:{requirement_id}:"
        f"{safe_id(observation)}"
    )
    return {
        "plan_id": f"match-engine-concatenation-exact-plan:{requirement_id}",
        **copy_requirement_metadata(row, include_local_id=True),
        "mapping_family": "match_engine_concatenation",
        "executable_layer": "match_engine",
        "match_sequence_subfamily": "match_sequence_operation",
        "match_sequence_route": "matcher_continuation_runtime_semantics",
        **behavior_case(number),
        "exact_case_family": observation,
        "exact_case_id": exact_case_id,
        "expected_observation": observation,
        "expected_observed": "true",
        "expected_behavior": "match_sequence_exact_plan_observable",
        "coverage_credit": "none_match_engine_concatenation_exact_planned",
        "plan_state": "planned_not_executable",
        "target_test_artifact": TARGET_TEST_ARTIFACT,
        "exact_case_obligation": row["requirement_text"],
        "observability_status": "match_sequence_model_observable",
        "observability_reason": (
            "Ecma_regex_core exposes a test-only MatchSequence model "
            "observation while public Ecma_regex.search verifies the selected "
            "runtime path"
        ),
        "next_action": "materialize_match_engine_concatenation_exact_case",
        "plan_reason": (
            "MatchSequence exact case maps the ECMA-262 22.2.2.3.4 operation "
            "row directly to executable matcher-continuation evidence; ledger "
            "credit is assigned only after exactness audit consumption"
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache", default="cache")
    parser.add_argument(
        "--worklist",
        default="cache/ecma262-regexp-requirement-test-worklist.tsv",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    cache = Path(args.cache)
    worklist = Path(args.worklist)
    detail = cache / DETAIL_NAME
    summary = cache / SUMMARY_NAME

    if not worklist.is_file():
        raise SystemExit(
            f"missing requirement-test worklist at {worklist}; run "
            "tools/map_ecma262_requirements_to_tests.py first"
        )

    fields, worklist_rows = read_tsv(worklist)
    require_columns(
        worklist,
        fields,
        {
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
            "product_surface",
            "ledger_state",
            "mapping_state",
        },
    )
    rows = [plan_row(row) for row in selected_source_rows(worklist_rows)]
    validate_unique_ids(rows)

    fieldnames = [
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
        "match_sequence_subfamily",
        "match_sequence_route",
        "case_route",
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
    search_counts = Counter(row["expected_search_result"] for row in rows)
    observation_counts = Counter(row["expected_observation"] for row in rows)
    route_counts = Counter(row["case_route"] for row in rows)
    summary_lines = [
        "ecma262_snapshot\t2026\n",
        f"input_worklist\t{worklist}\n",
        f"match_engine_concatenation_exact_plan_rows\t{len(rows)}\n",
        f"planned_executable_rows\t{state_counts.get('planned_not_executable', 0)}\n",
        f"target_test_artifact\t{TARGET_TEST_ARTIFACT}\n",
        f"planned_detail_output\t{detail}\n",
        f"planned_summary_output\t{summary}\n",
        f"dry_run\t{bool_text(args.dry_run)}\n",
    ]
    for name, count in sorted(state_counts.items()):
        summary_lines.append(f"plan_state_{name}\t{count}\n")
    for name, count in sorted(search_counts.items()):
        summary_lines.append(f"expected_search_result_{name}\t{count}\n")
    for name, count in sorted(route_counts.items()):
        summary_lines.append(f"case_route_{name}\t{count}\n")
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
