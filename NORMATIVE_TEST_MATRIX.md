# Normative Test Matrix

This document connects `ecma-regex` requirements to executable evidence.

It is downstream of:

- [`NORMATIVE_HIERARCHY.md`](NORMATIVE_HIERARCHY.md)
- [`SPEC_CONFORMANCE.md`](SPEC_CONFORMANCE.md)

The hierarchy states which source governs each surface. The conformance
statement states what the library claims. This matrix states how those claims
are credited by tests, generated evidence, or explicit exclusion policy.

This document is not a generated table dump. Generated machine-readable
matrices are reproducibility inputs; this document is the stable interpretation
of their current result.

## Status Language

Allowed statuses in this document:

- `covered`: executable evidence or generated evidence is wired into the
  conformance gate.
- `intentional exclusion`: the row is outside the OCaml public API and has a
  recorded reason.
- `contract-only`: the behavior is public OCaml contract, not a direct
  ECMA-262 requirement row.
- `uncredited evidence`: executable evidence exists but is not currently used
  as exact requirement-level credit.
- `gap`: a requirement has no sufficient evidence and no accepted exclusion.

`covered` is only valid when the evidence is connected to a committed test,
tool, or generated runtime source path.

## Current Ledger Result

The current ECMA-262 RegExp coverage ledger reports:

```text
ecma262_snapshot=2026
ledger_rows=2020
direct_requirement_rows=2018
covered_rows=1770
non_applicable_rows=248
release_blocking_open_rows=0
coverage_complete=true
```

Interpretation:

- `1770` rows are credited by exact tests, adapter tests, generated UCD tests,
  or other executable conformance evidence.
- `248` rows are intentional exclusions with reasons: JavaScript runtime,
  object/prototype dispatch, constructors, dynamic method lookup, function
  object behavior, JavaScript callable replacers, or other host protocol
  behavior outside this OCaml API.
- `2` rows are container clauses, not direct requirements.
- There is no current requirement row classified as a `gap`.

## Requirement-To-Evidence Matrix

| Requirement family | Governing source | Public surface | Evidence | Status |
|---|---|---|---|---|
| RegExp grammar and static syntax validation | ECMA-262 RegExp grammar and static semantics | `compile`, `regexp_literal_of_string`, `flags_of_string` | `test/test_ecma262_compile_parser_exact_plan.ml`, `test/test_ecma262_local_exact_compile_parser.ml`, `test/test_ecma262_reused_candidate_exact_compile_parser.ml`, `test/test_ecma262_literal_lexer_exact_plan.ml`, `test/test_ecma262_compile_parser_selection.ml` | covered |
| Flag parsing and literal flag text | ECMA-262 RegExp flags and regular-expression literal grammar | `flags`, `flags_of_string`, `regexp_literal_of_string` | `test/test_ecma262_literal_lexer_exact_plan.ml`, `test/test_api.ml` | covered |
| Matcher core dispatch | ECMA-262 RegExp matcher algorithms | `exec`, `search`, `exec_js`, `search_js` | `test/test_ecma262_match_engine_exact_plan.ml`, `test/test_ecma262_match_engine_atoms_exact_plan.ml`, `test/test_ecma262_match_engine_pattern_semantics_exact_plan.ml`, `test/test_ecma262_match_engine_annex_b_exact_plan.ml` | covered |
| Concatenation, alternation, and result priority | ECMA-262 matcher algorithms | `search`, `exec` | `test/test_ecma262_match_engine_concatenation_exact_plan.ml`, `test/test_ecma262_match_engine_result_exact_plan.ml`, `test/test_ecma262_exec_result_matching_exact_plan.ml` | covered |
| Assertions, anchors, lookahead, and lookbehind | ECMA-262 assertion compilation and matcher semantics | `search`, `exec`, `exec_js` | `test/test_ecma262_match_engine_assertion_exact_plan.ml`, `test/test_ecma262_match_engine_start_anchor_exact_plan.ml`, `test/test_ecma262_match_engine_end_anchor_exact_plan.ml`, `test/test_api.ml` | covered |
| Quantifiers and empty-match behavior | ECMA-262 quantifier semantics and `AdvanceStringIndex` | `search`, `exec`, `iter_matches`, `next_match`, `iter_matches_js`, `next_match_js` | `test/test_ecma262_match_engine_quantifier_exact_plan.ml`, `test/test_api.ml`, `test/test_raw_utf16_generated_cases.ml` | covered |
| Captures and named captures | ECMA-262 capturing group and named group semantics | `exec_js`, `match_js`, `match_all_js`, `js_capture`, `js_named_capture`, `js_match_result` | `test/test_ecma262_match_engine_capture_exact_plan.ml`, `test/test_ecma262_exec_result_capture_exact_plan.ml`, `test/test_raw_utf16_result_slicing_matrix.ml`, `test/test_api.ml` | covered |
| Backreferences | ECMA-262 backreference grammar and matcher semantics | `search`, `exec`, `exec_js` | `test/test_ecma262_match_engine_backreference_exact_plan.ml`, `test/test_ecma262_match_engine_backreference_matcher_exact_plan.ml` | covered |
| Character classes, ranges, and class escapes | ECMA-262 character-class grammar and matcher semantics | `search`, `exec_js` | `test/test_ecma262_match_engine_character_classes_exact_plan.ml`, `test/test_raw_utf16_escape_matrix.ml`, `test/test_raw_utf16_negative_position_matrix.ml` | covered |
| UnicodeSets string properties | ECMA-262 UnicodeSets character-class behavior | `search`, `exec_js` | `test/test_ecma262_match_engine_unicode_sets_string_exact_plan.ml`, `test/test_ecma262_match_engine_unicode_sets_escape_string_exact_plan.ml` | covered |
| Unicode property escapes and aliases | ECMA-262 Unicode property escape rules, UCD 16.0.0 | `compile`, `search`, `exec_js` | `tools/build_ucd_tables.py`, `tools/build_ucd_regexp_tests.py`, `test/test_ecma262_ucd_generated_cases.ml` | covered |
| Unicode ignore-case behavior | ECMA-262 Unicode ignore-case semantics, UCD 16.0.0 case folding | `search`, `exec_js` | `tools/build_ucd_regexp_tests.py`, `test/test_ecma262_ucd_generated_cases.ml`, `test/test_api.ml` | covered |
| Raw ECMAScript String representation | ECMA-262 UTF-16 String model | `js_string`, `js_string_of_utf8`, `js_string_of_utf16_code_units`, `js_string_to_utf16_code_units` | `test/test_raw_utf16_coverage_matrix.ml`, `test/test_raw_utf16_generated_cases.ml`, `test/test_api.ml` | covered |
| Raw UTF-16 search, exec, captures, and slicing | ECMA-262 UTF-16 indexing and matcher semantics | `exec_js`, `search_js`, `search_index_js`, `exec_instance_js`, `iter_matches_js`, `next_match_js` | `test/test_raw_utf16_generated_cases.ml`, `test/test_raw_utf16_result_slicing_matrix.ml`, `test/test_raw_utf16_negative_position_matrix.ml`, `test/test_raw_utf16_escape_matrix.ml` | covered |
| `lastIndex` state | ECMA-262 global and sticky RegExp state behavior | `instance`, `last_index`, `set_last_index`, `exec_instance`, `exec_instance_js`, `search_instance_index`, `search_instance_index_js` | `test/test_api.ml`, `test/test_ecma262_exec_result_instances_exact_plan.ml`, `test/test_ecma262_match_state_exact_plan.ml` | covered |
| RegExp string iterators | ECMA-262 RegExp String Iterator behavior | `iter_matches`, `next_match`, `iter_matches_js`, `next_match_js` | `test/test_api.ml`, `test/test_raw_utf16_generated_cases.ml` | covered |
| Search adapter | ECMA-262 search adapter semantics | `search_index`, `search_instance_index`, `search_index_js`, `search_instance_index_js` | `test/test_ecma262_search_adapter.ml` | covered |
| Match adapter | ECMA-262 match adapter semantics | `match_`, `match_js`, `match_instance`, `match_instance_js` | `test/test_ecma262_match_adapter.ml` | covered |
| MatchAll adapter | ECMA-262 matchAll adapter semantics | `match_all`, `match_all_js`, `match_all_instance`, `match_all_instance_js` | `test/test_ecma262_match_all_adapter.ml` | covered |
| Split adapter | ECMA-262 RegExp split adapter semantics | `split`, `split_js`, `split_instance`, `split_instance_js`, `split_part`, `js_split_part` | `test/test_ecma262_split_adapter.ml` | covered |
| Replace and replaceAll adapters | ECMA-262 RegExp replacement and replacement-template semantics | `replace`, `replace_js`, `replace_instance`, `replace_instance_js`, `replace_all`, `replace_all_js`, `replace_all_instance`, `replace_all_instance_js` | `test/test_ecma262_replace_adapter.ml` | covered |
| RegExp escaping | ECMA-262 `RegExp.escape` | `escape`, `escape_js` | `test/test_ecma262_escape_adapter.ml`, `test/test_raw_utf16_escape_matrix.ml` | covered |
| JSON Schema regex-facing consumer behavior | JSON Schema `pattern`, `patternProperties`, and `format: regex` consumer expectations over ECMA-262 RegExp syntax | Consumer use of `ecma-regex` | `test/test_json_schema_corpus.ml` | covered |
| OCaml result shapes and diagnostic representation | Library-defined OCaml contract | `syntax_error`, record fields, variants, `option`, `list`, `result` | `lib/ecma_regex.mli`, `test/test_api.ml`, exact-plan result tests | contract-only |
| JavaScript object/prototype/constructor protocol | JavaScript host and object model, not the OCaml API | none | Product-surface matrix routes these rows to explicit reasons | intentional exclusion |
| Negative syntax corpus extraction | test262 negative RegExp syntax cases | `compile`, `regexp_literal_of_string` where applicable | `test/test_test262_negative_syntax.ml`, `test/test_ecma262_test_evidence.ml` | uncredited evidence |

## Evidence Counts By Layer

Current credited layer counts:

```text
exactness_credit_rows=1144
ucd_generated_credit_rows=366
covered_by_search_adapter=16
covered_by_match_adapter=25
covered_by_match_all_adapter=16
covered_by_split_adapter=52
covered_by_replace_adapter=119
covered_by_escape_adapter=32
```

Current generated UCD evidence:

```text
ucd_version=16.0.0
ucd_generated_case_rows=366
ucd_coverage_credit_rows=366
ucd_alcotest_cases=17
```

Current raw UTF-16 inventory:

```text
raw_utf16_rows=35
raw_utf16_covered=32
raw_utf16_open=0
raw_utf16_non_applicable_with_reason=3
raw_utf16_generated_cases=1625
```

Current JSON Schema regex-facing corpus:

```text
corpus_cases=187
observed_pass=187
observed_fail=0
remaining_failure_worklist_rows=0
```

Current negative syntax corpus:

```text
negative_compile_cases=410
executable_evidence_rows=410
requirement_linked_rows=0
coverage_credit_rows=0
```

The negative syntax corpus is executable evidence, but it is not counted as
exact requirement-level credit. That is intentional for this matrix: a corpus
row becomes requirement credit only after it is mapped to a specific ECMA-262
requirement row or proved to duplicate already credited evidence.

## Exclusion Rules

An `intentional exclusion` row is valid only when all of these are true:

1. the behavior belongs to JavaScript host/object protocol rather than RegExp
   matching semantics exposed by this OCaml API;
2. the row remains visible in the product-surface matrix;
3. the row has a concrete reason;
4. equivalent RegExp behavior, where relevant, is tested through explicit
   OCaml adapter functions.

The current intentional-exclusion bucket covers JavaScript runtime embedding,
constructors, subclassing, prototype mutation, dynamic method lookup, receiver
coercion/object wrapping, function object metadata, JavaScript callable
replacement functions, plain String prototype branches, and Annex B mutating
`RegExp.prototype.compile` host behavior.

## Completion Rule

For this repository, the matrix is complete only when:

1. every direct ECMA-262 RegExp requirement row is `covered` or has an
   accepted `intentional exclusion`;
2. every public OCaml contract row is either covered by tests or marked
   `contract-only` with a stable API reason;
3. every generated Unicode claim is pinned to a Unicode version and has an
   executable generated gate;
4. every consumer-profile claim has a corpus gate;
5. every remaining executable corpus artifact that is not credited is marked
   `uncredited evidence`, not silently counted as conformance credit.

The current matrix satisfies those rules with no `gap` rows.
