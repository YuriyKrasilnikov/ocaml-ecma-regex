let repo_root () =
  let cwd = Sys.getcwd () in
  let rec climb dir =
    let candidate =
      Filename.concat dir "cache/ecma262-regexp-match-engine-exact-plan.tsv"
    in
    if Sys.file_exists candidate then dir
    else
      let parent = Filename.dirname dir in
      if parent = dir then
        Alcotest.fail
          "cache/ecma262-regexp-match-engine-exact-plan.tsv is missing; \
           run tools/build_ecma262_regexp_match_engine_exact_plan.py"
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
  line
  |> strip_trailing_cr
  |> String.split_on_char '\t'

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
  read_tsv [ "cache"; "ecma262-regexp-match-engine-exact-plan.tsv" ]

let count_by field_name rows =
  let counts = Hashtbl.create 16 in
  List.iter
    (fun row ->
       let key = field field_name row in
       let count = Option.value (Hashtbl.find_opt counts key) ~default:0 in
       Hashtbl.replace counts key (count + 1))
    rows;
  counts

let check_count counts key expected =
  Alcotest.(check int)
    key
    expected
    (Option.value (Hashtbl.find_opt counts key) ~default:0)

let source_exists source_file =
  source_file <> "" && Sys.file_exists (path [ source_file ])

let target_exists target =
  target <> "" && Sys.file_exists (path [ target ])

let executable_rows rows =
  List.filter
    (fun row ->
       field "plan_state" row = "planned_not_executable"
       && field "coverage_credit" row = "none_match_engine_exact_planned")
    rows

let deferred_rows rows =
  List.filter
    (fun row ->
       String.starts_with ~prefix:"deferred_" (field "plan_state" row)
       && field "coverage_credit" row = "none_match_engine_exact_deferred")
    rows

let parse_expected_bool row =
  match field "expected_search_result" row with
  | "true" -> true
  | "false" -> false
  | other ->
    Alcotest.failf "%s: invalid expected_search_result %S"
      (field "plan_id" row)
      other

let test_exact_plan_manifest () =
  let rows = plan_rows () in
  Alcotest.(check int) "match-engine exact plan rows" 14 (List.length rows);
  let executable = executable_rows rows in
  Alcotest.(check int) "executable planned rows" 10 (List.length executable);
  let deferred = deferred_rows rows in
  Alcotest.(check int) "deferred planned rows" 4 (List.length deferred);
  let state_counts = count_by "plan_state" rows in
  check_count state_counts "planned_not_executable" 10;
  check_count state_counts "deferred_requires_exec_result_observer" 1;
  check_count state_counts "deferred_requires_match_state_model" 3;
  let credit_counts = count_by "coverage_credit" rows in
  check_count credit_counts "none_match_engine_exact_planned" 10;
  check_count credit_counts "none_match_engine_exact_deferred" 4;
  let expected_counts = count_by "expected_behavior" rows in
  check_count expected_counts "search_true" 9;
  check_count expected_counts "search_false" 1;
  check_count expected_counts "requires_exec_result_observer" 1;
  check_count expected_counts "requires_match_state_model" 3;
  let search_counts = count_by "expected_search_result" rows in
  check_count search_counts "true" 9;
  check_count search_counts "false" 1;
  check_count search_counts "not_observable" 4;
  let layer_counts = count_by "executable_layer" rows in
  check_count layer_counts "match_engine" 14;
  let family_counts = count_by "mapping_family" rows in
  check_count family_counts "match_engine_atoms" 4;
  check_count family_counts "match_engine_concatenation" 3;
  check_count family_counts "match_engine_alternation" 7;
  List.iter
    (fun row ->
       if field "exact_case_id" row = "" then
         Alcotest.failf "%s: exact_case_id is empty" (field "plan_id" row);
       if field "exact_case_obligation" row = "" then
         Alcotest.failf "%s: exact_case_obligation is empty"
           (field "plan_id" row);
       if field "observability_status" row = "" then
         Alcotest.failf "%s: observability_status is empty"
           (field "plan_id" row);
       if field "observability_reason" row = "" then
         Alcotest.failf "%s: observability_reason is empty"
           (field "plan_id" row);
       if not (source_exists (field "source_file" row)) then
         Alcotest.failf "%s: missing ECMA source %s"
           (field "plan_id" row)
           (field "source_file" row);
       if field "plan_state" row = "planned_not_executable" then begin
         if
           not
             (String.starts_with ~prefix:"match-engine-exact:"
                (field "exact_case_id" row))
         then Alcotest.failf "%s: exact_case_id has wrong executable prefix"
             (field "plan_id" row);
         if field "pattern" row = "" then
           Alcotest.failf "%s: pattern is empty" (field "plan_id" row);
         if field "input_text" row = "" then
           Alcotest.failf "%s: input_text is empty" (field "plan_id" row);
         Alcotest.(check string)
           "observable executable row"
           "search_bool_observable"
           (field "observability_status" row);
         Alcotest.(check string)
           "executable next action"
           "materialize_match_engine_exact_case"
           (field "next_action" row);
         if not (target_exists (field "target_test_artifact" row)) then
           Alcotest.failf "%s: missing target test artifact %s"
             (field "plan_id" row)
             (field "target_test_artifact" row)
       end
       else begin
         if
           not
             (String.starts_with ~prefix:"match-engine-deferred:"
                (field "exact_case_id" row))
         then Alcotest.failf "%s: exact_case_id has wrong deferred prefix"
             (field "plan_id" row);
         Alcotest.(check string) "deferred pattern" "" (field "pattern" row);
         Alcotest.(check string) "deferred input" "" (field "input_text" row);
         Alcotest.(check string)
           "deferred target"
           ""
           (field "target_test_artifact" row);
         Alcotest.(check string)
           "deferred expected search"
           "not_observable"
           (field "expected_search_result" row);
         if
           field "observability_status" row <> "requires_match_state_model"
           && field "observability_status" row
              <> "requires_exec_result_observer"
         then Alcotest.failf "%s: invalid deferred observability_status %s"
             (field "plan_id" row)
             (field "observability_status" row)
       end)
    rows

let flags_for row =
  match Ecma_regex.flags_of_string (field "flags" row) with
  | Ok flags -> flags
  | Error msg ->
    Alcotest.failf "%s: flags failed: %s" (field "plan_id" row) msg

let check_match index total row =
  let flags = flags_for row in
  match Ecma_regex.compile ~flags (field "pattern" row) with
  | Error msg ->
    Alcotest.failf
      "match-engine exact case failed to compile (%d/%d): plan=%s \
       requirement=%s pattern=%S flags=%S error=%s"
      (index + 1) total
      (field "plan_id" row)
      (field "requirement_id" row)
      (field "pattern" row)
      (field "flags" row)
      msg
  | Ok regexp ->
    Alcotest.(check bool)
      (field "exact_case_id" row)
      (parse_expected_bool row)
      (Ecma_regex.search regexp (field "input_text" row))

let test_exact_plan_match_cases () =
  let rows = plan_rows () |> executable_rows in
  List.iteri (fun index row -> check_match index (List.length rows) row) rows

let () =
  Alcotest.run "ecma262-match-engine-exact-plan" [
    ("manifest", [
      Alcotest.test_case "match-engine exact plan invariants" `Quick
        test_exact_plan_manifest;
    ]);
    ("match", [
      Alcotest.test_case "match-engine exact planned cases" `Quick
        test_exact_plan_match_cases;
    ]);
  ]
