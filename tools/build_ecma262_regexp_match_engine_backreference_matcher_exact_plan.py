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


DETAIL_NAME = "ecma262-regexp-match-engine-backreference-matcher-exact-plan.tsv"
SUMMARY_NAME = "ecma262-regexp-match-engine-backreference-matcher-exact-plan.summary"
TARGET_TEST_ARTIFACT = (
    "test/test_ecma262_match_engine_backreference_matcher_exact_plan.ml"
)

OBSERVATIONS_BY_SUFFIX = {
    1: "backreference_matcher_operation",
    2: "backreference_matcher_closure",
    3: "backreference_match_state_parameter",
    4: "backreference_continuation_parameter",
    5: "backreference_input_read",
    6: "backreference_captures_read",
    7: "backreference_result_initialized_undefined",
    8: "backreference_ns_iteration",
    9: "backreference_defined_capture_branch",
    10: "backreference_single_defined_capture_assert",
    11: "backreference_selected_capture_range",
    12: "backreference_undefined_capture_continuation",
    13: "backreference_end_index_read",
    14: "backreference_capture_start_index_read",
    15: "backreference_capture_end_index_read",
    16: "backreference_capture_length_computed",
    17: "backreference_forward_index_computed",
    18: "backreference_backward_index_computed",
    19: "backreference_input_length_read",
    20: "backreference_bounds_failure",
    21: "backreference_compare_start_min",
    22: "backreference_canonicalize_compare",
    23: "backreference_result_state_created",
    24: "backreference_continuation_return",
}


def validate_source_row(row: dict[str, str]) -> None:
    requirement_id = row["requirement_id"]
    expected = {
        "clause_id": "22.2.2.7.2",
        "mapping_family": "match_engine_backreferences",
        "executable_layer": "match_engine",
        "product_surface": "match_engine",
        "ledger_state": "open_requirement_to_test_mapping_missing",
        "mapping_state": "open_exact_case_selection",
    }
    validate_expected_fields(
        row,
        expected,
        context="BackreferenceMatcher source row",
    )
    number = suffix_number(requirement_id)
    if number not in OBSERVATIONS_BY_SUFFIX:
        raise SystemExit(
            f"BackreferenceMatcher source row {requirement_id} has "
            f"unsupported suffix"
        )
    if not Path(row["source_file"]).is_file():
        raise SystemExit(
            f"BackreferenceMatcher source row {requirement_id} source is missing: "
            f"{row['source_file']}"
        )


def selected_source_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    expected_ids = {
        f"ecma262-22.2.2.7.2-{number:04d}" for number in OBSERVATIONS_BY_SUFFIX
    }
    return select_expected_source_rows(
        rows,
        include_row=lambda row: row["mapping_family"] == "match_engine_backreferences",
        expected_ids=expected_ids,
        validate_row=validate_source_row,
        duplicate_message=lambda requirement_id: (
            f"duplicate BackreferenceMatcher source row {requirement_id}"
        ),
        missing_prefix="BackreferenceMatcher source rows missing from worklist: ",
        extra_prefix="unexpected BackreferenceMatcher source rows in worklist: ",
    )


def validate_existing_plan_source_row(row: dict[str, str]) -> None:
    requirement_id = row["requirement_id"]
    expected = {
        "clause_id": "22.2.2.7.2",
        "mapping_family": "match_engine_backreferences",
        "executable_layer": "match_engine",
        "target_test_artifact": TARGET_TEST_ARTIFACT,
    }
    validate_expected_fields(
        row,
        expected,
        context="BackreferenceMatcher existing plan row",
    )
    number = suffix_number(requirement_id)
    if number not in OBSERVATIONS_BY_SUFFIX:
        raise SystemExit(
            f"BackreferenceMatcher existing plan row {requirement_id} has "
            f"unsupported suffix"
        )
    if not Path(row["source_file"]).is_file():
        raise SystemExit(
            f"BackreferenceMatcher existing plan row {requirement_id} source "
            f"is missing: {row['source_file']}"
        )


def selected_existing_plan_source_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    selected: dict[str, dict[str, str]] = {}
    for row in rows:
        if row["mapping_family"] != "match_engine_backreferences":
            continue
        requirement_id = row["requirement_id"]
        if requirement_id in selected:
            raise SystemExit(
                f"duplicate BackreferenceMatcher existing plan row {requirement_id}"
            )
        validate_existing_plan_source_row(row)
        selected[requirement_id] = row

    expected_ids = {
        f"ecma262-22.2.2.7.2-{number:04d}" for number in OBSERVATIONS_BY_SUFFIX
    }
    missing = sorted(expected_ids.difference(selected))
    extra = sorted(set(selected).difference(expected_ids))
    if missing:
        raise SystemExit(
            "BackreferenceMatcher existing plan rows missing: "
            + ", ".join(missing[:10])
        )
    if extra:
        raise SystemExit(
            "unexpected BackreferenceMatcher existing plan rows: "
            + ", ".join(extra[:10])
        )
    return [selected[requirement_id] for requirement_id in sorted(expected_ids)]


def behavior_case(number: int) -> dict[str, str]:
    if number == 12:
        return {
            "pattern": "(a|(b))\\2",
            "flags": "",
            "input_text": "a",
            "expected_search_result": "true",
            "case_route": "undefined_capture_continuation",
        }
    if number == 20:
        return {
            "pattern": "(aa)\\1",
            "flags": "",
            "input_text": "aa",
            "expected_search_result": "false",
            "case_route": "out_of_bounds_failure",
        }
    if number == 22:
        return {
            "pattern": "(a)\\1",
            "flags": "",
            "input_text": "ab",
            "expected_search_result": "false",
            "case_route": "canonicalized_character_mismatch",
        }
    if number == 18:
        return {
            "pattern": "\\1(a)",
            "flags": "",
            "input_text": "aa",
            "expected_search_result": "true",
            "case_route": "backward_direction_observer",
        }
    return {
        "pattern": "(a)\\1",
        "flags": "",
        "input_text": "aa",
        "expected_search_result": "true",
        "case_route": "defined_capture_forward_success",
    }


def plan_row(row: dict[str, str]) -> dict[str, str]:
    requirement_id = row["requirement_id"]
    number = suffix_number(requirement_id)
    observation = OBSERVATIONS_BY_SUFFIX[number]
    exact_case_id = (
        f"match-engine-backreference-matcher-exact:{requirement_id}:"
        f"{safe_id(observation)}"
    )
    return {
        "plan_id": f"match-engine-backreference-matcher-exact-plan:{requirement_id}",
        **copy_requirement_metadata(row, include_local_id=True),
        "mapping_family": "match_engine_backreferences",
        "executable_layer": "match_engine",
        "backreference_matcher_subfamily": "backreference_matcher_operation",
        "backreference_matcher_route": "capture_backreference_runtime_semantics",
        **behavior_case(number),
        "exact_case_family": observation,
        "exact_case_id": exact_case_id,
        "expected_observation": observation,
        "expected_observed": "true",
        "expected_behavior": "backreference_matcher_exact_plan_observable",
        "coverage_credit": "none_match_engine_backreference_matcher_exact_planned",
        "plan_state": "planned_not_executable",
        "target_test_artifact": TARGET_TEST_ARTIFACT,
        "exact_case_obligation": row["requirement_text"],
        "observability_status": "backreference_matcher_model_observable",
        "observability_reason": (
            "Ecma_regex_core exposes a test-only BackreferenceMatcher model "
            "observation while public Ecma_regex.search verifies the selected "
            "runtime path"
        ),
        "next_action": "materialize_match_engine_backreference_matcher_exact_case",
        "plan_reason": (
            "BackreferenceMatcher exact case maps the ECMA-262 22.2.2.7.2 "
            "operation row directly to executable matcher-model evidence; "
            "ledger credit is assigned only after exactness audit consumption"
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
    worklist_has_source_rows = any(
        row["mapping_family"] == "match_engine_backreferences"
        and row["clause_id"] == "22.2.2.7.2"
        for row in worklist_rows
    )
    if worklist_has_source_rows:
        source_rows = selected_source_rows(worklist_rows)
    elif detail.is_file():
        existing_fields, existing_rows = read_tsv(detail)
        require_columns(
            detail,
            existing_fields,
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
                "target_test_artifact",
            },
        )
        source_rows = selected_existing_plan_source_rows(existing_rows)
    else:
        source_rows = selected_source_rows(worklist_rows)
    rows = [plan_row(row) for row in source_rows]
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
        "backreference_matcher_subfamily",
        "backreference_matcher_route",
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
        f"match_engine_backreference_matcher_exact_plan_rows\t{len(rows)}\n",
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
