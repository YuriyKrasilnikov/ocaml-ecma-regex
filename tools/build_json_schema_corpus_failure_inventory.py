#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import subprocess
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from ecma262_tooling import safe_id, write_tsv


DETAIL_NAME = "json-schema-corpus-failure-inventory.tsv"
SUMMARY_NAME = "json-schema-corpus-failure-inventory.summary"
WORKLIST_DETAIL_NAME = "json-schema-corpus-failure-worklist.tsv"
WORKLIST_SUMMARY_NAME = "json-schema-corpus-failure-worklist.summary"
RUN_OUTPUT_DIR_NAME = "json-schema-corpus-alcotest-runs"
CORPUS_ROOT = Path("external/json-schema-test-suite/tests")
MANIFEST_PATH = Path("test/json_schema_corpus_files.tsv")


DETAIL_FIELDS = [
    "suite",
    "draft",
    "corpus_file",
    "case_index",
    "case_description",
    "schema_keyword",
    "schema_shape",
    "pattern_count",
    "patterns",
    "data_tests",
    "expected_valid",
    "expected_invalid",
    "observed_status",
    "failure_family",
    "implementation_bucket",
    "failure_message",
    "log_file",
]

WORKLIST_FIELDS = [
    "worklist_id",
    "suite",
    "draft",
    "corpus_file",
    "case_index",
    "case_description",
    "schema_keyword",
    "schema_shape",
    "pattern_count",
    "patterns",
    "data_tests",
    "expected_valid",
    "expected_invalid",
    "failure_family",
    "implementation_bucket",
    "owner_layer",
    "priority",
    "next_action",
    "target_test_artifact",
    "coverage_credit",
    "worklist_reason",
]

FAMILY_POLICY = {
    "format_regex_semantics": (
        "compile_parser",
        "1",
        "add_format_regex_compile_parser_exact_case",
        "test/test_json_schema_corpus.ml",
        "format regex corpus row exposes ECMA-262 syntax acceptance mismatch",
    ),
    "character_class_digit_semantics": (
        "match_engine_character_classes",
        "2",
        "add_json_schema_character_class_exact_case",
        "test/test_json_schema_corpus.ml",
        "JSON Schema patternProperties row exposes ECMA-262 digit class semantics mismatch",
    ),
    "character_class_word_semantics": (
        "match_engine_character_classes",
        "2",
        "add_json_schema_character_class_exact_case",
        "test/test_json_schema_corpus.ml",
        "JSON Schema patternProperties row exposes ECMA-262 word class semantics mismatch",
    ),
    "unicode_property_escape_semantics": (
        "match_engine_unicode",
        "3",
        "add_json_schema_unicode_property_exact_case",
        "test/test_json_schema_corpus.ml",
        "JSON Schema corpus row exposes Unicode property escape semantics mismatch",
    ),
    "unicode_non_bmp_semantics": (
        "match_engine_unicode",
        "4",
        "add_json_schema_non_bmp_exact_case",
        "test/test_json_schema_corpus.ml",
        "JSON Schema corpus row exposes non-BMP and UTF-16 pattern semantics mismatch",
    ),
    "unicode_semantics": (
        "match_engine_unicode",
        "5",
        "add_json_schema_unicode_mode_exact_case",
        "test/test_json_schema_corpus.ml",
        "JSON Schema corpus row exposes Unicode mode/range semantics mismatch",
    ),
}


@dataclass(frozen=True)
class RunnerResult:
    statuses: dict[tuple[str, int], str]
    run_id: str
    run_dir: Path
    stdout: str
    stderr: str
    returncode: int


def read_manifest(path: Path) -> list[tuple[str, Path]]:
    if not path.is_file():
        raise SystemExit(f"missing JSON Schema corpus manifest: {path}")
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        if reader.fieldnames != ["suite", "rel_path"]:
            raise SystemExit(f"invalid JSON Schema corpus manifest header in {path}")
        rows = [(row["suite"], Path(row["rel_path"])) for row in reader]
    if not rows:
        raise SystemExit(f"empty JSON Schema corpus manifest: {path}")
    return rows


def read_cases(path: Path) -> list[dict]:
    if not path.is_file():
        raise SystemExit(f"missing JSON Schema corpus file: {path}")
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise SystemExit(f"expected top-level JSON array in {path}")
    return data


def compact_text(value: str, limit: int = 240) -> str:
    compact = " ".join(str(value).split())
    if len(compact) > limit:
        return compact[: limit - 3] + "..."
    return compact


def encode_json(value: object, limit: int = 240) -> str:
    return compact_text(json.dumps(value, ensure_ascii=False, sort_keys=True), limit)


def schema_metadata(schema: object) -> dict[str, str]:
    if not isinstance(schema, dict):
        return {
            "schema_keyword": "unsupported",
            "schema_shape": "unsupported_schema_non_object",
            "pattern_count": "0",
            "patterns": "",
        }
    if isinstance(schema.get("pattern"), str):
        return {
            "schema_keyword": "pattern",
            "schema_shape": "pattern_string",
            "pattern_count": "1",
            "patterns": schema["pattern"],
        }
    pattern_properties = schema.get("patternProperties")
    if isinstance(pattern_properties, dict):
        patterns = list(pattern_properties.keys())
        shape = (
            "patternProperties_single_entry"
            if len(patterns) == 1
            else "patternProperties_multi_entry"
        )
        return {
            "schema_keyword": "patternProperties",
            "schema_shape": shape,
            "pattern_count": str(len(patterns)),
            "patterns": encode_json(patterns),
        }
    if schema.get("format") == "regex":
        return {
            "schema_keyword": "format",
            "schema_shape": "format_regex",
            "pattern_count": "0",
            "patterns": "",
        }
    return {
        "schema_keyword": "unsupported",
        "schema_shape": "unsupported_schema_shape",
        "pattern_count": "0",
        "patterns": "",
    }


def expected_counts(case: dict) -> tuple[int, int, int]:
    tests = case.get("tests")
    if not isinstance(tests, list):
        raise SystemExit(f"case {case.get('description', '<unknown>')} has no tests list")
    valid = 0
    invalid = 0
    for test in tests:
        if not isinstance(test, dict) or not isinstance(test.get("valid"), bool):
            raise SystemExit("JSON Schema corpus test has missing boolean valid field")
        if test["valid"]:
            valid += 1
        else:
            invalid += 1
    return len(tests), valid, invalid


def log_filename(suite: str, index: int) -> str:
    return f"{suite.replace('/', '-')}.{index:03d}.output"


def first_log_message(path: Path) -> str:
    if not path.is_file():
        return ""
    with path.open(encoding="utf-8", errors="replace") as f:
        lines = [line.strip() for line in f if line.strip()]
    return compact_text(" | ".join(lines), 400)


def classify_failure(message: str, metadata: dict[str, str]) -> tuple[str, str]:
    plain = re.sub(r"\x1b\[[0-9;]*m", "", message)
    lower = plain.lower()
    keyword = metadata["schema_keyword"]
    descriptionish = lower + " " + metadata["patterns"].lower()

    if not plain:
        return ("none", "none")
    if "unsupported schema shape" in lower:
        return ("json_schema_harness_unsupported_schema_shape", "json_schema_harness")
    if "not implemented for start anchor" in lower:
        return ("matcher_runtime_start_anchor", "match_engine_assertions")
    if "not implemented for end anchor" in lower:
        return ("matcher_runtime_end_anchor", "match_engine_assertions")
    if "not implemented for quantifier" in lower:
        return ("matcher_runtime_quantifier", "match_engine_quantifiers")
    if "not implemented for non-ascii code point" in lower:
        return ("unicode_non_ascii_code_point", "match_engine_unicode")
    if "not implemented for unicode property escape" in lower:
        return ("unicode_property_escape_semantics", "match_engine_unicode")
    if "compile failed" in lower:
        return ("compile_parser_regex_syntax", "compile_parser")
    if "\\p" in descriptionish or "\\p" in plain:
        return ("unicode_property_escape_semantics", "match_engine_unicode")
    if "non-bmp" in descriptionish or "surrogate" in descriptionish:
        return ("unicode_non_bmp_semantics", "match_engine_unicode")
    if "\\d" in descriptionish or "\\d" in plain:
        return ("character_class_digit_semantics", "match_engine_character_classes")
    if "\\w" in descriptionish or "\\w" in plain:
        return ("character_class_word_semantics", "match_engine_character_classes")
    if "\\s" in descriptionish or "\\s" in plain:
        return ("character_class_space_semantics", "match_engine_character_classes")
    if "unicode" in descriptionish:
        return ("unicode_semantics", "match_engine_unicode")
    if keyword == "format":
        return ("format_regex_semantics", "compile_parser")
    return ("assertion_mismatch_unclassified", "needs_triage")


def parse_runner_status(stdout: str, run_output_dir: Path) -> tuple[dict[tuple[str, int], str], str, Path]:
    run_match = re.search(r"This run has ID [`']([A-Za-z0-9]+)[`']", stdout)
    if not run_match:
        raise SystemExit(
            "could not parse Alcotest run id from runner output\n"
            f"runner_output_prefix={stdout[:1000]!r}"
        )
    run_id = run_match.group(1)
    statuses: dict[tuple[str, int], str] = {}
    status_re = re.compile(r"^\s*>?\s*\[(OK|FAIL)\]\s+(.+?)\s+(\d+)\s+")
    for line in stdout.splitlines():
        match = status_re.match(line)
        if match is None:
            continue
        status = "pass" if match.group(1) == "OK" else "fail"
        suite = match.group(2).rstrip()
        index = int(match.group(3))
        statuses[(suite, index)] = status
    if not statuses:
        raise SystemExit("could not parse Alcotest case statuses from runner output")
    return statuses, run_id, run_output_dir / run_id


def run_corpus(run_output_dir: Path) -> RunnerResult:
    run_output_dir.mkdir(parents=True, exist_ok=True)
    command = [
        "opam",
        "exec",
        "--",
        "dune",
        "exec",
        "test/test_json_schema_corpus.exe",
        "--",
        "test",
        "--color=never",
        "-o",
        str(run_output_dir),
    ]
    env = os.environ.copy()
    env["ALCOTEST_COLUMNS"] = "220"
    completed = subprocess.run(command, text=True, capture_output=True, env=env, check=False)
    stdout = completed.stdout
    stderr = completed.stderr
    combined_output = stdout + "\n" + stderr
    statuses, run_id, run_dir = parse_runner_status(combined_output, run_output_dir)
    if completed.returncode == 0:
        returncode_ok = True
    else:
        returncode_ok = completed.returncode == 1
    if not returncode_ok:
        raise SystemExit(
            f"unexpected corpus runner exit {completed.returncode}\nSTDOUT:\n{stdout}\nSTDERR:\n{stderr}"
        )
    return RunnerResult(
        statuses=statuses,
        run_id=run_id,
        run_dir=run_dir,
        stdout=stdout,
        stderr=stderr,
        returncode=completed.returncode,
    )


def build_rows(
    manifest: list[tuple[str, Path]],
    result: RunnerResult,
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    expected_status_keys: set[tuple[str, int]] = set()
    for suite, rel_path in manifest:
        draft, corpus_file = suite.split(" ", 1)
        cases = read_cases(rel_path)
        for index, case in enumerate(cases):
            key = (suite, index)
            expected_status_keys.add(key)
            if key not in result.statuses:
                raise SystemExit(f"runner output missing status for {suite} case {index}")
            metadata = schema_metadata(case.get("schema"))
            data_tests, expected_valid, expected_invalid = expected_counts(case)
            status = result.statuses[key]
            log_path = result.run_dir / log_filename(suite, index)
            message = first_log_message(log_path) if status == "fail" else ""
            failure_family, implementation_bucket = (
                classify_failure(message, metadata) if status == "fail" else ("none", "none")
            )
            rows.append(
                {
                    "suite": suite,
                    "draft": draft,
                    "corpus_file": corpus_file,
                    "case_index": str(index),
                    "case_description": compact_text(case.get("description", "")),
                    "schema_keyword": metadata["schema_keyword"],
                    "schema_shape": metadata["schema_shape"],
                    "pattern_count": metadata["pattern_count"],
                    "patterns": compact_text(metadata["patterns"]),
                    "data_tests": str(data_tests),
                    "expected_valid": str(expected_valid),
                    "expected_invalid": str(expected_invalid),
                    "observed_status": status,
                    "failure_family": failure_family,
                    "implementation_bucket": implementation_bucket,
                    "failure_message": message,
                    "log_file": str(log_path) if status == "fail" else "",
                }
            )
    extra = set(result.statuses).difference(expected_status_keys)
    if extra:
        formatted = ", ".join(f"{suite}#{index}" for suite, index in sorted(extra))
        raise SystemExit(f"runner output has unexpected cases: {formatted}")
    return rows


def worklist_row(row: dict[str, str]) -> dict[str, str]:
    failure_family = row["failure_family"]
    if failure_family not in FAMILY_POLICY:
        raise SystemExit(
            f"unsupported JSON Schema failure family {failure_family!r} "
            f"for {row['suite']}#{row['case_index']}"
        )
    owner_layer, priority, next_action, target, reason = FAMILY_POLICY[failure_family]
    expected_bucket = row["implementation_bucket"]
    if expected_bucket != owner_layer:
        raise SystemExit(
            f"failure family {failure_family} has bucket {expected_bucket!r}; "
            f"expected {owner_layer!r}"
        )
    worklist_id = (
        "json-schema-failure:"
        f"{safe_id(row['draft'])}:"
        f"{safe_id(row['corpus_file'])}:"
        f"{int(row['case_index']):04d}:"
        f"{safe_id(failure_family)}"
    )
    return {
        "worklist_id": worklist_id,
        "suite": row["suite"],
        "draft": row["draft"],
        "corpus_file": row["corpus_file"],
        "case_index": row["case_index"],
        "case_description": row["case_description"],
        "schema_keyword": row["schema_keyword"],
        "schema_shape": row["schema_shape"],
        "pattern_count": row["pattern_count"],
        "patterns": row["patterns"],
        "data_tests": row["data_tests"],
        "expected_valid": row["expected_valid"],
        "expected_invalid": row["expected_invalid"],
        "failure_family": failure_family,
        "implementation_bucket": expected_bucket,
        "owner_layer": owner_layer,
        "priority": priority,
        "next_action": next_action,
        "target_test_artifact": target,
        "coverage_credit": "none_json_schema_consumer_worklist",
        "worklist_reason": reason,
    }


def build_worklist_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    worklist_rows = [
        worklist_row(row)
        for row in rows
        if row["observed_status"] == "fail"
    ]
    validate_worklist_rows(worklist_rows)
    return worklist_rows


def validate_worklist_rows(rows: list[dict[str, str]]) -> None:
    seen: set[str] = set()
    for row in rows:
        worklist_id = row["worklist_id"]
        if worklist_id in seen:
            raise SystemExit(f"duplicate worklist_id {worklist_id}")
        seen.add(worklist_id)
        for field in WORKLIST_FIELDS:
            if field not in row:
                raise SystemExit(f"{worklist_id}: missing field {field}")
        if row["coverage_credit"] != "none_json_schema_consumer_worklist":
            raise SystemExit(f"{worklist_id}: worklist must not assign coverage credit")
        if not Path(row["target_test_artifact"]).is_file():
            raise SystemExit(
                f"{worklist_id}: missing target test artifact "
                f"{row['target_test_artifact']}"
            )


def write_worklist_summary(
    path: Path,
    rows: list[dict[str, str]],
    inventory: Path,
    detail: Path,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    family_counts = Counter(row["failure_family"] for row in rows)
    bucket_counts = Counter(row["implementation_bucket"] for row in rows)
    owner_counts = Counter(row["owner_layer"] for row in rows)
    priority_counts = Counter(row["priority"] for row in rows)
    action_counts = Counter(row["next_action"] for row in rows)
    keyword_counts = Counter(row["schema_keyword"] for row in rows)
    shape_counts = Counter(row["schema_shape"] for row in rows)
    lines = [
        f"input_failure_inventory\t{inventory}",
        f"worklist_rows\t{len(rows)}",
        "coverage_credit_rows\t0",
        f"detail_output\t{detail}",
        f"summary_output\t{path}",
        "dry_run\tfalse",
    ]
    for name, counts in [
        ("failure_family", family_counts),
        ("implementation_bucket", bucket_counts),
        ("owner_layer", owner_counts),
        ("priority", priority_counts),
        ("next_action", action_counts),
        ("schema_keyword", keyword_counts),
        ("schema_shape", shape_counts),
    ]:
        for key in sorted(counts):
            lines.append(f"{name}_{key}\t{counts[key]}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def count_by(rows: list[dict[str, str]], field: str) -> Counter[str]:
    return Counter(row[field] for row in rows)


def write_summary(
    path: Path,
    rows: list[dict[str, str]],
    result: RunnerResult,
    suite_count: int,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    status_counts = count_by(rows, "observed_status")
    keyword_counts = count_by(rows, "schema_keyword")
    shape_counts = count_by(rows, "schema_shape")
    family_counts = count_by(rows, "failure_family")
    bucket_counts = count_by(rows, "implementation_bucket")
    draft_status_counts = Counter(
        f"{row['draft']}:{row['observed_status']}" for row in rows
    )

    lines = [
        f"input_manifest\t{MANIFEST_PATH}",
        f"input_corpus_root\t{CORPUS_ROOT}",
        f"alcotest_run_id\t{result.run_id}",
        f"alcotest_run_dir\t{result.run_dir}",
        f"alcotest_returncode\t{result.returncode}",
        f"corpus_suites\t{suite_count}",
        f"corpus_cases\t{len(rows)}",
        f"corpus_data_tests\t{sum(int(row['data_tests']) for row in rows)}",
        f"observed_pass\t{status_counts['pass']}",
        f"observed_fail\t{status_counts['fail']}",
    ]
    for name, counts in [
        ("schema_keyword", keyword_counts),
        ("schema_shape", shape_counts),
        ("failure_family", family_counts),
        ("implementation_bucket", bucket_counts),
        ("draft_status", draft_status_counts),
    ]:
        for key in sorted(counts):
            lines.append(f"{name}:{key}\t{counts[key]}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def validate_static_inputs(manifest: list[tuple[str, Path]]) -> tuple[int, int]:
    total_cases = 0
    total_data_tests = 0
    for _, rel_path in manifest:
        cases = read_cases(rel_path)
        total_cases += len(cases)
        for case in cases:
            data_tests, _, _ = expected_counts(case)
            total_data_tests += data_tests
    return total_cases, total_data_tests


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache", default="cache")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    cache = Path(args.cache)
    detail_path = cache / DETAIL_NAME
    summary_path = cache / SUMMARY_NAME
    worklist_detail_path = cache / WORKLIST_DETAIL_NAME
    worklist_summary_path = cache / WORKLIST_SUMMARY_NAME
    run_output_dir = cache / RUN_OUTPUT_DIR_NAME
    manifest = read_manifest(MANIFEST_PATH)

    total_cases, total_data_tests = validate_static_inputs(manifest)
    if args.dry_run:
        print(f"input_manifest\t{MANIFEST_PATH}")
        print(f"input_corpus_root\t{CORPUS_ROOT}")
        print(f"corpus_suites\t{len(manifest)}")
        print(f"corpus_cases\t{total_cases}")
        print(f"corpus_data_tests\t{total_data_tests}")
        print(f"would_write_detail\t{detail_path}")
        print(f"would_write_summary\t{summary_path}")
        print(f"would_write_worklist_detail\t{worklist_detail_path}")
        print(f"would_write_worklist_summary\t{worklist_summary_path}")
        print(f"would_write_alcotest_logs_under\t{run_output_dir}")
        return

    result = run_corpus(run_output_dir)
    rows = build_rows(manifest, result)
    write_tsv(detail_path, DETAIL_FIELDS, rows)
    write_summary(summary_path, rows, result, len(manifest))
    worklist_rows = build_worklist_rows(rows)
    write_tsv(worklist_detail_path, WORKLIST_FIELDS, worklist_rows)
    write_worklist_summary(
        worklist_summary_path,
        worklist_rows,
        detail_path,
        worklist_detail_path,
    )
    print(f"wrote\t{detail_path}")
    print(f"wrote\t{summary_path}")
    print(f"wrote\t{worklist_detail_path}")
    print(f"wrote\t{worklist_summary_path}")


if __name__ == "__main__":
    main()
