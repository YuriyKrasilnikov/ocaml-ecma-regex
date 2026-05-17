#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path

from ecma262_tooling import bool_text, read_summary, read_tsv


DETAIL_NAME = "ecma262-regexp-requirement-test-worklist.tsv"
SUMMARY_NAME = "ecma262-regexp-requirement-test-worklist.summary"


def has_route(row: dict[str, str], route: str) -> bool:
    return route in {part for part in row["coverage_routes"].split(",") if part}


def classify(row: dict[str, str]) -> dict[str, str]:
    product_surface = row["product_surface"]
    semantic = row["semantic_family"]
    kind = row["requirement_kind"]

    if product_surface == "spec_model":
        return {
            "mapping_family": "spec_model_local_exact",
            "executable_layer": "spec_model",
            "test_obligation": "local exact test for grammar/source-model policy",
            "primary_test_artifact": "test/test_ecma262_spec_model.ml",
            "selector_source": "local_exact",
            "candidate_evidence": "none",
        }

    if product_surface == "literal_lexer":
        return {
            "mapping_family": "literal_lexer_exact",
            "executable_layer": "literal_lexer",
            "test_obligation": "literal lexer and flag text extraction tests",
            "primary_test_artifact": "test/test_ecma262_literal_lexer.ml",
            "selector_source": "test262_literal_lexer,local_exact",
            "candidate_evidence": "test262 inventory plus local literal lexer cases",
        }

    if product_surface == "compile":
        if semantic in {"syntax_early_errors", "regexp_literal_expression"}:
            mapping_family = "compile_literal_validity"
            primary = "test/test_ecma262_compile_validity.ml"
            obligation = "accepted and rejected RegExp literal validity tests"
        else:
            mapping_family = "compile_surface_exact"
            primary = "test/test_ecma262_compile_surface.ml"
            obligation = "compile surface tests for syntax and flag interactions"
        return {
            "mapping_family": mapping_family,
            "executable_layer": "compile",
            "test_obligation": obligation,
            "primary_test_artifact": primary,
            "selector_source": "test262_positive_compile,test262_negative_syntax,local_exact",
            "candidate_evidence": "cache/test262-regexp-core-compile-cases.tsv",
        }

    if product_surface == "parser":
        if kind == "grammar_rhs":
            mapping_family = "parser_grammar_production"
            obligation = "positive and negative compile tests for this grammar production"
            primary = "test/test_ecma262_parser_grammar.ml"
        elif semantic == "syntax_early_errors":
            mapping_family = "parser_early_error"
            obligation = "negative compile tests for parser early-error rule"
            primary = "test/test_ecma262_parser_negative.ml"
        elif semantic in {"captures", "character_classes", "escapes", "unicode_sets"}:
            mapping_family = f"parser_{semantic}_semantic_operation"
            obligation = "parser semantic-operation tests plus compile acceptance/rejection cases"
            primary = "test/test_ecma262_parser_semantic_ops.ml"
        else:
            mapping_family = "parser_semantic_operation"
            obligation = "parser semantic-operation tests tied to concrete patterns"
            primary = "test/test_ecma262_parser_semantic_ops.ml"
        return {
            "mapping_family": mapping_family,
            "executable_layer": "parser",
            "test_obligation": obligation,
            "primary_test_artifact": primary,
            "selector_source": "test262_positive_compile,test262_negative_syntax,local_exact",
            "candidate_evidence": "cache/test262-regexp-core-compile-cases.tsv",
        }

    if product_surface == "match_engine":
        if has_route(row, "json_schema_consumer"):
            selector = "test262_runtime_exec,json_schema_consumer,local_exact"
            evidence = "test262 runtime inventory plus JSON Schema consumer corpus"
        else:
            selector = "test262_runtime_exec,local_exact"
            evidence = "test262 runtime inventory"
        return {
            "mapping_family": f"match_engine_{semantic}",
            "executable_layer": "match_engine",
            "test_obligation": "runtime search/match tests for the semantic operation",
            "primary_test_artifact": "test/test_ecma262_match_engine.ml",
            "selector_source": selector,
            "candidate_evidence": evidence,
        }

    if product_surface == "exec_result":
        return {
            "mapping_family": f"exec_result_{semantic}",
            "executable_layer": "exec_result",
            "test_obligation": "exec result shape, capture, index, and state tests",
            "primary_test_artifact": "test/test_ecma262_exec_result.ml",
            "selector_source": "test262_runtime_exec,local_exact",
            "candidate_evidence": "test262 runtime inventory",
        }

    return {
        "mapping_family": "unknown_mapping_family",
        "executable_layer": product_surface,
        "test_obligation": "manual classification required",
        "primary_test_artifact": "requirement_mapping_policy_review",
        "selector_source": "manual",
        "candidate_evidence": "none",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache", default="cache")
    parser.add_argument(
        "--ledger",
        default="cache/ecma262-regexp-coverage-ledger.tsv",
    )
    parser.add_argument(
        "--compile-cases",
        default="cache/test262-regexp-core-compile-cases.tsv",
    )
    parser.add_argument(
        "--compile-cases-summary",
        default="cache/test262-regexp-core-compile-cases.summary",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    cache = Path(args.cache)
    ledger_path = Path(args.ledger)
    compile_cases_path = Path(args.compile_cases)
    detail = cache / DETAIL_NAME
    summary = cache / SUMMARY_NAME

    if not ledger_path.is_file():
        raise SystemExit(
            f"missing ECMA-262 coverage ledger at {ledger_path}; "
            "run tools/build_ecma262_regexp_coverage_ledger.py first"
        )

    input_fieldnames, ledger_rows = read_tsv(ledger_path)
    required_columns = {
        "requirement_id",
        "ledger_state",
        "product_surface",
        "semantic_family",
        "coverage_routes",
        "requirement_kind",
    }
    missing_columns = required_columns.difference(input_fieldnames)
    if missing_columns:
        raise SystemExit(
            f"missing required ledger columns: {', '.join(sorted(missing_columns))}"
        )

    open_rows = [
        row for row in ledger_rows
        if row["ledger_state"] == "open_requirement_to_test_mapping_missing"
    ]

    compile_case_count = 0
    if compile_cases_path.is_file():
        _, compile_cases = read_tsv(compile_cases_path)
        compile_case_count = len(compile_cases)

    compile_summary = read_summary(Path(args.compile_cases_summary))

    rows = []
    for row in open_rows:
        classified = classify(row)
        mapping_state = "open_exact_case_selection"
        if classified["mapping_family"] == "unknown_mapping_family":
            mapping_state = "open_manual_classification"
        rows.append(
            {
                **row,
                **classified,
                "mapping_state": mapping_state,
                "exact_test_case_id": "",
                "exact_test_source": "",
                "expected_behavior": "",
                "test_mapping_reason": "requirement is classified into a concrete test obligation, but no exact executable test case is selected yet",
            }
        )

    mapping_state_counts = Counter(row["mapping_state"] for row in rows)
    family_counts = Counter(row["mapping_family"] for row in rows)
    layer_counts = Counter(row["executable_layer"] for row in rows)
    artifact_counts = Counter(row["primary_test_artifact"] for row in rows)
    product_surface_counts = Counter(row["product_surface"] for row in rows)
    semantic_counts = Counter(row["semantic_family"] for row in rows)
    selector_counts = Counter(row["selector_source"] for row in rows)
    unknown_rows = family_counts.get("unknown_mapping_family", 0)
    exact_mapped_rows = sum(1 for row in rows if row["exact_test_case_id"])

    summary_lines = [
        "ecma262_snapshot\t2026\n",
        f"input_ledger\t{ledger_path}\n",
        f"input_ledger_rows\t{len(ledger_rows)}\n",
        f"input_open_requirement_to_test_mapping_rows\t{len(open_rows)}\n",
        f"worklist_rows\t{len(rows)}\n",
        f"exact_mapped_rows\t{exact_mapped_rows}\n",
        f"open_mapping_rows\t{len(rows) - exact_mapped_rows}\n",
        f"unknown_mapping_family_rows\t{unknown_rows}\n",
        f"compile_cases_present\t{bool_text(compile_cases_path.is_file())}\n",
        f"compile_case_rows\t{compile_case_count}\n",
        f"planned_detail_output\t{detail}\n",
        f"planned_summary_output\t{summary}\n",
        f"dry_run\t{bool_text(args.dry_run)}\n",
    ]
    for key in [
        "literal_compile_cases",
        "literal_compile_cases_without_flags",
        "literal_compile_cases_with_flags",
    ]:
        if key in compile_summary:
            summary_lines.append(f"compile_summary_{key}\t{compile_summary[key]}\n")
    for name, count in sorted(mapping_state_counts.items()):
        summary_lines.append(f"mapping_state_{name}\t{count}\n")
    for name, count in sorted(layer_counts.items()):
        summary_lines.append(f"executable_layer_{name}\t{count}\n")
    for name, count in sorted(family_counts.items()):
        summary_lines.append(f"mapping_family_{name}\t{count}\n")
    for name, count in sorted(artifact_counts.items()):
        summary_lines.append(f"primary_test_artifact_{name}\t{count}\n")
    for name, count in sorted(selector_counts.items()):
        summary_lines.append(f"selector_source_{name}\t{count}\n")
    for name, count in sorted(product_surface_counts.items()):
        summary_lines.append(f"product_surface_{name}\t{count}\n")
    for name, count in sorted(semantic_counts.items()):
        summary_lines.append(f"semantic_family_{name}\t{count}\n")

    if args.dry_run:
        print("".join(summary_lines), end="")
        return

    cache.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        *input_fieldnames,
        "mapping_state",
        "mapping_family",
        "executable_layer",
        "test_obligation",
        "primary_test_artifact",
        "selector_source",
        "candidate_evidence",
        "exact_test_case_id",
        "exact_test_source",
        "expected_behavior",
        "test_mapping_reason",
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
