#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path

from ecma262_tooling import read_tsv_rows


DETAIL_NAME = "ecma262-regexp-clause-matrix.tsv"
SUMMARY_NAME = "ecma262-regexp-clause-matrix.summary"

ECMA262_BASE = "https://tc39.es/ecma262/2026/multipage"
NOTATIONAL_URL = f"{ECMA262_BASE}/notational-conventions.html"
ABSTRACT_OPS_URL = f"{ECMA262_BASE}/abstract-operations.html"
LEXICAL_URL = f"{ECMA262_BASE}/ecmascript-language-lexical-grammar.html"
EXPRESSIONS_URL = f"{ECMA262_BASE}/ecmascript-language-expressions.html"
TEXT_URL = f"{ECMA262_BASE}/text-processing.html"
ANNEXB_URL = f"{ECMA262_BASE}/additional-ecmascript-features-for-web-browsers.html"


def clause(
    clause_id: str,
    title: str,
    spec_cluster: str,
    implementation_layer: str,
    coverage_areas: list[str],
    source_url: str = TEXT_URL,
    required_sources: str = "ecma262,test262,local",
) -> dict[str, str]:
    return {
        "clause_id": clause_id,
        "title": title,
        "source_url": source_url,
        "spec_cluster": spec_cluster,
        "implementation_layer": implementation_layer,
        "coverage_areas": "|".join(coverage_areas),
        "required_sources": required_sources,
    }


CLAUSES = [
    clause(
        "5.1.2",
        "The Lexical and RegExp Grammars",
        "grammar_model",
        "spec_model",
        ["regexp_pattern_syntax_positive"],
        source_url=NOTATIONAL_URL,
    ),
    clause(
        "12.9.5",
        "Regular Expression Literals",
        "regexp_literal_lexical_grammar",
        "lexer",
        ["regexp_literal_lexical_grammar"],
        source_url=LEXICAL_URL,
    ),
    clause(
        "12.9.5.1",
        "Static Semantics: BodyText",
        "regexp_literal_lexical_grammar",
        "lexer",
        ["regexp_literal_lexical_grammar"],
        source_url=LEXICAL_URL,
    ),
    clause(
        "12.9.5.2",
        "Static Semantics: FlagText",
        "regexp_literal_lexical_grammar",
        "lexer",
        ["regexp_literal_lexical_grammar", "regexp_flags"],
        source_url=LEXICAL_URL,
    ),
    clause(
        "13.2.7",
        "Regular Expression Literals",
        "regexp_literal_expression",
        "compile_surface",
        ["regexp_literal_lexical_grammar"],
        source_url=EXPRESSIONS_URL,
    ),
    clause(
        "13.2.7.1",
        "Static Semantics: Early Errors",
        "regexp_literal_expression",
        "compile_surface",
        ["regexp_syntax_negative"],
        source_url=EXPRESSIONS_URL,
    ),
    clause(
        "13.2.7.2",
        "Static Semantics: IsValidRegularExpressionLiteral",
        "regexp_literal_expression",
        "compile_surface",
        ["regexp_syntax_negative", "regexp_pattern_syntax_positive"],
        source_url=EXPRESSIONS_URL,
    ),
    clause(
        "13.2.7.3",
        "Runtime Semantics: Evaluation",
        "regexp_literal_expression",
        "compile_surface",
        ["regexp_literal_lexical_grammar", "regexp_flags"],
        source_url=EXPRESSIONS_URL,
    ),
    clause("22.2.1", "Patterns", "pattern_grammar", "parser", ["regexp_pattern_syntax_positive", "regexp_syntax_negative"]),
    clause("22.2.1.1", "Static Semantics: Early Errors", "pattern_grammar", "parser", ["regexp_syntax_negative"]),
    clause("22.2.1.2", "Static Semantics: CountLeftCapturingParensWithin", "captures", "parser", ["regexp_exec_and_captures"]),
    clause("22.2.1.3", "Static Semantics: CountLeftCapturingParensBefore", "captures", "parser", ["regexp_exec_and_captures"]),
    clause("22.2.1.4", "Static Semantics: MightBothParticipate", "captures", "parser", ["regexp_exec_and_captures"]),
    clause("22.2.1.5", "Static Semantics: CapturingGroupNumber", "captures", "parser", ["regexp_exec_and_captures"]),
    clause("22.2.1.6", "Static Semantics: IsCharacterClass", "character_classes", "parser", ["regexp_pattern_syntax_positive"]),
    clause("22.2.1.7", "Static Semantics: CharacterValue", "escapes", "parser", ["regexp_pattern_syntax_positive", "regexp_unicode_semantics"]),
    clause("22.2.1.8", "Static Semantics: MayContainStrings", "unicode_sets", "parser", ["regexp_unicode_semantics"]),
    clause("22.2.1.9", "Static Semantics: GroupSpecifiersThatMatch", "captures", "parser", ["regexp_exec_and_captures"]),
    clause("22.2.1.10", "Static Semantics: CapturingGroupName", "captures", "parser", ["regexp_exec_and_captures"]),
    clause("22.2.1.11", "Static Semantics: RegExpIdentifierCodePoints", "captures", "parser", ["regexp_exec_and_captures", "regexp_unicode_semantics"]),
    clause("22.2.1.12", "Static Semantics: RegExpIdentifierCodePoint", "captures", "parser", ["regexp_exec_and_captures", "regexp_unicode_semantics"]),
    clause("22.2.2", "Pattern Semantics", "pattern_semantics", "matcher", ["regexp_exec_and_captures", "regexp_unicode_semantics"]),
    clause("22.2.2.1", "Notation", "pattern_semantics", "matcher", ["regexp_exec_and_captures"]),
    clause("22.2.2.1.1", "RegExp Records", "pattern_semantics", "matcher", ["regexp_exec_and_captures", "regexp_flags"]),
    clause("22.2.2.2", "Runtime Semantics: CompilePattern", "pattern_semantics", "matcher", ["regexp_exec_and_captures", "regexp_unicode_semantics"]),
    clause("22.2.2.3", "Runtime Semantics: CompileSubpattern", "pattern_semantics", "matcher", ["regexp_exec_and_captures"]),
    clause("22.2.2.3.1", "RepeatMatcher", "quantifiers", "matcher", ["regexp_pattern_syntax_positive", "regexp_exec_and_captures"]),
    clause("22.2.2.3.2", "EmptyMatcher", "pattern_semantics", "matcher", ["regexp_exec_and_captures"]),
    clause("22.2.2.3.3", "MatchTwoAlternatives", "alternation", "matcher", ["regexp_pattern_syntax_positive", "regexp_exec_and_captures"]),
    clause("22.2.2.3.4", "MatchSequence", "concatenation", "matcher", ["regexp_exec_and_captures"]),
    clause("22.2.2.4", "Runtime Semantics: CompileAssertion", "assertions", "matcher", ["regexp_pattern_syntax_positive", "regexp_exec_and_captures"]),
    clause("22.2.2.4.1", "IsWordChar", "assertions", "unicode", ["regexp_unicode_semantics", "regexp_exec_and_captures"], required_sources="ecma262,test262,ucd,local"),
    clause("22.2.2.5", "Runtime Semantics: CompileQuantifier", "quantifiers", "matcher", ["regexp_pattern_syntax_positive", "regexp_exec_and_captures"]),
    clause("22.2.2.6", "Runtime Semantics: CompileQuantifierPrefix", "quantifiers", "matcher", ["regexp_pattern_syntax_positive", "regexp_exec_and_captures"]),
    clause("22.2.2.7", "Runtime Semantics: CompileAtom", "atoms", "matcher", ["regexp_pattern_syntax_positive", "regexp_exec_and_captures", "regexp_unicode_semantics"]),
    clause("22.2.2.7.1", "CharacterSetMatcher", "character_classes", "matcher", ["regexp_pattern_syntax_positive", "regexp_unicode_semantics"], required_sources="ecma262,test262,ucd,local"),
    clause("22.2.2.7.2", "BackreferenceMatcher", "backreferences", "matcher", ["regexp_exec_and_captures"]),
    clause("22.2.2.7.3", "Canonicalize", "unicode_case", "unicode", ["regexp_unicode_semantics"], required_sources="ecma262,test262,ucd,local"),
    clause("22.2.2.7.4", "UpdateModifiers", "modifiers", "parser", ["regexp_flags"]),
    clause("22.2.2.8", "Runtime Semantics: CompileCharacterClass", "character_classes", "matcher", ["regexp_pattern_syntax_positive", "regexp_unicode_semantics"], required_sources="ecma262,test262,ucd,local"),
    clause("22.2.2.9", "Runtime Semantics: CompileToCharSet", "character_classes", "matcher", ["regexp_pattern_syntax_positive", "regexp_unicode_semantics"], required_sources="ecma262,test262,ucd,local"),
    clause("22.2.2.9.1", "CharacterRange", "character_classes", "matcher", ["regexp_pattern_syntax_positive", "regexp_unicode_semantics"]),
    clause("22.2.2.9.2", "HasEitherUnicodeFlag", "flags", "compile_surface", ["regexp_flags", "regexp_unicode_semantics"]),
    clause("22.2.2.9.3", "WordCharacters", "unicode_case", "unicode", ["regexp_unicode_semantics"], required_sources="ecma262,test262,ucd,local"),
    clause("22.2.2.9.4", "AllCharacters", "unicode", "unicode", ["regexp_unicode_semantics"], required_sources="ecma262,test262,ucd,local"),
    clause("22.2.2.9.5", "MaybeSimpleCaseFolding", "unicode_case", "unicode", ["regexp_unicode_semantics"], required_sources="ecma262,test262,ucd,local"),
    clause("22.2.2.9.6", "CharacterComplement", "character_classes", "matcher", ["regexp_pattern_syntax_positive", "regexp_unicode_semantics"]),
    clause("22.2.2.9.7", "UnicodeMatchProperty", "unicode_properties", "unicode", ["regexp_unicode_semantics"], required_sources="ecma262,test262,ucd,local"),
    clause("22.2.2.9.8", "UnicodeMatchPropertyValue", "unicode_properties", "unicode", ["regexp_unicode_semantics"], required_sources="ecma262,test262,ucd,local"),
    clause("22.2.2.10", "Runtime Semantics: CompileClassSetString", "unicode_sets", "unicode", ["regexp_unicode_semantics"], required_sources="ecma262,test262,ucd,local"),
    clause("22.2.3", "Abstract Operations for RegExp Creation", "creation", "compile_surface", ["regexp_pattern_syntax_positive", "regexp_flags"]),
    clause("22.2.3.1", "RegExpCreate", "creation", "compile_surface", ["regexp_pattern_syntax_positive", "regexp_flags"]),
    clause("22.2.3.2", "RegExpAlloc", "creation", "js_api_integration", ["js_regexp_api_integration"]),
    clause("22.2.3.3", "RegExpInitialize", "creation", "compile_surface", ["regexp_pattern_syntax_positive", "regexp_flags", "regexp_syntax_negative"]),
    clause("22.2.3.4", "Static Semantics: ParsePattern", "creation", "parser", ["regexp_pattern_syntax_positive", "regexp_syntax_negative"]),
    clause("22.2.4", "The RegExp Constructor", "constructor", "js_api_integration", ["js_regexp_api_integration", "regexp_flags"]),
    clause("22.2.4.1", "RegExp ( pattern, flags )", "constructor", "js_api_integration", ["js_regexp_api_integration", "regexp_flags"]),
    clause("22.2.5", "Properties of the RegExp Constructor", "constructor_properties", "js_api_integration", ["js_regexp_api_integration"]),
    clause("22.2.5.1", "RegExp.escape", "regexp_escape", "js_api_integration", ["js_regexp_api_integration"], required_sources="ecma262,test262,local"),
    clause("22.2.5.1.1", "EncodeForRegExpEscape", "regexp_escape", "js_api_integration", ["js_regexp_api_integration"], required_sources="ecma262,test262,local"),
    clause("22.2.5.2", "RegExp.prototype", "constructor_properties", "js_api_integration", ["js_regexp_api_integration"]),
    clause("22.2.5.3", "get RegExp [ %Symbol.species% ]", "constructor_properties", "js_api_integration", ["js_regexp_api_integration"]),
    clause("22.2.6", "Properties of the RegExp Prototype Object", "regexp_prototype", "js_api_integration", ["js_regexp_api_integration", "regexp_exec_and_captures"]),
    clause("22.2.6.2", "RegExp.prototype.exec", "exec", "exec", ["regexp_exec_and_captures"]),
    clause("22.2.6.3", "get RegExp.prototype.dotAll", "flags", "compile_surface", ["regexp_flags"]),
    clause("22.2.6.4", "get RegExp.prototype.flags", "flags", "compile_surface", ["regexp_flags"]),
    clause("22.2.6.4.1", "RegExpHasFlag", "flags", "compile_surface", ["regexp_flags"]),
    clause("22.2.6.5", "get RegExp.prototype.global", "flags", "compile_surface", ["regexp_flags"]),
    clause("22.2.6.6", "get RegExp.prototype.hasIndices", "flags", "compile_surface", ["regexp_flags"]),
    clause("22.2.6.7", "get RegExp.prototype.ignoreCase", "flags", "compile_surface", ["regexp_flags", "regexp_unicode_semantics"]),
    clause("22.2.6.8", "RegExp.prototype [ %Symbol.match% ]", "symbol_integration", "js_api_integration", ["string_symbol_integration", "js_regexp_api_integration"]),
    clause("22.2.6.9", "RegExp.prototype [ %Symbol.matchAll% ]", "symbol_integration", "js_api_integration", ["string_symbol_integration", "js_regexp_api_integration", "regexp_string_iterator"]),
    clause("22.2.6.10", "get RegExp.prototype.multiline", "flags", "compile_surface", ["regexp_flags"]),
    clause("22.2.6.11", "RegExp.prototype [ %Symbol.replace% ]", "symbol_integration", "js_api_integration", ["string_symbol_integration", "js_regexp_api_integration", "regexp_exec_and_captures"]),
    clause("22.2.6.12", "RegExp.prototype [ %Symbol.search% ]", "symbol_integration", "js_api_integration", ["string_symbol_integration", "js_regexp_api_integration"]),
    clause("22.2.6.13", "get RegExp.prototype.source", "regexp_prototype", "js_api_integration", ["js_regexp_api_integration"]),
    clause("22.2.6.13.1", "EscapeRegExpPattern", "regexp_prototype", "compile_surface", ["regexp_pattern_syntax_positive"]),
    clause("22.2.6.14", "RegExp.prototype [ %Symbol.split% ]", "symbol_integration", "js_api_integration", ["string_symbol_integration", "js_regexp_api_integration", "regexp_exec_and_captures"]),
    clause("22.2.6.15", "get RegExp.prototype.sticky", "flags", "compile_surface", ["regexp_flags"]),
    clause("22.2.6.16", "RegExp.prototype.test", "exec", "exec", ["regexp_exec_and_captures"]),
    clause("22.2.6.17", "RegExp.prototype.toString", "regexp_prototype", "js_api_integration", ["js_regexp_api_integration"]),
    clause("22.2.6.18", "get RegExp.prototype.unicode", "flags", "compile_surface", ["regexp_flags", "regexp_unicode_semantics"]),
    clause("22.2.6.19", "get RegExp.prototype.unicodeSets", "flags", "compile_surface", ["regexp_flags", "regexp_unicode_semantics"]),
    clause("22.2.7", "Abstract Operations for RegExp Matching", "matching", "matcher", ["regexp_exec_and_captures", "regexp_unicode_semantics"]),
    clause("22.2.7.1", "RegExpExec", "matching", "exec", ["regexp_exec_and_captures", "js_regexp_api_integration"]),
    clause("22.2.7.2", "RegExpBuiltinExec", "matching", "exec", ["regexp_exec_and_captures", "regexp_flags", "regexp_unicode_semantics"]),
    clause("22.2.7.3", "AdvanceStringIndex", "unicode", "unicode", ["regexp_unicode_semantics"], required_sources="ecma262,test262,ucd,local"),
    clause("22.2.7.4", "GetStringIndex", "unicode", "unicode", ["regexp_unicode_semantics"], required_sources="ecma262,test262,ucd,local"),
    clause("22.2.7.5", "Match Records", "exec", "exec", ["regexp_exec_and_captures"]),
    clause("22.2.7.6", "GetMatchString", "exec", "exec", ["regexp_exec_and_captures"]),
    clause("22.2.7.7", "GetMatchIndexPair", "indices", "exec", ["regexp_exec_and_captures", "regexp_flags"]),
    clause("22.2.7.8", "MakeMatchIndicesIndexPairArray", "indices", "exec", ["regexp_exec_and_captures", "regexp_flags"]),
    clause("22.2.8", "Properties of RegExp Instances", "instances", "exec", ["regexp_exec_and_captures"]),
    clause("22.2.8.1", "lastIndex", "instances", "exec", ["regexp_exec_and_captures", "regexp_flags"]),
    clause("22.2.9", "RegExp String Iterator Objects", "regexp_string_iterator", "js_api_integration", ["regexp_string_iterator", "string_symbol_integration"]),
    clause("22.2.9.1", "CreateRegExpStringIterator", "regexp_string_iterator", "js_api_integration", ["regexp_string_iterator", "string_symbol_integration"]),
    clause("22.2.9.2", "%RegExpStringIteratorPrototype% Object", "regexp_string_iterator", "js_api_integration", ["regexp_string_iterator", "string_symbol_integration"]),
    clause("22.2.9.2.1", "%RegExpStringIteratorPrototype%.next", "regexp_string_iterator", "js_api_integration", ["regexp_string_iterator", "string_symbol_integration"]),
    clause("22.2.9.3", "Properties of RegExp String Iterator Instances", "regexp_string_iterator", "js_api_integration", ["regexp_string_iterator", "string_symbol_integration"]),
    clause("7.2.6", "IsRegExp", "abstract_operation", "js_api_integration", ["js_regexp_api_integration", "string_symbol_integration"], source_url=ABSTRACT_OPS_URL),
    clause("22.1.3.13", "String.prototype.match", "string_integration", "js_api_integration", ["string_symbol_integration"]),
    clause("22.1.3.14", "String.prototype.matchAll", "string_integration", "js_api_integration", ["string_symbol_integration", "regexp_string_iterator"]),
    clause("22.1.3.19", "String.prototype.replace", "string_integration", "js_api_integration", ["string_symbol_integration"]),
    clause("22.1.3.19.1", "GetSubstitution", "string_integration", "js_api_integration", ["string_symbol_integration", "regexp_exec_and_captures"]),
    clause("22.1.3.20", "String.prototype.replaceAll", "string_integration", "js_api_integration", ["string_symbol_integration"]),
    clause("22.1.3.21", "String.prototype.search", "string_integration", "js_api_integration", ["string_symbol_integration"]),
    clause("22.1.3.23", "String.prototype.split", "string_integration", "js_api_integration", ["string_symbol_integration"]),
    clause("B.1.2", "Regular Expressions Patterns", "annexB", "parser", ["regexp_pattern_syntax_positive", "regexp_syntax_negative"], source_url=ANNEXB_URL),
    clause("B.1.2.1", "Static Semantics: Early Errors", "annexB", "parser", ["regexp_syntax_negative"], source_url=ANNEXB_URL),
    clause("B.1.2.2", "CountLeftCapturingParensWithin and CountLeftCapturingParensBefore", "annexB", "parser", ["regexp_exec_and_captures"], source_url=ANNEXB_URL),
    clause("B.1.2.3", "Static Semantics: IsCharacterClass", "annexB", "parser", ["regexp_pattern_syntax_positive"], source_url=ANNEXB_URL),
    clause("B.1.2.4", "Static Semantics: CharacterValue", "annexB", "parser", ["regexp_pattern_syntax_positive"], source_url=ANNEXB_URL),
    clause("B.1.2.5", "Runtime Semantics: CompileSubpattern", "annexB", "matcher", ["regexp_exec_and_captures"], source_url=ANNEXB_URL),
    clause("B.1.2.6", "Runtime Semantics: CompileAssertion", "annexB", "matcher", ["regexp_exec_and_captures"], source_url=ANNEXB_URL),
    clause("B.1.2.7", "Runtime Semantics: CompileAtom", "annexB", "matcher", ["regexp_exec_and_captures", "regexp_pattern_syntax_positive"], source_url=ANNEXB_URL),
    clause("B.1.2.8", "Runtime Semantics: CompileToCharSet", "annexB", "matcher", ["regexp_exec_and_captures", "regexp_pattern_syntax_positive"], source_url=ANNEXB_URL),
    clause("B.1.2.8.1", "CharacterRangeOrUnion", "annexB", "matcher", ["regexp_pattern_syntax_positive"], source_url=ANNEXB_URL),
    clause("B.1.2.9", "Static Semantics: ParsePattern", "annexB", "parser", ["regexp_syntax_negative", "regexp_pattern_syntax_positive"], source_url=ANNEXB_URL),
    clause("B.2.4.1", "RegExp.prototype.compile", "annexB", "js_api_integration", ["js_regexp_api_integration"], source_url=ANNEXB_URL),
]


def status_for_clause(
    coverage_areas: set[str],
    status_counts_by_area: dict[str, Counter[str]],
) -> tuple[int, int, int, str]:
    total = 0
    connected = 0
    needs = 0
    for area in coverage_areas:
        counts = status_counts_by_area.get(area, Counter())
        area_total = sum(counts.values())
        total += area_total
        connected += counts.get("compile_cases_connected", 0)
        needs += sum(
            count for status, count in counts.items() if status.startswith("needs_")
        )
    if connected > 0 and needs > 0:
        status = "partial_executable_with_gaps"
    elif connected > 0:
        status = "partial_executable"
    elif total > 0:
        status = "inventory_only"
    else:
        status = "no_test262_mapping"
    return total, connected, needs, status


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache", default="cache")
    parser.add_argument(
        "--test262-coverage", default="cache/test262-regexp-coverage-matrix.tsv"
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    cache = Path(args.cache)
    test262_coverage = Path(args.test262_coverage)
    detail = cache / DETAIL_NAME
    summary = cache / SUMMARY_NAME

    if not test262_coverage.is_file():
        raise SystemExit(
            f"missing test262 coverage matrix at {test262_coverage}; "
            "run tools/build_test262_regexp_coverage_matrix.py"
        )

    status_counts_by_area: dict[str, Counter[str]] = {}
    for row in read_tsv_rows(test262_coverage):
        area = row["spec_area"]
        status_counts_by_area.setdefault(area, Counter())[row["coverage_status"]] += 1

    rows = []
    for row in CLAUSES:
        areas = {part for part in row["coverage_areas"].split("|") if part}
        total, connected, needs, test262_status = status_for_clause(
            areas, status_counts_by_area
        )
        required_sources = set(row["required_sources"].split(","))
        missing_sources = []
        if "ecma262" in required_sources:
            missing_sources.append("ecma262_clause_review")
        if "local" in required_sources:
            missing_sources.append("local_exact_tests")
        if "ucd" in required_sources:
            missing_sources.append("ucd_generated_tests")
        if "json-schema" in required_sources:
            missing_sources.append("json_schema_consumer_tests")
        if test262_status in {"inventory_only", "no_test262_mapping"}:
            missing_sources.append("test262_executable_tests")
        coverage_status = (
            "partial"
            if test262_status.startswith("partial_executable")
            else "not_executable"
        )
        rows.append(
            {
                **row,
                "test262_rows": str(total),
                "test262_connected_rows": str(connected),
                "test262_needs_rows": str(needs),
                "test262_status": test262_status,
                "coverage_status": coverage_status,
                "missing_sources": ",".join(missing_sources),
            }
        )

    cluster_counts = Counter(row["spec_cluster"] for row in rows)
    layer_counts = Counter(row["implementation_layer"] for row in rows)
    status_counts = Counter(row["coverage_status"] for row in rows)
    test262_status_counts = Counter(row["test262_status"] for row in rows)

    summary_lines = [
        "ecma262_snapshot\t2026\n",
        f"source_base\t{ECMA262_BASE}\n",
        f"input_test262_coverage\t{test262_coverage}\n",
        f"clause_rows\t{len(rows)}\n",
        f"planned_detail_output\t{detail}\n",
        f"planned_summary_output\t{summary}\n",
        f"dry_run\t{str(args.dry_run).lower()}\n",
    ]
    for name, count in sorted(cluster_counts.items()):
        summary_lines.append(f"cluster_{name}\t{count}\n")
    for name, count in sorted(layer_counts.items()):
        summary_lines.append(f"layer_{name}\t{count}\n")
    for name, count in sorted(status_counts.items()):
        summary_lines.append(f"coverage_status_{name}\t{count}\n")
    for name, count in sorted(test262_status_counts.items()):
        summary_lines.append(f"test262_status_{name}\t{count}\n")

    if args.dry_run:
        print("".join(summary_lines), end="")
        return

    cache.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "clause_id",
        "title",
        "source_url",
        "spec_cluster",
        "implementation_layer",
        "coverage_areas",
        "required_sources",
        "test262_rows",
        "test262_connected_rows",
        "test262_needs_rows",
        "test262_status",
        "coverage_status",
        "missing_sources",
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
