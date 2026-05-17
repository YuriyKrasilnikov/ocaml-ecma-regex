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
    require_coverage_area,
    safe_id,
    select_requirement_rows,
    suffix_number,
    validate_expected_fields,
    validate_unique_ids,
)


DETAIL_NAME = "ecma262-regexp-match-engine-atoms-exact-plan.tsv"
SUMMARY_NAME = "ecma262-regexp-match-engine-atoms-exact-plan.summary"
TARGET_TEST_ARTIFACT = "test/test_ecma262_match_engine_atoms_exact_plan.ml"

ALREADY_CREDITED_ATOM_REQUIREMENTS = {
    "ecma262-22.2.2.7-0003",
    "ecma262-22.2.2.7-0004",
    "ecma262-22.2.2.7-0005",
    "ecma262-22.2.2.7-0006",
}


def executable_case(
    *,
    subfamily: str,
    route: str,
    pattern: str,
    flags: str,
    input_text: str,
    expected: bool,
    expected_behavior: str,
    obligation: str,
) -> dict[str, str]:
    return {
        "atom_subfamily": subfamily,
        "atom_semantic_route": route,
        "pattern": pattern,
        "flags": flags,
        "input_text": input_text,
        "expected_search_result": bool_text(expected),
        "expected_behavior": expected_behavior,
        "coverage_credit": "none_match_engine_atoms_exact_planned",
        "plan_state": "planned_not_executable",
        "target_test_artifact": TARGET_TEST_ARTIFACT,
        "exact_case_obligation": obligation,
        "observability_status": "search_bool_observable",
        "observability_reason": (
            "public Ecma_regex.search exposes enough boolean behavior for this "
            "CompileAtom atom route"
        ),
        "next_action": "materialize_match_engine_atoms_exact_case",
    }


def operation_model_case(
    *,
    subfamily: str,
    pattern: str,
    input_text: str,
    expected_behavior: str,
    obligation: str,
) -> dict[str, str]:
    return {
        "atom_subfamily": subfamily,
        "atom_semantic_route": "operation_model",
        "pattern": pattern,
        "flags": "",
        "input_text": input_text,
        "expected_search_result": "model_observable",
        "expected_behavior": expected_behavior,
        "coverage_credit": "none_match_engine_atoms_exact_planned",
        "plan_state": "planned_not_executable",
        "target_test_artifact": TARGET_TEST_ARTIFACT,
        "exact_case_obligation": obligation,
        "observability_status": "compile_atom_operation_model_observable",
        "observability_reason": (
            "Ecma_regex_core exposes a test-only CompileAtom operation model "
            "observation without adding public Ecma_regex API surface"
        ),
        "next_action": "materialize_match_engine_atoms_exact_case",
    }


def deferred_case(
    *,
    subfamily: str,
    route: str,
    status: str,
    obligation: str,
) -> dict[str, str]:
    return {
        "atom_subfamily": subfamily,
        "atom_semantic_route": route,
        "pattern": "",
        "flags": "",
        "input_text": "",
        "expected_search_result": "not_observable",
        "expected_behavior": status,
        "coverage_credit": "none_match_engine_atoms_exact_deferred",
        "plan_state": f"deferred_{status}",
        "target_test_artifact": "",
        "exact_case_obligation": obligation,
        "observability_status": status,
        "observability_reason": obligation,
        "next_action": f"design_{status}_before_credit",
    }


def classify_requirement(row: dict[str, str]) -> dict[str, str]:
    requirement_id = row["requirement_id"]
    number = suffix_number(requirement_id)
    text = row["requirement_text"]

    if number == 1:
        return operation_model_case(
            subfamily="compile_atom_operation_shape",
            pattern="a",
            input_text="a",
            expected_behavior="compile_atom_operation_shape_observed",
            obligation=text,
        )
    if number == 2:
        return operation_model_case(
            subfamily="compile_atom_piecewise_dispatch",
            pattern=".",
            input_text="a",
            expected_behavior="compile_atom_piecewise_dispatch_observed",
            obligation=text,
        )
    if 7 <= number <= 11:
        dot_cases = {
            7: (".", "", "A", True, "dot_atom_grammar_matches_character"),
            8: (".", "s", "\\n", True, "dot_all_includes_line_terminator"),
            9: (".", "", "A", True, "dot_without_dot_all_uses_filtered_set"),
            10: (".", "", "\\n", False, "dot_without_dot_all_excludes_line_terminator"),
            11: (".", "", "Z", True, "dot_returns_character_set_matcher"),
        }
        pattern, flags, input_text, expected, behavior = dot_cases[number]
        return executable_case(
            subfamily="dot_atom",
            route="dot_character_set_matcher",
            pattern=pattern,
            flags=flags,
            input_text=input_text,
            expected=expected,
            expected_behavior=behavior,
            obligation=text,
        )
    if 12 <= number <= 15:
        class_cases = {
            12: ("[a]", "", "a", True, "character_class_atom_matches_member"),
            13: ("[a]", "", "a", True, "compile_character_class_result_used"),
            14: ("[a]", "", "b", False, "character_class_charset_rejects_non_member"),
            15: ("[^a]", "", "b", True, "character_class_invert_singletons_matcher"),
        }
        pattern, flags, input_text, expected, behavior = class_cases[number]
        return executable_case(
            subfamily="character_class_single_code_point",
            route="character_class_character_set_matcher",
            pattern=pattern,
            flags=flags,
            input_text=input_text,
            expected=expected,
            expected_behavior=behavior,
            obligation=text,
        )
    if 16 <= number <= 32:
        return deferred_case(
            subfamily="character_class_unicode_sets_string_elements",
            route="unicode_sets_string_element_matcher_model",
            status="requires_unicode_sets_string_element_model",
            obligation=text,
        )
    if 33 <= number <= 55:
        return deferred_case(
            subfamily="capturing_group_atom",
            route="capture_range_match_state_model",
            status="requires_capture_model",
            obligation=text,
        )
    if 56 <= number <= 65:
        return deferred_case(
            subfamily="modifiers_group_atom",
            route="scoped_modifier_runtime_model",
            status="requires_modifier_runtime_model",
            obligation=text,
        )
    if 66 <= number <= 69:
        return deferred_case(
            subfamily="decimal_backreference_atom_escape",
            route="capture_backreference_runtime_model",
            status="requires_capture_backreference_model",
            obligation=text,
        )
    if 70 <= number <= 74:
        escape_cases = {
            70: ("\\x41", "", "A", True, "character_escape_atom_matches_character"),
            71: ("\\x41", "", "A", True, "character_escape_value_is_used"),
            72: ("\\n", "", "\\n", True, "character_escape_value_becomes_character"),
            73: ("\\t", "", "\\t", True, "character_escape_builds_singleton_charset"),
            74: ("\\x41", "", "B", False, "character_escape_returns_character_set_matcher"),
        }
        pattern, flags, input_text, expected, behavior = escape_cases[number]
        return executable_case(
            subfamily="character_escape_atom_escape",
            route="character_escape_character_set_matcher",
            pattern=pattern,
            flags=flags,
            input_text=input_text,
            expected=expected,
            expected_behavior=behavior,
            obligation=text,
        )
    if 75 <= number <= 77:
        class_escape_cases = {
            75: ("\\d", "", "5", True, "character_class_escape_atom_matches_member"),
            76: ("\\D", "", "5", False, "compile_to_charset_result_used"),
            77: ("\\w", "", "_", True, "character_class_escape_singletons_matcher"),
        }
        pattern, flags, input_text, expected, behavior = class_escape_cases[number]
        return executable_case(
            subfamily="character_class_escape_single_code_point",
            route="character_class_escape_character_set_matcher",
            pattern=pattern,
            flags=flags,
            input_text=input_text,
            expected=expected,
            expected_behavior=behavior,
            obligation=text,
        )
    if 78 <= number <= 93:
        return deferred_case(
            subfamily="character_class_escape_unicode_sets_string_elements",
            route="unicode_sets_string_element_matcher_model",
            status="requires_unicode_sets_string_element_model",
            obligation=text,
        )
    if 94 <= number <= 100:
        return deferred_case(
            subfamily="named_backreference_atom_escape",
            route="named_capture_backreference_runtime_model",
            status="requires_named_backreference_model",
            obligation=text,
        )
    raise SystemExit(f"unclassified CompileAtom requirement row: {requirement_id}")


def include_requirement_row(row: dict[str, str]) -> bool:
    return (
        row["clause_id"] == "22.2.2.7"
        and row["semantic_family"] == "atoms"
        and row["product_surface"] == "match_engine"
        and row["requirement_id"] not in ALREADY_CREDITED_ATOM_REQUIREMENTS
    )


def selected_requirement_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return select_requirement_rows(
        rows,
        include_row=include_requirement_row,
        sort_key=lambda row: suffix_number(row["requirement_id"]),
        expected_count=96,
        count_message=lambda count: (
            f"expected 96 remaining CompileAtom rows, selected {count}"
        ),
    )


def validate_requirement_row(row: dict[str, str]) -> None:
    expected = {
        "route_status": "needs_requirement_to_test_case_mapping",
    }
    validate_expected_fields(row, expected, context="match-engine atom row")
    require_coverage_area(
        row,
        "regexp_exec_and_captures",
        context="match-engine atom row",
    )


def plan_row(row: dict[str, str]) -> dict[str, str]:
    validate_requirement_row(row)
    requirement_id = row["requirement_id"]
    case = classify_requirement(row)
    exact_case_id = (
        f"match-engine-atoms-exact:{requirement_id}:"
        f"{safe_id(case['atom_subfamily'])}"
    )
    return {
        "plan_id": f"match-engine-atoms-exact-plan:{requirement_id}",
        **copy_requirement_metadata(row, include_local_id=True),
        "mapping_family": "match_engine_atoms",
        "executable_layer": "match_engine",
        "exact_case_id": exact_case_id,
        **case,
        "plan_reason": (
            "remaining CompileAtom row is classified before runtime credit; "
            "executable rows must pass the atom exact gate before exactness "
            "audit or coverage ledger may consume them"
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache", default="cache")
    parser.add_argument(
        "--requirements",
        default="cache/ecma262-regexp-requirement-mapping.tsv",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    cache = Path(args.cache)
    requirements = Path(args.requirements)
    detail = cache / DETAIL_NAME
    summary = cache / SUMMARY_NAME

    if not requirements.is_file():
        raise SystemExit(
            f"missing ECMA-262 requirement mapping at {requirements}; "
            "run tools/build_ecma262_regexp_requirement_mapping.py first"
        )

    requirement_fields, requirement_rows = read_tsv(requirements)
    require_columns(
        requirements,
        requirement_fields,
        {
            "requirement_id",
            "clause_id",
            "clause_title",
            "source_file",
            "section_anchor",
            "requirement_kind",
            "requirement_local_id",
            "requirement_text",
            "coverage_areas",
            "semantic_family",
            "product_surface",
            "route_status",
        },
    )

    source_rows = selected_requirement_rows(requirement_rows)
    rows = [plan_row(row) for row in source_rows]
    validate_unique_ids(rows)

    state_counts = Counter(row["plan_state"] for row in rows)
    credit_counts = Counter(row["coverage_credit"] for row in rows)
    behavior_counts = Counter(row["expected_behavior"] for row in rows)
    search_counts = Counter(row["expected_search_result"] for row in rows)
    subfamily_counts = Counter(row["atom_subfamily"] for row in rows)
    route_counts = Counter(row["atom_semantic_route"] for row in rows)
    observability_counts = Counter(row["observability_status"] for row in rows)
    target_counts = Counter(row["target_test_artifact"] for row in rows)

    coverage_credit_rows = sum(
        count for credit, count in credit_counts.items() if not credit.startswith("none")
    )
    planned_executable_rows = state_counts.get("planned_not_executable", 0)
    deferred_rows = len(rows) - planned_executable_rows

    summary_lines = [
        "ecma262_snapshot\t2026\n",
        f"input_requirements\t{requirements}\n",
        f"input_requirement_rows\t{len(requirement_rows)}\n",
        f"source_requirement_rows\t{len(source_rows)}\n",
        f"already_credited_atom_rows\t{len(ALREADY_CREDITED_ATOM_REQUIREMENTS)}\n",
        f"match_engine_atoms_exact_plan_rows\t{len(rows)}\n",
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
    for name, count in sorted(search_counts.items()):
        summary_lines.append(f"expected_search_result_{name}\t{count}\n")
    for name, count in sorted(subfamily_counts.items()):
        summary_lines.append(f"atom_subfamily_{name}\t{count}\n")
    for name, count in sorted(route_counts.items()):
        summary_lines.append(f"atom_semantic_route_{name}\t{count}\n")
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
        "atom_subfamily",
        "atom_semantic_route",
        "exact_case_id",
        "pattern",
        "flags",
        "input_text",
        "expected_search_result",
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
    with detail.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, delimiter="\t", fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    with summary.open("w", encoding="utf-8") as f:
        f.write("".join(summary_lines))
    print(summary.read_text(encoding="utf-8"), end="")


if __name__ == "__main__":
    main()
