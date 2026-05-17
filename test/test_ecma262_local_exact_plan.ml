let repo_root () =
  let cwd = Sys.getcwd () in
  let rec climb dir =
    let candidate =
      Filename.concat dir "cache/ecma262-regexp-local-exact-plan.tsv"
    in
    if Sys.file_exists candidate then dir
    else
      let parent = Filename.dirname dir in
      if parent = dir then
        Alcotest.fail
          "cache/ecma262-regexp-local-exact-plan.tsv is missing; run \
           tools/build_ecma262_regexp_local_exact_plan.py"
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
  read_tsv [ "cache"; "ecma262-regexp-local-exact-plan.tsv" ]

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

let source_exists row =
  let source_file = field "source_file" row in
  source_file <> "" && Sys.file_exists (path [ source_file ])

let check_unique field_name rows =
  let seen = Hashtbl.create (List.length rows) in
  List.iter
    (fun row ->
       let value = field field_name row in
       if Hashtbl.mem seen value then
         Alcotest.failf "duplicate %s %s" field_name value;
       Hashtbl.add seen value ())
    rows

let test_local_exact_plan_manifest () =
  let rows = plan_rows () in
  Alcotest.(check int) "local exact plan rows" 319 (List.length rows);
  check_unique "plan_id" rows;
  check_unique "local_case_id" rows;
  let family_counts = count_by "local_case_family" rows in
  check_count family_counts "compile_literal_validity" 1;
  check_count family_counts "compile_surface_exact" 16;
  check_count family_counts "parser_capture_local_exact" 27;
  check_count family_counts "parser_character_class_local_exact" 4;
  check_count family_counts "parser_character_escape_local_exact" 79;
  check_count family_counts "parser_modifiers_local_exact" 15;
  check_count family_counts "parser_unicode_property_local_exact" 131;
  check_count family_counts "parser_unicode_sets_local_exact" 46;
  let layer_counts = count_by "executable_layer" rows in
  check_count layer_counts "compile" 17;
  check_count layer_counts "parser" 302;
  let flag_counts = count_by "planned_flags" rows in
  check_count flag_counts "" 127;
  check_count flag_counts "u" 146;
  check_count flag_counts "v" 46;
  let state_counts = count_by "plan_state" rows in
  check_count state_counts "planned_not_executable" 319;
  let credit_counts = count_by "coverage_credit" rows in
  check_count credit_counts "none_local_exact_planned" 319;
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
           "mapping_family";
           "executable_layer";
           "selector_tags";
           "missing_selector_tags";
           "local_case_family";
           "local_case_id";
           "planned_pattern";
           "expected_behavior";
           "coverage_credit";
           "plan_state";
           "target_test_artifact";
           "spec_reason";
           "implementation_pressure";
           "next_action";
         ];
       if not (source_exists row) then
         Alcotest.failf "%s: missing source file %s"
           (field "plan_id" row)
           (field "source_file" row);
       Alcotest.(check string)
         "expected behavior"
         "compile_ok"
         (field "expected_behavior" row);
       Alcotest.(check string)
         "coverage credit"
         "none_local_exact_planned"
         (field "coverage_credit" row);
       Alcotest.(check string)
         "plan state"
         "planned_not_executable"
         (field "plan_state" row);
       Alcotest.(check string)
         "target artifact"
         "test/test_ecma262_local_exact_compile_parser.ml"
         (field "target_test_artifact" row);
       Alcotest.(check string)
         "next action"
         "materialize_local_exact_case"
         (field "next_action" row))
    rows

let () =
  Alcotest.run "ecma262-local-exact-plan" [
    ("manifest", [
      Alcotest.test_case "local exact planned rows are explicit" `Quick
        test_local_exact_plan_manifest;
    ]);
  ]
