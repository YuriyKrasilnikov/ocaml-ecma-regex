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

let match_clause row =
  field "clause_id" row = "22.1.3.13"
  || field "clause_id" row = "22.2.6.8"

let match_adapter_rows =
  List.filter
    (fun row ->
       match_clause row
       && field "surface_decision" row = "ocaml_adapter_requirement")
    product_rows

let match_nonapp_rows =
  List.filter
    (fun row ->
       match_clause row
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

let texts_of_match_results = function
  | None -> None
  | Some results -> Some (List.map (fun result -> result.Ecma_regex.matched_text) results)

let starts_of_match_results = function
  | None -> None
  | Some results -> Some (List.map (fun result -> result.Ecma_regex.start_index) results)

let js_text_units_of_match_results = function
  | None -> None
  | Some results ->
    Some
      (List.map
         (fun result ->
            Ecma_regex.js_string_to_utf16_code_units
              result.Ecma_regex.js_matched_text)
         results)

let js_starts_of_match_results = function
  | None -> None
  | Some results -> Some (List.map (fun result -> result.Ecma_regex.js_start_index) results)

let js_capture_units capture =
  Option.map Ecma_regex.js_string_to_utf16_code_units
    capture.Ecma_regex.js_capture_text

let single_js_match_result_or_fail = function
  | Some [ result ] -> result
  | None -> Alcotest.fail "expected one JS match result, got none"
  | Some results ->
    Alcotest.failf "expected one JS match result, got %d" (List.length results)

let test_product_surface_match_rows () =
  check_ids
    "match adapter rows"
    [ "ecma262-22.1.3.13-0001"
    ; "ecma262-22.1.3.13-0002"
    ; "ecma262-22.1.3.13-0008"
    ; "ecma262-22.1.3.13-0010"
    ; "ecma262-22.2.6.8-0001"
    ; "ecma262-22.2.6.8-0002"
    ; "ecma262-22.2.6.8-0004"
    ; "ecma262-22.2.6.8-0005"
    ; "ecma262-22.2.6.8-0006"
    ; "ecma262-22.2.6.8-0007"
    ; "ecma262-22.2.6.8-0008"
    ; "ecma262-22.2.6.8-0009"
    ; "ecma262-22.2.6.8-0010"
    ; "ecma262-22.2.6.8-0011"
    ; "ecma262-22.2.6.8-0012"
    ; "ecma262-22.2.6.8-0013"
    ; "ecma262-22.2.6.8-0014"
    ; "ecma262-22.2.6.8-0015"
    ; "ecma262-22.2.6.8-0016"
    ; "ecma262-22.2.6.8-0017"
    ; "ecma262-22.2.6.8-0018"
    ; "ecma262-22.2.6.8-0019"
    ; "ecma262-22.2.6.8-0020"
    ; "ecma262-22.2.6.8-0021"
    ; "ecma262-22.2.6.8-0022"
    ]
    match_adapter_rows;
  check_ids
    "match non-applicable rows"
    [ "ecma262-22.1.3.13-0003"
    ; "ecma262-22.1.3.13-0004"
    ; "ecma262-22.1.3.13-0005"
    ; "ecma262-22.1.3.13-0006"
    ; "ecma262-22.1.3.13-0007"
    ; "ecma262-22.1.3.13-0009"
    ; "ecma262-22.2.6.8-0003"
    ; "ecma262-22.2.6.8-0023"
    ]
    match_nonapp_rows;
  List.iter
    (fun row ->
       Alcotest.(check string)
         "match adapter artifact"
         "Ecma_regex.match_"
         (field "ocaml_artifact" row);
       Alcotest.(check string)
         "match adapter test artifact"
         "test/test_ecma262_match_adapter.ml"
         (field "next_test_artifact" row);
       Alcotest.(check string)
         "match adapter public API status"
         "current_public_api"
         (field "public_api_status" row))
    match_adapter_rows;
  List.iter
    (fun row ->
       Alcotest.(check string)
         "match JS protocol artifact"
         "none"
         (field "ocaml_artifact" row);
       Alcotest.(check string)
         "match JS protocol status"
         "not_ocaml_surface"
         (field "public_api_status" row))
    match_nonapp_rows

let test_match_non_global_returns_first_exec_result () =
  let regexp = compile_or_fail "b" in
  Alcotest.(check (option (list string))) "match text" (Some [ "b" ])
    (Ecma_regex.match_ regexp "abc" |> texts_of_match_results);
  Alcotest.(check (option (list int))) "match start" (Some [ 1 ])
    (Ecma_regex.match_ regexp "abc" |> starts_of_match_results);
  Alcotest.(check (option (list string))) "no match" None
    (Ecma_regex.match_ regexp "ac" |> texts_of_match_results)

let test_match_global_collects_all_full_matches () =
  let flags = flags_or_fail "g" in
  let regexp = compile_or_fail ~flags "a" in
  Alcotest.(check (option (list string))) "global match texts"
    (Some [ "a"; "a"; "a" ])
    (Ecma_regex.match_ regexp "banana" |> texts_of_match_results);
  Alcotest.(check (option (list int))) "global match starts"
    (Some [ 1; 3; 5 ])
    (Ecma_regex.match_ regexp "banana" |> starts_of_match_results);
  Alcotest.(check (option (list string))) "global no match" None
    (Ecma_regex.match_ regexp "xyz" |> texts_of_match_results)

let test_match_global_empty_advances_with_unicode_semantics () =
  let flags = flags_or_fail "gu" in
  let regexp = compile_or_fail ~flags "" in
  let non_bmp = "\xF0\x9F\x98\x80" in
  Alcotest.(check (option (list int))) "empty unicode starts"
    (Some [ 0; 2; 3 ])
    (Ecma_regex.match_ regexp (non_bmp ^ "a") |> starts_of_match_results)

let test_match_instance_global_resets_last_index () =
  let flags = flags_or_fail "g" in
  let regexp = compile_or_fail ~flags "a" in
  let instance = Ecma_regex.instance regexp in
  Ecma_regex.set_last_index instance 4;
  Alcotest.(check (option (list int))) "instance global starts"
    (Some [ 1; 3; 5 ])
    (Ecma_regex.match_instance instance "banana" |> starts_of_match_results);
  Alcotest.(check int) "instance global final lastIndex" 0
    (Ecma_regex.last_index instance)

let test_match_instance_non_global_sticky_uses_last_index () =
  let flags = flags_or_fail "y" in
  let regexp = compile_or_fail ~flags "b" in
  let instance = Ecma_regex.instance regexp in
  Ecma_regex.set_last_index instance 1;
  Alcotest.(check (option (list int))) "sticky match at lastIndex"
    (Some [ 1 ])
    (Ecma_regex.match_instance instance "ab" |> starts_of_match_results);
  Alcotest.(check int) "sticky lastIndex after match" 2
    (Ecma_regex.last_index instance);
  Ecma_regex.set_last_index instance 0;
  Alcotest.(check (option (list int))) "sticky mismatch" None
    (Ecma_regex.match_instance instance "ab" |> starts_of_match_results);
  Alcotest.(check int) "sticky lastIndex after mismatch" 0
    (Ecma_regex.last_index instance)

let test_match_js_returns_raw_utf16_slices () =
  let flags = flags_or_fail "gu" in
  let high = 0xD83D in
  let low = 0xDE00 in
  let input =
    js_string_of_utf16_units_or_fail
      [ high; low; Char.code 'a'; high; low ]
  in
  let regexp = compile_or_fail ~flags "." in
  Alcotest.(check (option (list (list int)))) "JS match units"
    (Some [ [ high; low ]; [ Char.code 'a' ]; [ high; low ] ])
    (Ecma_regex.match_js regexp input |> js_text_units_of_match_results);
  Alcotest.(check (option (list int))) "JS match starts"
    (Some [ 0; 2; 3 ])
    (Ecma_regex.match_js regexp input |> js_starts_of_match_results)

let test_match_js_non_global_exposes_raw_capture_slices () =
  let flags = flags_or_fail "u" in
  let high = 0xD83D in
  let low = 0xDE00 in
  let input =
    js_string_of_utf16_units_or_fail
      [ high; low; Char.code 'a'; Char.code 'z' ]
  in
  let regexp = compile_or_fail ~flags "(\\u{1F600})(?<tail>a)?" in
  let result = Ecma_regex.match_js regexp input |> single_js_match_result_or_fail in
  Alcotest.(check (list int)) "full match units"
    [ high; low; Char.code 'a' ]
    (Ecma_regex.js_string_to_utf16_code_units result.Ecma_regex.js_matched_text);
  Alcotest.(check int) "full match start" 0 result.Ecma_regex.js_start_index;
  Alcotest.(check int) "full match end" 3 result.Ecma_regex.js_end_index;
  let captures = result.Ecma_regex.js_captures in
  Alcotest.(check int) "capture count" 2 (List.length captures);
  let first_capture = List.nth captures 0 in
  let second_capture = List.nth captures 1 in
  Alcotest.(check (option (list int))) "pair capture units"
    (Some [ high; low ])
    (js_capture_units first_capture);
  Alcotest.(check (option int)) "pair capture start" (Some 0)
    first_capture.Ecma_regex.js_capture_start_index;
  Alcotest.(check (option int)) "pair capture end" (Some 2)
    first_capture.Ecma_regex.js_capture_end_index;
  Alcotest.(check (option (list int))) "tail capture units"
    (Some [ Char.code 'a' ])
    (js_capture_units second_capture);
  Alcotest.(check int) "named capture count" 1
    (List.length result.Ecma_regex.js_named_captures);
  let named = List.hd result.Ecma_regex.js_named_captures in
  Alcotest.(check string) "named capture name" "tail"
    named.Ecma_regex.js_named_capture_name;
  Alcotest.(check (option (list int))) "named capture units"
    (Some [ Char.code 'a' ])
    (js_capture_units named.Ecma_regex.js_named_capture)

let test_match_js_global_empty_advances_over_raw_surrogate_pair () =
  let flags = flags_or_fail "gu" in
  let high = 0xD83D in
  let low = 0xDE00 in
  let input =
    js_string_of_utf16_units_or_fail [ high; low; Char.code 'a' ]
  in
  let regexp = compile_or_fail ~flags "" in
  Alcotest.(check (option (list int))) "empty match starts"
    (Some [ 0; 2; 3 ])
    (Ecma_regex.match_js regexp input |> js_starts_of_match_results);
  Alcotest.(check (option (list (list int)))) "empty match units"
    (Some [ []; []; [] ])
    (Ecma_regex.match_js regexp input |> js_text_units_of_match_results)

let () =
  Alcotest.run
    "ecma262-match-adapter"
    [ ( "manifest"
      , [ Alcotest.test_case
            "product-surface match rows"
            `Quick
            test_product_surface_match_rows
        ] )
    ; ( "adapter semantics"
      , [ Alcotest.test_case
            "match_ non-global returns first exec result"
            `Quick
            test_match_non_global_returns_first_exec_result
        ; Alcotest.test_case
            "match_ global collects all full matches"
            `Quick
            test_match_global_collects_all_full_matches
        ; Alcotest.test_case
            "match_ global empty advances with unicode semantics"
            `Quick
            test_match_global_empty_advances_with_unicode_semantics
        ; Alcotest.test_case
            "match_instance global resets lastIndex"
            `Quick
            test_match_instance_global_resets_last_index
        ; Alcotest.test_case
            "match_instance non-global sticky uses lastIndex"
            `Quick
            test_match_instance_non_global_sticky_uses_last_index
        ; Alcotest.test_case
            "match_js returns raw UTF-16 slices"
            `Quick
            test_match_js_returns_raw_utf16_slices
        ; Alcotest.test_case
            "match_js non-global exposes raw capture slices"
            `Quick
            test_match_js_non_global_exposes_raw_capture_slices
        ; Alcotest.test_case
            "match_js global empty advances over raw surrogate pair"
            `Quick
            test_match_js_global_empty_advances_over_raw_surrogate_pair
        ] )
    ]
