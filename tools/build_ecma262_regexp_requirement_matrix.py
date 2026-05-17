#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import html
import re
from collections import Counter
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

from ecma262_tooling import read_tsv_rows


DETAIL_NAME = "ecma262-regexp-requirement-matrix.tsv"
SUMMARY_NAME = "ecma262-regexp-requirement-matrix.summary"


TAG_RE = re.compile(r"</?emu-(?:clause|annex)\b[^>]*>", re.IGNORECASE)
ATTR_RE = re.compile(r"""([A-Za-z_:][-A-Za-z0-9_:]*)\s*=\s*(['"])(.*?)\2""")
H1_RE = re.compile(r"<h1\b[^>]*>(.*?)</h1>", re.IGNORECASE | re.DOTALL)
SECNUM_RE = re.compile(
    r"""<span\b[^>]*class\s*=\s*['"]secnum['"][^>]*>(.*?)</span>""",
    re.IGNORECASE | re.DOTALL,
)
NOTE_RE = re.compile(r"<emu-note\b.*?</emu-note>", re.IGNORECASE | re.DOTALL)
EXAMPLE_RE = re.compile(r"<emu-example\b.*?</emu-example>", re.IGNORECASE | re.DOTALL)
SCRIPT_STYLE_RE = re.compile(
    r"<(?:script|style)\b.*?</(?:script|style)>", re.IGNORECASE | re.DOTALL
)


@dataclass
class Section:
    kind: str
    attrs: dict[str, str]
    start: int
    open_end: int
    end: int = 0
    close_start: int = 0
    parent: int | None = None
    children: list[int] = field(default_factory=list)
    clause_id: str = ""
    title: str = ""
    raw: str = ""
    direct_raw: str = ""


def attrs_from_tag(tag: str) -> dict[str, str]:
    return {name: value for name, _, value in ATTR_RE.findall(tag)}


def text_from_html(raw: str) -> str:
    raw = SCRIPT_STYLE_RE.sub(" ", raw)
    raw = re.sub(r"<[^>]+>", " ", raw)
    raw = html.unescape(raw)
    raw = raw.replace("\xa0", " ")
    return " ".join(raw.split())


def title_from_h1(raw: str) -> tuple[str, str]:
    match = H1_RE.search(raw)
    if not match:
        return "", ""
    h1 = match.group(1)
    secnum_match = SECNUM_RE.search(h1)
    secnum = text_from_html(secnum_match.group(1)) if secnum_match else ""
    title = text_from_html(SECNUM_RE.sub(" ", h1))
    return secnum, title


def parse_sections(source: str) -> list[Section]:
    sections: list[Section] = []
    stack: list[int] = []
    for match in TAG_RE.finditer(source):
        tag = match.group(0)
        closing = tag.startswith("</")
        kind = "annex" if "emu-annex" in tag.lower() else "clause"
        if not closing:
            parent = stack[-1] if stack else None
            section = Section(
                kind=kind,
                attrs=attrs_from_tag(tag),
                start=match.start(),
                open_end=match.end(),
                parent=parent,
            )
            sections.append(section)
            index = len(sections) - 1
            if parent is not None:
                sections[parent].children.append(index)
            stack.append(index)
        else:
            if not stack:
                continue
            index = stack.pop()
            section = sections[index]
            section.close_start = match.start()
            section.end = match.end()

    for section in sections:
        if section.end == 0:
            continue
        section.raw = source[section.start : section.end]
        secnum, title = title_from_h1(section.raw)
        section.clause_id = secnum
        section.title = title
        body = source[section.open_end : section.close_start]
        ranges = [
            (
                sections[child].start - section.open_end,
                sections[child].end - section.open_end,
            )
            for child in section.children
            if sections[child].end
        ]
        direct_parts = []
        offset = 0
        for start, end in sorted(ranges):
            if offset < start:
                direct_parts.append(body[offset:start])
            offset = max(offset, end)
        direct_parts.append(body[offset:])
        section.direct_raw = "".join(direct_parts)
    return sections


class AlgorithmParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ol_counts: list[int] = []
        self.items: list[dict[str, object]] = []
        self.finished: list[tuple[int, str, str]] = []
        self.item_order = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "ol":
            self.ol_counts.append(0)
        elif tag == "li":
            if not self.ol_counts:
                self.ol_counts.append(0)
            self.ol_counts[-1] += 1
            path = ".".join(str(part) for part in self.ol_counts)
            self.item_order += 1
            self.items.append({"order": self.item_order, "path": path, "parts": []})

    def handle_endtag(self, tag: str) -> None:
        if tag == "li" and self.items:
            item = self.items.pop()
            text = " ".join("".join(item["parts"]).split())
            if text:
                self.finished.append((int(item["order"]), str(item["path"]), text))
        elif tag == "ol" and self.ol_counts:
            self.ol_counts.pop()

    def handle_data(self, data: str) -> None:
        if self.items:
            self.items[-1]["parts"].append(data)


class TableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.in_caption = False
        self.in_cell = False
        self.caption_parts: list[str] = []
        self.cell_parts: list[str] = []
        self.current_row: list[str] = []
        self.rows: list[list[str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "figcaption":
            self.in_caption = True
        elif tag == "tr":
            self.current_row = []
        elif tag in {"td", "th"}:
            self.in_cell = True
            self.cell_parts = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "figcaption":
            self.in_caption = False
        elif tag in {"td", "th"} and self.in_cell:
            text = " ".join("".join(self.cell_parts).split())
            self.current_row.append(text)
            self.in_cell = False
        elif tag == "tr" and self.current_row:
            self.rows.append(self.current_row)

    def handle_data(self, data: str) -> None:
        if self.in_caption:
            self.caption_parts.append(data)
        if self.in_cell:
            self.cell_parts.append(data)


def html_blocks(raw: str, tag: str) -> list[str]:
    return re.findall(
        rf"<{tag}\b[^>]*>.*?</{tag}>",
        raw,
        flags=re.IGNORECASE | re.DOTALL,
    )


def blank_matches(raw: str, pattern: re.Pattern[str]) -> str:
    return pattern.sub(lambda match: " " * (match.end() - match.start()), raw)


def direct_requirement_blocks(raw: str) -> list[tuple[str, str, str]]:
    raw = blank_matches(raw, NOTE_RE)
    raw = blank_matches(raw, EXAMPLE_RE)
    blocks: list[tuple[int, int, str, str, str]] = []
    protected_ranges: list[tuple[int, int]] = []

    for production_match in re.finditer(
        r"<emu-production\b[^>]*>.*?</emu-production>",
        raw,
        flags=re.IGNORECASE | re.DOTALL,
    ):
        production = production_match.group(0)
        protected_ranges.append((production_match.start(), production_match.end()))
        name_match = re.search(r"\bname=(['\"])(.*?)\1", production)
        production_name = name_match.group(2) if name_match else "production"
        rhs_blocks = list(
            re.finditer(
                r"<emu-rhs\b[^>]*>.*?</emu-rhs>",
                production,
                flags=re.IGNORECASE | re.DOTALL,
            )
        )
        if rhs_blocks:
            for index, rhs_match in enumerate(rhs_blocks, start=1):
                rhs = rhs_match.group(0)
                rhs_id_match = re.search(r"\bid=(['\"])(.*?)\1", rhs)
                rhs_id = rhs_id_match.group(2) if rhs_id_match else str(index)
                blocks.append(
                    (
                        production_match.start() + rhs_match.start(),
                        index,
                        "grammar_rhs",
                        f"{production_name}:{rhs_id}",
                        f"{production_name} :: {text_from_html(rhs)}",
                    )
                )
        else:
            blocks.append(
                (
                    production_match.start(),
                    0,
                    "grammar_production",
                    production_name,
                    text_from_html(production),
                )
            )

    for alg_index, alg_match in enumerate(
        re.finditer(
            r"<emu-alg\b[^>]*>.*?</emu-alg>",
            raw,
            flags=re.IGNORECASE | re.DOTALL,
        ),
        start=1,
    ):
        alg = alg_match.group(0)
        protected_ranges.append((alg_match.start(), alg_match.end()))
        parser = AlgorithmParser()
        parser.feed(alg)
        for order, path, text in sorted(parser.finished):
            blocks.append(
                (
                    alg_match.start(),
                    order,
                    "algorithm_step",
                    f"{alg_index}.{path}",
                    text,
                )
            )

    for table_index, table_match in enumerate(
        re.finditer(
            r"<emu-table\b[^>]*>.*?</emu-table>",
            raw,
            flags=re.IGNORECASE | re.DOTALL,
        ),
        start=1,
    ):
        table = table_match.group(0)
        protected_ranges.append((table_match.start(), table_match.end()))
        parser = TableParser()
        parser.feed(table)
        caption = " ".join("".join(parser.caption_parts).split())
        for row_index, row in enumerate(parser.rows, start=1):
            blocks.append(
                (
                    table_match.start(),
                    row_index,
                    "table_row",
                    f"{table_index}.{row_index}",
                    f"{caption}: {' | '.join(row)}",
                )
            )

    def is_protected(position: int) -> bool:
        return any(start <= position < end for start, end in protected_ranges)

    prose_index = 0
    for paragraph_match in re.finditer(
        r"<p\b[^>]*>.*?</p>",
        raw,
        flags=re.IGNORECASE | re.DOTALL,
    ):
        if is_protected(paragraph_match.start()):
            continue
        prose_index += 1
        paragraph = paragraph_match.group(0)
        text = text_from_html(paragraph)
        if text:
            blocks.append((paragraph_match.start(), prose_index, "prose", str(prose_index), text))

    return [(kind, local_id, text) for _, _, kind, local_id, text in sorted(blocks)]


def source_file_for_url(snapshot: Path, url: str) -> Path:
    name = Path(urlparse(url).path).name
    return snapshot / name


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache", default="cache")
    parser.add_argument(
        "--clause-matrix", default="cache/ecma262-regexp-clause-matrix.tsv"
    )
    parser.add_argument("--snapshot", default="external/ecma262/2026/multipage")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    cache = Path(args.cache)
    clause_matrix = Path(args.clause_matrix)
    snapshot = Path(args.snapshot)
    detail = cache / DETAIL_NAME
    summary = cache / SUMMARY_NAME

    if not clause_matrix.is_file():
        raise SystemExit(
            f"missing ECMA-262 clause matrix at {clause_matrix}; "
            "run tools/build_ecma262_regexp_clause_matrix.py first"
        )
    if not snapshot.is_dir():
        raise SystemExit(
            f"missing ECMA-262 snapshot at {snapshot}; "
            "run tools/fetch_ecma262_sources.py first"
        )

    clause_rows = read_tsv_rows(clause_matrix)
    sections_by_source: dict[Path, dict[str, Section]] = {}
    source_hashes: dict[Path, str] = {}
    missing_sources: list[str] = []
    for clause_row in clause_rows:
        source_file = source_file_for_url(snapshot, clause_row["source_url"])
        if source_file in sections_by_source:
            continue
        if not source_file.is_file():
            missing_sources.append(str(source_file))
            continue
        source_hashes[source_file] = sha256_file(source_file)
        source_text = source_file.read_text(encoding="utf-8")
        sections = parse_sections(source_text)
        sections_by_source[source_file] = {
            section.clause_id: section
            for section in sections
            if section.clause_id
        }

    rows: list[dict[str, str]] = []
    missing_clauses: list[str] = []
    clauses_with_zero_blocks = 0
    zero_block_clauses: list[str] = []
    for clause_row in clause_rows:
        source_file = source_file_for_url(snapshot, clause_row["source_url"])
        section = sections_by_source.get(source_file, {}).get(clause_row["clause_id"])
        if section is None:
            missing_clauses.append(clause_row["clause_id"])
            continue
        blocks = direct_requirement_blocks(section.direct_raw)
        if not blocks:
            clauses_with_zero_blocks += 1
            zero_block_clauses.append(clause_row["clause_id"])
            blocks = [
                (
                    "section_marker",
                    "0",
                    "Clause has no direct extracted normative blocks; child clauses or manual review must carry requirements.",
                )
            ]
        for index, (kind, local_id, text) in enumerate(blocks, start=1):
            requirement_id = f"ecma262-{clause_row['clause_id']}-{index:04d}"
            rows.append(
                {
                    "requirement_id": requirement_id,
                    "clause_id": clause_row["clause_id"],
                    "clause_title": clause_row["title"],
                    "source_url": clause_row["source_url"],
                    "source_file": str(source_file),
                    "source_sha256": source_hashes.get(source_file, ""),
                    "section_anchor": section.attrs.get("id", ""),
                    "requirement_kind": kind,
                    "requirement_local_id": local_id,
                    "requirement_text": text,
                    "spec_cluster": clause_row["spec_cluster"],
                    "implementation_layer": clause_row["implementation_layer"],
                    "coverage_areas": clause_row["coverage_areas"],
                    "required_sources": clause_row["required_sources"],
                    "test262_status": clause_row["test262_status"],
                    "clause_coverage_status": clause_row["coverage_status"],
                    "requirement_test_status": "not_mapped",
                    "missing_sources": clause_row["missing_sources"],
                }
            )

    kind_counts = Counter(row["requirement_kind"] for row in rows)
    layer_counts = Counter(row["implementation_layer"] for row in rows)
    test262_counts = Counter(row["test262_status"] for row in rows)
    clause_coverage_counts = Counter(row["clause_coverage_status"] for row in rows)

    summary_lines = [
        "ecma262_snapshot\t2026\n",
        f"input_clause_matrix\t{clause_matrix}\n",
        f"snapshot_dir\t{snapshot}\n",
        f"source_files\t{len(sections_by_source)}\n",
        f"clause_rows\t{len(clause_rows)}\n",
        f"clauses_found\t{len(clause_rows) - len(missing_clauses)}\n",
        f"clauses_missing\t{len(missing_clauses)}\n",
        f"clauses_with_zero_blocks\t{clauses_with_zero_blocks}\n",
        f"requirement_rows\t{len(rows)}\n",
        f"planned_detail_output\t{detail}\n",
        f"planned_summary_output\t{summary}\n",
        f"dry_run\t{str(args.dry_run).lower()}\n",
    ]
    for name, count in sorted(kind_counts.items()):
        summary_lines.append(f"kind_{name}\t{count}\n")
    for name, count in sorted(layer_counts.items()):
        summary_lines.append(f"layer_{name}\t{count}\n")
    for name, count in sorted(test262_counts.items()):
        summary_lines.append(f"test262_status_{name}\t{count}\n")
    for name, count in sorted(clause_coverage_counts.items()):
        summary_lines.append(f"clause_coverage_status_{name}\t{count}\n")
    for missing in missing_sources:
        summary_lines.append(f"missing_source\t{missing}\n")
    for missing in missing_clauses:
        summary_lines.append(f"missing_clause\t{missing}\n")
    for clause_id in zero_block_clauses:
        summary_lines.append(f"zero_block_clause\t{clause_id}\n")

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
