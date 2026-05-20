let repo_root () =
  let cwd = Sys.getcwd () in
  let rec climb dir =
    let candidate =
      Filename.concat dir
        "cache/ecma262-regexp-match-engine-quantifier-exact-plan.tsv"
    in
    if Sys.file_exists candidate then dir
    else
      let parent = Filename.dirname dir in
      if parent = dir then
        Alcotest.fail
          "cache/ecma262-regexp-match-engine-quantifier-exact-plan.tsv is \
           missing; run \
           tools/build_ecma262_regexp_match_engine_quantifier_exact_plan.py"
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

let plan_rows () =
  read_tsv [ "cache"; "ecma262-regexp-match-engine-quantifier-exact-plan.tsv" ]

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
  Alcotest.(check int)
    key expected
    (Option.value (Hashtbl.find_opt counts key) ~default:0)

let source_exists source_file =
  source_file <> "" && Sys.file_exists (path [ source_file ])

let target_exists target = target <> "" && Sys.file_exists (path [ target ])

let planned_rows rows =
  List.filter
    (fun row ->
      field "plan_state" row = "planned_not_executable"
      && field "coverage_credit" row
         = "none_match_engine_quantifier_exact_planned")
    rows

let parse_bool row name =
  match field name row with
  | "true" -> true
  | "false" -> false
  | other -> Alcotest.failf "%s: invalid %s %S" (field "plan_id" row) name other

let parse_int_field row name =
  match int_of_string_opt (field name row) with
  | Some value -> value
  | None ->
      Alcotest.failf "%s: invalid %s %S" (field "plan_id" row) name
        (field name row)

let parse_nonnegative_int_field row name =
  let value = parse_int_field row name in
  if value < 0 then
    Alcotest.failf "%s: %s must be non-negative" (field "plan_id" row) name;
  value

let flags_for row =
  match Ecma_regex.flags_of_string (field "flags" row) with
  | Ok flags -> flags
  | Error msg -> Alcotest.failf "%s: flags failed: %s" (field "plan_id" row) msg

let test_exact_plan_manifest () =
  let rows = plan_rows () in
  Alcotest.(check int) "quantifier exact plan rows" 45 (List.length rows);
  Alcotest.(check int)
    "planned executable rows" 45
    (List.length (planned_rows rows));
  let state_counts = count_by "plan_state" rows in
  check_count state_counts "planned_not_executable" 45;
  let credit_counts = count_by "coverage_credit" rows in
  check_count credit_counts "none_match_engine_quantifier_exact_planned" 45;
  let clause_counts = count_by "clause_id" rows in
  check_count clause_counts "22.2.2.3.1" 21;
  check_count clause_counts "22.2.2.5" 7;
  check_count clause_counts "22.2.2.6" 17;
  let search_counts = count_by "expected_search_result" rows in
  check_count search_counts "true" 41;
  check_count search_counts "false" 4;
  let exec_counts = count_by "expected_exec_result" rows in
  check_count exec_counts "true" 41;
  check_count exec_counts "false" 4;
  let behavior_counts = count_by "expected_behavior" rows in
  check_count behavior_counts "repeat_matcher_recursive_many" 7;
  check_count behavior_counts "repeat_matcher_zero_max_continuation" 1;
  check_count behavior_counts "repeat_matcher_zero_width_progress_guard" 1;
  check_count behavior_counts "repeat_matcher_capture_state_rewritten" 5;
  check_count behavior_counts "repeat_matcher_lazy_tries_continuation_first" 4;
  check_count behavior_counts "repeat_matcher_greedy_backtracks_for_suffix" 3;
  check_count behavior_counts "compile_quantifier_greedy_true" 4;
  check_count behavior_counts "compile_quantifier_greedy_false" 3;
  check_count behavior_counts "quantifier_prefix_star_min_zero_max_infinity" 3;
  check_count behavior_counts "quantifier_prefix_plus_min_one_max_infinity" 1;
  check_count behavior_counts "quantifier_prefix_plus_requires_one" 1;
  check_count behavior_counts "quantifier_prefix_question_accepts_zero" 1;
  check_count behavior_counts "quantifier_prefix_question_max_one" 1;
  check_count behavior_counts "quantifier_prefix_braced_exact" 2;
  check_count behavior_counts "quantifier_prefix_braced_exact_requires_count" 1;
  check_count behavior_counts "quantifier_prefix_braced_open_max_infinity" 3;
  check_count behavior_counts "quantifier_prefix_braced_range" 3;
  check_count behavior_counts "quantifier_prefix_braced_range_max_bound" 1;
  let mapping_counts = count_by "mapping_family" rows in
  check_count mapping_counts "match_engine_quantifiers" 45;
  List.iter
    (fun row ->
      if
        not
          (String.starts_with ~prefix:"match-engine-quantifier-exact:"
             (field "exact_case_id" row))
      then
        Alcotest.failf "%s: exact_case_id has wrong prefix"
          (field "plan_id" row);
      List.iter
        (fun name ->
          if field name row = "" then
            Alcotest.failf "%s: %s is empty" (field "plan_id" row) name)
        [
          "pattern";
          "expected_search_result";
          "expected_exec_result";
          "expected_behavior";
          "source_failure_family";
          "source_failure_count";
          "exact_case_obligation";
          "observability_reason";
        ];
      if parse_bool row "expected_exec_result" then begin
        if field "expected_start_index" row = "" then
          Alcotest.failf "%s: expected_start_index is empty"
            (field "plan_id" row);
        if field "expected_end_index" row = "" then
          Alcotest.failf "%s: expected_end_index is empty" (field "plan_id" row)
      end;
      Alcotest.(check string)
        "source failure family" "matcher_runtime_quantifier"
        (field "source_failure_family" row);
      ignore (parse_nonnegative_int_field row "source_failure_count");
      Alcotest.(check string)
        "observability" "search_and_exec_observable"
        (field "observability_status" row);
      if not (source_exists (field "source_file" row)) then
        Alcotest.failf "%s: missing ECMA source %s" (field "plan_id" row)
          (field "source_file" row);
      if not (target_exists (field "target_test_artifact" row)) then
        Alcotest.failf "%s: missing target test artifact %s"
          (field "plan_id" row)
          (field "target_test_artifact" row))
    rows

let check_exec_result row regexp input =
  match Ecma_regex.exec regexp input with
  | None when not (parse_bool row "expected_exec_result") -> ()
  | None ->
      Alcotest.failf "%s: expected exec result, got None" (field "plan_id" row)
  | Some result when not (parse_bool row "expected_exec_result") ->
      Alcotest.failf "%s: expected no exec result, got %d..%d %S"
        (field "plan_id" row) result.start_index result.end_index
        result.matched_text
  | Some result ->
      Alcotest.(check int)
        "start_index"
        (parse_int_field row "expected_start_index")
        result.start_index;
      Alcotest.(check int)
        "end_index"
        (parse_int_field row "expected_end_index")
        result.end_index;
      Alcotest.(check string)
        "matched_text"
        (field "expected_match_text" row)
        result.matched_text

let check_quantifier_case row =
  let flags = flags_for row in
  match Ecma_regex.compile ~flags (field "pattern" row) with
  | Error msg ->
      Alcotest.failf
        "quantifier exact case failed to compile: plan=%s requirement=%s \
         pattern=%S flags=%S error=%s"
        (field "plan_id" row)
        (field "requirement_id" row)
        (field "pattern" row) (field "flags" row) msg
  | Ok regexp ->
      let input = field "input_text" row in
      Alcotest.(check bool)
        (field "exact_case_id" row)
        (parse_bool row "expected_search_result")
        (Ecma_regex.search regexp input);
      check_exec_result row regexp input

let test_exact_plan_quantifier_cases () =
  plan_rows () |> planned_rows |> List.iter check_quantifier_case

let () =
  Alcotest.run "ecma262-match-engine-quantifier-exact-plan"
    [
      ( "manifest",
        [
          Alcotest.test_case "quantifier exact plan invariants" `Quick
            test_exact_plan_manifest;
        ] );
      ( "match",
        [
          Alcotest.test_case "quantifier exact planned cases" `Quick
            test_exact_plan_quantifier_cases;
        ] );
    ]
