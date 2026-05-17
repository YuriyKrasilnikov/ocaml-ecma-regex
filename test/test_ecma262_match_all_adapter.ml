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

let match_all_clause row =
  field "clause_id" row = "22.1.3.14"
  || field "clause_id" row = "22.2.6.9"

let match_all_adapter_rows =
  List.filter
    (fun row ->
       match_all_clause row
       && field "surface_decision" row = "ocaml_adapter_requirement")
    product_rows

let match_all_nonapp_rows =
  List.filter
    (fun row ->
       match_all_clause row
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

let texts_of_match_results results =
  List.map (fun result -> result.Ecma_regex.matched_text) results

let starts_of_match_results results =
  List.map (fun result -> result.Ecma_regex.start_index) results

let js_text_units_of_match_results results =
  List.map
    (fun result ->
       Ecma_regex.js_string_to_utf16_code_units
         result.Ecma_regex.js_matched_text)
    results

let js_starts_of_match_results results =
  List.map (fun result -> result.Ecma_regex.js_start_index) results

let js_capture_units capture =
  Option.map Ecma_regex.js_string_to_utf16_code_units
    capture.Ecma_regex.js_capture_text

let test_product_surface_match_all_rows () =
  check_ids
    "matchAll adapter rows"
    [ "ecma262-22.1.3.14-0001"
    ; "ecma262-22.1.3.14-0002"
    ; "ecma262-22.1.3.14-0003"
    ; "ecma262-22.1.3.14-0014"
    ; "ecma262-22.1.3.14-0016"
    ; "ecma262-22.2.6.9-0001"
    ; "ecma262-22.2.6.9-0002"
    ; "ecma262-22.2.6.9-0004"
    ; "ecma262-22.2.6.9-0006"
    ; "ecma262-22.2.6.9-0008"
    ; "ecma262-22.2.6.9-0009"
    ; "ecma262-22.2.6.9-0010"
    ; "ecma262-22.2.6.9-0011"
    ; "ecma262-22.2.6.9-0012"
    ; "ecma262-22.2.6.9-0013"
    ; "ecma262-22.2.6.9-0014"
    ]
    match_all_adapter_rows;
  check_ids
    "matchAll non-applicable rows"
    [ "ecma262-22.1.3.14-0004"
    ; "ecma262-22.1.3.14-0005"
    ; "ecma262-22.1.3.14-0006"
    ; "ecma262-22.1.3.14-0007"
    ; "ecma262-22.1.3.14-0008"
    ; "ecma262-22.1.3.14-0009"
    ; "ecma262-22.1.3.14-0010"
    ; "ecma262-22.1.3.14-0011"
    ; "ecma262-22.1.3.14-0012"
    ; "ecma262-22.1.3.14-0013"
    ; "ecma262-22.1.3.14-0015"
    ; "ecma262-22.2.6.9-0003"
    ; "ecma262-22.2.6.9-0005"
    ; "ecma262-22.2.6.9-0007"
    ; "ecma262-22.2.6.9-0015"
    ]
    match_all_nonapp_rows;
  List.iter
    (fun row ->
       Alcotest.(check string)
         "matchAll adapter artifact"
         "Ecma_regex.match_all"
         (field "ocaml_artifact" row);
       Alcotest.(check string)
         "matchAll adapter test artifact"
         "test/test_ecma262_match_all_adapter.ml"
         (field "next_test_artifact" row);
       Alcotest.(check string)
         "matchAll adapter public API status"
         "current_public_api"
         (field "public_api_status" row))
    match_all_adapter_rows;
  List.iter
    (fun row ->
       Alcotest.(check string)
         "matchAll JS protocol artifact"
         "none"
         (field "ocaml_artifact" row);
       Alcotest.(check string)
         "matchAll JS protocol status"
         "not_ocaml_surface"
         (field "public_api_status" row))
    match_all_nonapp_rows

let test_match_all_non_global_yields_first_result_or_empty () =
  let regexp = compile_or_fail "a" in
  Alcotest.(check (list string)) "non-global text" [ "a" ]
    (Ecma_regex.match_all regexp "banana" |> texts_of_match_results);
  Alcotest.(check (list int)) "non-global start" [ 1 ]
    (Ecma_regex.match_all regexp "banana" |> starts_of_match_results);
  Alcotest.(check (list string)) "no matches" []
    (Ecma_regex.match_all regexp "xyz" |> texts_of_match_results)

let test_match_all_global_collects_all_results () =
  let flags = flags_or_fail "g" in
  let regexp = compile_or_fail ~flags "a" in
  Alcotest.(check (list string)) "global texts" [ "a"; "a"; "a" ]
    (Ecma_regex.match_all regexp "banana" |> texts_of_match_results);
  Alcotest.(check (list int)) "global starts" [ 1; 3; 5 ]
    (Ecma_regex.match_all regexp "banana" |> starts_of_match_results)

let test_match_all_global_empty_advances_with_unicode_semantics () =
  let flags = flags_or_fail "gu" in
  let regexp = compile_or_fail ~flags "" in
  let non_bmp = "\xF0\x9F\x98\x80" in
  Alcotest.(check (list int)) "empty unicode starts" [ 0; 2; 3 ]
    (Ecma_regex.match_all regexp (non_bmp ^ "a") |> starts_of_match_results)

let test_match_all_instance_clones_last_index () =
  let flags = flags_or_fail "g" in
  let regexp = compile_or_fail ~flags "a" in
  let instance = Ecma_regex.instance regexp in
  Ecma_regex.set_last_index instance 3;
  Alcotest.(check (list int)) "global clone starts from lastIndex" [ 3; 5 ]
    (Ecma_regex.match_all_instance instance "banana" |> starts_of_match_results);
  Alcotest.(check int) "original lastIndex preserved" 3
    (Ecma_regex.last_index instance)

let test_match_all_instance_non_global_sticky_uses_last_index () =
  let flags = flags_or_fail "y" in
  let regexp = compile_or_fail ~flags "b" in
  let instance = Ecma_regex.instance regexp in
  Ecma_regex.set_last_index instance 1;
  Alcotest.(check (list int)) "sticky clone match at lastIndex" [ 1 ]
    (Ecma_regex.match_all_instance instance "ab" |> starts_of_match_results);
  Alcotest.(check int) "sticky original lastIndex preserved" 1
    (Ecma_regex.last_index instance);
  Ecma_regex.set_last_index instance 0;
  Alcotest.(check (list int)) "sticky clone mismatch" []
    (Ecma_regex.match_all_instance instance "ab" |> starts_of_match_results);
  Alcotest.(check int) "sticky mismatch preserves original lastIndex" 0
    (Ecma_regex.last_index instance)

let test_match_all_js_returns_raw_utf16_slices () =
  let flags = flags_or_fail "gu" in
  let high = 0xD83D in
  let low = 0xDE00 in
  let input =
    js_string_of_utf16_units_or_fail
      [ high; low; Char.code 'a'; high; low ]
  in
  let regexp = compile_or_fail ~flags "." in
  Alcotest.(check (list (list int))) "JS match units"
    [ [ high; low ]; [ Char.code 'a' ]; [ high; low ] ]
    (Ecma_regex.match_all_js regexp input |> js_text_units_of_match_results);
  Alcotest.(check (list int)) "JS match starts" [ 0; 2; 3 ]
    (Ecma_regex.match_all_js regexp input |> js_starts_of_match_results)

let test_match_all_js_global_exposes_raw_capture_slices () =
  let flags = flags_or_fail "gu" in
  let high = 0xD83D in
  let low = 0xDE00 in
  let input =
    js_string_of_utf16_units_or_fail
      [ high; low; Char.code 'a'; high; low; Char.code 'b' ]
  in
  let regexp = compile_or_fail ~flags "(\\u{1F600})(?<tail>[ab])" in
  let results = Ecma_regex.match_all_js regexp input in
  Alcotest.(check (list int)) "match starts" [ 0; 3 ]
    (js_starts_of_match_results results);
  Alcotest.(check (list (list int))) "match units"
    [ [ high; low; Char.code 'a' ]; [ high; low; Char.code 'b' ] ]
    (js_text_units_of_match_results results);
  let first = List.nth results 0 in
  let second = List.nth results 1 in
  Alcotest.(check (option (list int))) "first pair capture"
    (Some [ high; low ])
    (js_capture_units (List.nth first.Ecma_regex.js_captures 0));
  Alcotest.(check (option (list int))) "first named tail"
    (Some [ Char.code 'a' ])
    (js_capture_units
       (List.hd first.Ecma_regex.js_named_captures).Ecma_regex.js_named_capture);
  Alcotest.(check (option (list int))) "second pair capture"
    (Some [ high; low ])
    (js_capture_units (List.nth second.Ecma_regex.js_captures 0));
  Alcotest.(check (option (list int))) "second named tail"
    (Some [ Char.code 'b' ])
    (js_capture_units
       (List.hd second.Ecma_regex.js_named_captures).Ecma_regex.js_named_capture)

let test_match_all_js_empty_advances_over_raw_surrogate_pair () =
  let flags = flags_or_fail "gu" in
  let high = 0xD83D in
  let low = 0xDE00 in
  let input =
    js_string_of_utf16_units_or_fail [ high; low; Char.code 'a' ]
  in
  let regexp = compile_or_fail ~flags "" in
  let results = Ecma_regex.match_all_js regexp input in
  Alcotest.(check (list int)) "empty match starts" [ 0; 2; 3 ]
    (js_starts_of_match_results results);
  Alcotest.(check (list (list int))) "empty match units" [ []; []; [] ]
    (js_text_units_of_match_results results)

let test_match_all_instance_js_clones_last_index () =
  let flags = flags_or_fail "gu" in
  let high = 0xD83D in
  let low = 0xDE00 in
  let input =
    js_string_of_utf16_units_or_fail
      [ high; low; Char.code 'a'; high; low ]
  in
  let instance = Ecma_regex.instance (compile_or_fail ~flags ".") in
  Ecma_regex.set_last_index instance 2;
  Alcotest.(check (list int)) "JS clone starts from lastIndex" [ 2; 3 ]
    (Ecma_regex.match_all_instance_js instance input
     |> js_starts_of_match_results);
  Alcotest.(check int) "JS original lastIndex preserved" 2
    (Ecma_regex.last_index instance)

let () =
  Alcotest.run
    "ecma262-match-all-adapter"
    [ ( "manifest"
      , [ Alcotest.test_case
            "product-surface matchAll rows"
            `Quick
            test_product_surface_match_all_rows
        ] )
    ; ( "adapter semantics"
      , [ Alcotest.test_case
            "match_all non-global yields first result or empty"
            `Quick
            test_match_all_non_global_yields_first_result_or_empty
        ; Alcotest.test_case
            "match_all global collects all results"
            `Quick
            test_match_all_global_collects_all_results
        ; Alcotest.test_case
            "match_all global empty advances with unicode semantics"
            `Quick
            test_match_all_global_empty_advances_with_unicode_semantics
        ; Alcotest.test_case
            "match_all_instance clones lastIndex"
            `Quick
            test_match_all_instance_clones_last_index
        ; Alcotest.test_case
            "match_all_instance non-global sticky uses lastIndex"
            `Quick
            test_match_all_instance_non_global_sticky_uses_last_index
        ; Alcotest.test_case
            "match_all_js returns raw UTF-16 slices"
            `Quick
            test_match_all_js_returns_raw_utf16_slices
        ; Alcotest.test_case
            "match_all_js global exposes raw capture slices"
            `Quick
            test_match_all_js_global_exposes_raw_capture_slices
        ; Alcotest.test_case
            "match_all_js empty advances over raw surrogate pair"
            `Quick
            test_match_all_js_empty_advances_over_raw_surrogate_pair
        ; Alcotest.test_case
            "match_all_instance_js clones lastIndex"
            `Quick
            test_match_all_instance_js_clones_last_index
        ] )
    ]
