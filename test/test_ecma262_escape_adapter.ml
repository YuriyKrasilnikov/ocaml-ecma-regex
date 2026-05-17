let repo_root () =
  let cwd = Sys.getcwd () in
  let rec climb dir =
    let candidate =
      Filename.concat dir "cache/ecma262-regexp-product-surface-matrix.tsv"
    in
    if Sys.file_exists candidate then dir
    else
      let parent = Filename.dirname dir in
      if parent = dir then
        Alcotest.fail
          "cache/ecma262-regexp-product-surface-matrix.tsv is missing; run \
           tools/build_ecma262_regexp_product_surface_matrix.py"
      else climb parent
  in
  climb cwd

let path segments = List.fold_left Filename.concat (repo_root ()) segments

let strip_trailing_cr value =
  let length = String.length value in
  if length > 0 && value.[length - 1] = '\r' then
    String.sub value 0 (length - 1)
  else value

let split_tsv_line line = line |> strip_trailing_cr |> String.split_on_char '\t'

let pad_to width fields =
  let rec loop fields =
    if List.length fields >= width then fields else loop (fields @ [ "" ])
  in
  loop fields

let read_tsv rel =
  let file = path rel in
  let ic = open_in file in
  Fun.protect
    ~finally:(fun () -> close_in_noerr ic)
    (fun () ->
       let header = split_tsv_line (input_line ic) in
       let width = List.length header in
       let rec rows acc =
         match input_line ic with
         | line ->
           let fields = split_tsv_line line |> pad_to width in
           let row = List.combine header fields in
           rows (row :: acc)
         | exception End_of_file -> List.rev acc
       in
       rows [])

let field name row =
  match List.assoc_opt name row with
  | Some value -> value
  | None -> Alcotest.failf "missing TSV field %s" name

let product_rows =
  read_tsv [ "cache"; "ecma262-regexp-product-surface-matrix.tsv" ]

let escape_clause row =
  field "clause_id" row = "22.2.5.1"
  || field "clause_id" row = "22.2.5.1.1"

let escape_adapter_rows =
  List.filter
    (fun row ->
       escape_clause row
       && field "surface_decision" row = "ocaml_adapter_requirement")
    product_rows

let escape_nonapp_rows =
  List.filter
    (fun row ->
       escape_clause row
       && field "surface_decision" row = "non_applicable_with_reason")
    product_rows

let compile_or_fail pattern =
  match Ecma_regex.compile pattern with
  | Ok regexp -> regexp
  | Error msg -> Alcotest.failf "compile %S failed: %s" pattern msg

let js_string_of_utf16_units_or_fail units =
  match Ecma_regex.js_string_of_utf16_code_units units with
  | Ok value -> value
  | Error msg -> Alcotest.failf "js_string_of_utf16_code_units failed: %s" msg

let check_ids name expected rows =
  let actual = rows |> List.map (field "requirement_id") |> List.sort String.compare in
  Alcotest.(check (list string)) name expected actual

let check_escape name expected input =
  Alcotest.(check string) name expected (Ecma_regex.escape input)

let check_escape_js_units name expected input_units =
  let escaped =
    input_units
    |> js_string_of_utf16_units_or_fail
    |> Ecma_regex.escape_js
    |> Ecma_regex.js_string_to_utf16_code_units
  in
  Alcotest.(check (list int)) name expected escaped

let ascii_units value =
  List.init (String.length value) (fun index -> Char.code value.[index])

let test_product_surface_escape_rows () =
  check_ids
    "escape adapter rows"
    [ "ecma262-22.2.5.1-0001"
    ; "ecma262-22.2.5.1-0002"
    ; "ecma262-22.2.5.1-0004"
    ; "ecma262-22.2.5.1-0005"
    ; "ecma262-22.2.5.1-0006"
    ; "ecma262-22.2.5.1-0007"
    ; "ecma262-22.2.5.1-0008"
    ; "ecma262-22.2.5.1-0009"
    ; "ecma262-22.2.5.1-0010"
    ; "ecma262-22.2.5.1-0011"
    ; "ecma262-22.2.5.1-0012"
    ; "ecma262-22.2.5.1-0013"
    ; "ecma262-22.2.5.1-0014"
    ; "ecma262-22.2.5.1-0015"
    ; "ecma262-22.2.5.1.1-0001"
    ; "ecma262-22.2.5.1.1-0002"
    ; "ecma262-22.2.5.1.1-0003"
    ; "ecma262-22.2.5.1.1-0004"
    ; "ecma262-22.2.5.1.1-0005"
    ; "ecma262-22.2.5.1.1-0006"
    ; "ecma262-22.2.5.1.1-0007"
    ; "ecma262-22.2.5.1.1-0008"
    ; "ecma262-22.2.5.1.1-0009"
    ; "ecma262-22.2.5.1.1-0010"
    ; "ecma262-22.2.5.1.1-0011"
    ; "ecma262-22.2.5.1.1-0012"
    ; "ecma262-22.2.5.1.1-0013"
    ; "ecma262-22.2.5.1.1-0014"
    ; "ecma262-22.2.5.1.1-0015"
    ; "ecma262-22.2.5.1.1-0016"
    ; "ecma262-22.2.5.1.1-0017"
    ; "ecma262-22.2.5.1.1-0018"
    ]
    escape_adapter_rows;
  check_ids
    "escape non-applicable rows"
    [ "ecma262-22.2.5.1-0003" ]
    escape_nonapp_rows;
  List.iter
    (fun row ->
       Alcotest.(check string)
         "escape adapter artifact"
         "Ecma_regex.escape"
         (field "ocaml_artifact" row);
       Alcotest.(check string)
         "escape adapter test artifact"
         "test/test_ecma262_escape_adapter.ml"
         (field "next_test_artifact" row);
       Alcotest.(check string)
         "escape adapter public API status"
         "current_public_api"
         (field "public_api_status" row))
    escape_adapter_rows;
  List.iter
    (fun row ->
       Alcotest.(check string)
         "escape JS type protocol artifact"
         "none"
         (field "ocaml_artifact" row);
       Alcotest.(check string)
         "escape JS type protocol status"
         "not_ocaml_surface"
         (field "public_api_status" row))
    escape_nonapp_rows

let test_escape_leading_ascii_alnum_and_plain_chars () =
  check_escape "empty string" "" "";
  check_escape "leading lowercase ASCII letter" "\\x61bc" "abc";
  check_escape "leading uppercase ASCII letter" "\\x41bc" "Abc";
  check_escape "leading decimal digit" "\\x31a" "1a";
  check_escape "non-leading ASCII letter is literal" "_a" "_a";
  check_escape "escaped first char does not force following letter" "\\x2da" "-a"

let test_escape_syntax_characters_and_solidus () =
  List.iter
    (fun (input, expected) -> check_escape ("syntax " ^ input) expected input)
    [ "^", "\\^"
    ; "$", "\\$"
    ; "\\", "\\\\"
    ; ".", "\\."
    ; "*", "\\*"
    ; "+", "\\+"
    ; "?", "\\?"
    ; "(", "\\("
    ; ")", "\\)"
    ; "[", "\\["
    ; "]", "\\]"
    ; "{", "\\{"
    ; "}", "\\}"
    ; "|", "\\|"
    ; "/", "\\/"
    ]

let test_escape_control_escape_table () =
  List.iter
    (fun (name, input, expected) -> check_escape name expected input)
    [ "form feed", "\012", "\\f"
    ; "line feed", "\n", "\\n"
    ; "carriage return", "\r", "\\r"
    ; "tab", "\t", "\\t"
    ; "vertical tab", "\011", "\\v"
    ]

let test_escape_other_punctuators_and_whitespace () =
  List.iter
    (fun (input, expected) -> check_escape ("punctuator " ^ input) expected input)
    [ ",", "\\x2c"
    ; "-", "\\x2d"
    ; "=", "\\x3d"
    ; "<", "\\x3c"
    ; ">", "\\x3e"
    ; "#", "\\x23"
    ; "&", "\\x26"
    ; "!", "\\x21"
    ; "%", "\\x25"
    ; ":", "\\x3a"
    ; ";", "\\x3b"
    ; "@", "\\x40"
    ; "~", "\\x7e"
    ; "'", "\\x27"
    ; "`", "\\x60"
    ; "\"", "\\x22"
    ];
  check_escape "space" "\\x20" " ";
  check_escape "no-break space" "\\xa0" "\194\160";
  check_escape "ogham space mark" "\\u1680" "\225\154\128";
  check_escape "en quad" "\\u2000" "\226\128\128";
  check_escape "hair space" "\\u200a" "\226\128\138";
  check_escape "line separator" "\\u2028" "\226\128\168";
  check_escape "paragraph separator" "\\u2029" "\226\128\169";
  check_escape "narrow no-break space" "\\u202f" "\226\128\175";
  check_escape "medium mathematical space" "\\u205f" "\226\129\159";
  check_escape "ideographic space" "\\u3000" "\227\128\128";
  check_escape "byte order mark" "\\ufeff" "\239\187\191";
  check_escape "snowman is literal" "\226\152\131" "\226\152\131";
  check_escape "non-BMP scalar is literal" "\240\159\152\128" "\240\159\152\128"

let test_escape_result_is_usable_pattern_text () =
  let input = "a+b/c[d]" in
  let escaped = Ecma_regex.escape input in
  let regexp = compile_or_fail ("^" ^ escaped ^ "$") in
  Alcotest.(check bool) "escaped pattern matches original" true
    (Ecma_regex.search regexp input);
  Alcotest.(check bool) "escaped pattern rejects different text" false
    (Ecma_regex.search regexp "aXb/c[d]")

let test_escape_js_preserves_raw_utf16_semantics () =
  let high = 0xD83D in
  let low = 0xDE00 in
  check_escape_js_units "lone high surrogate"
    (ascii_units "\\ud83d")
    [ high ];
  check_escape_js_units "lone low surrogate"
    (ascii_units "\\ude00")
    [ low ];
  check_escape_js_units "valid pair remains a pair"
    [ high; low ]
    [ high; low ];
  check_escape_js_units "leading alnum plus lone surrogate"
    (ascii_units "\\x61\\ud83d")
    [ Char.code 'a'; high ];
  check_escape_js_units "pair then escaped punctuation"
    ([ high; low ] @ ascii_units "\\x21")
    [ high; low; Char.code '!' ]

let () =
  Alcotest.run
    "ecma262-escape-adapter"
    [ ( "manifest"
      , [ Alcotest.test_case
            "product-surface escape rows"
            `Quick
            test_product_surface_escape_rows
        ] )
    ; ( "adapter semantics"
      , [ Alcotest.test_case
            "leading ASCII alnum and plain chars"
            `Quick
            test_escape_leading_ascii_alnum_and_plain_chars
        ; Alcotest.test_case
            "syntax characters and solidus"
            `Quick
            test_escape_syntax_characters_and_solidus
        ; Alcotest.test_case
            "control escape table"
            `Quick
            test_escape_control_escape_table
        ; Alcotest.test_case
            "other punctuators and whitespace"
            `Quick
            test_escape_other_punctuators_and_whitespace
        ; Alcotest.test_case
            "result is usable pattern text"
            `Quick
            test_escape_result_is_usable_pattern_text
        ; Alcotest.test_case
            "escape_js preserves raw UTF-16 semantics"
            `Quick
            test_escape_js_preserves_raw_utf16_semantics
        ] )
    ]
