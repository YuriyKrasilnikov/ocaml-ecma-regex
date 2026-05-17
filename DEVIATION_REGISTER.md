# Deviation Register

This document records confirmed deviations, intentional exclusions, and
library-defined behavior that could otherwise be mistaken for missing
implementation.

It is downstream of:

- [`NORMATIVE_HIERARCHY.md`](NORMATIVE_HIERARCHY.md)
- [`SPEC_CONFORMANCE.md`](SPEC_CONFORMANCE.md)
- [`NORMATIVE_TEST_MATRIX.md`](NORMATIVE_TEST_MATRIX.md)
- [`TEST_EVIDENCE_AUDIT.md`](TEST_EVIDENCE_AUDIT.md)

## Current Confirmed Mismatches

There are currently no confirmed runtime mismatches recorded for the public
`ecma-regex` API.

A confirmed mismatch means:

1. the behavior belongs to the public OCaml API;
2. the governing source requires different behavior;
3. executable evidence demonstrates the mismatch;
4. the row is not covered by an accepted intentional exclusion or
   library-defined contract.

If a future mismatch meets those conditions, it must be recorded here until it
is fixed or formally reclassified.

## Intentional Exclusions

These areas are intentionally outside the `ecma-regex` OCaml public API:

- JavaScript runtime embedding;
- JavaScript object dispatch;
- constructors and subclassing;
- prototype mutation;
- dynamic method lookup;
- receiver coercion and object wrapping;
- function objects and function metadata;
- JavaScript callable replacement functions;
- plain String prototype branches that do not exercise a RegExp adapter;
- Annex B mutating `RegExp.prototype.compile` host behavior.

These are not matcher deviations. They are JavaScript host/object protocol
areas. Where the underlying RegExp behavior is part of the OCaml API, it is
tested through explicit functions such as `search_index`, `match_`,
`match_all`, `split`, `replace`, `replace_all`, and `escape`, plus their raw
ECMAScript String variants.

## Library-Defined Behavior

These behaviors are public and intentional, but their exact shape is defined by
the OCaml API rather than direct ECMA-262 host-object text:

- OCaml module and function names;
- OCaml record and variant field names;
- `syntax_error = string`;
- `result`, `option`, and `list` return shapes;
- eager list materialization where JavaScript would expose iterator objects;
- direct adapter functions where JavaScript would use method dispatch;
- `js_string` as an explicit OCaml representation of ECMAScript String values;
- package metadata and install documentation shape.

Library-defined behavior must still be tested. It must not be used to hide a
real RegExp semantic mismatch.

## Non-Applicable Rows With Reasons

The current conformance ledger contains:

```text
non_applicable_rows=248
```

Those rows are non-applicable because they describe JavaScript host/object
protocol rather than the explicit OCaml RegExp API. They remain visible in the
product-surface evidence and are not silently dropped.

The rule is:

1. if a row describes RegExp matching semantics, it must be tested through the
   OCaml public API;
2. if a row describes JavaScript host/object protocol, it may be
   non-applicable only with a concrete reason;
3. if the distinction is unclear, the row remains audit work until it is
   classified.

## Uncredited Evidence

The current negative syntax corpus status is:

```text
negative_syntax_executable_rows=410
negative_syntax_requirement_linked_rows=0
negative_syntax_coverage_credit_rows=0
```

This is not recorded as a runtime mismatch.

It is recorded as uncredited evidence because the rows execute and pass, but
they are not yet mapped to exact ECMA-262 requirement rows. They may become
credit only after exact mapping or proof that they duplicate already credited
syntax evidence.

## Unicode Version Policy

The current Unicode version is:

```text
UCD 16.0.0
```

Changing the Unicode version can change accepted property names, property value
aliases, membership sets, and case-folding behavior. Such a change is not a
small documentation update. It requires regenerated runtime tables, regenerated
Unicode evidence, and a fresh conformance ledger check.

## Registration Rule

Add a row to this document when any of the following happens:

1. a public API behavior is proven to differ from its governing source;
2. a previously excluded row becomes part of the public API;
3. a library-defined behavior is easy to confuse with a spec deviation;
4. a generated-data policy change affects observable behavior;
5. an evidence layer is green but not accepted as conformance credit.

Do not add vague backlog items here. A row belongs here only when it is a
confirmed mismatch, an intentional exclusion, a library-defined contract, or
uncredited evidence with a concrete classification.
