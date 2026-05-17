#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path

from ecma262_tooling import read_tsv_rows


DETAIL_NAME = "ecma262-regexp-requirement-mapping.tsv"
SUMMARY_NAME = "ecma262-regexp-requirement-mapping.summary"


AREA_ROUTES = {
    "regexp_literal_lexical_grammar": "test262_literal_lexer",
    "regexp_pattern_syntax_positive": "test262_positive_compile",
    "regexp_syntax_negative": "test262_negative_syntax",
    "regexp_flags": "test262_flags",
    "regexp_exec_and_captures": "test262_runtime_exec",
    "regexp_unicode_semantics": "test262_unicode_runtime",
    "js_regexp_api_integration": "test262_js_runtime_integration",
    "regexp_string_iterator": "test262_regexp_string_iterator",
    "string_symbol_integration": "test262_string_symbol_integration",
}

LAYER_SURFACES = {
    "compile_surface": "compile",
    "exec": "exec_result",
    "js_api_integration": "js_runtime_api_or_adapter_policy",
    "lexer": "literal_lexer",
    "matcher": "match_engine",
    "parser": "parser",
    "spec_model": "spec_model",
    "unicode": "unicode_tables",
}

NEXT_ARTIFACTS = {
    "container_marker": "ecma262_requirement_review",
    "needs_product_policy_decision": "product_surface_policy_decision",
    "needs_ucd_generated_tests": "tools/build_ucd_regexp_tests.py",
    "needs_test262_executable_extractor": "tools/extract_test262_regexp_executable_cases.py",
    "needs_requirement_to_test_case_mapping": "tools/map_ecma262_requirements_to_tests.py",
    "needs_local_exact_tests": "test/test_ecma262_local_exact.ml",
}


def semantic_family(row: dict[str, str]) -> str:
    clause_id = row["clause_id"]
    cluster = row["spec_cluster"]
    title = row["clause_title"].lower()
    text = row["requirement_text"].lower()

    if row["requirement_kind"] == "section_marker":
        return "container_clause"
    if clause_id.startswith("B."):
        return f"annex_b_{cluster}"
    if "early errors" in title:
        return "syntax_early_errors"
    if "parsepattern" in title.replace(" ", ""):
        return "parse_pattern"
    if "unicode" in cluster or "unicode" in text:
        return cluster
    if "capture" in cluster or "capturing" in text:
        return cluster
    if "flag" in cluster or "flag" in title:
        return "flags"
    if row["requirement_kind"] == "grammar_rhs" and row["implementation_layer"] in {
        "parser",
        "lexer",
    }:
        return f"{cluster}_grammar"
    return cluster


def product_surface(row: dict[str, str]) -> str:
    return LAYER_SURFACES.get(row["implementation_layer"], row["implementation_layer"])


def routes_for(row: dict[str, str]) -> list[str]:
    if row["requirement_kind"] == "section_marker":
        return ["manual_clause_review"]

    routes = ["local_exact"]
    areas = [part for part in row["coverage_areas"].split("|") if part]
    for area in areas:
        route = AREA_ROUTES.get(area)
        if route is not None:
            routes.append(route)

    required_sources = {part for part in row["required_sources"].split(",") if part}
    if "ucd" in required_sources:
        routes.append("ucd_generated")

    if row["implementation_layer"] in {"matcher", "unicode"} and (
        "regexp_pattern_syntax_positive" in areas
        or "regexp_unicode_semantics" in areas
        or "regexp_exec_and_captures" in areas
    ):
        routes.append("json_schema_consumer")

    if row["implementation_layer"] == "js_api_integration":
        routes.append("product_policy_decision")

    return sorted(set(routes))


def route_status(row: dict[str, str], routes: list[str]) -> str:
    if row["requirement_kind"] == "section_marker":
        return "container_marker"
    if "product_policy_decision" in routes:
        return "needs_product_policy_decision"
    if "ucd_generated" in routes:
        return "needs_ucd_generated_tests"
    if row["test262_status"] == "inventory_only":
        return "needs_test262_executable_extractor"
    if row["test262_status"].startswith("partial_executable"):
        return "needs_requirement_to_test_case_mapping"
    return "needs_local_exact_tests"


def coverage_state(status: str) -> str:
    if status == "container_marker":
        return "not_a_direct_requirement"
    return "not_covered"


def reason_for(row: dict[str, str], routes: list[str], status: str) -> str:
    if status == "container_marker":
        return "group clause has no direct extracted requirement blocks"
    if status == "needs_product_policy_decision":
        return "ECMA-262 JavaScript API integration requires explicit product-surface policy before executable OCaml tests are meaningful"
    if status == "needs_ucd_generated_tests":
        return "Unicode-sensitive requirement needs generated UCD 16.0.0 evidence in addition to corpus tests"
    if status == "needs_test262_executable_extractor":
        return "test262 signal is inventory-level only; executable extractor does not exist for this requirement family yet"
    if status == "needs_requirement_to_test_case_mapping":
        return "coarse test262 signal exists, but this exact requirement row is not mapped to concrete test cases yet"
    if "json_schema_consumer" in routes:
        return "requirement also needs downstream JSON Schema consumer evidence"
    return "requirement needs local exact tests because corpus evidence alone is not enough"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache", default="cache")
    parser.add_argument(
        "--requirement-matrix",
        default="cache/ecma262-regexp-requirement-matrix.tsv",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    cache = Path(args.cache)
    requirement_matrix = Path(args.requirement_matrix)
    detail = cache / DETAIL_NAME
    summary = cache / SUMMARY_NAME

    if not requirement_matrix.is_file():
        raise SystemExit(
            f"missing ECMA-262 requirement matrix at {requirement_matrix}; "
            "run tools/build_ecma262_regexp_requirement_matrix.py first"
        )

    rows = []
    for row in read_tsv_rows(requirement_matrix):
        routes = routes_for(row)
        status = route_status(row, routes)
        rows.append(
            {
                **row,
                "semantic_family": semantic_family(row),
                "product_surface": product_surface(row),
                "coverage_routes": ",".join(routes),
                "route_status": status,
                "coverage_state": coverage_state(status),
                "primary_next_artifact": NEXT_ARTIFACTS[status],
                "mapping_reason": reason_for(row, routes, status),
            }
        )

    status_counts = Counter(row["route_status"] for row in rows)
    state_counts = Counter(row["coverage_state"] for row in rows)
    surface_counts = Counter(row["product_surface"] for row in rows)
    semantic_counts = Counter(row["semantic_family"] for row in rows)
    next_artifact_counts = Counter(row["primary_next_artifact"] for row in rows)
    route_counts: Counter[str] = Counter()
    for row in rows:
        route_counts.update(row["coverage_routes"].split(","))

    summary_lines = [
        "ecma262_snapshot\t2026\n",
        f"input_requirement_matrix\t{requirement_matrix}\n",
        f"requirement_rows\t{len(rows)}\n",
        f"planned_detail_output\t{detail}\n",
        f"planned_summary_output\t{summary}\n",
        f"dry_run\t{str(args.dry_run).lower()}\n",
    ]
    for name, count in sorted(state_counts.items()):
        summary_lines.append(f"coverage_state_{name}\t{count}\n")
    for name, count in sorted(status_counts.items()):
        summary_lines.append(f"route_status_{name}\t{count}\n")
    for name, count in sorted(surface_counts.items()):
        summary_lines.append(f"product_surface_{name}\t{count}\n")
    for name, count in sorted(route_counts.items()):
        summary_lines.append(f"coverage_route_{name}\t{count}\n")
    for name, count in sorted(next_artifact_counts.items()):
        summary_lines.append(f"next_artifact_{name}\t{count}\n")
    for name, count in sorted(semantic_counts.items()):
        summary_lines.append(f"semantic_family_{name}\t{count}\n")

    if args.dry_run:
        print("".join(summary_lines), end="")
        return

    cache.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "requirement_id",
        "clause_id",
        "clause_title",
        "source_url",
        "source_file",
        "source_sha256",
        "section_anchor",
        "requirement_kind",
        "requirement_local_id",
        "requirement_text",
        "spec_cluster",
        "implementation_layer",
        "coverage_areas",
        "required_sources",
        "test262_status",
        "clause_coverage_status",
        "requirement_test_status",
        "missing_sources",
        "semantic_family",
        "product_surface",
        "coverage_routes",
        "route_status",
        "coverage_state",
        "primary_next_artifact",
        "mapping_reason",
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
