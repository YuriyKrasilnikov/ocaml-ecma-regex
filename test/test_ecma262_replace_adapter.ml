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

let replace_clause row =
  match field "clause_id" row with
  | "22.1.3.19" | "22.1.3.19.1" | "22.1.3.20" | "22.2.6.11" -> true
  | _ -> false

let replace_adapter_rows =
  List.filter
    (fun row ->
       replace_clause row
       && field "surface_decision" row = "ocaml_adapter_requirement")
    product_rows

let replace_nonapp_rows =
  List.filter
    (fun row ->
       replace_clause row
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

let id clause number =
  Printf.sprintf "ecma262-%s-%04d" clause number

let range_ids clause first last =
  List.init (last - first + 1) (fun offset -> id clause (first + offset))

let without ids excluded =
  List.filter (fun value -> not (List.exists (String.equal value) excluded)) ids

let test_product_surface_replace_rows () =
  let regexp_replace_nonapp =
    List.map (id "22.2.6.11") [ 3; 49; 50; 51; 52; 53; 54; 57; 65 ]
  in
  let expected_adapter_rows =
    List.concat
      [ without (range_ids "22.2.6.11" 1 65) regexp_replace_nonapp
      ; range_ids "22.1.3.19.1" 1 63
      ]
    |> List.sort String.compare
  in
  let expected_nonapp_rows =
    List.concat
      [ range_ids "22.1.3.19" 1 24
      ; range_ids "22.1.3.20" 1 39
      ; regexp_replace_nonapp
      ]
    |> List.sort String.compare
  in
  check_ids "replace adapter rows" expected_adapter_rows replace_adapter_rows;
  check_ids "replace non-applicable rows" expected_nonapp_rows replace_nonapp_rows;
  List.iter
    (fun row ->
       Alcotest.(check string)
         "replace adapter artifact"
         "Ecma_regex.replace"
         (field "ocaml_artifact" row);
       Alcotest.(check string)
         "replace adapter test artifact"
         "test/test_ecma262_replace_adapter.ml"
         (field "next_test_artifact" row);
       Alcotest.(check string)
         "replace adapter public API status"
         "current_public_api"
         (field "public_api_status" row))
    replace_adapter_rows;
  List.iter
    (fun row ->
       Alcotest.(check string)
         "replace non-applicable artifact"
         "none"
         (field "ocaml_artifact" row);
       Alcotest.(check string)
         "replace non-applicable status"
         "not_ocaml_surface"
         (field "public_api_status" row))
    replace_nonapp_rows

let test_replace_first_and_global_modes () =
  let regexp = compile_or_fail "a" in
  Alcotest.(check string) "non-global replaces first match"
    "bXaa"
    (Ecma_regex.replace ~replacement:"X" regexp "baaa");
  let global = compile_or_fail ~flags:(flags_or_fail "g") "a" in
  Alcotest.(check string) "global replaces every match"
    "bXXX"
    (Ecma_regex.replace ~replacement:"X" global "baaa");
  Alcotest.(check string) "no match returns original"
    "bbb"
    (Ecma_regex.replace ~replacement:"X" regexp "bbb")

let test_replace_instance_last_index_semantics () =
  let global = compile_or_fail ~flags:(flags_or_fail "g") "a" in
  let global_instance = Ecma_regex.instance global in
  Ecma_regex.set_last_index global_instance 2;
  Alcotest.(check string) "global replace resets lastIndex before matching"
    "XbX"
    (Ecma_regex.replace_instance ~replacement:"X" global_instance "aba");
  Alcotest.(check int) "global replace leaves terminal lastIndex"
    0
    (Ecma_regex.last_index global_instance);
  let sticky = compile_or_fail ~flags:(flags_or_fail "y") "a" in
  let sticky_instance = Ecma_regex.instance sticky in
  Ecma_regex.set_last_index sticky_instance 1;
  Alcotest.(check string) "sticky non-global replace uses receiver lastIndex"
    "bX"
    (Ecma_regex.replace_instance ~replacement:"X" sticky_instance "ba");
  Alcotest.(check int) "sticky replace updates lastIndex"
    2
    (Ecma_regex.last_index sticky_instance)

let test_get_substitution_special_references () =
  let regexp = compile_or_fail "(b)" in
  Alcotest.(check string) "special replacement references"
    "a[$][b][a][cde][b][$2]cde"
    (Ecma_regex.replace
       ~replacement:"[$$][$&][$`][$'][$1][$2]"
       regexp
       "abcde")

let test_get_substitution_numbered_capture_edges () =
  let regexp = compile_or_fail "(a)(b)" in
  Alcotest.(check string) "two-digit capture fallback and zero handling"
    "b-a-a2-$99-a"
    (Ecma_regex.replace ~replacement:"$2-$1-$12-$99-$01" regexp "ab");
  let alternate = compile_or_fail "(a)|(b)" in
  Alcotest.(check string) "undefined numbered capture becomes empty"
    "[][b]"
    (Ecma_regex.replace ~replacement:"[$1][$2]" alternate "b")

let test_get_substitution_named_captures () =
  let regexp = compile_or_fail "(?<word>a)" in
  Alcotest.(check string) "named capture substitution"
    "a::$<"
    (Ecma_regex.replace ~replacement:"$<word>:$<missing>:$<" regexp "a");
  let unnamed = compile_or_fail "(a)" in
  Alcotest.(check string) "named syntax stays literal without named captures"
    "$<word>"
    (Ecma_regex.replace ~replacement:"$<word>" unnamed "a")

let test_replace_all_explicit_helper () =
  let regexp = compile_or_fail "a" in
  Alcotest.(check string) "replace_all forces all-match traversal"
    "bXXX"
    (Ecma_regex.replace_all ~replacement:"X" regexp "baaa");
  let instance = Ecma_regex.instance regexp in
  Ecma_regex.set_last_index instance 2;
  Alcotest.(check string) "replace_all_instance preserves receiver"
    "bXXX"
    (Ecma_regex.replace_all_instance ~replacement:"X" instance "baaa");
  Alcotest.(check int) "replace_all_instance does not mutate receiver"
    2
    (Ecma_regex.last_index instance)

let test_replace_js_preserves_raw_utf16_slices () =
  let flags = flags_or_fail "u" in
  let high = 0xD83D in
  let low = 0xDE00 in
  let input =
    js_string_of_utf16_units_or_fail [ high; low; Char.code 'a' ]
  in
  let replacement = js_string_of_utf16_units_or_fail [ Char.code '-' ] in
  let regexp = compile_or_fail ~flags "" in
  let replaced =
    Ecma_regex.replace_all_js ~replacement regexp input
    |> Ecma_regex.js_string_to_utf16_code_units
  in
  Alcotest.(check (list int)) "JS unicode empty replaceAll units"
    [ Char.code '-'; high; low; Char.code '-'; Char.code 'a'; Char.code '-' ]
    replaced

let () =
  Alcotest.run
    "ecma262-replace-adapter"
    [ ( "manifest"
      , [ Alcotest.test_case
            "product-surface replace rows"
            `Quick
            test_product_surface_replace_rows
        ] )
    ; ( "adapter semantics"
      , [ Alcotest.test_case
            "replace first and global modes"
            `Quick
            test_replace_first_and_global_modes
        ; Alcotest.test_case
            "replace instance lastIndex semantics"
            `Quick
            test_replace_instance_last_index_semantics
        ; Alcotest.test_case
            "GetSubstitution special references"
            `Quick
            test_get_substitution_special_references
        ; Alcotest.test_case
            "GetSubstitution numbered captures"
            `Quick
            test_get_substitution_numbered_capture_edges
        ; Alcotest.test_case
            "GetSubstitution named captures"
            `Quick
            test_get_substitution_named_captures
        ; Alcotest.test_case
            "replace_all explicit helper"
            `Quick
            test_replace_all_explicit_helper
        ; Alcotest.test_case
            "replace_js preserves raw UTF-16 slices"
            `Quick
            test_replace_js_preserves_raw_utf16_slices
        ] )
    ]
