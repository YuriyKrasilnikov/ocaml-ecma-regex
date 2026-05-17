#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path

from ecma262_tooling import bool_text, read_tsv, split_csv, validate_unique_ids


DETAIL_NAME = "ecma262-regexp-exactness-audit.tsv"
SUMMARY_NAME = "ecma262-regexp-exactness-audit.summary"
REUSED_EXACT_TARGET_TEST_ARTIFACT = (
    "test/test_ecma262_reused_candidate_exact_compile_parser.ml"
)
COMPILE_PARSER_EXACT_TARGET_TEST_ARTIFACT = (
    "test/test_ecma262_compile_parser_exact_plan.ml"
)
LITERAL_LEXER_EXACT_TARGET_TEST_ARTIFACT = (
    "test/test_ecma262_literal_lexer_exact_plan.ml"
)
MATCH_ENGINE_EXACT_TARGET_TEST_ARTIFACT = (
    "test/test_ecma262_match_engine_exact_plan.ml"
)
MATCH_ENGINE_ATOMS_EXACT_TARGET_TEST_ARTIFACT = (
    "test/test_ecma262_match_engine_atoms_exact_plan.ml"
)
MATCH_ENGINE_CAPTURE_EXACT_TARGET_TEST_ARTIFACT = (
    "test/test_ecma262_match_engine_capture_exact_plan.ml"
)
MATCH_ENGINE_UNICODE_SETS_STRING_EXACT_TARGET_TEST_ARTIFACT = (
    "test/test_ecma262_match_engine_unicode_sets_string_exact_plan.ml"
)
MATCH_ENGINE_UNICODE_SETS_ESCAPE_STRING_EXACT_TARGET_TEST_ARTIFACT = (
    "test/test_ecma262_match_engine_unicode_sets_escape_string_exact_plan.ml"
)
MATCH_ENGINE_CHARACTER_CLASSES_EXACT_TARGET_TEST_ARTIFACT = (
    "test/test_ecma262_match_engine_character_classes_exact_plan.ml"
)
MATCH_ENGINE_CONCATENATION_EXACT_TARGET_TEST_ARTIFACT = (
    "test/test_ecma262_match_engine_concatenation_exact_plan.ml"
)
MATCH_ENGINE_BACKREFERENCE_EXACT_TARGET_TEST_ARTIFACT = (
    "test/test_ecma262_match_engine_backreference_exact_plan.ml"
)
MATCH_ENGINE_BACKREFERENCE_MATCHER_EXACT_TARGET_TEST_ARTIFACT = (
    "test/test_ecma262_match_engine_backreference_matcher_exact_plan.ml"
)
MATCH_ENGINE_RESULT_EXACT_TARGET_TEST_ARTIFACT = (
    "test/test_ecma262_match_engine_result_exact_plan.ml"
)
EXEC_RESULT_MATCHING_EXACT_TARGET_TEST_ARTIFACT = (
    "test/test_ecma262_exec_result_matching_exact_plan.ml"
)
EXEC_RESULT_EXEC_EXACT_TARGET_TEST_ARTIFACT = (
    "test/test_ecma262_exec_result_exec_exact_plan.ml"
)
EXEC_RESULT_CAPTURE_EXACT_TARGET_TEST_ARTIFACT = (
    "test/test_ecma262_exec_result_capture_exact_plan.ml"
)
EXEC_RESULT_INDICES_EXACT_TARGET_TEST_ARTIFACT = (
    "test/test_ecma262_exec_result_indices_exact_plan.ml"
)
EXEC_RESULT_INSTANCES_EXACT_TARGET_TEST_ARTIFACT = (
    "test/test_ecma262_exec_result_instances_exact_plan.ml"
)
SPEC_MODEL_EXACT_TARGET_TEST_ARTIFACT = (
    "test/test_ecma262_spec_model_exact_plan.ml"
)
TEST262_LITERAL_LEXER_TARGET_TEST_ARTIFACT = (
    "test/test_test262_regexp_executable_cases.ml"
)
MATCH_ENGINE_START_ANCHOR_EXACT_TARGET_TEST_ARTIFACT = (
    "test/test_ecma262_match_engine_start_anchor_exact_plan.ml"
)
MATCH_ENGINE_END_ANCHOR_EXACT_TARGET_TEST_ARTIFACT = (
    "test/test_ecma262_match_engine_end_anchor_exact_plan.ml"
)
MATCH_ENGINE_ASSERTION_EXACT_TARGET_TEST_ARTIFACT = (
    "test/test_ecma262_match_engine_assertion_exact_plan.ml"
)
MATCH_ENGINE_QUANTIFIER_EXACT_TARGET_TEST_ARTIFACT = (
    "test/test_ecma262_match_engine_quantifier_exact_plan.ml"
)
MATCH_ENGINE_MODIFIER_EXACT_TARGET_TEST_ARTIFACT = (
    "test/test_ecma262_match_engine_modifier_exact_plan.ml"
)
MATCH_ENGINE_PATTERN_SEMANTICS_EXACT_TARGET_TEST_ARTIFACT = (
    "test/test_ecma262_match_engine_pattern_semantics_exact_plan.ml"
)
MATCH_ENGINE_ANNEX_B_EXACT_TARGET_TEST_ARTIFACT = (
    "test/test_ecma262_match_engine_annex_b_exact_plan.ml"
)
MATCH_STATE_EXACT_TARGET_TEST_ARTIFACT = (
    "test/test_ecma262_match_state_exact_plan.ml"
)

KNOWN_EXACTNESS_STATES = [
    "covered_by_compile_parser_exact",
    "covered_by_literal_lexer_exact",
    "covered_by_local_exact_compile_parser",
    "covered_by_match_engine_exact",
    "covered_by_exec_result_exact",
    "covered_by_spec_model_exact",
    "covered_by_test262_literal_lexer_exact",
    "covered_by_reused_candidate_exact_compile_parser",
    "open_missing_selector_coverage",
    "open_local_exact_executable_credit_pending",
    "open_no_case_negative_or_local_exact",
    "open_reused_candidate_needs_exact_proof",
    "open_reused_candidate_manual_spec_review_required",
    "open_unmapped_negative_syntax_case",
    "potential_exact_ready_manual_review",
]

KNOWN_COVERAGE_CREDITS = [
    "compile_parser_exact_requirement_credit",
    "literal_lexer_exact_requirement_credit",
    "local_exact_compile_parser_requirement_credit",
    "match_engine_exact_requirement_credit",
    "exec_result_exact_requirement_credit",
    "spec_model_exact_requirement_credit",
    "test262_literal_lexer_requirement_credit",
    "reused_candidate_exact_compile_parser_requirement_credit",
    "none_missing_selector_coverage",
    "none_local_exact_executable_pending_credit",
    "none_no_executable_case",
    "none_reused_candidate",
    "none_unmapped_corpus",
    "none_manual_review_required",
]

KNOWN_EVIDENCE_KINDS = [
    "compile_parser_exact_case",
    "literal_lexer_exact_case",
    "local_exact_compile_parser_case",
    "match_engine_atoms_exact_case",
    "match_engine_backreference_exact_case",
    "match_engine_backreference_matcher_exact_case",
    "match_engine_capture_exact_case",
    "match_engine_unicode_sets_string_exact_case",
    "match_engine_unicode_sets_escape_string_exact_case",
    "match_engine_character_classes_exact_case",
    "match_engine_concatenation_exact_case",
    "match_engine_exact_case",
    "match_engine_result_exact_case",
    "exec_result_matching_exact_case",
    "exec_result_exec_exact_case",
    "exec_result_capture_exact_case",
    "exec_result_indices_exact_case",
    "exec_result_instances_exact_case",
    "spec_model_exact_case",
    "test262_literal_lexer_exact_case",
    "match_engine_start_anchor_exact_case",
    "match_engine_end_anchor_exact_case",
    "match_engine_assertion_exact_case",
    "match_engine_quantifier_exact_case",
    "match_engine_modifier_exact_case",
    "match_engine_pattern_semantics_exact_case",
    "match_engine_annex_b_exact_case",
    "match_state_exact_case",
    "reused_candidate_exact_compile_parser_case",
    "open_reused_candidate_manual_spec_review",
    "open_negative_or_local_exact_mapping",
    "selected_compile_positive_case",
    "unmapped_negative_syntax_case",
]

KNOWN_NEXT_ACTIONS = [
    "add_selector_complete_case_or_local_exact_test",
    "connect_local_exact_executable_evidence_to_requirement_credit",
    "map_negative_syntax_case_to_requirement",
    "manual_spec_exactness_review_before_credit",
    "none_covered_by_compile_parser_exact",
    "none_covered_by_literal_lexer_exact",
    "none_covered_by_local_exact_compile_parser",
    "none_covered_by_match_engine_exact",
    "none_covered_by_exec_result_exact",
    "none_covered_by_spec_model_exact",
    "none_covered_by_test262_literal_lexer_exact",
    "none_covered_by_reused_candidate_exact_compile_parser",
    "select_negative_syntax_or_local_exact_case",
    "split_reused_candidate_or_add_local_exact_test",
]


def csv_set(value: str) -> set[str]:
    return set(split_csv(value))


def exactness_for_selected(
    row: dict[str, str],
    reuse_counts: Counter[str],
) -> tuple[str, str, str]:
    missing_selectors = split_csv(row["selected_missing_selector_tags"])
    case_id = row["selected_case_id"]
    reuse_count = reuse_counts[case_id]

    if missing_selectors:
        return (
            "open_missing_selector_coverage",
            "none_missing_selector_coverage",
            "selected case does not satisfy every selector tag required by the requirement row",
        )

    if reuse_count > 1:
        return (
            "open_reused_candidate_needs_exact_proof",
            "none_reused_candidate",
            "selected case is reused across multiple requirement rows; exact proof must split or justify reuse before coverage credit",
        )

    return (
        "potential_exact_ready_manual_review",
        "none_manual_review_required",
        "selected case is unique and selector-complete, but manual/spec exactness review is still required before coverage credit",
    )


def validate_local_exact_row(row: dict[str, str]) -> None:
    requirement_id = row["requirement_id"]
    expected = {
        "expected_behavior": "compile_ok",
        "coverage_credit": "none_local_exact_planned",
        "plan_state": "planned_not_executable",
        "target_test_artifact": "test/test_ecma262_local_exact_compile_parser.ml",
        "next_action": "materialize_local_exact_case",
    }
    for field, expected_value in expected.items():
        if row[field] != expected_value:
            raise SystemExit(
                f"local exact row {requirement_id} has {field}={row[field]!r}; "
                f"expected {expected_value!r}"
            )
    for field in [
        "local_case_id",
        "source_file",
        "section_anchor",
        "selector_tags",
        "missing_selector_tags",
        "local_case_family",
        "planned_pattern",
    ]:
        if not row[field]:
            raise SystemExit(f"local exact row {requirement_id} has empty {field}")
    if not Path(row["source_file"]).is_file():
        raise SystemExit(
            f"local exact row {requirement_id} source is missing: {row['source_file']}"
        )
    if not Path(row["target_test_artifact"]).is_file():
        raise SystemExit(
            f"local exact row {requirement_id} target artifact is missing: "
            f"{row['target_test_artifact']}"
        )


def validate_local_exact_against_selector_gap(
    local_exact: dict[str, str],
    selector_gap: dict[str, str],
) -> None:
    requirement_id = local_exact["requirement_id"]
    expected_gap = {
        "selector_gap_state": "local_exact_test_required",
        "next_action": "add_local_exact_compile_or_parser_test",
    }
    for field, expected_value in expected_gap.items():
        if selector_gap[field] != expected_value:
            raise SystemExit(
                f"selector gap row {requirement_id} has {field}={selector_gap[field]!r}; "
                f"expected {expected_value!r}"
            )
    for field in [
        "mapping_family",
        "executable_layer",
        "selector_tags",
        "missing_selector_tags",
    ]:
        if local_exact[field] != selector_gap[field]:
            raise SystemExit(
                f"local exact row {requirement_id} has {field}={local_exact[field]!r}; "
                f"selector gap has {selector_gap[field]!r}"
            )


def local_exact_audit_row(
    local_exact: dict[str, str],
) -> dict[str, str]:
    validate_local_exact_row(local_exact)
    requirement_id = local_exact["requirement_id"]
    if not split_csv(local_exact["missing_selector_tags"]):
        raise SystemExit(f"local exact row {requirement_id} has no missing selectors")
    if not local_exact["local_case_id"].startswith(f"local-exact:{requirement_id}:"):
        raise SystemExit(
            f"local exact row {requirement_id} case id has wrong prefix: "
            f"{local_exact['local_case_id']}"
        )
    return {
        "audit_id": f"exactness:{requirement_id}:{local_exact['local_case_id']}",
        "audit_scope": "ecma262_requirement",
        "requirement_id": requirement_id,
        "mapping_family": local_exact["mapping_family"],
        "executable_layer": local_exact["executable_layer"],
        "evidence_kind": "local_exact_compile_parser_case",
        "case_id": local_exact["local_case_id"],
        "case_source": f"{local_exact['source_file']}#{local_exact['section_anchor']}",
        "expected_behavior": local_exact["expected_behavior"],
        "selector_tags": local_exact["selector_tags"],
        "selected_feature_tags": local_exact["selector_tags"],
        "selected_matched_selector_tags": local_exact["selector_tags"],
        "selected_missing_selector_tags": "",
        "case_reuse_count": "1",
        "exactness_audit_state": "covered_by_local_exact_compile_parser",
        "coverage_credit": "local_exact_compile_parser_requirement_credit",
        "next_action": "none_covered_by_local_exact_compile_parser",
        "audit_reason": (
            "local exact compile/parser case is selector-complete, unique for "
            "the requirement row, linked to the ECMA-262 source clause, and "
            "covered by the executable local exact gate"
        ),
    }


def selected_audit_row(
    row: dict[str, str],
    reuse_counts: Counter[str],
) -> dict[str, str]:
    state, credit, reason = exactness_for_selected(row, reuse_counts)
    return {
        "audit_id": f"exactness:{row['requirement_id']}:{row['selected_case_id']}",
        "audit_scope": "ecma262_requirement",
        "requirement_id": row["requirement_id"],
        "mapping_family": row["mapping_family"],
        "executable_layer": row["executable_layer"],
        "evidence_kind": "selected_compile_positive_case",
        "case_id": row["selected_case_id"],
        "case_source": row["selected_case_source"],
        "expected_behavior": row["selected_expected_behavior"],
        "selector_tags": row["candidate_selector_tags"],
        "selected_feature_tags": row["selected_feature_tags"],
        "selected_matched_selector_tags": row["selected_matched_selector_tags"],
        "selected_missing_selector_tags": row["selected_missing_selector_tags"],
        "case_reuse_count": str(reuse_counts[row["selected_case_id"]]),
        "exactness_audit_state": state,
        "coverage_credit": credit,
        "next_action": next_action_for_state(state),
        "audit_reason": reason,
    }


def open_selection_audit_row(row: dict[str, str]) -> dict[str, str]:
    return {
        "audit_id": f"exactness:{row['requirement_id']}:open-negative-or-local",
        "audit_scope": "ecma262_requirement",
        "requirement_id": row["requirement_id"],
        "mapping_family": row["mapping_family"],
        "executable_layer": row["executable_layer"],
        "evidence_kind": "open_negative_or_local_exact_mapping",
        "case_id": "",
        "case_source": "",
        "expected_behavior": row["selected_expected_behavior"],
        "selector_tags": row["candidate_selector_tags"],
        "selected_feature_tags": "",
        "selected_matched_selector_tags": "",
        "selected_missing_selector_tags": row["candidate_selector_tags"],
        "case_reuse_count": "0",
        "exactness_audit_state": "open_no_case_negative_or_local_exact",
        "coverage_credit": "none_no_executable_case",
        "next_action": "select_negative_syntax_or_local_exact_case",
        "audit_reason": "requirement row has no concrete executable case selected yet",
    }


def negative_corpus_audit_row(row: dict[str, str]) -> dict[str, str]:
    case_id = f"test262-negative:{row['source_path']}:{row['line']}"
    return {
        "audit_id": f"exactness:{case_id}",
        "audit_scope": "test262_negative_syntax_corpus",
        "requirement_id": "",
        "mapping_family": "compile_literal_validity",
        "executable_layer": "compile",
        "evidence_kind": "unmapped_negative_syntax_case",
        "case_id": case_id,
        "case_source": f"{row['source_path']}:{row['line']}",
        "expected_behavior": row["expected_behavior"],
        "selector_tags": "negative_syntax_needed",
        "selected_feature_tags": "",
        "selected_matched_selector_tags": "",
        "selected_missing_selector_tags": "requirement_id",
        "case_reuse_count": "0",
        "exactness_audit_state": "open_unmapped_negative_syntax_case",
        "coverage_credit": "none_unmapped_corpus",
        "next_action": "map_negative_syntax_case_to_requirement",
        "audit_reason": "negative syntax case is executable, but it is not linked to an ECMA-262 requirement row",
    }


def next_action_for_state(state: str) -> str:
    if state == "covered_by_local_exact_compile_parser":
        return "none_covered_by_local_exact_compile_parser"
    if state == "open_missing_selector_coverage":
        return "add_selector_complete_case_or_local_exact_test"
    if state == "open_local_exact_executable_credit_pending":
        return "connect_local_exact_executable_evidence_to_requirement_credit"
    if state == "open_reused_candidate_needs_exact_proof":
        return "split_reused_candidate_or_add_local_exact_test"
    if state == "covered_by_reused_candidate_exact_compile_parser":
        return "none_covered_by_reused_candidate_exact_compile_parser"
    if state == "open_reused_candidate_manual_spec_review_required":
        return "manual_spec_exactness_review_before_credit"
    if state == "potential_exact_ready_manual_review":
        return "manual_spec_exactness_review_before_credit"
    raise SystemExit(f"missing next action for exactness state {state}")


def validate_reused_exact_against_selected(
    plan: dict[str, str],
    selected: dict[str, str] | None,
    reuse_counts: Counter[str],
) -> None:
    if selected is None:
        return

    requirement_id = plan["requirement_id"]
    selected_state, _, _ = exactness_for_selected(selected, reuse_counts)
    if selected_state != "open_reused_candidate_needs_exact_proof":
        raise SystemExit(
            f"reused exact plan row {requirement_id} applies to selected state "
            f"{selected_state!r}; expected 'open_reused_candidate_needs_exact_proof'"
        )
    for field in [
        "mapping_family",
        "executable_layer",
        "selected_case_id",
        "selected_case_source",
        "selected_pattern",
        "selected_flags",
    ]:
        selected_field = field
        if field == "selected_pattern":
            selected_field = "selected_pattern"
        if plan[field] != selected[selected_field]:
            raise SystemExit(
                f"reused exact plan row {requirement_id} has {field}={plan[field]!r}; "
                f"selection has {selected[selected_field]!r}"
            )
    set_pairs = [
        ("selector_tags", "candidate_selector_tags"),
        ("selected_feature_tags", "selected_feature_tags"),
    ]
    for plan_field, selected_field in set_pairs:
        if csv_set(plan[plan_field]) != csv_set(selected[selected_field]):
            raise SystemExit(
                f"reused exact plan row {requirement_id} has "
                f"{plan_field}={plan[plan_field]!r}; selection has "
                f"{selected[selected_field]!r}"
            )
    if selected["selected_missing_selector_tags"]:
        raise SystemExit(
            f"reused exact plan row {requirement_id} selection has missing "
            f"selector tags {selected['selected_missing_selector_tags']!r}"
        )
    if plan["source_file"] != selected["source_file"]:
        raise SystemExit(
            f"reused exact plan row {requirement_id} has source_file="
            f"{plan['source_file']!r}; selection has {selected['source_file']!r}"
        )
    if plan["section_anchor"] != selected["section_anchor"]:
        raise SystemExit(
            f"reused exact plan row {requirement_id} has section_anchor="
            f"{plan['section_anchor']!r}; selection has "
            f"{selected['section_anchor']!r}"
        )


def validate_reused_exact_plan_row(
    plan: dict[str, str],
    selected: dict[str, str] | None,
    reuse_counts: Counter[str],
) -> None:
    requirement_id = plan["requirement_id"]
    validate_reused_exact_against_selected(plan, selected, reuse_counts)
    if not Path(plan["source_file"]).is_file():
        raise SystemExit(
            f"reused exact plan row {requirement_id} source is missing: "
            f"{plan['source_file']}"
        )
    if plan["plan_state"] == "planned_not_executable":
        expected = {
            "expected_behavior": "compile_ok",
            "coverage_credit": "none_reused_candidate_exact_planned",
            "target_test_artifact": REUSED_EXACT_TARGET_TEST_ARTIFACT,
            "next_action": "materialize_reused_candidate_exact_case",
        }
        for field, expected_value in expected.items():
            if plan[field] != expected_value:
                raise SystemExit(
                    f"reused exact plan row {requirement_id} has "
                    f"{field}={plan[field]!r}; expected {expected_value!r}"
                )
        for field in [
            "exact_case_id",
            "planned_pattern",
            "implementation_pressure",
        ]:
            if not plan[field]:
                raise SystemExit(
                    f"reused exact plan row {requirement_id} has empty {field}"
                )
        if not plan["exact_case_id"].startswith(f"reused-exact:{requirement_id}:"):
            raise SystemExit(
                f"reused exact plan row {requirement_id} has invalid exact_case_id "
                f"{plan['exact_case_id']!r}"
            )
        if not Path(plan["target_test_artifact"]).is_file():
            raise SystemExit(
                f"reused exact plan row {requirement_id} target artifact is missing: "
                f"{plan['target_test_artifact']}"
            )
        return

    if plan["plan_state"] == "manual_spec_review_required":
        expected = {
            "exact_case_id": "",
            "planned_pattern": "",
            "planned_flags": "",
            "expected_behavior": "",
            "coverage_credit": "none_manual_review_required",
            "target_test_artifact": "",
            "implementation_pressure": "",
            "next_action": "manual_spec_review_before_exact_case",
        }
        for field, expected_value in expected.items():
            if plan[field] != expected_value:
                raise SystemExit(
                    f"manual reused exact plan row {requirement_id} has "
                    f"{field}={plan[field]!r}; expected {expected_value!r}"
                )
        return

    raise SystemExit(
        f"reused exact plan row {requirement_id} has unsupported plan_state "
        f"{plan['plan_state']!r}"
    )


def reused_exact_audit_row(
    plan: dict[str, str],
    selected: dict[str, str] | None,
    reuse_counts: Counter[str],
) -> dict[str, str]:
    validate_reused_exact_plan_row(plan, selected, reuse_counts)
    requirement_id = plan["requirement_id"]
    case_source = f"{plan['source_file']}#{plan['section_anchor']}"

    if plan["plan_state"] == "manual_spec_review_required":
        return {
            "audit_id": f"exactness:{requirement_id}:manual-reused-candidate-review",
            "audit_scope": "ecma262_requirement",
            "requirement_id": requirement_id,
            "mapping_family": plan["mapping_family"],
            "executable_layer": plan["executable_layer"],
            "evidence_kind": "open_reused_candidate_manual_spec_review",
            "case_id": "",
            "case_source": case_source,
            "expected_behavior": "",
            "selector_tags": plan["selector_tags"],
            "selected_feature_tags": plan["selected_feature_tags"],
            "selected_matched_selector_tags": plan["selector_tags"],
            "selected_missing_selector_tags": "",
            "case_reuse_count": "0",
            "exactness_audit_state": "open_reused_candidate_manual_spec_review_required",
            "coverage_credit": "none_manual_review_required",
            "next_action": "manual_spec_exactness_review_before_credit",
            "audit_reason": (
                "reused selected compile-positive case is selector-complete, "
                "but this requirement row needs manual spec review before an "
                "exact executable case can receive credit"
            ),
        }

    return {
        "audit_id": f"exactness:{requirement_id}:{plan['exact_case_id']}",
        "audit_scope": "ecma262_requirement",
        "requirement_id": requirement_id,
        "mapping_family": plan["mapping_family"],
        "executable_layer": plan["executable_layer"],
        "evidence_kind": "reused_candidate_exact_compile_parser_case",
        "case_id": plan["exact_case_id"],
        "case_source": case_source,
        "expected_behavior": plan["expected_behavior"],
        "selector_tags": plan["selector_tags"],
        "selected_feature_tags": plan["selector_tags"],
        "selected_matched_selector_tags": plan["selector_tags"],
        "selected_missing_selector_tags": "",
        "case_reuse_count": "1",
        "exactness_audit_state": "covered_by_reused_candidate_exact_compile_parser",
        "coverage_credit": "reused_candidate_exact_compile_parser_requirement_credit",
        "next_action": "none_covered_by_reused_candidate_exact_compile_parser",
        "audit_reason": (
            "reused-candidate exact compile/parser case is selector-complete, "
            "unique for the requirement row, linked to the ECMA-262 source "
            "clause, and covered by the executable reused-candidate exact gate"
        ),
    }


def validate_compile_parser_exact_plan_row(
    plan: dict[str, str],
) -> None:
    requirement_id = plan["requirement_id"]
    expected = {
        "coverage_credit": "none_compile_parser_exact_planned",
        "plan_state": "planned_not_executable",
        "target_test_artifact": COMPILE_PARSER_EXACT_TARGET_TEST_ARTIFACT,
        "next_action": "materialize_compile_parser_exact_case",
    }
    for field, expected_value in expected.items():
        if plan[field] != expected_value:
            raise SystemExit(
                f"compile/parser exact plan row {requirement_id} has "
                f"{field}={plan[field]!r}; expected {expected_value!r}"
            )
    if plan["expected_behavior"] not in {"compile_ok", "compile_error"}:
        raise SystemExit(
            f"compile/parser exact plan row {requirement_id} has unsupported "
            f"expected_behavior {plan['expected_behavior']!r}"
        )
    if plan["selection_state"] == "selected_compile_positive_case":
        if plan["expected_behavior"] != "compile_ok":
            raise SystemExit(
                f"compile/parser exact plan row {requirement_id} should be "
                "compile_ok for selected positive selection"
            )
    elif plan["selection_state"] == "needs_negative_or_local_exact_case":
        if plan["expected_behavior"] != "compile_error":
            raise SystemExit(
                f"compile/parser exact plan row {requirement_id} should be "
                "compile_error for negative/local exact selection"
            )
    else:
        raise SystemExit(
            f"compile/parser exact plan row {requirement_id} has unsupported "
            f"selection state {selected['selection_state']!r}"
        )
    for field in [
        "source_file",
        "section_anchor",
        "mapping_family",
        "executable_layer",
        "selection_state",
        "selector_tags",
        "exact_case_family",
        "exact_case_id",
        "planned_pattern",
        "exact_case_obligation",
    ]:
        if not plan[field]:
            raise SystemExit(
                f"compile/parser exact plan row {requirement_id} has empty {field}"
            )
    if not plan["exact_case_id"].startswith(
        f"compile-parser-exact:{requirement_id}:"
    ):
        raise SystemExit(
            f"compile/parser exact plan row {requirement_id} has invalid "
            f"exact_case_id {plan['exact_case_id']!r}"
        )
    if not Path(plan["source_file"]).is_file():
        raise SystemExit(
            f"compile/parser exact plan row {requirement_id} source is missing: "
            f"{plan['source_file']}"
        )
    if not Path(plan["target_test_artifact"]).is_file():
        raise SystemExit(
            f"compile/parser exact plan row {requirement_id} target artifact is "
            f"missing: {plan['target_test_artifact']}"
        )


def compile_parser_exact_audit_row(
    plan: dict[str, str],
) -> dict[str, str]:
    validate_compile_parser_exact_plan_row(plan)
    requirement_id = plan["requirement_id"]
    return {
        "audit_id": f"exactness:{requirement_id}:{plan['exact_case_id']}",
        "audit_scope": "ecma262_requirement",
        "requirement_id": requirement_id,
        "mapping_family": plan["mapping_family"],
        "executable_layer": plan["executable_layer"],
        "evidence_kind": "compile_parser_exact_case",
        "case_id": plan["exact_case_id"],
        "case_source": f"{plan['source_file']}#{plan['section_anchor']}",
        "expected_behavior": plan["expected_behavior"],
        "selector_tags": plan["selector_tags"],
        "selected_feature_tags": plan["selector_tags"],
        "selected_matched_selector_tags": plan["selector_tags"],
        "selected_missing_selector_tags": "",
        "case_reuse_count": "1",
        "exactness_audit_state": "covered_by_compile_parser_exact",
        "coverage_credit": "compile_parser_exact_requirement_credit",
        "next_action": "none_covered_by_compile_parser_exact",
        "audit_reason": (
            "post-credit compile/parser exact case is selector-complete, "
            "unique for the requirement row, linked to the ECMA-262 source "
            "clause, and covered by the executable compile/parser exact gate"
        ),
    }


def validate_literal_lexer_exact_plan_row(plan: dict[str, str]) -> None:
    requirement_id = plan["requirement_id"]
    expected = {
        "mapping_family": "literal_lexer_exact",
        "executable_layer": "literal_lexer",
        "expected_behavior": "literal_parse_ok",
        "coverage_credit": "none_literal_lexer_exact_planned",
        "plan_state": "planned_not_executable",
        "target_test_artifact": LITERAL_LEXER_EXACT_TARGET_TEST_ARTIFACT,
        "next_action": "materialize_literal_lexer_exact_case",
    }
    for field, expected_value in expected.items():
        if plan[field] != expected_value:
            raise SystemExit(
                f"literal lexer exact plan row {requirement_id} has "
                f"{field}={plan[field]!r}; expected {expected_value!r}"
            )
    for field in [
        "source_file",
        "section_anchor",
        "exact_case_family",
        "exact_case_id",
        "literal_source",
        "expected_flag_text",
        "exact_case_obligation",
    ]:
        if not plan[field]:
            raise SystemExit(
                f"literal lexer exact plan row {requirement_id} has empty {field}"
            )
    if not plan["exact_case_id"].startswith(
        f"literal-lexer-exact:{requirement_id}:"
    ):
        raise SystemExit(
            f"literal lexer exact plan row {requirement_id} has invalid "
            f"exact_case_id {plan['exact_case_id']!r}"
        )
    if not Path(plan["source_file"]).is_file():
        raise SystemExit(
            f"literal lexer exact plan row {requirement_id} source is missing: "
            f"{plan['source_file']}"
        )
    if not Path(plan["target_test_artifact"]).is_file():
        raise SystemExit(
            f"literal lexer exact plan row {requirement_id} target artifact is "
            f"missing: {plan['target_test_artifact']}"
        )


def literal_lexer_exact_audit_row(
    plan: dict[str, str],
) -> dict[str, str]:
    validate_literal_lexer_exact_plan_row(plan)
    requirement_id = plan["requirement_id"]
    selector_tags = "regexp_flags,regexp_literal_lexical_grammar"
    return {
        "audit_id": f"exactness:{requirement_id}:{plan['exact_case_id']}",
        "audit_scope": "ecma262_requirement",
        "requirement_id": requirement_id,
        "mapping_family": plan["mapping_family"],
        "executable_layer": plan["executable_layer"],
        "evidence_kind": "literal_lexer_exact_case",
        "case_id": plan["exact_case_id"],
        "case_source": f"{plan['source_file']}#{plan['section_anchor']}",
        "expected_behavior": plan["expected_behavior"],
        "selector_tags": selector_tags,
        "selected_feature_tags": selector_tags,
        "selected_matched_selector_tags": selector_tags,
        "selected_missing_selector_tags": "",
        "case_reuse_count": "1",
        "exactness_audit_state": "covered_by_literal_lexer_exact",
        "coverage_credit": "literal_lexer_exact_requirement_credit",
        "next_action": "none_covered_by_literal_lexer_exact",
        "audit_reason": (
            "literal lexer exact case is selector-complete, unique for the "
            "requirement row, linked to the ECMA-262 FlagText source clause, "
            "and covered by the executable literal lexer exact gate"
        ),
    }


def match_engine_exact_plan_is_creditable(plan: dict[str, str]) -> bool:
    return (
        plan["plan_state"] == "planned_not_executable"
        and plan["coverage_credit"] == "none_match_engine_exact_planned"
    )


def validate_match_engine_exact_plan_row(plan: dict[str, str]) -> None:
    requirement_id = plan["requirement_id"]
    if plan["executable_layer"] != "match_engine":
        raise SystemExit(
            f"match-engine exact plan row {requirement_id} has "
            f"executable_layer={plan['executable_layer']!r}"
        )
    if plan["mapping_family"] not in {
        "match_engine_atoms",
        "match_engine_concatenation",
        "match_engine_alternation",
    }:
        raise SystemExit(
            f"match-engine exact plan row {requirement_id} has "
            f"mapping_family={plan['mapping_family']!r}"
        )
    for field in [
        "source_file",
        "section_anchor",
        "exact_case_family",
        "exact_case_id",
        "exact_case_obligation",
        "observability_status",
        "observability_reason",
    ]:
        if not plan[field]:
            raise SystemExit(
                f"match-engine exact plan row {requirement_id} has empty {field}"
            )
    if not Path(plan["source_file"]).is_file():
        raise SystemExit(
            f"match-engine exact plan row {requirement_id} source is missing: "
            f"{plan['source_file']}"
        )
    if match_engine_exact_plan_is_creditable(plan):
        expected = {
            "target_test_artifact": MATCH_ENGINE_EXACT_TARGET_TEST_ARTIFACT,
            "next_action": "materialize_match_engine_exact_case",
            "observability_status": "search_bool_observable",
        }
        for field, expected_value in expected.items():
            if plan[field] != expected_value:
                raise SystemExit(
                    f"match-engine exact plan row {requirement_id} has "
                    f"{field}={plan[field]!r}; expected {expected_value!r}"
                )
        if plan["expected_behavior"] not in {"search_true", "search_false"}:
            raise SystemExit(
                f"match-engine exact plan row {requirement_id} has "
                f"expected_behavior={plan['expected_behavior']!r}"
            )
        if plan["expected_search_result"] not in {"true", "false"}:
            raise SystemExit(
                f"match-engine exact plan row {requirement_id} has "
                f"expected_search_result={plan['expected_search_result']!r}"
            )
        for field in ["pattern", "input_text"]:
            if not plan[field]:
                raise SystemExit(
                    f"match-engine exact plan row {requirement_id} has empty {field}"
                )
        if not plan["exact_case_id"].startswith(
            f"match-engine-exact:{requirement_id}:"
        ):
            raise SystemExit(
                f"match-engine exact plan row {requirement_id} has invalid "
                f"exact_case_id {plan['exact_case_id']!r}"
            )
        if not Path(plan["target_test_artifact"]).is_file():
            raise SystemExit(
                f"match-engine exact plan row {requirement_id} target artifact is "
                f"missing: {plan['target_test_artifact']}"
            )
    elif plan["coverage_credit"] == "none_match_engine_exact_deferred":
        if plan["plan_state"] not in {
            "deferred_requires_exec_result_observer",
            "deferred_requires_match_state_model",
        }:
            raise SystemExit(
                f"match-engine exact plan row {requirement_id} has "
                f"plan_state={plan['plan_state']!r}"
            )
        if plan["expected_behavior"] not in {
            "requires_exec_result_observer",
            "requires_match_state_model",
        }:
            raise SystemExit(
                f"match-engine exact plan row {requirement_id} has "
                f"expected_behavior={plan['expected_behavior']!r}"
            )
        if plan["expected_search_result"] != "not_observable":
            raise SystemExit(
                f"match-engine exact plan row {requirement_id} has "
                f"expected_search_result={plan['expected_search_result']!r}"
            )
        if plan["pattern"] or plan["input_text"] or plan["target_test_artifact"]:
            raise SystemExit(
                f"match-engine exact deferred row {requirement_id} must not "
                "declare executable pattern, input, or target artifact"
            )
        if not plan["next_action"].startswith("design_"):
            raise SystemExit(
                f"match-engine exact deferred row {requirement_id} has "
                f"next_action={plan['next_action']!r}"
            )
        if not plan["exact_case_id"].startswith(
            f"match-engine-deferred:{requirement_id}:"
        ):
            raise SystemExit(
                f"match-engine exact deferred row {requirement_id} has invalid "
                f"exact_case_id {plan['exact_case_id']!r}"
            )
    else:
        raise SystemExit(
            f"match-engine exact plan row {requirement_id} has unsupported "
            f"coverage_credit={plan['coverage_credit']!r} and "
            f"plan_state={plan['plan_state']!r}"
        )


def match_engine_exact_audit_row(
    plan: dict[str, str],
) -> dict[str, str]:
    validate_match_engine_exact_plan_row(plan)
    if not match_engine_exact_plan_is_creditable(plan):
        raise SystemExit(
            f"match-engine exact plan row {plan['requirement_id']} is not creditable"
        )
    requirement_id = plan["requirement_id"]
    selector_tags = "regexp_exec_and_captures,regexp_runtime_search"
    return {
        "audit_id": f"exactness:{requirement_id}:{plan['exact_case_id']}",
        "audit_scope": "ecma262_requirement",
        "requirement_id": requirement_id,
        "mapping_family": plan["mapping_family"],
        "executable_layer": plan["executable_layer"],
        "evidence_kind": "match_engine_exact_case",
        "case_id": plan["exact_case_id"],
        "case_source": f"{plan['source_file']}#{plan['section_anchor']}",
        "expected_behavior": plan["expected_behavior"],
        "selector_tags": selector_tags,
        "selected_feature_tags": selector_tags,
        "selected_matched_selector_tags": selector_tags,
        "selected_missing_selector_tags": "",
        "case_reuse_count": "1",
        "exactness_audit_state": "covered_by_match_engine_exact",
        "coverage_credit": "match_engine_exact_requirement_credit",
        "next_action": "none_covered_by_match_engine_exact",
        "audit_reason": (
            "match-engine exact case is selector-complete, unique for the "
            "requirement row, linked to the ECMA-262 runtime source clause, "
            "and covered by the executable match-engine exact gate"
        ),
    }


def match_engine_start_anchor_exact_plan_is_creditable(plan: dict[str, str]) -> bool:
    return (
        plan["plan_state"] == "planned_not_executable"
        and plan["coverage_credit"] == "none_match_engine_start_anchor_exact_planned"
    )


def validate_match_engine_start_anchor_exact_plan_row(plan: dict[str, str]) -> None:
    requirement_id = plan["requirement_id"]
    if plan["executable_layer"] != "match_engine":
        raise SystemExit(
            f"match-engine start-anchor exact plan row {requirement_id} has "
            f"executable_layer={plan['executable_layer']!r}"
        )
    if plan["mapping_family"] != "match_engine_assertions":
        raise SystemExit(
            f"match-engine start-anchor exact plan row {requirement_id} has "
            f"mapping_family={plan['mapping_family']!r}"
        )
    for field in [
        "source_file",
        "section_anchor",
        "exact_case_family",
        "exact_case_id",
        "pattern",
        "input_text",
        "expected_search_result",
        "expected_exec_result",
        "expected_behavior",
        "exact_case_obligation",
        "observability_status",
        "observability_reason",
    ]:
        if not plan[field]:
            raise SystemExit(
                f"match-engine start-anchor exact plan row {requirement_id} "
                f"has empty {field}"
            )
    if not Path(plan["source_file"]).is_file():
        raise SystemExit(
            f"match-engine start-anchor exact plan row {requirement_id} source "
            f"is missing: {plan['source_file']}"
        )
    if not match_engine_start_anchor_exact_plan_is_creditable(plan):
        raise SystemExit(
            f"match-engine start-anchor exact plan row {requirement_id} has "
            f"unsupported coverage_credit={plan['coverage_credit']!r} and "
            f"plan_state={plan['plan_state']!r}"
        )
    expected = {
        "target_test_artifact": MATCH_ENGINE_START_ANCHOR_EXACT_TARGET_TEST_ARTIFACT,
        "next_action": "materialize_match_engine_start_anchor_exact_case",
        "observability_status": "search_and_exec_observable",
    }
    for field, expected_value in expected.items():
        if plan[field] != expected_value:
            raise SystemExit(
                f"match-engine start-anchor exact plan row {requirement_id} has "
                f"{field}={plan[field]!r}; expected {expected_value!r}"
            )
    if plan["expected_search_result"] not in {"true", "false"}:
        raise SystemExit(
            f"match-engine start-anchor exact plan row {requirement_id} has "
            f"expected_search_result={plan['expected_search_result']!r}"
        )
    if plan["expected_exec_result"] not in {"true", "false"}:
        raise SystemExit(
            f"match-engine start-anchor exact plan row {requirement_id} has "
            f"expected_exec_result={plan['expected_exec_result']!r}"
        )
    if plan["expected_exec_result"] == "true":
        for field in ["expected_start_index", "expected_end_index"]:
            if not plan[field]:
                raise SystemExit(
                    f"match-engine start-anchor exact plan row {requirement_id} "
                    f"has empty {field}"
                )
    else:
        for field in ["expected_start_index", "expected_end_index", "expected_match_text"]:
            if plan[field]:
                raise SystemExit(
                    f"match-engine start-anchor exact negative row {requirement_id} "
                    f"has non-empty {field}"
                )
    if not plan["exact_case_id"].startswith(
        f"match-engine-start-anchor-exact:{requirement_id}:"
    ):
        raise SystemExit(
            f"match-engine start-anchor exact plan row {requirement_id} has "
            f"invalid exact_case_id {plan['exact_case_id']!r}"
        )
    if not Path(plan["target_test_artifact"]).is_file():
        raise SystemExit(
            f"match-engine start-anchor exact plan row {requirement_id} target "
            f"artifact is missing: {plan['target_test_artifact']}"
        )


def match_engine_start_anchor_exact_audit_row(
    plans: list[dict[str, str]],
) -> dict[str, str]:
    if not plans:
        raise SystemExit("empty match-engine start-anchor exact plan group")
    for plan in plans:
        validate_match_engine_start_anchor_exact_plan_row(plan)
    requirement_ids = {plan["requirement_id"] for plan in plans}
    if len(requirement_ids) != 1:
        raise SystemExit(
            "match-engine start-anchor exact plan group spans multiple "
            f"requirements: {', '.join(sorted(requirement_ids))}"
        )
    requirement_id = plans[0]["requirement_id"]
    representative = sorted(plans, key=lambda row: row["exact_case_id"])[0]
    selector_tags = (
        "regexp_exec_and_captures,regexp_runtime_search,"
        "regexp_match_engine_assertions"
    )
    return {
        "audit_id": (
            f"exactness:{requirement_id}:{representative['exact_case_id']}"
        ),
        "audit_scope": "ecma262_requirement",
        "requirement_id": requirement_id,
        "mapping_family": representative["mapping_family"],
        "executable_layer": representative["executable_layer"],
        "evidence_kind": "match_engine_start_anchor_exact_case",
        "case_id": representative["exact_case_id"],
        "case_source": (
            f"{representative['source_file']}#{representative['section_anchor']}"
        ),
        "expected_behavior": "start_anchor_exact_plan_observable",
        "selector_tags": selector_tags,
        "selected_feature_tags": selector_tags,
        "selected_matched_selector_tags": selector_tags,
        "selected_missing_selector_tags": "",
        "case_reuse_count": "1",
        "exactness_audit_state": "covered_by_match_engine_exact",
        "coverage_credit": "match_engine_exact_requirement_credit",
        "next_action": "none_covered_by_match_engine_exact",
        "audit_reason": (
            "all start-anchor exact plan rows for this requirement are linked "
            "to ECMA-262 CompileAssertion source text and covered by the "
            "executable search/exec start-anchor gate"
        ),
    }


def match_engine_end_anchor_exact_plan_is_creditable(plan: dict[str, str]) -> bool:
    return (
        plan["plan_state"] == "planned_not_executable"
        and plan["coverage_credit"] == "none_match_engine_end_anchor_exact_planned"
    )


def validate_match_engine_end_anchor_exact_plan_row(plan: dict[str, str]) -> None:
    requirement_id = plan["requirement_id"]
    if plan["executable_layer"] != "match_engine":
        raise SystemExit(
            f"match-engine end-anchor exact plan row {requirement_id} has "
            f"executable_layer={plan['executable_layer']!r}"
        )
    if plan["mapping_family"] != "match_engine_assertions":
        raise SystemExit(
            f"match-engine end-anchor exact plan row {requirement_id} has "
            f"mapping_family={plan['mapping_family']!r}"
        )
    for field in [
        "source_file",
        "section_anchor",
        "exact_case_family",
        "exact_case_id",
        "pattern",
        "input_text",
        "expected_search_result",
        "expected_exec_result",
        "expected_behavior",
        "exact_case_obligation",
        "observability_status",
        "observability_reason",
    ]:
        if not plan[field]:
            raise SystemExit(
                f"match-engine end-anchor exact plan row {requirement_id} "
                f"has empty {field}"
            )
    if not Path(plan["source_file"]).is_file():
        raise SystemExit(
            f"match-engine end-anchor exact plan row {requirement_id} source "
            f"is missing: {plan['source_file']}"
        )
    if not match_engine_end_anchor_exact_plan_is_creditable(plan):
        raise SystemExit(
            f"match-engine end-anchor exact plan row {requirement_id} has "
            f"unsupported coverage_credit={plan['coverage_credit']!r} and "
            f"plan_state={plan['plan_state']!r}"
        )
    expected = {
        "target_test_artifact": MATCH_ENGINE_END_ANCHOR_EXACT_TARGET_TEST_ARTIFACT,
        "next_action": "materialize_match_engine_end_anchor_exact_case",
        "observability_status": "search_and_exec_observable",
    }
    for field, expected_value in expected.items():
        if plan[field] != expected_value:
            raise SystemExit(
                f"match-engine end-anchor exact plan row {requirement_id} has "
                f"{field}={plan[field]!r}; expected {expected_value!r}"
            )
    if plan["expected_search_result"] not in {"true", "false"}:
        raise SystemExit(
            f"match-engine end-anchor exact plan row {requirement_id} has "
            f"expected_search_result={plan['expected_search_result']!r}"
        )
    if plan["expected_exec_result"] not in {"true", "false"}:
        raise SystemExit(
            f"match-engine end-anchor exact plan row {requirement_id} has "
            f"expected_exec_result={plan['expected_exec_result']!r}"
        )
    if plan["expected_exec_result"] == "true":
        for field in ["expected_start_index", "expected_end_index"]:
            if not plan[field]:
                raise SystemExit(
                    f"match-engine end-anchor exact plan row {requirement_id} "
                    f"has empty {field}"
                )
    else:
        for field in ["expected_start_index", "expected_end_index", "expected_match_text"]:
            if plan[field]:
                raise SystemExit(
                    f"match-engine end-anchor exact negative row {requirement_id} "
                    f"has non-empty {field}"
                )
    if not plan["exact_case_id"].startswith(
        f"match-engine-end-anchor-exact:{requirement_id}:"
    ):
        raise SystemExit(
            f"match-engine end-anchor exact plan row {requirement_id} has "
            f"invalid exact_case_id {plan['exact_case_id']!r}"
        )
    if not Path(plan["target_test_artifact"]).is_file():
        raise SystemExit(
            f"match-engine end-anchor exact plan row {requirement_id} target "
            f"artifact is missing: {plan['target_test_artifact']}"
        )


def match_engine_end_anchor_exact_audit_row(
    plans: list[dict[str, str]],
) -> dict[str, str]:
    if not plans:
        raise SystemExit("empty match-engine end-anchor exact plan group")
    for plan in plans:
        validate_match_engine_end_anchor_exact_plan_row(plan)
    requirement_ids = {plan["requirement_id"] for plan in plans}
    if len(requirement_ids) != 1:
        raise SystemExit(
            "match-engine end-anchor exact plan group spans multiple "
            f"requirements: {', '.join(sorted(requirement_ids))}"
        )
    requirement_id = plans[0]["requirement_id"]
    representative = sorted(plans, key=lambda row: row["exact_case_id"])[0]
    selector_tags = (
        "regexp_exec_and_captures,regexp_runtime_search,"
        "regexp_match_engine_assertions"
    )
    return {
        "audit_id": (
            f"exactness:{requirement_id}:{representative['exact_case_id']}"
        ),
        "audit_scope": "ecma262_requirement",
        "requirement_id": requirement_id,
        "mapping_family": representative["mapping_family"],
        "executable_layer": representative["executable_layer"],
        "evidence_kind": "match_engine_end_anchor_exact_case",
        "case_id": representative["exact_case_id"],
        "case_source": (
            f"{representative['source_file']}#{representative['section_anchor']}"
        ),
        "expected_behavior": "end_anchor_exact_plan_observable",
        "selector_tags": selector_tags,
        "selected_feature_tags": selector_tags,
        "selected_matched_selector_tags": selector_tags,
        "selected_missing_selector_tags": "",
        "case_reuse_count": "1",
        "exactness_audit_state": "covered_by_match_engine_exact",
        "coverage_credit": "match_engine_exact_requirement_credit",
        "next_action": "none_covered_by_match_engine_exact",
        "audit_reason": (
            "all end-anchor exact plan rows for this requirement are linked "
            "to ECMA-262 CompileAssertion source text and covered by the "
            "executable search/exec end-anchor gate"
        ),
    }


def match_engine_quantifier_exact_plan_is_creditable(plan: dict[str, str]) -> bool:
    return (
        plan["plan_state"] == "planned_not_executable"
        and plan["coverage_credit"] == "none_match_engine_quantifier_exact_planned"
    )


def validate_match_engine_quantifier_exact_plan_row(plan: dict[str, str]) -> None:
    requirement_id = plan["requirement_id"]
    expected = {
        "mapping_family": "match_engine_quantifiers",
        "executable_layer": "match_engine",
        "coverage_credit": "none_match_engine_quantifier_exact_planned",
        "plan_state": "planned_not_executable",
        "target_test_artifact": MATCH_ENGINE_QUANTIFIER_EXACT_TARGET_TEST_ARTIFACT,
        "observability_status": "search_and_exec_observable",
        "next_action": "materialize_match_engine_quantifier_exact_case",
    }
    for field, expected_value in expected.items():
        if plan[field] != expected_value:
            raise SystemExit(
                f"match-engine quantifier exact plan row {requirement_id} has "
                f"{field}={plan[field]!r}; expected {expected_value!r}"
            )
    for field in [
        "source_file",
        "section_anchor",
        "exact_case_family",
        "exact_case_id",
        "pattern",
        "expected_search_result",
        "expected_exec_result",
        "expected_behavior",
        "exact_case_obligation",
        "observability_reason",
    ]:
        if not plan[field]:
            raise SystemExit(
                f"match-engine quantifier exact plan row {requirement_id} "
                f"has empty {field}"
            )
    if plan["expected_search_result"] not in {"true", "false"}:
        raise SystemExit(
            f"match-engine quantifier exact plan row {requirement_id} has "
            f"expected_search_result={plan['expected_search_result']!r}"
        )
    if plan["expected_exec_result"] not in {"true", "false"}:
        raise SystemExit(
            f"match-engine quantifier exact plan row {requirement_id} has "
            f"expected_exec_result={plan['expected_exec_result']!r}"
        )
    if plan["expected_exec_result"] == "true":
        for field in ["expected_start_index", "expected_end_index"]:
            if not plan[field]:
                raise SystemExit(
                    f"match-engine quantifier exact plan row {requirement_id} "
                    f"has empty {field}"
                )
    else:
        for field in ["expected_start_index", "expected_end_index", "expected_match_text"]:
            if plan[field]:
                raise SystemExit(
                    f"match-engine quantifier exact negative row {requirement_id} "
                    f"has non-empty {field}"
                )
    if not plan["exact_case_id"].startswith(
        f"match-engine-quantifier-exact:{requirement_id}:"
    ):
        raise SystemExit(
            f"match-engine quantifier exact plan row {requirement_id} has "
            f"invalid exact_case_id {plan['exact_case_id']!r}"
        )
    if not Path(plan["source_file"]).is_file():
        raise SystemExit(
            f"match-engine quantifier exact plan row {requirement_id} source "
            f"is missing: {plan['source_file']}"
        )
    if not Path(plan["target_test_artifact"]).is_file():
        raise SystemExit(
            f"match-engine quantifier exact plan row {requirement_id} target "
            f"artifact is missing: {plan['target_test_artifact']}"
        )
    if not match_engine_quantifier_exact_plan_is_creditable(plan):
        raise SystemExit(
            f"match-engine quantifier exact plan row {requirement_id} has "
            f"unsupported coverage_credit={plan['coverage_credit']!r} and "
            f"plan_state={plan['plan_state']!r}"
        )


def match_engine_quantifier_exact_audit_row(
    plan: dict[str, str],
) -> dict[str, str]:
    validate_match_engine_quantifier_exact_plan_row(plan)
    requirement_id = plan["requirement_id"]
    selector_tags = (
        "regexp_exec_and_captures,regexp_runtime_search,"
        "regexp_match_engine_quantifiers"
    )
    return {
        "audit_id": f"exactness:{requirement_id}:{plan['exact_case_id']}",
        "audit_scope": "ecma262_requirement",
        "requirement_id": requirement_id,
        "mapping_family": plan["mapping_family"],
        "executable_layer": plan["executable_layer"],
        "evidence_kind": "match_engine_quantifier_exact_case",
        "case_id": plan["exact_case_id"],
        "case_source": f"{plan['source_file']}#{plan['section_anchor']}",
        "expected_behavior": "quantifier_exact_plan_observable",
        "selector_tags": selector_tags,
        "selected_feature_tags": selector_tags,
        "selected_matched_selector_tags": selector_tags,
        "selected_missing_selector_tags": "",
        "case_reuse_count": "1",
        "exactness_audit_state": "covered_by_match_engine_exact",
        "coverage_credit": "match_engine_exact_requirement_credit",
        "next_action": "none_covered_by_match_engine_exact",
        "audit_reason": (
            "match-engine quantifier exact case is linked to ECMA-262 "
            "RepeatMatcher/CompileQuantifier source text and covered by the "
            "executable search/exec quantifier gate"
        ),
    }


def match_engine_modifier_exact_plan_is_creditable(plan: dict[str, str]) -> bool:
    return (
        plan["plan_state"] == "planned_not_executable"
        and plan["coverage_credit"] == "none_match_engine_modifier_exact_planned"
    )


def validate_match_engine_modifier_exact_plan_row(plan: dict[str, str]) -> None:
    requirement_id = plan["requirement_id"]
    expected = {
        "mapping_family": "match_engine_atoms",
        "executable_layer": "match_engine",
        "modifier_subfamily": "modifiers_group_atom",
        "modifier_semantic_route": "scoped_modifier_runtime_model",
        "coverage_credit": "none_match_engine_modifier_exact_planned",
        "plan_state": "planned_not_executable",
        "target_test_artifact": MATCH_ENGINE_MODIFIER_EXACT_TARGET_TEST_ARTIFACT,
        "observability_status": "search_and_exec_observable",
        "next_action": "materialize_match_engine_modifier_exact_case",
    }
    for field, expected_value in expected.items():
        if plan[field] != expected_value:
            raise SystemExit(
                f"match-engine modifier exact plan row {requirement_id} has "
                f"{field}={plan[field]!r}; expected {expected_value!r}"
            )
    for field in [
        "source_atom_plan_id",
        "source_file",
        "section_anchor",
        "exact_case_family",
        "exact_case_id",
        "pattern",
        "expected_search_result",
        "expected_exec_result",
        "expected_behavior",
        "exact_case_obligation",
        "observability_reason",
    ]:
        if not plan[field]:
            raise SystemExit(
                f"match-engine modifier exact plan row {requirement_id} "
                f"has empty {field}"
            )
    if plan["expected_search_result"] not in {"true", "false"}:
        raise SystemExit(
            f"match-engine modifier exact plan row {requirement_id} has "
            f"expected_search_result={plan['expected_search_result']!r}"
        )
    if plan["expected_exec_result"] not in {"true", "false"}:
        raise SystemExit(
            f"match-engine modifier exact plan row {requirement_id} has "
            f"expected_exec_result={plan['expected_exec_result']!r}"
        )
    if plan["expected_exec_result"] == "true":
        for field in ["expected_start_index", "expected_end_index"]:
            if not plan[field]:
                raise SystemExit(
                    f"match-engine modifier exact plan row {requirement_id} "
                    f"has empty {field}"
                )
    else:
        for field in ["expected_start_index", "expected_end_index", "expected_match_text"]:
            if plan[field]:
                raise SystemExit(
                    f"match-engine modifier exact negative row {requirement_id} "
                    f"has non-empty {field}"
                )
    if not plan["exact_case_id"].startswith(
        f"match-engine-modifier-exact:{requirement_id}:"
    ):
        raise SystemExit(
            f"match-engine modifier exact plan row {requirement_id} has "
            f"invalid exact_case_id {plan['exact_case_id']!r}"
        )
    if not Path(plan["source_file"]).is_file():
        raise SystemExit(
            f"match-engine modifier exact plan row {requirement_id} source "
            f"is missing: {plan['source_file']}"
        )
    if not Path(plan["target_test_artifact"]).is_file():
        raise SystemExit(
            f"match-engine modifier exact plan row {requirement_id} target "
            f"artifact is missing: {plan['target_test_artifact']}"
        )
    if not match_engine_modifier_exact_plan_is_creditable(plan):
        raise SystemExit(
            f"match-engine modifier exact plan row {requirement_id} has "
            f"unsupported coverage_credit={plan['coverage_credit']!r} and "
            f"plan_state={plan['plan_state']!r}"
        )


def match_engine_modifier_exact_audit_row(
    plan: dict[str, str],
) -> dict[str, str]:
    validate_match_engine_modifier_exact_plan_row(plan)
    requirement_id = plan["requirement_id"]
    selector_tags = (
        "regexp_exec_and_captures,regexp_compile_atom,"
        "regexp_match_engine_modifiers"
    )
    return {
        "audit_id": f"exactness:{requirement_id}:{plan['exact_case_id']}",
        "audit_scope": "ecma262_requirement",
        "requirement_id": requirement_id,
        "mapping_family": plan["mapping_family"],
        "executable_layer": plan["executable_layer"],
        "evidence_kind": "match_engine_modifier_exact_case",
        "case_id": plan["exact_case_id"],
        "case_source": f"{plan['source_file']}#{plan['section_anchor']}",
        "expected_behavior": "modifier_exact_plan_observable",
        "selector_tags": selector_tags,
        "selected_feature_tags": selector_tags,
        "selected_matched_selector_tags": selector_tags,
        "selected_missing_selector_tags": "",
        "case_reuse_count": "1",
        "exactness_audit_state": "covered_by_match_engine_exact",
        "coverage_credit": "match_engine_exact_requirement_credit",
        "next_action": "none_covered_by_match_engine_exact",
        "audit_reason": (
            "match-engine modifier exact case is linked to ECMA-262 "
            "CompileAtom scoped modifier source text and covered by the "
            "executable search/exec modifier gate"
        ),
    }


def match_engine_pattern_semantics_exact_plan_is_creditable(
    plan: dict[str, str],
) -> bool:
    return (
        plan["plan_state"] == "planned_not_executable"
        and plan["coverage_credit"]
        == "none_match_engine_pattern_semantics_exact_planned"
    )


def validate_match_engine_pattern_semantics_exact_plan_row(
    plan: dict[str, str],
) -> None:
    requirement_id = plan["requirement_id"]
    expected = {
        "mapping_family": "match_engine_pattern_semantics",
        "executable_layer": "match_engine",
    }
    for field, expected_value in expected.items():
        if plan[field] != expected_value:
            raise SystemExit(
                f"match-engine Pattern Semantics exact plan row {requirement_id} "
                f"has {field}={plan[field]!r}; expected {expected_value!r}"
            )
    for field in [
        "source_file",
        "section_anchor",
        "pattern_semantics_subfamily",
        "pattern_semantics_route",
        "exact_case_id",
        "expected_behavior",
        "exact_case_obligation",
        "observability_status",
        "observability_reason",
    ]:
        if not plan[field]:
            raise SystemExit(
                f"match-engine Pattern Semantics exact plan row {requirement_id} "
                f"has empty {field}"
            )
    if not Path(plan["source_file"]).is_file():
        raise SystemExit(
            f"match-engine Pattern Semantics exact plan row {requirement_id} "
            f"source is missing: {plan['source_file']}"
        )
    if not plan["exact_case_id"].startswith(
        f"match-engine-pattern-semantics-exact:{requirement_id}:"
    ):
        raise SystemExit(
            f"match-engine Pattern Semantics exact plan row {requirement_id} "
            f"has invalid exact_case_id {plan['exact_case_id']!r}"
        )
    if match_engine_pattern_semantics_exact_plan_is_creditable(plan):
        expected_common = {
            "coverage_credit": "none_match_engine_pattern_semantics_exact_planned",
            "plan_state": "planned_not_executable",
            "target_test_artifact": (
                MATCH_ENGINE_PATTERN_SEMANTICS_EXACT_TARGET_TEST_ARTIFACT
            ),
            "next_action": "materialize_match_engine_pattern_semantics_exact_case",
        }
        for field, expected_value in expected_common.items():
            if plan[field] != expected_value:
                raise SystemExit(
                    f"match-engine Pattern Semantics exact plan row "
                    f"{requirement_id} has {field}={plan[field]!r}; "
                    f"expected {expected_value!r}"
                )
        if plan["observability_status"] == "search_and_exec_observable":
            expected_public = {
                "expected_search_result": "true",
                "expected_exec_result": "true",
                "expected_model_field": "",
                "model_scenario": "",
            }
            for field, expected_value in expected_public.items():
                if plan[field] != expected_value:
                    raise SystemExit(
                        f"match-engine Pattern Semantics exact plan row "
                        f"{requirement_id} has {field}={plan[field]!r}; "
                        f"expected {expected_value!r}"
                    )
            for field in ["expected_start_index", "expected_end_index"]:
                if not plan[field]:
                    raise SystemExit(
                        f"match-engine Pattern Semantics exact plan row "
                        f"{requirement_id} has empty {field}"
                    )
        elif (
            plan["observability_status"]
            == "internal_pattern_semantics_model_observable"
        ):
            expected_internal = {
                "expected_search_result": "not_applicable",
                "expected_exec_result": "not_applicable",
                "expected_start_index": "",
                "expected_end_index": "",
                "expected_match_text": "",
            }
            for field, expected_value in expected_internal.items():
                if plan[field] != expected_value:
                    raise SystemExit(
                        f"internal match-engine Pattern Semantics exact plan row "
                        f"{requirement_id} has {field}={plan[field]!r}; "
                        f"expected {expected_value!r}"
                    )
            for field in ["expected_model_field", "model_scenario"]:
                if not plan[field]:
                    raise SystemExit(
                        f"internal match-engine Pattern Semantics exact plan row "
                        f"{requirement_id} has empty {field}"
                    )
            if plan["expected_behavior"] != plan["expected_model_field"]:
                raise SystemExit(
                    f"internal match-engine Pattern Semantics exact plan row "
                    f"{requirement_id} has expected_behavior="
                    f"{plan['expected_behavior']!r}; expected "
                    f"{plan['expected_model_field']!r}"
                )
        else:
            raise SystemExit(
                f"match-engine Pattern Semantics exact plan row {requirement_id} "
                "has unsupported observability_status="
                f"{plan['observability_status']!r}"
            )
        if not Path(plan["target_test_artifact"]).is_file():
            raise SystemExit(
                f"match-engine Pattern Semantics exact plan row {requirement_id} "
                f"target artifact is missing: {plan['target_test_artifact']}"
            )
    else:
        expected_deferred = {
            "coverage_credit": "none_match_engine_pattern_semantics_exact_deferred",
            "expected_search_result": "not_observable",
            "expected_exec_result": "not_observable",
            "pattern": "",
            "flags": "",
            "input_text": "",
            "expected_start_index": "",
            "expected_end_index": "",
            "expected_match_text": "",
            "expected_model_field": "",
            "model_scenario": "",
            "target_test_artifact": "",
        }
        for field, expected_value in expected_deferred.items():
            if plan[field] != expected_value:
                raise SystemExit(
                    f"deferred match-engine Pattern Semantics exact plan row "
                    f"{requirement_id} has {field}={plan[field]!r}; "
                    f"expected {expected_value!r}"
                )
        if not plan["plan_state"].startswith("deferred_"):
            raise SystemExit(
                f"match-engine Pattern Semantics exact plan row {requirement_id} "
                f"has uncreditable non-deferred state {plan['plan_state']!r}"
            )


def match_engine_pattern_semantics_exact_audit_row(
    plan: dict[str, str],
) -> dict[str, str]:
    validate_match_engine_pattern_semantics_exact_plan_row(plan)
    if not match_engine_pattern_semantics_exact_plan_is_creditable(plan):
        raise SystemExit(
            "match-engine Pattern Semantics exact plan row "
            f"{plan['requirement_id']} is not creditable"
        )
    requirement_id = plan["requirement_id"]
    selector_tags = (
        "regexp_exec_and_captures,regexp_runtime_search,"
        "regexp_pattern_semantics"
    )
    return {
        "audit_id": f"exactness:{requirement_id}:{plan['exact_case_id']}",
        "audit_scope": "ecma262_requirement",
        "requirement_id": requirement_id,
        "mapping_family": plan["mapping_family"],
        "executable_layer": plan["executable_layer"],
        "evidence_kind": "match_engine_pattern_semantics_exact_case",
        "case_id": plan["exact_case_id"],
        "case_source": f"{plan['source_file']}#{plan['section_anchor']}",
        "expected_behavior": "pattern_semantics_exact_plan_observable",
        "selector_tags": selector_tags,
        "selected_feature_tags": selector_tags,
        "selected_matched_selector_tags": selector_tags,
        "selected_missing_selector_tags": "",
        "case_reuse_count": "1",
        "exactness_audit_state": "covered_by_match_engine_exact",
        "coverage_credit": "match_engine_exact_requirement_credit",
        "next_action": "none_covered_by_match_engine_exact",
        "audit_reason": (
            "match-engine Pattern Semantics exact case is linked to ECMA-262 "
            "Pattern/CompilePattern/CompileSubpattern source text and covered "
            "by the executable search/exec or internal model Pattern Semantics "
            "gate"
        ),
    }


def match_engine_annex_b_exact_plan_is_creditable(plan: dict[str, str]) -> bool:
    return (
        plan["plan_state"] == "planned_not_executable"
        and plan["coverage_credit"] == "none_match_engine_annex_b_exact_planned"
    )


def validate_match_engine_annex_b_exact_plan_row(plan: dict[str, str]) -> None:
    requirement_id = plan["requirement_id"]
    expected = {
        "mapping_family": "match_engine_annex_b_annexB",
        "executable_layer": "match_engine",
        "coverage_credit": "none_match_engine_annex_b_exact_planned",
        "plan_state": "planned_not_executable",
        "target_test_artifact": MATCH_ENGINE_ANNEX_B_EXACT_TARGET_TEST_ARTIFACT,
        "observability_status": "search_and_exec_observable",
        "next_action": "materialize_match_engine_annex_b_exact_case",
        "expected_search_result": "true",
        "expected_exec_result": "true",
    }
    for field, expected_value in expected.items():
        if plan[field] != expected_value:
            raise SystemExit(
                f"match-engine Annex B exact plan row {requirement_id} has "
                f"{field}={plan[field]!r}; expected {expected_value!r}"
            )
    for field in [
        "source_file",
        "section_anchor",
        "annex_b_subfamily",
        "annex_b_route",
        "exact_case_family",
        "exact_case_id",
        "pattern",
        "input_text",
        "expected_start_index",
        "expected_end_index",
        "expected_match_text",
        "expected_behavior",
        "exact_case_obligation",
        "observability_reason",
    ]:
        if not plan[field]:
            raise SystemExit(
                f"match-engine Annex B exact plan row {requirement_id} has "
                f"empty {field}"
            )
    if not Path(plan["source_file"]).is_file():
        raise SystemExit(
            f"match-engine Annex B exact plan row {requirement_id} source is "
            f"missing: {plan['source_file']}"
        )
    if not Path(plan["target_test_artifact"]).is_file():
        raise SystemExit(
            f"match-engine Annex B exact plan row {requirement_id} target "
            f"artifact is missing: {plan['target_test_artifact']}"
        )
    if not plan["exact_case_id"].startswith(
        f"match-engine-annex-b-exact:{requirement_id}:"
    ):
        raise SystemExit(
            f"match-engine Annex B exact plan row {requirement_id} has invalid "
            f"exact_case_id {plan['exact_case_id']!r}"
        )


def match_engine_annex_b_exact_audit_row(plan: dict[str, str]) -> dict[str, str]:
    validate_match_engine_annex_b_exact_plan_row(plan)
    if not match_engine_annex_b_exact_plan_is_creditable(plan):
        raise SystemExit(
            f"match-engine Annex B exact plan row {plan['requirement_id']} "
            "is not creditable"
        )
    requirement_id = plan["requirement_id"]
    selector_tags = "regexp_exec_and_captures,regexp_runtime_search,regexp_annex_b"
    return {
        "audit_id": f"exactness:{requirement_id}:{plan['exact_case_id']}",
        "audit_scope": "ecma262_requirement",
        "requirement_id": requirement_id,
        "mapping_family": plan["mapping_family"],
        "executable_layer": plan["executable_layer"],
        "evidence_kind": "match_engine_annex_b_exact_case",
        "case_id": plan["exact_case_id"],
        "case_source": f"{plan['source_file']}#{plan['section_anchor']}",
        "expected_behavior": "annex_b_exact_plan_observable",
        "selector_tags": selector_tags,
        "selected_feature_tags": selector_tags,
        "selected_matched_selector_tags": selector_tags,
        "selected_missing_selector_tags": "",
        "case_reuse_count": "1",
        "exactness_audit_state": "covered_by_match_engine_exact",
        "coverage_credit": "match_engine_exact_requirement_credit",
        "next_action": "none_covered_by_match_engine_exact",
        "audit_reason": (
            "match-engine Annex B exact case is linked to ECMA-262 Annex B "
            "BMP-pattern runtime source text and covered by the executable "
            "search/exec Annex B gate"
        ),
    }


def match_engine_assertion_exact_plan_is_creditable(plan: dict[str, str]) -> bool:
    return (
        plan["plan_state"] == "planned_not_executable"
        and plan["coverage_credit"] == "none_match_engine_assertion_exact_planned"
    )


def validate_match_engine_assertion_exact_plan_row(plan: dict[str, str]) -> None:
    requirement_id = plan["requirement_id"]
    expected = {
        "mapping_family": "match_engine_assertions",
        "executable_layer": "match_engine",
        "coverage_credit": "none_match_engine_assertion_exact_planned",
        "plan_state": "planned_not_executable",
        "target_test_artifact": MATCH_ENGINE_ASSERTION_EXACT_TARGET_TEST_ARTIFACT,
        "observability_status": "search_and_exec_observable",
        "next_action": "materialize_match_engine_assertion_exact_case",
    }
    for field, expected_value in expected.items():
        if plan[field] != expected_value:
            raise SystemExit(
                f"match-engine assertion exact plan row {requirement_id} has "
                f"{field}={plan[field]!r}; expected {expected_value!r}"
            )
    for field in [
        "source_file",
        "section_anchor",
        "exact_case_family",
        "exact_case_id",
        "pattern",
        "expected_search_result",
        "expected_exec_result",
        "expected_behavior",
        "exact_case_obligation",
        "observability_reason",
    ]:
        if not plan[field]:
            raise SystemExit(
                f"match-engine assertion exact plan row {requirement_id} "
                f"has empty {field}"
            )
    if plan["expected_search_result"] not in {"true", "false"}:
        raise SystemExit(
            f"match-engine assertion exact plan row {requirement_id} has "
            f"expected_search_result={plan['expected_search_result']!r}"
        )
    if plan["expected_exec_result"] not in {"true", "false"}:
        raise SystemExit(
            f"match-engine assertion exact plan row {requirement_id} has "
            f"expected_exec_result={plan['expected_exec_result']!r}"
        )
    if plan["expected_exec_result"] == "true":
        for field in ["expected_start_index", "expected_end_index"]:
            if not plan[field]:
                raise SystemExit(
                    f"match-engine assertion exact plan row {requirement_id} "
                    f"has empty {field}"
                )
    else:
        for field in ["expected_start_index", "expected_end_index", "expected_match_text"]:
            if plan[field]:
                raise SystemExit(
                    f"match-engine assertion exact negative row {requirement_id} "
                    f"has non-empty {field}"
                )
    if not plan["exact_case_id"].startswith(
        f"match-engine-assertion-exact:{requirement_id}:"
    ):
        raise SystemExit(
            f"match-engine assertion exact plan row {requirement_id} has "
            f"invalid exact_case_id {plan['exact_case_id']!r}"
        )
    if not Path(plan["source_file"]).is_file():
        raise SystemExit(
            f"match-engine assertion exact plan row {requirement_id} source "
            f"is missing: {plan['source_file']}"
        )
    if not Path(plan["target_test_artifact"]).is_file():
        raise SystemExit(
            f"match-engine assertion exact plan row {requirement_id} target "
            f"artifact is missing: {plan['target_test_artifact']}"
        )
    if not match_engine_assertion_exact_plan_is_creditable(plan):
        raise SystemExit(
            f"match-engine assertion exact plan row {requirement_id} has "
            f"unsupported coverage_credit={plan['coverage_credit']!r} and "
            f"plan_state={plan['plan_state']!r}"
        )


def match_engine_assertion_exact_audit_row(
    plan: dict[str, str],
) -> dict[str, str]:
    validate_match_engine_assertion_exact_plan_row(plan)
    requirement_id = plan["requirement_id"]
    selector_tags = (
        "regexp_exec_and_captures,regexp_runtime_search,"
        "regexp_match_engine_assertions"
    )
    return {
        "audit_id": f"exactness:{requirement_id}:{plan['exact_case_id']}",
        "audit_scope": "ecma262_requirement",
        "requirement_id": requirement_id,
        "mapping_family": plan["mapping_family"],
        "executable_layer": plan["executable_layer"],
        "evidence_kind": "match_engine_assertion_exact_case",
        "case_id": plan["exact_case_id"],
        "case_source": f"{plan['source_file']}#{plan['section_anchor']}",
        "expected_behavior": "assertion_exact_plan_observable",
        "selector_tags": selector_tags,
        "selected_feature_tags": selector_tags,
        "selected_matched_selector_tags": selector_tags,
        "selected_missing_selector_tags": "",
        "case_reuse_count": "1",
        "exactness_audit_state": "covered_by_match_engine_exact",
        "coverage_credit": "match_engine_exact_requirement_credit",
        "next_action": "none_covered_by_match_engine_exact",
        "audit_reason": (
            "match-engine assertion exact case is linked to ECMA-262 "
            "CompileAssertion source text and covered by the executable "
            "search/exec assertion gate"
        ),
    }


def match_engine_atoms_exact_plan_is_creditable(plan: dict[str, str]) -> bool:
    return (
        plan["plan_state"] == "planned_not_executable"
        and plan["coverage_credit"] == "none_match_engine_atoms_exact_planned"
    )


def validate_match_engine_atoms_exact_plan_row(plan: dict[str, str]) -> None:
    requirement_id = plan["requirement_id"]
    expected = {
        "mapping_family": "match_engine_atoms",
        "executable_layer": "match_engine",
    }
    for field, expected_value in expected.items():
        if plan[field] != expected_value:
            raise SystemExit(
                f"match-engine atom exact plan row {requirement_id} has "
                f"{field}={plan[field]!r}; expected {expected_value!r}"
            )
    for field in [
        "source_file",
        "section_anchor",
        "atom_subfamily",
        "atom_semantic_route",
        "exact_case_id",
        "exact_case_obligation",
        "observability_status",
        "observability_reason",
    ]:
        if not plan[field]:
            raise SystemExit(
                f"match-engine atom exact plan row {requirement_id} has empty {field}"
            )
    if not Path(plan["source_file"]).is_file():
        raise SystemExit(
            f"match-engine atom exact plan row {requirement_id} source is "
            f"missing: {plan['source_file']}"
        )
    if match_engine_atoms_exact_plan_is_creditable(plan):
        expected_creditable = {
            "target_test_artifact": MATCH_ENGINE_ATOMS_EXACT_TARGET_TEST_ARTIFACT,
            "next_action": "materialize_match_engine_atoms_exact_case",
        }
        for field, expected_value in expected_creditable.items():
            if plan[field] != expected_value:
                raise SystemExit(
                    f"match-engine atom exact plan row {requirement_id} has "
                    f"{field}={plan[field]!r}; expected {expected_value!r}"
                )
        if plan["observability_status"] == "search_bool_observable":
            if plan["expected_search_result"] not in {"true", "false"}:
                raise SystemExit(
                    f"match-engine atom exact plan row {requirement_id} has "
                    f"expected_search_result={plan['expected_search_result']!r}"
                )
        elif plan["observability_status"] == "compile_atom_operation_model_observable":
            if plan["atom_semantic_route"] != "operation_model":
                raise SystemExit(
                    f"match-engine atom exact plan row {requirement_id} has "
                    f"atom_semantic_route={plan['atom_semantic_route']!r}; "
                    "expected 'operation_model'"
                )
            if plan["expected_search_result"] != "model_observable":
                raise SystemExit(
                    f"match-engine atom exact plan row {requirement_id} has "
                    f"expected_search_result={plan['expected_search_result']!r}; "
                    "expected 'model_observable'"
                )
            if plan["expected_behavior"] not in {
                "compile_atom_operation_shape_observed",
                "compile_atom_piecewise_dispatch_observed",
            }:
                raise SystemExit(
                    f"match-engine atom exact plan row {requirement_id} has "
                    f"expected_behavior={plan['expected_behavior']!r}"
                )
        else:
            raise SystemExit(
                f"match-engine atom exact plan row {requirement_id} has "
                f"observability_status={plan['observability_status']!r}"
            )
        for field in ["pattern", "input_text", "expected_behavior"]:
            if not plan[field]:
                raise SystemExit(
                    f"match-engine atom exact plan row {requirement_id} has empty {field}"
                )
        if not plan["exact_case_id"].startswith(
            f"match-engine-atoms-exact:{requirement_id}:"
        ):
            raise SystemExit(
                f"match-engine atom exact plan row {requirement_id} has invalid "
                f"exact_case_id {plan['exact_case_id']!r}"
            )
        if not Path(plan["target_test_artifact"]).is_file():
            raise SystemExit(
                f"match-engine atom exact plan row {requirement_id} target "
                f"artifact is missing: {plan['target_test_artifact']}"
            )
    else:
        expected_deferred = {
            "coverage_credit": "none_match_engine_atoms_exact_deferred",
            "expected_search_result": "not_observable",
            "pattern": "",
            "input_text": "",
            "target_test_artifact": "",
        }
        for field, expected_value in expected_deferred.items():
            if plan[field] != expected_value:
                raise SystemExit(
                    f"deferred match-engine atom exact plan row {requirement_id} "
                    f"has {field}={plan[field]!r}; expected {expected_value!r}"
                )
        if not plan["plan_state"].startswith("deferred_"):
            raise SystemExit(
                f"match-engine atom exact plan row {requirement_id} has "
                f"uncreditable non-deferred state {plan['plan_state']!r}"
            )


def match_engine_atoms_exact_audit_row(plan: dict[str, str]) -> dict[str, str]:
    validate_match_engine_atoms_exact_plan_row(plan)
    if not match_engine_atoms_exact_plan_is_creditable(plan):
        raise SystemExit(
            f"match-engine atom exact plan row {plan['requirement_id']} is not creditable"
        )
    requirement_id = plan["requirement_id"]
    selector_tags = "regexp_exec_and_captures,regexp_compile_atom,regexp_match_engine_atoms"
    return {
        "audit_id": f"exactness:{requirement_id}:{plan['exact_case_id']}",
        "audit_scope": "ecma262_requirement",
        "requirement_id": requirement_id,
        "mapping_family": plan["mapping_family"],
        "executable_layer": plan["executable_layer"],
        "evidence_kind": "match_engine_atoms_exact_case",
        "case_id": plan["exact_case_id"],
        "case_source": f"{plan['source_file']}#{plan['section_anchor']}",
        "expected_behavior": plan["expected_behavior"],
        "selector_tags": selector_tags,
        "selected_feature_tags": selector_tags,
        "selected_matched_selector_tags": selector_tags,
        "selected_missing_selector_tags": "",
        "case_reuse_count": "1",
        "exactness_audit_state": "covered_by_match_engine_exact",
        "coverage_credit": "match_engine_exact_requirement_credit",
        "next_action": "none_covered_by_match_engine_exact",
        "audit_reason": (
            "match-engine atom exact case is selector-complete, unique for "
            "the CompileAtom requirement row, linked to the ECMA-262 runtime "
            "source clause, and covered by the executable atom exact gate"
        ),
    }


def validate_match_engine_capture_exact_plan_row(plan: dict[str, str]) -> None:
    requirement_id = plan["requirement_id"]
    expected = {
        "mapping_family": "match_engine_atoms",
        "executable_layer": "match_engine",
        "capture_subfamily": "capturing_group_atom",
        "capture_semantic_route": "capture_range_match_state_model",
        "expected_observed": "true",
        "expected_behavior": "capture_model_observable",
        "coverage_credit": "none_match_engine_capture_exact_planned",
        "plan_state": "planned_not_executable",
        "target_test_artifact": MATCH_ENGINE_CAPTURE_EXACT_TARGET_TEST_ARTIFACT,
        "observability_status": "capture_model_observable",
        "next_action": "materialize_match_engine_capture_exact_case",
    }
    for field, expected_value in expected.items():
        if plan[field] != expected_value:
            raise SystemExit(
                f"match-engine capture exact plan row {requirement_id} has "
                f"{field}={plan[field]!r}; expected {expected_value!r}"
            )
    allowed_observations = {
        "capture_group_atom",
        "capture_subpattern_matcher",
        "capture_paren_index",
        "capture_matcher_closure",
        "capture_match_state_parameter",
        "capture_continuation_parameter",
        "capture_nested_continuation",
        "capture_nested_match_state_parameter",
        "capture_copy",
        "capture_input_preserved",
        "capture_start_index",
        "capture_end_index",
        "capture_forward_branch",
        "capture_forward_order",
        "capture_forward_range",
        "capture_backward_branch",
        "capture_backward_direction",
        "capture_backward_order",
        "capture_backward_range",
        "capture_slot_write",
        "capture_result_state",
        "capture_outer_continuation",
        "capture_submatcher_invocation",
    }
    if plan["expected_observation"] not in allowed_observations:
        raise SystemExit(
            f"match-engine capture exact plan row {requirement_id} has "
            f"expected_observation={plan['expected_observation']!r}"
        )
    for field in [
        "source_atom_plan_id",
        "source_file",
        "section_anchor",
        "exact_case_family",
        "exact_case_id",
        "pattern",
        "input_text",
        "exact_case_obligation",
        "observability_reason",
    ]:
        if not plan[field]:
            raise SystemExit(
                f"match-engine capture exact plan row {requirement_id} "
                f"has empty {field}"
            )
    if not plan["exact_case_id"].startswith(
        f"match-engine-capture-exact:{requirement_id}:"
    ):
        raise SystemExit(
            f"match-engine capture exact plan row {requirement_id} has invalid "
            f"exact_case_id {plan['exact_case_id']!r}"
        )
    if not Path(plan["source_file"]).is_file():
        raise SystemExit(
            f"match-engine capture exact plan row {requirement_id} source is "
            f"missing: {plan['source_file']}"
        )
    if not Path(plan["target_test_artifact"]).is_file():
        raise SystemExit(
            f"match-engine capture exact plan row {requirement_id} target "
            f"artifact is missing: {plan['target_test_artifact']}"
        )


def match_engine_capture_exact_audit_row(plan: dict[str, str]) -> dict[str, str]:
    validate_match_engine_capture_exact_plan_row(plan)
    requirement_id = plan["requirement_id"]
    selector_tags = (
        "regexp_exec_and_captures,regexp_compile_atom,regexp_match_engine_atoms,"
        "regexp_capture_model"
    )
    return {
        "audit_id": f"exactness:{requirement_id}:{plan['exact_case_id']}",
        "audit_scope": "ecma262_requirement",
        "requirement_id": requirement_id,
        "mapping_family": plan["mapping_family"],
        "executable_layer": plan["executable_layer"],
        "evidence_kind": "match_engine_capture_exact_case",
        "case_id": plan["exact_case_id"],
        "case_source": f"{plan['source_file']}#{plan['section_anchor']}",
        "expected_behavior": plan["expected_behavior"],
        "selector_tags": selector_tags,
        "selected_feature_tags": selector_tags,
        "selected_matched_selector_tags": selector_tags,
        "selected_missing_selector_tags": "",
        "case_reuse_count": "1",
        "exactness_audit_state": "covered_by_match_engine_exact",
        "coverage_credit": "match_engine_exact_requirement_credit",
        "next_action": "none_covered_by_match_engine_exact",
        "audit_reason": (
            "match-engine capture exact case is selector-complete, unique for "
            "the CompileAtom capturing-group requirement row, linked to the "
            "ECMA-262 runtime source clause, and covered by the executable "
            "capture matcher-model gate"
        ),
    }


def validate_match_engine_unicode_sets_string_exact_plan_row(
    plan: dict[str, str],
) -> None:
    requirement_id = plan["requirement_id"]
    expected = {
        "mapping_family": "match_engine_atoms",
        "executable_layer": "match_engine",
        "unicode_sets_subfamily": "character_class_unicode_sets_string_elements",
        "unicode_sets_semantic_route": "unicode_sets_string_element_matcher_model",
        "expected_observed": "true",
        "expected_behavior": "unicode_sets_string_element_model_observable",
        "coverage_credit": "none_match_engine_unicode_sets_string_exact_planned",
        "plan_state": "planned_not_executable",
        "target_test_artifact": (
            MATCH_ENGINE_UNICODE_SETS_STRING_EXACT_TARGET_TEST_ARTIFACT
        ),
        "observability_status": "unicode_sets_string_element_model_observable",
        "next_action": "materialize_match_engine_unicode_sets_string_exact_case",
    }
    for field, expected_value in expected.items():
        if plan[field] != expected_value:
            raise SystemExit(
                "match-engine UnicodeSets string exact plan row "
                f"{requirement_id} has {field}={plan[field]!r}; "
                f"expected {expected_value!r}"
            )
    allowed_observations = {
        "unicode_sets_character_class_invert_false_assert",
        "unicode_sets_matcher_list_initialized",
        "unicode_sets_multi_char_elements_descending_iteration",
        "unicode_sets_last_code_point_charset",
        "unicode_sets_last_code_point_matcher",
        "unicode_sets_prefix_code_point_iteration",
        "unicode_sets_prefix_code_point_charset",
        "unicode_sets_prefix_code_point_matcher",
        "unicode_sets_match_sequence_built",
        "unicode_sets_multi_matcher_appended",
        "unicode_sets_singles_charset_built",
        "unicode_sets_singles_matcher_appended",
        "unicode_sets_empty_sequence_checked",
        "unicode_sets_empty_matcher_appended",
        "unicode_sets_last_matcher_selected",
        "unicode_sets_match_two_alternatives_fold",
        "unicode_sets_final_matcher_return",
    }
    if plan["expected_observation"] not in allowed_observations:
        raise SystemExit(
            "match-engine UnicodeSets string exact plan row "
            f"{requirement_id} has "
            f"expected_observation={plan['expected_observation']!r}"
        )
    for field in [
        "source_atom_plan_id",
        "source_file",
        "section_anchor",
        "exact_case_family",
        "exact_case_id",
        "pattern",
        "flags",
        "input_text",
        "expected_exec_text",
        "exact_case_obligation",
        "observability_reason",
    ]:
        if not plan[field]:
            raise SystemExit(
                "match-engine UnicodeSets string exact plan row "
                f"{requirement_id} has empty {field}"
            )
    if not plan["exact_case_id"].startswith(
        f"match-engine-unicode-sets-string-exact:{requirement_id}:"
    ):
        raise SystemExit(
            "match-engine UnicodeSets string exact plan row "
            f"{requirement_id} has invalid exact_case_id "
            f"{plan['exact_case_id']!r}"
        )
    if not Path(plan["source_file"]).is_file():
        raise SystemExit(
            "match-engine UnicodeSets string exact plan row "
            f"{requirement_id} source is missing: {plan['source_file']}"
        )
    if not Path(plan["target_test_artifact"]).is_file():
        raise SystemExit(
            "match-engine UnicodeSets string exact plan row "
            f"{requirement_id} target artifact is missing: "
            f"{plan['target_test_artifact']}"
        )


def match_engine_unicode_sets_string_exact_audit_row(
    plan: dict[str, str],
) -> dict[str, str]:
    validate_match_engine_unicode_sets_string_exact_plan_row(plan)
    requirement_id = plan["requirement_id"]
    selector_tags = (
        "regexp_exec_and_captures,regexp_compile_atom,regexp_match_engine_atoms,"
        "regexp_unicode_sets_string_elements"
    )
    return {
        "audit_id": f"exactness:{requirement_id}:{plan['exact_case_id']}",
        "audit_scope": "ecma262_requirement",
        "requirement_id": requirement_id,
        "mapping_family": plan["mapping_family"],
        "executable_layer": plan["executable_layer"],
        "evidence_kind": "match_engine_unicode_sets_string_exact_case",
        "case_id": plan["exact_case_id"],
        "case_source": f"{plan['source_file']}#{plan['section_anchor']}",
        "expected_behavior": plan["expected_behavior"],
        "selector_tags": selector_tags,
        "selected_feature_tags": selector_tags,
        "selected_matched_selector_tags": selector_tags,
        "selected_missing_selector_tags": "",
        "case_reuse_count": "1",
        "exactness_audit_state": "covered_by_match_engine_exact",
        "coverage_credit": "match_engine_exact_requirement_credit",
        "next_action": "none_covered_by_match_engine_exact",
        "audit_reason": (
            "match-engine UnicodeSets string-element exact case is "
            "selector-complete, unique for the CompileAtom CharacterClass "
            "requirement row, linked to the ECMA-262 runtime source clause, "
            "and covered by the executable internal matcher-model gate"
        ),
    }


def validate_match_engine_unicode_sets_escape_string_exact_plan_row(
    plan: dict[str, str],
) -> None:
    requirement_id = plan["requirement_id"]
    expected = {
        "mapping_family": "match_engine_atoms",
        "executable_layer": "match_engine",
        "unicode_sets_subfamily": (
            "character_class_escape_unicode_sets_string_elements"
        ),
        "unicode_sets_semantic_route": "unicode_sets_string_element_matcher_model",
        "expected_observed": "true",
        "expected_behavior": "unicode_sets_string_element_model_observable",
        "coverage_credit": (
            "none_match_engine_unicode_sets_escape_string_exact_planned"
        ),
        "plan_state": "planned_not_executable",
        "target_test_artifact": (
            MATCH_ENGINE_UNICODE_SETS_ESCAPE_STRING_EXACT_TARGET_TEST_ARTIFACT
        ),
        "observability_status": "unicode_sets_string_element_model_observable",
        "next_action": (
            "materialize_match_engine_unicode_sets_escape_string_exact_case"
        ),
    }
    for field, expected_value in expected.items():
        if plan[field] != expected_value:
            raise SystemExit(
                "match-engine UnicodeSets escape string exact plan row "
                f"{requirement_id} has {field}={plan[field]!r}; "
                f"expected {expected_value!r}"
            )
    allowed_observations = {
        "unicode_sets_matcher_list_initialized",
        "unicode_sets_multi_char_elements_descending_iteration",
        "unicode_sets_last_code_point_charset",
        "unicode_sets_last_code_point_matcher",
        "unicode_sets_prefix_code_point_iteration",
        "unicode_sets_prefix_code_point_charset",
        "unicode_sets_prefix_code_point_matcher",
        "unicode_sets_match_sequence_built",
        "unicode_sets_multi_matcher_appended",
        "unicode_sets_singles_charset_built",
        "unicode_sets_singles_matcher_appended",
        "unicode_sets_empty_sequence_checked",
        "unicode_sets_empty_matcher_appended",
        "unicode_sets_last_matcher_selected",
        "unicode_sets_match_two_alternatives_fold",
        "unicode_sets_final_matcher_return",
    }
    if plan["expected_observation"] not in allowed_observations:
        raise SystemExit(
            "match-engine UnicodeSets escape string exact plan row "
            f"{requirement_id} has "
            f"expected_observation={plan['expected_observation']!r}"
        )
    for field in [
        "source_atom_plan_id",
        "source_file",
        "section_anchor",
        "exact_case_family",
        "exact_case_id",
        "pattern",
        "flags",
        "input_text",
        "expected_exec_text",
        "exact_case_obligation",
        "observability_reason",
    ]:
        if not plan[field]:
            raise SystemExit(
                "match-engine UnicodeSets escape string exact plan row "
                f"{requirement_id} has empty {field}"
            )
    if not plan["exact_case_id"].startswith(
        f"match-engine-unicode-sets-escape-string-exact:{requirement_id}:"
    ):
        raise SystemExit(
            "match-engine UnicodeSets escape string exact plan row "
            f"{requirement_id} has invalid exact_case_id "
            f"{plan['exact_case_id']!r}"
        )
    if not Path(plan["source_file"]).is_file():
        raise SystemExit(
            "match-engine UnicodeSets escape string exact plan row "
            f"{requirement_id} source is missing: {plan['source_file']}"
        )
    if not Path(plan["target_test_artifact"]).is_file():
        raise SystemExit(
            "match-engine UnicodeSets escape string exact plan row "
            f"{requirement_id} target artifact is missing: "
            f"{plan['target_test_artifact']}"
        )


def match_engine_unicode_sets_escape_string_exact_audit_row(
    plan: dict[str, str],
) -> dict[str, str]:
    validate_match_engine_unicode_sets_escape_string_exact_plan_row(plan)
    requirement_id = plan["requirement_id"]
    selector_tags = (
        "regexp_exec_and_captures,regexp_compile_atom,regexp_match_engine_atoms,"
        "regexp_unicode_sets_string_elements,regexp_character_class_escape"
    )
    return {
        "audit_id": f"exactness:{requirement_id}:{plan['exact_case_id']}",
        "audit_scope": "ecma262_requirement",
        "requirement_id": requirement_id,
        "mapping_family": plan["mapping_family"],
        "executable_layer": plan["executable_layer"],
        "evidence_kind": "match_engine_unicode_sets_escape_string_exact_case",
        "case_id": plan["exact_case_id"],
        "case_source": f"{plan['source_file']}#{plan['section_anchor']}",
        "expected_behavior": plan["expected_behavior"],
        "selector_tags": selector_tags,
        "selected_feature_tags": selector_tags,
        "selected_matched_selector_tags": selector_tags,
        "selected_missing_selector_tags": "",
        "case_reuse_count": "1",
        "exactness_audit_state": "covered_by_match_engine_exact",
        "coverage_credit": "match_engine_exact_requirement_credit",
        "next_action": "none_covered_by_match_engine_exact",
        "audit_reason": (
            "match-engine UnicodeSets escape string-element exact case is "
            "selector-complete, unique for the CompileAtom CharacterClassEscape "
            "requirement row, linked to the ECMA-262 runtime source clause, "
            "and covered by the executable internal matcher-model gate"
        ),
    }


def validate_match_engine_concatenation_exact_plan_row(
    plan: dict[str, str],
) -> None:
    requirement_id = plan["requirement_id"]
    expected = {
        "clause_id": "22.2.2.3.4",
        "mapping_family": "match_engine_concatenation",
        "executable_layer": "match_engine",
        "expected_search_result": "true",
        "expected_observed": "true",
        "expected_behavior": "match_sequence_exact_plan_observable",
        "coverage_credit": "none_match_engine_concatenation_exact_planned",
        "plan_state": "planned_not_executable",
        "target_test_artifact": (
            MATCH_ENGINE_CONCATENATION_EXACT_TARGET_TEST_ARTIFACT
        ),
        "observability_status": "match_sequence_model_observable",
        "next_action": "materialize_match_engine_concatenation_exact_case",
    }
    for field, expected_value in expected.items():
        if plan[field] != expected_value:
            raise SystemExit(
                "match-engine concatenation exact plan row "
                f"{requirement_id} has {field}={plan[field]!r}; "
                f"expected {expected_value!r}"
            )
    if plan["match_sequence_subfamily"] != "match_sequence_operation":
        raise SystemExit(
            "match-engine concatenation exact plan row "
            f"{requirement_id} has match_sequence_subfamily="
            f"{plan['match_sequence_subfamily']!r}"
        )
    if plan["match_sequence_route"] != "matcher_continuation_runtime_semantics":
        raise SystemExit(
            "match-engine concatenation exact plan row "
            f"{requirement_id} has match_sequence_route="
            f"{plan['match_sequence_route']!r}"
        )
    if plan["expected_observation"] not in {
        "match_sequence_operation",
        "match_sequence_forward_branch",
        "match_sequence_forward_closure",
        "match_sequence_forward_match_state_parameter",
        "match_sequence_forward_continuation_parameter",
        "match_sequence_forward_nested_match_state_parameter",
        "match_sequence_backward_branch",
        "match_sequence_backward_closure",
        "match_sequence_backward_match_state_parameter",
        "match_sequence_backward_continuation_parameter",
        "match_sequence_backward_nested_continuation",
        "match_sequence_backward_nested_match_state_parameter",
        "match_sequence_backward_first_matcher_return",
        "match_sequence_backward_second_matcher_return",
    }:
        raise SystemExit(
            "match-engine concatenation exact plan row "
            f"{requirement_id} has expected_observation="
            f"{plan['expected_observation']!r}"
        )
    for field in [
        "source_file",
        "section_anchor",
        "case_route",
        "exact_case_family",
        "exact_case_id",
        "pattern",
        "input_text",
        "exact_case_obligation",
        "observability_reason",
    ]:
        if not plan[field]:
            raise SystemExit(
                "match-engine concatenation exact plan row "
                f"{requirement_id} has empty {field}"
            )
    if not plan["exact_case_id"].startswith(
        f"match-engine-concatenation-exact:{requirement_id}:"
    ):
        raise SystemExit(
            "match-engine concatenation exact plan row "
            f"{requirement_id} has invalid exact_case_id "
            f"{plan['exact_case_id']!r}"
        )
    if not Path(plan["source_file"]).is_file():
        raise SystemExit(
            "match-engine concatenation exact plan row "
            f"{requirement_id} source is missing: {plan['source_file']}"
        )
    if not Path(plan["target_test_artifact"]).is_file():
        raise SystemExit(
            "match-engine concatenation exact plan row "
            f"{requirement_id} target artifact is missing: "
            f"{plan['target_test_artifact']}"
        )


def match_engine_concatenation_exact_audit_row(
    plan: dict[str, str],
) -> dict[str, str]:
    validate_match_engine_concatenation_exact_plan_row(plan)
    requirement_id = plan["requirement_id"]
    selector_tags = (
        "regexp_exec_and_captures,regexp_match_sequence,"
        "regexp_match_engine_concatenation"
    )
    return {
        "audit_id": f"exactness:{requirement_id}:{plan['exact_case_id']}",
        "audit_scope": "ecma262_requirement",
        "requirement_id": requirement_id,
        "mapping_family": plan["mapping_family"],
        "executable_layer": plan["executable_layer"],
        "evidence_kind": "match_engine_concatenation_exact_case",
        "case_id": plan["exact_case_id"],
        "case_source": f"{plan['source_file']}#{plan['section_anchor']}",
        "expected_behavior": plan["expected_behavior"],
        "selector_tags": selector_tags,
        "selected_feature_tags": selector_tags,
        "selected_matched_selector_tags": selector_tags,
        "selected_missing_selector_tags": "",
        "case_reuse_count": "1",
        "exactness_audit_state": "covered_by_match_engine_exact",
        "coverage_credit": "match_engine_exact_requirement_credit",
        "next_action": "none_covered_by_match_engine_exact",
        "audit_reason": (
            "match-engine concatenation exact case is selector-complete, "
            "unique for the ECMA-262 22.2.2.3.4 requirement row, linked to "
            "the runtime source clause, and covered by the executable "
            "MatchSequence matcher-continuation gate"
        ),
    }


def match_engine_character_classes_exact_plan_is_creditable(
    plan: dict[str, str],
) -> bool:
    return (
        plan["character_class_subfamily"]
        in {"character_range", "character_complement"}
        and plan["plan_state"] == "planned_not_executable"
        and plan["coverage_credit"]
        == "none_match_engine_character_classes_exact_planned"
    )


def validate_match_engine_character_classes_exact_plan_row(
    plan: dict[str, str],
) -> None:
    requirement_id = plan["requirement_id"]
    common_expected = {
        "mapping_family": "match_engine_character_classes",
        "executable_layer": "match_engine",
        "target_test_artifact": (
            MATCH_ENGINE_CHARACTER_CLASSES_EXACT_TARGET_TEST_ARTIFACT
        ),
    }
    for field, expected_value in common_expected.items():
        if plan[field] != expected_value:
            raise SystemExit(
                "match-engine character-class exact plan row "
                f"{requirement_id} has {field}={plan[field]!r}; "
                f"expected {expected_value!r}"
            )
    if plan["character_class_subfamily"] == "character_range":
        expected = {
            "clause_id": "22.2.2.9.1",
            "character_class_route": "character_range_runtime_semantics",
            "expected_search_result": "true",
            "expected_observed": "true",
            "expected_behavior": "character_range_exact_plan_observable",
            "coverage_credit": "none_match_engine_character_classes_exact_planned",
            "plan_state": "planned_not_executable",
            "observability_status": "character_range_model_observable",
            "next_action": "materialize_match_engine_character_class_exact_case",
        }
        allowed_observations = {
            "character_range_operation",
            "character_range_singleton_assert",
            "character_range_start_char_read",
            "character_range_end_char_read",
            "character_range_start_code",
            "character_range_end_code",
            "character_range_order_assert",
            "character_range_inclusive_return",
        }
    elif plan["character_class_subfamily"] == "character_complement":
        expected = {
            "clause_id": "22.2.2.9.6",
            "character_class_route": "character_complement_allcharacters_policy",
            "expected_search_result": "true",
            "expected_observed": "true",
            "expected_behavior": "character_complement_exact_plan_observable",
            "coverage_credit": "none_match_engine_character_classes_exact_planned",
            "plan_state": "planned_not_executable",
            "observability_status": (
                "character_complement_allcharacters_model_observable"
            ),
            "next_action": "materialize_match_engine_character_class_exact_case",
        }
        allowed_observations = {
            "character_complement_operation",
            "character_complement_all_characters",
            "character_complement_difference_return",
        }
    else:
        raise SystemExit(
            "match-engine character-class exact plan row "
            f"{requirement_id} has character_class_subfamily="
            f"{plan['character_class_subfamily']!r}"
        )
    for field, expected_value in expected.items():
        if plan[field] != expected_value:
            raise SystemExit(
                "match-engine character-class exact plan row "
                f"{requirement_id} has {field}={plan[field]!r}; "
                f"expected {expected_value!r}"
            )
    if plan["expected_observation"] not in allowed_observations:
        raise SystemExit(
            "match-engine character-class exact plan row "
            f"{requirement_id} has expected_observation="
            f"{plan['expected_observation']!r}"
        )
    for field in [
        "source_file",
        "section_anchor",
        "case_route",
        "exact_case_family",
        "exact_case_id",
        "pattern",
        "input_text",
        "exact_case_obligation",
        "observability_reason",
    ]:
        if not plan[field]:
            raise SystemExit(
                "match-engine character-class exact plan row "
                f"{requirement_id} has empty {field}"
            )
    if not plan["exact_case_id"].startswith(
        f"match-engine-character-classes-exact:{requirement_id}:"
    ):
        raise SystemExit(
            "match-engine character-class exact plan row "
            f"{requirement_id} has invalid exact_case_id "
            f"{plan['exact_case_id']!r}"
        )
    if not Path(plan["source_file"]).is_file():
        raise SystemExit(
            "match-engine character-class exact plan row "
            f"{requirement_id} source is missing: {plan['source_file']}"
        )
    if not Path(plan["target_test_artifact"]).is_file():
        raise SystemExit(
            "match-engine character-class exact plan row "
            f"{requirement_id} target artifact is missing: "
            f"{plan['target_test_artifact']}"
        )


def match_engine_character_classes_exact_audit_row(
    plan: dict[str, str],
) -> dict[str, str]:
    validate_match_engine_character_classes_exact_plan_row(plan)
    if not match_engine_character_classes_exact_plan_is_creditable(plan):
        raise SystemExit(
            "match-engine character-class exact plan row "
            f"{plan['requirement_id']} is not creditable"
        )
    requirement_id = plan["requirement_id"]
    if plan["character_class_subfamily"] == "character_range":
        selector_tags = (
            "regexp_character_class,regexp_character_range,"
            "regexp_match_engine_character_classes"
        )
        audit_reason = (
            "match-engine character-class exact case is selector-complete, "
            "unique for the ECMA-262 CharacterRange requirement row, linked to "
            "the runtime source clause, and covered by the executable "
            "character-range matcher-model gate"
        )
    else:
        selector_tags = (
            "regexp_character_class,regexp_character_complement,"
            "regexp_match_engine_character_classes"
        )
        audit_reason = (
            "match-engine character-class exact case is selector-complete, "
            "unique for the ECMA-262 CharacterComplement requirement row, "
            "linked to the runtime source clause, and covered by the "
            "executable AllCharacters-backed complement matcher-model gate"
        )
    return {
        "audit_id": f"exactness:{requirement_id}:{plan['exact_case_id']}",
        "audit_scope": "ecma262_requirement",
        "requirement_id": requirement_id,
        "mapping_family": plan["mapping_family"],
        "executable_layer": plan["executable_layer"],
        "evidence_kind": "match_engine_character_classes_exact_case",
        "case_id": plan["exact_case_id"],
        "case_source": f"{plan['source_file']}#{plan['section_anchor']}",
        "expected_behavior": plan["expected_behavior"],
        "selector_tags": selector_tags,
        "selected_feature_tags": selector_tags,
        "selected_matched_selector_tags": selector_tags,
        "selected_missing_selector_tags": "",
        "case_reuse_count": "1",
        "exactness_audit_state": "covered_by_match_engine_exact",
        "coverage_credit": "match_engine_exact_requirement_credit",
        "next_action": "none_covered_by_match_engine_exact",
        "audit_reason": audit_reason,
    }


def validate_match_engine_backreference_exact_plan_row(
    plan: dict[str, str],
) -> None:
    requirement_id = plan["requirement_id"]
    expected = {
        "mapping_family": "match_engine_atoms",
        "executable_layer": "match_engine",
        "expected_search_result": "true",
        "expected_observed": "true",
        "expected_behavior": "backreference_model_observable",
        "coverage_credit": "none_match_engine_backreference_exact_planned",
        "plan_state": "planned_not_executable",
        "target_test_artifact": MATCH_ENGINE_BACKREFERENCE_EXACT_TARGET_TEST_ARTIFACT,
        "observability_status": "backreference_model_observable",
        "next_action": "materialize_match_engine_backreference_exact_case",
    }
    for field, expected_value in expected.items():
        if plan[field] != expected_value:
            raise SystemExit(
                f"match-engine backreference exact plan row {requirement_id} has "
                f"{field}={plan[field]!r}; expected {expected_value!r}"
            )
    if plan["backreference_subfamily"] == "decimal_backreference_atom_escape":
        if plan["backreference_semantic_route"] != "capture_backreference_runtime_model":
            raise SystemExit(
                f"decimal backreference exact plan row {requirement_id} has "
                f"backreference_semantic_route={plan['backreference_semantic_route']!r}"
            )
        allowed_observations = {
            "decimal_backreference_atom",
            "decimal_capturing_group_number",
            "decimal_group_count_assert",
            "decimal_backreference_matcher_return",
        }
    elif plan["backreference_subfamily"] == "named_backreference_atom_escape":
        if (
            plan["backreference_semantic_route"]
            != "named_capture_backreference_runtime_model"
        ):
            raise SystemExit(
                f"named backreference exact plan row {requirement_id} has "
                f"backreference_semantic_route={plan['backreference_semantic_route']!r}"
            )
        allowed_observations = {
            "named_backreference_atom",
            "named_matching_group_specifiers",
            "named_paren_indices_list",
            "named_group_specifier_iteration",
            "named_count_left_capturing_parens",
            "named_paren_index_append",
            "named_backreference_matcher_return",
        }
    else:
        raise SystemExit(
            f"match-engine backreference exact plan row {requirement_id} has "
            f"backreference_subfamily={plan['backreference_subfamily']!r}"
        )
    if plan["expected_observation"] not in allowed_observations:
        raise SystemExit(
            f"match-engine backreference exact plan row {requirement_id} has "
            f"expected_observation={plan['expected_observation']!r}"
        )
    for field in [
        "source_atom_plan_id",
        "source_file",
        "section_anchor",
        "exact_case_family",
        "exact_case_id",
        "pattern",
        "input_text",
        "exact_case_obligation",
        "observability_reason",
    ]:
        if not plan[field]:
            raise SystemExit(
                f"match-engine backreference exact plan row {requirement_id} "
                f"has empty {field}"
            )
    if not plan["exact_case_id"].startswith(
        f"match-engine-backreference-exact:{requirement_id}:"
    ):
        raise SystemExit(
            f"match-engine backreference exact plan row {requirement_id} has "
            f"invalid exact_case_id {plan['exact_case_id']!r}"
        )
    if not Path(plan["source_file"]).is_file():
        raise SystemExit(
            f"match-engine backreference exact plan row {requirement_id} source "
            f"is missing: {plan['source_file']}"
        )
    if not Path(plan["target_test_artifact"]).is_file():
        raise SystemExit(
            f"match-engine backreference exact plan row {requirement_id} target "
            f"artifact is missing: {plan['target_test_artifact']}"
        )


def match_engine_backreference_exact_audit_row(
    plan: dict[str, str],
) -> dict[str, str]:
    validate_match_engine_backreference_exact_plan_row(plan)
    requirement_id = plan["requirement_id"]
    selector_tags = (
        "regexp_exec_and_captures,regexp_compile_atom,"
        "regexp_match_engine_backreferences"
    )
    return {
        "audit_id": f"exactness:{requirement_id}:{plan['exact_case_id']}",
        "audit_scope": "ecma262_requirement",
        "requirement_id": requirement_id,
        "mapping_family": plan["mapping_family"],
        "executable_layer": plan["executable_layer"],
        "evidence_kind": "match_engine_backreference_exact_case",
        "case_id": plan["exact_case_id"],
        "case_source": f"{plan['source_file']}#{plan['section_anchor']}",
        "expected_behavior": plan["expected_behavior"],
        "selector_tags": selector_tags,
        "selected_feature_tags": selector_tags,
        "selected_matched_selector_tags": selector_tags,
        "selected_missing_selector_tags": "",
        "case_reuse_count": "1",
        "exactness_audit_state": "covered_by_match_engine_exact",
        "coverage_credit": "match_engine_exact_requirement_credit",
        "next_action": "none_covered_by_match_engine_exact",
        "audit_reason": (
            "match-engine backreference exact case is selector-complete, "
            "unique for the CompileAtom backreference requirement row, linked "
            "to the ECMA-262 runtime source clause, and covered by the "
            "executable backreference matcher-model gate"
        ),
    }


def validate_match_engine_backreference_matcher_exact_plan_row(
    plan: dict[str, str],
) -> None:
    requirement_id = plan["requirement_id"]
    expected = {
        "clause_id": "22.2.2.7.2",
        "mapping_family": "match_engine_backreferences",
        "executable_layer": "match_engine",
        "expected_observed": "true",
        "expected_behavior": "backreference_matcher_exact_plan_observable",
        "coverage_credit": "none_match_engine_backreference_matcher_exact_planned",
        "plan_state": "planned_not_executable",
        "target_test_artifact": (
            MATCH_ENGINE_BACKREFERENCE_MATCHER_EXACT_TARGET_TEST_ARTIFACT
        ),
        "observability_status": "backreference_matcher_model_observable",
        "next_action": (
            "materialize_match_engine_backreference_matcher_exact_case"
        ),
    }
    for field, expected_value in expected.items():
        if plan[field] != expected_value:
            raise SystemExit(
                "match-engine BackreferenceMatcher exact plan row "
                f"{requirement_id} has {field}={plan[field]!r}; "
                f"expected {expected_value!r}"
            )
    if plan["backreference_matcher_subfamily"] != "backreference_matcher_operation":
        raise SystemExit(
            "match-engine BackreferenceMatcher exact plan row "
            f"{requirement_id} has "
            "backreference_matcher_subfamily="
            f"{plan['backreference_matcher_subfamily']!r}"
        )
    if (
        plan["backreference_matcher_route"]
        != "capture_backreference_runtime_semantics"
    ):
        raise SystemExit(
            "match-engine BackreferenceMatcher exact plan row "
            f"{requirement_id} has backreference_matcher_route="
            f"{plan['backreference_matcher_route']!r}"
        )
    if plan["expected_observation"] not in {
        "backreference_matcher_operation",
        "backreference_matcher_closure",
        "backreference_match_state_parameter",
        "backreference_continuation_parameter",
        "backreference_input_read",
        "backreference_captures_read",
        "backreference_result_initialized_undefined",
        "backreference_ns_iteration",
        "backreference_defined_capture_branch",
        "backreference_single_defined_capture_assert",
        "backreference_selected_capture_range",
        "backreference_undefined_capture_continuation",
        "backreference_end_index_read",
        "backreference_capture_start_index_read",
        "backreference_capture_end_index_read",
        "backreference_capture_length_computed",
        "backreference_forward_index_computed",
        "backreference_backward_index_computed",
        "backreference_input_length_read",
        "backreference_bounds_failure",
        "backreference_compare_start_min",
        "backreference_canonicalize_compare",
        "backreference_result_state_created",
        "backreference_continuation_return",
    }:
        raise SystemExit(
            "match-engine BackreferenceMatcher exact plan row "
            f"{requirement_id} has expected_observation="
            f"{plan['expected_observation']!r}"
        )
    if plan["expected_search_result"] not in {"true", "false"}:
        raise SystemExit(
            "match-engine BackreferenceMatcher exact plan row "
            f"{requirement_id} has expected_search_result="
            f"{plan['expected_search_result']!r}"
        )
    for field in [
        "source_file",
        "section_anchor",
        "case_route",
        "exact_case_family",
        "exact_case_id",
        "pattern",
        "input_text",
        "exact_case_obligation",
        "observability_reason",
    ]:
        if not plan[field]:
            raise SystemExit(
                "match-engine BackreferenceMatcher exact plan row "
                f"{requirement_id} has empty {field}"
            )
    if not plan["exact_case_id"].startswith(
        f"match-engine-backreference-matcher-exact:{requirement_id}:"
    ):
        raise SystemExit(
            "match-engine BackreferenceMatcher exact plan row "
            f"{requirement_id} has invalid exact_case_id "
            f"{plan['exact_case_id']!r}"
        )
    if not Path(plan["source_file"]).is_file():
        raise SystemExit(
            "match-engine BackreferenceMatcher exact plan row "
            f"{requirement_id} source is missing: {plan['source_file']}"
        )
    if not Path(plan["target_test_artifact"]).is_file():
        raise SystemExit(
            "match-engine BackreferenceMatcher exact plan row "
            f"{requirement_id} target artifact is missing: "
            f"{plan['target_test_artifact']}"
        )


def match_engine_backreference_matcher_exact_audit_row(
    plan: dict[str, str],
) -> dict[str, str]:
    validate_match_engine_backreference_matcher_exact_plan_row(plan)
    requirement_id = plan["requirement_id"]
    selector_tags = (
        "regexp_exec_and_captures,regexp_backreference_matcher,"
        "regexp_match_engine_backreferences"
    )
    return {
        "audit_id": f"exactness:{requirement_id}:{plan['exact_case_id']}",
        "audit_scope": "ecma262_requirement",
        "requirement_id": requirement_id,
        "mapping_family": plan["mapping_family"],
        "executable_layer": plan["executable_layer"],
        "evidence_kind": "match_engine_backreference_matcher_exact_case",
        "case_id": plan["exact_case_id"],
        "case_source": f"{plan['source_file']}#{plan['section_anchor']}",
        "expected_behavior": plan["expected_behavior"],
        "selector_tags": selector_tags,
        "selected_feature_tags": selector_tags,
        "selected_matched_selector_tags": selector_tags,
        "selected_missing_selector_tags": "",
        "case_reuse_count": "1",
        "exactness_audit_state": "covered_by_match_engine_exact",
        "coverage_credit": "match_engine_exact_requirement_credit",
        "next_action": "none_covered_by_match_engine_exact",
        "audit_reason": (
            "match-engine BackreferenceMatcher exact case is "
            "selector-complete, unique for the ECMA-262 22.2.2.7.2 "
            "requirement row, linked to the runtime source clause, and "
            "covered by the executable backreference matcher-model gate"
        ),
    }


def validate_match_engine_result_exact_plan_row(plan: dict[str, str]) -> None:
    requirement_id = plan["requirement_id"]
    expected = {
        "mapping_family": "match_engine_alternation",
        "executable_layer": "match_engine",
        "expected_behavior": "exec_left_priority_match",
        "coverage_credit": "none_match_engine_result_exact_planned",
        "plan_state": "planned_not_executable",
        "target_test_artifact": MATCH_ENGINE_RESULT_EXACT_TARGET_TEST_ARTIFACT,
        "observability_status": "exec_result_observable",
        "next_action": "materialize_match_engine_result_exact_case",
    }
    for field, expected_value in expected.items():
        if plan[field] != expected_value:
            raise SystemExit(
                f"match-engine result exact plan row {requirement_id} has "
                f"{field}={plan[field]!r}; expected {expected_value!r}"
            )
    for field in [
        "source_file",
        "section_anchor",
        "exact_case_family",
        "exact_case_id",
        "pattern",
        "input_text",
        "expected_start_index",
        "expected_end_index",
        "expected_match_text",
        "exact_case_obligation",
        "observability_reason",
    ]:
        if not plan[field]:
            raise SystemExit(
                f"match-engine result exact plan row {requirement_id} has empty {field}"
            )
    if not plan["exact_case_id"].startswith(
        f"match-engine-result-exact:{requirement_id}:"
    ):
        raise SystemExit(
            f"match-engine result exact plan row {requirement_id} has invalid "
            f"exact_case_id {plan['exact_case_id']!r}"
        )
    for field in ["expected_start_index", "expected_end_index"]:
        try:
            int(plan[field])
        except ValueError as exc:
            raise SystemExit(
                f"match-engine result exact plan row {requirement_id} has "
                f"invalid {field}={plan[field]!r}"
            ) from exc
    if not Path(plan["source_file"]).is_file():
        raise SystemExit(
            f"match-engine result exact plan row {requirement_id} source is "
            f"missing: {plan['source_file']}"
        )
    if not Path(plan["target_test_artifact"]).is_file():
        raise SystemExit(
            f"match-engine result exact plan row {requirement_id} target "
            f"artifact is missing: {plan['target_test_artifact']}"
        )


def match_engine_result_exact_audit_row(plan: dict[str, str]) -> dict[str, str]:
    validate_match_engine_result_exact_plan_row(plan)
    requirement_id = plan["requirement_id"]
    selector_tags = "regexp_exec_and_captures,regexp_runtime_exec_result"
    return {
        "audit_id": f"exactness:{requirement_id}:{plan['exact_case_id']}",
        "audit_scope": "ecma262_requirement",
        "requirement_id": requirement_id,
        "mapping_family": plan["mapping_family"],
        "executable_layer": plan["executable_layer"],
        "evidence_kind": "match_engine_result_exact_case",
        "case_id": plan["exact_case_id"],
        "case_source": f"{plan['source_file']}#{plan['section_anchor']}",
        "expected_behavior": plan["expected_behavior"],
        "selector_tags": selector_tags,
        "selected_feature_tags": selector_tags,
        "selected_matched_selector_tags": selector_tags,
        "selected_missing_selector_tags": "",
        "case_reuse_count": "1",
        "exactness_audit_state": "covered_by_match_engine_exact",
        "coverage_credit": "match_engine_exact_requirement_credit",
        "next_action": "none_covered_by_match_engine_exact",
        "audit_reason": (
            "match-engine result exact case is selector-complete, unique for "
            "the requirement row, linked to the ECMA-262 runtime source clause, "
            "and covered by the executable result-observability gate"
        ),
    }


def exec_result_matching_exact_plan_is_creditable(plan: dict[str, str]) -> bool:
    return (
        plan["plan_state"] == "planned_not_executable"
        and plan["coverage_credit"] == "none_exec_result_matching_exact_planned"
    )


def validate_exec_result_matching_exact_plan_row(plan: dict[str, str]) -> None:
    requirement_id = plan["requirement_id"]
    expected = {
        "mapping_family": "exec_result_matching",
        "executable_layer": "exec_result",
    }
    for field, expected_value in expected.items():
        if plan[field] != expected_value:
            raise SystemExit(
                f"exec-result matching exact plan row {requirement_id} has "
                f"{field}={plan[field]!r}; expected {expected_value!r}"
            )
    for field in [
        "source_file",
        "section_anchor",
        "result_subfamily",
        "result_semantic_route",
        "exact_case_family",
        "exact_case_id",
        "exact_case_obligation",
        "observability_status",
        "observability_reason",
    ]:
        if not plan[field]:
            raise SystemExit(
                f"exec-result matching exact plan row {requirement_id} has empty {field}"
            )
    if not plan["exact_case_id"].startswith(
        f"exec-result-matching-exact:{requirement_id}:"
    ):
        raise SystemExit(
            f"exec-result matching exact plan row {requirement_id} has invalid "
            f"exact_case_id {plan['exact_case_id']!r}"
        )
    if not Path(plan["source_file"]).is_file():
        raise SystemExit(
            f"exec-result matching exact plan row {requirement_id} source is "
            f"missing: {plan['source_file']}"
        )
    if exec_result_matching_exact_plan_is_creditable(plan):
        expected_creditable = {
            "target_test_artifact": EXEC_RESULT_MATCHING_EXACT_TARGET_TEST_ARTIFACT,
            "observability_status": "internal_exec_result_matching_model_observable",
            "next_action": "materialize_exec_result_matching_exact_case",
        }
        for field, expected_value in expected_creditable.items():
            if plan[field] != expected_value:
                raise SystemExit(
                    f"exec-result matching exact plan row {requirement_id} has "
                    f"{field}={plan[field]!r}; expected {expected_value!r}"
                )
        for field in [
            "pattern",
            "input_text",
            "expected_behavior",
            "expected_model_field",
            "model_scenario",
        ]:
            if not plan[field]:
                raise SystemExit(
                    f"exec-result matching exact plan row {requirement_id} has empty {field}"
                )
        if plan["expected_behavior"] != plan["expected_model_field"]:
            raise SystemExit(
                f"exec-result matching exact plan row {requirement_id} has "
                f"expected_behavior={plan['expected_behavior']!r}; expected "
                f"expected_model_field={plan['expected_model_field']!r}"
            )
        if plan["expected_exec_result"] not in {"true", "false", "not_applicable"}:
            raise SystemExit(
                f"exec-result matching exact plan row {requirement_id} has "
                f"invalid expected_exec_result={plan['expected_exec_result']!r}"
            )
        if plan["expected_exec_result"] == "true":
            for field in [
                "expected_start_index",
                "expected_end_index",
                "expected_match_text",
            ]:
                if not plan[field]:
                    raise SystemExit(
                        f"exec-result matching exact plan row {requirement_id} has empty {field}"
                    )
            for field in ["expected_start_index", "expected_end_index"]:
                try:
                    int(plan[field])
                except ValueError as exc:
                    raise SystemExit(
                        f"exec-result matching exact plan row {requirement_id} has "
                        f"invalid {field}={plan[field]!r}"
                    ) from exc
        else:
            for field in [
                "expected_start_index",
                "expected_end_index",
                "expected_match_text",
            ]:
                if plan[field]:
                    raise SystemExit(
                        f"exec-result matching exact plan row {requirement_id} has "
                        f"{field}={plan[field]!r}; expected empty for "
                        f"expected_exec_result={plan['expected_exec_result']!r}"
                    )
        if not Path(plan["target_test_artifact"]).is_file():
            raise SystemExit(
                f"exec-result matching exact plan row {requirement_id} target "
                f"artifact is missing: {plan['target_test_artifact']}"
            )
    else:
        expected_deferred = {
            "coverage_credit": "none_exec_result_matching_exact_deferred",
            "expected_exec_result": "not_observable",
            "pattern": "",
            "input_text": "",
            "expected_start_index": "",
            "expected_end_index": "",
            "expected_match_text": "",
            "expected_model_field": "",
            "model_scenario": "",
            "target_test_artifact": "",
        }
        for field, expected_value in expected_deferred.items():
            if plan[field] != expected_value:
                raise SystemExit(
                    f"deferred exec-result matching exact plan row {requirement_id} "
                    f"has {field}={plan[field]!r}; expected {expected_value!r}"
                )
        if not plan["plan_state"].startswith("deferred_"):
            raise SystemExit(
                f"exec-result matching exact plan row {requirement_id} has "
                f"uncreditable non-deferred state {plan['plan_state']!r}"
            )


def exec_result_matching_exact_audit_row(plan: dict[str, str]) -> dict[str, str]:
    validate_exec_result_matching_exact_plan_row(plan)
    if not exec_result_matching_exact_plan_is_creditable(plan):
        raise SystemExit(
            f"exec-result matching exact plan row {plan['requirement_id']} is not creditable"
        )
    requirement_id = plan["requirement_id"]
    selector_tags = (
        "regexp_exec_and_captures,regexp_runtime_exec_result,"
        "regexp_exec_result_matching"
    )
    return {
        "audit_id": f"exactness:{requirement_id}:{plan['exact_case_id']}",
        "audit_scope": "ecma262_requirement",
        "requirement_id": requirement_id,
        "mapping_family": plan["mapping_family"],
        "executable_layer": plan["executable_layer"],
        "evidence_kind": "exec_result_matching_exact_case",
        "case_id": plan["exact_case_id"],
        "case_source": f"{plan['source_file']}#{plan['section_anchor']}",
        "expected_behavior": plan["expected_behavior"],
        "selector_tags": selector_tags,
        "selected_feature_tags": selector_tags,
        "selected_matched_selector_tags": selector_tags,
        "selected_missing_selector_tags": "",
        "case_reuse_count": "1",
        "exactness_audit_state": "covered_by_exec_result_exact",
        "coverage_credit": "exec_result_exact_requirement_credit",
        "next_action": "none_covered_by_exec_result_exact",
        "audit_reason": (
            "exec-result matching exact case is selector-complete, unique for "
            "the RegExpExec/RegExpBuiltinExec requirement row, linked to the "
            "ECMA-262 runtime source clause, and covered by the executable "
            "public exec result gate"
        ),
    }


def exec_result_exec_exact_plan_is_creditable(plan: dict[str, str]) -> bool:
    return (
        plan["plan_state"] == "planned_not_executable"
        and plan["coverage_credit"] == "none_exec_result_exec_exact_planned"
    )


def validate_exec_result_exec_exact_plan_row(plan: dict[str, str]) -> None:
    requirement_id = plan["requirement_id"]
    expected = {
        "mapping_family": "exec_result_exec",
        "executable_layer": "exec_result",
        "coverage_credit": "none_exec_result_exec_exact_planned",
        "plan_state": "planned_not_executable",
        "target_test_artifact": EXEC_RESULT_EXEC_EXACT_TARGET_TEST_ARTIFACT,
        "observability_status": "internal_exec_result_exec_model_observable",
        "next_action": "materialize_exec_result_exec_exact_case",
    }
    for field, expected_value in expected.items():
        if plan[field] != expected_value:
            raise SystemExit(
                f"exec-result exec exact plan row {requirement_id} has "
                f"{field}={plan[field]!r}; expected {expected_value!r}"
            )
    allowed_routes = {
        ("regexp_prototype_exec", "exec_method_model"),
        ("regexp_prototype_test", "test_method_model"),
        ("match_record", "match_record_model"),
        ("get_match_string", "get_match_string_model"),
    }
    route = (plan["result_subfamily"], plan["result_semantic_route"])
    if route not in allowed_routes:
        raise SystemExit(
            f"exec-result exec exact plan row {requirement_id} has "
            f"unsupported route {route!r}"
        )
    if plan["expected_behavior"] not in {
        "regexp_prototype_exec_result_shape_observable",
        "regexp_prototype_exec_operation_observable",
        "regexp_prototype_exec_this_value_observable",
        "regexp_prototype_exec_requires_matcher_slot",
        "regexp_prototype_exec_string_argument_observable",
        "regexp_prototype_exec_delegates_to_builtin_exec",
        "regexp_prototype_test_operation_observable",
        "regexp_prototype_test_this_value_observable",
        "regexp_prototype_test_receiver_type_enforced",
        "regexp_prototype_test_string_argument_observable",
        "regexp_prototype_test_calls_regexp_exec",
        "regexp_prototype_test_returns_false_for_null",
        "regexp_prototype_test_returns_true_for_match",
        "match_record_encapsulates_start_end_indices",
        "match_record_fields_list_observable",
        "match_record_field_table_observable",
        "match_record_start_index_non_negative",
        "match_record_end_index_after_start",
        "get_match_string_operation_observable",
        "get_match_string_range_assertion",
        "get_match_string_returns_substring",
    }:
        raise SystemExit(
            f"exec-result exec exact plan row {requirement_id} has "
            f"expected_behavior={plan['expected_behavior']!r}"
        )
    for field in [
        "source_file",
        "section_anchor",
        "result_subfamily",
        "result_semantic_route",
        "exact_case_family",
        "exact_case_id",
        "pattern",
        "input_text",
        "expected_exec_result",
        "expected_test_result",
        "expected_behavior",
        "expected_model_field",
        "exact_case_obligation",
        "observability_reason",
    ]:
        if not plan[field]:
            raise SystemExit(
                f"exec-result exec exact plan row {requirement_id} has empty {field}"
            )
    if not plan["exact_case_id"].startswith(
        f"exec-result-exec-exact:{requirement_id}:"
    ):
        raise SystemExit(
            f"exec-result exec exact plan row {requirement_id} has invalid "
            f"exact_case_id {plan['exact_case_id']!r}"
        )
    if plan["expected_exec_result"] not in {"true", "false"}:
        raise SystemExit(
            f"exec-result exec exact plan row {requirement_id} has "
            f"expected_exec_result={plan['expected_exec_result']!r}"
        )
    if plan["expected_test_result"] not in {"true", "false", "not_applicable"}:
        raise SystemExit(
            f"exec-result exec exact plan row {requirement_id} has "
            f"expected_test_result={plan['expected_test_result']!r}"
        )
    if plan["expected_exec_result"] == "true":
        for field in ["expected_start_index", "expected_end_index"]:
            if not plan[field]:
                raise SystemExit(
                    f"exec-result exec exact plan row {requirement_id} has empty {field}"
                )
            try:
                int(plan[field])
            except ValueError as exc:
                raise SystemExit(
                    f"exec-result exec exact plan row {requirement_id} has "
                    f"invalid {field}={plan[field]!r}"
                ) from exc
        if not plan["expected_match_text"]:
            raise SystemExit(
                f"exec-result exec exact plan row {requirement_id} has empty "
                "expected_match_text"
            )
    else:
        for field in [
            "expected_start_index",
            "expected_end_index",
            "expected_match_text",
        ]:
            if plan[field]:
                raise SystemExit(
                    f"exec-result exec exact plan row {requirement_id} has "
                    f"{field}={plan[field]!r}; expected empty for no match"
                )
    if not Path(plan["source_file"]).is_file():
        raise SystemExit(
            f"exec-result exec exact plan row {requirement_id} source is "
            f"missing: {plan['source_file']}"
        )
    if not Path(plan["target_test_artifact"]).is_file():
        raise SystemExit(
            f"exec-result exec exact plan row {requirement_id} target "
            f"artifact is missing: {plan['target_test_artifact']}"
        )


def exec_result_exec_exact_audit_row(plan: dict[str, str]) -> dict[str, str]:
    validate_exec_result_exec_exact_plan_row(plan)
    requirement_id = plan["requirement_id"]
    selector_tags = (
        "regexp_exec_and_captures,regexp_runtime_exec_result,"
        "regexp_exec_result_exec"
    )
    return {
        "audit_id": f"exactness:{requirement_id}:{plan['exact_case_id']}",
        "audit_scope": "ecma262_requirement",
        "requirement_id": requirement_id,
        "mapping_family": plan["mapping_family"],
        "executable_layer": plan["executable_layer"],
        "evidence_kind": "exec_result_exec_exact_case",
        "case_id": plan["exact_case_id"],
        "case_source": f"{plan['source_file']}#{plan['section_anchor']}",
        "expected_behavior": plan["expected_behavior"],
        "selector_tags": selector_tags,
        "selected_feature_tags": selector_tags,
        "selected_matched_selector_tags": selector_tags,
        "selected_missing_selector_tags": "",
        "case_reuse_count": "1",
        "exactness_audit_state": "covered_by_exec_result_exact",
        "coverage_credit": "exec_result_exact_requirement_credit",
        "next_action": "none_covered_by_exec_result_exact",
        "audit_reason": (
            "exec-result exec exact case is selector-complete, unique for the "
            "RegExp.prototype.exec/test, Match Record, or GetMatchString "
            "requirement row, linked to the ECMA-262 runtime source clause, "
            "and covered by the executable internal exec-result exec model gate"
        ),
    }


def exec_result_instances_exact_plan_is_creditable(plan: dict[str, str]) -> bool:
    return (
        plan["plan_state"] == "planned_not_executable"
        and plan["coverage_credit"] == "none_exec_result_instances_exact_planned"
    )


def validate_exec_result_instances_exact_plan_row(plan: dict[str, str]) -> None:
    requirement_id = plan["requirement_id"]
    expected = {
        "mapping_family": "exec_result_instances",
        "executable_layer": "exec_result",
        "coverage_credit": "none_exec_result_instances_exact_planned",
        "plan_state": "planned_not_executable",
        "target_test_artifact": EXEC_RESULT_INSTANCES_EXACT_TARGET_TEST_ARTIFACT,
        "observability_status": "internal_exec_result_instance_model_observable",
        "next_action": "materialize_exec_result_instances_exact_case",
    }
    for field, expected_value in expected.items():
        if plan[field] != expected_value:
            raise SystemExit(
                f"exec-result instances exact plan row {requirement_id} has "
                f"{field}={plan[field]!r}; expected {expected_value!r}"
            )
    allowed_routes = {
        ("regexp_instance_internal_slots", "instance_slots_model"),
        ("regexp_instance_property_inventory", "last_index_property_model"),
        ("last_index_property", "last_index_property_attributes_model"),
    }
    route = (plan["result_subfamily"], plan["result_semantic_route"])
    if route not in allowed_routes:
        raise SystemExit(
            f"exec-result instances exact plan row {requirement_id} has "
            f"unsupported route {route!r}"
        )
    if plan["expected_behavior"] not in {
        "regexp_instance_internal_slots_observed",
        "regexp_instance_last_index_property_observed",
        "last_index_integral_start_property_attributes_observed",
    }:
        raise SystemExit(
            f"exec-result instances exact plan row {requirement_id} has "
            f"expected_behavior={plan['expected_behavior']!r}"
        )
    if plan["expected_behavior"] != plan["expected_model_field"]:
        raise SystemExit(
            f"exec-result instances exact plan row {requirement_id} has "
            f"expected_behavior={plan['expected_behavior']!r}; expected "
            f"expected_model_field={plan['expected_model_field']!r}"
        )
    for field in [
        "source_file",
        "section_anchor",
        "result_subfamily",
        "result_semantic_route",
        "exact_case_family",
        "exact_case_id",
        "pattern",
        "flags",
        "input_text",
        "expected_original_source",
        "expected_original_flags",
        "expected_internal_slots",
        "expected_last_index_initial_value",
        "expected_last_index_writable",
        "expected_last_index_enumerable",
        "expected_last_index_configurable",
        "expected_behavior",
        "expected_model_field",
        "exact_case_obligation",
        "observability_reason",
    ]:
        if not plan[field]:
            raise SystemExit(
                f"exec-result instances exact plan row {requirement_id} has "
                f"empty {field}"
            )
    if not plan["exact_case_id"].startswith(
        f"exec-result-instances-exact:{requirement_id}:"
    ):
        raise SystemExit(
            f"exec-result instances exact plan row {requirement_id} has invalid "
            f"exact_case_id {plan['exact_case_id']!r}"
        )
    try:
        int(plan["expected_last_index_initial_value"])
    except ValueError as exc:
        raise SystemExit(
            f"exec-result instances exact plan row {requirement_id} has invalid "
            "expected_last_index_initial_value="
            f"{plan['expected_last_index_initial_value']!r}"
        ) from exc
    for field in [
        "expected_last_index_writable",
        "expected_last_index_enumerable",
        "expected_last_index_configurable",
    ]:
        if plan[field] not in {"true", "false"}:
            raise SystemExit(
                f"exec-result instances exact plan row {requirement_id} has "
                f"{field}={plan[field]!r}"
            )
    if not Path(plan["source_file"]).is_file():
        raise SystemExit(
            f"exec-result instances exact plan row {requirement_id} source is "
            f"missing: {plan['source_file']}"
        )
    if not Path(plan["target_test_artifact"]).is_file():
        raise SystemExit(
            f"exec-result instances exact plan row {requirement_id} target "
            f"artifact is missing: {plan['target_test_artifact']}"
        )


def exec_result_instances_exact_audit_row(plan: dict[str, str]) -> dict[str, str]:
    validate_exec_result_instances_exact_plan_row(plan)
    requirement_id = plan["requirement_id"]
    selector_tags = (
        "regexp_exec_and_captures,regexp_runtime_exec_result,"
        "regexp_exec_result_instances"
    )
    return {
        "audit_id": f"exactness:{requirement_id}:{plan['exact_case_id']}",
        "audit_scope": "ecma262_requirement",
        "requirement_id": requirement_id,
        "mapping_family": plan["mapping_family"],
        "executable_layer": plan["executable_layer"],
        "evidence_kind": "exec_result_instances_exact_case",
        "case_id": plan["exact_case_id"],
        "case_source": f"{plan['source_file']}#{plan['section_anchor']}",
        "expected_behavior": plan["expected_behavior"],
        "selector_tags": selector_tags,
        "selected_feature_tags": selector_tags,
        "selected_matched_selector_tags": selector_tags,
        "selected_missing_selector_tags": "",
        "case_reuse_count": "1",
        "exactness_audit_state": "covered_by_exec_result_exact",
        "coverage_credit": "exec_result_exact_requirement_credit",
        "next_action": "none_covered_by_exec_result_exact",
        "audit_reason": (
            "exec-result instances exact case is selector-complete, unique for "
            "the RegExp instance internal-slot or lastIndex requirement row, "
            "linked to the ECMA-262 runtime source clause, and covered by the "
            "executable internal instance model gate"
        ),
    }


def spec_model_exact_plan_is_creditable(plan: dict[str, str]) -> bool:
    return (
        plan["plan_state"] == "planned_not_executable"
        and plan["coverage_credit"] == "none_spec_model_exact_planned"
    )


def validate_spec_model_exact_plan_row(plan: dict[str, str]) -> None:
    requirement_id = plan["requirement_id"]
    expected = {
        "mapping_family": "spec_model_local_exact",
        "executable_layer": "spec_model",
        "coverage_credit": "none_spec_model_exact_planned",
        "plan_state": "planned_not_executable",
        "target_test_artifact": SPEC_MODEL_EXACT_TARGET_TEST_ARTIFACT,
        "observability_status": "internal_spec_model_observable",
        "next_action": "materialize_spec_model_exact_case",
    }
    for field, expected_value in expected.items():
        if plan[field] != expected_value:
            raise SystemExit(
                f"spec-model exact plan row {requirement_id} has "
                f"{field}={plan[field]!r}; expected {expected_value!r}"
            )
    allowed_routes = {
        ("lexical_grammar_source_model", "source_character_goal_symbols"),
        ("syntactic_token_stream_policy", "token_stream_boundary_policy"),
        ("regexp_grammar_pattern_model", "source_character_pattern_goal"),
        ("grammar_notation_boundary_model", "lexical_regexp_shared_productions"),
    }
    route = (plan["spec_model_subfamily"], plan["spec_model_route"])
    if route not in allowed_routes:
        raise SystemExit(
            f"spec-model exact plan row {requirement_id} has "
            f"unsupported route {route!r}"
        )
    if plan["expected_behavior"] not in {
        "lexical_grammar_source_character_goal_model_observed",
        "syntactic_token_stream_boundary_policy_observed",
        "regexp_grammar_pattern_source_model_observed",
        "lexical_regexp_grammar_notation_boundary_observed",
    }:
        raise SystemExit(
            f"spec-model exact plan row {requirement_id} has "
            f"expected_behavior={plan['expected_behavior']!r}"
        )
    if plan["expected_behavior"] != plan["expected_model_field"]:
        raise SystemExit(
            f"spec-model exact plan row {requirement_id} has "
            f"expected_behavior={plan['expected_behavior']!r}; expected "
            f"expected_model_field={plan['expected_model_field']!r}"
        )
    if plan["expected_lexical_goal_symbols"] != (
        "InputElementDiv,InputElementTemplateTail,InputElementRegExp,"
        "InputElementRegExpOrTemplateTail,InputElementHashbangOrRegExp"
    ):
        raise SystemExit(
            f"spec-model exact plan row {requirement_id} has invalid "
            "expected_lexical_goal_symbols"
        )
    if plan["expected_regexp_goal_symbol"] != "Pattern":
        raise SystemExit(
            f"spec-model exact plan row {requirement_id} has "
            f"expected_regexp_goal_symbol={plan['expected_regexp_goal_symbol']!r}"
        )
    if plan["expected_regexp_clause"] != "22.2.1":
        raise SystemExit(
            f"spec-model exact plan row {requirement_id} has "
            f"expected_regexp_clause={plan['expected_regexp_clause']!r}"
        )
    for field in [
        "source_file",
        "section_anchor",
        "spec_model_subfamily",
        "spec_model_route",
        "exact_case_family",
        "exact_case_id",
        "model_scenario",
        "source_text",
        "expected_source_code_point_count",
        "expected_utf16_code_unit_length",
        "expected_lexical_goal_symbols",
        "expected_regexp_goal_symbol",
        "expected_regexp_clause",
        "expected_behavior",
        "expected_model_field",
        "exact_case_obligation",
        "observability_reason",
    ]:
        if not plan[field]:
            raise SystemExit(
                f"spec-model exact plan row {requirement_id} has empty {field}"
            )
    if not plan["exact_case_id"].startswith(f"spec-model-exact:{requirement_id}:"):
        raise SystemExit(
            f"spec-model exact plan row {requirement_id} has invalid "
            f"exact_case_id {plan['exact_case_id']!r}"
        )
    try:
        int(plan["expected_source_code_point_count"])
        int(plan["expected_utf16_code_unit_length"])
    except ValueError as exc:
        raise SystemExit(
            f"spec-model exact plan row {requirement_id} has invalid source "
            "length expectation"
        ) from exc
    if not Path(plan["source_file"]).is_file():
        raise SystemExit(
            f"spec-model exact plan row {requirement_id} source is missing: "
            f"{plan['source_file']}"
        )
    if not Path(plan["target_test_artifact"]).is_file():
        raise SystemExit(
            f"spec-model exact plan row {requirement_id} target artifact is "
            f"missing: {plan['target_test_artifact']}"
        )


def spec_model_exact_audit_row(plan: dict[str, str]) -> dict[str, str]:
    validate_spec_model_exact_plan_row(plan)
    requirement_id = plan["requirement_id"]
    selector_tags = (
        "regexp_pattern_syntax_positive,regexp_spec_model,"
        "regexp_grammar_model"
    )
    return {
        "audit_id": f"exactness:{requirement_id}:{plan['exact_case_id']}",
        "audit_scope": "ecma262_requirement",
        "requirement_id": requirement_id,
        "mapping_family": plan["mapping_family"],
        "executable_layer": plan["executable_layer"],
        "evidence_kind": "spec_model_exact_case",
        "case_id": plan["exact_case_id"],
        "case_source": f"{plan['source_file']}#{plan['section_anchor']}",
        "expected_behavior": plan["expected_behavior"],
        "selector_tags": selector_tags,
        "selected_feature_tags": selector_tags,
        "selected_matched_selector_tags": selector_tags,
        "selected_missing_selector_tags": "",
        "case_reuse_count": "1",
        "exactness_audit_state": "covered_by_spec_model_exact",
        "coverage_credit": "spec_model_exact_requirement_credit",
        "next_action": "none_covered_by_spec_model_exact",
        "audit_reason": (
            "spec-model exact case is unique for the ECMA-262 5.1.2 "
            "lexical/RegExp grammar model row, linked to the source clause, "
            "and covered by the executable internal spec-model gate"
        ),
    }


TEST262_LITERAL_LEXER_BEHAVIORS = {
    "literal_body_and_flags_reparsed",
    "literal_rejects_extended_flags",
    "regular_expression_literal_body_flags_observed",
    "regular_expression_body_first_char_chars_observed",
    "regular_expression_chars_empty_observed",
    "regular_expression_chars_recursive_observed",
    "regular_expression_first_char_nonterminator_observed",
    "regular_expression_first_char_backslash_sequence_observed",
    "regular_expression_first_char_class_observed",
    "regular_expression_char_nonterminator_observed",
    "regular_expression_char_backslash_sequence_observed",
    "regular_expression_char_class_observed",
    "regular_expression_backslash_sequence_nonterminator_observed",
    "regular_expression_nonterminator_rejects_line_terminator",
    "regular_expression_class_brackets_observed",
    "regular_expression_class_chars_empty_observed",
    "regular_expression_class_chars_recursive_observed",
    "regular_expression_class_char_nonterminator_observed",
    "regular_expression_class_char_backslash_sequence_observed",
    "regular_expression_flags_empty_observed",
    "regular_expression_flags_recursive_identifier_part_observed",
    "body_text_operation_source_text_observed",
    "body_text_production_literal_body_flags_observed",
    "body_text_returns_regular_expression_body_source_text",
    "regular_expression_literal_primary_expression_delegates_to_12_9_5",
}


def test262_literal_lexer_exact_case_is_creditable(row: dict[str, str]) -> bool:
    return (
        row["case_state"] == "planned_not_executable"
        and row["coverage_credit"]
        == "none_test262_literal_lexer_executable_planned"
    )


def validate_test262_literal_lexer_exact_case_row(row: dict[str, str]) -> None:
    requirement_id = row["requirement_id"]
    expected = {
        "mapping_family": "test262_literal_lexer",
        "executable_layer": "literal_lexer",
        "coverage_credit": "none_test262_literal_lexer_executable_planned",
        "case_state": "planned_not_executable",
        "target_test_artifact": TEST262_LITERAL_LEXER_TARGET_TEST_ARTIFACT,
        "next_action": "materialize_test262_literal_lexer_exact_case",
    }
    for field, expected_value in expected.items():
        if row[field] != expected_value:
            raise SystemExit(
                f"test262 literal-lexer exact row {requirement_id} has "
                f"{field}={row[field]!r}; expected {expected_value!r}"
            )
    if row["expected_behavior"] not in TEST262_LITERAL_LEXER_BEHAVIORS:
        raise SystemExit(
            f"test262 literal-lexer exact row {requirement_id} has "
            f"expected_behavior={row['expected_behavior']!r}"
        )
    if row["expected_parser_result"] == "literal_parse_ok":
        if row["expected_compile_result"] != "compile_ok":
            raise SystemExit(
                f"test262 literal-lexer exact row {requirement_id} has "
                f"expected_compile_result={row['expected_compile_result']!r}"
            )
        if not row["expected_pattern_text"]:
            raise SystemExit(
                f"test262 literal-lexer exact row {requirement_id} has empty "
                "expected_pattern_text"
            )
    elif row["expected_parser_result"] == "literal_parse_error":
        if row["expected_compile_result"] != "not_applicable":
            raise SystemExit(
                f"test262 literal-lexer parse-error row {requirement_id} has "
                f"expected_compile_result={row['expected_compile_result']!r}"
            )
        if row["expected_pattern_text"] or row["expected_flag_text"]:
            raise SystemExit(
                f"test262 literal-lexer parse-error row {requirement_id} has "
                "non-empty expected parsed output"
            )
    else:
        raise SystemExit(
            f"test262 literal-lexer exact row {requirement_id} has "
            f"expected_parser_result={row['expected_parser_result']!r}"
        )
    if row["literal_source_encoding"] not in {"plain", "escaped_line_feed"}:
        raise SystemExit(
            f"test262 literal-lexer exact row {requirement_id} has "
            f"literal_source_encoding={row['literal_source_encoding']!r}"
        )
    for field in [
        "case_id",
        "clause_id",
        "clause_title",
        "source_file",
        "section_anchor",
        "requirement_kind",
        "requirement_local_id",
        "requirement_text",
        "semantic_family",
        "product_surface",
        "source_path",
        "source_line",
        "source_snippet",
        "literal_source",
        "expected_parser_result",
        "expected_compile_result",
        "expected_behavior",
        "exact_case_obligation",
        "extractor_reason",
    ]:
        if not row[field]:
            raise SystemExit(
                f"test262 literal-lexer exact row {requirement_id} has empty {field}"
            )
    if not row["case_id"].startswith(
        f"test262-regexp-executable:{requirement_id}:"
    ):
        raise SystemExit(
            f"test262 literal-lexer exact row {requirement_id} has invalid "
            f"case_id {row['case_id']!r}"
        )
    try:
        source_line = int(row["source_line"])
    except ValueError as exc:
        raise SystemExit(
            f"test262 literal-lexer exact row {requirement_id} has invalid "
            f"source_line={row['source_line']!r}"
        ) from exc
    if source_line <= 0:
        raise SystemExit(
            f"test262 literal-lexer exact row {requirement_id} has non-positive "
            f"source_line={row['source_line']!r}"
        )
    if not Path("external/test262", row["source_path"]).is_file():
        raise SystemExit(
            f"test262 literal-lexer exact row {requirement_id} source is "
            f"missing: {row['source_path']}"
        )
    if not Path(row["source_file"]).is_file():
        raise SystemExit(
            f"test262 literal-lexer exact row {requirement_id} ECMA source is "
            f"missing: {row['source_file']}"
        )
    if not Path(row["target_test_artifact"]).is_file():
        raise SystemExit(
            f"test262 literal-lexer exact row {requirement_id} target artifact "
            f"is missing: {row['target_test_artifact']}"
        )


def test262_literal_lexer_exact_audit_row(row: dict[str, str]) -> dict[str, str]:
    validate_test262_literal_lexer_exact_case_row(row)
    requirement_id = row["requirement_id"]
    selector_tags = "regexp_literal_lexical_grammar,test262_literal_lexer"
    return {
        "audit_id": f"exactness:{requirement_id}:{row['case_id']}",
        "audit_scope": "ecma262_requirement",
        "requirement_id": requirement_id,
        "mapping_family": row["mapping_family"],
        "executable_layer": row["executable_layer"],
        "evidence_kind": "test262_literal_lexer_exact_case",
        "case_id": row["case_id"],
        "case_source": f"{row['source_path']}:{row['source_line']}",
        "expected_behavior": row["expected_behavior"],
        "selector_tags": selector_tags,
        "selected_feature_tags": selector_tags,
        "selected_matched_selector_tags": selector_tags,
        "selected_missing_selector_tags": "",
        "case_reuse_count": "1",
        "exactness_audit_state": "covered_by_test262_literal_lexer_exact",
        "coverage_credit": "test262_literal_lexer_requirement_credit",
        "next_action": "none_covered_by_test262_literal_lexer_exact",
        "audit_reason": (
            "test262 literal-lexer exact case is unique for the ECMA-262 "
            "RegExp literal lexical requirement row, linked to a concrete "
            "test262 source snippet, and covered by the executable literal "
            "parser gate"
        ),
    }


def exec_result_capture_exact_plan_is_creditable(plan: dict[str, str]) -> bool:
    return (
        plan["plan_state"] == "planned_not_executable"
        and plan["coverage_credit"] == "none_exec_result_capture_exact_planned"
    )


def validate_exec_result_capture_exact_plan_row(plan: dict[str, str]) -> None:
    requirement_id = plan["requirement_id"]
    expected = {
        "mapping_family": "exec_result_matching",
        "executable_layer": "exec_result",
        "result_subfamily": "builtin_exec_captures",
        "result_semantic_route": "capture_result_model",
        "expected_exec_result": "true",
        "coverage_credit": "none_exec_result_capture_exact_planned",
        "plan_state": "planned_not_executable",
        "target_test_artifact": EXEC_RESULT_CAPTURE_EXACT_TARGET_TEST_ARTIFACT,
        "observability_status": "internal_exec_result_capture_model_observable",
        "next_action": "materialize_exec_result_capture_exact_case",
    }
    for field, expected_value in expected.items():
        if plan[field] != expected_value:
            raise SystemExit(
                f"exec-result capture exact plan row {requirement_id} has "
                f"{field}={plan[field]!r}; expected {expected_value!r}"
            )
    if plan["expected_behavior"] not in {
        "exec_result_capture_count_observable",
        "exec_result_capture_count_matches_regexp_record",
        "exec_result_capture_count_within_array_limit",
        "exec_result_reads_capture_slot",
        "exec_result_detects_undefined_capture",
        "exec_result_returns_undefined_capture_value",
        "exec_result_takes_defined_capture_branch",
        "exec_result_exposes_capture_start",
        "exec_result_exposes_capture_end",
        "exec_result_builds_capture_match_record",
        "exec_result_extracts_captured_value",
        "exec_result_appends_capture_index_record",
        "exec_result_writes_capture_result_property",
    }:
        raise SystemExit(
            f"exec-result capture exact plan row {requirement_id} has "
            f"expected_behavior={plan['expected_behavior']!r}"
        )
    for field in [
        "source_file",
        "section_anchor",
        "exact_case_family",
        "exact_case_id",
        "pattern",
        "input_text",
        "expected_capture_count",
        "expected_capture_ordinal",
        "expected_capture_defined",
        "expected_behavior",
        "expected_model_field",
        "exact_case_obligation",
        "observability_reason",
    ]:
        if not plan[field]:
            raise SystemExit(
                f"exec-result capture exact plan row {requirement_id} has empty {field}"
            )
    if not plan["exact_case_id"].startswith(
        f"exec-result-capture-exact:{requirement_id}:"
    ):
        raise SystemExit(
            f"exec-result capture exact plan row {requirement_id} has invalid "
            f"exact_case_id {plan['exact_case_id']!r}"
        )
    for field in ["expected_capture_count", "expected_capture_ordinal"]:
        try:
            int(plan[field])
        except ValueError as exc:
            raise SystemExit(
                f"exec-result capture exact plan row {requirement_id} has "
                f"invalid {field}={plan[field]!r}"
            ) from exc
    if plan["expected_capture_defined"] not in {"true", "false"}:
        raise SystemExit(
            f"exec-result capture exact plan row {requirement_id} has "
            f"expected_capture_defined={plan['expected_capture_defined']!r}"
        )
    if plan["expected_capture_defined"] == "true":
        for field in [
            "expected_capture_start_index",
            "expected_capture_end_index",
            "expected_capture_text",
        ]:
            if not plan[field]:
                raise SystemExit(
                    f"exec-result capture exact plan row {requirement_id} has "
                    f"empty {field}"
                )
    else:
        for field in [
            "expected_capture_start_index",
            "expected_capture_end_index",
            "expected_capture_text",
        ]:
            if plan[field]:
                raise SystemExit(
                    f"exec-result capture exact plan row {requirement_id} has "
                    f"{field}={plan[field]!r}; expected empty for undefined capture"
                )
    if not Path(plan["source_file"]).is_file():
        raise SystemExit(
            f"exec-result capture exact plan row {requirement_id} source is "
            f"missing: {plan['source_file']}"
        )
    if not Path(plan["target_test_artifact"]).is_file():
        raise SystemExit(
            f"exec-result capture exact plan row {requirement_id} target "
            f"artifact is missing: {plan['target_test_artifact']}"
        )


def exec_result_capture_exact_audit_row(plan: dict[str, str]) -> dict[str, str]:
    validate_exec_result_capture_exact_plan_row(plan)
    requirement_id = plan["requirement_id"]
    selector_tags = (
        "regexp_exec_and_captures,regexp_runtime_exec_result,"
        "regexp_exec_result_matching,regexp_exec_result_captures"
    )
    return {
        "audit_id": f"exactness:{requirement_id}:{plan['exact_case_id']}",
        "audit_scope": "ecma262_requirement",
        "requirement_id": requirement_id,
        "mapping_family": plan["mapping_family"],
        "executable_layer": plan["executable_layer"],
        "evidence_kind": "exec_result_capture_exact_case",
        "case_id": plan["exact_case_id"],
        "case_source": f"{plan['source_file']}#{plan['section_anchor']}",
        "expected_behavior": plan["expected_behavior"],
        "selector_tags": selector_tags,
        "selected_feature_tags": selector_tags,
        "selected_matched_selector_tags": selector_tags,
        "selected_missing_selector_tags": "",
        "case_reuse_count": "1",
        "exactness_audit_state": "covered_by_exec_result_exact",
        "coverage_credit": "exec_result_exact_requirement_credit",
        "next_action": "none_covered_by_exec_result_exact",
        "audit_reason": (
            "exec-result capture exact case is selector-complete, unique for "
            "the RegExpBuiltinExec capture-result requirement row, linked to "
            "the ECMA-262 runtime source clause, and covered by the executable "
            "internal exec-result capture model gate"
        ),
    }


def exec_result_indices_exact_plan_is_creditable(plan: dict[str, str]) -> bool:
    return (
        plan["plan_state"] == "planned_not_executable"
        and plan["coverage_credit"] == "none_exec_result_indices_exact_planned"
    )


def validate_exec_result_indices_exact_plan_row(plan: dict[str, str]) -> None:
    requirement_id = plan["requirement_id"]
    expected = {
        "executable_layer": "exec_result",
        "expected_exec_result": "true",
        "coverage_credit": "none_exec_result_indices_exact_planned",
        "plan_state": "planned_not_executable",
        "target_test_artifact": EXEC_RESULT_INDICES_EXACT_TARGET_TEST_ARTIFACT,
        "observability_status": "internal_exec_result_indices_model_observable",
        "next_action": "materialize_exec_result_indices_exact_case",
    }
    for field, expected_value in expected.items():
        if plan[field] != expected_value:
            raise SystemExit(
                f"exec-result indices exact plan row {requirement_id} has "
                f"{field}={plan[field]!r}; expected {expected_value!r}"
            )
    allowed_routes = {
        ("exec_result_matching", "builtin_exec_indices", "indices_result_model"),
        ("exec_result_indices", "get_match_index_pair", "indices_index_pair_model"),
        (
            "exec_result_indices",
            "make_match_indices_index_pair_array",
            "indices_array_model",
        ),
    }
    route = (
        plan["mapping_family"],
        plan["result_subfamily"],
        plan["result_semantic_route"],
    )
    if route not in allowed_routes:
        raise SystemExit(
            f"exec-result indices exact plan row {requirement_id} has "
            f"unsupported route {route!r}"
        )
    if plan["expected_behavior"] not in {
        "exec_result_indices_list_initialized",
        "exec_result_group_names_list_initialized",
        "exec_result_appends_full_match_to_indices",
        "exec_result_appends_undefined_capture_to_indices",
        "exec_result_takes_has_indices_branch",
        "exec_result_builds_indices_array",
        "exec_result_writes_indices_property",
        "get_match_index_pair_operation_observable",
        "get_match_index_pair_range_assertion",
        "get_match_index_pair_returns_start_end_pair",
        "make_match_indices_array_operation_observable",
        "make_match_indices_reads_indices_length",
        "make_match_indices_length_within_array_limit",
        "make_match_indices_group_names_length_matches",
        "make_match_indices_group_names_aligned",
        "make_match_indices_creates_array",
        "make_match_indices_takes_has_groups_branch",
        "make_match_indices_creates_groups_object",
        "make_match_indices_takes_no_groups_branch",
        "make_match_indices_groups_undefined_without_groups",
        "make_match_indices_writes_groups_property",
        "make_match_indices_iterates_entries",
        "make_match_indices_reads_index_entry",
        "make_match_indices_takes_defined_entry_branch",
        "make_match_indices_calls_get_match_index_pair",
        "make_match_indices_takes_undefined_entry_branch",
        "make_match_indices_returns_undefined_pair",
        "make_match_indices_writes_numeric_property",
        "make_match_indices_takes_capture_entry_branch",
        "make_match_indices_reads_group_name",
        "make_match_indices_takes_named_group_branch",
        "make_match_indices_asserts_groups_object_for_name",
        "make_match_indices_allows_duplicate_group_property_write",
        "make_match_indices_writes_named_group_property",
        "make_match_indices_returns_array",
    }:
        raise SystemExit(
            f"exec-result indices exact plan row {requirement_id} has "
            f"expected_behavior={plan['expected_behavior']!r}"
        )
    for field in [
        "source_file",
        "section_anchor",
        "exact_case_family",
        "exact_case_id",
        "pattern",
        "flags",
        "input_text",
        "expected_indices_length",
        "expected_group_names_length",
        "expected_has_groups",
        "expected_entry_index",
        "expected_index_pair_defined",
        "expected_behavior",
        "expected_model_field",
        "exact_case_obligation",
        "observability_reason",
    ]:
        if not plan[field]:
            raise SystemExit(
                f"exec-result indices exact plan row {requirement_id} has empty {field}"
            )
    if plan["flags"] != "d":
        raise SystemExit(
            f"exec-result indices exact plan row {requirement_id} has "
            f"flags={plan['flags']!r}; expected 'd'"
        )
    if not plan["exact_case_id"].startswith(
        f"exec-result-indices-exact:{requirement_id}:"
    ):
        raise SystemExit(
            f"exec-result indices exact plan row {requirement_id} has invalid "
            f"exact_case_id {plan['exact_case_id']!r}"
        )
    for field in [
        "expected_indices_length",
        "expected_group_names_length",
        "expected_entry_index",
    ]:
        try:
            int(plan[field])
        except ValueError as exc:
            raise SystemExit(
                f"exec-result indices exact plan row {requirement_id} has "
                f"invalid {field}={plan[field]!r}"
            ) from exc
    for field in [
        "expected_has_groups",
        "expected_index_pair_defined",
        "expected_duplicate_group_name",
    ]:
        if plan[field] not in {"true", "false"}:
            raise SystemExit(
                f"exec-result indices exact plan row {requirement_id} has "
                f"{field}={plan[field]!r}"
            )
    if plan["expected_index_pair_defined"] == "true":
        for field in ["expected_index_pair_start", "expected_index_pair_end"]:
            if not plan[field]:
                raise SystemExit(
                    f"exec-result indices exact plan row {requirement_id} has "
                    f"empty {field}"
                )
            try:
                int(plan[field])
            except ValueError as exc:
                raise SystemExit(
                    f"exec-result indices exact plan row {requirement_id} has "
                    f"invalid {field}={plan[field]!r}"
                ) from exc
    else:
        for field in ["expected_index_pair_start", "expected_index_pair_end"]:
            if plan[field]:
                raise SystemExit(
                    f"exec-result indices exact plan row {requirement_id} has "
                    f"{field}={plan[field]!r}; expected empty for undefined pair"
                )
    if not Path(plan["source_file"]).is_file():
        raise SystemExit(
            f"exec-result indices exact plan row {requirement_id} source is "
            f"missing: {plan['source_file']}"
        )
    if not Path(plan["target_test_artifact"]).is_file():
        raise SystemExit(
            f"exec-result indices exact plan row {requirement_id} target "
            f"artifact is missing: {plan['target_test_artifact']}"
        )


def exec_result_indices_exact_audit_row(plan: dict[str, str]) -> dict[str, str]:
    validate_exec_result_indices_exact_plan_row(plan)
    requirement_id = plan["requirement_id"]
    selector_tags = (
        "regexp_exec_and_captures,regexp_runtime_exec_result,"
        "regexp_exec_result_matching,regexp_exec_result_indices,regexp_has_indices"
    )
    return {
        "audit_id": f"exactness:{requirement_id}:{plan['exact_case_id']}",
        "audit_scope": "ecma262_requirement",
        "requirement_id": requirement_id,
        "mapping_family": plan["mapping_family"],
        "executable_layer": plan["executable_layer"],
        "evidence_kind": "exec_result_indices_exact_case",
        "case_id": plan["exact_case_id"],
        "case_source": f"{plan['source_file']}#{plan['section_anchor']}",
        "expected_behavior": plan["expected_behavior"],
        "selector_tags": selector_tags,
        "selected_feature_tags": selector_tags,
        "selected_matched_selector_tags": selector_tags,
        "selected_missing_selector_tags": "",
        "case_reuse_count": "1",
        "exactness_audit_state": "covered_by_exec_result_exact",
        "coverage_credit": "exec_result_exact_requirement_credit",
        "next_action": "none_covered_by_exec_result_exact",
        "audit_reason": (
            "exec-result indices exact case is selector-complete, unique for "
            "the RegExpBuiltinExec/GetMatchIndexPair/MakeMatchIndicesIndexPairArray "
            "requirement row, linked to the ECMA-262 runtime source clause, "
            "and covered by the executable internal exec-result indices model gate"
        ),
    }


def validate_match_state_exact_plan_row(plan: dict[str, str]) -> None:
    requirement_id = plan["requirement_id"]
    expected = {
        "mapping_family": "match_engine_alternation",
        "executable_layer": "match_engine",
        "expected_behavior": "match_state_model_observable",
        "coverage_credit": "none_match_state_exact_planned",
        "plan_state": "planned_not_executable",
        "target_test_artifact": MATCH_STATE_EXACT_TARGET_TEST_ARTIFACT,
        "observability_status": "match_state_model_observable",
        "next_action": "materialize_match_state_exact_case",
    }
    for field, expected_value in expected.items():
        if plan[field] != expected_value:
            raise SystemExit(
                f"match-state exact plan row {requirement_id} has "
                f"{field}={plan[field]!r}; expected {expected_value!r}"
            )
    if plan["expected_observation"] not in {
        "match_two_alternatives_closure",
        "match_state_parameter",
        "matcher_continuation_parameter",
    }:
        raise SystemExit(
            f"match-state exact plan row {requirement_id} has "
            f"expected_observation={plan['expected_observation']!r}"
        )
    if plan["expected_observed"] != "true":
        raise SystemExit(
            f"match-state exact plan row {requirement_id} has "
            f"expected_observed={plan['expected_observed']!r}; expected 'true'"
        )
    for field in [
        "source_file",
        "section_anchor",
        "exact_case_family",
        "exact_case_id",
        "pattern",
        "input_text",
        "exact_case_obligation",
        "observability_reason",
    ]:
        if not plan[field]:
            raise SystemExit(
                f"match-state exact plan row {requirement_id} has empty {field}"
            )
    if not plan["exact_case_id"].startswith(
        f"match-state-exact:{requirement_id}:"
    ):
        raise SystemExit(
            f"match-state exact plan row {requirement_id} has invalid "
            f"exact_case_id {plan['exact_case_id']!r}"
        )
    if not Path(plan["source_file"]).is_file():
        raise SystemExit(
            f"match-state exact plan row {requirement_id} source is "
            f"missing: {plan['source_file']}"
        )
    if not Path(plan["target_test_artifact"]).is_file():
        raise SystemExit(
            f"match-state exact plan row {requirement_id} target artifact is "
            f"missing: {plan['target_test_artifact']}"
        )


def match_state_exact_audit_row(plan: dict[str, str]) -> dict[str, str]:
    validate_match_state_exact_plan_row(plan)
    requirement_id = plan["requirement_id"]
    selector_tags = "regexp_exec_and_captures,regexp_match_state_model"
    return {
        "audit_id": f"exactness:{requirement_id}:{plan['exact_case_id']}",
        "audit_scope": "ecma262_requirement",
        "requirement_id": requirement_id,
        "mapping_family": plan["mapping_family"],
        "executable_layer": plan["executable_layer"],
        "evidence_kind": "match_state_exact_case",
        "case_id": plan["exact_case_id"],
        "case_source": f"{plan['source_file']}#{plan['section_anchor']}",
        "expected_behavior": plan["expected_behavior"],
        "selector_tags": selector_tags,
        "selected_feature_tags": selector_tags,
        "selected_matched_selector_tags": selector_tags,
        "selected_missing_selector_tags": "",
        "case_reuse_count": "1",
        "exactness_audit_state": "covered_by_match_engine_exact",
        "coverage_credit": "match_engine_exact_requirement_credit",
        "next_action": "none_covered_by_match_engine_exact",
        "audit_reason": (
            "match-state exact case is selector-complete, unique for the "
            "requirement row, linked to the ECMA-262 runtime source clause, "
            "and covered by the executable MatchState/MatcherContinuation "
            "model gate"
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache", default="cache")
    parser.add_argument(
        "--selection",
        default="cache/ecma262-regexp-compile-parser-test-selection.tsv",
    )
    parser.add_argument(
        "--negative-syntax",
        default="cache/test262-regexp-negative-syntax-cases.tsv",
    )
    parser.add_argument(
        "--local-exact-plan",
        default="cache/ecma262-regexp-local-exact-plan.tsv",
    )
    parser.add_argument(
        "--selector-gap-worklist",
        default="cache/ecma262-regexp-selector-gap-worklist.tsv",
    )
    parser.add_argument(
        "--reused-candidate-exact-plan",
        default="cache/ecma262-regexp-reused-candidate-exact-plan.tsv",
    )
    parser.add_argument(
        "--compile-parser-exact-plan",
        default="cache/ecma262-regexp-compile-parser-exact-plan.tsv",
    )
    parser.add_argument(
        "--literal-lexer-exact-plan",
        default="cache/ecma262-regexp-literal-lexer-exact-plan.tsv",
    )
    parser.add_argument(
        "--match-engine-exact-plan",
        default="cache/ecma262-regexp-match-engine-exact-plan.tsv",
    )
    parser.add_argument(
        "--match-engine-atoms-exact-plan",
        default="cache/ecma262-regexp-match-engine-atoms-exact-plan.tsv",
    )
    parser.add_argument(
        "--match-engine-capture-exact-plan",
        default="cache/ecma262-regexp-match-engine-capture-exact-plan.tsv",
    )
    parser.add_argument(
        "--match-engine-unicode-sets-string-exact-plan",
        default=(
            "cache/ecma262-regexp-match-engine-unicode-sets-string-exact-plan.tsv"
        ),
    )
    parser.add_argument(
        "--match-engine-unicode-sets-escape-string-exact-plan",
        default=(
            "cache/ecma262-regexp-match-engine-unicode-sets-escape-string-exact-plan.tsv"
        ),
    )
    parser.add_argument(
        "--match-engine-character-classes-exact-plan",
        default=(
            "cache/ecma262-regexp-match-engine-character-classes-exact-plan.tsv"
        ),
    )
    parser.add_argument(
        "--match-engine-concatenation-exact-plan",
        default="cache/ecma262-regexp-match-engine-concatenation-exact-plan.tsv",
    )
    parser.add_argument(
        "--match-engine-backreference-exact-plan",
        default="cache/ecma262-regexp-match-engine-backreference-exact-plan.tsv",
    )
    parser.add_argument(
        "--match-engine-backreference-matcher-exact-plan",
        default=(
            "cache/ecma262-regexp-match-engine-backreference-matcher-exact-plan.tsv"
        ),
    )
    parser.add_argument(
        "--match-engine-result-exact-plan",
        default="cache/ecma262-regexp-match-engine-result-exact-plan.tsv",
    )
    parser.add_argument(
        "--exec-result-matching-exact-plan",
        default="cache/ecma262-regexp-exec-result-matching-exact-plan.tsv",
    )
    parser.add_argument(
        "--exec-result-capture-exact-plan",
        default="cache/ecma262-regexp-exec-result-capture-exact-plan.tsv",
    )
    parser.add_argument(
        "--exec-result-exec-exact-plan",
        default="cache/ecma262-regexp-exec-result-exec-exact-plan.tsv",
    )
    parser.add_argument(
        "--exec-result-indices-exact-plan",
        default="cache/ecma262-regexp-exec-result-indices-exact-plan.tsv",
    )
    parser.add_argument(
        "--exec-result-instances-exact-plan",
        default="cache/ecma262-regexp-exec-result-instances-exact-plan.tsv",
    )
    parser.add_argument(
        "--spec-model-exact-plan",
        default="cache/ecma262-regexp-spec-model-exact-plan.tsv",
    )
    parser.add_argument(
        "--test262-regexp-executable-cases",
        default="cache/test262-regexp-executable-cases.tsv",
    )
    parser.add_argument(
        "--match-engine-start-anchor-exact-plan",
        default="cache/ecma262-regexp-match-engine-start-anchor-exact-plan.tsv",
    )
    parser.add_argument(
        "--match-engine-end-anchor-exact-plan",
        default="cache/ecma262-regexp-match-engine-end-anchor-exact-plan.tsv",
    )
    parser.add_argument(
        "--match-engine-assertion-exact-plan",
        default="cache/ecma262-regexp-match-engine-assertion-exact-plan.tsv",
    )
    parser.add_argument(
        "--match-engine-quantifier-exact-plan",
        default="cache/ecma262-regexp-match-engine-quantifier-exact-plan.tsv",
    )
    parser.add_argument(
        "--match-engine-modifier-exact-plan",
        default="cache/ecma262-regexp-match-engine-modifier-exact-plan.tsv",
    )
    parser.add_argument(
        "--match-engine-pattern-semantics-exact-plan",
        default=(
            "cache/ecma262-regexp-match-engine-pattern-semantics-exact-plan.tsv"
        ),
    )
    parser.add_argument(
        "--match-engine-annex-b-exact-plan",
        default="cache/ecma262-regexp-match-engine-annex-b-exact-plan.tsv",
    )
    parser.add_argument(
        "--match-state-exact-plan",
        default="cache/ecma262-regexp-match-state-exact-plan.tsv",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    cache = Path(args.cache)
    selection = Path(args.selection)
    negative_syntax = Path(args.negative_syntax)
    local_exact_plan = Path(args.local_exact_plan)
    selector_gap_worklist = Path(args.selector_gap_worklist)
    reused_candidate_exact_plan = Path(args.reused_candidate_exact_plan)
    compile_parser_exact_plan = Path(args.compile_parser_exact_plan)
    literal_lexer_exact_plan = Path(args.literal_lexer_exact_plan)
    match_engine_exact_plan = Path(args.match_engine_exact_plan)
    match_engine_atoms_exact_plan = Path(args.match_engine_atoms_exact_plan)
    match_engine_capture_exact_plan = Path(args.match_engine_capture_exact_plan)
    match_engine_unicode_sets_string_exact_plan = Path(
        args.match_engine_unicode_sets_string_exact_plan
    )
    match_engine_unicode_sets_escape_string_exact_plan = Path(
        args.match_engine_unicode_sets_escape_string_exact_plan
    )
    match_engine_character_classes_exact_plan = Path(
        args.match_engine_character_classes_exact_plan
    )
    match_engine_concatenation_exact_plan = Path(
        args.match_engine_concatenation_exact_plan
    )
    match_engine_backreference_exact_plan = Path(
        args.match_engine_backreference_exact_plan
    )
    match_engine_backreference_matcher_exact_plan = Path(
        args.match_engine_backreference_matcher_exact_plan
    )
    match_engine_result_exact_plan = Path(args.match_engine_result_exact_plan)
    exec_result_matching_exact_plan = Path(args.exec_result_matching_exact_plan)
    exec_result_capture_exact_plan = Path(args.exec_result_capture_exact_plan)
    exec_result_exec_exact_plan = Path(args.exec_result_exec_exact_plan)
    exec_result_indices_exact_plan = Path(args.exec_result_indices_exact_plan)
    exec_result_instances_exact_plan = Path(args.exec_result_instances_exact_plan)
    spec_model_exact_plan = Path(args.spec_model_exact_plan)
    test262_regexp_executable_cases = Path(args.test262_regexp_executable_cases)
    match_engine_start_anchor_exact_plan = Path(
        args.match_engine_start_anchor_exact_plan
    )
    match_engine_end_anchor_exact_plan = Path(args.match_engine_end_anchor_exact_plan)
    match_engine_assertion_exact_plan = Path(args.match_engine_assertion_exact_plan)
    match_engine_quantifier_exact_plan = Path(args.match_engine_quantifier_exact_plan)
    match_engine_modifier_exact_plan = Path(args.match_engine_modifier_exact_plan)
    match_engine_pattern_semantics_exact_plan = Path(
        args.match_engine_pattern_semantics_exact_plan
    )
    match_engine_annex_b_exact_plan = Path(args.match_engine_annex_b_exact_plan)
    match_state_exact_plan = Path(args.match_state_exact_plan)
    detail = cache / DETAIL_NAME
    summary = cache / SUMMARY_NAME

    if not selection.is_file():
        raise SystemExit(
            f"missing compile/parser selection at {selection}; "
            "run tools/map_ecma262_compile_parser_candidates.py first"
        )
    if not negative_syntax.is_file():
        raise SystemExit(
            f"missing negative syntax cases at {negative_syntax}; "
            "run tools/extract_test262_regexp_negative_syntax.py first"
        )
    if not local_exact_plan.is_file():
        raise SystemExit(
            f"missing local exact plan at {local_exact_plan}; "
            "run tools/build_ecma262_regexp_local_exact_plan.py first"
        )
    if not selector_gap_worklist.is_file():
        raise SystemExit(
            f"missing selector-gap worklist at {selector_gap_worklist}; "
            "run tools/build_ecma262_regexp_selector_gap_worklist.py first"
        )
    if not reused_candidate_exact_plan.is_file():
        raise SystemExit(
            f"missing reused-candidate exact plan at {reused_candidate_exact_plan}; "
            "run tools/build_ecma262_regexp_reused_candidate_exact_plan.py first"
        )
    if not compile_parser_exact_plan.is_file():
        raise SystemExit(
            f"missing compile/parser exact plan at {compile_parser_exact_plan}; "
            "run tools/build_ecma262_regexp_compile_parser_exact_plan.py first"
        )
    if not literal_lexer_exact_plan.is_file():
        raise SystemExit(
            f"missing literal lexer exact plan at {literal_lexer_exact_plan}; "
            "run tools/build_ecma262_regexp_literal_lexer_exact_plan.py first"
        )
    if not match_engine_exact_plan.is_file():
        raise SystemExit(
            f"missing match-engine exact plan at {match_engine_exact_plan}; "
            "run tools/build_ecma262_regexp_match_engine_exact_plan.py first"
        )
    if not match_engine_atoms_exact_plan.is_file():
        raise SystemExit(
            "missing match-engine atoms exact plan at "
            f"{match_engine_atoms_exact_plan}; run "
            "tools/build_ecma262_regexp_match_engine_atoms_exact_plan.py first"
        )
    if not match_engine_capture_exact_plan.is_file():
        raise SystemExit(
            "missing match-engine capture exact plan at "
            f"{match_engine_capture_exact_plan}; run "
            "tools/build_ecma262_regexp_match_engine_capture_exact_plan.py first"
        )
    if not match_engine_unicode_sets_string_exact_plan.is_file():
        raise SystemExit(
            "missing match-engine UnicodeSets string exact plan at "
            f"{match_engine_unicode_sets_string_exact_plan}; run "
            "tools/build_ecma262_regexp_match_engine_unicode_sets_string_exact_plan.py "
            "first"
        )
    if not match_engine_unicode_sets_escape_string_exact_plan.is_file():
        raise SystemExit(
            "missing match-engine UnicodeSets escape string exact plan at "
            f"{match_engine_unicode_sets_escape_string_exact_plan}; run "
            "tools/build_ecma262_regexp_match_engine_unicode_sets_escape_string_exact_plan.py "
            "first"
        )
    if not match_engine_character_classes_exact_plan.is_file():
        raise SystemExit(
            "missing match-engine character-classes exact plan at "
            f"{match_engine_character_classes_exact_plan}; run "
            "tools/build_ecma262_regexp_match_engine_character_classes_exact_plan.py "
            "first"
        )
    if not match_engine_concatenation_exact_plan.is_file():
        raise SystemExit(
            "missing match-engine concatenation exact plan at "
            f"{match_engine_concatenation_exact_plan}; run "
            "tools/build_ecma262_regexp_match_engine_concatenation_exact_plan.py "
            "first"
        )
    if not match_engine_backreference_exact_plan.is_file():
        raise SystemExit(
            "missing match-engine backreference exact plan at "
            f"{match_engine_backreference_exact_plan}; run "
            "tools/build_ecma262_regexp_match_engine_backreference_exact_plan.py first"
        )
    if not match_engine_backreference_matcher_exact_plan.is_file():
        raise SystemExit(
            "missing match-engine BackreferenceMatcher exact plan at "
            f"{match_engine_backreference_matcher_exact_plan}; run "
            "tools/build_ecma262_regexp_match_engine_backreference_matcher_exact_plan.py "
            "first"
        )
    if not match_engine_result_exact_plan.is_file():
        raise SystemExit(
            "missing match-engine result exact plan at "
            f"{match_engine_result_exact_plan}; run "
            "tools/build_ecma262_regexp_match_engine_result_exact_plan.py first"
        )
    if not exec_result_matching_exact_plan.is_file():
        raise SystemExit(
            "missing exec-result matching exact plan at "
            f"{exec_result_matching_exact_plan}; run "
            "tools/build_ecma262_regexp_exec_result_matching_exact_plan.py first"
        )
    if not exec_result_capture_exact_plan.is_file():
        raise SystemExit(
            "missing exec-result capture exact plan at "
            f"{exec_result_capture_exact_plan}; run "
            "tools/build_ecma262_regexp_exec_result_capture_exact_plan.py first"
        )
    if not exec_result_exec_exact_plan.is_file():
        raise SystemExit(
            "missing exec-result exec exact plan at "
            f"{exec_result_exec_exact_plan}; run "
            "tools/build_ecma262_regexp_exec_result_exec_exact_plan.py first"
        )
    if not exec_result_indices_exact_plan.is_file():
        raise SystemExit(
            "missing exec-result indices exact plan at "
            f"{exec_result_indices_exact_plan}; run "
            "tools/build_ecma262_regexp_exec_result_indices_exact_plan.py first"
        )
    if not exec_result_instances_exact_plan.is_file():
        raise SystemExit(
            "missing exec-result instances exact plan at "
            f"{exec_result_instances_exact_plan}; run "
            "tools/build_ecma262_regexp_exec_result_instances_exact_plan.py first"
        )
    if not spec_model_exact_plan.is_file():
        raise SystemExit(
            f"missing spec-model exact plan at {spec_model_exact_plan}; run "
            "tools/build_ecma262_regexp_spec_model_exact_plan.py first"
        )
    if not test262_regexp_executable_cases.is_file():
        raise SystemExit(
            "missing test262 RegExp executable cases at "
            f"{test262_regexp_executable_cases}; run "
            "tools/extract_test262_regexp_executable_cases.py first"
        )
    if not match_engine_start_anchor_exact_plan.is_file():
        raise SystemExit(
            "missing match-engine start-anchor exact plan at "
            f"{match_engine_start_anchor_exact_plan}; run "
            "tools/build_ecma262_regexp_match_engine_start_anchor_exact_plan.py "
            "first"
        )
    if not match_engine_end_anchor_exact_plan.is_file():
        raise SystemExit(
            "missing match-engine end-anchor exact plan at "
            f"{match_engine_end_anchor_exact_plan}; run "
            "tools/build_ecma262_regexp_match_engine_end_anchor_exact_plan.py "
            "first"
        )
    if not match_engine_assertion_exact_plan.is_file():
        raise SystemExit(
            "missing match-engine assertion exact plan at "
            f"{match_engine_assertion_exact_plan}; run "
            "tools/build_ecma262_regexp_match_engine_assertion_exact_plan.py "
            "first"
        )
    if not match_engine_quantifier_exact_plan.is_file():
        raise SystemExit(
            "missing match-engine quantifier exact plan at "
            f"{match_engine_quantifier_exact_plan}; run "
            "tools/build_ecma262_regexp_match_engine_quantifier_exact_plan.py "
            "first"
        )
    if not match_engine_modifier_exact_plan.is_file():
        raise SystemExit(
            "missing match-engine modifier exact plan at "
            f"{match_engine_modifier_exact_plan}; run "
            "tools/build_ecma262_regexp_match_engine_modifier_exact_plan.py "
            "first"
        )
    if not match_engine_pattern_semantics_exact_plan.is_file():
        raise SystemExit(
            "missing match-engine Pattern Semantics exact plan at "
            f"{match_engine_pattern_semantics_exact_plan}; run "
            "tools/build_ecma262_regexp_match_engine_pattern_semantics_exact_plan.py "
            "first"
        )
    if not match_engine_annex_b_exact_plan.is_file():
        raise SystemExit(
            "missing match-engine Annex B exact plan at "
            f"{match_engine_annex_b_exact_plan}; run "
            "tools/build_ecma262_regexp_match_engine_annex_b_exact_plan.py first"
        )
    if not match_state_exact_plan.is_file():
        raise SystemExit(
            f"missing match-state exact plan at {match_state_exact_plan}; run "
            "tools/build_ecma262_regexp_match_state_exact_plan.py first"
        )

    selection_fields, selection_rows = read_tsv(selection)
    negative_fields, negative_rows = read_tsv(negative_syntax)
    local_exact_fields, local_exact_rows_list = read_tsv(local_exact_plan)
    selector_gap_fields, selector_gap_rows_list = read_tsv(selector_gap_worklist)
    reused_plan_fields, reused_plan_rows_list = read_tsv(reused_candidate_exact_plan)
    compile_parser_plan_fields, compile_parser_plan_rows_list = read_tsv(
        compile_parser_exact_plan
    )
    literal_lexer_plan_fields, literal_lexer_plan_rows_list = read_tsv(
        literal_lexer_exact_plan
    )
    match_engine_plan_fields, match_engine_plan_rows_list = read_tsv(
        match_engine_exact_plan
    )
    match_engine_atoms_plan_fields, match_engine_atoms_plan_rows_list = read_tsv(
        match_engine_atoms_exact_plan
    )
    (
        match_engine_capture_plan_fields,
        match_engine_capture_plan_rows_list,
    ) = read_tsv(match_engine_capture_exact_plan)
    (
        match_engine_unicode_sets_string_plan_fields,
        match_engine_unicode_sets_string_plan_rows_list,
    ) = read_tsv(match_engine_unicode_sets_string_exact_plan)
    (
        match_engine_unicode_sets_escape_string_plan_fields,
        match_engine_unicode_sets_escape_string_plan_rows_list,
    ) = read_tsv(match_engine_unicode_sets_escape_string_exact_plan)
    (
        match_engine_character_classes_plan_fields,
        match_engine_character_classes_plan_rows_list,
    ) = read_tsv(match_engine_character_classes_exact_plan)
    (
        match_engine_concatenation_plan_fields,
        match_engine_concatenation_plan_rows_list,
    ) = read_tsv(match_engine_concatenation_exact_plan)
    (
        match_engine_backreference_plan_fields,
        match_engine_backreference_plan_rows_list,
    ) = read_tsv(match_engine_backreference_exact_plan)
    (
        match_engine_backreference_matcher_plan_fields,
        match_engine_backreference_matcher_plan_rows_list,
    ) = read_tsv(match_engine_backreference_matcher_exact_plan)
    match_engine_result_plan_fields, match_engine_result_plan_rows_list = read_tsv(
        match_engine_result_exact_plan
    )
    exec_result_matching_plan_fields, exec_result_matching_plan_rows_list = read_tsv(
        exec_result_matching_exact_plan
    )
    exec_result_capture_plan_fields, exec_result_capture_plan_rows_list = read_tsv(
        exec_result_capture_exact_plan
    )
    exec_result_exec_plan_fields, exec_result_exec_plan_rows_list = read_tsv(
        exec_result_exec_exact_plan
    )
    exec_result_indices_plan_fields, exec_result_indices_plan_rows_list = read_tsv(
        exec_result_indices_exact_plan
    )
    (
        exec_result_instances_plan_fields,
        exec_result_instances_plan_rows_list,
    ) = read_tsv(exec_result_instances_exact_plan)
    spec_model_plan_fields, spec_model_plan_rows_list = read_tsv(
        spec_model_exact_plan
    )
    (
        test262_literal_lexer_fields,
        test262_literal_lexer_rows_list,
    ) = read_tsv(test262_regexp_executable_cases)
    (
        match_engine_start_anchor_plan_fields,
        match_engine_start_anchor_plan_rows_list,
    ) = read_tsv(match_engine_start_anchor_exact_plan)
    (
        match_engine_end_anchor_plan_fields,
        match_engine_end_anchor_plan_rows_list,
    ) = read_tsv(match_engine_end_anchor_exact_plan)
    (
        match_engine_assertion_plan_fields,
        match_engine_assertion_plan_rows_list,
    ) = read_tsv(match_engine_assertion_exact_plan)
    (
        match_engine_quantifier_plan_fields,
        match_engine_quantifier_plan_rows_list,
    ) = read_tsv(match_engine_quantifier_exact_plan)
    (
        match_engine_modifier_plan_fields,
        match_engine_modifier_plan_rows_list,
    ) = read_tsv(match_engine_modifier_exact_plan)
    (
        match_engine_pattern_semantics_plan_fields,
        match_engine_pattern_semantics_plan_rows_list,
    ) = read_tsv(match_engine_pattern_semantics_exact_plan)
    (
        match_engine_annex_b_plan_fields,
        match_engine_annex_b_plan_rows_list,
    ) = read_tsv(match_engine_annex_b_exact_plan)
    match_state_plan_fields, match_state_plan_rows_list = read_tsv(
        match_state_exact_plan
    )

    required_selection = {
        "requirement_id",
        "source_file",
        "section_anchor",
        "mapping_family",
        "executable_layer",
        "selection_state",
        "selected_case_id",
        "selected_case_source",
        "selected_pattern",
        "selected_flags",
        "selected_expected_behavior",
        "candidate_selector_tags",
        "selected_feature_tags",
        "selected_matched_selector_tags",
        "selected_missing_selector_tags",
    }
    missing_selection = required_selection.difference(selection_fields)
    if missing_selection:
        raise SystemExit(
            "missing required selection columns: "
            + ", ".join(sorted(missing_selection))
        )

    required_negative = {
        "source_path",
        "line",
        "expected_behavior",
    }
    missing_negative = required_negative.difference(negative_fields)
    if missing_negative:
        raise SystemExit(
            "missing required negative syntax columns: "
            + ", ".join(sorted(missing_negative))
        )

    required_local_exact = {
        "requirement_id",
        "source_file",
        "section_anchor",
        "mapping_family",
        "executable_layer",
        "selector_tags",
        "missing_selector_tags",
        "local_case_id",
        "local_case_family",
        "planned_pattern",
        "planned_flags",
        "expected_behavior",
        "coverage_credit",
        "plan_state",
        "target_test_artifact",
        "next_action",
    }
    missing_local_exact = required_local_exact.difference(local_exact_fields)
    if missing_local_exact:
        raise SystemExit(
            "missing required local exact columns: "
            + ", ".join(sorted(missing_local_exact))
        )

    required_selector_gap = {
        "requirement_id",
        "mapping_family",
        "executable_layer",
        "selector_tags",
        "missing_selector_tags",
        "selector_gap_state",
        "next_action",
    }
    missing_selector_gap = required_selector_gap.difference(selector_gap_fields)
    if missing_selector_gap:
        raise SystemExit(
            "missing required selector-gap columns: "
            + ", ".join(sorted(missing_selector_gap))
        )

    required_reused_plan = {
        "requirement_id",
        "source_file",
        "section_anchor",
        "mapping_family",
        "executable_layer",
        "selector_tags",
        "selected_feature_tags",
        "selected_case_id",
        "selected_case_source",
        "selected_pattern",
        "selected_flags",
        "exact_case_id",
        "planned_pattern",
        "planned_flags",
        "expected_behavior",
        "coverage_credit",
        "plan_state",
        "target_test_artifact",
        "implementation_pressure",
        "next_action",
    }
    missing_reused_plan = required_reused_plan.difference(reused_plan_fields)
    if missing_reused_plan:
        raise SystemExit(
            "missing required reused-candidate exact plan columns: "
            + ", ".join(sorted(missing_reused_plan))
        )

    required_compile_parser_plan = {
        "requirement_id",
        "source_file",
        "section_anchor",
        "mapping_family",
        "executable_layer",
        "selection_state",
        "selector_tags",
        "selected_case_id",
        "selected_case_source",
        "selected_pattern",
        "selected_flags",
        "exact_case_family",
        "exact_case_id",
        "planned_pattern",
        "planned_flags",
        "expected_behavior",
        "coverage_credit",
        "plan_state",
        "target_test_artifact",
        "exact_case_obligation",
        "next_action",
    }
    missing_compile_parser_plan = required_compile_parser_plan.difference(
        compile_parser_plan_fields
    )
    if missing_compile_parser_plan:
        raise SystemExit(
            "missing required compile/parser exact plan columns: "
            + ", ".join(sorted(missing_compile_parser_plan))
        )

    required_literal_lexer_plan = {
        "requirement_id",
        "source_file",
        "section_anchor",
        "mapping_family",
        "executable_layer",
        "exact_case_family",
        "exact_case_id",
        "literal_source",
        "expected_pattern_text",
        "expected_flag_text",
        "expected_behavior",
        "coverage_credit",
        "plan_state",
        "target_test_artifact",
        "exact_case_obligation",
        "next_action",
    }
    missing_literal_lexer_plan = required_literal_lexer_plan.difference(
        literal_lexer_plan_fields
    )
    if missing_literal_lexer_plan:
        raise SystemExit(
            "missing required literal lexer exact plan columns: "
            + ", ".join(sorted(missing_literal_lexer_plan))
        )

    required_match_engine_plan = {
        "requirement_id",
        "source_file",
        "section_anchor",
        "mapping_family",
        "executable_layer",
        "exact_case_family",
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
    }
    missing_match_engine_plan = required_match_engine_plan.difference(
        match_engine_plan_fields
    )
    if missing_match_engine_plan:
        raise SystemExit(
            "missing required match-engine exact plan columns: "
            + ", ".join(sorted(missing_match_engine_plan))
        )

    required_match_engine_atoms_plan = {
        "requirement_id",
        "source_file",
        "section_anchor",
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
    }
    missing_match_engine_atoms_plan = required_match_engine_atoms_plan.difference(
        match_engine_atoms_plan_fields
    )
    if missing_match_engine_atoms_plan:
        raise SystemExit(
            "missing required match-engine atoms exact plan columns: "
            + ", ".join(sorted(missing_match_engine_atoms_plan))
        )

    required_match_engine_capture_plan = {
        "source_atom_plan_id",
        "requirement_id",
        "source_file",
        "section_anchor",
        "mapping_family",
        "executable_layer",
        "capture_subfamily",
        "capture_semantic_route",
        "exact_case_family",
        "exact_case_id",
        "pattern",
        "flags",
        "input_text",
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
    }
    missing_match_engine_capture_plan = (
        required_match_engine_capture_plan.difference(
            match_engine_capture_plan_fields
        )
    )
    if missing_match_engine_capture_plan:
        raise SystemExit(
            "missing required match-engine capture exact plan columns: "
            + ", ".join(sorted(missing_match_engine_capture_plan))
        )

    required_match_engine_unicode_sets_string_plan = {
        "source_atom_plan_id",
        "requirement_id",
        "source_file",
        "section_anchor",
        "mapping_family",
        "executable_layer",
        "unicode_sets_subfamily",
        "unicode_sets_semantic_route",
        "exact_case_family",
        "exact_case_id",
        "pattern",
        "flags",
        "input_text",
        "expected_exec_text",
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
    }
    missing_match_engine_unicode_sets_string_plan = (
        required_match_engine_unicode_sets_string_plan.difference(
            match_engine_unicode_sets_string_plan_fields
        )
    )
    if missing_match_engine_unicode_sets_string_plan:
        raise SystemExit(
            "missing required match-engine UnicodeSets string exact plan columns: "
            + ", ".join(sorted(missing_match_engine_unicode_sets_string_plan))
        )

    required_match_engine_unicode_sets_escape_string_plan = {
        "source_atom_plan_id",
        "requirement_id",
        "source_file",
        "section_anchor",
        "mapping_family",
        "executable_layer",
        "unicode_sets_subfamily",
        "unicode_sets_semantic_route",
        "exact_case_family",
        "exact_case_id",
        "pattern",
        "flags",
        "input_text",
        "expected_exec_text",
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
    }
    missing_match_engine_unicode_sets_escape_string_plan = (
        required_match_engine_unicode_sets_escape_string_plan.difference(
            match_engine_unicode_sets_escape_string_plan_fields
        )
    )
    if missing_match_engine_unicode_sets_escape_string_plan:
        raise SystemExit(
            "missing required match-engine UnicodeSets escape string exact "
            "plan columns: "
            + ", ".join(
                sorted(missing_match_engine_unicode_sets_escape_string_plan)
            )
        )

    required_match_engine_character_classes_plan = {
        "requirement_id",
        "clause_id",
        "source_file",
        "section_anchor",
        "mapping_family",
        "executable_layer",
        "character_class_subfamily",
        "character_class_route",
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
    }
    missing_match_engine_character_classes_plan = (
        required_match_engine_character_classes_plan.difference(
            match_engine_character_classes_plan_fields
        )
    )
    if missing_match_engine_character_classes_plan:
        raise SystemExit(
            "missing required match-engine character-classes exact plan columns: "
            + ", ".join(sorted(missing_match_engine_character_classes_plan))
        )

    required_match_engine_concatenation_plan = {
        "requirement_id",
        "clause_id",
        "source_file",
        "section_anchor",
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
    }
    missing_match_engine_concatenation_plan = (
        required_match_engine_concatenation_plan.difference(
            match_engine_concatenation_plan_fields
        )
    )
    if missing_match_engine_concatenation_plan:
        raise SystemExit(
            "missing required match-engine concatenation exact plan columns: "
            + ", ".join(sorted(missing_match_engine_concatenation_plan))
        )

    required_match_engine_backreference_plan = {
        "source_atom_plan_id",
        "requirement_id",
        "source_file",
        "section_anchor",
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
    }
    missing_match_engine_backreference_plan = (
        required_match_engine_backreference_plan.difference(
            match_engine_backreference_plan_fields
        )
    )
    if missing_match_engine_backreference_plan:
        raise SystemExit(
            "missing required match-engine backreference exact plan columns: "
            + ", ".join(sorted(missing_match_engine_backreference_plan))
        )

    required_match_engine_backreference_matcher_plan = {
        "requirement_id",
        "clause_id",
        "source_file",
        "section_anchor",
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
    }
    missing_match_engine_backreference_matcher_plan = (
        required_match_engine_backreference_matcher_plan.difference(
            match_engine_backreference_matcher_plan_fields
        )
    )
    if missing_match_engine_backreference_matcher_plan:
        raise SystemExit(
            "missing required match-engine BackreferenceMatcher exact plan "
            "columns: "
            + ", ".join(sorted(missing_match_engine_backreference_matcher_plan))
        )

    required_match_engine_result_plan = {
        "requirement_id",
        "source_file",
        "section_anchor",
        "mapping_family",
        "executable_layer",
        "exact_case_family",
        "exact_case_id",
        "pattern",
        "flags",
        "input_text",
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
    }
    missing_match_engine_result_plan = required_match_engine_result_plan.difference(
        match_engine_result_plan_fields
    )
    if missing_match_engine_result_plan:
        raise SystemExit(
            "missing required match-engine result exact plan columns: "
            + ", ".join(sorted(missing_match_engine_result_plan))
        )

    required_exec_result_matching_plan = {
        "requirement_id",
        "source_file",
        "section_anchor",
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
    }
    missing_exec_result_matching_plan = required_exec_result_matching_plan.difference(
        exec_result_matching_plan_fields
    )
    if missing_exec_result_matching_plan:
        raise SystemExit(
            "missing required exec-result matching exact plan columns: "
            + ", ".join(sorted(missing_exec_result_matching_plan))
        )

    required_exec_result_capture_plan = {
        "requirement_id",
        "source_file",
        "section_anchor",
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
    }
    missing_exec_result_capture_plan = required_exec_result_capture_plan.difference(
        exec_result_capture_plan_fields
    )
    if missing_exec_result_capture_plan:
        raise SystemExit(
            "missing required exec-result capture exact plan columns: "
            + ", ".join(sorted(missing_exec_result_capture_plan))
        )

    required_exec_result_exec_plan = {
        "requirement_id",
        "source_file",
        "section_anchor",
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
        "expected_test_result",
        "expected_behavior",
        "expected_model_field",
        "coverage_credit",
        "plan_state",
        "target_test_artifact",
        "exact_case_obligation",
        "observability_status",
        "observability_reason",
        "next_action",
    }
    missing_exec_result_exec_plan = required_exec_result_exec_plan.difference(
        exec_result_exec_plan_fields
    )
    if missing_exec_result_exec_plan:
        raise SystemExit(
            "missing required exec-result exec exact plan columns: "
            + ", ".join(sorted(missing_exec_result_exec_plan))
        )

    required_exec_result_indices_plan = {
        "requirement_id",
        "source_file",
        "section_anchor",
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
        "expected_indices_length",
        "expected_group_names_length",
        "expected_has_groups",
        "expected_entry_index",
        "expected_index_pair_defined",
        "expected_index_pair_start",
        "expected_index_pair_end",
        "expected_group_name",
        "expected_duplicate_group_name",
        "expected_behavior",
        "expected_model_field",
        "coverage_credit",
        "plan_state",
        "target_test_artifact",
        "exact_case_obligation",
        "observability_status",
        "observability_reason",
        "next_action",
    }
    missing_exec_result_indices_plan = required_exec_result_indices_plan.difference(
        exec_result_indices_plan_fields
    )
    if missing_exec_result_indices_plan:
        raise SystemExit(
            "missing required exec-result indices exact plan columns: "
            + ", ".join(sorted(missing_exec_result_indices_plan))
        )

    required_exec_result_instances_plan = {
        "requirement_id",
        "source_file",
        "section_anchor",
        "mapping_family",
        "executable_layer",
        "result_subfamily",
        "result_semantic_route",
        "exact_case_family",
        "exact_case_id",
        "pattern",
        "flags",
        "input_text",
        "expected_original_source",
        "expected_original_flags",
        "expected_internal_slots",
        "expected_last_index_initial_value",
        "expected_last_index_writable",
        "expected_last_index_enumerable",
        "expected_last_index_configurable",
        "expected_behavior",
        "expected_model_field",
        "coverage_credit",
        "plan_state",
        "target_test_artifact",
        "exact_case_obligation",
        "observability_status",
        "observability_reason",
        "next_action",
    }
    missing_exec_result_instances_plan = (
        required_exec_result_instances_plan.difference(
            exec_result_instances_plan_fields
        )
    )
    if missing_exec_result_instances_plan:
        raise SystemExit(
            "missing required exec-result instances exact plan columns: "
            + ", ".join(sorted(missing_exec_result_instances_plan))
        )

    required_spec_model_plan = {
        "requirement_id",
        "source_file",
        "section_anchor",
        "mapping_family",
        "executable_layer",
        "spec_model_subfamily",
        "spec_model_route",
        "exact_case_family",
        "exact_case_id",
        "model_scenario",
        "source_text",
        "expected_source_code_point_count",
        "expected_utf16_code_unit_length",
        "expected_lexical_goal_symbols",
        "expected_regexp_goal_symbol",
        "expected_regexp_clause",
        "expected_behavior",
        "expected_model_field",
        "coverage_credit",
        "plan_state",
        "target_test_artifact",
        "exact_case_obligation",
        "observability_status",
        "observability_reason",
        "next_action",
    }
    missing_spec_model_plan = required_spec_model_plan.difference(
        spec_model_plan_fields
    )
    if missing_spec_model_plan:
        raise SystemExit(
            "missing required spec-model exact plan columns: "
            + ", ".join(sorted(missing_spec_model_plan))
        )

    required_test262_literal_lexer = {
        "case_id",
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
        "mapping_family",
        "executable_layer",
        "source_path",
        "source_line",
        "source_snippet",
        "literal_source",
        "literal_source_encoding",
        "expected_parser_result",
        "expected_pattern_text",
        "expected_flag_text",
        "expected_compile_result",
        "expected_behavior",
        "coverage_credit",
        "case_state",
        "target_test_artifact",
        "exact_case_obligation",
        "next_action",
        "extractor_reason",
    }
    missing_test262_literal_lexer = required_test262_literal_lexer.difference(
        test262_literal_lexer_fields
    )
    if missing_test262_literal_lexer:
        raise SystemExit(
            "missing required test262 literal-lexer exact columns: "
            + ", ".join(sorted(missing_test262_literal_lexer))
        )

    required_match_engine_start_anchor_plan = {
        "requirement_id",
        "source_file",
        "section_anchor",
        "mapping_family",
        "executable_layer",
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
    }
    missing_match_engine_start_anchor_plan = (
        required_match_engine_start_anchor_plan.difference(
            match_engine_start_anchor_plan_fields
        )
    )
    if missing_match_engine_start_anchor_plan:
        raise SystemExit(
            "missing required match-engine start-anchor exact plan columns: "
            + ", ".join(sorted(missing_match_engine_start_anchor_plan))
        )

    required_match_engine_end_anchor_plan = {
        "requirement_id",
        "source_file",
        "section_anchor",
        "mapping_family",
        "executable_layer",
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
    }
    missing_match_engine_end_anchor_plan = (
        required_match_engine_end_anchor_plan.difference(
            match_engine_end_anchor_plan_fields
        )
    )
    if missing_match_engine_end_anchor_plan:
        raise SystemExit(
            "missing required match-engine end-anchor exact plan columns: "
            + ", ".join(sorted(missing_match_engine_end_anchor_plan))
        )

    required_match_engine_assertion_plan = {
        "requirement_id",
        "source_file",
        "section_anchor",
        "mapping_family",
        "executable_layer",
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
    }
    missing_match_engine_assertion_plan = (
        required_match_engine_assertion_plan.difference(
            match_engine_assertion_plan_fields
        )
    )
    if missing_match_engine_assertion_plan:
        raise SystemExit(
            "missing required match-engine assertion exact plan columns: "
            + ", ".join(sorted(missing_match_engine_assertion_plan))
        )

    required_match_engine_quantifier_plan = {
        "requirement_id",
        "source_file",
        "section_anchor",
        "mapping_family",
        "executable_layer",
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
    }
    missing_match_engine_quantifier_plan = (
        required_match_engine_quantifier_plan.difference(
            match_engine_quantifier_plan_fields
        )
    )
    if missing_match_engine_quantifier_plan:
        raise SystemExit(
            "missing required match-engine quantifier exact plan columns: "
            + ", ".join(sorted(missing_match_engine_quantifier_plan))
        )

    required_match_engine_modifier_plan = {
        "requirement_id",
        "source_atom_plan_id",
        "source_file",
        "section_anchor",
        "mapping_family",
        "executable_layer",
        "modifier_subfamily",
        "modifier_semantic_route",
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
    }
    missing_match_engine_modifier_plan = (
        required_match_engine_modifier_plan.difference(
            match_engine_modifier_plan_fields
        )
    )
    if missing_match_engine_modifier_plan:
        raise SystemExit(
            "missing required match-engine modifier exact plan columns: "
            + ", ".join(sorted(missing_match_engine_modifier_plan))
        )

    required_match_engine_pattern_semantics_plan = {
        "requirement_id",
        "source_file",
        "section_anchor",
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
    }
    missing_match_engine_pattern_semantics_plan = (
        required_match_engine_pattern_semantics_plan.difference(
            match_engine_pattern_semantics_plan_fields
        )
    )
    if missing_match_engine_pattern_semantics_plan:
        raise SystemExit(
            "missing required match-engine Pattern Semantics exact plan columns: "
            + ", ".join(sorted(missing_match_engine_pattern_semantics_plan))
        )

    required_match_engine_annex_b_plan = {
        "requirement_id",
        "source_file",
        "section_anchor",
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
    }
    missing_match_engine_annex_b_plan = required_match_engine_annex_b_plan.difference(
        match_engine_annex_b_plan_fields
    )
    if missing_match_engine_annex_b_plan:
        raise SystemExit(
            "missing required match-engine Annex B exact plan columns: "
            + ", ".join(sorted(missing_match_engine_annex_b_plan))
        )

    required_match_state_plan = {
        "requirement_id",
        "source_file",
        "section_anchor",
        "mapping_family",
        "executable_layer",
        "exact_case_family",
        "exact_case_id",
        "pattern",
        "flags",
        "input_text",
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
    }
    missing_match_state_plan = required_match_state_plan.difference(
        match_state_plan_fields
    )
    if missing_match_state_plan:
        raise SystemExit(
            "missing required match-state exact plan columns: "
            + ", ".join(sorted(missing_match_state_plan))
        )

    local_exact_rows: dict[str, dict[str, str]] = {}
    for row in local_exact_rows_list:
        requirement_id = row["requirement_id"]
        if requirement_id in local_exact_rows:
            raise SystemExit(f"duplicate local exact row for {requirement_id}")
        local_exact_rows[requirement_id] = row

    selector_gap_rows: dict[str, dict[str, str]] = {}
    for row in selector_gap_rows_list:
        requirement_id = row["requirement_id"]
        if requirement_id in selector_gap_rows:
            raise SystemExit(f"duplicate selector-gap row for {requirement_id}")
        selector_gap_rows[requirement_id] = row

    reused_plan_rows: dict[str, dict[str, str]] = {}
    for row in reused_plan_rows_list:
        requirement_id = row["requirement_id"]
        if requirement_id in reused_plan_rows:
            raise SystemExit(f"duplicate reused exact plan row for {requirement_id}")
        reused_plan_rows[requirement_id] = row

    compile_parser_plan_rows: dict[str, dict[str, str]] = {}
    for row in compile_parser_plan_rows_list:
        requirement_id = row["requirement_id"]
        if requirement_id in compile_parser_plan_rows:
            raise SystemExit(
                f"duplicate compile/parser exact plan row for {requirement_id}"
            )
        compile_parser_plan_rows[requirement_id] = row

    literal_lexer_plan_rows: dict[str, dict[str, str]] = {}
    for row in literal_lexer_plan_rows_list:
        requirement_id = row["requirement_id"]
        if requirement_id in literal_lexer_plan_rows:
            raise SystemExit(
                f"duplicate literal lexer exact plan row for {requirement_id}"
            )
        literal_lexer_plan_rows[requirement_id] = row

    match_engine_plan_rows: dict[str, dict[str, str]] = {}
    for row in match_engine_plan_rows_list:
        requirement_id = row["requirement_id"]
        if requirement_id in match_engine_plan_rows:
            raise SystemExit(
                f"duplicate match-engine exact plan row for {requirement_id}"
            )
        match_engine_plan_rows[requirement_id] = row

    match_engine_atoms_plan_rows: dict[str, dict[str, str]] = {}
    for row in match_engine_atoms_plan_rows_list:
        requirement_id = row["requirement_id"]
        if requirement_id in match_engine_atoms_plan_rows:
            raise SystemExit(
                f"duplicate match-engine atoms exact plan row for {requirement_id}"
            )
        match_engine_atoms_plan_rows[requirement_id] = row

    match_engine_capture_plan_rows: dict[str, dict[str, str]] = {}
    for row in match_engine_capture_plan_rows_list:
        requirement_id = row["requirement_id"]
        if requirement_id in match_engine_capture_plan_rows:
            raise SystemExit(
                f"duplicate match-engine capture exact plan row for {requirement_id}"
            )
        match_engine_capture_plan_rows[requirement_id] = row

    match_engine_unicode_sets_string_plan_rows: dict[str, dict[str, str]] = {}
    for row in match_engine_unicode_sets_string_plan_rows_list:
        requirement_id = row["requirement_id"]
        if requirement_id in match_engine_unicode_sets_string_plan_rows:
            raise SystemExit(
                "duplicate match-engine UnicodeSets string exact plan row for "
                f"{requirement_id}"
            )
        match_engine_unicode_sets_string_plan_rows[requirement_id] = row

    match_engine_unicode_sets_escape_string_plan_rows: dict[str, dict[str, str]] = {}
    for row in match_engine_unicode_sets_escape_string_plan_rows_list:
        requirement_id = row["requirement_id"]
        if requirement_id in match_engine_unicode_sets_escape_string_plan_rows:
            raise SystemExit(
                "duplicate match-engine UnicodeSets escape string exact plan row "
                f"for {requirement_id}"
            )
        match_engine_unicode_sets_escape_string_plan_rows[requirement_id] = row

    match_engine_character_classes_plan_rows: dict[str, dict[str, str]] = {}
    for row in match_engine_character_classes_plan_rows_list:
        requirement_id = row["requirement_id"]
        if requirement_id in match_engine_character_classes_plan_rows:
            raise SystemExit(
                "duplicate match-engine character-classes exact plan row for "
                f"{requirement_id}"
            )
        match_engine_character_classes_plan_rows[requirement_id] = row

    match_engine_concatenation_plan_rows: dict[str, dict[str, str]] = {}
    for row in match_engine_concatenation_plan_rows_list:
        requirement_id = row["requirement_id"]
        if requirement_id in match_engine_concatenation_plan_rows:
            raise SystemExit(
                "duplicate match-engine concatenation exact plan row for "
                f"{requirement_id}"
            )
        match_engine_concatenation_plan_rows[requirement_id] = row

    match_engine_backreference_plan_rows: dict[str, dict[str, str]] = {}
    for row in match_engine_backreference_plan_rows_list:
        requirement_id = row["requirement_id"]
        if requirement_id in match_engine_backreference_plan_rows:
            raise SystemExit(
                "duplicate match-engine backreference exact plan row for "
                f"{requirement_id}"
            )
        match_engine_backreference_plan_rows[requirement_id] = row

    match_engine_backreference_matcher_plan_rows: dict[str, dict[str, str]] = {}
    for row in match_engine_backreference_matcher_plan_rows_list:
        requirement_id = row["requirement_id"]
        if requirement_id in match_engine_backreference_matcher_plan_rows:
            raise SystemExit(
                "duplicate match-engine BackreferenceMatcher exact plan row "
                f"for {requirement_id}"
            )
        match_engine_backreference_matcher_plan_rows[requirement_id] = row

    match_engine_result_plan_rows: dict[str, dict[str, str]] = {}
    for row in match_engine_result_plan_rows_list:
        requirement_id = row["requirement_id"]
        if requirement_id in match_engine_result_plan_rows:
            raise SystemExit(
                f"duplicate match-engine result exact plan row for {requirement_id}"
            )
        match_engine_result_plan_rows[requirement_id] = row

    exec_result_matching_plan_rows: dict[str, dict[str, str]] = {}
    for row in exec_result_matching_plan_rows_list:
        requirement_id = row["requirement_id"]
        if requirement_id in exec_result_matching_plan_rows:
            raise SystemExit(
                f"duplicate exec-result matching exact plan row for {requirement_id}"
            )
        exec_result_matching_plan_rows[requirement_id] = row

    exec_result_capture_plan_rows: dict[str, dict[str, str]] = {}
    for row in exec_result_capture_plan_rows_list:
        requirement_id = row["requirement_id"]
        if requirement_id in exec_result_capture_plan_rows:
            raise SystemExit(
                f"duplicate exec-result capture exact plan row for {requirement_id}"
            )
        exec_result_capture_plan_rows[requirement_id] = row

    exec_result_exec_plan_rows: dict[str, dict[str, str]] = {}
    for row in exec_result_exec_plan_rows_list:
        requirement_id = row["requirement_id"]
        if requirement_id in exec_result_exec_plan_rows:
            raise SystemExit(
                f"duplicate exec-result exec exact plan row for {requirement_id}"
            )
        exec_result_exec_plan_rows[requirement_id] = row

    exec_result_indices_plan_rows: dict[str, dict[str, str]] = {}
    for row in exec_result_indices_plan_rows_list:
        requirement_id = row["requirement_id"]
        if requirement_id in exec_result_indices_plan_rows:
            raise SystemExit(
                f"duplicate exec-result indices exact plan row for {requirement_id}"
            )
        exec_result_indices_plan_rows[requirement_id] = row

    exec_result_instances_plan_rows: dict[str, dict[str, str]] = {}
    for row in exec_result_instances_plan_rows_list:
        requirement_id = row["requirement_id"]
        if requirement_id in exec_result_instances_plan_rows:
            raise SystemExit(
                f"duplicate exec-result instances exact plan row for {requirement_id}"
            )
        exec_result_instances_plan_rows[requirement_id] = row

    spec_model_plan_rows: dict[str, dict[str, str]] = {}
    for row in spec_model_plan_rows_list:
        requirement_id = row["requirement_id"]
        if requirement_id in spec_model_plan_rows:
            raise SystemExit(
                f"duplicate spec-model exact plan row for {requirement_id}"
            )
        spec_model_plan_rows[requirement_id] = row

    test262_literal_lexer_rows: dict[str, dict[str, str]] = {}
    test262_literal_lexer_case_ids: set[str] = set()
    for row in test262_literal_lexer_rows_list:
        requirement_id = row["requirement_id"]
        case_id = row["case_id"]
        if requirement_id in test262_literal_lexer_rows:
            raise SystemExit(
                "duplicate test262 literal-lexer exact row for "
                f"{requirement_id}"
            )
        if case_id in test262_literal_lexer_case_ids:
            raise SystemExit(
                f"duplicate test262 literal-lexer exact case id {case_id}"
            )
        test262_literal_lexer_case_ids.add(case_id)
        test262_literal_lexer_rows[requirement_id] = row

    match_engine_start_anchor_plan_rows: dict[str, list[dict[str, str]]] = {}
    match_engine_start_anchor_case_ids: set[str] = set()
    for row in match_engine_start_anchor_plan_rows_list:
        requirement_id = row["requirement_id"]
        exact_case_id = row["exact_case_id"]
        if exact_case_id in match_engine_start_anchor_case_ids:
            raise SystemExit(
                "duplicate match-engine start-anchor exact plan case id "
                f"{exact_case_id}"
            )
        match_engine_start_anchor_case_ids.add(exact_case_id)
        match_engine_start_anchor_plan_rows.setdefault(requirement_id, []).append(row)

    match_engine_end_anchor_plan_rows: dict[str, list[dict[str, str]]] = {}
    match_engine_end_anchor_case_ids: set[str] = set()
    for row in match_engine_end_anchor_plan_rows_list:
        requirement_id = row["requirement_id"]
        exact_case_id = row["exact_case_id"]
        if exact_case_id in match_engine_end_anchor_case_ids:
            raise SystemExit(
                "duplicate match-engine end-anchor exact plan case id "
                f"{exact_case_id}"
            )
        match_engine_end_anchor_case_ids.add(exact_case_id)
        match_engine_end_anchor_plan_rows.setdefault(requirement_id, []).append(row)

    match_engine_assertion_plan_rows: dict[str, dict[str, str]] = {}
    for row in match_engine_assertion_plan_rows_list:
        requirement_id = row["requirement_id"]
        if requirement_id in match_engine_assertion_plan_rows:
            raise SystemExit(
                f"duplicate match-engine assertion exact plan row for {requirement_id}"
            )
        match_engine_assertion_plan_rows[requirement_id] = row

    match_engine_quantifier_plan_rows: dict[str, dict[str, str]] = {}
    for row in match_engine_quantifier_plan_rows_list:
        requirement_id = row["requirement_id"]
        if requirement_id in match_engine_quantifier_plan_rows:
            raise SystemExit(
                f"duplicate match-engine quantifier exact plan row for {requirement_id}"
            )
        match_engine_quantifier_plan_rows[requirement_id] = row

    match_engine_modifier_plan_rows: dict[str, dict[str, str]] = {}
    for row in match_engine_modifier_plan_rows_list:
        requirement_id = row["requirement_id"]
        if requirement_id in match_engine_modifier_plan_rows:
            raise SystemExit(
                f"duplicate match-engine modifier exact plan row for {requirement_id}"
            )
        match_engine_modifier_plan_rows[requirement_id] = row

    match_engine_pattern_semantics_plan_rows: dict[str, dict[str, str]] = {}
    for row in match_engine_pattern_semantics_plan_rows_list:
        requirement_id = row["requirement_id"]
        if requirement_id in match_engine_pattern_semantics_plan_rows:
            raise SystemExit(
                "duplicate match-engine Pattern Semantics exact plan row for "
                f"{requirement_id}"
            )
        match_engine_pattern_semantics_plan_rows[requirement_id] = row

    match_engine_annex_b_plan_rows: dict[str, dict[str, str]] = {}
    for row in match_engine_annex_b_plan_rows_list:
        requirement_id = row["requirement_id"]
        if requirement_id in match_engine_annex_b_plan_rows:
            raise SystemExit(
                f"duplicate match-engine Annex B exact plan row for {requirement_id}"
            )
        match_engine_annex_b_plan_rows[requirement_id] = row

    match_state_plan_rows: dict[str, dict[str, str]] = {}
    for row in match_state_plan_rows_list:
        requirement_id = row["requirement_id"]
        if requirement_id in match_state_plan_rows:
            raise SystemExit(
                f"duplicate match-state exact plan row for {requirement_id}"
            )
        match_state_plan_rows[requirement_id] = row

    selected_rows = [
        row
        for row in selection_rows
        if row["selection_state"] == "selected_compile_positive_case"
    ]
    open_rows = [
        row
        for row in selection_rows
        if row["selection_state"] == "needs_negative_or_local_exact_case"
    ]
    unsupported_states = sorted(
        {
            row["selection_state"]
            for row in selection_rows
            if row["selection_state"]
            not in {"selected_compile_positive_case", "needs_negative_or_local_exact_case"}
        }
    )
    if unsupported_states:
        raise SystemExit(
            "unsupported selection states: " + ", ".join(unsupported_states)
        )

    reuse_counts = Counter(row["selected_case_id"] for row in selected_rows)
    selected_by_requirement: dict[str, dict[str, str]] = {}
    for row in selected_rows:
        requirement_id = row["requirement_id"]
        if requirement_id in selected_by_requirement:
            raise SystemExit(f"duplicate selected row for {requirement_id}")
        selected_by_requirement[requirement_id] = row

    reused_open_ids = {
        row["requirement_id"]
        for row in selected_rows
        if exactness_for_selected(row, reuse_counts)[0]
        == "open_reused_candidate_needs_exact_proof"
    }
    missing_reused_plan_ids = sorted(reused_open_ids.difference(reused_plan_rows))
    if missing_reused_plan_ids:
        raise SystemExit(
            "open reused-candidate rows absent from reused exact plan: "
            + ", ".join(missing_reused_plan_ids[:10])
        )

    local_exact_ids = set(local_exact_rows)
    selector_gap_ids = set(selector_gap_rows)
    if selector_gap_ids:
        missing_local_exact_ids = sorted(selector_gap_ids.difference(local_exact_ids))
        unknown_local_exact_ids = sorted(local_exact_ids.difference(selector_gap_ids))
        if missing_local_exact_ids:
            raise SystemExit(
                "selector-gap rows absent from local exact plan: "
                + ", ".join(missing_local_exact_ids[:10])
            )
        if unknown_local_exact_ids:
            raise SystemExit(
                "local exact plan contains rows that are not selector-gap rows: "
                + ", ".join(unknown_local_exact_ids[:10])
            )
    selection_ids = {row["requirement_id"] for row in selection_rows}
    compile_parser_plan_ids = set(compile_parser_plan_rows)
    literal_lexer_plan_ids = set(literal_lexer_plan_rows)
    match_engine_plan_ids = set(match_engine_plan_rows)
    match_engine_atoms_plan_ids = set(match_engine_atoms_plan_rows)
    match_engine_capture_plan_ids = set(match_engine_capture_plan_rows)
    match_engine_unicode_sets_string_plan_ids = set(
        match_engine_unicode_sets_string_plan_rows
    )
    match_engine_unicode_sets_escape_string_plan_ids = set(
        match_engine_unicode_sets_escape_string_plan_rows
    )
    match_engine_character_classes_plan_ids = set(
        match_engine_character_classes_plan_rows
    )
    match_engine_concatenation_plan_ids = set(match_engine_concatenation_plan_rows)
    match_engine_backreference_plan_ids = set(match_engine_backreference_plan_rows)
    match_engine_backreference_matcher_plan_ids = set(
        match_engine_backreference_matcher_plan_rows
    )
    match_engine_result_plan_ids = set(match_engine_result_plan_rows)
    exec_result_matching_plan_ids = set(exec_result_matching_plan_rows)
    exec_result_capture_plan_ids = set(exec_result_capture_plan_rows)
    exec_result_exec_plan_ids = set(exec_result_exec_plan_rows)
    exec_result_indices_plan_ids = set(exec_result_indices_plan_rows)
    exec_result_instances_plan_ids = set(exec_result_instances_plan_rows)
    spec_model_plan_ids = set(spec_model_plan_rows)
    test262_literal_lexer_ids = set(test262_literal_lexer_rows)
    match_engine_start_anchor_plan_ids = set(match_engine_start_anchor_plan_rows)
    match_engine_end_anchor_plan_ids = set(match_engine_end_anchor_plan_rows)
    match_engine_assertion_plan_ids = set(match_engine_assertion_plan_rows)
    match_engine_quantifier_plan_ids = set(match_engine_quantifier_plan_rows)
    match_engine_modifier_plan_ids = set(match_engine_modifier_plan_rows)
    match_engine_pattern_semantics_plan_ids = set(
        match_engine_pattern_semantics_plan_rows
    )
    match_engine_annex_b_plan_ids = set(match_engine_annex_b_plan_rows)
    match_state_plan_ids = set(match_state_plan_rows)
    match_engine_creditable_plan_ids = {
        requirement_id
        for requirement_id, row in match_engine_plan_rows.items()
        if match_engine_exact_plan_is_creditable(row)
    }
    match_engine_atoms_creditable_plan_ids = {
        requirement_id
        for requirement_id, row in match_engine_atoms_plan_rows.items()
        if match_engine_atoms_exact_plan_is_creditable(row)
    }
    match_engine_character_classes_creditable_plan_ids = {
        requirement_id
        for requirement_id, row in match_engine_character_classes_plan_rows.items()
        if match_engine_character_classes_exact_plan_is_creditable(row)
    }
    match_engine_start_anchor_creditable_plan_ids = {
        requirement_id
        for requirement_id, plans in match_engine_start_anchor_plan_rows.items()
        if plans
        and all(match_engine_start_anchor_exact_plan_is_creditable(row) for row in plans)
    }
    match_engine_end_anchor_creditable_plan_ids = {
        requirement_id
        for requirement_id, plans in match_engine_end_anchor_plan_rows.items()
        if plans
        and all(match_engine_end_anchor_exact_plan_is_creditable(row) for row in plans)
    }
    match_engine_assertion_creditable_plan_ids = {
        requirement_id
        for requirement_id, row in match_engine_assertion_plan_rows.items()
        if match_engine_assertion_exact_plan_is_creditable(row)
    }
    match_engine_quantifier_creditable_plan_ids = {
        requirement_id
        for requirement_id, row in match_engine_quantifier_plan_rows.items()
        if match_engine_quantifier_exact_plan_is_creditable(row)
    }
    match_engine_modifier_creditable_plan_ids = {
        requirement_id
        for requirement_id, row in match_engine_modifier_plan_rows.items()
        if match_engine_modifier_exact_plan_is_creditable(row)
    }
    exec_result_matching_creditable_plan_ids = {
        requirement_id
        for requirement_id, row in exec_result_matching_plan_rows.items()
        if exec_result_matching_exact_plan_is_creditable(row)
    }
    exec_result_capture_creditable_plan_ids = {
        requirement_id
        for requirement_id, row in exec_result_capture_plan_rows.items()
        if exec_result_capture_exact_plan_is_creditable(row)
    }
    exec_result_exec_creditable_plan_ids = {
        requirement_id
        for requirement_id, row in exec_result_exec_plan_rows.items()
        if exec_result_exec_exact_plan_is_creditable(row)
    }
    exec_result_indices_creditable_plan_ids = {
        requirement_id
        for requirement_id, row in exec_result_indices_plan_rows.items()
        if exec_result_indices_exact_plan_is_creditable(row)
    }
    exec_result_instances_creditable_plan_ids = {
        requirement_id
        for requirement_id, row in exec_result_instances_plan_rows.items()
        if exec_result_instances_exact_plan_is_creditable(row)
    }
    spec_model_creditable_plan_ids = {
        requirement_id
        for requirement_id, row in spec_model_plan_rows.items()
        if spec_model_exact_plan_is_creditable(row)
    }
    test262_literal_lexer_creditable_ids = {
        requirement_id
        for requirement_id, row in test262_literal_lexer_rows.items()
        if test262_literal_lexer_exact_case_is_creditable(row)
    }
    match_engine_pattern_semantics_creditable_plan_ids = {
        requirement_id
        for requirement_id, row in match_engine_pattern_semantics_plan_rows.items()
        if match_engine_pattern_semantics_exact_plan_is_creditable(row)
    }
    match_engine_annex_b_creditable_plan_ids = {
        requirement_id
        for requirement_id, row in match_engine_annex_b_plan_rows.items()
        if match_engine_annex_b_exact_plan_is_creditable(row)
    }
    reopened_compile_parser_plan_ids = sorted(
        compile_parser_plan_ids.intersection(selection_ids)
    )
    if reopened_compile_parser_plan_ids:
        raise SystemExit(
            "compile/parser exact credited rows are still present in open selection: "
            + ", ".join(reopened_compile_parser_plan_ids[:10])
        )
    reopened_literal_lexer_plan_ids = sorted(
        literal_lexer_plan_ids.intersection(selection_ids)
    )
    if reopened_literal_lexer_plan_ids:
        raise SystemExit(
            "literal lexer exact credited rows are still present in open selection: "
            + ", ".join(reopened_literal_lexer_plan_ids[:10])
        )
    reopened_match_engine_plan_ids = sorted(
        match_engine_creditable_plan_ids.intersection(selection_ids)
    )
    if reopened_match_engine_plan_ids:
        raise SystemExit(
            "match-engine exact credited rows are still present in open selection: "
            + ", ".join(reopened_match_engine_plan_ids[:10])
        )
    reopened_match_engine_atoms_plan_ids = sorted(
        match_engine_atoms_creditable_plan_ids.intersection(selection_ids)
    )
    if reopened_match_engine_atoms_plan_ids:
        raise SystemExit(
            "match-engine atom exact credited rows are still present in open "
            "selection: "
            + ", ".join(reopened_match_engine_atoms_plan_ids[:10])
        )
    reopened_match_engine_capture_plan_ids = sorted(
        match_engine_capture_plan_ids.intersection(selection_ids)
    )
    if reopened_match_engine_capture_plan_ids:
        raise SystemExit(
            "match-engine capture exact credited rows are still present in open "
            "selection: "
            + ", ".join(reopened_match_engine_capture_plan_ids[:10])
        )
    reopened_match_engine_unicode_sets_string_plan_ids = sorted(
        match_engine_unicode_sets_string_plan_ids.intersection(selection_ids)
    )
    if reopened_match_engine_unicode_sets_string_plan_ids:
        raise SystemExit(
            "match-engine UnicodeSets string exact credited rows are still "
            "present in open selection: "
            + ", ".join(reopened_match_engine_unicode_sets_string_plan_ids[:10])
        )
    reopened_match_engine_unicode_sets_escape_string_plan_ids = sorted(
        match_engine_unicode_sets_escape_string_plan_ids.intersection(selection_ids)
    )
    if reopened_match_engine_unicode_sets_escape_string_plan_ids:
        raise SystemExit(
            "match-engine UnicodeSets escape string exact credited rows are "
            "still present in open selection: "
            + ", ".join(
                reopened_match_engine_unicode_sets_escape_string_plan_ids[:10]
            )
        )
    reopened_match_engine_character_classes_plan_ids = sorted(
        match_engine_character_classes_creditable_plan_ids.intersection(selection_ids)
    )
    if reopened_match_engine_character_classes_plan_ids:
        raise SystemExit(
            "match-engine character-class exact credited rows are still present "
            "in open selection: "
            + ", ".join(reopened_match_engine_character_classes_plan_ids[:10])
        )
    reopened_match_engine_concatenation_plan_ids = sorted(
        match_engine_concatenation_plan_ids.intersection(selection_ids)
    )
    if reopened_match_engine_concatenation_plan_ids:
        raise SystemExit(
            "match-engine concatenation exact credited rows are still present "
            "in open selection: "
            + ", ".join(reopened_match_engine_concatenation_plan_ids[:10])
        )
    reopened_match_engine_backreference_plan_ids = sorted(
        match_engine_backreference_plan_ids.intersection(selection_ids)
    )
    if reopened_match_engine_backreference_plan_ids:
        raise SystemExit(
            "match-engine backreference exact credited rows are still present in "
            "open selection: "
            + ", ".join(reopened_match_engine_backreference_plan_ids[:10])
        )
    reopened_match_engine_backreference_matcher_plan_ids = sorted(
        match_engine_backreference_matcher_plan_ids.intersection(selection_ids)
    )
    if reopened_match_engine_backreference_matcher_plan_ids:
        raise SystemExit(
            "match-engine BackreferenceMatcher exact credited rows are still "
            "present in open selection: "
            + ", ".join(
                reopened_match_engine_backreference_matcher_plan_ids[:10]
            )
        )
    reopened_match_engine_result_plan_ids = sorted(
        match_engine_result_plan_ids.intersection(selection_ids)
    )
    if reopened_match_engine_result_plan_ids:
        raise SystemExit(
            "match-engine result exact credited rows are still present in open "
            "selection: "
            + ", ".join(reopened_match_engine_result_plan_ids[:10])
        )
    reopened_match_engine_start_anchor_plan_ids = sorted(
        match_engine_start_anchor_creditable_plan_ids.intersection(selection_ids)
    )
    if reopened_match_engine_start_anchor_plan_ids:
        raise SystemExit(
            "match-engine start-anchor exact credited rows are still present in "
            "open selection: "
            + ", ".join(reopened_match_engine_start_anchor_plan_ids[:10])
        )
    reopened_match_engine_end_anchor_plan_ids = sorted(
        match_engine_end_anchor_creditable_plan_ids.intersection(selection_ids)
    )
    if reopened_match_engine_end_anchor_plan_ids:
        raise SystemExit(
            "match-engine end-anchor exact credited rows are still present in "
            "open selection: "
            + ", ".join(reopened_match_engine_end_anchor_plan_ids[:10])
        )
    reopened_match_engine_assertion_plan_ids = sorted(
        match_engine_assertion_creditable_plan_ids.intersection(selection_ids)
    )
    if reopened_match_engine_assertion_plan_ids:
        raise SystemExit(
            "match-engine assertion exact credited rows are still present in "
            "open selection: "
            + ", ".join(reopened_match_engine_assertion_plan_ids[:10])
        )
    reopened_match_engine_quantifier_plan_ids = sorted(
        match_engine_quantifier_creditable_plan_ids.intersection(selection_ids)
    )
    if reopened_match_engine_quantifier_plan_ids:
        raise SystemExit(
            "match-engine quantifier exact credited rows are still present in "
            "open selection: "
            + ", ".join(reopened_match_engine_quantifier_plan_ids[:10])
        )
    reopened_match_engine_modifier_plan_ids = sorted(
        match_engine_modifier_creditable_plan_ids.intersection(selection_ids)
    )
    if reopened_match_engine_modifier_plan_ids:
        raise SystemExit(
            "match-engine modifier exact credited rows are still present in "
            "open selection: "
            + ", ".join(reopened_match_engine_modifier_plan_ids[:10])
        )
    reopened_match_engine_pattern_semantics_plan_ids = sorted(
        match_engine_pattern_semantics_creditable_plan_ids.intersection(selection_ids)
    )
    if reopened_match_engine_pattern_semantics_plan_ids:
        raise SystemExit(
            "match-engine Pattern Semantics exact credited rows are still "
            "present in open selection: "
            + ", ".join(reopened_match_engine_pattern_semantics_plan_ids[:10])
        )
    reopened_match_engine_annex_b_plan_ids = sorted(
        match_engine_annex_b_creditable_plan_ids.intersection(selection_ids)
    )
    if reopened_match_engine_annex_b_plan_ids:
        raise SystemExit(
            "match-engine Annex B exact credited rows are still present in open "
            "selection: "
            + ", ".join(reopened_match_engine_annex_b_plan_ids[:10])
        )
    reopened_match_state_plan_ids = sorted(
        match_state_plan_ids.intersection(selection_ids)
    )
    if reopened_match_state_plan_ids:
        raise SystemExit(
            "match-state exact credited rows are still present in open "
            "selection: "
            + ", ".join(reopened_match_state_plan_ids[:10])
        )
    reopened_spec_model_plan_ids = sorted(
        spec_model_creditable_plan_ids.intersection(selection_ids)
    )
    if reopened_spec_model_plan_ids:
        raise SystemExit(
            "spec-model exact credited rows are still present in open "
            "selection: "
            + ", ".join(reopened_spec_model_plan_ids[:10])
        )
    reopened_test262_literal_lexer_ids = sorted(
        test262_literal_lexer_ids.intersection(selection_ids)
    )
    if reopened_test262_literal_lexer_ids:
        raise SystemExit(
            "test262 literal-lexer exact credited rows are still present in "
            "open selection: "
            + ", ".join(reopened_test262_literal_lexer_ids[:10])
        )
    reopened_local_exact_ids = sorted(local_exact_ids.intersection(selection_ids))
    if reopened_local_exact_ids:
        raise SystemExit(
            "local exact credited rows are still present in open selection: "
            + ", ".join(reopened_local_exact_ids[:10])
        )
    for requirement_id, local_exact in sorted(local_exact_rows.items()):
        selector_gap = selector_gap_rows.get(requirement_id)
        if selector_gap is not None:
            validate_local_exact_against_selector_gap(local_exact, selector_gap)

    rows: list[dict[str, str]] = []
    rows.extend(local_exact_audit_row(row) for row in local_exact_rows_list)
    consumed_reused_plan_ids: set[str] = set(compile_parser_plan_ids)
    consumed_compile_parser_plan_ids: set[str] = set()
    consumed_literal_lexer_plan_ids: set[str] = set()
    consumed_match_engine_plan_ids: set[str] = set()
    consumed_match_engine_atoms_plan_ids: set[str] = set()
    consumed_match_engine_capture_plan_ids: set[str] = set()
    consumed_match_engine_unicode_sets_string_plan_ids: set[str] = set()
    consumed_match_engine_unicode_sets_escape_string_plan_ids: set[str] = set()
    consumed_match_engine_character_classes_plan_ids: set[str] = set()
    consumed_match_engine_concatenation_plan_ids: set[str] = set()
    consumed_match_engine_backreference_plan_ids: set[str] = set()
    consumed_match_engine_backreference_matcher_plan_ids: set[str] = set()
    consumed_match_engine_result_plan_ids: set[str] = set()
    consumed_exec_result_matching_plan_ids: set[str] = set()
    consumed_exec_result_capture_plan_ids: set[str] = set()
    consumed_exec_result_exec_plan_ids: set[str] = set()
    consumed_exec_result_indices_plan_ids: set[str] = set()
    consumed_exec_result_instances_plan_ids: set[str] = set()
    consumed_spec_model_plan_ids: set[str] = set()
    consumed_test262_literal_lexer_ids: set[str] = set()
    consumed_match_engine_start_anchor_case_ids: set[str] = set()
    consumed_match_engine_end_anchor_case_ids: set[str] = set()
    consumed_match_engine_assertion_plan_ids: set[str] = set()
    consumed_match_engine_quantifier_plan_ids: set[str] = set()
    consumed_match_engine_modifier_plan_ids: set[str] = set()
    consumed_match_engine_pattern_semantics_plan_ids: set[str] = set()
    consumed_match_engine_annex_b_plan_ids: set[str] = set()
    consumed_match_state_plan_ids: set[str] = set()
    for requirement_id, compile_parser_plan in sorted(
        compile_parser_plan_rows.items()
    ):
        rows.append(compile_parser_exact_audit_row(compile_parser_plan))
        consumed_compile_parser_plan_ids.add(requirement_id)
    for requirement_id, literal_lexer_plan in sorted(
        literal_lexer_plan_rows.items()
    ):
        rows.append(literal_lexer_exact_audit_row(literal_lexer_plan))
        consumed_literal_lexer_plan_ids.add(requirement_id)
    for requirement_id, match_engine_plan in sorted(
        match_engine_plan_rows.items()
    ):
        validate_match_engine_exact_plan_row(match_engine_plan)
        if match_engine_exact_plan_is_creditable(match_engine_plan):
            rows.append(match_engine_exact_audit_row(match_engine_plan))
            consumed_match_engine_plan_ids.add(requirement_id)
    for requirement_id, match_engine_atoms_plan in sorted(
        match_engine_atoms_plan_rows.items()
    ):
        validate_match_engine_atoms_exact_plan_row(match_engine_atoms_plan)
        if match_engine_atoms_exact_plan_is_creditable(match_engine_atoms_plan):
            rows.append(match_engine_atoms_exact_audit_row(match_engine_atoms_plan))
            consumed_match_engine_atoms_plan_ids.add(requirement_id)
    for requirement_id, match_engine_capture_plan in sorted(
        match_engine_capture_plan_rows.items()
    ):
        rows.append(match_engine_capture_exact_audit_row(match_engine_capture_plan))
        consumed_match_engine_capture_plan_ids.add(requirement_id)
    for requirement_id, match_engine_unicode_sets_string_plan in sorted(
        match_engine_unicode_sets_string_plan_rows.items()
    ):
        rows.append(
            match_engine_unicode_sets_string_exact_audit_row(
                match_engine_unicode_sets_string_plan
            )
        )
        consumed_match_engine_unicode_sets_string_plan_ids.add(requirement_id)
    for requirement_id, match_engine_unicode_sets_escape_string_plan in sorted(
        match_engine_unicode_sets_escape_string_plan_rows.items()
    ):
        rows.append(
            match_engine_unicode_sets_escape_string_exact_audit_row(
                match_engine_unicode_sets_escape_string_plan
            )
        )
        consumed_match_engine_unicode_sets_escape_string_plan_ids.add(requirement_id)
    for requirement_id, match_engine_character_classes_plan in sorted(
        match_engine_character_classes_plan_rows.items()
    ):
        validate_match_engine_character_classes_exact_plan_row(
            match_engine_character_classes_plan
        )
        if match_engine_character_classes_exact_plan_is_creditable(
            match_engine_character_classes_plan
        ):
            rows.append(
                match_engine_character_classes_exact_audit_row(
                    match_engine_character_classes_plan
                )
            )
            consumed_match_engine_character_classes_plan_ids.add(requirement_id)
    for requirement_id, match_engine_concatenation_plan in sorted(
        match_engine_concatenation_plan_rows.items()
    ):
        rows.append(
            match_engine_concatenation_exact_audit_row(
                match_engine_concatenation_plan
            )
        )
        consumed_match_engine_concatenation_plan_ids.add(requirement_id)
    for requirement_id, match_engine_backreference_plan in sorted(
        match_engine_backreference_plan_rows.items()
    ):
        rows.append(
            match_engine_backreference_exact_audit_row(
                match_engine_backreference_plan
            )
        )
        consumed_match_engine_backreference_plan_ids.add(requirement_id)
    for requirement_id, match_engine_backreference_matcher_plan in sorted(
        match_engine_backreference_matcher_plan_rows.items()
    ):
        rows.append(
            match_engine_backreference_matcher_exact_audit_row(
                match_engine_backreference_matcher_plan
            )
        )
        consumed_match_engine_backreference_matcher_plan_ids.add(requirement_id)
    for requirement_id, match_engine_result_plan in sorted(
        match_engine_result_plan_rows.items()
    ):
        rows.append(match_engine_result_exact_audit_row(match_engine_result_plan))
        consumed_match_engine_result_plan_ids.add(requirement_id)
    for requirement_id, exec_result_matching_plan in sorted(
        exec_result_matching_plan_rows.items()
    ):
        validate_exec_result_matching_exact_plan_row(exec_result_matching_plan)
        if exec_result_matching_exact_plan_is_creditable(exec_result_matching_plan):
            rows.append(exec_result_matching_exact_audit_row(exec_result_matching_plan))
            consumed_exec_result_matching_plan_ids.add(requirement_id)
    for requirement_id, exec_result_capture_plan in sorted(
        exec_result_capture_plan_rows.items()
    ):
        validate_exec_result_capture_exact_plan_row(exec_result_capture_plan)
        if exec_result_capture_exact_plan_is_creditable(exec_result_capture_plan):
            rows.append(exec_result_capture_exact_audit_row(exec_result_capture_plan))
            consumed_exec_result_capture_plan_ids.add(requirement_id)
    for requirement_id, exec_result_exec_plan in sorted(
        exec_result_exec_plan_rows.items()
    ):
        validate_exec_result_exec_exact_plan_row(exec_result_exec_plan)
        if exec_result_exec_exact_plan_is_creditable(exec_result_exec_plan):
            rows.append(exec_result_exec_exact_audit_row(exec_result_exec_plan))
            consumed_exec_result_exec_plan_ids.add(requirement_id)
    for requirement_id, exec_result_indices_plan in sorted(
        exec_result_indices_plan_rows.items()
    ):
        validate_exec_result_indices_exact_plan_row(exec_result_indices_plan)
        if exec_result_indices_exact_plan_is_creditable(exec_result_indices_plan):
            rows.append(exec_result_indices_exact_audit_row(exec_result_indices_plan))
            consumed_exec_result_indices_plan_ids.add(requirement_id)
    for requirement_id, exec_result_instances_plan in sorted(
        exec_result_instances_plan_rows.items()
    ):
        validate_exec_result_instances_exact_plan_row(exec_result_instances_plan)
        if exec_result_instances_exact_plan_is_creditable(
            exec_result_instances_plan
        ):
            rows.append(
                exec_result_instances_exact_audit_row(exec_result_instances_plan)
            )
            consumed_exec_result_instances_plan_ids.add(requirement_id)
    for requirement_id, spec_model_plan in sorted(spec_model_plan_rows.items()):
        validate_spec_model_exact_plan_row(spec_model_plan)
        if spec_model_exact_plan_is_creditable(spec_model_plan):
            rows.append(spec_model_exact_audit_row(spec_model_plan))
            consumed_spec_model_plan_ids.add(requirement_id)
    for requirement_id, test262_literal_lexer in sorted(
        test262_literal_lexer_rows.items()
    ):
        validate_test262_literal_lexer_exact_case_row(test262_literal_lexer)
        if test262_literal_lexer_exact_case_is_creditable(test262_literal_lexer):
            rows.append(
                test262_literal_lexer_exact_audit_row(test262_literal_lexer)
            )
            consumed_test262_literal_lexer_ids.add(requirement_id)
    for requirement_id, match_engine_start_anchor_plans in sorted(
        match_engine_start_anchor_plan_rows.items()
    ):
        rows.append(
            match_engine_start_anchor_exact_audit_row(
                match_engine_start_anchor_plans
            )
        )
        consumed_match_engine_start_anchor_case_ids.update(
            row["exact_case_id"] for row in match_engine_start_anchor_plans
        )
    for requirement_id, match_engine_end_anchor_plans in sorted(
        match_engine_end_anchor_plan_rows.items()
    ):
        rows.append(
            match_engine_end_anchor_exact_audit_row(
                match_engine_end_anchor_plans
            )
        )
        consumed_match_engine_end_anchor_case_ids.update(
            row["exact_case_id"] for row in match_engine_end_anchor_plans
        )
    for requirement_id, match_engine_assertion_plan in sorted(
        match_engine_assertion_plan_rows.items()
    ):
        rows.append(
            match_engine_assertion_exact_audit_row(
                match_engine_assertion_plan
            )
        )
        consumed_match_engine_assertion_plan_ids.add(requirement_id)
    for requirement_id, match_engine_quantifier_plan in sorted(
        match_engine_quantifier_plan_rows.items()
    ):
        rows.append(
            match_engine_quantifier_exact_audit_row(
                match_engine_quantifier_plan
            )
        )
        consumed_match_engine_quantifier_plan_ids.add(requirement_id)
    for requirement_id, match_engine_modifier_plan in sorted(
        match_engine_modifier_plan_rows.items()
    ):
        rows.append(
            match_engine_modifier_exact_audit_row(
                match_engine_modifier_plan
            )
        )
        consumed_match_engine_modifier_plan_ids.add(requirement_id)
    for requirement_id, match_engine_pattern_semantics_plan in sorted(
        match_engine_pattern_semantics_plan_rows.items()
    ):
        validate_match_engine_pattern_semantics_exact_plan_row(
            match_engine_pattern_semantics_plan
        )
        if match_engine_pattern_semantics_exact_plan_is_creditable(
            match_engine_pattern_semantics_plan
        ):
            rows.append(
                match_engine_pattern_semantics_exact_audit_row(
                    match_engine_pattern_semantics_plan
                )
            )
            consumed_match_engine_pattern_semantics_plan_ids.add(requirement_id)
    for requirement_id, match_engine_annex_b_plan in sorted(
        match_engine_annex_b_plan_rows.items()
    ):
        rows.append(match_engine_annex_b_exact_audit_row(match_engine_annex_b_plan))
        consumed_match_engine_annex_b_plan_ids.add(requirement_id)
    for requirement_id, match_state_plan in sorted(match_state_plan_rows.items()):
        rows.append(match_state_exact_audit_row(match_state_plan))
        consumed_match_state_plan_ids.add(requirement_id)
    for row in selected_rows:
        requirement_id = row["requirement_id"]
        plan = reused_plan_rows.get(requirement_id)
        if plan is None:
            rows.append(selected_audit_row(row, reuse_counts))
        else:
            rows.append(reused_exact_audit_row(plan, row, reuse_counts))
            consumed_reused_plan_ids.add(requirement_id)
    for requirement_id in sorted(set(reused_plan_rows).difference(consumed_reused_plan_ids)):
        rows.append(
            reused_exact_audit_row(
                reused_plan_rows[requirement_id],
                selected_by_requirement.get(requirement_id),
                reuse_counts,
            )
        )
    for row in open_rows:
        requirement_id = row["requirement_id"]
        rows.append(open_selection_audit_row(row))
    unconsumed_compile_parser_plan_ids = sorted(
        compile_parser_plan_ids.difference(consumed_compile_parser_plan_ids)
    )
    if unconsumed_compile_parser_plan_ids:
        raise SystemExit(
            "compile/parser exact plan rows were not consumed: "
            + ", ".join(unconsumed_compile_parser_plan_ids[:10])
        )
    unconsumed_literal_lexer_plan_ids = sorted(
        literal_lexer_plan_ids.difference(consumed_literal_lexer_plan_ids)
    )
    if unconsumed_literal_lexer_plan_ids:
        raise SystemExit(
            "literal lexer exact plan rows were not consumed: "
            + ", ".join(unconsumed_literal_lexer_plan_ids[:10])
        )
    unconsumed_match_engine_plan_ids = sorted(
        match_engine_creditable_plan_ids.difference(consumed_match_engine_plan_ids)
    )
    if unconsumed_match_engine_plan_ids:
        raise SystemExit(
            "match-engine exact plan rows were not consumed: "
            + ", ".join(unconsumed_match_engine_plan_ids[:10])
        )
    unconsumed_match_engine_atoms_plan_ids = sorted(
        match_engine_atoms_creditable_plan_ids.difference(
            consumed_match_engine_atoms_plan_ids
        )
    )
    if unconsumed_match_engine_atoms_plan_ids:
        raise SystemExit(
            "match-engine atom exact plan rows were not consumed: "
            + ", ".join(unconsumed_match_engine_atoms_plan_ids[:10])
        )
    unconsumed_match_engine_capture_plan_ids = sorted(
        match_engine_capture_plan_ids.difference(
            consumed_match_engine_capture_plan_ids
        )
    )
    if unconsumed_match_engine_capture_plan_ids:
        raise SystemExit(
            "match-engine capture exact plan rows were not consumed: "
            + ", ".join(unconsumed_match_engine_capture_plan_ids[:10])
        )
    unconsumed_match_engine_unicode_sets_string_plan_ids = sorted(
        match_engine_unicode_sets_string_plan_ids.difference(
            consumed_match_engine_unicode_sets_string_plan_ids
        )
    )
    if unconsumed_match_engine_unicode_sets_string_plan_ids:
        raise SystemExit(
            "match-engine UnicodeSets string exact plan rows were not consumed: "
            + ", ".join(unconsumed_match_engine_unicode_sets_string_plan_ids[:10])
        )
    unconsumed_match_engine_unicode_sets_escape_string_plan_ids = sorted(
        match_engine_unicode_sets_escape_string_plan_ids.difference(
            consumed_match_engine_unicode_sets_escape_string_plan_ids
        )
    )
    if unconsumed_match_engine_unicode_sets_escape_string_plan_ids:
        raise SystemExit(
            "match-engine UnicodeSets escape string exact plan rows were not "
            "consumed: "
            + ", ".join(
                unconsumed_match_engine_unicode_sets_escape_string_plan_ids[:10]
            )
        )
    unconsumed_match_engine_character_classes_plan_ids = sorted(
        match_engine_character_classes_creditable_plan_ids.difference(
            consumed_match_engine_character_classes_plan_ids
        )
    )
    if unconsumed_match_engine_character_classes_plan_ids:
        raise SystemExit(
            "match-engine character-class exact plan rows were not consumed: "
            + ", ".join(unconsumed_match_engine_character_classes_plan_ids[:10])
        )
    unconsumed_match_engine_concatenation_plan_ids = sorted(
        match_engine_concatenation_plan_ids.difference(
            consumed_match_engine_concatenation_plan_ids
        )
    )
    if unconsumed_match_engine_concatenation_plan_ids:
        raise SystemExit(
            "match-engine concatenation exact plan rows were not consumed: "
            + ", ".join(unconsumed_match_engine_concatenation_plan_ids[:10])
        )
    unconsumed_match_engine_backreference_plan_ids = sorted(
        match_engine_backreference_plan_ids.difference(
            consumed_match_engine_backreference_plan_ids
        )
    )
    if unconsumed_match_engine_backreference_plan_ids:
        raise SystemExit(
            "match-engine backreference exact plan rows were not consumed: "
            + ", ".join(unconsumed_match_engine_backreference_plan_ids[:10])
        )
    unconsumed_match_engine_backreference_matcher_plan_ids = sorted(
        match_engine_backreference_matcher_plan_ids.difference(
            consumed_match_engine_backreference_matcher_plan_ids
        )
    )
    if unconsumed_match_engine_backreference_matcher_plan_ids:
        raise SystemExit(
            "match-engine BackreferenceMatcher exact plan rows were not "
            "consumed: "
            + ", ".join(unconsumed_match_engine_backreference_matcher_plan_ids[:10])
        )
    unconsumed_match_engine_result_plan_ids = sorted(
        match_engine_result_plan_ids.difference(
            consumed_match_engine_result_plan_ids
        )
    )
    if unconsumed_match_engine_result_plan_ids:
        raise SystemExit(
            "match-engine result exact plan rows were not consumed: "
            + ", ".join(unconsumed_match_engine_result_plan_ids[:10])
        )
    unconsumed_exec_result_matching_plan_ids = sorted(
        exec_result_matching_creditable_plan_ids.difference(
            consumed_exec_result_matching_plan_ids
        )
    )
    if unconsumed_exec_result_matching_plan_ids:
        raise SystemExit(
            "exec-result matching exact plan rows were not consumed: "
            + ", ".join(unconsumed_exec_result_matching_plan_ids[:10])
        )
    unconsumed_exec_result_capture_plan_ids = sorted(
        exec_result_capture_creditable_plan_ids.difference(
            consumed_exec_result_capture_plan_ids
        )
    )
    if unconsumed_exec_result_capture_plan_ids:
        raise SystemExit(
            "exec-result capture exact plan rows were not consumed: "
            + ", ".join(unconsumed_exec_result_capture_plan_ids[:10])
        )
    unconsumed_exec_result_exec_plan_ids = sorted(
        exec_result_exec_creditable_plan_ids.difference(
            consumed_exec_result_exec_plan_ids
        )
    )
    if unconsumed_exec_result_exec_plan_ids:
        raise SystemExit(
            "exec-result exec exact plan rows were not consumed: "
            + ", ".join(unconsumed_exec_result_exec_plan_ids[:10])
        )
    unconsumed_exec_result_indices_plan_ids = sorted(
        exec_result_indices_creditable_plan_ids.difference(
            consumed_exec_result_indices_plan_ids
        )
    )
    if unconsumed_exec_result_indices_plan_ids:
        raise SystemExit(
            "exec-result indices exact plan rows were not consumed: "
            + ", ".join(unconsumed_exec_result_indices_plan_ids[:10])
        )
    unconsumed_exec_result_instances_plan_ids = sorted(
        exec_result_instances_creditable_plan_ids.difference(
            consumed_exec_result_instances_plan_ids
        )
    )
    if unconsumed_exec_result_instances_plan_ids:
        raise SystemExit(
            "exec-result instances exact plan rows were not consumed: "
            + ", ".join(unconsumed_exec_result_instances_plan_ids[:10])
        )
    unconsumed_spec_model_plan_ids = sorted(
        spec_model_creditable_plan_ids.difference(consumed_spec_model_plan_ids)
    )
    if unconsumed_spec_model_plan_ids:
        raise SystemExit(
            "spec-model exact plan rows were not consumed: "
            + ", ".join(unconsumed_spec_model_plan_ids[:10])
        )
    unconsumed_test262_literal_lexer_ids = sorted(
        test262_literal_lexer_creditable_ids.difference(
            consumed_test262_literal_lexer_ids
        )
    )
    if unconsumed_test262_literal_lexer_ids:
        raise SystemExit(
            "test262 literal-lexer exact rows were not consumed: "
            + ", ".join(unconsumed_test262_literal_lexer_ids[:10])
        )
    unconsumed_match_engine_start_anchor_case_ids = sorted(
        match_engine_start_anchor_case_ids.difference(
            consumed_match_engine_start_anchor_case_ids
        )
    )
    if unconsumed_match_engine_start_anchor_case_ids:
        raise SystemExit(
            "match-engine start-anchor exact plan rows were not consumed: "
            + ", ".join(unconsumed_match_engine_start_anchor_case_ids[:10])
        )
    unconsumed_match_engine_end_anchor_case_ids = sorted(
        match_engine_end_anchor_case_ids.difference(
            consumed_match_engine_end_anchor_case_ids
        )
    )
    if unconsumed_match_engine_end_anchor_case_ids:
        raise SystemExit(
            "match-engine end-anchor exact plan rows were not consumed: "
            + ", ".join(unconsumed_match_engine_end_anchor_case_ids[:10])
        )
    unconsumed_match_engine_assertion_plan_ids = sorted(
        match_engine_assertion_plan_ids.difference(
            consumed_match_engine_assertion_plan_ids
        )
    )
    if unconsumed_match_engine_assertion_plan_ids:
        raise SystemExit(
            "match-engine assertion exact plan rows were not consumed: "
            + ", ".join(unconsumed_match_engine_assertion_plan_ids[:10])
        )
    unconsumed_match_engine_quantifier_plan_ids = sorted(
        match_engine_quantifier_plan_ids.difference(
            consumed_match_engine_quantifier_plan_ids
        )
    )
    if unconsumed_match_engine_quantifier_plan_ids:
        raise SystemExit(
            "match-engine quantifier exact plan rows were not consumed: "
            + ", ".join(unconsumed_match_engine_quantifier_plan_ids[:10])
        )
    unconsumed_match_engine_modifier_plan_ids = sorted(
        match_engine_modifier_plan_ids.difference(
            consumed_match_engine_modifier_plan_ids
        )
    )
    if unconsumed_match_engine_modifier_plan_ids:
        raise SystemExit(
            "match-engine modifier exact plan rows were not consumed: "
            + ", ".join(unconsumed_match_engine_modifier_plan_ids[:10])
        )
    unconsumed_match_engine_pattern_semantics_plan_ids = sorted(
        match_engine_pattern_semantics_creditable_plan_ids.difference(
            consumed_match_engine_pattern_semantics_plan_ids
        )
    )
    if unconsumed_match_engine_pattern_semantics_plan_ids:
        raise SystemExit(
            "match-engine Pattern Semantics exact plan rows were not consumed: "
            + ", ".join(unconsumed_match_engine_pattern_semantics_plan_ids[:10])
        )
    unconsumed_match_engine_annex_b_plan_ids = sorted(
        match_engine_annex_b_creditable_plan_ids.difference(
            consumed_match_engine_annex_b_plan_ids
        )
    )
    if unconsumed_match_engine_annex_b_plan_ids:
        raise SystemExit(
            "match-engine Annex B exact plan rows were not consumed: "
            + ", ".join(unconsumed_match_engine_annex_b_plan_ids[:10])
        )
    unconsumed_match_state_plan_ids = sorted(
        match_state_plan_ids.difference(consumed_match_state_plan_ids)
    )
    if unconsumed_match_state_plan_ids:
        raise SystemExit(
            "match-state exact plan rows were not consumed: "
            + ", ".join(unconsumed_match_state_plan_ids[:10])
        )
    rows.extend(negative_corpus_audit_row(row) for row in negative_rows)
    validate_unique_ids(rows, fields=("audit_id",))

    state_counts = Counter(row["exactness_audit_state"] for row in rows)
    credit_counts = Counter(row["coverage_credit"] for row in rows)
    scope_counts = Counter(row["audit_scope"] for row in rows)
    kind_counts = Counter(row["evidence_kind"] for row in rows)
    action_counts = Counter(row["next_action"] for row in rows)
    family_counts = Counter(row["mapping_family"] for row in rows)
    layer_counts = Counter(row["executable_layer"] for row in rows)
    reuse_counts_for_rows = Counter(row["case_reuse_count"] for row in rows if row["case_id"])

    potential_ready_rows = state_counts.get("potential_exact_ready_manual_review", 0)
    credit_rows = sum(
        count for credit, count in credit_counts.items() if not credit.startswith("none")
    )
    open_rows_count = len(rows) - credit_rows

    summary_lines = [
        "ecma262_snapshot\t2026\n",
        f"input_selection\t{selection}\n",
        f"input_negative_syntax\t{negative_syntax}\n",
        f"input_local_exact_plan\t{local_exact_plan}\n",
        f"input_selector_gap_worklist\t{selector_gap_worklist}\n",
        f"input_reused_candidate_exact_plan\t{reused_candidate_exact_plan}\n",
        f"input_compile_parser_exact_plan\t{compile_parser_exact_plan}\n",
        f"input_literal_lexer_exact_plan\t{literal_lexer_exact_plan}\n",
        f"input_match_engine_exact_plan\t{match_engine_exact_plan}\n",
        f"input_match_engine_atoms_exact_plan\t{match_engine_atoms_exact_plan}\n",
        f"input_match_engine_capture_exact_plan\t{match_engine_capture_exact_plan}\n",
        "input_match_engine_unicode_sets_string_exact_plan\t"
        f"{match_engine_unicode_sets_string_exact_plan}\n",
        "input_match_engine_unicode_sets_escape_string_exact_plan\t"
        f"{match_engine_unicode_sets_escape_string_exact_plan}\n",
        "input_match_engine_character_classes_exact_plan\t"
        f"{match_engine_character_classes_exact_plan}\n",
        f"input_match_engine_concatenation_exact_plan\t{match_engine_concatenation_exact_plan}\n",
        f"input_match_engine_backreference_exact_plan\t{match_engine_backreference_exact_plan}\n",
        "input_match_engine_backreference_matcher_exact_plan\t"
        f"{match_engine_backreference_matcher_exact_plan}\n",
        f"input_match_engine_result_exact_plan\t{match_engine_result_exact_plan}\n",
        f"input_exec_result_matching_exact_plan\t{exec_result_matching_exact_plan}\n",
        f"input_exec_result_capture_exact_plan\t{exec_result_capture_exact_plan}\n",
        f"input_exec_result_exec_exact_plan\t{exec_result_exec_exact_plan}\n",
        f"input_exec_result_indices_exact_plan\t{exec_result_indices_exact_plan}\n",
        f"input_exec_result_instances_exact_plan\t{exec_result_instances_exact_plan}\n",
        f"input_spec_model_exact_plan\t{spec_model_exact_plan}\n",
        f"input_test262_regexp_executable_cases\t{test262_regexp_executable_cases}\n",
        f"input_match_engine_start_anchor_exact_plan\t{match_engine_start_anchor_exact_plan}\n",
        f"input_match_engine_end_anchor_exact_plan\t{match_engine_end_anchor_exact_plan}\n",
        f"input_match_engine_assertion_exact_plan\t{match_engine_assertion_exact_plan}\n",
        f"input_match_engine_quantifier_exact_plan\t{match_engine_quantifier_exact_plan}\n",
        f"input_match_engine_modifier_exact_plan\t{match_engine_modifier_exact_plan}\n",
        "input_match_engine_pattern_semantics_exact_plan\t"
        f"{match_engine_pattern_semantics_exact_plan}\n",
        f"input_match_engine_annex_b_exact_plan\t{match_engine_annex_b_exact_plan}\n",
        f"input_match_state_exact_plan\t{match_state_exact_plan}\n",
        f"selection_rows\t{len(selection_rows)}\n",
        f"selected_compile_positive_rows\t{len(selected_rows)}\n",
        f"selection_open_negative_or_local_rows\t{len(open_rows)}\n",
        f"negative_syntax_rows\t{len(negative_rows)}\n",
        f"local_exact_plan_rows\t{len(local_exact_rows_list)}\n",
        f"local_exact_consumed_rows\t{len(local_exact_rows)}\n",
        f"reused_candidate_exact_plan_rows\t{len(reused_plan_rows_list)}\n",
        f"reused_candidate_exact_consumed_rows\t{len(reused_plan_rows)}\n",
        f"compile_parser_exact_plan_rows\t{len(compile_parser_plan_rows_list)}\n",
        f"compile_parser_exact_consumed_rows\t{len(consumed_compile_parser_plan_ids)}\n",
        f"literal_lexer_exact_plan_rows\t{len(literal_lexer_plan_rows_list)}\n",
        f"literal_lexer_exact_consumed_rows\t{len(consumed_literal_lexer_plan_ids)}\n",
        f"match_engine_exact_plan_rows\t{len(match_engine_plan_rows_list)}\n",
        f"match_engine_exact_consumed_rows\t{len(consumed_match_engine_plan_ids)}\n",
        f"match_engine_atoms_exact_plan_rows\t{len(match_engine_atoms_plan_rows_list)}\n",
        f"match_engine_atoms_exact_consumed_rows\t{len(consumed_match_engine_atoms_plan_ids)}\n",
        f"match_engine_capture_exact_plan_rows\t{len(match_engine_capture_plan_rows_list)}\n",
        f"match_engine_capture_exact_consumed_rows\t{len(consumed_match_engine_capture_plan_ids)}\n",
        "match_engine_unicode_sets_string_exact_plan_rows\t"
        f"{len(match_engine_unicode_sets_string_plan_rows_list)}\n",
        "match_engine_unicode_sets_string_exact_consumed_rows\t"
        f"{len(consumed_match_engine_unicode_sets_string_plan_ids)}\n",
        "match_engine_unicode_sets_escape_string_exact_plan_rows\t"
        f"{len(match_engine_unicode_sets_escape_string_plan_rows_list)}\n",
        "match_engine_unicode_sets_escape_string_exact_consumed_rows\t"
        f"{len(consumed_match_engine_unicode_sets_escape_string_plan_ids)}\n",
        "match_engine_character_classes_exact_plan_rows\t"
        f"{len(match_engine_character_classes_plan_rows_list)}\n",
        "match_engine_character_classes_exact_consumed_rows\t"
        f"{len(consumed_match_engine_character_classes_plan_ids)}\n",
        "match_engine_concatenation_exact_plan_rows\t"
        f"{len(match_engine_concatenation_plan_rows_list)}\n",
        "match_engine_concatenation_exact_consumed_rows\t"
        f"{len(consumed_match_engine_concatenation_plan_ids)}\n",
        f"match_engine_backreference_exact_plan_rows\t{len(match_engine_backreference_plan_rows_list)}\n",
        f"match_engine_backreference_exact_consumed_rows\t{len(consumed_match_engine_backreference_plan_ids)}\n",
        "match_engine_backreference_matcher_exact_plan_rows\t"
        f"{len(match_engine_backreference_matcher_plan_rows_list)}\n",
        "match_engine_backreference_matcher_exact_consumed_rows\t"
        f"{len(consumed_match_engine_backreference_matcher_plan_ids)}\n",
        f"match_engine_result_exact_plan_rows\t{len(match_engine_result_plan_rows_list)}\n",
        f"match_engine_result_exact_consumed_rows\t{len(consumed_match_engine_result_plan_ids)}\n",
        f"exec_result_matching_exact_plan_rows\t{len(exec_result_matching_plan_rows_list)}\n",
        f"exec_result_matching_exact_consumed_rows\t{len(consumed_exec_result_matching_plan_ids)}\n",
        f"exec_result_capture_exact_plan_rows\t{len(exec_result_capture_plan_rows_list)}\n",
        f"exec_result_capture_exact_consumed_rows\t{len(consumed_exec_result_capture_plan_ids)}\n",
        f"exec_result_exec_exact_plan_rows\t{len(exec_result_exec_plan_rows_list)}\n",
        f"exec_result_exec_exact_consumed_rows\t{len(consumed_exec_result_exec_plan_ids)}\n",
        f"exec_result_indices_exact_plan_rows\t{len(exec_result_indices_plan_rows_list)}\n",
        f"exec_result_indices_exact_consumed_rows\t{len(consumed_exec_result_indices_plan_ids)}\n",
        f"exec_result_instances_exact_plan_rows\t{len(exec_result_instances_plan_rows_list)}\n",
        "exec_result_instances_exact_consumed_rows\t"
        f"{len(consumed_exec_result_instances_plan_ids)}\n",
        f"spec_model_exact_plan_rows\t{len(spec_model_plan_rows_list)}\n",
        f"spec_model_exact_consumed_rows\t{len(consumed_spec_model_plan_ids)}\n",
        f"test262_regexp_executable_case_rows\t{len(test262_literal_lexer_rows_list)}\n",
        "test262_regexp_executable_consumed_rows\t"
        f"{len(consumed_test262_literal_lexer_ids)}\n",
        f"match_engine_start_anchor_exact_plan_rows\t{len(match_engine_start_anchor_plan_rows_list)}\n",
        f"match_engine_start_anchor_exact_consumed_rows\t{len(consumed_match_engine_start_anchor_case_ids)}\n",
        f"match_engine_start_anchor_exact_consumed_requirements\t{len(match_engine_start_anchor_plan_rows)}\n",
        f"match_engine_end_anchor_exact_plan_rows\t{len(match_engine_end_anchor_plan_rows_list)}\n",
        f"match_engine_end_anchor_exact_consumed_rows\t{len(consumed_match_engine_end_anchor_case_ids)}\n",
        f"match_engine_end_anchor_exact_consumed_requirements\t{len(match_engine_end_anchor_plan_rows)}\n",
        f"match_engine_assertion_exact_plan_rows\t{len(match_engine_assertion_plan_rows_list)}\n",
        f"match_engine_assertion_exact_consumed_rows\t{len(consumed_match_engine_assertion_plan_ids)}\n",
        f"match_engine_quantifier_exact_plan_rows\t{len(match_engine_quantifier_plan_rows_list)}\n",
        f"match_engine_quantifier_exact_consumed_rows\t{len(consumed_match_engine_quantifier_plan_ids)}\n",
        f"match_engine_modifier_exact_plan_rows\t{len(match_engine_modifier_plan_rows_list)}\n",
        f"match_engine_modifier_exact_consumed_rows\t{len(consumed_match_engine_modifier_plan_ids)}\n",
        "match_engine_pattern_semantics_exact_plan_rows\t"
        f"{len(match_engine_pattern_semantics_plan_rows_list)}\n",
        "match_engine_pattern_semantics_exact_consumed_rows\t"
        f"{len(consumed_match_engine_pattern_semantics_plan_ids)}\n",
        f"match_engine_annex_b_exact_plan_rows\t{len(match_engine_annex_b_plan_rows_list)}\n",
        f"match_engine_annex_b_exact_consumed_rows\t{len(consumed_match_engine_annex_b_plan_ids)}\n",
        f"match_state_exact_plan_rows\t{len(match_state_plan_rows_list)}\n",
        f"match_state_exact_consumed_rows\t{len(consumed_match_state_plan_ids)}\n",
        f"exactness_audit_rows\t{len(rows)}\n",
        f"potential_exact_ready_rows\t{potential_ready_rows}\n",
        f"open_exactness_rows\t{open_rows_count}\n",
        f"coverage_credit_rows\t{credit_rows}\n",
        f"planned_detail_output\t{detail}\n",
        f"planned_summary_output\t{summary}\n",
        f"dry_run\t{bool_text(args.dry_run)}\n",
    ]
    for name in KNOWN_EXACTNESS_STATES:
        summary_lines.append(f"exactness_state_{name}\t{state_counts.get(name, 0)}\n")
    for name, count in sorted(state_counts.items()):
        if name not in KNOWN_EXACTNESS_STATES:
            summary_lines.append(f"exactness_state_{name}\t{count}\n")
    for name in KNOWN_COVERAGE_CREDITS:
        summary_lines.append(f"coverage_credit_{name}\t{credit_counts.get(name, 0)}\n")
    for name, count in sorted(credit_counts.items()):
        if name not in KNOWN_COVERAGE_CREDITS:
            summary_lines.append(f"coverage_credit_{name}\t{count}\n")
    for name, count in sorted(scope_counts.items()):
        summary_lines.append(f"audit_scope_{name}\t{count}\n")
    for name in KNOWN_EVIDENCE_KINDS:
        summary_lines.append(f"evidence_kind_{name}\t{kind_counts.get(name, 0)}\n")
    for name, count in sorted(kind_counts.items()):
        if name not in KNOWN_EVIDENCE_KINDS:
            summary_lines.append(f"evidence_kind_{name}\t{count}\n")
    for name in KNOWN_NEXT_ACTIONS:
        summary_lines.append(f"next_action_{name}\t{action_counts.get(name, 0)}\n")
    for name, count in sorted(action_counts.items()):
        if name not in KNOWN_NEXT_ACTIONS:
            summary_lines.append(f"next_action_{name}\t{count}\n")
    for name, count in sorted(family_counts.items()):
        summary_lines.append(f"mapping_family_{name}\t{count}\n")
    for name, count in sorted(layer_counts.items()):
        summary_lines.append(f"executable_layer_{name}\t{count}\n")
    for name, count in sorted(reuse_counts_for_rows.items(), key=lambda item: int(item[0])):
        summary_lines.append(f"case_reuse_count_{name}\t{count}\n")

    if args.dry_run:
        print("".join(summary_lines), end="")
        return

    cache.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "audit_id",
        "audit_scope",
        "requirement_id",
        "mapping_family",
        "executable_layer",
        "evidence_kind",
        "case_id",
        "case_source",
        "expected_behavior",
        "selector_tags",
        "selected_feature_tags",
        "selected_matched_selector_tags",
        "selected_missing_selector_tags",
        "case_reuse_count",
        "exactness_audit_state",
        "coverage_credit",
        "next_action",
        "audit_reason",
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
