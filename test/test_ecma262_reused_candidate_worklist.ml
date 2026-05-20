let repo_root () =
  let cwd = Sys.getcwd () in
  let rec climb dir =
    let candidate =
      Filename.concat dir "cache/ecma262-regexp-reused-candidate-worklist.tsv"
    in
    if Sys.file_exists candidate then dir
    else
      let parent = Filename.dirname dir in
      if parent = dir then
        Alcotest.fail
          "cache/ecma262-regexp-reused-candidate-worklist.tsv is missing; run \
           tools/build_ecma262_regexp_reused_candidate_worklist.py"
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

let worklist_rows () =
  read_tsv [ "cache"; "ecma262-regexp-reused-candidate-worklist.tsv" ]

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
    key expected
    (Option.value (Hashtbl.find_opt counts key) ~default:0)

let test262_source_exists case_source =
  match String.split_on_char ':' case_source with
  | source_path :: _ ->
      Sys.file_exists (path [ "external"; "test262"; source_path ])
  | [] -> false

let ecma262_source_exists source_file =
  String.starts_with ~prefix:"external/ecma262/" source_file
  && Sys.file_exists (path [ source_file ])

let int_field name row =
  match int_of_string_opt (field name row) with
  | Some value -> value
  | None ->
      Alcotest.failf "%s: field %s is not an int" (field "worklist_id" row) name

let test_reused_candidate_manifest () =
  let rows = worklist_rows () in
  Alcotest.(check int) "reused candidate rows" 0 (List.length rows);
  let state_counts = count_by "reuse_worklist_state" rows in
  check_count state_counts "reused_candidate_needs_exact_proof" 0;
  let decision_counts = count_by "proof_decision" rows in
  check_count decision_counts "needs_local_exact_case" 0;
  check_count decision_counts "manual_spec_review_required" 0;
  let credit_counts = count_by "coverage_credit" rows in
  check_count credit_counts "none_reused_candidate_worklist" 0;
  let pressure_counts = count_by "cluster_pressure" rows in
  check_count pressure_counts "high_reuse_spread" 0;
  check_count pressure_counts "medium_reuse_spread" 0;
  check_count pressure_counts "low_reuse_spread" 0;
  let layer_counts = count_by "executable_layer" rows in
  check_count layer_counts "compile" 0;
  check_count layer_counts "parser" 0;
  let cluster_size_counts = count_by "cluster_size" rows in
  check_count cluster_size_counts "64" 0;
  check_count cluster_size_counts "42" 0;
  check_count cluster_size_counts "41" 0;
  check_count cluster_size_counts "27" 0;
  check_count cluster_size_counts "11" 0;
  check_count cluster_size_counts "8" 0;
  check_count cluster_size_counts "4" 0;
  check_count cluster_size_counts "2" 0;
  let case_counts = count_by "selected_case_id" rows in
  Alcotest.(check int) "reused clusters" 0 (Hashtbl.length case_counts);
  List.iter
    (fun row ->
      Alcotest.(check string)
        "next action" "split_reused_candidate_or_add_local_exact_test"
        (field "next_action" row);
      if field "selected_pattern" row = "" then
        Alcotest.failf "%s: selected_pattern is empty" (field "worklist_id" row);
      if int_field "case_reuse_count" row <> int_field "cluster_size" row then
        Alcotest.failf "%s: case_reuse_count and cluster_size differ"
          (field "worklist_id" row);
      if int_field "cluster_size" row <= 1 then
        Alcotest.failf "%s: cluster_size must be reused"
          (field "worklist_id" row);
      if
        field "selected_case_source" row = ""
        || not (test262_source_exists (field "selected_case_source" row))
      then
        Alcotest.failf "%s: selected case source missing: %s"
          (field "worklist_id" row)
          (field "selected_case_source" row);
      if not (ecma262_source_exists (field "source_file" row)) then
        Alcotest.failf "%s: ECMA source missing: %s" (field "worklist_id" row)
          (field "source_file" row);
      if not (String.starts_with ~prefix:"none" (field "coverage_credit" row))
      then
        Alcotest.failf "%s: reused worklist must not credit coverage"
          (field "worklist_id" row))
    rows

let () =
  Alcotest.run "ecma262-reused-candidate-worklist"
    [
      ( "manifest",
        [
          Alcotest.test_case "reused candidate worklist invariants" `Quick
            test_reused_candidate_manifest;
        ] );
    ]
