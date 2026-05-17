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
    suffix_number,
    validate_unique_ids,
)


DETAIL_NAME = "ecma262-regexp-exec-result-matching-exact-plan.tsv"
SUMMARY_NAME = "ecma262-regexp-exec-result-matching-exact-plan.summary"
TARGET_TEST_ARTIFACT = "test/test_ecma262_exec_result_matching_exact_plan.ml"

EXPECTED_SOURCE_ROWS = 92


PUBLIC_EXEC_FIELDS = {
    "ecma262-22.2.7.2-0014": (
        "search_loop_observed",
        "public_exec_search_loop",
        "search_loop_repeats_until_match",
        "b",
        "",
        "ab",
        "1",
        "2",
        "b",
    ),
    "ecma262-22.2.7.2-0020": (
        "matcher_invoked_at_input_index_observed",
        "public_exec_match_result",
        "matcher_called_at_input_index",
        "a",
        "",
        "a",
        "0",
        "1",
        "a",
    ),
    "ecma262-22.2.7.2-0021": (
        "matcher_failure_observed",
        "public_exec_search_loop",
        "failure_branch_before_later_match",
        "b",
        "",
        "ab",
        "1",
        "2",
        "b",
    ),
    "ecma262-22.2.7.2-0025": (
        "advance_string_index_observed",
        "public_exec_ascii_advance",
        "advance_string_index_ascii_after_failure",
        "b",
        "",
        "ab",
        "1",
        "2",
        "b",
    ),
    "ecma262-22.2.7.2-0026": (
        "success_branch_observed",
        "public_exec_match_result",
        "success_branch_returns_result",
        "a",
        "",
        "a",
        "0",
        "1",
        "a",
    ),
    "ecma262-22.2.7.2-0029": (
        "end_index_read_observed",
        "public_exec_result_span",
        "end_index_result_observable",
        "bc",
        "",
        "abc",
        "1",
        "3",
        "bc",
    ),
    "ecma262-22.2.7.2-0040": (
        "match_record_created_observed",
        "public_exec_result_span",
        "match_record_span_observable",
        "bc",
        "",
        "abc",
        "1",
        "3",
        "bc",
    ),
    "ecma262-22.2.7.2-0044": (
        "matched_substring_observed",
        "public_exec_match_text",
        "get_match_string_observable",
        "bc",
        "",
        "abc",
        "1",
        "3",
        "bc",
    ),
}


REGEXP_EXEC_FIELDS = {
    1: "regexp_exec_operation_observed",
    2: "regexp_exec_get_exec_property_observed",
    3: "regexp_exec_callable_exec_branch_observed",
    4: "regexp_exec_custom_exec_call_observed",
    5: "regexp_exec_custom_result_type_guard_observed",
    6: "regexp_exec_custom_result_return_observed",
    7: "regexp_exec_builtin_slot_required_observed",
    8: "regexp_exec_delegates_to_builtin_exec_observed",
}


BUILTIN_EXEC_FIELDS = {
    1: "builtin_exec_operation_observed",
    2: "input_length_observed",
    3: "last_index_read_observed",
    4: "original_flags_read_observed",
    5: "global_flag_computed_observed",
    6: "sticky_flag_computed_observed",
    7: "has_indices_flag_computed_observed",
    8: "non_global_non_sticky_last_index_reset_observed",
    9: "matcher_read_observed",
    10: "full_unicode_flag_computed_observed",
    11: "match_succeeded_initialized_false_observed",
    12: "input_list_created_observed",
    13: "input_character_note_observed",
    15: "last_index_greater_than_length_branch_observed",
    16: "global_or_sticky_oob_reset_branch_observed",
    17: "last_index_reset_to_zero_observed",
    18: "return_null_on_oob_observed",
    19: "input_index_from_last_index_observed",
    22: "sticky_failure_branch_observed",
    23: "sticky_failure_reset_last_index_observed",
    24: "sticky_failure_return_null_observed",
    27: "match_state_assertion_observed",
    28: "match_succeeded_set_true_observed",
    30: "full_unicode_end_index_conversion_observed",
    31: "global_or_sticky_success_branch_observed",
    32: "last_index_updated_to_end_observed",
    36: "result_array_created_observed",
    37: "result_array_length_observed",
    38: "result_index_property_observed",
    39: "result_input_property_observed",
    45: "result_zero_property_observed",
    46: "named_groups_branch_observed",
    47: "groups_object_created_observed",
    48: "has_groups_true_observed",
    49: "no_groups_branch_observed",
    50: "groups_undefined_observed",
    51: "has_groups_false_observed",
    52: "groups_property_observed",
    53: "matched_group_names_list_created_observed",
    54: "capture_iteration_observed",
    62: "full_unicode_capture_conversion_branch_observed",
    63: "capture_start_get_string_index_observed",
    64: "capture_end_get_string_index_observed",
    69: "named_capture_branch_observed",
    70: "capturing_group_name_read_observed",
    71: "matched_group_names_duplicate_check_observed",
    72: "duplicate_group_assert_undefined_observed",
    73: "duplicate_group_undefined_appended_observed",
    74: "named_capture_else_branch_observed",
    75: "matched_group_name_appended_observed",
    76: "duplicate_group_note_observed",
    77: "named_group_property_created_observed",
    78: "group_name_appended_observed",
    79: "unnamed_capture_branch_observed",
    80: "undefined_group_name_appended_observed",
    84: "return_array_observed",
}


ALREADY_COVERED_EXACT_KINDS = {
    "exec_result_capture_exact_case",
    "exec_result_indices_exact_case",
}


def selected_ledger_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    selected = [
        row
        for row in rows
        if row["semantic_family"] == "matching"
        and row["product_surface"] == "exec_result"
        and row["clause_id"] in {"22.2.7.1", "22.2.7.2"}
    ]
    selected.sort(key=lambda row: (row["clause_id"], suffix_number(row["requirement_id"])))
    if len(selected) != EXPECTED_SOURCE_ROWS:
        raise SystemExit(
            f"expected {EXPECTED_SOURCE_ROWS} exec-result matching rows, "
            f"selected {len(selected)}"
        )
    return selected


def result_subfamily_and_route(row: dict[str, str]) -> tuple[str, str]:
    clause_id = row["clause_id"]
    number = suffix_number(row["requirement_id"])
    if clause_id == "22.2.7.1":
        return ("regexp_exec_object_dispatch", "regexp_exec_object_model")
    if number in {3, 4, 5, 6, 7, 8, 15, 16, 17, 22, 23, 31, 32}:
        return ("builtin_exec_last_index_and_flags", "last_index_state_model")
    if number in {10, 12, 13, 19, 30, 62, 63, 64}:
        return ("builtin_exec_full_unicode_indices", "unicode_index_model")
    if number in {1, 36, 37, 38, 39, 45, 52, 84}:
        return ("builtin_exec_result_array_object", "array_result_object_model")
    if number in {33, 34, 35, 55, 56, 57, 59, 60, 61, 65, 66, 67, 68}:
        return ("builtin_exec_captures", "capture_result_model")
    if 46 <= number <= 51 or 53 <= number <= 54 or 69 <= number <= 80:
        return ("builtin_exec_groups", "groups_result_model")
    if number in {41, 42, 43, 58, 81, 82, 83}:
        return ("builtin_exec_indices", "indices_result_model")
    if row["requirement_id"] in PUBLIC_EXEC_FIELDS:
        return ("builtin_exec_public_result", "public_exec_result")
    return ("builtin_exec_internal_state", "builtin_exec_state_model")


def model_scenario(row: dict[str, str]) -> str:
    clause_id = row["clause_id"]
    number = suffix_number(row["requirement_id"])
    if clause_id == "22.2.7.1":
        return "regexp_exec_object_dispatch"
    if number in {15, 16, 17, 18}:
        return "last_index_out_of_bounds_global"
    if number in {22, 23, 24}:
        return "sticky_failure"
    if number in {30, 62, 63, 64}:
        return "unicode_success"
    if number in {31, 32}:
        return "global_success"
    if number in {71, 72, 73, 76}:
        return "duplicate_named_groups"
    if number in {46, 47, 48, 52, 53, 54, 69, 70, 74, 75, 77, 78}:
        return "named_groups"
    if number in {49, 50, 51, 79, 80}:
        return "no_groups"
    return "default_match"


def pattern_case(row: dict[str, str]) -> tuple[str, str, str, str, str, str]:
    requirement_id = row["requirement_id"]
    if requirement_id in PUBLIC_EXEC_FIELDS:
        _, _, _, pattern, flags, input_text, start, end, text = PUBLIC_EXEC_FIELDS[
            requirement_id
        ]
        return (pattern, flags, input_text, "true", start, end, text)
    scenario = model_scenario(row)
    if scenario == "regexp_exec_object_dispatch":
        return ("a", "", "a", "not_applicable", "", "", "")
    if scenario == "last_index_out_of_bounds_global":
        return ("z", "g", "a", "false", "", "", "")
    if scenario == "sticky_failure":
        return ("z", "y", "a", "false", "", "", "")
    if scenario == "unicode_success":
        return ("(?<x>a)", "u", "a", "true", "0", "1", "a")
    if scenario in {"named_groups", "duplicate_named_groups"}:
        return ("(?<x>a)", "", "a", "true", "0", "1", "a")
    if scenario == "no_groups":
        return ("(a)", "", "a", "true", "0", "1", "a")
    if scenario == "global_success":
        return ("a", "g", "a", "true", "0", "1", "a")
    return ("a", "", "a", "true", "0", "1", "a")


def expected_model_field(row: dict[str, str]) -> str:
    requirement_id = row["requirement_id"]
    if requirement_id in PUBLIC_EXEC_FIELDS:
        return PUBLIC_EXEC_FIELDS[requirement_id][0]
    number = suffix_number(requirement_id)
    if row["clause_id"] == "22.2.7.1":
        return REGEXP_EXEC_FIELDS[number]
    return BUILTIN_EXEC_FIELDS[number]


def is_current_or_prior_matching_credit(row: dict[str, str]) -> bool:
    return (
        row["ledger_state"] == "open_requirement_to_test_mapping_missing"
        or row["exactness_evidence_kind"] == "exec_result_matching_exact_case"
    )


def planned_case(row: dict[str, str]) -> dict[str, str]:
    subfamily, route = result_subfamily_and_route(row)
    pattern, flags, input_text, expected_exec, start, end, text = pattern_case(row)
    model_field = expected_model_field(row)
    return {
        "result_subfamily": subfamily,
        "result_semantic_route": route,
        "exact_case_family": safe_id(model_field.removesuffix("_observed")),
        "pattern": pattern,
        "flags": flags,
        "input_text": input_text,
        "expected_exec_result": expected_exec,
        "expected_start_index": start,
        "expected_end_index": end,
        "expected_match_text": text,
        "expected_behavior": model_field,
        "expected_model_field": model_field,
        "model_scenario": model_scenario(row),
        "coverage_credit": "none_exec_result_matching_exact_planned",
        "plan_state": "planned_not_executable",
        "target_test_artifact": TARGET_TEST_ARTIFACT,
        "exact_case_obligation": row["requirement_text"],
        "observability_status": "internal_exec_result_matching_model_observable",
        "observability_reason": (
            "internal RegExpExec/RegExpBuiltinExec model exposes this "
            "requirement row without expanding the public OCaml API"
        ),
        "next_action": "materialize_exec_result_matching_exact_case",
    }


def deferred_case(row: dict[str, str]) -> dict[str, str]:
    subfamily, route = result_subfamily_and_route(row)
    evidence_kind = row["exactness_evidence_kind"]
    if evidence_kind in ALREADY_COVERED_EXACT_KINDS:
        status = f"already_covered_by_{evidence_kind}"
    else:
        status = "requires_more_specific_exec_result_model"
    return {
        "result_subfamily": subfamily,
        "result_semantic_route": route,
        "exact_case_family": status,
        "pattern": "",
        "flags": "",
        "input_text": "",
        "expected_exec_result": "not_observable",
        "expected_start_index": "",
        "expected_end_index": "",
        "expected_match_text": "",
        "expected_behavior": status,
        "expected_model_field": "",
        "model_scenario": "",
        "coverage_credit": "none_exec_result_matching_exact_deferred",
        "plan_state": f"deferred_{status}",
        "target_test_artifact": "",
        "exact_case_obligation": row["requirement_text"],
        "observability_status": status,
        "observability_reason": row["requirement_text"],
        "next_action": f"design_{status}_before_credit",
    }


def plan_row(row: dict[str, str]) -> dict[str, str]:
    requirement_id = row["requirement_id"]
    case = planned_case(row) if is_current_or_prior_matching_credit(row) else deferred_case(row)
    exact_case_id = (
        f"exec-result-matching-exact:{requirement_id}:"
        f"{safe_id(case['exact_case_family'])}"
    )
    return {
        "plan_id": f"exec-result-matching-exact-plan:{requirement_id}",
        **copy_requirement_metadata(row, include_local_id=True),
        "mapping_family": "exec_result_matching",
        "executable_layer": "exec_result",
        "exact_case_id": exact_case_id,
        **case,
        "plan_reason": (
            "RegExpExec/RegExpBuiltinExec matching row is classified against "
            "the full ledger so previously credited public rows are preserved, "
            "current open rows receive executable model cases, and rows already "
            "covered by more specific capture/indices evidence are not double credited"
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache", default="cache")
    parser.add_argument(
        "--ledger",
        default="cache/ecma262-regexp-coverage-ledger.tsv",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    cache = Path(args.cache)
    ledger = Path(args.ledger)
    detail = cache / DETAIL_NAME
    summary = cache / SUMMARY_NAME

    if not ledger.is_file():
        raise SystemExit(
            f"missing ECMA-262 coverage ledger at {ledger}; "
            "run tools/build_ecma262_regexp_coverage_ledger.py first"
        )

    ledger_fields, ledger_rows = read_tsv(ledger)
    require_columns(
        ledger,
        ledger_fields,
        {
            "requirement_id",
            "clause_id",
            "clause_title",
            "source_file",
            "section_anchor",
            "requirement_kind",
            "requirement_local_id",
            "requirement_text",
            "semantic_family",
            "product_surface",
            "ledger_state",
            "exactness_evidence_kind",
        },
    )
    source_rows = selected_ledger_rows(ledger_rows)
    rows = [plan_row(row) for row in source_rows]
    validate_unique_ids(rows)

    state_counts = Counter(row["plan_state"] for row in rows)
    credit_counts = Counter(row["coverage_credit"] for row in rows)
    behavior_counts = Counter(row["expected_behavior"] for row in rows)
    exec_counts = Counter(row["expected_exec_result"] for row in rows)
    subfamily_counts = Counter(row["result_subfamily"] for row in rows)
    route_counts = Counter(row["result_semantic_route"] for row in rows)
    scenario_counts = Counter(row["model_scenario"] for row in rows)
    observability_counts = Counter(row["observability_status"] for row in rows)
    target_counts = Counter(row["target_test_artifact"] for row in rows)

    planned_executable_rows = state_counts.get("planned_not_executable", 0)
    deferred_rows = len(rows) - planned_executable_rows
    coverage_credit_rows = sum(
        count for credit, count in credit_counts.items() if not credit.startswith("none")
    )

    summary_lines = [
        "ecma262_snapshot\t2026\n",
        f"input_ledger\t{ledger}\n",
        f"input_ledger_rows\t{len(ledger_rows)}\n",
        f"source_requirement_rows\t{len(source_rows)}\n",
        f"exec_result_matching_exact_plan_rows\t{len(rows)}\n",
        f"planned_executable_rows\t{planned_executable_rows}\n",
        f"deferred_rows\t{deferred_rows}\n",
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
    for name, count in sorted(exec_counts.items()):
        summary_lines.append(f"expected_exec_result_{name}\t{count}\n")
    for name, count in sorted(subfamily_counts.items()):
        summary_lines.append(f"result_subfamily_{name}\t{count}\n")
    for name, count in sorted(route_counts.items()):
        summary_lines.append(f"result_semantic_route_{name}\t{count}\n")
    for name, count in sorted(scenario_counts.items()):
        if name:
            summary_lines.append(f"model_scenario_{name}\t{count}\n")
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
        "expected_start_index",
        "expected_end_index",
        "expected_match_text",
        "expected_behavior",
        "expected_model_field",
        "model_scenario",
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
