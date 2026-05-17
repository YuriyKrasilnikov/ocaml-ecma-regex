# Changes

## 0.1.0 - 2026-05-17

Initial release.

- Add an explicit OCaml API for ECMAScript RegExp syntax, matching semantics,
  stateful `lastIndex` behavior, adapter operations, and raw UTF-16
  ECMAScript String inputs.
- Support Unicode property escapes, captures, named captures, backreferences,
  assertions, quantifiers, `RegExp.escape`, search, match, matchAll, split,
  replace, and replaceAll style operations.
- Add generated Unicode runtime tables pinned to UCD 16.0.0.
- Add stable conformance documentation covering normative hierarchy,
  conformance status, test evidence, and documented deviations.
- Add ECMA-262, Test262, UCD, raw UTF-16, and JSON Schema regex-facing
  evidence tests.
- Add reproducible evidence tooling for rebuilding and auditing the release
  evidence.
- Keep default `dune runtest` self-contained for clean opam `--with-test`
  builds, with generated evidence and external corpus checks available through
  the explicit `@test/evidence` local gate.

This package provides an explicit OCaml API. It does not embed a JavaScript
runtime and does not claim JavaScript object, prototype, constructor,
receiver-coercion, or callable-replacer dispatch.
