let repo_root () =
  let cwd = Sys.getcwd () in
  let rec climb dir =
    let candidate =
      Filename.concat dir "cache/json-schema-corpus-failure-worklist.tsv"
    in
    if Sys.file_exists candidate then dir
    else
      let parent = Filename.dirname dir in
      if parent = dir then
        Alcotest.fail
          "cache/json-schema-corpus-failure-worklist.tsv is missing; run \
           tools/build_json_schema_corpus_failure_inventory.py"
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

let test_manifest () =
  let rows = read_tsv [ "cache"; "json-schema-corpus-failure-worklist.tsv" ] in
  Alcotest.(check int) "worklist rows" 0 (List.length rows);
  let family_counts = count_by "failure_family" rows in
  check_count family_counts "character_class_digit_semantics" 0;
  check_count family_counts "character_class_word_semantics" 0;
  check_count family_counts "format_regex_semantics" 0;
  check_count family_counts "unicode_non_bmp_semantics" 0;
  check_count family_counts "unicode_property_escape_semantics" 0;
  check_count family_counts "unicode_semantics" 0;
  check_count family_counts "json_schema_harness_unsupported_schema_shape" 0;
  let bucket_counts = count_by "implementation_bucket" rows in
  check_count bucket_counts "compile_parser" 0;
  check_count bucket_counts "match_engine_character_classes" 0;
  check_count bucket_counts "match_engine_unicode" 0;
  check_count bucket_counts "json_schema_harness" 0;
  let priority_counts = count_by "priority" rows in
  check_count priority_counts "1" 0;
  check_count priority_counts "2" 0;
  check_count priority_counts "3" 0;
  check_count priority_counts "4" 0;
  check_count priority_counts "5" 0;
  let seen = Hashtbl.create 128 in
  List.iter
    (fun row ->
      let worklist_id = field "worklist_id" row in
      if Hashtbl.mem seen worklist_id then
        Alcotest.failf "%s: duplicate worklist id" worklist_id;
      Hashtbl.add seen worklist_id ();
      Alcotest.(check string)
        "coverage credit" "none_json_schema_consumer_worklist"
        (field "coverage_credit" row);
      if field "target_test_artifact" row = "" then
        Alcotest.failf "%s: empty target test artifact" worklist_id;
      if not (Sys.file_exists (path [ field "target_test_artifact" row ])) then
        Alcotest.failf "%s: missing target test artifact %s" worklist_id
          (field "target_test_artifact" row);
      if field "next_action" row = "" then
        Alcotest.failf "%s: empty next action" worklist_id;
      if field "worklist_reason" row = "" then
        Alcotest.failf "%s: empty reason" worklist_id)
    rows

let () =
  Alcotest.run "json-schema-failure-worklist"
    [
      ( "manifest",
        [
          Alcotest.test_case "JSON Schema failure worklist manifest" `Quick
            test_manifest;
        ] );
    ]
