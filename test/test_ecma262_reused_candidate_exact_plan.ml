let repo_root () =
  let cwd = Sys.getcwd () in
  let rec climb dir =
    let candidate =
      Filename.concat dir
        "cache/ecma262-regexp-reused-candidate-exact-plan.tsv"
    in
    if Sys.file_exists candidate then dir
    else
      let parent = Filename.dirname dir in
      if parent = dir then
        Alcotest.fail
          "cache/ecma262-regexp-reused-candidate-exact-plan.tsv is missing; \
           run tools/build_ecma262_regexp_reused_candidate_exact_plan.py"
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
  read_tsv [ "cache"; "ecma262-regexp-reused-candidate-exact-plan.tsv" ]

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

let require_nonempty row field_name =
  if field field_name row = "" then
    Alcotest.failf "%s: %s is empty" (field "plan_id" row) field_name

let check_unique_nonempty field_name rows =
  let seen = Hashtbl.create (List.length rows) in
  List.iter
    (fun row ->
       let value = field field_name row in
       if value = "" then
         Alcotest.failf "%s: %s is empty" (field "plan_id" row) field_name;
       if Hashtbl.mem seen value then
         Alcotest.failf "duplicate %s %s" field_name value;
       Hashtbl.add seen value ())
    rows

let test262_source_exists case_source =
  match String.split_on_char ':' case_source with
  | source_path :: _ ->
    Sys.file_exists (path [ "external"; "test262"; source_path ])
  | [] -> false

let ecma262_source_exists source_file =
  String.starts_with ~prefix:"external/ecma262/" source_file
  && Sys.file_exists (path [ source_file ])

let planned_rows rows =
  List.filter (fun row -> field "plan_state" row = "planned_not_executable") rows

let manual_rows rows =
  List.filter (fun row -> field "plan_state" row = "manual_spec_review_required") rows

let test_reused_candidate_exact_plan_manifest () =
  let rows = plan_rows () in
  Alcotest.(check int) "exact plan rows" 226 (List.length rows);
  check_unique_nonempty "plan_id" rows;
  check_unique_nonempty "exact_case_id" (planned_rows rows);
  let state_counts = count_by "plan_state" rows in
  check_count state_counts "planned_not_executable" 224;
  check_count state_counts "manual_spec_review_required" 2;
  let decision_counts = count_by "proof_decision" rows in
  check_count decision_counts "needs_local_exact_case" 224;
  check_count decision_counts "manual_spec_review_required" 2;
  let credit_counts = count_by "coverage_credit" rows in
  check_count credit_counts "none_reused_candidate_exact_planned" 224;
  check_count credit_counts "none_manual_review_required" 2;
  let action_counts = count_by "next_action" rows in
  check_count action_counts "materialize_reused_candidate_exact_case" 224;
  check_count action_counts "manual_spec_review_before_exact_case" 2;
  let layer_counts = count_by "executable_layer" rows in
  check_count layer_counts "compile" 102;
  check_count layer_counts "parser" 124;
  let flag_counts = count_by "planned_flags" (planned_rows rows) in
  check_count flag_counts "" 129;
  check_count flag_counts "g" 89;
  check_count flag_counts "u" 1;
  check_count flag_counts "v" 1;
  check_count flag_counts "y" 4;
  List.iter
    (fun row ->
       List.iter
         (require_nonempty row)
         [
           "plan_id";
           "requirement_id";
           "clause_id";
           "clause_title";
           "source_file";
           "section_anchor";
           "requirement_kind";
           "semantic_family";
           "mapping_family";
           "executable_layer";
           "selected_case_id";
           "selected_case_source";
           "selected_pattern";
           "case_reuse_count";
           "cluster_size";
           "cluster_pressure";
           "proof_decision";
           "coverage_credit";
           "plan_state";
           "next_action";
           "plan_reason";
         ];
       if not (ecma262_source_exists (field "source_file" row)) then
         Alcotest.failf "%s: ECMA source missing: %s"
           (field "plan_id" row)
           (field "source_file" row);
       if not (test262_source_exists (field "selected_case_source" row)) then
         Alcotest.failf "%s: test262 source missing: %s"
           (field "plan_id" row)
           (field "selected_case_source" row);
       if not (String.starts_with ~prefix:"none" (field "coverage_credit" row))
       then Alcotest.failf "%s: exact plan must not credit coverage"
           (field "plan_id" row))
    rows;
  List.iter
    (fun row ->
       List.iter
         (require_nonempty row)
         [
           "exact_case_id";
           "planned_pattern";
           "expected_behavior";
           "target_test_artifact";
           "implementation_pressure";
         ];
       if
         not (String.starts_with ~prefix:"reused-exact:" (field "exact_case_id" row))
       then Alcotest.failf "%s: exact_case_id must use reused-exact prefix"
           (field "plan_id" row);
       Alcotest.(check string)
         "expected behavior"
         "compile_ok"
         (field "expected_behavior" row);
       Alcotest.(check string)
         "target artifact"
         "test/test_ecma262_reused_candidate_exact_compile_parser.ml"
         (field "target_test_artifact" row))
    (planned_rows rows);
  List.iter
    (fun row ->
       Alcotest.(check string) "exact case id" "" (field "exact_case_id" row);
       Alcotest.(check string) "planned pattern" "" (field "planned_pattern" row);
       Alcotest.(check string) "planned flags" "" (field "planned_flags" row);
       Alcotest.(check string) "expected behavior" "" (field "expected_behavior" row);
       Alcotest.(check string) "target artifact" "" (field "target_test_artifact" row);
       Alcotest.(check string)
         "implementation pressure"
         ""
         (field "implementation_pressure" row))
    (manual_rows rows)

let () =
  Alcotest.run "ecma262-reused-candidate-exact-plan" [
    ("manifest", [
      Alcotest.test_case "reused candidate exact plan invariants" `Quick
        test_reused_candidate_exact_plan_manifest;
    ]);
  ]
