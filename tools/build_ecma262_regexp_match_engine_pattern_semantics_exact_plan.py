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
    validate_expected_fields,
    validate_unique_ids,
)


DETAIL_NAME = "ecma262-regexp-match-engine-pattern-semantics-exact-plan.tsv"
SUMMARY_NAME = "ecma262-regexp-match-engine-pattern-semantics-exact-plan.summary"
TARGET_TEST_ARTIFACT = "test/test_ecma262_match_engine_pattern_semantics_exact_plan.ml"


def executable_case(
    *,
    subfamily: str,
    route: str,
    pattern: str,
    flags: str,
    input_text: str,
    expected_start_index: str,
    expected_end_index: str,
    expected_match_text: str,
    expected_behavior: str,
    obligation: str,
) -> dict[str, str]:
    return {
        "pattern_semantics_subfamily": subfamily,
        "pattern_semantics_route": route,
        "pattern": pattern,
        "flags": flags,
        "input_text": input_text,
        "expected_search_result": "true",
        "expected_exec_result": "true",
        "expected_start_index": expected_start_index,
        "expected_end_index": expected_end_index,
        "expected_match_text": expected_match_text,
        "expected_behavior": expected_behavior,
        "expected_model_field": "",
        "model_scenario": "",
        "coverage_credit": "none_match_engine_pattern_semantics_exact_planned",
        "plan_state": "planned_not_executable",
        "target_test_artifact": TARGET_TEST_ARTIFACT,
        "exact_case_obligation": obligation,
        "observability_status": "search_and_exec_observable",
        "observability_reason": (
            "public Ecma_regex.search observes boolean success and public "
            "Ecma_regex.exec observes start, end, and matched text for this "
            "Pattern Semantics route"
        ),
        "next_action": "materialize_match_engine_pattern_semantics_exact_case",
    }


def internal_model_case(
    *,
    subfamily: str,
    route: str,
    pattern: str,
    flags: str,
    input_text: str,
    expected_model_field: str,
    model_scenario: str,
    obligation: str,
) -> dict[str, str]:
    return {
        "pattern_semantics_subfamily": subfamily,
        "pattern_semantics_route": route,
        "pattern": pattern,
        "flags": flags,
        "input_text": input_text,
        "expected_search_result": "not_applicable",
        "expected_exec_result": "not_applicable",
        "expected_start_index": "",
        "expected_end_index": "",
        "expected_match_text": "",
        "expected_behavior": expected_model_field,
        "expected_model_field": expected_model_field,
        "model_scenario": model_scenario,
        "coverage_credit": "none_match_engine_pattern_semantics_exact_planned",
        "plan_state": "planned_not_executable",
        "target_test_artifact": TARGET_TEST_ARTIFACT,
        "exact_case_obligation": obligation,
        "observability_status": "internal_pattern_semantics_model_observable",
        "observability_reason": (
            "internal Ecma_regex_core Pattern Semantics model observer exposes "
            "the ECMA-262 abstract data/operation field required by this row "
            "without expanding the public API"
        ),
        "next_action": "materialize_match_engine_pattern_semantics_exact_case",
    }


def deferred_case(
    *,
    subfamily: str,
    route: str,
    status: str,
    obligation: str,
) -> dict[str, str]:
    return {
        "pattern_semantics_subfamily": subfamily,
        "pattern_semantics_route": route,
        "pattern": "",
        "flags": "",
        "input_text": "",
        "expected_search_result": "not_observable",
        "expected_exec_result": "not_observable",
        "expected_start_index": "",
        "expected_end_index": "",
        "expected_match_text": "",
        "expected_behavior": status,
        "expected_model_field": "",
        "model_scenario": "",
        "coverage_credit": "none_match_engine_pattern_semantics_exact_deferred",
        "plan_state": f"deferred_{status}",
        "target_test_artifact": "",
        "exact_case_obligation": obligation,
        "observability_status": status,
        "observability_reason": obligation,
        "next_action": f"design_{status}_before_credit",
    }


def exec_basic(subfamily: str, route: str, behavior: str, obligation: str) -> dict[str, str]:
    return executable_case(
        subfamily=subfamily,
        route=route,
        pattern="a",
        flags="",
        input_text="a",
        expected_start_index="0",
        expected_end_index="1",
        expected_match_text="a",
        expected_behavior=behavior,
        obligation=obligation,
    )


def classify_requirement(row: dict[str, str]) -> dict[str, str]:
    requirement_id = row["requirement_id"]
    clause_id = row["clause_id"]
    ordinal = int(requirement_id.rsplit("-", 1)[1])
    text = row["requirement_text"]

    if clause_id == "22.2.2":
        if ordinal == 1:
            return exec_basic(
                "pattern_closure",
                "abstract_closure_matcher",
                "pattern_closure_matcher_observable",
                text,
            )
        if ordinal in {2, 3}:
            return internal_model_case(
                subfamily="unicode_input_model",
                route="utf16_bmp_unicode_character_model",
                pattern="a",
                flags=("u" if ordinal == 2 else ""),
                input_text="a",
                expected_model_field=(
                    "unicode_pattern_definition_observed"
                    if ordinal == 2
                    else "source_character_list_model_observed"
                ),
                model_scenario="utf16_bmp_unicode_character_model",
                obligation=text,
            )

    if clause_id == "22.2.2.1":
        return internal_model_case(
            subfamily="pattern_semantics_notation",
            route="internal_data_structure_notation",
            pattern="a",
            flags="",
            input_text="a",
            expected_model_field=(
                "pattern_semantics_internal_data_structures_observed"
            ),
            model_scenario="pattern_semantics_notation",
            obligation=text,
        )

    if clause_id == "22.2.2.1.1":
        record_cases = {
            4: executable_case(
                subfamily="regexp_record_flag",
                route="ignore_case_flag_to_matcher",
                pattern="a",
                flags="i",
                input_text="A",
                expected_start_index="0",
                expected_end_index="1",
                expected_match_text="A",
                expected_behavior="regexp_record_ignore_case_flag_observable",
                obligation=text,
            ),
            5: executable_case(
                subfamily="regexp_record_flag",
                route="multiline_flag_to_anchor_matcher",
                pattern="^a",
                flags="m",
                input_text="\\na",
                expected_start_index="1",
                expected_end_index="2",
                expected_match_text="a",
                expected_behavior="regexp_record_multiline_flag_observable",
                obligation=text,
            ),
            6: executable_case(
                subfamily="regexp_record_flag",
                route="dot_all_flag_to_dot_matcher",
                pattern=".",
                flags="s",
                input_text="\\n",
                expected_start_index="0",
                expected_end_index="1",
                expected_match_text="\\n",
                expected_behavior="regexp_record_dot_all_flag_observable",
                obligation=text,
            ),
            7: executable_case(
                subfamily="regexp_record_flag",
                route="unicode_flag_to_pattern_parser_and_matcher",
                pattern="\\u{41}",
                flags="u",
                input_text="A",
                expected_start_index="0",
                expected_end_index="1",
                expected_match_text="A",
                expected_behavior="regexp_record_unicode_flag_observable",
                obligation=text,
            ),
            8: executable_case(
                subfamily="regexp_record_flag",
                route="unicode_sets_flag_to_pattern_parser_and_matcher",
                pattern="\\u{41}",
                flags="v",
                input_text="A",
                expected_start_index="0",
                expected_end_index="1",
                expected_match_text="A",
                expected_behavior="regexp_record_unicode_sets_flag_observable",
                obligation=text,
            ),
            9: executable_case(
                subfamily="regexp_record_capture_count",
                route="capturing_groups_count_to_backreference_matcher",
                pattern="(a)\\1",
                flags="",
                input_text="aa",
                expected_start_index="0",
                expected_end_index="2",
                expected_match_text="aa",
                expected_behavior="regexp_record_capturing_groups_count_observable",
                obligation=text,
            ),
        }
        if ordinal in record_cases:
            return record_cases[ordinal]
        return internal_model_case(
            subfamily="regexp_record_inventory",
            route="record_field_inventory_model",
            pattern="(a)",
            flags="imsuv".replace("uv", "u"),
            input_text="A",
            expected_model_field={
                1: "regexp_record_inventory_observed",
                2: "regexp_record_fields_table_observed",
                3: "regexp_record_matcher_slot_observed",
            }[ordinal],
            model_scenario="regexp_record_inventory",
            obligation=text,
        )

    if clause_id == "22.2.2.2":
        executable = {
            1: exec_basic(
                "compile_pattern_operation",
                "compile_pattern_closure_shape",
                "compile_pattern_operation_returns_matcher",
                text,
            ),
            2: executable_case(
                subfamily="compile_pattern_dispatch",
                route="pattern_disjunction_dispatch",
                pattern="a|b",
                flags="",
                input_text="b",
                expected_start_index="0",
                expected_end_index="1",
                expected_match_text="b",
                expected_behavior="compile_pattern_uses_disjunction",
                obligation=text,
            ),
            3: executable_case(
                subfamily="compile_pattern_dispatch",
                route="compile_subpattern_invocation",
                pattern="ab",
                flags="",
                input_text="ab",
                expected_start_index="0",
                expected_end_index="2",
                expected_match_text="ab",
                expected_behavior="compile_pattern_invokes_compile_subpattern",
                obligation=text,
            ),
            4: executable_case(
                subfamily="compile_pattern_operation",
                route="compile_pattern_input_index_parameters",
                pattern="a",
                flags="",
                input_text="ba",
                expected_start_index="1",
                expected_end_index="2",
                expected_match_text="a",
                expected_behavior="compile_pattern_closure_uses_input_and_index",
                obligation=text,
            ),
            9: exec_basic(
                "compile_pattern_continuation",
                "compile_pattern_final_continuation_result",
                "compile_pattern_final_continuation_returns_match_state",
                text,
            ),
            10: executable_case(
                subfamily="compile_pattern_capture_initialization",
                route="initial_undefined_capture_list",
                pattern="(a)?\\1b",
                flags="",
                input_text="b",
                expected_start_index="0",
                expected_end_index="1",
                expected_match_text="b",
                expected_behavior="compile_pattern_initializes_captures_undefined",
                obligation=text,
            ),
            11: executable_case(
                subfamily="compile_pattern_match_state",
                route="initial_match_state_end_index",
                pattern="a",
                flags="",
                input_text="ba",
                expected_start_index="1",
                expected_end_index="2",
                expected_match_text="a",
                expected_behavior="compile_pattern_initial_match_state_observable",
                obligation=text,
            ),
            12: exec_basic(
                "compile_pattern_dispatch",
                "compile_pattern_returns_subpattern_result",
                "compile_pattern_returns_matcher_result",
                text,
            ),
        }
        if ordinal in executable:
            return executable[ordinal]
        internal_model = {
            5: (
                "requires_compile_pattern_input_list_model",
                "compile_pattern_input_list",
                "compile_pattern_input_list_assertion_observed",
            ),
            6: (
                "requires_compile_pattern_index_model",
                "compile_pattern_index",
                "compile_pattern_index_bounds_assertion_observed",
            ),
            7: (
                "requires_compile_pattern_continuation_model",
                "compile_pattern_continuation",
                "compile_pattern_continuation_closure_observed",
            ),
            8: (
                "requires_compile_pattern_match_state_model",
                "compile_pattern_match_state",
                "compile_pattern_match_state_assertion_observed",
            ),
        }[ordinal]
        return internal_model_case(
            subfamily="compile_pattern_internal_model",
            route=internal_model[0],
            pattern="a",
            flags="",
            input_text="ba",
            expected_model_field=internal_model[2],
            model_scenario=internal_model[1],
            obligation=text,
        )

    if clause_id == "22.2.2.3":
        executable = {
            3: executable_case(
                subfamily="compile_subpattern_alternation",
                route="disjunction_alternative_or_disjunction",
                pattern="a|b",
                flags="",
                input_text="b",
                expected_start_index="0",
                expected_end_index="1",
                expected_match_text="b",
                expected_behavior="compile_subpattern_disjunction_observable",
                obligation=text,
            ),
            4: executable_case(
                subfamily="compile_subpattern_alternation",
                route="first_alternative_matcher",
                pattern="a|b",
                flags="",
                input_text="a",
                expected_start_index="0",
                expected_end_index="1",
                expected_match_text="a",
                expected_behavior="compile_subpattern_first_alternative_observable",
                obligation=text,
            ),
            5: executable_case(
                subfamily="compile_subpattern_alternation",
                route="rest_disjunction_matcher",
                pattern="a|b",
                flags="",
                input_text="b",
                expected_start_index="0",
                expected_end_index="1",
                expected_match_text="b",
                expected_behavior="compile_subpattern_rest_disjunction_observable",
                obligation=text,
            ),
            6: executable_case(
                subfamily="compile_subpattern_alternation",
                route="match_two_alternatives_dispatch",
                pattern="a|b",
                flags="",
                input_text="b",
                expected_start_index="0",
                expected_end_index="1",
                expected_match_text="b",
                expected_behavior="compile_subpattern_match_two_alternatives_observable",
                obligation=text,
            ),
            7: executable_case(
                subfamily="compile_subpattern_empty",
                route="empty_alternative_grammar",
                pattern="a|",
                flags="",
                input_text="",
                expected_start_index="0",
                expected_end_index="0",
                expected_match_text="",
                expected_behavior="compile_subpattern_empty_alternative_observable",
                obligation=text,
            ),
            8: executable_case(
                subfamily="compile_subpattern_empty",
                route="empty_matcher_dispatch",
                pattern="",
                flags="",
                input_text="x",
                expected_start_index="0",
                expected_end_index="0",
                expected_match_text="",
                expected_behavior="compile_subpattern_empty_matcher_observable",
                obligation=text,
            ),
            9: executable_case(
                subfamily="compile_subpattern_sequence",
                route="alternative_term_grammar",
                pattern="ab",
                flags="",
                input_text="ab",
                expected_start_index="0",
                expected_end_index="2",
                expected_match_text="ab",
                expected_behavior="compile_subpattern_sequence_grammar_observable",
                obligation=text,
            ),
            10: executable_case(
                subfamily="compile_subpattern_sequence",
                route="sequence_left_matcher",
                pattern="ab",
                flags="",
                input_text="ab",
                expected_start_index="0",
                expected_end_index="2",
                expected_match_text="ab",
                expected_behavior="compile_subpattern_sequence_left_observable",
                obligation=text,
            ),
            11: executable_case(
                subfamily="compile_subpattern_sequence",
                route="sequence_right_matcher",
                pattern="ab",
                flags="",
                input_text="ab",
                expected_start_index="0",
                expected_end_index="2",
                expected_match_text="ab",
                expected_behavior="compile_subpattern_sequence_right_observable",
                obligation=text,
            ),
            12: executable_case(
                subfamily="compile_subpattern_sequence",
                route="match_sequence_dispatch",
                pattern="ab",
                flags="",
                input_text="ab",
                expected_start_index="0",
                expected_end_index="2",
                expected_match_text="ab",
                expected_behavior="compile_subpattern_match_sequence_observable",
                obligation=text,
            ),
            13: executable_case(
                subfamily="compile_subpattern_assertion",
                route="term_assertion_grammar",
                pattern="^a",
                flags="",
                input_text="a",
                expected_start_index="0",
                expected_end_index="1",
                expected_match_text="a",
                expected_behavior="compile_subpattern_assertion_term_observable",
                obligation=text,
            ),
            14: executable_case(
                subfamily="compile_subpattern_assertion",
                route="compile_assertion_dispatch",
                pattern="^a",
                flags="",
                input_text="a",
                expected_start_index="0",
                expected_end_index="1",
                expected_match_text="a",
                expected_behavior="compile_subpattern_compile_assertion_observable",
                obligation=text,
            ),
            15: exec_basic(
                "compile_subpattern_atom",
                "term_atom_grammar",
                "compile_subpattern_atom_term_observable",
                text,
            ),
            16: exec_basic(
                "compile_subpattern_atom",
                "compile_atom_dispatch",
                "compile_subpattern_compile_atom_observable",
                text,
            ),
            17: executable_case(
                subfamily="compile_subpattern_quantifier",
                route="term_atom_quantifier_grammar",
                pattern="a*",
                flags="",
                input_text="aaa",
                expected_start_index="0",
                expected_end_index="3",
                expected_match_text="aaa",
                expected_behavior="compile_subpattern_quantified_term_observable",
                obligation=text,
            ),
            18: executable_case(
                subfamily="compile_subpattern_quantifier",
                route="quantified_atom_compile_atom_dispatch",
                pattern="a*",
                flags="",
                input_text="aaa",
                expected_start_index="0",
                expected_end_index="3",
                expected_match_text="aaa",
                expected_behavior="compile_subpattern_quantified_atom_observable",
                obligation=text,
            ),
            19: executable_case(
                subfamily="compile_subpattern_quantifier",
                route="compile_quantifier_dispatch",
                pattern="a*",
                flags="",
                input_text="aaa",
                expected_start_index="0",
                expected_end_index="3",
                expected_match_text="aaa",
                expected_behavior="compile_subpattern_compile_quantifier_observable",
                obligation=text,
            ),
            26: executable_case(
                subfamily="compile_subpattern_quantifier",
                route="repeat_matcher_dispatch",
                pattern="a*",
                flags="",
                input_text="aaa",
                expected_start_index="0",
                expected_end_index="3",
                expected_match_text="aaa",
                expected_behavior="compile_subpattern_repeat_matcher_observable",
                obligation=text,
            ),
        }
        if ordinal in executable:
            return executable[ordinal]
        if ordinal in {1, 2}:
            return internal_model_case(
                subfamily="compile_subpattern_operation_model",
                route="compile_subpattern_operation_inventory",
                pattern="a|b",
                flags="",
                input_text="b",
                expected_model_field=(
                    "compile_subpattern_operation_model_observed"
                    if ordinal == 1
                    else "compile_subpattern_piecewise_inventory_observed"
                ),
                model_scenario=(
                    "compile_subpattern_operation"
                    if ordinal == 1
                    else "compile_subpattern_piecewise_inventory"
                ),
                obligation=text,
            )
        if ordinal == 20:
            return internal_model_case(
                subfamily="compile_subpattern_quantifier_model",
                route="quantifier_bounds_assert_model",
                pattern="a{1,2}",
                flags="",
                input_text="aa",
                expected_model_field="quantifier_bounds_assertion_observed",
                model_scenario="quantifier_bounds_assert",
                obligation=text,
            )
        if ordinal in {21, 22}:
            return internal_model_case(
                subfamily="compile_subpattern_quantifier_model",
                route="quantified_capture_index_model",
                pattern="(a)(b)*",
                flags="",
                input_text="abb",
                expected_model_field=(
                    "quantified_paren_index_observed"
                    if ordinal == 21
                    else "quantified_paren_count_observed"
                ),
                model_scenario="quantified_capture_index",
                obligation=text,
            )
        if ordinal in {23, 24, 25}:
            return internal_model_case(
                subfamily="compile_subpattern_quantifier_model",
                route="quantified_repeat_closure_model",
                pattern="(a)*",
                flags="",
                input_text="aa",
                expected_model_field={
                    23: "quantified_repeat_closure_observed",
                    24: "quantified_repeat_match_state_parameter_observed",
                    25: "quantified_repeat_continuation_parameter_observed",
                }[ordinal],
                model_scenario="quantified_repeat_closure",
                obligation=text,
            )

    if clause_id == "22.2.2.3.2":
        if ordinal in {1, 2, 5}:
            return executable_case(
                subfamily="empty_matcher",
                route="empty_matcher_continuation",
                pattern="",
                flags="",
                input_text="x",
                expected_start_index="0",
                expected_end_index="0",
                expected_match_text="",
                expected_behavior={
                    1: "empty_matcher_operation_observable",
                    2: "empty_matcher_closure_observable",
                    5: "empty_matcher_returns_continuation_result",
                }[ordinal],
                obligation=text,
            )
        return internal_model_case(
            subfamily="empty_matcher",
            route="empty_matcher_state_model",
            pattern="",
            flags="",
            input_text="x",
            expected_model_field={
                3: "empty_matcher_match_state_parameter_observed",
                4: "empty_matcher_continuation_parameter_observed",
            }[ordinal],
            model_scenario="empty_matcher_state",
            obligation=text,
        )

    raise SystemExit(f"unclassified Pattern Semantics requirement row: {requirement_id}")


def include_requirement_row(row: dict[str, str]) -> bool:
    return (
        row["product_surface"] == "match_engine"
        and row["semantic_family"] == "pattern_semantics"
        and row["route_status"] == "needs_requirement_to_test_case_mapping"
    )


def selected_requirement_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return select_requirement_rows(
        rows,
        include_row=include_requirement_row,
        sort_key=lambda row: (row["clause_id"], row["requirement_id"]),
        expected_count=56,
        count_message=lambda count: (
            "expected 56 match-engine Pattern Semantics rows, got "
            f"{count}"
        ),
    )


def validate_requirement_row(row: dict[str, str]) -> None:
    expected = {
        "product_surface": "match_engine",
        "semantic_family": "pattern_semantics",
        "route_status": "needs_requirement_to_test_case_mapping",
    }
    validate_expected_fields(row, expected, context="Pattern Semantics row")
    require_coverage_area(
        row,
        "regexp_exec_and_captures",
        context="Pattern Semantics row",
    )


def plan_row(requirement: dict[str, str]) -> dict[str, str]:
    validate_requirement_row(requirement)
    requirement_id = requirement["requirement_id"]
    case = classify_requirement(requirement)
    exact_case_id = (
        f"match-engine-pattern-semantics-exact:{requirement_id}:"
        f"{safe_id(case['pattern_semantics_subfamily'])}"
    )
    return {
        "plan_id": f"match-engine-pattern-semantics-exact-plan:{requirement_id}",
        **copy_requirement_metadata(requirement, include_local_id=False),
        "mapping_family": "match_engine_pattern_semantics",
        "executable_layer": "match_engine",
        "exact_case_id": exact_case_id,
        **case,
        "plan_reason": (
            "Pattern Semantics row is classified before runtime credit; "
            "executable rows must pass this exact gate before exactness audit "
            "or coverage ledger may consume them"
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
            "requirement_text",
            "coverage_areas",
            "semantic_family",
            "product_surface",
            "route_status",
        },
    )

    rows = [plan_row(row) for row in selected_requirement_rows(requirement_rows)]
    validate_unique_ids(rows)

    state_counts = Counter(row["plan_state"] for row in rows)
    credit_counts = Counter(row["coverage_credit"] for row in rows)
    behavior_counts = Counter(row["expected_behavior"] for row in rows)
    search_counts = Counter(row["expected_search_result"] for row in rows)
    exec_counts = Counter(row["expected_exec_result"] for row in rows)
    clause_counts = Counter(row["clause_id"] for row in rows)
    subfamily_counts = Counter(row["pattern_semantics_subfamily"] for row in rows)
    route_counts = Counter(row["pattern_semantics_route"] for row in rows)
    observability_counts = Counter(row["observability_status"] for row in rows)

    coverage_credit_rows = sum(
        count for credit, count in credit_counts.items() if not credit.startswith("none")
    )
    planned_executable_rows = state_counts.get("planned_not_executable", 0)
    deferred_rows = sum(
        count for state, count in state_counts.items() if state.startswith("deferred_")
    )

    summary_lines = [
        "ecma262_snapshot\t2026\n",
        f"input_requirements\t{requirements}\n",
        f"input_requirement_rows\t{len(requirement_rows)}\n",
        f"match_engine_pattern_semantics_exact_plan_rows\t{len(rows)}\n",
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
    for name, count in sorted(exec_counts.items()):
        summary_lines.append(f"expected_exec_result_{name}\t{count}\n")
    for name, count in sorted(clause_counts.items()):
        summary_lines.append(f"clause_id_{name}\t{count}\n")
    for name, count in sorted(subfamily_counts.items()):
        summary_lines.append(f"pattern_semantics_subfamily_{name}\t{count}\n")
    for name, count in sorted(route_counts.items()):
        summary_lines.append(f"pattern_semantics_route_{name}\t{count}\n")
    for name, count in sorted(observability_counts.items()):
        summary_lines.append(f"observability_status_{name}\t{count}\n")

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
        "requirement_text",
        "mapping_family",
        "executable_layer",
        "pattern_semantics_subfamily",
        "pattern_semantics_route",
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
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    summary.write_text("".join(summary_lines), encoding="utf-8")


if __name__ == "__main__":
    main()
