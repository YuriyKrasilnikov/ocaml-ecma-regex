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
  if length > 0 && value.[length - 1] = '\r' then String.sub value 0 (length - 1)
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

let search_clause row =
  field "clause_id" row = "22.1.3.21" || field "clause_id" row = "22.2.6.12"

let search_adapter_rows =
  List.filter
    (fun row ->
      search_clause row
      && field "surface_decision" row = "ocaml_adapter_requirement")
    product_rows

let search_nonapp_rows =
  List.filter
    (fun row ->
      search_clause row
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
  let actual =
    rows |> List.map (field "requirement_id") |> List.sort String.compare
  in
  Alcotest.(check (list string)) name expected actual

let test_product_surface_search_rows () =
  check_ids "search adapter rows"
    [
      "ecma262-22.1.3.21-0001";
      "ecma262-22.1.3.21-0002";
      "ecma262-22.1.3.21-0008";
      "ecma262-22.1.3.21-0010";
      "ecma262-22.2.6.12-0001";
      "ecma262-22.2.6.12-0002";
      "ecma262-22.2.6.12-0004";
      "ecma262-22.2.6.12-0005";
      "ecma262-22.2.6.12-0006";
      "ecma262-22.2.6.12-0007";
      "ecma262-22.2.6.12-0008";
      "ecma262-22.2.6.12-0009";
      "ecma262-22.2.6.12-0010";
      "ecma262-22.2.6.12-0011";
      "ecma262-22.2.6.12-0012";
      "ecma262-22.2.6.12-0013";
    ]
    search_adapter_rows;
  check_ids "search non-applicable rows"
    [
      "ecma262-22.1.3.21-0003";
      "ecma262-22.1.3.21-0004";
      "ecma262-22.1.3.21-0005";
      "ecma262-22.1.3.21-0006";
      "ecma262-22.1.3.21-0007";
      "ecma262-22.1.3.21-0009";
      "ecma262-22.2.6.12-0003";
      "ecma262-22.2.6.12-0014";
    ]
    search_nonapp_rows;
  List.iter
    (fun row ->
      Alcotest.(check string)
        "search adapter artifact" "Ecma_regex.search_index"
        (field "ocaml_artifact" row);
      Alcotest.(check string)
        "search adapter test artifact" "test/test_ecma262_search_adapter.ml"
        (field "next_test_artifact" row);
      Alcotest.(check string)
        "search adapter public API status" "current_public_api"
        (field "public_api_status" row))
    search_adapter_rows

let test_search_index_returns_match_start_or_minus_one () =
  let regexp = compile_or_fail "b" in
  Alcotest.(check int)
    "match start index" 1
    (Ecma_regex.search_index regexp "abc");
  Alcotest.(check int)
    "no match index" (-1)
    (Ecma_regex.search_index regexp "ac");
  let non_bmp = "\xF0\x9F\x98\x80" in
  let unicode_regexp = compile_or_fail "a" in
  Alcotest.(check int)
    "UTF-16 start index after non-BMP" 2
    (Ecma_regex.search_index unicode_regexp (non_bmp ^ "a"))

let test_search_index_respects_sticky_from_zero () =
  let flags = flags_or_fail "y" in
  let later = compile_or_fail ~flags "b" in
  Alcotest.(check int)
    "sticky does not search past zero" (-1)
    (Ecma_regex.search_index later "ab");
  let at_zero = compile_or_fail ~flags "a" in
  Alcotest.(check int)
    "sticky match at zero" 0
    (Ecma_regex.search_index at_zero "ab")

let test_search_index_js_returns_utf16_index () =
  let high = 0xD83D in
  let low = 0xDE00 in
  let input = js_string_of_utf16_units_or_fail [ high; low; Char.code 'a' ] in
  let regexp = compile_or_fail "a" in
  Alcotest.(check int)
    "JS string UTF-16 start index" 2
    (Ecma_regex.search_index_js regexp input);
  let flags = flags_or_fail "u" in
  let low_surrogate = compile_or_fail ~flags "\\uDE00" in
  Alcotest.(check int)
    "Unicode search skips inside surrogate pair" (-1)
    (Ecma_regex.search_index_js low_surrogate input)

let test_search_instance_index_restores_last_index () =
  let flags = flags_or_fail "g" in
  let regexp = compile_or_fail ~flags "b" in
  let instance = Ecma_regex.instance regexp in
  Ecma_regex.set_last_index instance 2;
  Alcotest.(check int)
    "global instance search index" 1
    (Ecma_regex.search_instance_index instance "abc");
  Alcotest.(check int)
    "global instance lastIndex restored" 2
    (Ecma_regex.last_index instance);
  let sticky_flags = flags_or_fail "y" in
  let sticky = Ecma_regex.instance (compile_or_fail ~flags:sticky_flags "b") in
  Ecma_regex.set_last_index sticky 1;
  Alcotest.(check int)
    "sticky instance search starts at zero" (-1)
    (Ecma_regex.search_instance_index sticky "ab");
  Alcotest.(check int)
    "sticky instance lastIndex restored" 1
    (Ecma_regex.last_index sticky)

let test_search_instance_index_js_restores_last_index () =
  let flags = flags_or_fail "gu" in
  let high = 0xD83D in
  let low = 0xDE00 in
  let input = js_string_of_utf16_units_or_fail [ high; low; Char.code 'a' ] in
  let instance = Ecma_regex.instance (compile_or_fail ~flags "a") in
  Ecma_regex.set_last_index instance 3;
  Alcotest.(check int)
    "JS instance search index" 2
    (Ecma_regex.search_instance_index_js instance input);
  Alcotest.(check int)
    "JS instance lastIndex restored" 3
    (Ecma_regex.last_index instance)

let () =
  Alcotest.run "ecma262-search-adapter"
    [
      ( "manifest",
        [
          Alcotest.test_case "product-surface search rows" `Quick
            test_product_surface_search_rows;
        ] );
      ( "adapter semantics",
        [
          Alcotest.test_case "search_index returns match start or -1" `Quick
            test_search_index_returns_match_start_or_minus_one;
          Alcotest.test_case "search_index respects sticky from zero" `Quick
            test_search_index_respects_sticky_from_zero;
          Alcotest.test_case "search_index_js returns UTF-16 index" `Quick
            test_search_index_js_returns_utf16_index;
          Alcotest.test_case "search_instance_index restores lastIndex" `Quick
            test_search_instance_index_restores_last_index;
          Alcotest.test_case "search_instance_index_js restores lastIndex"
            `Quick test_search_instance_index_js_restores_last_index;
        ] );
    ]
