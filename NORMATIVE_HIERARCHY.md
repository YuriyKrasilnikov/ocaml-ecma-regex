# Normative Hierarchy

This document fixes the governing-source hierarchy for `ecma-regex`.

It answers one question for each public surface:

**which source governs this behavior first, which sources are secondary, and
which parts are intentionally library-defined?**

This file is not a test matrix and not a release log. It is the stable boundary
that later conformance and evidence documents must use.

## Source Precedence

When sources overlap, this repository uses the following precedence model.

1. **ECMA-262 RegExp grammar and algorithms** govern ECMAScript regular
   expression syntax, flags, literal parsing, matching, result shape, stateful
   `lastIndex` behavior, string-iterator behavior, and RegExp adapter
   semantics.
2. **Unicode Character Database 16.0.0** governs the versioned data used for
   Unicode property names and values, script and script-extension membership,
   general categories, binary properties, character-set membership, and
   simple/common case folding.
3. **ECMA-262 `RegExp.escape`** governs the escaping helper exposed as
   `Ecma_regex.escape` and `Ecma_regex.escape_js`.
4. **JSON Schema regex-facing behavior** governs the consumer expectation that
   `pattern` and `patternProperties` are regular-expression searches, not
   implicit full-string matches. JSON Schema does not replace ECMA-262 as the
   RegExp semantic source.
5. **The explicit OCaml API contract** governs module layout, function names,
   OCaml result types, diagnostic-string error representation, and the choice
   to expose JavaScript-like operations as direct OCaml functions rather than
   through JavaScript object dispatch.

Corollaries:

- ECMA-262 RegExp semantics govern the regular-expression language and matcher.
- UCD 16.0.0 governs versioned Unicode facts consumed by the matcher.
- JSON Schema is a consumer profile over the same RegExp semantics.
- JavaScript object/prototype/constructor dispatch is not the governing model
  for this OCaml library's public API.

## Architectural Hierarchy

The repository is expected to respect the following layered split.

### Generated Facts

These are governed first by ECMA-262 tables and UCD 16.0.0 source data. They
must come from generator tooling and generated runtime source, not from
hand-maintained ad hoc runtime lists:

- Unicode property aliases and value aliases accepted by property escapes.
- Script and Script_Extensions membership.
- General_Category membership.
- Binary property membership.
- Character-class property membership.
- Character-set membership.
- Simple/common case folding data used by Unicode ignore-case matching.
- Runtime generated source needed by the library, such as
  `lib/ecma_regex_ucd_tables.ml`.

Generated cache or matrix outputs are development artifacts. They may be used
to reproduce evidence, but they are not public API and are not part of the
package surface.

### Hand-Written Semantic Orchestration

These are governed by ECMA-262 grammar and algorithm prose and must remain
explicit in runtime code:

- flag parsing and duplicate/unknown flag rejection;
- `u` / `v` conflict rejection;
- regular-expression literal parsing;
- compile-time syntax validation;
- matcher state and continuation behavior;
- captures, named captures, and backreferences;
- assertions, anchors, lookahead, and lookbehind;
- quantifier and alternation behavior;
- raw UTF-16 code-unit and code-point advancement;
- stateful `lastIndex` behavior;
- string iterator advancement after empty matches;
- RegExp adapter behavior for search, match, matchAll, split, replace,
  replaceAll, and escape.

### Library-Defined Contract

These are intentionally outside direct normative text:

- OCaml module and function names.
- OCaml record and variant names.
- `syntax_error = string` as the current public diagnostic representation.
- Whether an operation returns `option`, `list`, `result`, or raises
  `invalid_arg` for inputs outside documented OCaml preconditions.
- The split between UTF-8 convenience APIs and explicit raw UTF-16
  ECMAScript String APIs.
- The choice to expose JavaScript RegExp adapter semantics as direct functions
  instead of invoking JavaScript object/prototype protocol.
- Package documentation and install surface.

Library-defined does not mean untested. It means the behavior is judged by the
documented OCaml contract and by consistency with the governing runtime
semantics, not by one-to-one textual equivalence to a JavaScript host object
operation.

## Governing-Source Matrix

| Public surface | Governing source | Secondary sources | Library-defined remainder |
|---|---|---|---|
| `flags` / `flags_of_string` | ECMA-262 RegExp flags | ECMA-262 Unicode mode and UnicodeSets mode constraints | OCaml constructor shape and error-string text |
| `regexp_literal_of_string` | ECMA-262 regular-expression literal lexical grammar | ECMA-262 flag grammar | returned OCaml record shape |
| `compile` | ECMA-262 RegExp grammar and static semantics | UCD 16.0.0 for Unicode property validation | `result` shape and diagnostic-string content |
| `exec` / `search` | ECMA-262 matching algorithms | UCD 16.0.0 for Unicode-sensitive matching | UTF-8 convenience input surface and OCaml result shape |
| `search_index` | ECMA-262 search adapter semantics | ECMA-262 UTF-16 index model | direct OCaml function instead of JS method dispatch |
| `match_` | ECMA-262 match adapter semantics | ECMA-262 global matching and empty-match advancement | `None` / list representation |
| `match_all` | ECMA-262 matchAll adapter semantics | ECMA-262 iterator behavior | eager OCaml list instead of JS iterator object |
| `split` | ECMA-262 RegExp split adapter semantics | ECMA-262 captures and `AdvanceStringIndex` | OCaml `split_part` representation |
| `replace` / `replace_all` | ECMA-262 RegExp replacement semantics | ECMA-262 replacement-template behavior | string-replacement-only OCaml surface, no functional replacer dispatch |
| `escape` | ECMA-262 `RegExp.escape` | ECMA-262 syntax character rules | OCaml string input/output shape |
| `js_string` and conversion functions | ECMA-262 ECMAScript String model | Unicode scalar/code-unit distinction | OCaml abstract type and validation error shape |
| `exec_js` / `search_js` / `search_index_js` | ECMA-262 matching over ECMAScript String values | UCD 16.0.0 for Unicode-sensitive behavior | explicit `js_string` API instead of host JS strings |
| `match_js` / `match_all_js` / `split_js` / `replace_js` / `replace_all_js` / `escape_js` | ECMA-262 RegExp adapter semantics over ECMAScript String values | ECMA-262 raw UTF-16 indexing and capture semantics | OCaml records, variants, and list materialization |
| `instance`, `last_index`, `set_last_index` | ECMA-262 RegExp instance state model | ECMA-262 global/sticky behavior | explicit mutable OCaml `instance` type |
| `exec_instance` and `*_instance` adapters | ECMA-262 stateful RegExp operation semantics | ECMA-262 `lastIndex` update/reset rules | direct OCaml instance calls instead of JS receiver protocol |
| `iter_matches` / `next_match` / `iter_matches_js` / `next_match_js` | ECMA-262 RegExp String Iterator behavior | ECMA-262 `AdvanceStringIndex` and raw UTF-16 indexing | explicit OCaml iterator types |
| JSON Schema regex compatibility | JSON Schema `pattern` / `patternProperties` search expectation | ECMA-262 RegExp semantics | consumer-profile evidence, not a separate regex language |
| Generated Unicode runtime tables | UCD 16.0.0 plus ECMA-262 property tables | generator tooling | generated OCaml source is committed runtime source; generated cache is not public API |
| Package metadata and install surface | Dune/opam package model | repository release policy | exact package description and included docs |

## Product-Surface Boundary

`ecma-regex` is an OCaml library for ECMAScript regular-expression behavior. It
is not a JavaScript runtime.

The following JavaScript-host behaviors are outside this public surface:

- JavaScript object dispatch;
- constructors and subclassing;
- prototype mutation;
- dynamic method lookup;
- function objects and function metadata;
- functional replacer dispatch as a JavaScript callable;
- JavaScript receiver coercion and object wrapping.

These areas are not runtime matcher semantics. They are JavaScript host/object
protocol. The OCaml library may expose equivalent RegExp operations as direct
functions, and those direct functions are the public surface to test.

Any future claim that one of these excluded areas is required must show:

1. the ECMA-262 requirement is actually RegExp semantic behavior rather than
   JavaScript object protocol;
2. the behavior cannot already be expressed by the explicit OCaml API;
3. the public API change needed to expose it;
4. the tests that will prove it.

Until then, these areas belong in product-surface policy or a deviation
register as non-OCaml-surface behavior, not in the implementation backlog.

## Consumer-Profile Boundary

JSON Schema compatibility is a consumer profile over ECMA-262 RegExp semantics.

For this repository:

- JSON Schema `pattern` and `patternProperties` use search semantics, not
  implicit full-string anchoring.
- `format: regex` is a compile/parse consumer of the same RegExp syntax.
- JSON Schema does not introduce a different regular-expression engine.
- JSON Schema corpus evidence can prove consumer compatibility, but ECMA-262
  remains the governing source for regexp syntax and matching semantics.

## Unicode Version Boundary

Unicode-sensitive behavior in this repository is pinned to UCD 16.0.0.

This affects:

- Unicode property escapes;
- script and script-extension membership;
- general category membership;
- binary properties;
- UnicodeSets character-class behavior;
- simple/common case folding used by Unicode ignore-case matching.

Changing the Unicode version is a semantic change. It requires regenerated
runtime source and regenerated evidence, followed by the relevant test gates.

## Decision Gate

Any implementation or documentation change should be able to name:

1. the governing source from this hierarchy;
2. the public surface affected;
3. whether the behavior is normative, contract-only, library-defined, or
   outside the product API;
4. the tests or evidence that prove the behavior;
5. whether generated facts or hand-written semantic orchestration are involved.

If one of these is missing, the work stays in research/audit phase and must not
be described as completed release work.
