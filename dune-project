(lang dune 3.17)

(name ecma-regex)

(generate_opam_files true)

(license ISC)

(authors "Yuriy Krasilnikov")

(maintainers "Yuriy Krasilnikov")

(source (github YuriyKrasilnikov/ocaml-ecma-regex))

(homepage "https://github.com/YuriyKrasilnikov/ocaml-ecma-regex")

(bug_reports "https://github.com/YuriyKrasilnikov/ocaml-ecma-regex/issues")

(package
 (name ecma-regex)
 (synopsis "ECMAScript regular expressions for OCaml")
 (description
  "Library for ECMAScript regular-expression syntax and matching semantics
   for OCaml, including Unicode property escapes, raw UTF-16 ECMAScript String
   APIs, and JSON Schema regex compatibility evidence.")
 (depends
  (ocaml (>= 5.1))
  (alcotest :with-test)
  (yojson :with-test)))
