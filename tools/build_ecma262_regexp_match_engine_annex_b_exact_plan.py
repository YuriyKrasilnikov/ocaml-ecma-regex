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


DETAIL_NAME = "ecma262-regexp-match-engine-annex-b-exact-plan.tsv"
SUMMARY_NAME = "ecma262-regexp-match-engine-annex-b-exact-plan.summary"
TARGET_TEST_ARTIFACT = "test/test_ecma262_match_engine_annex_b_exact_plan.ml"
EXPECTED_WORKLIST_ROWS = 49


def selected_worklist_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return select_worklist_rows(
        rows,
        include_row=lambda row: row["mapping_family"] == "match_engine_annex_b_annexB"
        and row["executable_layer"] == "match_engine"
        and row["ledger_state"] == "open_requirement_to_test_mapping_missing",
        sort_key=lambda row: (row["clause_id"], suffix_number(row["requirement_id"])),
        expected_count=EXPECTED_WORKLIST_ROWS,
        count_message=lambda selected_count: (
            f"expected {EXPECTED_WORKLIST_ROWS} Annex B match-engine rows, "
            f"selected {selected_count}"
        ),
    )


def executable_case(
    *,
    subfamily: str,
    route: str,
    case_family: str,
    pattern: str,
    input_text: str,
    expected_start_index: str,
    expected_end_index: str,
    expected_match_text: str,
    expected_behavior: str,
    obligation: str,
) -> dict[str, str]:
    return {
        "annex_b_subfamily": subfamily,
        "annex_b_route": route,
        "exact_case_family": case_family,
        "pattern": pattern,
        "flags": "",
        "input_text": input_text,
        "expected_search_result": "true",
        "expected_exec_result": "true",
        "expected_start_index": expected_start_index,
        "expected_end_index": expected_end_index,
        "expected_match_text": expected_match_text,
        "expected_behavior": expected_behavior,
        "coverage_credit": "none_match_engine_annex_b_exact_planned",
        "plan_state": "planned_not_executable",
        "target_test_artifact": TARGET_TEST_ARTIFACT,
        "exact_case_obligation": obligation,
        "observability_status": "search_and_exec_observable",
        "observability_reason": (
            "public Ecma_regex.search observes boolean success and public "
            "Ecma_regex.exec observes start, end, and matched text for this "
            "Annex B BMP-pattern match-engine route"
        ),
        "next_action": "materialize_match_engine_annex_b_exact_case",
    }


def atom_quantifier_reference(obligation: str) -> dict[str, str]:
    return executable_case(
        subfamily="compile_subpattern_substitution",
        route="atom_quantifier_reference",
        case_family="atom_quantifier_reference",
        pattern="a+",
        input_text="aa",
        expected_start_index="0",
        expected_end_index="2",
        expected_match_text="aa",
        expected_behavior="annex_b_atom_quantifier_reference_observable",
        obligation=obligation,
    )


def quantified_positive_lookahead(obligation: str) -> dict[str, str]:
    return executable_case(
        subfamily="quantifiable_assertion",
        route="positive_lookahead_quantifier",
        case_family="positive_lookahead_quantifier",
        pattern="(?=a)+a",
        input_text="a",
        expected_start_index="0",
        expected_end_index="1",
        expected_match_text="a",
        expected_behavior="annex_b_quantified_positive_lookahead_observable",
        obligation=obligation,
    )


def quantified_negative_lookahead(obligation: str) -> dict[str, str]:
    return executable_case(
        subfamily="quantifiable_assertion",
        route="negative_lookahead_quantifier",
        case_family="negative_lookahead_quantifier",
        pattern="(?!b)+a",
        input_text="a",
        expected_start_index="0",
        expected_end_index="1",
        expected_match_text="a",
        expected_behavior="annex_b_quantified_negative_lookahead_observable",
        obligation=obligation,
    )


def extended_backslash_c_atom(obligation: str) -> dict[str, str]:
    return executable_case(
        subfamily="extended_atom",
        route="backslash_lookahead_c_literal",
        case_family="extended_backslash_c_atom",
        pattern="\\c",
        input_text="\\c",
        expected_start_index="0",
        expected_end_index="2",
        expected_match_text="\\c",
        expected_behavior="annex_b_extended_backslash_c_atom_observable",
        obligation=obligation,
    )


def extended_backslash_c_quantifier(obligation: str) -> dict[str, str]:
    return executable_case(
        subfamily="extended_atom",
        route="extended_atom_quantifier",
        case_family="extended_backslash_c_quantifier",
        pattern="\\c+",
        input_text="\\cc",
        expected_start_index="0",
        expected_end_index="3",
        expected_match_text="\\cc",
        expected_behavior="annex_b_extended_atom_quantifier_observable",
        obligation=obligation,
    )


def extended_pattern_character(obligation: str) -> dict[str, str]:
    return executable_case(
        subfamily="extended_atom",
        route="extended_pattern_character",
        case_family="extended_pattern_character_literal",
        pattern="]",
        input_text="]",
        expected_start_index="0",
        expected_end_index="1",
        expected_match_text="]",
        expected_behavior="annex_b_extended_pattern_character_observable",
        obligation=obligation,
    )


def class_range_or_union_left(obligation: str, input_text: str, behavior: str) -> dict[str, str]:
    return executable_case(
        subfamily="compile_to_charset",
        route="class_range_or_union_left_escape",
        case_family=f"class_range_or_union_left_{safe_id(behavior)}",
        pattern="[\\d-ab]",
        input_text=input_text,
        expected_start_index="0",
        expected_end_index="1",
        expected_match_text=input_text,
        expected_behavior=behavior,
        obligation=obligation,
    )


def class_range_or_union_right(obligation: str, input_text: str, behavior: str) -> dict[str, str]:
    return executable_case(
        subfamily="compile_to_charset",
        route="class_range_or_union_right_escape",
        case_family=f"class_range_or_union_right_{safe_id(behavior)}",
        pattern="[a-\\db]",
        input_text=input_text,
        expected_start_index="0",
        expected_end_index="1",
        expected_match_text=input_text,
        expected_behavior=behavior,
        obligation=obligation,
    )


def class_control_digit(obligation: str) -> dict[str, str]:
    return executable_case(
        subfamily="compile_to_charset",
        route="class_control_letter",
        case_family="class_control_digit_escape",
        pattern="[\\c1]",
        input_text="\\x11",
        expected_start_index="0",
        expected_end_index="1",
        expected_match_text="\\x11",
        expected_behavior="annex_b_class_control_letter_observable",
        obligation=obligation,
    )


def class_backslash_c(obligation: str) -> dict[str, str]:
    return executable_case(
        subfamily="compile_to_charset",
        route="class_atom_no_dash_backslash_c",
        case_family="class_backslash_c_literal",
        pattern="[\\c]",
        input_text="\\\\",
        expected_start_index="0",
        expected_end_index="1",
        expected_match_text="\\\\",
        expected_behavior="annex_b_class_atom_no_dash_backslash_c_observable",
        obligation=obligation,
    )


def simple_character_range(obligation: str) -> dict[str, str]:
    return executable_case(
        subfamily="character_range_or_union",
        route="single_character_range",
        case_family="single_character_range",
        pattern="[a-c]",
        input_text="b",
        expected_start_index="0",
        expected_end_index="1",
        expected_match_text="b",
        expected_behavior="annex_b_character_range_fallback_observable",
        obligation=obligation,
    )


def classify_requirement(row: dict[str, str]) -> dict[str, str]:
    clause_id = row["clause_id"]
    ordinal = suffix_number(row["requirement_id"])
    text = row["requirement_text"]

    if clause_id == "B.1.2.5":
        if ordinal in {1, 2, 3}:
            return quantified_positive_lookahead(text)
        if ordinal in {4, 7, 10}:
            return atom_quantifier_reference(text)
        if ordinal in {5, 6}:
            return extended_backslash_c_quantifier(text)
        if ordinal in {8, 9}:
            return extended_pattern_character(text)

    if clause_id == "B.1.2.6":
        if ordinal in {1, 2}:
            return quantified_positive_lookahead(text)
        if ordinal == 3:
            return quantified_negative_lookahead(text)

    if clause_id == "B.1.2.7":
        if ordinal in {1, 2}:
            return extended_pattern_character(text)
        if ordinal in {3, 4, 5}:
            return extended_backslash_c_atom(text)
        if ordinal in {6, 7, 8, 9}:
            return extended_pattern_character(text)

    if clause_id == "B.1.2.8":
        if ordinal in {1, 2, 3, 7, 8}:
            return class_range_or_union_left(
                text, "-", "annex_b_character_range_or_union_hyphen_observable"
            )
        if ordinal == 4:
            return class_range_or_union_left(
                text, "5", "annex_b_compile_to_charset_first_atom_observable"
            )
        if ordinal == 5:
            return class_range_or_union_left(
                text, "a", "annex_b_compile_to_charset_second_atom_observable"
            )
        if ordinal == 6:
            return class_range_or_union_left(
                text, "b", "annex_b_compile_to_charset_class_contents_observable"
            )
        if ordinal in {9, 13, 14}:
            return class_range_or_union_right(
                text, "-", "annex_b_character_range_or_union_hyphen_observable"
            )
        if ordinal == 10:
            return class_range_or_union_right(
                text, "a", "annex_b_compile_to_charset_class_atom_no_dash_observable"
            )
        if ordinal == 11:
            return class_range_or_union_right(
                text, "5", "annex_b_compile_to_charset_class_atom_observable"
            )
        if ordinal == 12:
            return class_range_or_union_right(
                text, "b", "annex_b_compile_to_charset_class_contents_observable"
            )
        if ordinal in {15, 16, 17, 18, 19}:
            return class_control_digit(text)
        if ordinal in {20, 21}:
            return class_backslash_c(text)

    if clause_id == "B.1.2.8.1":
        if ordinal in {1, 2, 3, 4}:
            return class_range_or_union_right(
                text, "-", "annex_b_character_range_or_union_hyphen_observable"
            )
        if ordinal == 5:
            return class_range_or_union_right(
                text, "5", "annex_b_character_range_or_union_union_observable"
            )
        if ordinal == 6:
            return simple_character_range(text)

    raise SystemExit(
        f"unclassified Annex B requirement {row['requirement_id']} "
        f"({clause_id}, ordinal {ordinal})"
    )


def plan_row(row: dict[str, str]) -> dict[str, str]:
    requirement_id = row["requirement_id"]
    case = classify_requirement(row)
    exact_case_id = (
        f"match-engine-annex-b-exact:{requirement_id}:"
        f"{safe_id(case['exact_case_family'])}"
    )
    return {
        "plan_id": f"match-engine-annex-b-exact-plan:{requirement_id}",
        **copy_requirement_metadata(row, include_local_id=True),
        "mapping_family": "match_engine_annex_b_annexB",
        "executable_layer": "match_engine",
        "exact_case_id": exact_case_id,
        **case,
        "plan_reason": (
            "Annex B BMP-pattern runtime semantics are credited only through "
            "exact public search/exec cases that prove the concrete parser and "
            "matcher route for this requirement row"
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
    search_counts = Counter(row["expected_search_result"] for row in rows)
    exec_counts = Counter(row["expected_exec_result"] for row in rows)
    subfamily_counts = Counter(row["annex_b_subfamily"] for row in rows)
    route_counts = Counter(row["annex_b_route"] for row in rows)
    clause_counts = Counter(row["clause_id"] for row in rows)
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
        f"match_engine_annex_b_exact_plan_rows\t{len(rows)}\n",
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
    for name, count in sorted(search_counts.items()):
        summary_lines.append(f"expected_search_result_{name}\t{count}\n")
    for name, count in sorted(exec_counts.items()):
        summary_lines.append(f"expected_exec_result_{name}\t{count}\n")
    for name, count in sorted(subfamily_counts.items()):
        summary_lines.append(f"annex_b_subfamily_{name}\t{count}\n")
    for name, count in sorted(route_counts.items()):
        summary_lines.append(f"annex_b_route_{name}\t{count}\n")
    for name, count in sorted(clause_counts.items()):
        summary_lines.append(f"clause_{name}\t{count}\n")
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
        "annex_b_subfamily",
        "annex_b_route",
        "exact_case_family",
        "exact_case_id",
        "pattern",
        "flags",
        "input_text",
        "expected_search_result",
        "expected_exec_result",
        "expected_start_index",
        "expected_end_index",
        "expected_match_text",
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
