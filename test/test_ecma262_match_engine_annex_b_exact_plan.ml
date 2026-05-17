let repo_root () =
  let cwd = Sys.getcwd () in
  let rec climb dir =
    let candidate =
      Filename.concat dir
        "cache/ecma262-regexp-match-engine-annex-b-exact-plan.tsv"
    in
    if Sys.file_exists candidate then dir
    else
      let parent = Filename.dirname dir in
      if parent = dir then
        Alcotest.fail
          "cache/ecma262-regexp-match-engine-annex-b-exact-plan.tsv is \
           missing; run \
           tools/build_ecma262_regexp_match_engine_annex_b_exact_plan.py"
      else climb parent
  in
  climb cwd

let path segments =
  List.fold_left Filename.concat (repo_root ()) segments

let strip_trailing_cr value =
  let length = String.length value in
  if length > 0 && value.[length - 1] = '\r' then
    String.sub value 0 (length - 1)
  else value

let split_tsv_line line =
  line |> strip_trailing_cr |> String.split_on_char '\t'

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

let plan_rows () =
  read_tsv [ "cache"; "ecma262-regexp-match-engine-annex-b-exact-plan.tsv" ]

let count_by field_name rows =
  let counts = Hashtbl.create 32 in
  List.iter
    (fun row ->
       let key = field field_name row in
       let count = Option.value (Hashtbl.find_opt counts key) ~default:0 in
       Hashtbl.replace counts key (count + 1))
    rows;
  counts

let check_count counts key expected =
  Alcotest.(check int) key expected
    (Option.value (Hashtbl.find_opt counts key) ~default:0)

let source_exists source_file =
  source_file <> "" && Sys.file_exists (path [ source_file ])

let target_exists target =
  target <> "" && Sys.file_exists (path [ target ])

let hex_value = function
  | '0' .. '9' as char -> Some (Char.code char - Char.code '0')
  | 'a' .. 'f' as char -> Some (10 + Char.code char - Char.code 'a')
  | 'A' .. 'F' as char -> Some (10 + Char.code char - Char.code 'A')
  | _ -> None

let decode_text source =
  let buffer = Buffer.create (String.length source) in
  let add_hex index =
    if index + 3 >= String.length source then
      Alcotest.failf "unterminated hex escape in %S" source
    else
      match hex_value source.[index + 2], hex_value source.[index + 3] with
      | Some high, Some low ->
        Buffer.add_char buffer (Char.chr ((high * 16) + low));
        index + 4
      | _ -> Alcotest.failf "invalid hex escape in %S" source
  in
  let rec loop index =
    if index = String.length source then Buffer.contents buffer
    else if source.[index] = '\\' && index + 1 < String.length source then
      match source.[index + 1] with
      | 'n' ->
        Buffer.add_char buffer '\n';
        loop (index + 2)
      | 'r' ->
        Buffer.add_char buffer '\r';
        loop (index + 2)
      | 't' ->
        Buffer.add_char buffer '\t';
        loop (index + 2)
      | '\\' ->
        Buffer.add_char buffer '\\';
        loop (index + 2)
      | 'x' -> loop (add_hex index)
      | _ ->
        Buffer.add_char buffer source.[index];
        Buffer.add_char buffer source.[index + 1];
        loop (index + 2)
    else begin
      Buffer.add_char buffer source.[index];
      loop (index + 1)
    end
  in
  loop 0

let parse_bool row name =
  match field name row with
  | "true" -> true
  | "false" -> false
  | other ->
    Alcotest.failf "%s: invalid %s %S" (field "plan_id" row) name other

let parse_int_field row name =
  match int_of_string_opt (field name row) with
  | Some value -> value
  | None ->
    Alcotest.failf "%s: invalid %s %S"
      (field "plan_id" row)
      name
      (field name row)

let flags_for row =
  match Ecma_regex.flags_of_string (field "flags" row) with
  | Ok flags -> flags
  | Error msg -> Alcotest.failf "%s: flags failed: %s" (field "plan_id" row) msg

let test_exact_plan_manifest () =
  let rows = plan_rows () in
  Alcotest.(check int) "Annex B exact plan rows" 49 (List.length rows);
  let state_counts = count_by "plan_state" rows in
  check_count state_counts "planned_not_executable" 49;
  let credit_counts = count_by "coverage_credit" rows in
  check_count credit_counts "none_match_engine_annex_b_exact_planned" 49;
  let mapping_counts = count_by "mapping_family" rows in
  check_count mapping_counts "match_engine_annex_b_annexB" 49;
  let layer_counts = count_by "executable_layer" rows in
  check_count layer_counts "match_engine" 49;
  let clause_counts = count_by "clause_id" rows in
  check_count clause_counts "B.1.2.5" 10;
  check_count clause_counts "B.1.2.6" 3;
  check_count clause_counts "B.1.2.7" 9;
  check_count clause_counts "B.1.2.8" 21;
  check_count clause_counts "B.1.2.8.1" 6;
  let subfamily_counts = count_by "annex_b_subfamily" rows in
  check_count subfamily_counts "quantifiable_assertion" 6;
  check_count subfamily_counts "extended_atom" 13;
  check_count subfamily_counts "compile_to_charset" 26;
  check_count subfamily_counts "character_range_or_union" 1;
  check_count subfamily_counts "compile_subpattern_substitution" 3;
  let route_counts = count_by "annex_b_route" rows in
  check_count route_counts "positive_lookahead_quantifier" 5;
  check_count route_counts "negative_lookahead_quantifier" 1;
  check_count route_counts "extended_atom_quantifier" 2;
  check_count route_counts "backslash_lookahead_c_literal" 3;
  check_count route_counts "extended_pattern_character" 8;
  check_count route_counts "class_range_or_union_left_escape" 8;
  check_count route_counts "class_range_or_union_right_escape" 11;
  check_count route_counts "class_control_letter" 5;
  check_count route_counts "class_atom_no_dash_backslash_c" 2;
  check_count route_counts "single_character_range" 1;
  let search_counts = count_by "expected_search_result" rows in
  check_count search_counts "true" 49;
  let exec_counts = count_by "expected_exec_result" rows in
  check_count exec_counts "true" 49;
  let target_counts = count_by "target_test_artifact" rows in
  check_count target_counts "test/test_ecma262_match_engine_annex_b_exact_plan.ml" 49;
  List.iter
    (fun row ->
       if
         not
           (String.starts_with
              ~prefix:"match-engine-annex-b-exact:"
              (field "exact_case_id" row))
       then
         Alcotest.failf "%s: exact_case_id has wrong prefix"
           (field "plan_id" row);
       List.iter
         (fun name ->
            if field name row = "" then
              Alcotest.failf "%s: %s is empty" (field "plan_id" row) name)
         [
           "annex_b_subfamily";
           "annex_b_route";
           "exact_case_family";
           "pattern";
           "input_text";
           "expected_match_text";
           "expected_behavior";
           "exact_case_obligation";
           "observability_status";
           "observability_reason";
         ];
       Alcotest.(check string)
         "observable executable row"
         "search_and_exec_observable"
         (field "observability_status" row);
       Alcotest.(check string)
         "executable next action"
         "materialize_match_engine_annex_b_exact_case"
         (field "next_action" row);
       if not (source_exists (field "source_file" row)) then
         Alcotest.failf "%s: missing ECMA source %s"
           (field "plan_id" row)
           (field "source_file" row);
       if not (target_exists (field "target_test_artifact" row)) then
         Alcotest.failf "%s: missing target test artifact %s"
           (field "plan_id" row)
           (field "target_test_artifact" row))
    rows

let compile_or_fail row =
  match Ecma_regex.compile ~flags:(flags_for row) (field "pattern" row) with
  | Ok regexp -> regexp
  | Error msg -> Alcotest.failf "%s: compile failed: %s" (field "plan_id" row) msg

let test_exact_plan_cases () =
  let rows = plan_rows () in
  List.iter
    (fun row ->
       let regexp = compile_or_fail row in
       let input = decode_text (field "input_text" row) in
       let expected_search = parse_bool row "expected_search_result" in
       Alcotest.(check bool)
         (field "plan_id" row ^ ": search")
         expected_search
         (Ecma_regex.search regexp input);
       let expected_exec = parse_bool row "expected_exec_result" in
       match Ecma_regex.exec regexp input, expected_exec with
       | None, false -> ()
       | None, true ->
         Alcotest.failf "%s: expected exec match" (field "plan_id" row)
       | Some result, false ->
         Alcotest.failf "%s: unexpected exec match %S"
           (field "plan_id" row)
           result.matched_text
       | Some result, true ->
         Alcotest.(check int)
           (field "plan_id" row ^ ": start_index")
           (parse_int_field row "expected_start_index")
           result.start_index;
         Alcotest.(check int)
           (field "plan_id" row ^ ": end_index")
           (parse_int_field row "expected_end_index")
           result.end_index;
         Alcotest.(check string)
           (field "plan_id" row ^ ": matched_text")
           (decode_text (field "expected_match_text" row))
           result.matched_text)
    rows

let () =
  Alcotest.run "ecma262-match-engine-annex-b-exact-plan" [
    ("manifest", [
       Alcotest.test_case
         "Annex B exact plan invariants"
         `Quick
         test_exact_plan_manifest;
     ]);
    ("exec", [
       Alcotest.test_case
         "Annex B exact planned cases"
         `Quick
         test_exact_plan_cases;
     ]);
  ]
