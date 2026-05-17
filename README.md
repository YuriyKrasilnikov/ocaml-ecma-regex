# ecma-regex

ECMAScript regular expressions for OCaml.

`ecma-regex` implements ECMAScript `RegExp` syntax and matching semantics with
an explicit OCaml API. It is designed for users that need JavaScript-compatible
regular expressions without embedding a JavaScript runtime.

The library supports the core regexp language, Unicode property escapes,
captures, named captures, backreferences, assertions, quantifiers, RegExp
adapter operations, and explicit ECMAScript String values represented as raw
UTF-16 code units.

## Install

```sh
opam install ecma-regex
```

## Basic Use

Compile a pattern, then run search or exec-style operations:

```ocaml
let re =
  let flags = Ecma_regex.flags ~unicode:true () in
  match Ecma_regex.compile ~flags "\\p{Script=Greek}+" with
  | Ok re -> re
  | Error msg -> invalid_arg msg

let has_greek = Ecma_regex.search re "abc \206\177\206\178"

let first =
  match Ecma_regex.exec re "abc \206\177\206\178" with
  | None -> None
  | Some result ->
    Some (result.start_index, result.end_index, result.matched_text)
```

Patterns are not implicitly anchored. This matches ECMAScript and JSON Schema
`pattern` behavior: use `^` and `$` when the whole input must match.

## Flags

Use `flags` for typed construction or `flags_of_string` for ECMAScript flag
text:

```ocaml
let unicode_global = Ecma_regex.flags ~unicode:true ~global:true ()

let parsed =
  match Ecma_regex.flags_of_string "gu" with
  | Ok flags -> flags
  | Error msg -> invalid_arg msg
```

Duplicate flags, unknown flags, and the invalid `u` plus `v` combination are
rejected.

## Match Results

The simple UTF-8 string API exposes full-match text and UTF-16 code-unit
indices:

```ocaml
type match_result = {
  start_index : int;
  end_index : int;
  matched_text : string;
}
```

For captures and exact ECMAScript String behavior, use the `*_js` APIs.

## Raw UTF-16 Strings

ECMAScript strings are sequences of UTF-16 code units. That matters for
surrogate pairs, lone surrogates, `lastIndex`, and result indices.

`ecma-regex` exposes this model explicitly:

```ocaml
let js =
  match Ecma_regex.js_string_of_utf16_code_units [ 0xD83D; 0xDE00; 0x61 ] with
  | Ok s -> s
  | Error msg -> invalid_arg msg

let units = Ecma_regex.js_string_to_utf16_code_units js
```

Values outside `0x0000..0xFFFF` are rejected before matching.

## Adapter Operations

The library provides OCaml functions for the RegExp operations commonly reached
through JavaScript `RegExp.prototype` and `String.prototype` hooks:

```ocaml
val search_index : t -> string -> int
val match_ : t -> string -> match_result list option
val match_all : t -> string -> match_result list
val split : ?limit:int -> t -> string -> split_part list
val replace : replacement:string -> t -> string -> string
val replace_all : replacement:string -> t -> string -> string
val escape : string -> string
```

Each operation also has explicit raw UTF-16 variants such as `match_js`,
`match_all_js`, `split_js`, `replace_js`, and `escape_js`.

These functions model RegExp semantics directly. They do not implement
JavaScript object dispatch, constructors, prototype mutation, function objects,
or dynamic method lookup.

## Stateful RegExp Instances

Use `instance` when code needs ECMAScript `lastIndex` behavior:

```ocaml
let flags = Ecma_regex.flags ~global:true () in
let re = Result.get_ok (Ecma_regex.compile ~flags "a") in
let instance = Ecma_regex.instance re

let first = Ecma_regex.exec_instance instance "banana"
let next_index = Ecma_regex.last_index instance
```

Global and sticky regexps update or reset `lastIndex` according to ECMAScript
matching rules. Stateless regexps ignore stored `lastIndex`.

## Compatibility Evidence

The implementation is tested against:

- ECMA-262 RegExp requirement matrices,
- extracted `test262` RegExp cases,
- Unicode Character Database 16.0.0 generated cases,
- JSON-Schema-Test-Suite regex-facing cases,
- focused raw UTF-16 ECMAScript String matrices,
- local exact tests for specification rows that external corpora do not cover.

Generated corpora and working evidence files are development artifacts, not
part of the public API.

Default package tests are self-contained and run from a clean opam source
archive:

```sh
opam exec -- dune runtest
```

Full local evidence tests require prepared `cache/` outputs and downloaded
`external/` corpora:

```sh
opam exec -- dune build @runtest @test/evidence
```

Formal conformance documentation:

- [`NORMATIVE_HIERARCHY.md`](NORMATIVE_HIERARCHY.md)
- [`SPEC_CONFORMANCE.md`](SPEC_CONFORMANCE.md)
- [`NORMATIVE_TEST_MATRIX.md`](NORMATIVE_TEST_MATRIX.md)
- [`TEST_EVIDENCE_AUDIT.md`](TEST_EVIDENCE_AUDIT.md)
- [`DEVIATION_REGISTER.md`](DEVIATION_REGISTER.md)

Release history:

- [`CHANGES.md`](CHANGES.md)
