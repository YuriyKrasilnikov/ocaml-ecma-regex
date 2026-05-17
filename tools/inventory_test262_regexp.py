#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
from collections import Counter
from pathlib import Path


PRIMARY_PREFIXES = (
    "test/built-ins/RegExp/",
    "test/built-ins/RegExpStringIteratorPrototype/",
    "test/language/literals/regexp/",
    "test/language/statements/class/subclass/builtin-objects/RegExp/",
    "test/annexB/built-ins/RegExp/",
    "test/annexB/language/literals/regexp/",
)

SECONDARY_PREFIXES = (
    "test/built-ins/String/prototype/match/",
    "test/built-ins/String/prototype/matchAll/",
    "test/built-ins/String/prototype/replace/",
    "test/built-ins/String/prototype/replaceAll/",
    "test/built-ins/String/prototype/search/",
    "test/built-ins/String/prototype/split/",
    "test/annexB/built-ins/String/prototype/match/",
    "test/annexB/built-ins/String/prototype/matchAll/",
    "test/annexB/built-ins/String/prototype/replace/",
    "test/annexB/built-ins/String/prototype/replaceAll/",
    "test/annexB/built-ins/String/prototype/search/",
    "test/annexB/built-ins/String/prototype/split/",
)

CONTENT_RE = re.compile(
    r"RegExp|regexp|RegularExpression|regular expression|"
    r"Symbol\.(match|matchAll|replace|search|split)|"
    r"\.exec\(|\.test\("
)

FEATURE_PATTERNS = [
    ("syntax_errors", re.compile(r"syntax|early-err|invalid|duplicate-flags|SyntaxError|negative:|Early Error", re.I)),
    ("flags", re.compile(r"flags|dotAll|ignoreCase|multiline|global|sticky|unicode|unicodeSets|hasIndices", re.I)),
    ("dotAll", re.compile(r"dotall", re.I)),
    ("ignoreCase", re.compile(r"ignorecase|ignore case", re.I)),
    ("multiline", re.compile(r"multiline", re.I)),
    ("global", re.compile(r"global", re.I)),
    ("sticky", re.compile(r"sticky", re.I)),
    ("hasIndices", re.compile(r"hasindices|match-indices|indices", re.I)),
    ("unicode", re.compile(r"unicode|surrogate|astral|non-bmp|code point|codepoint", re.I)),
    ("unicodeSets", re.compile(r"unicodesets|unicode sets|/v", re.I)),
    ("property_escapes", re.compile(r"property-escapes|\\p\{|\\P\{|Unicode property|property escape", re.I)),
    ("literal_regexp", re.compile(r"language/literals/regexp|RegularExpression", re.I)),
    ("captures", re.compile(r"capture|capturing|Capture", re.I)),
    ("named_captures", re.compile(r"named-groups|named capture|NamedCapture|groups|groupName|<[^>]+>", re.I)),
    ("backreferences", re.compile(r"backreference|Backreference|\\\\[1-9]|\\\\k<", re.I)),
    ("lookahead", re.compile(r"lookahead|Lookahead", re.I)),
    ("lookbehind", re.compile(r"lookbehind|Lookbehind", re.I)),
    ("character_classes", re.compile(r"CharacterClass|character class|character-class|\[[^\]]*\]", re.I)),
    ("character_class_escapes", re.compile(r"CharacterClassEscapes|\\\\d|\\\\D|\\\\w|\\\\W|\\\\s|\\\\S", re.I)),
    ("quantifiers", re.compile(r"quantifier|Quantifier|\*|\+|\{|\?", re.I)),
    ("alternation", re.compile(r"Disjunction|disjunction|alternation|\|", re.I)),
    ("assertions", re.compile(r"Assertion|assertion|\\\^|\\\$|\\\\b|\\\\B", re.I)),
    ("exec", re.compile(r"/exec/|\.exec\(|RegExp.prototype.exec", re.I)),
    ("test_method", re.compile(r"prototype/test|\.test\(|RegExp.prototype.test", re.I)),
    ("lastIndex", re.compile(r"lastIndex", re.I)),
    ("symbol_matchAll", re.compile(r"Symbol\.matchAll|Symbol.matchAll", re.I)),
    ("symbol_match", re.compile(r"Symbol\.match|Symbol.match", re.I)),
    ("symbol_replace", re.compile(r"Symbol\.replace|Symbol.replace", re.I)),
    ("symbol_search", re.compile(r"Symbol\.search|Symbol.search", re.I)),
    ("symbol_split", re.compile(r"Symbol\.split|Symbol.split", re.I)),
    ("string_match", re.compile(r"String/prototype/match", re.I)),
    ("string_replace", re.compile(r"String/prototype/replace", re.I)),
    ("string_search", re.compile(r"String/prototype/search", re.I)),
    ("string_split", re.compile(r"String/prototype/split", re.I)),
    ("regexp_string_iterator", re.compile(r"RegExpStringIteratorPrototype", re.I)),
    ("subclassing", re.compile(r"subclass/builtin-objects/RegExp", re.I)),
    ("annexB", re.compile(r"annexB", re.I)),
]

META_RE = re.compile(r"/\*---(?P<body>.*?)---\*/", re.S)


def git_revision(root: Path) -> str:
    return subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()


def rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def bucket_for(relative: str) -> str:
    if relative.startswith(PRIMARY_PREFIXES):
        return "primary"
    if relative.startswith(SECONDARY_PREFIXES):
        return "secondary"
    return "candidate"


def path_candidate(relative: str) -> bool:
    return relative.startswith(PRIMARY_PREFIXES) or relative.startswith(SECONDARY_PREFIXES)


def metadata(text: str) -> str:
    match = META_RE.search(text)
    if not match:
        return ""
    return match.group("body")


def flags_from_meta(meta: str) -> str:
    match = re.search(r"^\s*flags:\s*\[(?P<flags>[^\]]*)\]", meta, re.M)
    if not match:
        return ""
    return ",".join(part.strip() for part in match.group("flags").split(",") if part.strip())


def features_for(relative: str, text: str, meta: str) -> list[str]:
    haystack = "\n".join((relative, meta, text))
    features: set[str] = set()
    for name, pattern in FEATURE_PATTERNS:
        if pattern.search(haystack):
            features.add(name)
    if not features:
        features.add("unclassified")
    return sorted(features)


def source_for(relative: str, content_match: bool) -> str:
    parts = []
    if path_candidate(relative):
        parts.append("path")
    if content_match:
        parts.append("content")
    return ",".join(parts)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--test262", default="external/test262")
    parser.add_argument("--cache", default="cache")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    root = Path(args.test262)
    test_root = root / "test"
    if not test_root.is_dir():
        raise SystemExit(f"missing test262 checkout at {root}; run tools/fetch_test262.py")

    cache = Path(args.cache)
    detail = cache / "test262-regexp-inventory.tsv"
    summary = cache / "test262-regexp-inventory.summary"

    all_js_count = sum(1 for _ in test_root.rglob("*.js"))
    candidate_paths: set[Path] = set()
    for prefix in PRIMARY_PREFIXES + SECONDARY_PREFIXES:
        directory = root / prefix
        if directory.is_dir():
            candidate_paths.update(directory.rglob("*.js"))

    if shutil.which("rg"):
        rg = subprocess.run(
            [
                "rg",
                "-l",
                "-e", "RegExp",
                "-e", "regexp",
                "-e", "RegularExpression",
                "-e", "regular expression",
                "-e", r"Symbol\.(match|matchAll|replace|search|split)",
                "-e", r"\.exec\(",
                "-e", r"\.test\(",
                str(test_root),
            ],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        candidate_paths.update(Path(line) for line in rg.stdout.splitlines() if line)
    else:
        for path in test_root.rglob("*.js"):
            text = path.read_text(encoding="utf-8", errors="replace")
            if CONTENT_RE.search(text):
                candidate_paths.add(path)

    all_candidates = sorted(candidate_paths)
    rows = []
    for path in all_candidates:
        relative = rel(path, root)
        text = path.read_text(encoding="utf-8", errors="replace")
        content_match = bool(CONTENT_RE.search(text))
        meta = metadata(text)
        rows.append(
            {
                "path": relative,
                "bucket": bucket_for(relative),
                "features": ",".join(features_for(relative, text, meta)),
                "source": source_for(relative, content_match),
                "flags": flags_from_meta(meta),
            }
        )

    bucket_counts = Counter(row["bucket"] for row in rows)
    feature_counts: Counter[str] = Counter()
    source_counts = Counter(row["source"] for row in rows)
    for row in rows:
        for feature in row["features"].split(","):
            feature_counts[feature] += 1

    revision = git_revision(root)
    summary_lines = []
    summary_lines.append(f"revision\t{revision}\n")
    summary_lines.append(f"total_js_files\t{all_js_count}\n")
    summary_lines.append(f"regexp_candidate_files\t{len(rows)}\n")
    summary_lines.append(f"planned_detail_output\t{detail}\n")
    summary_lines.append(f"planned_summary_output\t{summary}\n")
    summary_lines.append(f"dry_run\t{str(args.dry_run).lower()}\n")
    for name, count in sorted(bucket_counts.items()):
        summary_lines.append(f"bucket_{name}\t{count}\n")
    for name, count in sorted(source_counts.items()):
        summary_lines.append(f"source_{name}\t{count}\n")
    for name, count in sorted(feature_counts.items()):
        summary_lines.append(f"family_{name}\t{count}\n")

    if args.dry_run:
        print("".join(summary_lines), end="")
        return

    cache.mkdir(parents=True, exist_ok=True)
    with detail.open("w", encoding="utf-8") as f:
        f.write("path\tbucket\tfeatures\tsource\tflags\n")
        for row in rows:
            f.write(
                f"{row['path']}\t{row['bucket']}\t{row['features']}\t"
                f"{row['source']}\t{row['flags']}\n"
            )

    with summary.open("w", encoding="utf-8") as f:
        f.write("".join(summary_lines))

    print(summary.read_text(encoding="utf-8"), end="")


if __name__ == "__main__":
    main()
