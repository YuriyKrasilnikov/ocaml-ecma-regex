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
    select_exact_case_requirement_rows,
    split_csv_set,
    validate_unique_ids,
)


DETAIL_NAME = "ecma262-regexp-compile-parser-exact-plan.tsv"
SUMMARY_NAME = "ecma262-regexp-compile-parser-exact-plan.summary"
TARGET_TEST_ARTIFACT = "test/test_ecma262_compile_parser_exact_plan.ml"


EXACT_CASES = {
    "ecma262-13.2.7.1-0001": {
        "family": "compile_literal_invalid_regular_expression_literal",
        "pattern": "[",
        "flags": "",
        "expected": "compile_error",
        "obligation": "IsValidRegularExpressionLiteral returns false when the RegExp pattern grammar cannot parse the literal body",
    },
    "ecma262-22.2.1-0116": {
        "family": "parser_unicode_sets_class_union_range_then_union",
        "pattern": "[A-ZB]",
        "flags": "v",
        "expected": "compile_ok",
        "obligation": "ClassUnion accepts a ClassSetRange followed by optional ClassUnion in UnicodeSetsMode",
    },
    "ecma262-22.2.1-0122": {
        "family": "parser_unicode_sets_class_set_range",
        "pattern": "[A-Z]",
        "flags": "v",
        "expected": "compile_ok",
        "obligation": "ClassSetRange accepts ClassSetCharacter dash ClassSetCharacter in UnicodeSetsMode",
    },
    "ecma262-22.2.1.1-0001": {
        "family": "early_error_duplicate_named_groups_same_path",
        "pattern": "(?<a>a)(?<a>b)",
        "flags": "",
        "expected": "compile_error",
        "obligation": "Pattern is a Syntax Error when two matching GroupSpecifiers with the same CapturingGroupName may both participate",
    },
    "ecma262-22.2.1.1-0002": {
        "family": "early_error_quantifier_range_min_gt_max",
        "pattern": "a{2,1}",
        "flags": "",
        "expected": "compile_error",
        "obligation": "QuantifierPrefix {m,n} is a Syntax Error when m is greater than n",
    },
    "ecma262-22.2.1.1-0003": {
        "family": "early_error_modifiers_duplicate_add",
        "pattern": "(?ii:a)",
        "flags": "",
        "expected": "compile_error",
        "obligation": "RegularExpressionModifiers add-list is a Syntax Error when it contains the same code point more than once",
    },
    "ecma262-22.2.1.1-0004": {
        "family": "early_error_modifiers_add_remove_overlap",
        "pattern": "(?i-i:a)",
        "flags": "",
        "expected": "compile_error",
        "obligation": "RegularExpressionModifiers add/remove form is a Syntax Error when a modifier appears in both lists",
    },
    "ecma262-22.2.1.1-0005": {
        "family": "early_error_named_backreference_missing_group",
        "pattern": "\\k<missing>",
        "flags": "",
        "expected": "compile_error",
        "obligation": "AtomEscape named backreference is a Syntax Error when GroupSpecifiersThatMatch is empty",
    },
    "ecma262-22.2.1.1-0006": {
        "family": "early_error_decimal_escape_capture_index_too_large",
        "pattern": "\\2",
        "flags": "u",
        "expected": "compile_error",
        "obligation": "AtomEscape DecimalEscape is a Syntax Error when its capturing group number is greater than the containing Pattern capture count",
    },
    "ecma262-22.2.1.1-0007": {
        "family": "early_error_class_range_left_is_character_class",
        "pattern": "[\\d-a]",
        "flags": "u",
        "expected": "compile_error",
        "obligation": "NonemptyClassRanges is a Syntax Error when the first range endpoint is a character class",
    },
    "ecma262-22.2.1.1-0008": {
        "family": "early_error_class_range_right_is_character_class",
        "pattern": "[a-\\d]",
        "flags": "u",
        "expected": "compile_error",
        "obligation": "NonemptyClassRangesNoDash is a Syntax Error when the second range endpoint is a character class",
    },
    "ecma262-22.2.1.1-0009": {
        "family": "early_error_identifier_start_escape_not_identifier_start",
        "pattern": "(?<\\u0030>a)",
        "flags": "u",
        "expected": "compile_error",
        "obligation": "RegExpIdentifierStart escaped code point is a Syntax Error when it is not IdentifierStartChar",
    },
    "ecma262-22.2.1.1-0010": {
        "family": "early_error_identifier_start_surrogate_pair_not_id_start",
        "pattern": "(?<\\uD83D\\uDCA9>a)",
        "flags": "u",
        "expected": "compile_error",
        "obligation": "RegExpIdentifierStart surrogate pair is a Syntax Error when the code point is not UnicodeIDStart",
    },
    "ecma262-22.2.1.1-0011": {
        "family": "early_error_identifier_part_escape_not_identifier_part",
        "pattern": "(?<a\\u002D>a)",
        "flags": "u",
        "expected": "compile_error",
        "obligation": "RegExpIdentifierPart escaped code point is a Syntax Error when it is not IdentifierPartChar",
    },
    "ecma262-22.2.1.1-0012": {
        "family": "early_error_identifier_part_surrogate_pair_not_id_continue",
        "pattern": "(?<a\\uD83D\\uDCA9>a)",
        "flags": "u",
        "expected": "compile_error",
        "obligation": "RegExpIdentifierPart surrogate pair is a Syntax Error when the code point is not UnicodeIDContinue",
    },
    "ecma262-22.2.1.1-0013": {
        "family": "early_error_unicode_property_value_unknown",
        "pattern": "\\p{Script=NoSuch}",
        "flags": "u",
        "expected": "compile_error",
        "obligation": "UnicodePropertyValueExpression name=value is a Syntax Error when the value is not listed for the property",
    },
    "ecma262-22.2.1.1-0014": {
        "family": "early_error_lone_unicode_property_unknown",
        "pattern": "\\p{NoSuch}",
        "flags": "u",
        "expected": "compile_error",
        "obligation": "LoneUnicodePropertyNameOrValue is a Syntax Error when it is neither a General_Category value nor a binary property",
    },
    "ecma262-22.2.1.1-0015": {
        "family": "early_error_complement_property_may_contain_strings",
        "pattern": "\\P{RGI_Emoji}",
        "flags": "v",
        "expected": "compile_error",
        "obligation": "CharacterClassEscape P{...} is a Syntax Error when the property expression may contain strings",
    },
    "ecma262-22.2.1.1-0016": {
        "family": "early_error_negated_class_may_contain_strings",
        "pattern": "[^\\p{RGI_Emoji}]",
        "flags": "v",
        "expected": "compile_error",
        "obligation": "CharacterClass [^ ClassContents ] is a Syntax Error when ClassContents may contain strings",
    },
    "ecma262-22.2.1.1-0017": {
        "family": "early_error_nested_negated_class_may_contain_strings",
        "pattern": "[[^^\\p{RGI_Emoji}]]",
        "flags": "v",
        "expected": "compile_error",
        "obligation": "NestedClass [^ ClassContents ] is a Syntax Error when ClassContents may contain strings",
    },
    "ecma262-22.2.1.1-0018": {
        "family": "early_error_class_set_range_descending",
        "pattern": "[z-a]",
        "flags": "v",
        "expected": "compile_error",
        "obligation": "ClassSetRange is a Syntax Error when the first ClassSetCharacter value is greater than the second",
    },
}


def selectors_for(row: dict[str, str]) -> set[str]:
    semantic = row["semantic_family"]
    text = f"{row['requirement_text']} {row['requirement_local_id']}".lower()
    routes = split_csv_set(row["coverage_routes"])
    selectors: set[str] = set()

    if "test262_positive_compile" in routes:
        selectors.add("accepted_literal")
    if "test262_flags" in routes or semantic == "flags" or "flag" in text:
        selectors.add("flagged")
    if semantic in {"captures", "creation"} or "capture" in text:
        selectors.update({"capturing_group", "named_capture"})
    if "groupname" in text or "group specifier" in text:
        selectors.add("named_capture")
    if semantic == "unicode_sets" or "unicode sets" in text:
        selectors.update({"unicode_sets", "unicode_sets_mode", "unicode_property"})
    if semantic in {"escapes", "escapes_grammar"} or "escape" in text:
        selectors.update({"escape", "unicode_escape", "hex_escape", "control_escape"})
    if "unicode" in semantic or "unicode" in text:
        selectors.update({"unicode_mode", "unicode_escape", "unicode_property"})
    if "class" in semantic or "class" in text:
        selectors.add("character_class")
    if "range" in text:
        selectors.add("class_range")
    if "backreference" in text:
        selectors.update({"backreference", "named_backreference"})
    if "alternative" in text or "disjunction" in text or semantic == "pattern_grammar":
        selectors.add("alternation")
    if "quantifier" in text:
        selectors.add("quantifier")
    if "assertion" in text:
        selectors.add("assertion")
    if "atom" in text:
        selectors.update({"dot", "character_class", "capturing_group", "escape"})
    if semantic == "modifiers" or "modifier" in text:
        selectors.add("modifiers")
    if semantic == "syntax_early_errors":
        selectors.add("negative_syntax_needed")
    if semantic == "regexp_literal_expression":
        selectors.add("accepted_literal")

    return selectors


def classify_for_plan(row: dict[str, str]) -> tuple[str, str]:
    product_surface = row["product_surface"]
    semantic = row["semantic_family"]
    kind = row["requirement_kind"]

    if product_surface == "compile":
        if semantic in {"syntax_early_errors", "regexp_literal_expression"}:
            return "compile_literal_validity", "compile"
        return "compile_surface_exact", "compile"

    if product_surface == "parser":
        if kind == "grammar_rhs":
            return "parser_grammar_production", "parser"
        if semantic == "syntax_early_errors":
            return "parser_early_error", "parser"
        if semantic in {"captures", "character_classes", "escapes", "unicode_sets"}:
            return f"parser_{semantic}_semantic_operation", "parser"
        return "parser_semantic_operation", "parser"

    raise SystemExit(
        f"requirement {row['requirement_id']} has unsupported product_surface "
        f"{product_surface!r} for compile/parser exact plan"
    )


def plan_row(row: dict[str, str]) -> dict[str, str]:
    requirement_id = row["requirement_id"]
    case = EXACT_CASES.get(requirement_id)
    if case is None:
        raise SystemExit(f"missing exact case definition for {requirement_id}")

    exact_case_id = (
        f"compile-parser-exact:{requirement_id}:{safe_id(case['family'])}"
    )
    mapping_family, executable_layer = classify_for_plan(row)
    selection_state = (
        "selected_compile_positive_case"
        if case["expected"] == "compile_ok"
        else "needs_negative_or_local_exact_case"
    )
    return {
        "plan_id": f"compile-parser-exact-plan:{requirement_id}",
        **copy_requirement_metadata(row, include_local_id=False),
        "mapping_family": mapping_family,
        "executable_layer": executable_layer,
        "selection_state": selection_state,
        "selector_tags": ",".join(sorted(selectors_for(row))),
        "selected_case_id": "",
        "selected_case_source": "",
        "selected_pattern": "",
        "selected_flags": "",
        "exact_case_family": case["family"],
        "exact_case_id": exact_case_id,
        "planned_pattern": case["pattern"],
        "planned_flags": case["flags"],
        "expected_behavior": case["expected"],
        "coverage_credit": "none_compile_parser_exact_planned",
        "plan_state": "planned_not_executable",
        "target_test_artifact": TARGET_TEST_ARTIFACT,
        "exact_case_obligation": case["obligation"],
        "next_action": "materialize_compile_parser_exact_case",
        "plan_reason": (
            "post-credit compile/parser exact case is planned from the "
            "ECMA-262 requirement row; no ledger credit is assigned until the "
            "executable gate and exactness audit consume it"
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache", default="cache")
    parser.add_argument(
        "--requirements",
        default="cache/ecma262-regexp-requirement-mapping.tsv",
    )
    parser.add_argument("--selection", default="", help=argparse.SUPPRESS)
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
            "semantic_family",
            "coverage_routes",
            "product_surface",
        },
    )
    source_rows = select_exact_case_requirement_rows(requirement_rows, EXACT_CASES)

    rows = [plan_row(row) for row in source_rows]
    validate_unique_ids(rows)

    state_counts = Counter(row["plan_state"] for row in rows)
    credit_counts = Counter(row["coverage_credit"] for row in rows)
    expected_counts = Counter(row["expected_behavior"] for row in rows)
    layer_counts = Counter(row["executable_layer"] for row in rows)
    selection_counts = Counter(row["selection_state"] for row in rows)
    family_counts = Counter(row["exact_case_family"] for row in rows)
    flag_counts = Counter(
        row["planned_flags"] if row["planned_flags"] else "<none>" for row in rows
    )
    target_counts = Counter(row["target_test_artifact"] for row in rows)
    executable_rows = state_counts.get("planned_not_executable", 0)
    coverage_credit_rows = sum(
        count for credit, count in credit_counts.items() if not credit.startswith("none")
    )

    summary_lines = [
        "ecma262_snapshot\t2026\n",
        f"input_requirements\t{requirements}\n",
        f"input_requirement_rows\t{len(requirement_rows)}\n",
        f"source_requirement_rows\t{len(source_rows)}\n",
        f"compile_parser_exact_plan_rows\t{len(rows)}\n",
        f"planned_executable_rows\t{executable_rows}\n",
        f"coverage_credit_rows\t{coverage_credit_rows}\n",
        f"planned_detail_output\t{detail}\n",
        f"planned_summary_output\t{summary}\n",
        f"dry_run\t{bool_text(args.dry_run)}\n",
    ]
    for name, count in sorted(state_counts.items()):
        summary_lines.append(f"plan_state_{name}\t{count}\n")
    for name, count in sorted(credit_counts.items()):
        summary_lines.append(f"coverage_credit_{name}\t{count}\n")
    for name, count in sorted(expected_counts.items()):
        summary_lines.append(f"expected_behavior_{name}\t{count}\n")
    for name, count in sorted(layer_counts.items()):
        summary_lines.append(f"executable_layer_{name}\t{count}\n")
    for name, count in sorted(selection_counts.items()):
        summary_lines.append(f"selection_state_{name}\t{count}\n")
    for name, count in sorted(family_counts.items()):
        summary_lines.append(f"exact_case_family_{name}\t{count}\n")
    for name, count in sorted(flag_counts.items()):
        summary_lines.append(f"planned_flags_{name}\t{count}\n")
    for name, count in sorted(target_counts.items()):
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
        "requirement_text",
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
