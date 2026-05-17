#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path

from ecma262_tooling import bool_text, read_tsv, require_columns, split_csv


DETAIL_NAME = "ecma262-regexp-reused-candidate-worklist.tsv"
SUMMARY_NAME = "ecma262-regexp-reused-candidate-worklist.summary"


def csv_signature(value: str) -> str:
    return ",".join(sorted(split_csv(value)))


def compact_text(value: str, limit: int = 180) -> str:
    compact = " ".join(value.split())
    if len(compact) > limit:
        return compact[: limit - 3] + "..."
    return compact


def test262_source_exists(case_source: str) -> bool:
    if not case_source:
        return False
    source_path = case_source.split(":", 1)[0]
    return Path("external/test262", source_path).is_file()


def ecma262_source_exists(case_source: str) -> bool:
    if not case_source:
        return False
    source_path = case_source.split("#", 1)[0]
    return Path(source_path).is_file()


def row_by_requirement(
    rows: list[dict[str, str]],
    source_name: str,
) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    for row in rows:
        requirement_id = row["requirement_id"]
        if requirement_id in result:
            raise SystemExit(f"duplicate requirement_id in {source_name}: {requirement_id}")
        result[requirement_id] = row
    return result


def classify_cluster(size: int, mapping_count: int, selector_count: int, clause_count: int) -> str:
    if size >= 40 or mapping_count >= 3 or selector_count >= 6 or clause_count >= 6:
        return "high_reuse_spread"
    if size >= 10 or mapping_count >= 2 or selector_count >= 2 or clause_count >= 2:
        return "medium_reuse_spread"
    return "low_reuse_spread"


def proof_decision(mapping_count: int, selector_count: int, clause_count: int) -> str:
    if mapping_count == 1 and selector_count == 1 and clause_count == 1:
        return "manual_spec_review_required"
    return "needs_local_exact_case"


def validate_exactness_row(row: dict[str, str]) -> None:
    requirement_id = row["requirement_id"]
    expected = {
        "audit_scope": "ecma262_requirement",
        "evidence_kind": "selected_compile_positive_case",
        "expected_behavior": "compile_ok",
        "selected_missing_selector_tags": "",
        "exactness_audit_state": "open_reused_candidate_needs_exact_proof",
        "coverage_credit": "none_reused_candidate",
        "next_action": "split_reused_candidate_or_add_local_exact_test",
    }
    for field, expected_value in expected.items():
        if row[field] != expected_value:
            raise SystemExit(
                f"reused exactness row {requirement_id} has {field}={row[field]!r}; "
                f"expected {expected_value!r}"
            )
    if not requirement_id:
        raise SystemExit("reused exactness row has empty requirement_id")
    if not row["case_id"]:
        raise SystemExit(f"reused exactness row {requirement_id} has empty case_id")
    if int(row["case_reuse_count"]) <= 1:
        raise SystemExit(
            f"reused exactness row {requirement_id} has case_reuse_count="
            f"{row['case_reuse_count']}"
        )
    if not test262_source_exists(row["case_source"]):
        raise SystemExit(
            f"reused exactness row {requirement_id} missing test262 source: "
            f"{row['case_source']}"
        )


def validate_selection_row(
    exactness: dict[str, str],
    selection: dict[str, str],
) -> None:
    requirement_id = exactness["requirement_id"]
    expected = {
        "selection_state": "selected_compile_positive_case",
        "selected_expected_behavior": "compile_ok",
        "selected_missing_selector_tags": "",
        "selection_exactness": "selected_candidate_not_coverage",
    }
    for field, expected_value in expected.items():
        if selection[field] != expected_value:
            raise SystemExit(
                f"selection row {requirement_id} has {field}={selection[field]!r}; "
                f"expected {expected_value!r}"
            )
    if selection["selected_case_id"] != exactness["case_id"]:
        raise SystemExit(
            f"selection row {requirement_id} case mismatch: "
            f"{selection['selected_case_id']} != {exactness['case_id']}"
        )
    if selection["selected_case_source"] != exactness["case_source"]:
        raise SystemExit(
            f"selection row {requirement_id} source mismatch: "
            f"{selection['selected_case_source']} != {exactness['case_source']}"
        )
    if not selection["selected_pattern"]:
        raise SystemExit(f"selection row {requirement_id} has empty selected_pattern")


def build_row(
    exactness: dict[str, str],
    selection: dict[str, str],
    requirement: dict[str, str],
    cluster: list[dict[str, str]],
) -> dict[str, str]:
    case_id = exactness["case_id"]
    cluster_size = len(cluster)
    mapping_count = len({row["mapping_family"] for row in cluster})
    layer_count = len({row["executable_layer"] for row in cluster})
    selector_count = len({csv_signature(row["selector_tags"]) for row in cluster})
    clause_count = len({row["clause_id"] for row in cluster})
    semantic_count = len({row["semantic_family"] for row in cluster})
    pressure = classify_cluster(cluster_size, mapping_count, selector_count, clause_count)
    decision = proof_decision(mapping_count, selector_count, clause_count)

    case_sources = sorted({row["case_source"] for row in cluster})
    selected_sources = sorted({row["selected_case_source"] for row in cluster})
    if case_sources != selected_sources:
        raise SystemExit(f"cluster {case_id} has mismatched exactness/selection sources")

    return {
        "worklist_id": f"reused-candidate:{exactness['requirement_id']}:{case_id}",
        "requirement_id": exactness["requirement_id"],
        "clause_id": requirement["clause_id"],
        "clause_title": requirement["clause_title"],
        "source_file": requirement["source_file"],
        "section_anchor": requirement["section_anchor"],
        "requirement_kind": requirement["requirement_kind"],
        "requirement_text": compact_text(requirement["requirement_text"]),
        "semantic_family": selection["semantic_family"],
        "mapping_family": exactness["mapping_family"],
        "executable_layer": exactness["executable_layer"],
        "selector_tags": csv_signature(exactness["selector_tags"]),
        "selected_feature_tags": csv_signature(exactness["selected_feature_tags"]),
        "selected_case_id": case_id,
        "selected_case_source": exactness["case_source"],
        "selected_pattern": selection["selected_pattern"],
        "selected_flags": selection["selected_flags"],
        "case_reuse_count": exactness["case_reuse_count"],
        "cluster_size": str(cluster_size),
        "cluster_mapping_family_count": str(mapping_count),
        "cluster_executable_layer_count": str(layer_count),
        "cluster_selector_signature_count": str(selector_count),
        "cluster_clause_count": str(clause_count),
        "cluster_semantic_family_count": str(semantic_count),
        "cluster_pressure": pressure,
        "reuse_worklist_state": "reused_candidate_needs_exact_proof",
        "proof_decision": decision,
        "coverage_credit": "none_reused_candidate_worklist",
        "next_action": "split_reused_candidate_or_add_local_exact_test",
        "worklist_reason": (
            "selected compile-positive case is reused by multiple requirement "
            "rows; exact coverage needs split proof or local exact cases"
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache", default="cache")
    parser.add_argument(
        "--exactness-audit",
        default="cache/ecma262-regexp-exactness-audit.tsv",
    )
    parser.add_argument(
        "--selection",
        default="cache/ecma262-regexp-compile-parser-test-selection.tsv",
    )
    parser.add_argument(
        "--requirement-matrix",
        default="cache/ecma262-regexp-requirement-matrix.tsv",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    cache = Path(args.cache)
    exactness_path = Path(args.exactness_audit)
    selection_path = Path(args.selection)
    requirement_path = Path(args.requirement_matrix)
    detail = cache / DETAIL_NAME
    summary = cache / SUMMARY_NAME

    if not exactness_path.is_file():
        raise SystemExit(
            f"missing exactness audit at {exactness_path}; "
            "run tools/build_ecma262_regexp_exactness_audit.py first"
        )
    if not selection_path.is_file():
        raise SystemExit(
            f"missing compile/parser selection at {selection_path}; "
            "run tools/map_ecma262_compile_parser_candidates.py first"
        )
    if not requirement_path.is_file():
        raise SystemExit(
            f"missing requirement matrix at {requirement_path}; "
            "run tools/build_ecma262_regexp_requirement_matrix.py first"
        )

    exactness_fields, exactness_rows = read_tsv(exactness_path)
    selection_fields, selection_rows = read_tsv(selection_path)
    requirement_fields, requirement_rows = read_tsv(requirement_path)

    require_columns(
        exactness_path,
        exactness_fields,
        {
            "requirement_id",
            "mapping_family",
            "executable_layer",
            "evidence_kind",
            "case_id",
            "case_source",
            "expected_behavior",
            "selector_tags",
            "selected_feature_tags",
            "selected_missing_selector_tags",
            "case_reuse_count",
            "audit_scope",
            "exactness_audit_state",
            "coverage_credit",
            "next_action",
        },
    )
    require_columns(
        selection_path,
        selection_fields,
        {
            "requirement_id",
            "selected_case_id",
            "selected_case_source",
            "selected_pattern",
            "selected_flags",
            "selected_feature_tags",
            "selected_expected_behavior",
            "selected_missing_selector_tags",
            "selection_state",
            "selection_exactness",
            "semantic_family",
        },
    )
    require_columns(
        requirement_path,
        requirement_fields,
        {
            "requirement_id",
            "clause_id",
            "clause_title",
            "source_file",
            "section_anchor",
            "requirement_kind",
            "requirement_text",
        },
    )

    selection_by_requirement = row_by_requirement(selection_rows, str(selection_path))
    requirement_by_requirement = row_by_requirement(requirement_rows, str(requirement_path))

    reused_exactness_rows = [
        row
        for row in exactness_rows
        if row["exactness_audit_state"] == "open_reused_candidate_needs_exact_proof"
    ]
    for row in reused_exactness_rows:
        validate_exactness_row(row)
        requirement_id = row["requirement_id"]
        if requirement_id not in selection_by_requirement:
            raise SystemExit(f"reused row {requirement_id} missing from selection")
        if requirement_id not in requirement_by_requirement:
            raise SystemExit(f"reused row {requirement_id} missing from requirement matrix")
        validate_selection_row(row, selection_by_requirement[requirement_id])
        if not ecma262_source_exists(requirement_by_requirement[requirement_id]["source_file"]):
            raise SystemExit(
                f"reused row {requirement_id} missing ECMA source: "
                f"{requirement_by_requirement[requirement_id]['source_file']}"
            )

    clusters: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in reused_exactness_rows:
        selection = selection_by_requirement[row["requirement_id"]]
        requirement = requirement_by_requirement[row["requirement_id"]]
        clusters[row["case_id"]].append(
            {
                **row,
                "clause_id": requirement["clause_id"],
                "semantic_family": selection["semantic_family"],
                "selected_case_source": selection["selected_case_source"],
            }
        )

    rows = [
        build_row(
            row,
            selection_by_requirement[row["requirement_id"]],
            requirement_by_requirement[row["requirement_id"]],
            clusters[row["case_id"]],
        )
        for row in reused_exactness_rows
    ]

    seen_worklist_ids: set[str] = set()
    for row in rows:
        worklist_id = row["worklist_id"]
        if worklist_id in seen_worklist_ids:
            raise SystemExit(f"duplicate worklist_id {worklist_id}")
        seen_worklist_ids.add(worklist_id)

    state_counts = Counter(row["reuse_worklist_state"] for row in rows)
    decision_counts = Counter(row["proof_decision"] for row in rows)
    credit_counts = Counter(row["coverage_credit"] for row in rows)
    pressure_counts = Counter(row["cluster_pressure"] for row in rows)
    family_counts = Counter(row["mapping_family"] for row in rows)
    layer_counts = Counter(row["executable_layer"] for row in rows)
    cluster_size_counts = Counter(row["cluster_size"] for row in rows)
    case_counts = Counter(row["selected_case_id"] for row in rows)
    largest_cluster_size = max((int(size) for size in cluster_size_counts), default=0)
    coverage_credit_rows = sum(
        count for credit, count in credit_counts.items() if not credit.startswith("none")
    )

    summary_lines = [
        "ecma262_snapshot\t2026\n",
        f"input_exactness_audit\t{exactness_path}\n",
        f"input_selection\t{selection_path}\n",
        f"input_requirement_matrix\t{requirement_path}\n",
        f"exactness_audit_rows\t{len(exactness_rows)}\n",
        f"reused_candidate_rows\t{len(rows)}\n",
        f"reused_candidate_clusters\t{len(clusters)}\n",
        f"largest_reused_candidate_cluster_size\t{largest_cluster_size}\n",
        f"coverage_credit_rows\t{coverage_credit_rows}\n",
        f"planned_detail_output\t{detail}\n",
        f"planned_summary_output\t{summary}\n",
        f"dry_run\t{bool_text(args.dry_run)}\n",
    ]
    for name, count in sorted(state_counts.items()):
        summary_lines.append(f"reuse_worklist_state_{name}\t{count}\n")
    for name, count in sorted(decision_counts.items()):
        summary_lines.append(f"proof_decision_{name}\t{count}\n")
    for name, count in sorted(credit_counts.items()):
        summary_lines.append(f"coverage_credit_{name}\t{count}\n")
    for name, count in sorted(pressure_counts.items()):
        summary_lines.append(f"cluster_pressure_{name}\t{count}\n")
    for name, count in sorted(family_counts.items()):
        summary_lines.append(f"mapping_family_{name}\t{count}\n")
    for name, count in sorted(layer_counts.items()):
        summary_lines.append(f"executable_layer_{name}\t{count}\n")
    for name, count in sorted(cluster_size_counts.items(), key=lambda item: int(item[0])):
        summary_lines.append(f"cluster_size_{name}\t{count}\n")
    for case_id, count in case_counts.most_common():
        summary_lines.append(f"reused_case_{case_id}\t{count}\n")

    if args.dry_run:
        print("".join(summary_lines), end="")
        return

    cache.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "worklist_id",
        "requirement_id",
        "clause_id",
        "clause_title",
        "source_file",
        "section_anchor",
        "requirement_kind",
        "requirement_text",
        "semantic_family",
        "mapping_family",
        "executable_layer",
        "selector_tags",
        "selected_feature_tags",
        "selected_case_id",
        "selected_case_source",
        "selected_pattern",
        "selected_flags",
        "case_reuse_count",
        "cluster_size",
        "cluster_mapping_family_count",
        "cluster_executable_layer_count",
        "cluster_selector_signature_count",
        "cluster_clause_count",
        "cluster_semantic_family_count",
        "cluster_pressure",
        "reuse_worklist_state",
        "proof_decision",
        "coverage_credit",
        "next_action",
        "worklist_reason",
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
