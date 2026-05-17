#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import re
import subprocess
from collections import Counter
from pathlib import Path


DETAIL_NAME = "test262-regexp-candidate-audit.tsv"
SUMMARY_NAME = "test262-regexp-candidate-audit.summary"

META_RE = re.compile(r"/\*---(?P<body>.*?)---\*/", re.S)
REGEXP_WORD_RE = re.compile(r"\bRegExp\b|RegularExpression|regular expression", re.I)
SYMBOL_PROTOCOL_RE = re.compile(r"Symbol\.(match|matchAll|replace|search|split)")
REGEXP_LITERAL_HINT_RE = re.compile(r"(^|[\s=(:,\[{!])/[^\n/*][^\n/]*/[dgimsuvy]*")


def git_revision(root: Path) -> str:
    return subprocess.check_output(
        ["git", "-C", str(root), "rev-parse", "HEAD"], text=True
    ).strip()


def metadata(text: str) -> str:
    match = META_RE.search(text)
    if not match:
        return ""
    return match.group("body")


def code_without_metadata(text: str) -> str:
    return META_RE.sub("", text, count=1)


def metadata_field(meta: str, name: str) -> str:
    match = re.search(rf"^\s*{re.escape(name)}:\s*(?P<value>.+)$", meta, re.M)
    if not match:
        return ""
    value = match.group("value").strip()
    if value.startswith("["):
        return value
    if value in {"|", ">"}:
        return ""
    return value


def path_prefix(path: str, depth: int = 3) -> str:
    return "/".join(path.split("/")[:depth])


def content_signals(path: str, code: str, meta: str) -> list[str]:
    signals: set[str] = set()
    if REGEXP_WORD_RE.search(code):
        signals.add("code_regexp_word")
    if REGEXP_WORD_RE.search(meta):
        signals.add("metadata_regexp_word")
    if SYMBOL_PROTOCOL_RE.search(code):
        signals.add("symbol_protocol")
    if REGEXP_LITERAL_HINT_RE.search(code):
        signals.add("regexp_literal_hint")
    if re.search(r"\.exec\(", code):
        signals.add("dot_exec")
    if re.search(r"\.test\(", code):
        signals.add("dot_test")
    if "regexp" in path.lower() or "reg-exp" in path.lower():
        signals.add("path_regexp_word")
    if not signals:
        signals.add("no_signal_after_metadata_split")
    return sorted(signals)


def has_runtime_regexp_signal(signals: list[str]) -> bool:
    runtime = {
        "code_regexp_word",
        "symbol_protocol",
        "regexp_literal_hint",
        "dot_exec",
        "path_regexp_word",
    }
    return bool(runtime.intersection(signals))


def classify(
    path: str, text: str, meta: str, code: str, signals: list[str]
) -> tuple[str, str, str]:
    haystack = "\n".join((path, meta, text))
    signal_set = set(signals)

    if signal_set <= {"dot_test"}:
        return (
            "weak_content_match_noise",
            "do_not_promote_regexp_corpus",
            "content match is an ordinary .test() method call, not RegExp evidence",
        )

    if path.startswith("test/language/types/string/"):
        return (
            "text_fixture_regexp_word",
            "do_not_promote_regexp_corpus",
            "large string fixture contains ECMA text mentioning regular expressions",
        )

    if path.startswith("test/language/expressions/object/method-definition/"):
        return (
            "metadata_only_regexp_reference",
            "do_not_promote_regexp_corpus",
            "metadata references grammar notation that mentions RegExp grammar",
        )

    if path == "test/harness/nativeFunctionMatcher.js":
        return (
            "consumer_assertion_usage",
            "downstream_or_helper_evidence",
            "test262 harness helper exercises a regular-expression-based matcher",
        )

    if signal_set <= {"metadata_regexp_word"}:
        return (
            "metadata_only_regexp_reference",
            "do_not_promote_regexp_corpus",
            "metadata mentions RegExp but test code has no RegExp signal",
        )

    if path.startswith("test/staging/built-ins/RegExp/"):
        return (
            "core_regexp_semantics",
            "promote_core_corpus",
            "staging built-ins RegExp tests exercise RegExp syntax/API behavior",
        )

    if path.startswith("test/staging/sm/RegExp/"):
        return (
            "core_regexp_semantics",
            "promote_core_corpus",
            "SpiderMonkey staging RegExp tests exercise RegExp behavior",
        )

    if (
        path.startswith("test/language/module-code/")
        or path.startswith("test/language/expressions/division/")
        or path.startswith("test/language/expressions/template-literal/")
        or path.startswith("test/language/expressions/yield/")
        or path.startswith("test/language/statementList/")
        or path.startswith("test/language/white-space/")
        or path.startswith("test/language/line-terminators/")
        or path.startswith("test/annexB/language/comments/")
        or "regular-expression-literal" in path.lower()
        or "regexp-literal" in path.lower()
        or "RegularExpressionLiteral" in haystack
    ):
        return (
            "regexp_literal_js_grammar",
            "scope_decision",
            "tests JavaScript source grammar around RegExp literals, not only pattern strings",
        )

    if (
        path.startswith("test/staging/sm/misc/regexp-functions-with-undefined.js")
        or path.startswith("test/staging/sm/misc/builtin-methods-reject-null-undefined-this.js")
        or path.startswith("test/staging/sm/statements/regress-642975.js")
        or path.startswith("test/staging/sm/String/")
        or path.startswith("test/built-ins/Symbol/")
        or path.startswith("test/staging/sm/Symbol/")
        or "Symbol.match" in haystack
        or "Symbol.matchAll" in haystack
        or "Symbol.replace" in haystack
        or "Symbol.search" in haystack
        or "Symbol.split" in haystack
    ):
        return (
            "js_regexp_api_integration",
            "scope_decision",
            "tests well-known Symbol protocol integration with RegExp/String behavior",
        )

    if (
        path.startswith("test/built-ins/String/prototype/endsWith/")
        or path.startswith("test/built-ins/String/prototype/includes/")
        or path.startswith("test/built-ins/String/prototype/startsWith/")
    ):
        return (
            "js_regexp_api_integration",
            "scope_decision",
            "tests String API IsRegExp/protocol behavior outside the regex engine core",
        )

    if (
        "subclass-RegExp" in path
        or "subclass/builtin-objects/RegExp" in path
        or "subclass-builtins/subclass-RegExp" in path
        or "extends RegExp" in haystack
    ):
        return (
            "js_regexp_api_integration",
            "scope_decision",
            "tests RegExp object subclassing or constructor integration",
        )

    if path.startswith("test/built-ins/global/"):
        return (
            "js_regexp_api_integration",
            "scope_decision",
            "tests global object bindings where RegExp is part of JS runtime surface",
        )

    if (
        path.startswith("test/built-ins/Date/")
        or path.startswith("test/intl402/")
        or path.startswith("test/staging/sm/expressions/constant-folded-labeled-statement.js")
    ):
        return (
            "consumer_assertion_usage",
            "downstream_or_helper_evidence",
            "uses regular expressions as assertions for another specification surface",
        )

    generic_prefixes = (
        "test/built-ins/Array/",
        "test/built-ins/Error/",
        "test/built-ins/Function/",
        "test/built-ins/Object/",
        "test/built-ins/Proxy/",
        "test/built-ins/ShadowRealm/",
        "test/built-ins/String/prototype/toLocaleLowerCase/",
        "test/built-ins/String/prototype/toLocaleUpperCase/",
        "test/built-ins/String/prototype/toLowerCase/",
        "test/built-ins/String/prototype/toUpperCase/",
        "test/built-ins/String/prototype/trim/",
        "test/built-ins/TypedArray/",
        "test/language/expressions/delete/",
        "test/language/expressions/typeof/",
        "test/language/statements/for-of/",
        "test/staging/sm/Function/",
        "test/staging/sm/Proxy/",
        "test/staging/sm/Reflect/",
        "test/staging/sm/class/extendBuiltinConstructors.js",
        "test/staging/sm/expressions/computed-property-side-effects.js",
        "test/staging/sm/expressions/destructuring-array-done.js",
        "test/staging/sm/extensions/",
        "test/staging/sm/object/",
    )
    if path.startswith(generic_prefixes) and has_runtime_regexp_signal(signals):
        return (
            "generic_regexp_object_usage",
            "downstream_or_helper_evidence",
            "uses RegExp as an ordinary JS value while testing another built-in",
        )

    if path.startswith(generic_prefixes):
        return (
            "metadata_only_regexp_reference",
            "do_not_promote_regexp_corpus",
            "generic built-in test mentions RegExp only outside executable RegExp behavior",
        )

    if path.startswith("test/language/comments/") or path.startswith(
        "test/language/literals/string/"
    ):
        return (
            "regexp_literal_js_grammar",
            "scope_decision",
            "tests JavaScript lexical grammar with regex usage as evidence",
        )

    if (
        path.startswith("test/language/literals/null/")
        or path.startswith("test/staging/sm/regress/regress-325925.js")
    ):
        return (
            "core_regexp_semantics",
            "promote_core_corpus",
            "misplaced regression test directly exercises RegExp matching behavior",
        )

    if path.startswith("test/staging/sm/"):
        return (
            "manual_review",
            "manual_audit",
            "SpiderMonkey staging candidate outside known RegExp/String/Symbol roots",
        )

    return (
        "manual_review",
        "manual_audit",
        "content matched RegExp patterns outside known inventory routes",
    )


def read_candidates(inventory: Path) -> list[dict[str, str]]:
    with inventory.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    return [row for row in rows if row["bucket"] == "candidate"]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--test262", default="external/test262")
    parser.add_argument("--cache", default="cache")
    parser.add_argument(
        "--inventory", default="cache/test262-regexp-inventory.tsv"
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    test262 = Path(args.test262)
    inventory = Path(args.inventory)
    cache = Path(args.cache)
    detail = cache / DETAIL_NAME
    summary = cache / SUMMARY_NAME

    if not test262.is_dir():
        raise SystemExit(f"missing test262 checkout at {test262}")
    if not inventory.is_file():
        raise SystemExit(
            f"missing inventory at {inventory}; run tools/inventory_test262_regexp.py"
        )

    rows = []
    for row in read_candidates(inventory):
        path = row["path"]
        full_path = test262 / path
        text = full_path.read_text(encoding="utf-8", errors="replace")
        meta = metadata(text)
        code = code_without_metadata(text)
        signals = content_signals(path, code, meta)
        candidate_class, action, reason = classify(path, text, meta, code, signals)
        rows.append(
            {
                "path": path,
                "candidate_class": candidate_class,
                "action": action,
                "reason": reason,
                "content_signals": ",".join(signals),
                "path_prefix_3": path_prefix(path, 3),
                "path_prefix_4": path_prefix(path, 4),
                "inventory_features": row["features"],
                "metadata_esid": metadata_field(meta, "esid"),
                "metadata_features": metadata_field(meta, "features"),
            }
        )

    class_counts = Counter(row["candidate_class"] for row in rows)
    action_counts = Counter(row["action"] for row in rows)
    signal_counts: Counter[str] = Counter()
    for row in rows:
        for signal in row["content_signals"].split(","):
            signal_counts[signal] += 1
    prefix3_counts = Counter(row["path_prefix_3"] for row in rows)
    prefix4_counts = Counter(row["path_prefix_4"] for row in rows)

    summary_lines = [
        f"revision\t{git_revision(test262)}\n",
        f"input_inventory\t{inventory}\n",
        f"candidate_rows\t{len(rows)}\n",
        f"planned_detail_output\t{detail}\n",
        f"planned_summary_output\t{summary}\n",
        f"dry_run\t{str(args.dry_run).lower()}\n",
    ]
    for name, count in sorted(class_counts.items()):
        summary_lines.append(f"class_{name}\t{count}\n")
    for name, count in sorted(action_counts.items()):
        summary_lines.append(f"action_{name}\t{count}\n")
    for name, count in sorted(signal_counts.items()):
        summary_lines.append(f"signal_{name}\t{count}\n")
    for name, count in prefix3_counts.most_common(40):
        summary_lines.append(f"prefix3_{name}\t{count}\n")
    for name, count in prefix4_counts.most_common(40):
        summary_lines.append(f"prefix4_{name}\t{count}\n")

    if args.dry_run:
        print("".join(summary_lines), end="")
        return

    cache.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "path",
        "candidate_class",
        "action",
        "reason",
        "content_signals",
        "path_prefix_3",
        "path_prefix_4",
        "inventory_features",
        "metadata_esid",
        "metadata_features",
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
