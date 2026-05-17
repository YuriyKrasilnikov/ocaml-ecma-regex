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
    select_worklist_rows,
    suffix_number,
    validate_unique_ids,
)


DETAIL_NAME = "ecma262-regexp-exec-result-capture-exact-plan.tsv"
SUMMARY_NAME = "ecma262-regexp-exec-result-capture-exact-plan.summary"
TARGET_TEST_ARTIFACT = "test/test_ecma262_exec_result_capture_exact_plan.ml"

CAPTURE_REQUIREMENT_SUFFIXES = {33, 34, 35, 55, 56, 57, 59, 60, 61, 65, 66, 67, 68}
EXPECTED_CAPTURE_ROWS = 13

DEFINED_CAPTURE_CASE = {
    "case_family": "defined_capture_result_model",
    "pattern": "(a)(b)",
    "flags": "",
    "input_text": "ab",
    "expected_capture_count": "2",
    "expected_capture_ordinal": "1",
    "expected_capture_defined": "true",
    "expected_capture_start_index": "0",
    "expected_capture_end_index": "1",
    "expected_capture_text": "a",
}

UNDEFINED_CAPTURE_CASE = {
    "case_family": "undefined_capture_result_model",
    "pattern": "(a)|(b)",
    "flags": "",
    "input_text": "b",
    "expected_capture_count": "2",
    "expected_capture_ordinal": "1",
    "expected_capture_defined": "false",
    "expected_capture_start_index": "",
    "expected_capture_end_index": "",
    "expected_capture_text": "",
}

CASE_BY_SUFFIX = {
    33: {
        **DEFINED_CAPTURE_CASE,
        "expected_behavior": "exec_result_capture_count_observable",
        "expected_model_field": "capture_slot_count",
    },
    34: {
        **DEFINED_CAPTURE_CASE,
        "expected_behavior": "exec_result_capture_count_matches_regexp_record",
        "expected_model_field": "capture_count_matches_regexp_record",
    },
    35: {
        **DEFINED_CAPTURE_CASE,
        "expected_behavior": "exec_result_capture_count_within_array_limit",
        "expected_model_field": "capture_count_within_array_limit",
    },
    55: {
        **DEFINED_CAPTURE_CASE,
        "expected_behavior": "exec_result_reads_capture_slot",
        "expected_model_field": "capture_slot_read",
    },
    56: {
        **UNDEFINED_CAPTURE_CASE,
        "expected_behavior": "exec_result_detects_undefined_capture",
        "expected_model_field": "undefined_capture_observed",
    },
    57: {
        **UNDEFINED_CAPTURE_CASE,
        "expected_behavior": "exec_result_returns_undefined_capture_value",
        "expected_model_field": "undefined_capture_value",
    },
    59: {
        **DEFINED_CAPTURE_CASE,
        "expected_behavior": "exec_result_takes_defined_capture_branch",
        "expected_model_field": "defined_capture_observed",
    },
    60: {
        **DEFINED_CAPTURE_CASE,
        "expected_behavior": "exec_result_exposes_capture_start",
        "expected_model_field": "capture_start_index_observed",
    },
    61: {
        **DEFINED_CAPTURE_CASE,
        "expected_behavior": "exec_result_exposes_capture_end",
        "expected_model_field": "capture_end_index_observed",
    },
    65: {
        **DEFINED_CAPTURE_CASE,
        "expected_behavior": "exec_result_builds_capture_match_record",
        "expected_model_field": "capture_record_observed",
    },
    66: {
        **DEFINED_CAPTURE_CASE,
        "expected_behavior": "exec_result_extracts_captured_value",
        "expected_model_field": "captured_value_observed",
    },
    67: {
        **DEFINED_CAPTURE_CASE,
        "expected_behavior": "exec_result_appends_capture_index_record",
        "expected_model_field": "capture_index_list_append_observed",
    },
    68: {
        **DEFINED_CAPTURE_CASE,
        "expected_behavior": "exec_result_writes_capture_result_property",
        "expected_model_field": "result_capture_property_observed",
    },
}


def selected_worklist_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return select_worklist_rows(
        rows,
        include_row=lambda row: row["mapping_family"] == "exec_result_matching"
        and row["executable_layer"] == "exec_result"
        and row["ledger_state"] == "open_requirement_to_test_mapping_missing"
        and suffix_number(row["requirement_id"]) in CAPTURE_REQUIREMENT_SUFFIXES,
        sort_key=lambda row: suffix_number(row["requirement_id"]),
        expected_count=EXPECTED_CAPTURE_ROWS,
        count_message=lambda selected_count: (
            f"expected {EXPECTED_CAPTURE_ROWS} exec-result capture rows, "
            f"selected {selected_count}"
        ),
    )


def plan_row(row: dict[str, str]) -> dict[str, str]:
    requirement_id = row["requirement_id"]
    suffix = suffix_number(requirement_id)
    case = CASE_BY_SUFFIX[suffix]
    exact_case_id = (
        f"exec-result-capture-exact:{requirement_id}:"
        f"{safe_id(case['expected_behavior'])}"
    )
    return {
        "plan_id": f"exec-result-capture-exact-plan:{requirement_id}",
        **copy_requirement_metadata(row, include_local_id=True),
        "mapping_family": "exec_result_matching",
        "executable_layer": "exec_result",
        "result_subfamily": "builtin_exec_captures",
        "result_semantic_route": "capture_result_model",
        "exact_case_family": case["case_family"],
        "exact_case_id": exact_case_id,
        "pattern": case["pattern"],
        "flags": case["flags"],
        "input_text": case["input_text"],
        "expected_exec_result": "true",
        "expected_capture_count": case["expected_capture_count"],
        "expected_capture_ordinal": case["expected_capture_ordinal"],
        "expected_capture_defined": case["expected_capture_defined"],
        "expected_capture_start_index": case["expected_capture_start_index"],
        "expected_capture_end_index": case["expected_capture_end_index"],
        "expected_capture_text": case["expected_capture_text"],
        "expected_behavior": case["expected_behavior"],
        "expected_model_field": case["expected_model_field"],
        "coverage_credit": "none_exec_result_capture_exact_planned",
        "plan_state": "planned_not_executable",
        "target_test_artifact": TARGET_TEST_ARTIFACT,
        "exact_case_obligation": row["requirement_text"],
        "observability_status": "internal_exec_result_capture_model_observable",
        "observability_reason": (
            "internal exec-result capture observer exposes capture slot count, "
            "undefined/defined capture state, capture ranges, captured text, "
            "and capture result construction without changing public API"
        ),
        "next_action": "materialize_exec_result_capture_exact_case",
        "plan_reason": (
            "RegExpBuiltinExec capture-result row is classified as exact only "
            "after the executable internal capture-result model gate proves the "
            "requirement-specific result construction behavior"
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
            f"missing ECMA-262 requirement-test worklist at {worklist}; "
            "run tools/map_ecma262_requirements_to_tests.py first"
        )

    worklist_fields, worklist_rows = read_tsv(worklist)
    require_columns(
        worklist,
        worklist_fields,
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
            "ledger_state",
        },
    )
    source_rows = selected_worklist_rows(worklist_rows)
    rows = [plan_row(row) for row in source_rows]
    validate_unique_ids(rows)

    state_counts = Counter(row["plan_state"] for row in rows)
    credit_counts = Counter(row["coverage_credit"] for row in rows)
    behavior_counts = Counter(row["expected_behavior"] for row in rows)
    field_counts = Counter(row["expected_model_field"] for row in rows)
    defined_counts = Counter(row["expected_capture_defined"] for row in rows)
    family_counts = Counter(row["exact_case_family"] for row in rows)
    observability_counts = Counter(row["observability_status"] for row in rows)
    target_counts = Counter(row["target_test_artifact"] for row in rows)

    planned_executable_rows = state_counts.get("planned_not_executable", 0)
    coverage_credit_rows = sum(
        count for credit, count in credit_counts.items() if not credit.startswith("none")
    )

    summary_lines = [
        "ecma262_snapshot\t2026\n",
        f"input_worklist\t{worklist}\n",
        f"input_worklist_rows\t{len(worklist_rows)}\n",
        f"source_requirement_rows\t{len(source_rows)}\n",
        f"exec_result_capture_exact_plan_rows\t{len(rows)}\n",
        f"planned_executable_rows\t{planned_executable_rows}\n",
        f"coverage_credit_rows\t{coverage_credit_rows}\n",
        f"planned_detail_output\t{detail}\n",
        f"planned_summary_output\t{summary}\n",
        f"dry_run\t{bool_text(args.dry_run)}\n",
    ]
    for name, count in sorted(state_counts.items()):
        summary_lines.append(f"plan_state_{name}\t{count}\n")
    for name, count in sorted(credit_counts.items()):
        summary_lines.append(f"coverage_credit_{name}\t{count}\n")
    for name, count in sorted(behavior_counts.items()):
        summary_lines.append(f"expected_behavior_{name}\t{count}\n")
    for name, count in sorted(field_counts.items()):
        summary_lines.append(f"expected_model_field_{name}\t{count}\n")
    for name, count in sorted(defined_counts.items()):
        summary_lines.append(f"expected_capture_defined_{name}\t{count}\n")
    for name, count in sorted(family_counts.items()):
        summary_lines.append(f"exact_case_family_{name}\t{count}\n")
    for name, count in sorted(observability_counts.items()):
        summary_lines.append(f"observability_status_{name}\t{count}\n")
    for name, count in sorted(target_counts.items()):
        if name:
            summary_lines.append(f"target_test_artifact_{name}\t{count}\n")

    if args.dry_run:
        print("".join(summary_lines), end="")
        return

    cache.mkdir(parents=True, exist_ok=True)
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
        "result_subfamily",
        "result_semantic_route",
        "exact_case_family",
        "exact_case_id",
        "pattern",
        "flags",
        "input_text",
        "expected_exec_result",
        "expected_capture_count",
        "expected_capture_ordinal",
        "expected_capture_defined",
        "expected_capture_start_index",
        "expected_capture_end_index",
        "expected_capture_text",
        "expected_behavior",
        "expected_model_field",
        "coverage_credit",
        "plan_state",
        "target_test_artifact",
        "exact_case_obligation",
        "observability_status",
        "observability_reason",
        "next_action",
        "plan_reason",
    ]
    with detail.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, delimiter="\t", fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    with summary.open("w", encoding="utf-8") as f:
        f.write("".join(summary_lines))
    print(summary.read_text(encoding="utf-8"), end="")


if __name__ == "__main__":
    main()
