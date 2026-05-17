#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import subprocess
from collections import Counter
from pathlib import Path

from ecma262_tooling import read_tsv_rows


DETAIL_NAME = "test262-regexp-coverage-matrix.tsv"
SUMMARY_NAME = "test262-regexp-coverage-matrix.summary"


def git_revision(root: Path) -> str:
    return subprocess.check_output(
        ["git", "-C", str(root), "rev-parse", "HEAD"], text=True
    ).strip()


def feature_set(row: dict[str, str]) -> set[str]:
    value = row.get("features", "") or row.get("inventory_features", "")
    if not value:
        return set()
    return {part for part in value.split(",") if part}


def has_any(features: set[str], names: set[str]) -> bool:
    return bool(features.intersection(names))


def spec_area(path: str, features: set[str], bucket: str, candidate_class: str) -> str:
    if candidate_class == "metadata_only_regexp_reference":
        return "metadata_reference"
    if candidate_class == "text_fixture_regexp_word":
        return "text_fixture"
    if candidate_class == "weak_content_match_noise":
        return "false_positive_content_signal"
    if candidate_class == "consumer_assertion_usage":
        return "consumer_assertion_usage"
    if candidate_class == "generic_regexp_object_usage":
        return "generic_regexp_object_usage"
    if candidate_class == "regexp_literal_js_grammar":
        return "regexp_literal_lexical_grammar"
    if candidate_class == "js_regexp_api_integration":
        return "js_regexp_api_integration"

    if bucket == "secondary":
        return "string_symbol_integration"
    if "RegExpStringIteratorPrototype" in path:
        return "regexp_string_iterator"
    if path.startswith("test/language/literals/regexp/") or has_any(
        features, {"literal_regexp"}
    ):
        return "regexp_literal_lexical_grammar"
    if has_any(features, {"syntax_errors"}):
        return "regexp_syntax_negative"
    if has_any(features, {"unicode", "unicodeSets", "property_escapes"}):
        return "regexp_unicode_semantics"
    if has_any(
        features,
        {
            "exec",
            "test_method",
            "lastIndex",
            "captures",
            "named_captures",
            "backreferences",
        },
    ):
        return "regexp_exec_and_captures"
    if has_any(features, {"flags", "global", "ignoreCase", "multiline", "dotAll", "sticky", "hasIndices"}):
        return "regexp_flags"
    if has_any(
        features,
        {
            "character_classes",
            "character_class_escapes",
            "quantifiers",
            "alternation",
            "assertions",
            "lookahead",
            "lookbehind",
        },
    ):
        return "regexp_pattern_syntax_positive"
    if has_any(features, {"annexB"}):
        return "annexB_regexp"
    return "unclassified_regexp_surface"


def spec_cluster(area: str) -> str:
    if area in {
        "regexp_pattern_syntax_positive",
        "regexp_syntax_negative",
        "regexp_literal_lexical_grammar",
        "annexB_regexp",
    }:
        return "syntax"
    if area in {
        "regexp_exec_and_captures",
        "regexp_unicode_semantics",
        "regexp_flags",
        "regexp_string_iterator",
    }:
        return "regexp_runtime"
    if area in {"string_symbol_integration", "js_regexp_api_integration"}:
        return "api_integration"
    if area in {
        "consumer_assertion_usage",
        "generic_regexp_object_usage",
        "metadata_reference",
        "text_fixture",
        "false_positive_content_signal",
    }:
        return "non_core_evidence"
    return "unknown"


def coverage_status(
    bucket: str,
    path: str,
    action: str,
    area: str,
    core_compile_paths: set[str],
) -> tuple[str, str]:
    if action == "do_not_promote_regexp_corpus":
        return (
            "tracked_not_promoted",
            "candidate audit says this must not become RegExp corpus evidence",
        )
    if action == "downstream_or_helper_evidence":
        return (
            "tracked_downstream_evidence",
            "tracked as downstream/helper evidence, not a current core test gate",
        )
    if action == "scope_decision":
        return (
            "needs_scope_decision",
            "requires explicit product decision before executable test gate",
        )
    if action == "promote_core_corpus":
        if path in core_compile_paths:
            return (
                "compile_cases_connected",
                "accepted literal compile cases are generated and executed as red tests",
            )
        return (
            "promoted_no_compile_literals",
            "promoted core file has no extracted regex literal compile case yet",
        )

    if bucket == "primary":
        if area == "regexp_syntax_negative":
            return (
                "needs_negative_syntax_extraction",
                "primary test262 negative syntax layer is not generated yet",
            )
        return (
            "needs_primary_executable_mapping",
            "primary test262 RegExp file is inventoried but not executable in OCaml harness yet",
        )
    if bucket == "secondary":
        return (
            "needs_secondary_integration_mapping",
            "secondary String/Symbol integration file is inventoried but not executable yet",
        )
    return ("needs_manual_route", "row has no coverage route")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--test262", default="external/test262")
    parser.add_argument("--cache", default="cache")
    parser.add_argument(
        "--inventory", default="cache/test262-regexp-inventory.tsv"
    )
    parser.add_argument(
        "--candidate-audit", default="cache/test262-regexp-candidate-audit.tsv"
    )
    parser.add_argument(
        "--core-compile-cases", default="cache/test262-regexp-core-compile-cases.tsv"
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    test262 = Path(args.test262)
    cache = Path(args.cache)
    inventory_path = Path(args.inventory)
    candidate_audit_path = Path(args.candidate_audit)
    core_compile_cases_path = Path(args.core_compile_cases)
    detail = cache / DETAIL_NAME
    summary = cache / SUMMARY_NAME

    if not test262.is_dir():
        raise SystemExit(f"missing test262 checkout at {test262}")
    if not inventory_path.is_file():
        raise SystemExit(
            f"missing inventory at {inventory_path}; run tools/inventory_test262_regexp.py"
        )
    if not candidate_audit_path.is_file():
        raise SystemExit(
            f"missing candidate audit at {candidate_audit_path}; run tools/audit_test262_regexp_candidates.py"
        )
    if not core_compile_cases_path.is_file():
        raise SystemExit(
            f"missing core compile cases at {core_compile_cases_path}; run tools/extract_test262_regexp_core.py"
        )

    candidate_audit = {
        row["path"]: row for row in read_tsv_rows(candidate_audit_path)
    }
    core_compile_paths = {
        row["source_path"] for row in read_tsv_rows(core_compile_cases_path)
    }

    rows = []
    for inventory_row in read_tsv_rows(inventory_path):
        path = inventory_row["path"]
        bucket = inventory_row["bucket"]
        candidate_row = candidate_audit.get(path, {})
        candidate_class = candidate_row.get("candidate_class", "")
        action = candidate_row.get("action", "")
        features = feature_set(inventory_row)
        area = spec_area(path, features, bucket, candidate_class)
        cluster = spec_cluster(area)
        status, reason = coverage_status(
            bucket=bucket,
            path=path,
            action=action,
            area=area,
            core_compile_paths=core_compile_paths,
        )
        rows.append(
            {
                "path": path,
                "bucket": bucket,
                "source": inventory_row.get("source", ""),
                "features": inventory_row.get("features", ""),
                "candidate_class": candidate_class,
                "candidate_action": action,
                "spec_cluster": cluster,
                "spec_area": area,
                "coverage_status": status,
                "coverage_reason": reason,
            }
        )

    bucket_counts = Counter(row["bucket"] for row in rows)
    cluster_counts = Counter(row["spec_cluster"] for row in rows)
    area_counts = Counter(row["spec_area"] for row in rows)
    status_counts = Counter(row["coverage_status"] for row in rows)
    action_counts = Counter(
        row["candidate_action"] or "<non_candidate>" for row in rows
    )

    summary_lines = [
        f"revision\t{git_revision(test262)}\n",
        f"input_inventory\t{inventory_path}\n",
        f"input_candidate_audit\t{candidate_audit_path}\n",
        f"input_core_compile_cases\t{core_compile_cases_path}\n",
        f"matrix_rows\t{len(rows)}\n",
        f"planned_detail_output\t{detail}\n",
        f"planned_summary_output\t{summary}\n",
        f"dry_run\t{str(args.dry_run).lower()}\n",
    ]
    for name, count in sorted(bucket_counts.items()):
        summary_lines.append(f"bucket_{name}\t{count}\n")
    for name, count in sorted(action_counts.items()):
        summary_lines.append(f"candidate_action_{name}\t{count}\n")
    for name, count in sorted(cluster_counts.items()):
        summary_lines.append(f"cluster_{name}\t{count}\n")
    for name, count in sorted(area_counts.items()):
        summary_lines.append(f"area_{name}\t{count}\n")
    for name, count in sorted(status_counts.items()):
        summary_lines.append(f"status_{name}\t{count}\n")

    if args.dry_run:
        print("".join(summary_lines), end="")
        return

    cache.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "path",
        "bucket",
        "source",
        "features",
        "candidate_class",
        "candidate_action",
        "spec_cluster",
        "spec_area",
        "coverage_status",
        "coverage_reason",
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
