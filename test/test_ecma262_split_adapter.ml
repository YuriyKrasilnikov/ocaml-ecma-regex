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

let split_clause row =
  field "clause_id" row = "22.1.3.23"
  || field "clause_id" row = "22.2.6.14"

let split_adapter_rows =
  List.filter
    (fun row ->
       split_clause row
       && field "surface_decision" row = "ocaml_adapter_requirement")
    product_rows

let split_nonapp_rows =
  List.filter
    (fun row ->
       split_clause row
       && field "surface_decision" row = "non_applicable_with_reason")
    product_rows

let compile_or_fail ?flags pattern =
  match Ecma_regex.compile ?flags pattern with
  | Ok regexp -> regexp
  | Error msg -> Alcotest.failf "compile %S failed: %s" pattern msg

let flags_or_fail source =
  match Ecma_regex.flags_of_string source with
  | Ok flags -> flags
  | Error msg -> Alcotest.failf "flags %S failed: %s" source msg

let js_string_of_utf16_units_or_fail units =
  match Ecma_regex.js_string_of_utf16_code_units units with
  | Ok value -> value
  | Error msg -> Alcotest.failf "js_string_of_utf16_code_units failed: %s" msg

let check_ids name expected rows =
  let actual = rows |> List.map (field "requirement_id") |> List.sort String.compare in
  Alcotest.(check (list string)) name expected actual

let render_split_part = function
  | Ecma_regex.Split_text text -> "text:" ^ text
  | Ecma_regex.Split_capture None -> "capture:<undefined>"
  | Ecma_regex.Split_capture (Some text) -> "capture:" ^ text

let render_split_parts parts = List.map render_split_part parts

let render_units units =
  "[" ^ String.concat "," (List.map string_of_int units) ^ "]"

let render_js_split_part = function
  | Ecma_regex.Js_split_text text ->
    "text:" ^ render_units (Ecma_regex.js_string_to_utf16_code_units text)
  | Ecma_regex.Js_split_capture None -> "capture:<undefined>"
  | Ecma_regex.Js_split_capture (Some text) ->
    "capture:" ^ render_units (Ecma_regex.js_string_to_utf16_code_units text)

let render_js_split_parts parts = List.map render_js_split_part parts

let test_product_surface_split_rows () =
  check_ids
    "split adapter rows"
    [ "ecma262-22.1.3.23-0001"
    ; "ecma262-22.1.3.23-0002"
    ; "ecma262-22.1.3.23-0003"
    ; "ecma262-22.2.6.14-0001"
    ; "ecma262-22.2.6.14-0002"
    ; "ecma262-22.2.6.14-0004"
    ; "ecma262-22.2.6.14-0006"
    ; "ecma262-22.2.6.14-0007"
    ; "ecma262-22.2.6.14-0008"
    ; "ecma262-22.2.6.14-0009"
    ; "ecma262-22.2.6.14-0010"
    ; "ecma262-22.2.6.14-0012"
    ; "ecma262-22.2.6.14-0013"
    ; "ecma262-22.2.6.14-0014"
    ; "ecma262-22.2.6.14-0015"
    ; "ecma262-22.2.6.14-0016"
    ; "ecma262-22.2.6.14-0017"
    ; "ecma262-22.2.6.14-0018"
    ; "ecma262-22.2.6.14-0019"
    ; "ecma262-22.2.6.14-0020"
    ; "ecma262-22.2.6.14-0021"
    ; "ecma262-22.2.6.14-0022"
    ; "ecma262-22.2.6.14-0023"
    ; "ecma262-22.2.6.14-0024"
    ; "ecma262-22.2.6.14-0025"
    ; "ecma262-22.2.6.14-0026"
    ; "ecma262-22.2.6.14-0027"
    ; "ecma262-22.2.6.14-0028"
    ; "ecma262-22.2.6.14-0029"
    ; "ecma262-22.2.6.14-0030"
    ; "ecma262-22.2.6.14-0031"
    ; "ecma262-22.2.6.14-0032"
    ; "ecma262-22.2.6.14-0033"
    ; "ecma262-22.2.6.14-0034"
    ; "ecma262-22.2.6.14-0035"
    ; "ecma262-22.2.6.14-0036"
    ; "ecma262-22.2.6.14-0037"
    ; "ecma262-22.2.6.14-0038"
    ; "ecma262-22.2.6.14-0039"
    ; "ecma262-22.2.6.14-0040"
    ; "ecma262-22.2.6.14-0041"
    ; "ecma262-22.2.6.14-0042"
    ; "ecma262-22.2.6.14-0043"
    ; "ecma262-22.2.6.14-0044"
    ; "ecma262-22.2.6.14-0045"
    ; "ecma262-22.2.6.14-0046"
    ; "ecma262-22.2.6.14-0047"
    ; "ecma262-22.2.6.14-0048"
    ; "ecma262-22.2.6.14-0049"
    ; "ecma262-22.2.6.14-0050"
    ; "ecma262-22.2.6.14-0051"
    ; "ecma262-22.2.6.14-0052"
    ]
    split_adapter_rows;
  check_ids
    "split non-applicable rows"
    [ "ecma262-22.1.3.23-0004"
    ; "ecma262-22.1.3.23-0005"
    ; "ecma262-22.1.3.23-0006"
    ; "ecma262-22.1.3.23-0007"
    ; "ecma262-22.1.3.23-0008"
    ; "ecma262-22.1.3.23-0009"
    ; "ecma262-22.1.3.23-0010"
    ; "ecma262-22.1.3.23-0011"
    ; "ecma262-22.1.3.23-0012"
    ; "ecma262-22.1.3.23-0013"
    ; "ecma262-22.1.3.23-0014"
    ; "ecma262-22.1.3.23-0015"
    ; "ecma262-22.1.3.23-0016"
    ; "ecma262-22.1.3.23-0017"
    ; "ecma262-22.1.3.23-0018"
    ; "ecma262-22.1.3.23-0019"
    ; "ecma262-22.1.3.23-0020"
    ; "ecma262-22.1.3.23-0021"
    ; "ecma262-22.1.3.23-0022"
    ; "ecma262-22.1.3.23-0023"
    ; "ecma262-22.1.3.23-0024"
    ; "ecma262-22.1.3.23-0025"
    ; "ecma262-22.1.3.23-0026"
    ; "ecma262-22.1.3.23-0027"
    ; "ecma262-22.1.3.23-0028"
    ; "ecma262-22.1.3.23-0029"
    ; "ecma262-22.1.3.23-0030"
    ; "ecma262-22.1.3.23-0031"
    ; "ecma262-22.1.3.23-0032"
    ; "ecma262-22.1.3.23-0033"
    ; "ecma262-22.1.3.23-0034"
    ; "ecma262-22.1.3.23-0035"
    ; "ecma262-22.2.6.14-0003"
    ; "ecma262-22.2.6.14-0005"
    ; "ecma262-22.2.6.14-0011"
    ; "ecma262-22.2.6.14-0053"
    ]
    split_nonapp_rows;
  List.iter
    (fun row ->
       Alcotest.(check string)
         "split adapter artifact"
         "Ecma_regex.split"
         (field "ocaml_artifact" row);
       Alcotest.(check string)
         "split adapter test artifact"
         "test/test_ecma262_split_adapter.ml"
         (field "next_test_artifact" row);
       Alcotest.(check string)
         "split adapter public API status"
         "current_public_api"
         (field "public_api_status" row))
    split_adapter_rows;
  List.iter
    (fun row ->
       Alcotest.(check string)
         "split JS protocol artifact"
         "none"
         (field "ocaml_artifact" row);
       Alcotest.(check string)
         "split JS protocol status"
         "not_ocaml_surface"
         (field "public_api_status" row))
    split_nonapp_rows

let test_split_returns_substrings_and_respects_limit () =
  let regexp = compile_or_fail "," in
  Alcotest.(check (list string)) "split parts"
    [ "text:a"; "text:b"; "text:c" ]
    (Ecma_regex.split regexp "a,b,c" |> render_split_parts);
  Alcotest.(check (list string)) "no match keeps whole input"
    [ "text:abc" ]
    (Ecma_regex.split regexp "abc" |> render_split_parts);
  Alcotest.(check (list string)) "limit zero" []
    (Ecma_regex.split ~limit:0 regexp "a,b,c" |> render_split_parts);
  Alcotest.(check (list string)) "limit two"
    [ "text:a"; "text:b" ]
    (Ecma_regex.split ~limit:2 regexp "a,b,c" |> render_split_parts)

let test_split_empty_input_uses_regexp_exec_result () =
  Alcotest.(check (list string)) "empty input no regexp match"
    [ "text:" ]
    (Ecma_regex.split (compile_or_fail "a") "" |> render_split_parts);
  Alcotest.(check (list string)) "empty input regexp match" []
    (Ecma_regex.split (compile_or_fail "") "" |> render_split_parts)

let test_split_empty_matches_advance_with_unicode_semantics () =
  let flags = flags_or_fail "u" in
  let regexp = compile_or_fail ~flags "" in
  let non_bmp = "\xF0\x9F\x98\x80" in
  Alcotest.(check (list string)) "unicode empty split"
    [ "text:" ^ non_bmp; "text:a" ]
    (Ecma_regex.split regexp (non_bmp ^ "a") |> render_split_parts)

let test_split_inserts_numbered_captures_and_undefined_captures () =
  let capture_separator = compile_or_fail "(,)" in
  Alcotest.(check (list string)) "defined capture insertion"
    [ "text:a"; "capture:,"; "text:b"; "capture:,"; "text:c" ]
    (Ecma_regex.split capture_separator "a,b,c" |> render_split_parts);
  let alternate_capture = compile_or_fail "(-)|(,)" in
  Alcotest.(check (list string)) "undefined capture insertion"
    [ "text:a"; "capture:<undefined>"; "capture:,"; "text:b" ]
    (Ecma_regex.split alternate_capture "a,b" |> render_split_parts)

let test_split_instance_uses_fresh_sticky_splitter_without_mutating_receiver () =
  let flags = flags_or_fail "g" in
  let instance = Ecma_regex.instance (compile_or_fail ~flags ",") in
  Ecma_regex.set_last_index instance 2;
  Alcotest.(check (list string)) "instance split ignores receiver lastIndex"
    [ "text:a"; "text:b"; "text:c" ]
    (Ecma_regex.split_instance instance "a,b,c" |> render_split_parts);
  Alcotest.(check int) "receiver lastIndex preserved" 2
    (Ecma_regex.last_index instance)

let test_split_js_preserves_raw_utf16_slices () =
  let flags = flags_or_fail "u" in
  let high = 0xD83D in
  let low = 0xDE00 in
  let input =
    js_string_of_utf16_units_or_fail [ high; low; Char.code 'a' ]
  in
  let regexp = compile_or_fail ~flags "" in
  Alcotest.(check (list string)) "JS unicode empty split units"
    [ "text:[55357,56832]"; "text:[97]" ]
    (Ecma_regex.split_js regexp input |> render_js_split_parts);
  let capture_separator = compile_or_fail "(,)" in
  let comma_input =
    js_string_of_utf16_units_or_fail [ Char.code 'a'; Char.code ','; high; low ]
  in
  Alcotest.(check (list string)) "JS capture units"
    [ "text:[97]"; "capture:[44]"; "text:[55357,56832]" ]
    (Ecma_regex.split_js capture_separator comma_input |> render_js_split_parts)

let () =
  Alcotest.run
    "ecma262-split-adapter"
    [ ( "manifest"
      , [ Alcotest.test_case
            "product-surface split rows"
            `Quick
            test_product_surface_split_rows
        ] )
    ; ( "adapter semantics"
      , [ Alcotest.test_case
            "split returns substrings and respects limit"
            `Quick
            test_split_returns_substrings_and_respects_limit
        ; Alcotest.test_case
            "split empty input uses RegExpExec result"
            `Quick
            test_split_empty_input_uses_regexp_exec_result
        ; Alcotest.test_case
            "split empty matches advance with Unicode semantics"
            `Quick
            test_split_empty_matches_advance_with_unicode_semantics
        ; Alcotest.test_case
            "split inserts captures"
            `Quick
            test_split_inserts_numbered_captures_and_undefined_captures
        ; Alcotest.test_case
            "split instance preserves receiver"
            `Quick
            test_split_instance_uses_fresh_sticky_splitter_without_mutating_receiver
        ; Alcotest.test_case
            "split_js preserves raw UTF-16 slices"
            `Quick
            test_split_js_preserves_raw_utf16_slices
        ] )
    ]
