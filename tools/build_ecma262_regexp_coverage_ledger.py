#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path

from ecma262_tooling import bool_text, read_summary, read_tsv


DETAIL_NAME = "ecma262-regexp-coverage-ledger.tsv"
SUMMARY_NAME = "ecma262-regexp-coverage-ledger.summary"
LOCAL_EXACT_CREDIT = "local_exact_compile_parser_requirement_credit"
REUSED_EXACT_CREDIT = "reused_candidate_exact_compile_parser_requirement_credit"
COMPILE_PARSER_EXACT_CREDIT = "compile_parser_exact_requirement_credit"
LITERAL_LEXER_EXACT_CREDIT = "literal_lexer_exact_requirement_credit"
MATCH_ENGINE_EXACT_CREDIT = "match_engine_exact_requirement_credit"
EXEC_RESULT_EXACT_CREDIT = "exec_result_exact_requirement_credit"
SPEC_MODEL_EXACT_CREDIT = "spec_model_exact_requirement_credit"
TEST262_LITERAL_LEXER_EXACT_CREDIT = "test262_literal_lexer_requirement_credit"
UCD_GENERATED_REQUIREMENT_CREDIT = "ucd_generated_requirement_credit"

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

PRODUCT_FIELDS = [
    "surface_policy_state",
    "surface_decision",
    "surface_area",
    "public_api_status",
    "ocaml_artifact",
    "coverage_action",
    "next_test_artifact",
    "decision_reason",
]

EXACTNESS_CREDIT_FIELDS = [
    "exactness_audit_id",
    "exactness_evidence_kind",
    "exactness_case_id",
    "exactness_case_source",
    "exactness_coverage_credit",
]


def product_overlay(row: dict[str, str], product_rows: dict[str, dict[str, str]]) -> dict[str, str]:
    product = product_rows.get(row["requirement_id"])
    if product is None:
        return {field: "" for field in PRODUCT_FIELDS}
    return {field: product.get(field, "") for field in PRODUCT_FIELDS}


def exactness_overlay(
    row: dict[str, str],
    exactness_credits: dict[str, dict[str, str]],
) -> dict[str, str]:
    exactness = exactness_credits.get(row["requirement_id"])
    if exactness is None:
        return {field: "" for field in EXACTNESS_CREDIT_FIELDS}
    return {
        "exactness_audit_id": exactness["audit_id"],
        "exactness_evidence_kind": exactness["evidence_kind"],
        "exactness_case_id": exactness["case_id"],
        "exactness_case_source": exactness["case_source"],
        "exactness_coverage_credit": exactness["coverage_credit"],
    }


def source_exists(case_source: str) -> bool:
    if case_source.startswith("external/ecma262/"):
        source_path = case_source.split("#", 1)[0]
        return Path(source_path).is_file()
    if case_source.startswith("test/"):
        source_path = case_source.split(":", 1)[0]
        return Path("external/test262", source_path).is_file()
    return False


def read_exactness_credits(path: Path) -> tuple[list[str], dict[str, dict[str, str]]]:
    fieldnames, rows = read_tsv(path)
    required = {
        "audit_id",
        "audit_scope",
        "requirement_id",
        "evidence_kind",
        "case_id",
        "case_source",
        "expected_behavior",
        "selected_missing_selector_tags",
        "case_reuse_count",
        "exactness_audit_state",
        "coverage_credit",
        "next_action",
    }
    missing = required.difference(fieldnames)
    if missing:
        raise SystemExit(
            "missing required exactness audit columns: "
            + ", ".join(sorted(missing))
        )

    credits: dict[str, dict[str, str]] = {}
    for row in rows:
        if row["coverage_credit"] not in {
            LOCAL_EXACT_CREDIT,
            REUSED_EXACT_CREDIT,
            COMPILE_PARSER_EXACT_CREDIT,
            LITERAL_LEXER_EXACT_CREDIT,
            MATCH_ENGINE_EXACT_CREDIT,
            EXEC_RESULT_EXACT_CREDIT,
            SPEC_MODEL_EXACT_CREDIT,
            TEST262_LITERAL_LEXER_EXACT_CREDIT,
        }:
            continue
        requirement_id = row["requirement_id"]
        expected_source_prefix = "external/ecma262/"
        if row["coverage_credit"] == COMPILE_PARSER_EXACT_CREDIT:
            expected = {
                "audit_scope": "ecma262_requirement",
                "evidence_kind": "compile_parser_exact_case",
                "selected_missing_selector_tags": "",
                "case_reuse_count": "1",
                "exactness_audit_state": "covered_by_compile_parser_exact",
                "next_action": "none_covered_by_compile_parser_exact",
            }
            expected_case_prefix = f"compile-parser-exact:{requirement_id}:"
        elif row["coverage_credit"] == LITERAL_LEXER_EXACT_CREDIT:
            expected = {
                "audit_scope": "ecma262_requirement",
                "evidence_kind": "literal_lexer_exact_case",
                "expected_behavior": "literal_parse_ok",
                "selected_missing_selector_tags": "",
                "case_reuse_count": "1",
                "exactness_audit_state": "covered_by_literal_lexer_exact",
                "next_action": "none_covered_by_literal_lexer_exact",
            }
            expected_case_prefix = f"literal-lexer-exact:{requirement_id}:"
        elif row["coverage_credit"] == MATCH_ENGINE_EXACT_CREDIT:
            if (
                row["evidence_kind"] == "match_engine_exact_case"
                and row["expected_behavior"] not in {"search_true", "search_false"}
            ):
                raise SystemExit(
                    f"match-engine exact credit row {requirement_id} has "
                    f"expected_behavior={row['expected_behavior']!r}"
                )
            elif (
                row["evidence_kind"] == "match_engine_atoms_exact_case"
                and not row["expected_behavior"]
            ):
                raise SystemExit(
                    f"match-engine atom exact credit row {requirement_id} has "
                    "empty expected_behavior"
                )
            elif (
                row["evidence_kind"] == "match_engine_capture_exact_case"
                and row["expected_behavior"] != "capture_model_observable"
            ):
                raise SystemExit(
                    f"match-engine capture exact credit row {requirement_id} "
                    f"has expected_behavior={row['expected_behavior']!r}"
                )
            elif (
                row["evidence_kind"]
                == "match_engine_unicode_sets_string_exact_case"
                and row["expected_behavior"]
                != "unicode_sets_string_element_model_observable"
            ):
                raise SystemExit(
                    "match-engine UnicodeSets string exact credit row "
                    f"{requirement_id} has "
                    f"expected_behavior={row['expected_behavior']!r}"
                )
            elif (
                row["evidence_kind"]
                == "match_engine_unicode_sets_escape_string_exact_case"
                and row["expected_behavior"]
                != "unicode_sets_string_element_model_observable"
            ):
                raise SystemExit(
                    "match-engine UnicodeSets escape string exact credit row "
                    f"{requirement_id} has "
                    f"expected_behavior={row['expected_behavior']!r}"
                )
            elif (
                row["evidence_kind"] == "match_engine_character_classes_exact_case"
                and row["expected_behavior"]
                not in {
                    "character_range_exact_plan_observable",
                    "character_complement_exact_plan_observable",
                }
            ):
                raise SystemExit(
                    "match-engine character-class exact credit row "
                    f"{requirement_id} has "
                    f"expected_behavior={row['expected_behavior']!r}"
                )
            elif (
                row["evidence_kind"] == "match_engine_concatenation_exact_case"
                and row["expected_behavior"]
                != "match_sequence_exact_plan_observable"
            ):
                raise SystemExit(
                    "match-engine concatenation exact credit row "
                    f"{requirement_id} has "
                    f"expected_behavior={row['expected_behavior']!r}"
                )
            elif (
                row["evidence_kind"] == "match_engine_backreference_exact_case"
                and row["expected_behavior"] != "backreference_model_observable"
            ):
                raise SystemExit(
                    f"match-engine backreference exact credit row {requirement_id} "
                    f"has expected_behavior={row['expected_behavior']!r}"
                )
            elif (
                row["evidence_kind"]
                == "match_engine_backreference_matcher_exact_case"
                and row["expected_behavior"]
                != "backreference_matcher_exact_plan_observable"
            ):
                raise SystemExit(
                    "match-engine BackreferenceMatcher exact credit row "
                    f"{requirement_id} has "
                    f"expected_behavior={row['expected_behavior']!r}"
                )
            elif (
                row["evidence_kind"] == "match_engine_result_exact_case"
                and row["expected_behavior"] != "exec_left_priority_match"
            ):
                raise SystemExit(
                    f"match-engine result exact credit row {requirement_id} has "
                    f"expected_behavior={row['expected_behavior']!r}"
                )
            elif (
                row["evidence_kind"] == "match_engine_start_anchor_exact_case"
                and row["expected_behavior"] != "start_anchor_exact_plan_observable"
            ):
                raise SystemExit(
                    f"match-engine start-anchor exact credit row {requirement_id} "
                    f"has expected_behavior={row['expected_behavior']!r}"
                )
            elif (
                row["evidence_kind"] == "match_engine_end_anchor_exact_case"
                and row["expected_behavior"] != "end_anchor_exact_plan_observable"
            ):
                raise SystemExit(
                    f"match-engine end-anchor exact credit row {requirement_id} "
                    f"has expected_behavior={row['expected_behavior']!r}"
                )
            elif (
                row["evidence_kind"] == "match_engine_quantifier_exact_case"
                and row["expected_behavior"] != "quantifier_exact_plan_observable"
            ):
                raise SystemExit(
                    f"match-engine quantifier exact credit row {requirement_id} "
                    f"has expected_behavior={row['expected_behavior']!r}"
                )
            elif (
                row["evidence_kind"] == "match_engine_modifier_exact_case"
                and row["expected_behavior"] != "modifier_exact_plan_observable"
            ):
                raise SystemExit(
                    f"match-engine modifier exact credit row {requirement_id} "
                    f"has expected_behavior={row['expected_behavior']!r}"
                )
            elif (
                row["evidence_kind"] == "match_engine_assertion_exact_case"
                and row["expected_behavior"] != "assertion_exact_plan_observable"
            ):
                raise SystemExit(
                    f"match-engine assertion exact credit row {requirement_id} "
                    f"has expected_behavior={row['expected_behavior']!r}"
                )
            elif (
                row["evidence_kind"]
                == "match_engine_pattern_semantics_exact_case"
                and row["expected_behavior"]
                != "pattern_semantics_exact_plan_observable"
            ):
                raise SystemExit(
                    "match-engine Pattern Semantics exact credit row "
                    f"{requirement_id} has "
                    f"expected_behavior={row['expected_behavior']!r}"
                )
            elif (
                row["evidence_kind"] == "match_engine_annex_b_exact_case"
                and row["expected_behavior"] != "annex_b_exact_plan_observable"
            ):
                raise SystemExit(
                    f"match-engine Annex B exact credit row {requirement_id} "
                    f"has expected_behavior={row['expected_behavior']!r}"
                )
            elif (
                row["evidence_kind"] == "match_state_exact_case"
                and row["expected_behavior"] != "match_state_model_observable"
            ):
                raise SystemExit(
                    f"match-state exact credit row {requirement_id} has "
                    f"expected_behavior={row['expected_behavior']!r}"
                )
            elif row["evidence_kind"] not in {
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
                "match_engine_start_anchor_exact_case",
                "match_engine_end_anchor_exact_case",
                "match_engine_assertion_exact_case",
                "match_engine_quantifier_exact_case",
                "match_engine_modifier_exact_case",
                "match_engine_pattern_semantics_exact_case",
                "match_engine_annex_b_exact_case",
                "match_state_exact_case",
            }:
                raise SystemExit(
                    f"match-engine exact credit row {requirement_id} has "
                    f"evidence_kind={row['evidence_kind']!r}"
                )
            expected = {
                "audit_scope": "ecma262_requirement",
                "selected_missing_selector_tags": "",
                "case_reuse_count": "1",
                "exactness_audit_state": "covered_by_match_engine_exact",
                "next_action": "none_covered_by_match_engine_exact",
            }
            if row["evidence_kind"] == "match_engine_exact_case":
                expected_case_prefix = f"match-engine-exact:{requirement_id}:"
            elif row["evidence_kind"] == "match_engine_atoms_exact_case":
                expected_case_prefix = (
                    f"match-engine-atoms-exact:{requirement_id}:"
                )
            elif row["evidence_kind"] == "match_engine_capture_exact_case":
                expected_case_prefix = (
                    f"match-engine-capture-exact:{requirement_id}:"
                )
            elif (
                row["evidence_kind"]
                == "match_engine_unicode_sets_string_exact_case"
            ):
                expected_case_prefix = (
                    f"match-engine-unicode-sets-string-exact:{requirement_id}:"
                )
            elif (
                row["evidence_kind"]
                == "match_engine_unicode_sets_escape_string_exact_case"
            ):
                expected_case_prefix = (
                    "match-engine-unicode-sets-escape-string-exact:"
                    f"{requirement_id}:"
                )
            elif row["evidence_kind"] == "match_engine_character_classes_exact_case":
                expected_case_prefix = (
                    f"match-engine-character-classes-exact:{requirement_id}:"
                )
            elif row["evidence_kind"] == "match_engine_concatenation_exact_case":
                expected_case_prefix = (
                    f"match-engine-concatenation-exact:{requirement_id}:"
                )
            elif row["evidence_kind"] == "match_engine_backreference_exact_case":
                expected_case_prefix = (
                    f"match-engine-backreference-exact:{requirement_id}:"
                )
            elif (
                row["evidence_kind"]
                == "match_engine_backreference_matcher_exact_case"
            ):
                expected_case_prefix = (
                    "match-engine-backreference-matcher-exact:"
                    f"{requirement_id}:"
                )
            elif row["evidence_kind"] == "match_engine_result_exact_case":
                expected_case_prefix = (
                    f"match-engine-result-exact:{requirement_id}:"
                )
            elif row["evidence_kind"] == "match_engine_start_anchor_exact_case":
                expected_case_prefix = (
                    f"match-engine-start-anchor-exact:{requirement_id}:"
                )
            elif row["evidence_kind"] == "match_engine_end_anchor_exact_case":
                expected_case_prefix = (
                    f"match-engine-end-anchor-exact:{requirement_id}:"
                )
            elif row["evidence_kind"] == "match_engine_quantifier_exact_case":
                expected_case_prefix = (
                    f"match-engine-quantifier-exact:{requirement_id}:"
                )
            elif row["evidence_kind"] == "match_engine_modifier_exact_case":
                expected_case_prefix = (
                    f"match-engine-modifier-exact:{requirement_id}:"
                )
            elif row["evidence_kind"] == "match_engine_assertion_exact_case":
                expected_case_prefix = (
                    f"match-engine-assertion-exact:{requirement_id}:"
                )
            elif (
                row["evidence_kind"]
                == "match_engine_pattern_semantics_exact_case"
            ):
                expected_case_prefix = (
                    f"match-engine-pattern-semantics-exact:{requirement_id}:"
                )
            elif row["evidence_kind"] == "match_engine_annex_b_exact_case":
                expected_case_prefix = (
                    f"match-engine-annex-b-exact:{requirement_id}:"
                )
            else:
                expected_case_prefix = f"match-state-exact:{requirement_id}:"
        elif row["coverage_credit"] == EXEC_RESULT_EXACT_CREDIT:
            if row["evidence_kind"] not in {
                "exec_result_matching_exact_case",
                "exec_result_exec_exact_case",
                "exec_result_capture_exact_case",
                "exec_result_indices_exact_case",
                "exec_result_instances_exact_case",
            }:
                raise SystemExit(
                    f"exec-result exact credit row {requirement_id} has "
                    f"evidence_kind={row['evidence_kind']!r}"
                )
            allowed_matching_behaviors = {
                "exec_search_loop_reaches_later_match",
                "exec_invokes_matcher_at_current_index",
                "exec_handles_match_failure_before_success",
                "exec_advances_ascii_index_after_failure",
                "exec_takes_success_branch",
                "exec_exposes_end_index",
                "exec_exposes_match_record_span",
                "exec_exposes_matched_substring",
            }
            allowed_capture_behaviors = {
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
            }
            allowed_exec_behaviors = {
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
            }
            allowed_indices_behaviors = {
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
            }
            allowed_instance_behaviors = {
                "regexp_instance_internal_slots_observed",
                "regexp_instance_last_index_property_observed",
                "last_index_integral_start_property_attributes_observed",
            }
            if (
                row["evidence_kind"] == "exec_result_matching_exact_case"
                and row["expected_behavior"] not in allowed_matching_behaviors
                and not row["expected_behavior"].endswith("_observed")
            ):
                raise SystemExit(
                    f"exec-result exact credit row {requirement_id} has "
                    f"expected_behavior={row['expected_behavior']!r}"
                )
            if (
                row["evidence_kind"] == "exec_result_capture_exact_case"
                and row["expected_behavior"] not in allowed_capture_behaviors
            ):
                raise SystemExit(
                    f"exec-result exact credit row {requirement_id} has "
                    f"expected_behavior={row['expected_behavior']!r}"
                )
            if (
                row["evidence_kind"] == "exec_result_exec_exact_case"
                and row["expected_behavior"] not in allowed_exec_behaviors
            ):
                raise SystemExit(
                    f"exec-result exact credit row {requirement_id} has "
                    f"expected_behavior={row['expected_behavior']!r}"
                )
            if (
                row["evidence_kind"] == "exec_result_indices_exact_case"
                and row["expected_behavior"] not in allowed_indices_behaviors
            ):
                raise SystemExit(
                    f"exec-result exact credit row {requirement_id} has "
                    f"expected_behavior={row['expected_behavior']!r}"
                )
            if (
                row["evidence_kind"] == "exec_result_instances_exact_case"
                and row["expected_behavior"] not in allowed_instance_behaviors
            ):
                raise SystemExit(
                    f"exec-result exact credit row {requirement_id} has "
                    f"expected_behavior={row['expected_behavior']!r}"
                )
            expected = {
                "audit_scope": "ecma262_requirement",
                "selected_missing_selector_tags": "",
                "case_reuse_count": "1",
                "exactness_audit_state": "covered_by_exec_result_exact",
                "next_action": "none_covered_by_exec_result_exact",
            }
            if row["evidence_kind"] == "exec_result_matching_exact_case":
                expected_case_prefix = f"exec-result-matching-exact:{requirement_id}:"
            elif row["evidence_kind"] == "exec_result_exec_exact_case":
                expected_case_prefix = f"exec-result-exec-exact:{requirement_id}:"
            elif row["evidence_kind"] == "exec_result_capture_exact_case":
                expected_case_prefix = f"exec-result-capture-exact:{requirement_id}:"
            elif row["evidence_kind"] == "exec_result_indices_exact_case":
                expected_case_prefix = f"exec-result-indices-exact:{requirement_id}:"
            else:
                expected_case_prefix = (
                    f"exec-result-instances-exact:{requirement_id}:"
                )
        elif row["coverage_credit"] == SPEC_MODEL_EXACT_CREDIT:
            if row["evidence_kind"] != "spec_model_exact_case":
                raise SystemExit(
                    f"spec-model exact credit row {requirement_id} has "
                    f"evidence_kind={row['evidence_kind']!r}"
                )
            if row["expected_behavior"] not in {
                "lexical_grammar_source_character_goal_model_observed",
                "syntactic_token_stream_boundary_policy_observed",
                "regexp_grammar_pattern_source_model_observed",
                "lexical_regexp_grammar_notation_boundary_observed",
            }:
                raise SystemExit(
                    f"spec-model exact credit row {requirement_id} has "
                    f"expected_behavior={row['expected_behavior']!r}"
                )
            expected = {
                "audit_scope": "ecma262_requirement",
                "evidence_kind": "spec_model_exact_case",
                "selected_missing_selector_tags": "",
                "case_reuse_count": "1",
                "exactness_audit_state": "covered_by_spec_model_exact",
                "next_action": "none_covered_by_spec_model_exact",
            }
            expected_case_prefix = f"spec-model-exact:{requirement_id}:"
        elif row["coverage_credit"] == TEST262_LITERAL_LEXER_EXACT_CREDIT:
            if row["evidence_kind"] != "test262_literal_lexer_exact_case":
                raise SystemExit(
                    f"test262 literal-lexer exact credit row {requirement_id} "
                    f"has evidence_kind={row['evidence_kind']!r}"
                )
            if row["expected_behavior"] not in TEST262_LITERAL_LEXER_BEHAVIORS:
                raise SystemExit(
                    f"test262 literal-lexer exact credit row {requirement_id} "
                    f"has expected_behavior={row['expected_behavior']!r}"
                )
            expected = {
                "audit_scope": "ecma262_requirement",
                "evidence_kind": "test262_literal_lexer_exact_case",
                "selected_missing_selector_tags": "",
                "case_reuse_count": "1",
                "exactness_audit_state": "covered_by_test262_literal_lexer_exact",
                "next_action": "none_covered_by_test262_literal_lexer_exact",
            }
            expected_case_prefix = (
                f"test262-regexp-executable:{requirement_id}:"
            )
            expected_source_prefix = "test/"
        elif row["coverage_credit"] == LOCAL_EXACT_CREDIT:
            expected = {
                "audit_scope": "ecma262_requirement",
                "evidence_kind": "local_exact_compile_parser_case",
                "expected_behavior": "compile_ok",
                "selected_missing_selector_tags": "",
                "case_reuse_count": "1",
                "exactness_audit_state": "covered_by_local_exact_compile_parser",
                "next_action": "none_covered_by_local_exact_compile_parser",
            }
            expected_case_prefix = f"local-exact:{requirement_id}:"
        else:
            expected = {
                "audit_scope": "ecma262_requirement",
                "evidence_kind": "reused_candidate_exact_compile_parser_case",
                "expected_behavior": "compile_ok",
                "selected_missing_selector_tags": "",
                "case_reuse_count": "1",
                "exactness_audit_state": "covered_by_reused_candidate_exact_compile_parser",
                "next_action": "none_covered_by_reused_candidate_exact_compile_parser",
            }
            expected_case_prefix = f"reused-exact:{requirement_id}:"
        if row["coverage_credit"] not in {
            COMPILE_PARSER_EXACT_CREDIT,
            LITERAL_LEXER_EXACT_CREDIT,
            MATCH_ENGINE_EXACT_CREDIT,
            EXEC_RESULT_EXACT_CREDIT,
            SPEC_MODEL_EXACT_CREDIT,
            TEST262_LITERAL_LEXER_EXACT_CREDIT,
        }:
            expected["expected_behavior"] = "compile_ok"
        elif row["coverage_credit"] == COMPILE_PARSER_EXACT_CREDIT:
            if row["expected_behavior"] not in {"compile_ok", "compile_error"}:
                raise SystemExit(
                    f"compile/parser exact credit row {requirement_id} has "
                    f"expected_behavior={row['expected_behavior']!r}"
                )
        for field, expected_value in expected.items():
            if row[field] != expected_value:
                raise SystemExit(
                    f"exactness credit row {requirement_id} has "
                    f"{field}={row[field]!r}; expected {expected_value!r}"
                )
        if not requirement_id:
            raise SystemExit(f"exactness credit row {row['audit_id']} has empty requirement_id")
        if not row["case_id"].startswith(expected_case_prefix):
            raise SystemExit(
                f"exactness credit row {requirement_id} has invalid case_id "
                f"{row['case_id']!r}"
            )
        if not row["case_source"].startswith(expected_source_prefix):
            raise SystemExit(
                f"exactness credit row {requirement_id} has invalid source "
                f"{row['case_source']!r}; expected prefix "
                f"{expected_source_prefix!r}"
            )
        if not source_exists(row["case_source"]):
            raise SystemExit(
                f"exactness credit row {requirement_id} source missing: "
                f"{row['case_source']}"
            )
        if requirement_id in credits:
            raise SystemExit(f"duplicate exactness credit for {requirement_id}")
        credits[requirement_id] = row
    return fieldnames, credits


def read_ucd_generated_credits(
    path: Path,
    ucd_dir: Path,
) -> tuple[list[str], dict[str, dict[str, str]]]:
    if not path.is_file():
        return [], {}

    fieldnames, rows = read_tsv(path)
    required = {
        "case_id",
        "requirement_id",
        "source_file",
        "ucd_version",
        "ucd_model_family",
        "ucd_route",
        "ucd_files",
        "expected_behavior",
        "coverage_credit",
        "case_state",
        "target_test_artifact",
        "next_action",
    }
    missing = required.difference(fieldnames)
    if missing:
        raise SystemExit(
            "missing required UCD generated case columns: "
            + ", ".join(sorted(missing))
        )

    credits: dict[str, dict[str, str]] = {}
    for row in rows:
        if row["coverage_credit"] != UCD_GENERATED_REQUIREMENT_CREDIT:
            continue
        requirement_id = row["requirement_id"]
        expected_case_prefix = f"ucd-generated:{requirement_id}:"
        expected = {
            "ucd_version": "16.0.0",
            "expected_behavior": "ucd_generated_requirement_covered",
            "case_state": "covered_by_ucd_generated_tests",
            "target_test_artifact": "test/test_ecma262_ucd_generated_cases.ml",
            "next_action": "none_covered_by_ucd_generated_tests",
        }
        for field, expected_value in expected.items():
            if row[field] != expected_value:
                raise SystemExit(
                    f"UCD generated credit row {requirement_id} has "
                    f"{field}={row[field]!r}; expected {expected_value!r}"
                )
        if not row["case_id"].startswith(expected_case_prefix):
            raise SystemExit(
                f"UCD generated credit row {requirement_id} has invalid "
                f"case_id {row['case_id']!r}"
            )
        if not row["ucd_model_family"]:
            raise SystemExit(
                f"UCD generated credit row {requirement_id} has empty model family"
            )
        if not row["ucd_route"]:
            raise SystemExit(
                f"UCD generated credit row {requirement_id} has empty route"
            )
        if not Path(row["source_file"]).is_file():
            raise SystemExit(
                f"UCD generated credit row {requirement_id} source missing: "
                f"{row['source_file']}"
            )
        if not Path(row["target_test_artifact"]).is_file():
            raise SystemExit(
                f"UCD generated credit row {requirement_id} target test missing: "
                f"{row['target_test_artifact']}"
            )
        ucd_files = [name for name in row["ucd_files"].split(",") if name]
        if not ucd_files:
            raise SystemExit(
                f"UCD generated credit row {requirement_id} has no UCD files"
            )
        for name in ucd_files:
            if not (ucd_dir / name).is_file():
                raise SystemExit(
                    f"UCD generated credit row {requirement_id} UCD source "
                    f"missing: {ucd_dir / name}"
                )
        if requirement_id in credits:
            raise SystemExit(f"duplicate UCD generated credit for {requirement_id}")
        credits[requirement_id] = row
    return fieldnames, credits


def ledger_for(
    row: dict[str, str],
    product: dict[str, str],
    exactness: dict[str, str],
    ucd_generated: dict[str, str] | None,
) -> dict[str, str]:
    route_status = row["route_status"]

    if exactness["exactness_coverage_credit"]:
        expected_route = (
            "needs_test262_executable_extractor"
            if exactness["exactness_coverage_credit"] == TEST262_LITERAL_LEXER_EXACT_CREDIT
            else "needs_requirement_to_test_case_mapping"
        )
        if route_status != expected_route:
            raise SystemExit(
                f"exactness credit for {row['requirement_id']} cannot apply to "
                f"route_status {route_status}"
            )
        owner = "local_exact_tests"
        if exactness["exactness_coverage_credit"] == COMPILE_PARSER_EXACT_CREDIT:
            state = "covered_by_compile_parser_exact"
            reason = (
                "requirement row has exact post-credit compile/parser evidence "
                "with requirement-level credit"
            )
        elif exactness["exactness_coverage_credit"] == LITERAL_LEXER_EXACT_CREDIT:
            state = "covered_by_literal_lexer_exact"
            reason = (
                "requirement row has exact literal lexer evidence with "
                "requirement-level credit"
            )
        elif exactness["exactness_coverage_credit"] == MATCH_ENGINE_EXACT_CREDIT:
            state = "covered_by_match_engine_exact"
            reason = (
                "requirement row has exact match-engine evidence with "
                "requirement-level credit"
            )
        elif exactness["exactness_coverage_credit"] == EXEC_RESULT_EXACT_CREDIT:
            state = "covered_by_exec_result_exact"
            reason = (
                "requirement row has exact exec-result evidence with "
                "requirement-level credit"
            )
        elif exactness["exactness_coverage_credit"] == SPEC_MODEL_EXACT_CREDIT:
            state = "covered_by_spec_model_exact"
            reason = (
                "requirement row has exact spec-model evidence with "
                "requirement-level credit"
            )
        elif (
            exactness["exactness_coverage_credit"]
            == TEST262_LITERAL_LEXER_EXACT_CREDIT
        ):
            state = "covered_by_test262_literal_lexer_exact"
            owner = "test262_executable_extractor"
            reason = (
                "requirement row has exact test262 literal-lexer evidence with "
                "requirement-level credit"
            )
        elif exactness["exactness_coverage_credit"] == LOCAL_EXACT_CREDIT:
            state = "covered_by_local_exact_compile_parser"
            reason = (
                "requirement row has exact local compile/parser evidence with "
                "requirement-level credit"
            )
        elif exactness["exactness_coverage_credit"] == REUSED_EXACT_CREDIT:
            state = "covered_by_reused_candidate_exact_compile_parser"
            reason = (
                "requirement row has exact reused-candidate compile/parser "
                "evidence with requirement-level credit"
            )
        else:
            raise SystemExit(
                f"unsupported exactness credit {exactness['exactness_coverage_credit']!r} "
                f"for {row['requirement_id']}"
            )
        return {
            "ledger_state": state,
            "ledger_bucket": "covered",
            "release_gate": "not_blocking",
            "coverage_owner": owner,
            "ledger_next_artifact": "none",
            "ledger_reason": reason,
        }

    if route_status == "container_marker":
        return {
            "ledger_state": "not_direct_requirement",
            "ledger_bucket": "closed_not_direct_requirement",
            "release_gate": "not_blocking",
            "coverage_owner": "ecma262_requirement_extraction",
            "ledger_next_artifact": "none",
            "ledger_reason": "container clause has no direct extracted requirement rows; child clauses carry concrete requirements",
        }

    if route_status == "needs_product_policy_decision":
        decision = product.get("surface_decision", "")
        if not decision:
            return {
                "ledger_state": "open_product_surface_decision_missing",
                "ledger_bucket": "open_policy",
                "release_gate": "blocking",
                "coverage_owner": "product_surface_policy",
                "ledger_next_artifact": "product_surface_policy_decision",
                "ledger_reason": "product-surface row has no generated policy decision",
            }
        if decision == "non_applicable_with_reason":
            return {
                "ledger_state": "non_applicable_with_reason",
                "ledger_bucket": "closed_non_applicable",
                "release_gate": "not_blocking",
                "coverage_owner": "product_surface_policy",
                "ledger_next_artifact": product["next_test_artifact"],
                "ledger_reason": product["decision_reason"],
            }
        if decision == "ocaml_adapter_requirement":
            if (
                product.get("surface_area") == "search_adapter"
                and product.get("ocaml_artifact") == "Ecma_regex.search_index"
                and Path(product["next_test_artifact"]).is_file()
            ):
                return {
                    "ledger_state": "covered_by_search_adapter",
                    "ledger_bucket": "covered",
                    "release_gate": "not_blocking",
                    "coverage_owner": "product_surface_adapter",
                    "ledger_next_artifact": "none",
                    "ledger_reason": "search adapter rows are covered by executable Ecma_regex.search_index tests",
                }
            if (
                product.get("surface_area") == "match_adapter"
                and product.get("ocaml_artifact") == "Ecma_regex.match_"
                and Path(product["next_test_artifact"]).is_file()
            ):
                return {
                    "ledger_state": "covered_by_match_adapter",
                    "ledger_bucket": "covered",
                    "release_gate": "not_blocking",
                    "coverage_owner": "product_surface_adapter",
                    "ledger_next_artifact": "none",
                    "ledger_reason": "match adapter rows are covered by executable Ecma_regex.match_ tests",
                }
            if (
                product.get("surface_area") == "match_all_adapter"
                and product.get("ocaml_artifact") == "Ecma_regex.match_all"
                and Path(product["next_test_artifact"]).is_file()
            ):
                return {
                    "ledger_state": "covered_by_match_all_adapter",
                    "ledger_bucket": "covered",
                    "release_gate": "not_blocking",
                    "coverage_owner": "product_surface_adapter",
                    "ledger_next_artifact": "none",
                    "ledger_reason": "matchAll adapter rows are covered by executable Ecma_regex.match_all tests",
                }
            if (
                product.get("surface_area") == "split_adapter"
                and product.get("ocaml_artifact") == "Ecma_regex.split"
                and Path(product["next_test_artifact"]).is_file()
            ):
                return {
                    "ledger_state": "covered_by_split_adapter",
                    "ledger_bucket": "covered",
                    "release_gate": "not_blocking",
                    "coverage_owner": "product_surface_adapter",
                    "ledger_next_artifact": "none",
                    "ledger_reason": "split adapter rows are covered by executable Ecma_regex.split tests",
                }
            if (
                product.get("surface_area") == "replace_adapter"
                and product.get("ocaml_artifact") == "Ecma_regex.replace"
                and Path(product["next_test_artifact"]).is_file()
            ):
                return {
                    "ledger_state": "covered_by_replace_adapter",
                    "ledger_bucket": "covered",
                    "release_gate": "not_blocking",
                    "coverage_owner": "product_surface_adapter",
                    "ledger_next_artifact": "none",
                    "ledger_reason": "replace adapter rows are covered by executable Ecma_regex.replace tests",
                }
            if (
                product.get("surface_area") == "regexp_escape_adapter"
                and product.get("ocaml_artifact") == "Ecma_regex.escape"
                and Path(product["next_test_artifact"]).is_file()
            ):
                return {
                    "ledger_state": "covered_by_escape_adapter",
                    "ledger_bucket": "covered",
                    "release_gate": "not_blocking",
                    "coverage_owner": "product_surface_adapter",
                    "ledger_next_artifact": "none",
                    "ledger_reason": "RegExp.escape adapter rows are covered by executable Ecma_regex.escape tests",
                }
            return {
                "ledger_state": "open_adapter_tests_missing",
                "ledger_bucket": "open_tests_and_implementation",
                "release_gate": "blocking",
                "coverage_owner": "product_surface_adapter",
                "ledger_next_artifact": product["next_test_artifact"],
                "ledger_reason": "row is routed to an explicit OCaml adapter, but executable adapter tests and implementation are not present",
            }
        if decision == "core_library_requirement":
            return {
                "ledger_state": "open_core_library_tests_missing",
                "ledger_bucket": "open_tests_and_implementation",
                "release_gate": "blocking",
                "coverage_owner": "core_library",
                "ledger_next_artifact": product["next_test_artifact"],
                "ledger_reason": "row is routed to the core library surface, but exact tests and implementation are not present",
            }
        if decision == "test_adapter_only_requirement":
            return {
                "ledger_state": "open_test_adapter_tests_missing",
                "ledger_bucket": "open_tests",
                "release_gate": "blocking",
                "coverage_owner": "test_adapter",
                "ledger_next_artifact": product["next_test_artifact"],
                "ledger_reason": "row is routed to test-adapter evidence, but executable adapter tests are not present",
            }
        if decision == "deferred_with_reason":
            return {
                "ledger_state": "open_deferred_product_decision",
                "ledger_bucket": "open_policy",
                "release_gate": "blocking",
                "coverage_owner": "product_surface_policy",
                "ledger_next_artifact": product["next_test_artifact"],
                "ledger_reason": product["decision_reason"],
            }
        raise SystemExit(
            f"unknown product-surface decision {decision!r} for {row['requirement_id']}"
        )

    if route_status == "needs_ucd_generated_tests" and ucd_generated is not None:
        return {
            "ledger_state": "covered_by_ucd_generated_tests",
            "ledger_bucket": "covered",
            "release_gate": "not_blocking",
            "coverage_owner": "ucd_generated_tests",
            "ledger_next_artifact": "none",
            "ledger_reason": (
                "Unicode-sensitive requirement row is covered by generated "
                "UCD 16.0.0 cases in test/test_ecma262_ucd_generated_cases.ml"
            ),
        }

    if route_status == "needs_ucd_generated_tests":
        return {
            "ledger_state": "open_ucd_generated_tests_missing",
            "ledger_bucket": "open_generated_tests",
            "release_gate": "blocking",
            "coverage_owner": "ucd_generated_tests",
            "ledger_next_artifact": "tools/build_ucd_regexp_tests.py",
            "ledger_reason": "Unicode-sensitive requirement needs generated UCD 16.0.0 tests and implementation evidence",
        }

    if route_status == "needs_test262_executable_extractor":
        return {
            "ledger_state": "open_test262_executable_extractor_missing",
            "ledger_bucket": "open_extractor",
            "release_gate": "blocking",
            "coverage_owner": "test262_executable_extractor",
            "ledger_next_artifact": "tools/extract_test262_regexp_executable_cases.py",
            "ledger_reason": "test262 signal is inventory-level only; executable extractor is missing",
        }

    if route_status == "needs_requirement_to_test_case_mapping":
        return {
            "ledger_state": "open_requirement_to_test_mapping_missing",
            "ledger_bucket": "open_exact_mapping",
            "release_gate": "blocking",
            "coverage_owner": "ecma262_requirement_to_test_mapping",
            "ledger_next_artifact": "tools/map_ecma262_requirements_to_tests.py",
            "ledger_reason": "requirement has coarse corpus signal but no exact requirement-to-test mapping",
        }

    if route_status == "needs_local_exact_tests":
        return {
            "ledger_state": "open_local_exact_tests_missing",
            "ledger_bucket": "open_local_tests",
            "release_gate": "blocking",
            "coverage_owner": "local_exact_tests",
            "ledger_next_artifact": "test/test_ecma262_local_exact.ml",
            "ledger_reason": "requirement needs local exact tests because corpus evidence is not enough",
        }

    raise SystemExit(f"unknown route_status {route_status!r} for {row['requirement_id']}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache", default="cache")
    parser.add_argument(
        "--requirement-mapping",
        default="cache/ecma262-regexp-requirement-mapping.tsv",
    )
    parser.add_argument(
        "--product-surface-matrix",
        default="cache/ecma262-regexp-product-surface-matrix.tsv",
    )
    parser.add_argument(
        "--test262-summary",
        default="cache/test262-regexp-coverage-matrix.summary",
    )
    parser.add_argument(
        "--test-evidence-summary",
        default="cache/ecma262-regexp-test-evidence.summary",
    )
    parser.add_argument(
        "--exactness-audit-summary",
        default="cache/ecma262-regexp-exactness-audit.summary",
    )
    parser.add_argument(
        "--exactness-audit",
        default="cache/ecma262-regexp-exactness-audit.tsv",
    )
    parser.add_argument(
        "--ucd-generated-cases",
        default="cache/ecma262-regexp-ucd-generated-cases.tsv",
    )
    parser.add_argument(
        "--selector-gap-summary",
        default="cache/ecma262-regexp-selector-gap-worklist.summary",
    )
    parser.add_argument(
        "--local-exact-plan-summary",
        default="cache/ecma262-regexp-local-exact-plan.summary",
    )
    parser.add_argument("--ucd-dir", default="external/ucd/16.0.0")
    parser.add_argument(
        "--json-schema-harness",
        default="test/test_json_schema_corpus.ml",
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--fail-on-open",
        action="store_true",
        help="exit with status 1 when release-blocking rows remain open",
    )
    args = parser.parse_args()

    cache = Path(args.cache)
    requirement_mapping = Path(args.requirement_mapping)
    product_surface_matrix = Path(args.product_surface_matrix)
    test262_summary = Path(args.test262_summary)
    test_evidence_summary = Path(args.test_evidence_summary)
    exactness_audit_summary = Path(args.exactness_audit_summary)
    exactness_audit_detail = Path(args.exactness_audit)
    ucd_generated_cases = Path(args.ucd_generated_cases)
    selector_gap_summary = Path(args.selector_gap_summary)
    local_exact_plan_summary = Path(args.local_exact_plan_summary)
    detail = cache / DETAIL_NAME
    summary = cache / SUMMARY_NAME

    if not requirement_mapping.is_file():
        raise SystemExit(
            f"missing ECMA-262 requirement mapping at {requirement_mapping}; "
            "run tools/build_ecma262_regexp_requirement_mapping.py first"
        )
    if not product_surface_matrix.is_file():
        raise SystemExit(
            f"missing ECMA-262 product-surface matrix at {product_surface_matrix}; "
            "run tools/build_ecma262_regexp_product_surface_matrix.py first"
        )
    if not exactness_audit_detail.is_file():
        raise SystemExit(
            f"missing ECMA-262 exactness audit at {exactness_audit_detail}; "
            "run tools/build_ecma262_regexp_exactness_audit.py first"
        )

    input_fieldnames, input_rows = read_tsv(requirement_mapping)
    product_fieldnames, product_rows_list = read_tsv(product_surface_matrix)
    _exactness_fieldnames, exactness_credits = read_exactness_credits(exactness_audit_detail)
    _ucd_generated_fieldnames, ucd_generated_credits = read_ucd_generated_credits(
        ucd_generated_cases,
        Path(args.ucd_dir),
    )

    for required in ["requirement_id", "route_status", "requirement_kind"]:
        if required not in input_fieldnames:
            raise SystemExit(f"missing required mapping column {required!r}")
    for required in ["requirement_id", *PRODUCT_FIELDS]:
        if required not in product_fieldnames:
            raise SystemExit(f"missing required product column {required!r}")

    product_rows = {}
    for row in product_rows_list:
        requirement_id = row["requirement_id"]
        if requirement_id in product_rows:
            raise SystemExit(f"duplicate product row for {requirement_id}")
        product_rows[requirement_id] = row

    mapping_ids = {row["requirement_id"] for row in input_rows}
    unknown_product_ids = sorted(set(product_rows).difference(mapping_ids))
    if unknown_product_ids:
        raise SystemExit(
            "product matrix contains requirement ids absent from mapping: "
            + ", ".join(unknown_product_ids[:10])
        )
    unknown_exactness_ids = sorted(set(exactness_credits).difference(mapping_ids))
    if unknown_exactness_ids:
        raise SystemExit(
            "exactness audit contains credited requirement ids absent from mapping: "
            + ", ".join(unknown_exactness_ids[:10])
        )
    unknown_ucd_generated_ids = sorted(
        set(ucd_generated_credits).difference(mapping_ids)
    )
    if unknown_ucd_generated_ids:
        raise SystemExit(
            "UCD generated cases contain credited requirement ids absent from mapping: "
            + ", ".join(unknown_ucd_generated_ids[:10])
        )
    route_by_requirement = {row["requirement_id"]: row["route_status"] for row in input_rows}
    invalid_exactness_routes = []
    for requirement_id, exactness in exactness_credits.items():
        expected_route = (
            "needs_test262_executable_extractor"
            if exactness["coverage_credit"] == TEST262_LITERAL_LEXER_EXACT_CREDIT
            else "needs_requirement_to_test_case_mapping"
        )
        if route_by_requirement[requirement_id] != expected_route:
            invalid_exactness_routes.append(requirement_id)
    invalid_exactness_routes.sort()
    if invalid_exactness_routes:
        raise SystemExit(
            "exactness audit credits non exact-mapping rows: "
            + ", ".join(invalid_exactness_routes[:10])
        )
    invalid_ucd_generated_routes = []
    for requirement_id in ucd_generated_credits:
        if route_by_requirement[requirement_id] != "needs_ucd_generated_tests":
            invalid_ucd_generated_routes.append(requirement_id)
    invalid_ucd_generated_routes.sort()
    if invalid_ucd_generated_routes:
        raise SystemExit(
            "UCD generated cases credit non-UCD-routed rows: "
            + ", ".join(invalid_ucd_generated_routes[:10])
        )

    rows = []
    product_required_rows = 0
    product_missing_rows = 0
    for row in input_rows:
        product = product_overlay(row, product_rows)
        exactness = exactness_overlay(row, exactness_credits)
        if row["route_status"] == "needs_product_policy_decision":
            product_required_rows += 1
            if not product["surface_decision"]:
                product_missing_rows += 1
        ucd_generated = ucd_generated_credits.get(row["requirement_id"])
        ledger = ledger_for(row, product, exactness, ucd_generated)
        rows.append({**row, **product, **exactness, **ledger})

    state_counts = Counter(row["ledger_state"] for row in rows)
    bucket_counts = Counter(row["ledger_bucket"] for row in rows)
    gate_counts = Counter(row["release_gate"] for row in rows)
    owner_counts = Counter(row["coverage_owner"] for row in rows)
    next_artifact_counts = Counter(row["ledger_next_artifact"] for row in rows)
    route_counts = Counter(row["route_status"] for row in rows)
    product_decision_counts = Counter(
        row["surface_decision"] for row in rows if row["surface_decision"]
    )
    product_public_api_counts = Counter(
        row["public_api_status"] for row in rows if row["public_api_status"]
    )

    direct_rows = sum(1 for row in rows if row["ledger_state"] != "not_direct_requirement")
    covered_rows = bucket_counts.get("covered", 0)
    non_applicable_rows = state_counts.get("non_applicable_with_reason", 0)
    blocking_rows = gate_counts.get("blocking", 0)
    complete = blocking_rows == 0

    test262 = read_summary(test262_summary)
    test_evidence = read_summary(test_evidence_summary)
    exactness_audit = read_summary(exactness_audit_summary)
    selector_gap = read_summary(selector_gap_summary)
    local_exact_plan = read_summary(local_exact_plan_summary)
    ucd_present = Path(args.ucd_dir).is_dir()
    json_schema_harness_present = Path(args.json_schema_harness).is_file()

    summary_lines = [
        "ecma262_snapshot\t2026\n",
        f"input_requirement_mapping\t{requirement_mapping}\n",
        f"input_product_surface_matrix\t{product_surface_matrix}\n",
        f"input_test262_summary\t{test262_summary}\n",
        f"input_test_evidence_summary\t{test_evidence_summary}\n",
        f"input_exactness_audit_summary\t{exactness_audit_summary}\n",
        f"input_exactness_audit\t{exactness_audit_detail}\n",
        f"input_ucd_generated_cases\t{ucd_generated_cases}\n",
        f"input_selector_gap_summary\t{selector_gap_summary}\n",
        f"input_local_exact_plan_summary\t{local_exact_plan_summary}\n",
        f"ledger_rows\t{len(rows)}\n",
        f"direct_requirement_rows\t{direct_rows}\n",
        f"covered_rows\t{covered_rows}\n",
        f"non_applicable_rows\t{non_applicable_rows}\n",
        f"release_blocking_open_rows\t{blocking_rows}\n",
        f"coverage_complete\t{bool_text(complete)}\n",
        f"product_surface_required_rows\t{product_required_rows}\n",
        f"product_surface_matrix_rows\t{len(product_rows)}\n",
        f"product_surface_missing_policy_rows\t{product_missing_rows}\n",
        f"exactness_credit_rows\t{len(exactness_credits)}\n",
        f"ucd_generated_credit_rows\t{len(ucd_generated_credits)}\n",
        f"ucd_16_0_0_source_present\t{bool_text(ucd_present)}\n",
        f"json_schema_harness_present\t{bool_text(json_schema_harness_present)}\n",
        f"test_evidence_summary_present\t{bool_text(bool(test_evidence))}\n",
        f"exactness_audit_summary_present\t{bool_text(bool(exactness_audit))}\n",
        f"selector_gap_summary_present\t{bool_text(bool(selector_gap))}\n",
        f"local_exact_plan_summary_present\t{bool_text(bool(local_exact_plan))}\n",
        f"planned_detail_output\t{detail}\n",
        f"planned_summary_output\t{summary}\n",
        f"dry_run\t{bool_text(args.dry_run)}\n",
        f"fail_on_open\t{bool_text(args.fail_on_open)}\n",
    ]
    for name, count in sorted(state_counts.items()):
        summary_lines.append(f"ledger_state_{name}\t{count}\n")
    for name, count in sorted(bucket_counts.items()):
        summary_lines.append(f"ledger_bucket_{name}\t{count}\n")
    for name, count in sorted(gate_counts.items()):
        summary_lines.append(f"release_gate_{name}\t{count}\n")
    for name, count in sorted(owner_counts.items()):
        summary_lines.append(f"coverage_owner_{name}\t{count}\n")
    for name, count in sorted(next_artifact_counts.items()):
        summary_lines.append(f"next_artifact_{name}\t{count}\n")
    for name, count in sorted(route_counts.items()):
        summary_lines.append(f"route_status_{name}\t{count}\n")
    for name, count in sorted(product_decision_counts.items()):
        summary_lines.append(f"surface_decision_{name}\t{count}\n")
    for name, count in sorted(product_public_api_counts.items()):
        summary_lines.append(f"public_api_status_{name}\t{count}\n")
    for key in [
        "matrix_rows",
        "status_compile_cases_connected",
        "status_needs_negative_syntax_extraction",
        "status_needs_primary_executable_mapping",
        "status_needs_secondary_integration_mapping",
        "status_needs_scope_decision",
    ]:
        if key in test262:
            summary_lines.append(f"test262_{key}\t{test262[key]}\n")
    for key in [
        "evidence_rows",
        "executable_evidence_rows",
        "requirement_linked_rows",
        "unmapped_corpus_rows",
        "coverage_credit_rows",
        "evidence_kind_selected_compile_positive_case",
        "evidence_kind_open_negative_or_local_exact_mapping",
        "evidence_kind_unmapped_negative_syntax_case",
    ]:
        if key in test_evidence:
            summary_lines.append(f"test_evidence_{key}\t{test_evidence[key]}\n")
    for key in [
        "exactness_audit_rows",
        "potential_exact_ready_rows",
        "open_exactness_rows",
        "coverage_credit_rows",
        "coverage_credit_compile_parser_exact_requirement_credit",
        "coverage_credit_exec_result_exact_requirement_credit",
        "coverage_credit_literal_lexer_exact_requirement_credit",
        "coverage_credit_local_exact_compile_parser_requirement_credit",
        "coverage_credit_match_engine_exact_requirement_credit",
        "coverage_credit_reused_candidate_exact_compile_parser_requirement_credit",
        "coverage_credit_spec_model_exact_requirement_credit",
        "coverage_credit_test262_literal_lexer_requirement_credit",
        "exactness_state_covered_by_compile_parser_exact",
        "exactness_state_covered_by_exec_result_exact",
        "exactness_state_covered_by_literal_lexer_exact",
        "exactness_state_covered_by_local_exact_compile_parser",
        "exactness_state_covered_by_match_engine_exact",
        "exactness_state_covered_by_reused_candidate_exact_compile_parser",
        "exactness_state_covered_by_spec_model_exact",
        "exactness_state_covered_by_test262_literal_lexer_exact",
        "local_exact_plan_rows",
        "local_exact_consumed_rows",
        "reused_candidate_exact_plan_rows",
        "reused_candidate_exact_consumed_rows",
        "literal_lexer_exact_plan_rows",
        "literal_lexer_exact_consumed_rows",
        "match_engine_exact_plan_rows",
        "match_engine_exact_consumed_rows",
        "match_engine_atoms_exact_plan_rows",
        "match_engine_atoms_exact_consumed_rows",
        "match_engine_capture_exact_plan_rows",
        "match_engine_capture_exact_consumed_rows",
        "match_engine_unicode_sets_string_exact_plan_rows",
        "match_engine_unicode_sets_string_exact_consumed_rows",
        "match_engine_unicode_sets_escape_string_exact_plan_rows",
        "match_engine_unicode_sets_escape_string_exact_consumed_rows",
        "match_engine_character_classes_exact_plan_rows",
        "match_engine_character_classes_exact_consumed_rows",
        "match_engine_concatenation_exact_plan_rows",
        "match_engine_concatenation_exact_consumed_rows",
        "match_engine_backreference_exact_plan_rows",
        "match_engine_backreference_exact_consumed_rows",
        "match_engine_backreference_matcher_exact_plan_rows",
        "match_engine_backreference_matcher_exact_consumed_rows",
        "match_engine_result_exact_plan_rows",
        "match_engine_result_exact_consumed_rows",
        "match_engine_start_anchor_exact_plan_rows",
        "match_engine_start_anchor_exact_consumed_rows",
        "match_engine_start_anchor_exact_consumed_requirements",
        "match_engine_end_anchor_exact_plan_rows",
        "match_engine_end_anchor_exact_consumed_rows",
        "match_engine_end_anchor_exact_consumed_requirements",
        "match_engine_assertion_exact_plan_rows",
        "match_engine_assertion_exact_consumed_rows",
        "match_engine_quantifier_exact_plan_rows",
        "match_engine_quantifier_exact_consumed_rows",
        "match_engine_modifier_exact_plan_rows",
        "match_engine_modifier_exact_consumed_rows",
        "match_engine_pattern_semantics_exact_plan_rows",
        "match_engine_pattern_semantics_exact_consumed_rows",
        "match_engine_annex_b_exact_plan_rows",
        "match_engine_annex_b_exact_consumed_rows",
        "exec_result_matching_exact_plan_rows",
        "exec_result_matching_exact_consumed_rows",
        "exec_result_capture_exact_plan_rows",
        "exec_result_capture_exact_consumed_rows",
        "exec_result_exec_exact_plan_rows",
        "exec_result_exec_exact_consumed_rows",
        "exec_result_indices_exact_plan_rows",
        "exec_result_indices_exact_consumed_rows",
        "exec_result_instances_exact_plan_rows",
        "exec_result_instances_exact_consumed_rows",
        "spec_model_exact_plan_rows",
        "spec_model_exact_consumed_rows",
        "test262_regexp_executable_case_rows",
        "test262_regexp_executable_consumed_rows",
        "match_state_exact_plan_rows",
        "match_state_exact_consumed_rows",
        "exactness_state_open_missing_selector_coverage",
        "exactness_state_open_local_exact_executable_credit_pending",
        "exactness_state_open_reused_candidate_needs_exact_proof",
        "exactness_state_open_reused_candidate_manual_spec_review_required",
        "exactness_state_open_no_case_negative_or_local_exact",
        "exactness_state_open_unmapped_negative_syntax_case",
        "coverage_credit_none_local_exact_executable_pending_credit",
        "evidence_kind_compile_parser_exact_case",
        "evidence_kind_exec_result_matching_exact_case",
        "evidence_kind_exec_result_capture_exact_case",
        "evidence_kind_exec_result_exec_exact_case",
        "evidence_kind_exec_result_indices_exact_case",
        "evidence_kind_exec_result_instances_exact_case",
        "evidence_kind_spec_model_exact_case",
        "evidence_kind_test262_literal_lexer_exact_case",
        "evidence_kind_literal_lexer_exact_case",
        "evidence_kind_local_exact_compile_parser_case",
        "evidence_kind_match_engine_atoms_exact_case",
        "evidence_kind_match_engine_backreference_exact_case",
        "evidence_kind_match_engine_backreference_matcher_exact_case",
        "evidence_kind_match_engine_capture_exact_case",
        "evidence_kind_match_engine_unicode_sets_string_exact_case",
        "evidence_kind_match_engine_unicode_sets_escape_string_exact_case",
        "evidence_kind_match_engine_character_classes_exact_case",
        "evidence_kind_match_engine_concatenation_exact_case",
        "evidence_kind_match_engine_exact_case",
        "evidence_kind_match_engine_result_exact_case",
        "evidence_kind_match_engine_start_anchor_exact_case",
        "evidence_kind_match_engine_end_anchor_exact_case",
        "evidence_kind_match_engine_assertion_exact_case",
        "evidence_kind_match_engine_quantifier_exact_case",
        "evidence_kind_match_engine_modifier_exact_case",
        "evidence_kind_match_engine_pattern_semantics_exact_case",
        "evidence_kind_match_engine_annex_b_exact_case",
        "evidence_kind_match_state_exact_case",
        "evidence_kind_reused_candidate_exact_compile_parser_case",
        "next_action_connect_local_exact_executable_evidence_to_requirement_credit",
        "next_action_none_covered_by_compile_parser_exact",
        "next_action_none_covered_by_exec_result_exact",
        "next_action_none_covered_by_literal_lexer_exact",
        "next_action_none_covered_by_match_engine_exact",
        "next_action_none_covered_by_reused_candidate_exact_compile_parser",
        "next_action_none_covered_by_spec_model_exact",
        "next_action_none_covered_by_test262_literal_lexer_exact",
        "next_action_manual_spec_exactness_review_before_credit",
    ]:
        if key in exactness_audit:
            summary_lines.append(f"exactness_audit_{key}\t{exactness_audit[key]}\n")
    for key in [
        "selector_gap_rows",
        "selector_complete_case_available_rows",
        "local_exact_test_required_rows",
        "selector_gap_state_local_exact_test_required",
        "next_action_add_local_exact_compile_or_parser_test",
    ]:
        if key in selector_gap:
            summary_lines.append(f"selector_gap_{key}\t{selector_gap[key]}\n")
    for key in [
        "local_exact_plan_rows",
        "source_missing_rows",
        "coverage_credit_rows",
        "local_case_family_compile_literal_validity",
        "local_case_family_compile_surface_exact",
        "local_case_family_parser_capture_local_exact",
        "local_case_family_parser_character_class_local_exact",
        "local_case_family_parser_character_escape_local_exact",
        "local_case_family_parser_modifiers_local_exact",
        "local_case_family_parser_unicode_property_local_exact",
        "local_case_family_parser_unicode_sets_local_exact",
        "executable_layer_compile",
        "executable_layer_parser",
        "planned_flags_<none>",
        "planned_flags_u",
        "planned_flags_v",
        "plan_state_planned_not_executable",
        "coverage_credit_none_local_exact_planned",
    ]:
        if key in local_exact_plan:
            summary_lines.append(
                f"local_exact_plan_{key}\t{local_exact_plan[key]}\n"
            )

    if not args.dry_run:
        cache.mkdir(parents=True, exist_ok=True)
        fieldnames = [
            *input_fieldnames,
            *PRODUCT_FIELDS,
            *EXACTNESS_CREDIT_FIELDS,
            "ledger_state",
            "ledger_bucket",
            "release_gate",
            "coverage_owner",
            "ledger_next_artifact",
            "ledger_reason",
        ]
        with detail.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, delimiter="\t", fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        with summary.open("w", encoding="utf-8") as f:
            f.write("".join(summary_lines))

    print("".join(summary_lines), end="")
    if args.fail_on_open and blocking_rows > 0:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
