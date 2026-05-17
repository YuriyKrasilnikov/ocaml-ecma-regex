# Test Evidence Audit

This document summarizes what the committed tests and evidence runners prove
for `ecma-regex`.

It is downstream of:

- [`NORMATIVE_HIERARCHY.md`](NORMATIVE_HIERARCHY.md)
- [`SPEC_CONFORMANCE.md`](SPEC_CONFORMANCE.md)
- [`NORMATIVE_TEST_MATRIX.md`](NORMATIVE_TEST_MATRIX.md)

The test matrix maps requirement families to evidence. This audit explains the
evidence layers, their default-vs-explicit role, and the remaining
quality-hardening work that must not be mistaken for credited conformance.

## Test Runner Tiers

The package-safe default test gate is:

```text
opam exec -- dune runtest
```

It is intentionally self-contained so opam `--with-test` can run from a clean
source archive without `cache/` or `external/` working artifacts. That suite
includes:

- public API smoke and contract tests;
- raw UTF-16 escape matrix tests;
- raw UTF-16 negative-position tests;
- raw UTF-16 result-slicing tests.

The full local evidence gate is:

```text
opam exec -- dune build @runtest @test/evidence
```

It additionally runs ECMA-262 exact-plan tests, matcher and adapter evidence
tests, generated UCD 16.0.0 tests, JSON Schema regex-facing corpus tests,
test262-derived executable corpus tests, and coverage ledger/worklist invariant
tests. This gate requires prepared `cache/` outputs and downloaded `external/`
corpora and is therefore not part of opam package `@runtest`.

Default `dune runtest` is the installable package health gate. It is not, by
itself, the whole conformance argument; the conformance argument also depends
on the explicit evidence gate and generated ledger/corpus evidence described
below.

## Explicit Evidence Runners

These runners are evidence generators or evidence checkers. They are separate
from ordinary unit-test intent because they construct or verify requirement
coverage data.

| Evidence runner | Role | Credited result |
|---|---|---|
| `tools/build_ecma262_regexp_coverage_ledger.py --dry-run --fail-on-open` | top-level ECMA-262 RegExp requirement ledger gate | `coverage_complete=true`, `release_blocking_open_rows=0` |
| `test/test_ecma262_coverage_ledger.ml` | checks committed test view of ledger invariants | coverage ledger invariants green |
| `test/test_ecma262_requirement_test_worklist.ml` | checks no remaining requirement-to-test worklist pressure | `worklist_rows=0`, `open_mapping_rows=0` |
| `test/test_ecma262_selector_gap_worklist.ml` | checks no selector gap backlog remains | selector gap rows are zero |
| `test/test_ecma262_exactness_audit.ml` | checks exactness credit and open exactness classification | `coverage_credit_rows=1144` |
| `test/test_ecma262_test_evidence.ml` | checks executable test262-derived evidence inventory | `410` executable negative syntax evidence rows |
| `test/test_ecma262_ucd_generated_cases.ml` | checks generated UCD 16.0.0 cases | `366` requirement rows credited by UCD-generated tests |
| `test/test_raw_utf16_coverage_matrix.ml` | checks raw UTF-16 inventory classification | `32` covered rows, `0` open rows, `3` non-applicable rows |
| `test/test_raw_utf16_generated_cases.ml` | checks generated raw UTF-16 behavior cases | `1625` generated cases |
| `test/test_json_schema_corpus.ml` | checks regex-facing JSON Schema consumer corpus | `187/187` corpus cases passing |

The ledger is the only layer that may summarize ECMA-262 requirement coverage
as complete. Individual tests prove behavior; the ledger decides whether those
tests are sufficient requirement-level credit.

## ECMA-262 Evidence

Current ECMA-262 coverage result:

```text
ecma262_snapshot=2026
ledger_rows=2020
direct_requirement_rows=2018
covered_rows=1770
non_applicable_rows=248
coverage_complete=true
```

Credited ECMA-262 evidence comes from:

- local exact compile/parser tests;
- reused-candidate exact compile/parser tests;
- compile/parser exact-plan tests;
- literal lexer exact-plan tests;
- match-engine exact-plan tests;
- exec-result exact-plan tests;
- spec-model and match-state exact tests;
- product adapter tests;
- UCD-generated tests where ECMA-262 depends on Unicode data.

The exactness audit reports:

```text
exactness_credit_rows=1144
open_exactness_rows=410
potential_exact_ready_rows=0
```

The `410` open exactness rows are the executable negative syntax corpus rows.
They are deliberately not counted as ECMA-262 requirement credit until each row
is mapped to a concrete requirement row or proved to duplicate an already
credited requirement.

## Product Adapter Evidence

Product adapter evidence covers ECMA-262 RegExp behavior exposed through direct
OCaml functions instead of JavaScript object/prototype dispatch.

Credited adapter rows:

```text
search_adapter=16
match_adapter=25
match_all_adapter=16
split_adapter=52
replace_adapter=119
escape_adapter=32
```

Evidence artifacts:

- `test/test_ecma262_search_adapter.ml`
- `test/test_ecma262_match_adapter.ml`
- `test/test_ecma262_match_all_adapter.ml`
- `test/test_ecma262_split_adapter.ml`
- `test/test_ecma262_replace_adapter.ml`
- `test/test_ecma262_escape_adapter.ml`

These tests prove the explicit OCaml adapter API. They do not claim JavaScript
object dispatch, prototype lookup, constructors, receiver coercion, or
JavaScript callable replacement-function behavior.

## Unicode Evidence

Unicode behavior is pinned to UCD 16.0.0.

Required Unicode source files:

- `PropertyAliases.txt`
- `PropertyValueAliases.txt`
- `UnicodeData.txt`
- `CaseFolding.txt`
- `PropList.txt`
- `DerivedCoreProperties.txt`
- `DerivedNormalizationProps.txt`
- `Scripts.txt`
- `ScriptExtensions.txt`
- `emoji/emoji-data.txt`

Generated runtime source:

- `lib/ecma_regex_ucd_tables.ml`

Generation and test tools:

- `tools/build_ucd_tables.py`
- `tools/build_ucd_regexp_tests.py`
- `test/test_ecma262_ucd_generated_cases.ml`

Current credited result:

```text
ucd_version=16.0.0
ucd_generated_case_rows=366
ucd_coverage_credit_rows=366
ucd_alcotest_cases=17
```

This evidence covers Unicode property aliases, property value aliases,
Script/Script_Extensions membership, General_Category membership, binary
properties, property escapes inside character classes, character-set
membership, and simple/common case folding used by Unicode ignore-case
matching.

Changing the Unicode version is a semantic change: the generator, runtime
tables, UCD evidence, and conformance ledger must all be regenerated and
rechecked together.

## Raw UTF-16 Evidence

Raw UTF-16 evidence proves explicit ECMAScript String behavior where OCaml
UTF-8 strings are not sufficient to observe the semantics.

Public surfaces covered:

- `js_string`
- `js_string_of_utf8`
- `js_string_of_utf16_code_units`
- `js_string_to_utf16_code_units`
- `exec_js`
- `search_js`
- `search_index_js`
- `exec_instance_js`
- `iter_matches_js`
- `next_match_js`
- JS variants of match, matchAll, split, replace, replaceAll, and escape

Current raw UTF-16 inventory:

```text
rows=35
covered=32
open=0
non_applicable_with_reason=3
generated_cases=1625
```

Evidence artifacts:

- `test/test_raw_utf16_coverage_matrix.ml`
- `test/test_raw_utf16_generated_cases.ml`
- `test/test_raw_utf16_result_slicing_matrix.ml`
- `test/test_raw_utf16_negative_position_matrix.ml`
- `test/test_raw_utf16_escape_matrix.ml`
- `test/test_api.ml`

This evidence covers lone surrogates, valid surrogate pairs, Unicode
code-point advancement, non-Unicode code-unit behavior, raw result slicing,
captures over raw strings, iterator advancement, adapter variants, and
`RegExp.escape` behavior over raw ECMAScript Strings.

## JSON Schema Consumer Evidence

JSON Schema is a consumer profile, not the governing regular-expression
language source.

Covered JSON Schema regex-facing surfaces:

- `pattern`
- `patternProperties`
- `format: regex`

Covered draft families:

- draft-03
- draft-04
- draft-06
- draft-07
- draft-2019-09
- draft-2020-12
- v1 corpus layout

Current corpus result:

```text
corpus_cases=187
observed_pass=187
observed_fail=0
remaining_failure_worklist_rows=0
```

The corpus proves that regex-facing JSON Schema consumer behavior is compatible
with the `ecma-regex` public API. It does not define a separate regexp
language and does not override ECMA-262 RegExp semantics.

## Contract-Only Evidence

The following are public OCaml contract rather than direct ECMA-262
requirements:

- OCaml type names;
- record and variant field names;
- `syntax_error = string`;
- use of `result`, `option`, and `list`;
- direct functions instead of JavaScript method dispatch;
- eager result materialization instead of JavaScript iterator objects.

Contract-only does not mean untested. Contract-only behavior is checked through
the public signature and API tests, but its source of truth is the documented
OCaml API rather than one-to-one JavaScript host object text.

## Intentional Exclusions

Intentional exclusions are visible in the product-surface matrix and are not
counted as matcher gaps.

Current exclusion family:

- JavaScript runtime embedding;
- JavaScript object/prototype dispatch;
- constructors and subclassing;
- prototype mutation;
- dynamic method lookup;
- receiver coercion and object wrapping;
- function objects and function metadata;
- JavaScript callable replacement functions;
- plain String prototype branches;
- Annex B mutating `RegExp.prototype.compile` host behavior.

Where these areas have RegExp semantic equivalents, the semantic equivalent is
tested through explicit OCaml adapter functions.

## Package And Documentation Evidence

Package/install evidence is not ECMA-262 conformance evidence, but it proves
the delivered package surface.

Current package gates:

- `opam lint ecma-regex.opam`
- `opam exec -- dune build @install`
- `opam install . --with-test --dry-run --yes`
- `opam exec -- dune build @doc` in a switch with `odoc` available
- `opam install . --with-test --with-doc --dry-run --yes` in a switch where
  the documentation dependency can be solved

These gates prove metadata sanity, install artifact construction, documentation
buildability in an odoc-capable switch, and opam solver/package dry-run
behavior. They do not add ECMA-262 semantic coverage credit.

## Quality-Hardening Follow-Up

Current follow-up:

```text
negative_syntax_executable_rows=410
negative_syntax_requirement_linked_rows=0
negative_syntax_coverage_credit_rows=0
```

This is not a known runtime mismatch. It is a stricter evidence-accounting
task: map executable negative syntax corpus rows to exact ECMA-262 requirement
rows, or prove that a row duplicates already credited syntax evidence.

Until that mapping exists, those rows remain `uncredited evidence`, not
conformance credit.
