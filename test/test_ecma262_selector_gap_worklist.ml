let repo_root () =
  let cwd = Sys.getcwd () in
  let rec climb dir =
    let candidate =
      Filename.concat dir "cache/ecma262-regexp-selector-gap-worklist.tsv"
    in
    if Sys.file_exists candidate then dir
    else
      let parent = Filename.dirname dir in
      if parent = dir then
        Alcotest.fail
          "cache/ecma262-regexp-selector-gap-worklist.tsv is missing; run \
           tools/build_ecma262_regexp_selector_gap_worklist.py"
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

let worklist_rows () =
  read_tsv [ "cache"; "ecma262-regexp-selector-gap-worklist.tsv" ]

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

let source_exists case_source =
  match String.split_on_char ':' case_source with
  | source_path :: _ ->
    Sys.file_exists (path [ "external"; "test262"; source_path ])
  | [] -> false

let test_selector_gap_manifest () =
  let rows = worklist_rows () in
  Alcotest.(check int) "selector gap rows" 0 (List.length rows);
  let state_counts = count_by "selector_gap_state" rows in
  check_count state_counts "local_exact_test_required" 0;
  check_count state_counts "selector_complete_compile_case_available" 0;
  let action_counts = count_by "next_action" rows in
  check_count action_counts "add_local_exact_compile_or_parser_test" 0;
  let layer_counts = count_by "executable_layer" rows in
  check_count layer_counts "compile" 0;
  check_count layer_counts "parser" 0;
  let family_counts = count_by "mapping_family" rows in
  check_count family_counts "compile_literal_validity" 0;
  check_count family_counts "compile_surface_exact" 0;
  check_count family_counts "parser_captures_semantic_operation" 0;
  check_count family_counts "parser_escapes_semantic_operation" 0;
  check_count family_counts "parser_grammar_production" 0;
  check_count family_counts "parser_semantic_operation" 0;
  check_count family_counts "parser_unicode_sets_semantic_operation" 0;
  List.iter
    (fun row ->
       Alcotest.(check string)
         "exact candidate count"
         "0"
         (field "exact_candidate_count" row);
       Alcotest.(check string) "best case id" "" (field "best_case_id" row);
       Alcotest.(check string)
         "next action"
         "add_local_exact_compile_or_parser_test"
         (field "next_action" row);
       if field "missing_selector_tags" row = "" then
         Alcotest.failf "%s: missing_selector_tags is empty"
           (field "worklist_id" row);
       if not (source_exists (field "current_case_source" row)) then
         Alcotest.failf "%s: missing current test262 source %s"
           (field "worklist_id" row)
           (field "current_case_source" row))
    rows

let () =
  Alcotest.run "ecma262-selector-gap-worklist" [
    ("manifest", [
      Alcotest.test_case "selector gap worklist invariants" `Quick
        test_selector_gap_manifest;
    ]);
  ]
