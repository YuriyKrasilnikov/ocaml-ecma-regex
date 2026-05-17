from __future__ import annotations

import csv
import re
from collections.abc import Callable, Iterable
from pathlib import Path


def read_tsv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        if reader.fieldnames is None:
            raise SystemExit(f"missing header in {path}")
        return reader.fieldnames, list(reader)


def read_tsv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def read_summary(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}

    data: dict[str, str] = {}
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line or "\t" not in line:
                continue
            key, value = line.split("\t", 1)
            data[key] = value
    return data


def split_csv(value: str) -> list[str]:
    return [part for part in value.split(",") if part]


def split_csv_set(value: str) -> set[str]:
    return set(split_csv(value))


def suffix_number(requirement_id: str) -> int:
    try:
        return int(requirement_id.rsplit("-", 1)[1])
    except ValueError as exc:
        raise SystemExit(f"invalid ECMA requirement id: {requirement_id}") from exc


def copy_requirement_metadata(
    row: dict[str, str],
    *,
    include_local_id: bool,
) -> dict[str, str]:
    result = {
        "requirement_id": row["requirement_id"],
        "clause_id": row["clause_id"],
        "clause_title": row["clause_title"],
        "source_file": row["source_file"],
        "section_anchor": row["section_anchor"],
        "requirement_kind": row["requirement_kind"],
    }
    if include_local_id:
        result["requirement_local_id"] = row["requirement_local_id"]
    result["requirement_text"] = row["requirement_text"]
    return result


def validate_expected_fields(
    row: dict[str, str],
    expected: dict[str, str],
    *,
    context: str,
) -> None:
    requirement_id = row["requirement_id"]
    for field, expected_value in expected.items():
        if row[field] != expected_value:
            raise SystemExit(
                f"{context} {requirement_id} has {field}={row[field]!r}; "
                f"expected {expected_value!r}"
            )


def require_coverage_area(
    row: dict[str, str],
    area: str,
    *,
    context: str,
) -> None:
    requirement_id = row["requirement_id"]
    if area not in row["coverage_areas"].split("|"):
        raise SystemExit(f"{context} {requirement_id} lacks {area} coverage area")


def rows_by_requirement_id(
    rows: list[dict[str, str]],
) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    for row in rows:
        requirement_id = row["requirement_id"]
        if requirement_id in result:
            raise SystemExit(f"duplicate requirement row for {requirement_id}")
        result[requirement_id] = row
    return result


def select_exact_case_requirement_rows(
    rows: list[dict[str, str]],
    exact_cases: dict[str, object],
    missing_prefix: str = "exact case definitions absent from requirement mapping",
) -> list[dict[str, str]]:
    exact_case_ids = set(exact_cases)
    rows_by_id: dict[str, dict[str, str]] = {}
    for row in rows:
        requirement_id = row["requirement_id"]
        if requirement_id not in exact_case_ids:
            continue
        if requirement_id in rows_by_id:
            raise SystemExit(f"duplicate requirement row for {requirement_id}")
        rows_by_id[requirement_id] = row

    missing_case_ids = sorted(exact_case_ids.difference(rows_by_id))
    if missing_case_ids:
        raise SystemExit(
            f"{missing_prefix}: " + ", ".join(missing_case_ids[:10])
        )

    return [rows_by_id[requirement_id] for requirement_id in exact_cases]


def select_expected_source_rows(
    rows: list[dict[str, str]],
    *,
    include_row: Callable[[dict[str, str]], bool],
    expected_ids: Iterable[str],
    validate_row: Callable[[dict[str, str]], None],
    duplicate_message: Callable[[str], str],
    missing_prefix: str,
    extra_prefix: str,
) -> list[dict[str, str]]:
    selected: dict[str, dict[str, str]] = {}
    for row in rows:
        if not include_row(row):
            continue
        requirement_id = row["requirement_id"]
        if requirement_id in selected:
            raise SystemExit(duplicate_message(requirement_id))
        validate_row(row)
        selected[requirement_id] = row

    expected_id_set = set(expected_ids)
    missing = sorted(expected_id_set.difference(selected))
    extra = sorted(set(selected).difference(expected_id_set))
    if missing:
        raise SystemExit(missing_prefix + ", ".join(missing[:10]))
    if extra:
        raise SystemExit(extra_prefix + ", ".join(extra[:10]))

    return [selected[requirement_id] for requirement_id in sorted(expected_id_set)]


def select_worklist_rows(
    rows: list[dict[str, str]],
    *,
    include_row: Callable[[dict[str, str]], bool],
    sort_key: Callable[[dict[str, str]], object],
    expected_count: int,
    count_message: Callable[[int], str],
) -> list[dict[str, str]]:
    selected = [row for row in rows if include_row(row)]
    selected.sort(key=sort_key)
    if len(selected) != expected_count:
        raise SystemExit(count_message(len(selected)))
    return selected


def select_requirement_rows(
    rows: list[dict[str, str]],
    *,
    include_row: Callable[[dict[str, str]], bool],
    expected_count: int,
    count_message: Callable[[int], str],
    sort_key: Callable[[dict[str, str]], object] | None = None,
) -> list[dict[str, str]]:
    selected = [row for row in rows if include_row(row)]
    if sort_key is not None:
        selected.sort(key=sort_key)
    if len(selected) != expected_count:
        raise SystemExit(count_message(len(selected)))
    return selected


def write_tsv(
    path: Path,
    fieldnames: list[str],
    rows: list[dict[str, str]],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames,
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def bool_text(value: bool) -> str:
    return "true" if value else "false"


def safe_id(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "-", value).strip("-").lower()


def require_columns(path: Path, fields: list[str], required: set[str]) -> None:
    missing = required.difference(fields)
    if missing:
        raise SystemExit(
            f"missing required columns in {path}: {', '.join(sorted(missing))}"
        )


def validate_unique_ids(
    rows: list[dict[str, str]],
    fields: tuple[str, ...] = ("plan_id", "exact_case_id"),
    allow_empty: set[str] | None = None,
    field_label_prefix: str = "",
) -> None:
    allow_empty = set() if allow_empty is None else allow_empty
    seen_by_field: dict[str, set[str]] = {field: set() for field in fields}
    for row in rows:
        for field in fields:
            value = row[field]
            if field in allow_empty and not value:
                continue
            seen = seen_by_field[field]
            if value in seen:
                raise SystemExit(f"duplicate {field_label_prefix}{field} {value}")
            seen.add(value)
