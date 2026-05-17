# Spec Conformance

This document is the normative conformance statement for `ecma-regex`.

It sits downstream of [`NORMATIVE_HIERARCHY.md`](NORMATIVE_HIERARCHY.md): the
hierarchy fixes source precedence, while this document states what the current
library claims to implement, what is library-defined, and what is outside the
product API.

This document is not a command log and not a generated matrix dump. It is the
stable interpretation of the implementation and evidence story for release and
future audits.

## Sources

Primary sources used by this repository:

- ECMA-262 RegExp grammar and algorithms.
- ECMA-262 `RegExp.escape`.
- Unicode Character Database 16.0.0.
- JSON Schema regex-facing behavior for `pattern`, `patternProperties`, and
  `format: regex` as a consumer profile.

Secondary sources:

- Dune and opam package metadata rules for the package/install surface.
- The documented OCaml public API in `lib/ecma_regex.mli`.

## Current Conformance Status

The current conformance gate reports:

```text
coverage_complete=true
release_blocking_open_rows=0
covered_rows=1770
non_applicable_rows=248
```

Interpretation:

- every release-blocking direct requirement tracked by the coverage ledger is
  covered or explicitly outside the OCaml product surface;
- product-surface rows split into explicit OCaml adapter requirements and
  non-OCaml-surface policy rows;
- raw UTF-16 public behavior has no open inventory row;
- JSON Schema regex-facing corpus execution is green for the wired corpus;
- generated Unicode evidence is pinned to UCD 16.0.0.

This status is a claim about the explicit OCaml API, not about implementing a
JavaScript runtime.

## Architectural Boundary

### Generated facts

These facts are generated from ECMA-262 tables and UCD 16.0.0 data and are
consumed by runtime source:

- Unicode property aliases and value aliases.
- Script and Script_Extensions membership.
- General_Category membership.
- Binary property membership.
- Unicode property membership inside character classes.
- Character-set membership.
- Simple/common case folding used by Unicode ignore-case matching.

The generated OCaml runtime source is part of the library. Intermediate
generated matrices and downloaded source snapshots are reproducibility inputs,
not public API.

### Hand-written semantics

These behaviors are implemented as explicit runtime semantics:

- flag parsing and duplicate/unknown flag rejection;
- `u` and `v` conflict rejection;
- regular-expression literal parsing;
- compile-time syntax validation;
- parsing and matching of ECMA-262 RegExp constructs tracked by the
  conformance ledger;
- matcher state, continuations, captures, and backreferences;
- assertions, anchors, lookahead, and lookbehind;
- quantifiers, alternation, concatenation, and scoped modifiers;
- raw UTF-16 code-unit and code-point indexing;
- `lastIndex` state for global and sticky regexps;
- RegExp string iteration and empty-match advancement;
- adapter semantics for search, match, matchAll, split, replace, replaceAll,
  and escape.

### Library-defined contract

These parts are public and tested, but not direct normative ECMA-262 surface
names:

- OCaml module, function, record, and variant names.
- `syntax_error = string` as the current diagnostic representation.
- UTF-8 convenience APIs in addition to explicit raw UTF-16 APIs.
- Eager OCaml lists where JavaScript would expose iterator objects.
- Direct OCaml adapter functions where JavaScript would use object/prototype
  dispatch.
- Package metadata and install documentation surface.

Library-defined does not mean optional or untested. It means the behavior is
judged by the documented OCaml contract and by consistency with ECMA-262 RegExp
semantics.

## Public Surface Conformance

### Core public types

Public surface:

- `t`
- `instance`
- `match_iterator`
- `js_match_iterator`
- `js_string`
- `syntax_error`
- `flags`
- `regexp_literal`
- `match_result`
- `js_match_result`
- `js_capture`
- `js_named_capture`
- `split_part`
- `js_split_part`

Conformance claim:

- `t` represents a compiled ECMAScript regular expression.
- `instance` represents explicit mutable ECMAScript `lastIndex` state.
- `match_iterator` and `js_match_iterator` represent explicit RegExp string
  iterators for OCaml UTF-8 and raw ECMAScript String inputs.
- `js_string` represents an ECMAScript String as UTF-16 code units.
- `flags` represents ECMAScript RegExp flags.
- `regexp_literal` preserves parsed pattern text and exact flag source text.
- Match and split result types expose ECMAScript match spans, captures,
  undefined captures, and raw string slices where the public API promises them.

Library-defined:

- OCaml type names.
- Record and variant field names.
- `syntax_error = string` as the current diagnostic representation.
- Eager OCaml result materialization instead of JavaScript host objects.

### Flags and regular-expression literals

Public surface:

- `flags`
- `flags_of_string`
- `regexp_literal_of_string`

Conformance claim:

- ECMAScript flag text is parsed.
- Duplicate and unknown flags are rejected.
- Invalid `u` plus `v` combinations are rejected.
- Regular-expression literal source is split into pattern text, exact flag
  text, and parsed flags.

Library-defined:

- OCaml constructor function shape.
- Diagnostic string contents.
- Returned record field names.

### Compile-time syntax validation

Public surface:

- `compile`

Conformance claim:

- ECMAScript RegExp grammar and static syntax constraints tracked by the
  conformance ledger are enforced through the public RegExp compile surface.
- Unicode property escape names and values are validated against the generated
  Unicode/ECMA-262 data set.
- Patterns are not implicitly anchored.

Library-defined:

- `result` return shape.
- Diagnostic strings.

### UTF-8 convenience matching

Public surface:

- `exec`
- `search`
- `search_index`

Conformance claim:

- Matching follows ECMA-262 RegExp semantics.
- Result indices are ECMAScript UTF-16 code-unit indices, even for OCaml UTF-8
  string input.
- `search_index` exposes the first match start index or `-1`.

Library-defined:

- OCaml UTF-8 string input convenience surface.
- `option` and record result shape.

### Explicit raw UTF-16 ECMAScript String API

Public surface:

- `js_string`
- `js_string_of_utf8`
- `js_string_of_utf16_code_units`
- `js_string_to_utf16_code_units`
- `exec_js`
- `search_js`
- `search_index_js`

Conformance claim:

- ECMAScript String values are represented as UTF-16 code units.
- Lone surrogates and valid surrogate pairs are representable.
- Values outside `0x0000..0xFFFF` are rejected before matching.
- Raw UTF-16 result indices and matched text preserve ECMAScript String
  semantics.

Library-defined:

- OCaml abstract type for ECMAScript String values.
- Error reporting shape for invalid code units.

### Captures and result shape

Public surface:

- `match_result`
- `js_capture`
- `js_named_capture`
- `js_match_result`

Conformance claim:

- Full-match ranges are exposed.
- Numbered captures, named captures, undefined captures, and raw captured text
  are represented for explicit ECMAScript String results.
- Capture indices use UTF-16 code-unit indexing.

Library-defined:

- OCaml record field names.
- List representation of captures and named captures.

### Stateful RegExp instances

Public surface:

- `instance`
- `last_index`
- `set_last_index`
- `exec_instance`
- `exec_instance_js`
- `search_instance_index`
- `search_instance_index_js`

Conformance claim:

- Global and sticky regexps use and update `lastIndex` according to ECMA-262
  matching rules.
- Failed global/sticky execution resets state as required.
- Non-global and non-sticky instance execution preserves stored `lastIndex`.
- Explicit raw UTF-16 instance APIs preserve ECMAScript indexing.

Library-defined:

- Explicit mutable OCaml `instance` type.
- Direct setter/getter functions.

### RegExp string iterators

Public surface:

- `iter_matches`
- `next_match`
- `iter_matches_js`
- `next_match_js`

Conformance claim:

- Iterator advancement follows ECMA-262 `AdvanceStringIndex`.
- Empty global matches advance without looping forever.
- Unicode mode advances over valid surrogate pairs as code points where ECMA-262
  requires it.

Library-defined:

- Explicit OCaml iterator type.
- `option` result shape for exhaustion.

### Adapter operations

Public surface:

- `match_`
- `match_js`
- `match_instance`
- `match_instance_js`
- `match_all`
- `match_all_js`
- `match_all_instance`
- `match_all_instance_js`
- `split`
- `split_js`
- `split_instance`
- `split_instance_js`
- `replace`
- `replace_js`
- `replace_instance`
- `replace_instance_js`
- `replace_all`
- `replace_all_js`
- `replace_all_instance`
- `replace_all_instance_js`
- `escape`
- `escape_js`

Conformance claim:

- Adapter behavior follows ECMA-262 RegExp semantics for the explicit compiled
  regexp and string inputs.
- Match and matchAll behavior distinguishes null/no-match shape from iterator
  style result shape.
- Split inserts numbered captures and observes limits and empty-match
  advancement.
- Replacement uses string replacement-template semantics with numbered and
  named captures.
- Escape returns ECMA-262 `RegExp.escape` pattern text for literal matching.
- Raw UTF-16 variants preserve raw code-unit slices and indices.

Library-defined:

- Direct OCaml functions instead of JavaScript method dispatch.
- Eager OCaml list materialization.
- `split_part` and `js_split_part` variant names for split output.
- String-template replacement surface; JavaScript functional replacer callable
  dispatch is outside this product API.

### Unicode-sensitive behavior

Public surface:

- Unicode property escapes in compiled patterns.
- Unicode-sensitive matching under `u`, `v`, and ignore-case modes.
- Raw UTF-16 APIs where surrogate-pair behavior is observable.

Conformance claim:

- Unicode property aliases and values are governed by ECMA-262 and UCD 16.0.0.
- Script, Script_Extensions, General_Category, binary properties, and
  property escapes inside character classes are implemented for the public
  RegExp behavior credited by the conformance ledger.
- Simple/common case folding is used where ECMA-262 Unicode ignore-case
  semantics require it.

Library-defined:

- UCD version pinning policy.
- Generated OCaml source layout.

### JSON Schema regex-facing compatibility

Public surface:

- Consumer use of `ecma-regex` for JSON Schema regex-facing behavior.

Conformance claim:

- JSON Schema `pattern` and `patternProperties` use search semantics.
- JSON Schema `format: regex` is a compile/parse consumer of the same
  ECMA-262 RegExp syntax.
- The JSON Schema corpus does not define a separate regexp language.

Library-defined:

- How an OCaml JSON Schema validator wires this library into schema validation.

## Intentional Exclusions

The following are outside the `ecma-regex` product API:

- JavaScript runtime embedding.
- JavaScript object dispatch.
- Constructors and subclassing.
- Prototype mutation.
- Dynamic method lookup.
- Receiver coercion and object wrapping.
- Function objects and function metadata.
- JavaScript functional replacer callable dispatch.

These exclusions are not matcher gaps. They are JavaScript host/object protocol
areas. The corresponding RegExp behavior must be tested through the explicit
OCaml adapter functions where the behavior is part of this library.

## Known Quality-Hardening Follow-up

The extracted negative syntax corpus is executable and green, but those rows
are not currently consumed as exact requirement-level coverage credit.

Current interpretation:

- this is not a release-blocking conformance gap because the coverage gate has
  no release-blocking open row;
- it remains a valid adversarial-quality follow-up;
- future work should map those negative syntax rows to exact ECMA-262
  requirement rows or prove that they are duplicate evidence for already
  credited syntax requirements.

This follow-up must not be described as an implementation mismatch unless an
actual runtime mismatch is found.

## What This Document Does Not Claim

This document does not claim:

- implementation of a JavaScript runtime;
- implementation of JavaScript object/prototype protocol;
- that generated intermediate matrices are public API;
- that future Unicode versions have the same behavior as the pinned UCD 16.0.0
  version;
- that README examples or package metadata are themselves conformance proof.

## Decision Rule

Before adding or changing behavior, identify:

1. the governing source from `NORMATIVE_HIERARCHY.md`;
2. the public surface affected;
3. whether the behavior is normative, library-defined, contract-only, or
   outside the product API;
4. the tests or generated evidence that prove it;
5. whether the change affects generated facts or hand-written semantic
   orchestration.

If this cannot be answered, the work remains research/audit work and should not
be represented as completed conformance.
